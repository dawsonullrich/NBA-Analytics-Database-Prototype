import argparse
from collections import defaultdict
from pathlib import Path

import pandas as pd
from nba_api.stats.endpoints import (
    boxscoreadvancedv2,
    boxscoreadvancedv3,
    boxscoretraditionalv2,
    boxscoretraditionalv3,
    commonplayerinfo,
    leaguegamefinder,
)
from nba_api.stats.static import teams as nba_teams

from database_setup import create_database, run_reports


PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_FILE = PROJECT_DIR / "nba_analytics.db"
INJURY_FILE = PROJECT_DIR / "data" / "injuries.csv"


TEAM_DETAILS = {
    "ATL": ("East", "Southeast"),
    "BOS": ("East", "Atlantic"),
    "BKN": ("East", "Atlantic"),
    "CHA": ("East", "Southeast"),
    "CHI": ("East", "Central"),
    "CLE": ("East", "Central"),
    "DAL": ("West", "Southwest"),
    "DEN": ("West", "Northwest"),
    "DET": ("East", "Central"),
    "GSW": ("West", "Pacific"),
    "HOU": ("West", "Southwest"),
    "IND": ("East", "Central"),
    "LAC": ("West", "Pacific"),
    "LAL": ("West", "Pacific"),
    "MEM": ("West", "Southwest"),
    "MIA": ("East", "Southeast"),
    "MIL": ("East", "Central"),
    "MIN": ("West", "Northwest"),
    "NOP": ("West", "Southwest"),
    "NYK": ("East", "Atlantic"),
    "OKC": ("West", "Northwest"),
    "ORL": ("East", "Southeast"),
    "PHI": ("East", "Atlantic"),
    "PHX": ("West", "Pacific"),
    "POR": ("West", "Northwest"),
    "SAC": ("West", "Pacific"),
    "SAS": ("West", "Southwest"),
    "TOR": ("East", "Atlantic"),
    "UTA": ("West", "Northwest"),
    "WAS": ("East", "Southeast"),
}


def insert_dataframe(connection, table_name, dataframe):
    if dataframe.empty:
        return 0

    dataframe.to_sql(table_name, connection, if_exists="append", index=False)
    return len(dataframe)


def get_team_dataframe():
    team_rows = []

    for team in nba_teams.get_teams():
        conference, division = TEAM_DETAILS.get(
            team["abbreviation"],
            ("Unknown", "Unknown"),
        )
        team_rows.append({
            "team_id": team["id"],
            "abbreviation": team["abbreviation"],
            "team_name": team["full_name"],
            "conference": conference,
            "division": division,
        })

    return pd.DataFrame(team_rows)


def get_game_dataframe(season, max_games):
    finder = leaguegamefinder.LeagueGameFinder(
        league_id_nullable="00",
        season_nullable=season,
        season_type_nullable="Regular Season",
    )
    game_rows = finder.get_data_frames()[0]
    game_rows = game_rows.sort_values("GAME_DATE", ascending=False)

    games = []
    for game_id, rows in game_rows.groupby("GAME_ID", sort=False):
        if len(games) >= max_games:
            break

        if len(rows) != 2:
            continue

        home_row = rows[rows["MATCHUP"].str.contains(" vs. ", regex=False)]
        away_row = rows[rows["MATCHUP"].str.contains(" @ ", regex=False)]
        if home_row.empty or away_row.empty:
            continue

        home_row = home_row.iloc[0]
        away_row = away_row.iloc[0]
        games.append({
            "game_id": int(game_id),
            "game_date": home_row["GAME_DATE"],
            "season": season,
            "home_team_id": int(home_row["TEAM_ID"]),
            "away_team_id": int(away_row["TEAM_ID"]),
            "home_score": int(home_row["PTS"]),
            "away_score": int(away_row["PTS"]),
            "api_game_id": game_id,
        })

    return pd.DataFrame(games)


def player_height_to_inches(height_text):
    if not isinstance(height_text, str) or "-" not in height_text:
        return None

    feet, inches = height_text.split("-", 1)
    try:
        return int(feet) * 12 + int(inches)
    except ValueError:
        return None


def get_player_info(player_id):
    try:
        info = commonplayerinfo.CommonPlayerInfo(player_id=player_id)
        row = info.get_data_frames()[0].iloc[0]
    except Exception:
        return {
            "position": "Unknown",
            "height_inches": None,
            "weight_lbs": None,
        }

    weight = row.get("WEIGHT")
    try:
        weight = int(weight)
    except (TypeError, ValueError):
        weight = None

    return {
        "position": row.get("POSITION") or "Unknown",
        "height_inches": player_height_to_inches(row.get("HEIGHT")),
        "weight_lbs": weight,
    }


