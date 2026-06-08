PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS advanced_player_metrics;
DROP TABLE IF EXISTS injuries;
DROP TABLE IF EXISTS player_game_stats;
DROP TABLE IF EXISTS games;
DROP TABLE IF EXISTS players;
DROP TABLE IF EXISTS teams;

CREATE TABLE teams (
    team_id INTEGER PRIMARY KEY,
    abbreviation TEXT NOT NULL UNIQUE,
    team_name TEXT NOT NULL,
    conference TEXT NOT NULL CHECK (conference IN ('East', 'West')),
    division TEXT NOT NULL
);

CREATE TABLE players (
    player_id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    position TEXT NOT NULL,
    height_inches INTEGER,
    weight_lbs INTEGER,
    FOREIGN KEY (team_id) REFERENCES teams(team_id)
);

CREATE TABLE games (
    game_id INTEGER PRIMARY KEY,
    game_date DATE NOT NULL,
    season TEXT NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER NOT NULL,
    away_score INTEGER NOT NULL,
    FOREIGN KEY (home_team_id) REFERENCES teams(team_id),
    FOREIGN KEY (away_team_id) REFERENCES teams(team_id),
    CHECK (home_team_id != away_team_id)
);

CREATE TABLE player_game_stats (
    stat_id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    minutes_played REAL NOT NULL,
    points INTEGER NOT NULL,
    rebounds INTEGER NOT NULL,
    assists INTEGER NOT NULL,
    steals INTEGER NOT NULL,
    blocks INTEGER NOT NULL,
    turnovers INTEGER NOT NULL,
    field_goals_made INTEGER NOT NULL,
    field_goals_attempted INTEGER NOT NULL,
    three_points_made INTEGER NOT NULL,
    three_points_attempted INTEGER NOT NULL,
    free_throws_made INTEGER NOT NULL,
    free_throws_attempted INTEGER NOT NULL,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    UNIQUE (game_id, player_id)
);

CREATE TABLE injuries (
    injury_id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL,
    report_date DATE NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN ('Available', 'Questionable', 'Doubtful', 'Out')
    ),
    description TEXT NOT NULL,
    expected_return_date DATE,
    FOREIGN KEY (player_id) REFERENCES players(player_id)
);

CREATE TABLE advanced_player_metrics (
    metric_id INTEGER PRIMARY KEY,
    player_id INTEGER NOT NULL,
    season TEXT NOT NULL,
    usage_rate REAL NOT NULL,
    true_shooting_pct REAL NOT NULL,
    player_efficiency_rating REAL NOT NULL,
    offensive_rating REAL NOT NULL,
    defensive_rating REAL NOT NULL,
    FOREIGN KEY (player_id) REFERENCES players(player_id),
    UNIQUE (player_id, season)
);

CREATE INDEX idx_players_team ON players(team_id);
CREATE INDEX idx_games_date ON games(game_date);
CREATE INDEX idx_player_stats ON player_game_stats(player_id, game_id);
CREATE INDEX idx_injuries_status ON injuries(status, report_date);
CREATE INDEX idx_offensive_rating
    ON advanced_player_metrics(offensive_rating DESC);
