# NBA Analytics Database

This project creates a small NBA analytics database using Python, SQLite, SQL, pandas, and the `nba_api` package. The database stores information about NBA teams, players, games, player statistics, injuries, and advanced player metrics.

The project can run in two ways. The CSV version uses a small sample data set so the project works offline. The API version calls NBA Stats endpoints through `nba_api` and loads live team, game, player, box-score, and advanced metric data into the same SQLite database.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [How to Run](#how-to-run)
- [Testing](#testing)
- [Database Tables](#database-tables)
- [Queries Included](#queries-included)

---

## Project Overview

NBA data can be spread across game logs, player box scores, injury reports, roster pages, and advanced statistics. Each source is useful by itself, but the data becomes more valuable when it can be connected. For example, a player performance question may need the player's team, the game result, the player's box-score line, and an advanced efficiency metric all at the same time.

The problem this project addresses is that separated data makes analysis slower and less reliable. If the information is copied into one large spreadsheet, repeated team and player data can become inconsistent. If the information stays in separate files, every analysis requires extra manual work. A relational database is a better fit because teams, players, games, injuries, and performance metrics can be stored in separate tables while still being connected through keys.

This project is important because sports analytics depends on asking questions across several types of data. A database can answer questions such as which players had the strongest scoring games, which teams are more efficient, which players are listed on the injury report, and which advanced metrics point to the most efficient players. The same framework can also grow from a small prototype into a larger NBA data system.

The prototype includes:

- 4 NBA teams
- 8 players
- 4 games
- 16 player-game stat records
- injury reports
- advanced player metrics

The main notebook creates the database, loads the CSV files, runs analytical queries, creates charts, calculates descriptive statistics and correlations, and records a query-performance baseline. The separate API importer can rebuild the database from NBA API calls.

The latest API test loaded 10 real 2023-24 NBA games. After filtering out roster rows for players who did not log minutes, the database contained 30 teams, 10 games, 239 player records, 239 player-game stat records, and 239 advanced metric records.

---

## Requirements

You will need:

- Python 3.9 or higher
- pip

### Python Libraries Used

| Library | Purpose |
|---|---|
| `pandas` | Loading CSV files and displaying query results |
| `matplotlib` | Creating charts |
| `nba_api` | Pulling NBA Stats API data |
| `sqlite3` | Creating and querying the database |
| `jupyter` | Running the notebook |

`sqlite3` is included with Python and does not need to be installed separately.

---

## Installation

Clone or download the repository. Open a terminal in the project folder and run:

```bash
pip install -r requirements.txt
```

---

## Project Structure

```text
NBA-Analytics-Database/
|
|-- data/
|   |-- teams.csv
|   |-- players.csv
|   |-- games.csv
|   |-- player_game_stats.csv
|   |-- injuries.csv
|   `-- advanced_player_metrics.csv
|
|-- notebooks/
|   `-- NBA_Analytics_Database.ipynb
|
|-- docs/
|   `-- performance_summary.md
|
|-- sql/
|   |-- schema.sql
|   `-- analytics_queries.sql
|
|-- api_import.py
|-- benchmark_framework.py
|-- database_setup.py
|-- requirements.txt
|-- tests/
|   `-- test_database_framework.py
`-- README.md
```

---

## How to Run

### Option 1 - Run the Offline CSV Version

From the project folder, run:

```bash
python database_setup.py
```

This creates `nba_analytics.db`, loads the CSV data, and prints several reports.

### Option 2 - Run the NBA API Version

From the project folder, run:

```bash
python api_import.py --season 2023-24 --max-games 10
```

This creates the same SQLite database structure, but it fills the tables using NBA API calls. The script uses:

- `nba_api.stats.static.teams` for team data
- `LeagueGameFinder` for game results
- `BoxScoreTraditionalV3` for player box-score statistics
- `BoxScoreAdvancedV3` for advanced player metrics

For larger imports, the script uses box-score position data and leaves height and weight blank. If you want height and weight too, add `--fetch-player-details`, but this is slower because it calls an extra player profile endpoint for each player.

The NBA API does not provide a simple official injury-report endpoint in this package, so injury data remains a local/manual CSV table for now.

In the latest 10-game API test, the top scoring performance was GG Jackson with 44 points, followed by Payton Pritchard with 38 points.

### Option 3 - Run the Jupyter Notebook

Start Jupyter:

```bash
jupyter notebook
```

Open `notebooks/NBA_Analytics_Database.ipynb` and run the cells in order.

### Option 4 - Benchmark Individual Framework Parts

The intermediate project feedback suggested evaluating the performance of individual parts of the framework instead of trying to evaluate the entire framework at once. To address that, run:

```bash
python benchmark_framework.py --iterations 1000 --output benchmark_results.csv
```

This times separate parts of the project:

- schema creation and index creation
- each CSV table load
- SQL analytical queries
- the pandas statistics module
- the query plan check
- foreign-key validation

This is more useful for the current project size because it shows which parts of the framework are being measured and can be repeated later with API-loaded data.

---

## Testing

The test suite checks the main database framework pieces:

- CSV files load the expected number of rows
- foreign-key relationships are valid
- expected indexes exist
- SQL reports return correct and sorted results
- the injury report filters available players
- the points index is used for the top-scoring query
- the individual framework benchmark returns the expected benchmark sections
- API helper functions correctly convert NBA minute formats and filter non-playing rows

Run the tests with:

```bash
python -m unittest discover -s tests -v
```

---

## Database Tables

| Table | Information Stored |
|---|---|
| `teams` | Team name, abbreviation, conference, and division |
| `players` | Player name, position, height, weight, and team |
| `games` | Game date, teams, season, and final score |
| `player_game_stats` | Player box-score statistics for each game |
| `injuries` | Injury status and expected return date |
| `advanced_player_metrics` | Usage rate, true shooting, PER, and ratings |

Primary and foreign keys are used to connect the tables. Indexes are also included for fields that may be searched or sorted often.

---

## Queries Included

The project includes queries for:

- top scoring performances
- average team statistics
- current injury reports
- game results and winners
- advanced metric leaders
- descriptive statistics for player-game data
- player averages and scoring consistency
- correlations between minutes, points, rebounds, assists, and turnovers
- an SQLite query plan and repeated timing test for an indexed query
- separate performance benchmarks for schema creation, data loading, SQL queries, statistics, query planning, and foreign-key validation

The API importer now replaces the sample CSV files for teams, games, players, player-game statistics, and advanced metrics. The same performance test can be repeated with more API-loaded games to measure how the indexes behave as the tables grow.