def get_box_score_data(game_records, season, fetch_player_details=False):
    players = {}
    stat_rows = []
    advanced_totals = defaultdict(lambda: {
        "games": 0,
        "usage_rate": 0.0,
        "true_shooting_pct": 0.0,
        "player_efficiency_rating": 0.0,
        "offensive_rating": 0.0,
        "defensive_rating": 0.0,
    })

    stat_id = 1
    for game in game_records:
        game_id = game["api_game_id"]
        traditional_rows, advanced_by_player, use_v3 = get_box_score_frames(game_id)

        for _, row in traditional_rows.iterrows():
            player_id_value = row["personId"] if use_v3 else row["PLAYER_ID"]
            minutes_value = row["minutes"] if use_v3 else row["MIN"]
            if pd.isna(player_id_value) or not has_played_minutes(minutes_value):
                continue

            player_id = int(player_id_value)
            if use_v3:
                first_name = row["firstName"]
                last_name = row["familyName"]
                team_id = int(row["teamId"])
            else:
                full_name = str(row["PLAYER_NAME"]).split()
                first_name = full_name[0]
                last_name = " ".join(full_name[1:]) if len(full_name) > 1 else ""
                team_id = int(row["TEAM_ID"])

            if player_id not in players:
                if fetch_player_details:
                    player_details = get_player_info(player_id)
                else:
                    player_details = {
                        "position": row.get("position") if use_v3 else "Unknown",
                        "height_inches": None,
                        "weight_lbs": None,
                    }
                players[player_id] = {
                    "player_id": player_id,
                    "team_id": team_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    **player_details,
                }

            stat_rows.append({
                "stat_id": stat_id,
                "game_id": int(game["game_id"]),
                "player_id": player_id,
                "minutes_played": convert_minutes(minutes_value),
                "points": int_or_zero(value_from_row(row, use_v3, "points", "PTS")),
                "rebounds": int_or_zero(value_from_row(row, use_v3, "reboundsTotal", "REB")),
                "assists": int_or_zero(value_from_row(row, use_v3, "assists", "AST")),
                "steals": int_or_zero(value_from_row(row, use_v3, "steals", "STL")),
                "blocks": int_or_zero(value_from_row(row, use_v3, "blocks", "BLK")),
                "turnovers": int_or_zero(value_from_row(row, use_v3, "turnovers", "TO")),
                "field_goals_made": int_or_zero(value_from_row(row, use_v3, "fieldGoalsMade", "FGM")),
                "field_goals_attempted": int_or_zero(value_from_row(row, use_v3, "fieldGoalsAttempted", "FGA")),
                "three_points_made": int_or_zero(value_from_row(row, use_v3, "threePointersMade", "FG3M")),
                "three_points_attempted": int_or_zero(value_from_row(row, use_v3, "threePointersAttempted", "FG3A")),
                "free_throws_made": int_or_zero(value_from_row(row, use_v3, "freeThrowsMade", "FTM")),
                "free_throws_attempted": int_or_zero(value_from_row(row, use_v3, "freeThrowsAttempted", "FTA")),
            })
            stat_id += 1

            if player_id in advanced_by_player:
                advanced_row = advanced_by_player[player_id]
                player_totals = advanced_totals[player_id]
                player_totals["games"] += 1
                player_totals["usage_rate"] += advanced_value(advanced_row, use_v3, "usagePercentage", "USG_PCT")
                player_totals["true_shooting_pct"] += advanced_value(advanced_row, use_v3, "trueShootingPercentage", "TS_PCT")
                player_totals["player_efficiency_rating"] += advanced_value(advanced_row, use_v3, "PIE", "PIE")
                player_totals["offensive_rating"] += advanced_value(advanced_row, use_v3, "offensiveRating", "OFF_RATING")
                player_totals["defensive_rating"] += advanced_value(advanced_row, use_v3, "defensiveRating", "DEF_RATING")

    player_frame = pd.DataFrame(players.values())
    stat_frame = pd.DataFrame(stat_rows)
    advanced_frame = build_advanced_frame(advanced_totals, season)

    return player_frame, stat_frame, advanced_frame


def get_box_score_frames(game_id):
    try:
        traditional = boxscoretraditionalv3.BoxScoreTraditionalV3(game_id=game_id)
        advanced = boxscoreadvancedv3.BoxScoreAdvancedV3(game_id=game_id)
        advanced_rows = advanced.get_data_frames()[0]
        advanced_by_player = {
            int(row["personId"]): row
            for _, row in advanced_rows.iterrows()
            if pd.notna(row["personId"])
        }
        return traditional.get_data_frames()[0], advanced_by_player, True
    except Exception:
        traditional = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id)
        advanced = boxscoreadvancedv2.BoxScoreAdvancedV2(game_id=game_id)
        advanced_rows = advanced.get_data_frames()[0]
        advanced_by_player = {
            int(row["PLAYER_ID"]): row
            for _, row in advanced_rows.iterrows()
            if pd.notna(row["PLAYER_ID"])
        }
        return traditional.get_data_frames()[0], advanced_by_player, False


