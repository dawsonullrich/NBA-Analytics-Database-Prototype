import csv
import sqlite3
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"
SCHEMA_FILE = PROJECT_DIR / "sql" / "schema.sql"
DATABASE_FILE = PROJECT_DIR / "nba_analytics.db"


TABLE_FILES = {
    "teams": "teams.csv",
    "players": "players.csv",
    "games": "games.csv",
    "player_game_stats": "player_game_stats.csv",
    "injuries": "injuries.csv",
    "advanced_player_metrics": "advanced_player_metrics.csv",
}


def create_database(database_path=DATABASE_FILE):
    connection = sqlite3.connect(database_path)
    connection.execute("PRAGMA foreign_keys = ON")

    with open(SCHEMA_FILE, "r", encoding="utf-8") as schema_file:
        connection.executescript(schema_file.read())

    return connection


def load_csv(connection, table_name, csv_path):
    with open(csv_path, "r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    if not rows:
        return 0

    columns = list(rows[0].keys())
    placeholders = ", ".join(["?"] * len(columns))
    column_names = ", ".join(columns)

    values = []
    for row in rows:
        values.append([
            None if row[column] == "" else row[column]
            for column in columns
        ])

    connection.executemany(
        f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})",
        values,
    )
    return len(values)


def load_all_data(connection):
    loaded_counts = {}

    for table_name, file_name in TABLE_FILES.items():
        loaded_counts[table_name] = load_csv(
            connection,
            table_name,
            DATA_DIR / file_name,
        )

    connection.commit()
    return loaded_counts


def print_query(connection, title, query):
    print(f"\n{title}")
    cursor = connection.execute(query)
    column_names = [description[0] for description in cursor.description]
    print(" | ".join(column_names))
    print("-" * 80)

    for row in cursor.fetchall():
        print(" | ".join(str(value) for value in row))


def run_reports(connection):
    print_query(
        connection,
        "Top Scoring Performances",
        """
        SELECT
            p.first_name || ' ' || p.last_name AS player,
            t.abbreviation AS team,
            g.game_date,
            s.points,
            s.rebounds,
            s.assists
        FROM player_game_stats s
        JOIN players p ON s.player_id = p.player_id
        JOIN teams t ON p.team_id = t.team_id
        JOIN games g ON s.game_id = g.game_id
        ORDER BY s.points DESC
        LIMIT 5
        """,
    )

    print_query(
        connection,
        "Current Injury Report",
        """
        SELECT
            p.first_name || ' ' || p.last_name AS player,
            t.abbreviation AS team,
            i.status,
            i.description,
            COALESCE(i.expected_return_date, 'TBD') AS expected_return
        FROM injuries i
        JOIN players p ON i.player_id = p.player_id
        JOIN teams t ON p.team_id = t.team_id
        WHERE i.status != 'Available'
        ORDER BY i.report_date DESC
        """,
    )

    print_query(
        connection,
        "Offensive Rating Leaders",
        """
        SELECT
            p.first_name || ' ' || p.last_name AS player,
            t.abbreviation AS team,
            m.true_shooting_pct,
            m.player_efficiency_rating,
            m.offensive_rating
        FROM advanced_player_metrics m
        JOIN players p ON m.player_id = p.player_id
        JOIN teams t ON p.team_id = t.team_id
        ORDER BY m.offensive_rating DESC
        """,
    )


def main():
    connection = create_database()
    loaded_counts = load_all_data(connection)

    print("NBA Analytics Database")
    print("\nRows loaded:")
    for table_name, count in loaded_counts.items():
        print(f"{table_name}: {count}")

    run_reports(connection)
    connection.close()


if __name__ == "__main__":
    main()