def has_played_minutes(value):
    if pd.isna(value):
        return False

    text = str(value).strip()
    return text not in ("", "0", "0:00", "PT00M00.00S")


def value_from_row(row, use_v3, v3_column, v2_column):
    return row[v3_column] if use_v3 else row[v2_column]


def advanced_value(row, use_v3, v3_column, v2_column):
    return float_or_zero(row.get(v3_column if use_v3 else v2_column))


def convert_minutes(value):
    if pd.isna(value):
        return 0.0

    text = str(value)
    if text.startswith("PT") and "M" in text:
        minutes = text.split("PT", 1)[1].split("M", 1)[0]
        seconds = "0"
        if "S" in text:
            seconds = text.split("M", 1)[1].split("S", 1)[0]
        try:
            return round(int(minutes) + float(seconds) / 60, 2)
        except ValueError:
            return 0.0

    if ":" not in text:
        try:
            return float(text)
        except ValueError:
            return 0.0

    minutes, seconds = text.split(":", 1)
    return round(int(minutes) + int(seconds) / 60, 2)


def int_or_zero(value):
    if pd.isna(value):
        return 0
    return int(value)


def float_or_zero(value):
    if pd.isna(value):
        return 0.0
    return float(value)


def build_advanced_frame(advanced_totals, season):
    rows = []

    for metric_id, (player_id, totals) in enumerate(advanced_totals.items(), start=1):
        games = max(totals["games"], 1)
        rows.append({
            "metric_id": metric_id,
            "player_id": player_id,
            "season": season,
            "usage_rate": round(totals["usage_rate"] / games, 3),
            "true_shooting_pct": round(totals["true_shooting_pct"] / games, 3),
            "player_efficiency_rating": round(
                totals["player_efficiency_rating"] / games,
                3,
            ),
            "offensive_rating": round(totals["offensive_rating"] / games, 1),
            "defensive_rating": round(totals["defensive_rating"] / games, 1),
        })

    return pd.DataFrame(rows)


def load_api_data(
    connection,
    season,
    max_games,
    include_sample_injuries=False,
    fetch_player_details=False,
):
    teams = get_team_dataframe()
    games = get_game_dataframe(season, max_games)
    if games.empty:
        raise ValueError(f"No NBA games were returned for season {season}.")

    game_records = games.to_dict("records")
    games_for_database = games.drop(columns=["api_game_id"])
    players, stats, advanced_metrics = get_box_score_data(
        game_records,
        season,
        fetch_player_details=fetch_player_details,
    )

    counts = {
        "teams": insert_dataframe(connection, "teams", teams),
        "players": insert_dataframe(connection, "players", players),
        "games": insert_dataframe(connection, "games", games_for_database),
        "player_game_stats": insert_dataframe(connection, "player_game_stats", stats),
        "advanced_player_metrics": insert_dataframe(
            connection,
            "advanced_player_metrics",
            advanced_metrics,
        ),
    }

    if include_sample_injuries and INJURY_FILE.exists():
        counts["injuries"] = load_matching_sample_injuries(connection)
    else:
        counts["injuries"] = 0

    connection.commit()
    return counts


def load_matching_sample_injuries(connection):
    injuries = pd.read_csv(INJURY_FILE)
    player_ids = pd.read_sql_query(
        "SELECT player_id FROM players",
        connection,
    )["player_id"]
    injuries = injuries[injuries["player_id"].isin(player_ids)]

    return insert_dataframe(connection, "injuries", injuries)


def main():
    parser = argparse.ArgumentParser(
        description="Create the NBA analytics database from live nba_api data.",
    )
    parser.add_argument("--season", default="2023-24")
    parser.add_argument("--max-games", type=int, default=5)
    parser.add_argument("--database", default=DATABASE_FILE)
    parser.add_argument(
        "--include-sample-injuries",
        action="store_true",
        help="Also load the local sample injury CSV file.",
    )
    parser.add_argument(
        "--fetch-player-details",
        action="store_true",
        help="Call CommonPlayerInfo for height and weight. This is slower.",
    )
    args = parser.parse_args()

    connection = create_database(Path(args.database))
    counts = load_api_data(
        connection,
        season=args.season,
        max_games=args.max_games,
        include_sample_injuries=args.include_sample_injuries,
        fetch_player_details=args.fetch_player_details,
    )

    print("NBA Analytics Database - API Import")
    print("\nRows loaded:")
    for table_name, count in counts.items():
        print(f"{table_name}: {count}")

    run_reports(connection)
    connection.close()


if __name__ == "__main__":
    main()
