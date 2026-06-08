# NBA Analytics Database

This project creates a small NBA analytics database using Python, SQLite, SQL, and pandas. The database stores information about NBA teams, players, games, player statistics, injuries, and advanced player metrics.

The current version uses a small sample data set. It is meant to test the database design and queries before adding a larger amount of NBA data.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [How to Run](#how-to-run)
- [Database Tables](#database-tables)
- [Queries Included](#queries-included)

---

## Project Overview

NBA data can be spread across game logs, player box scores, injury reports, and advanced statistics. The goal of this project is to keep that information in one relational database and use SQL queries to compare player and team performance.

The prototype includes:

- 4 NBA teams
- 8 players
- 4 games
- 16 player-game stat records
- injury reports
- advanced player metrics

The main notebook creates the database, loads the CSV files, runs analytical queries, and creates a few charts.

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
|-- sql/
|   |-- schema.sql
|   `-- analytics_queries.sql
|
|-- database_setup.py
|-- requirements.txt
`-- README.md
```

---

## How to Run

### Option 1 - Run the Python Script

From the project folder, run:

```bash
python database_setup.py
```

This creates `nba_analytics.db`, loads the CSV data, and prints several reports.

### Option 2 - Run the Jupyter Notebook

Start Jupyter:

```bash
jupyter notebook
```

Open `notebooks/NBA_Analytics_Database.ipynb` and run the cells in order.

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

For the full project, the sample CSV files can be replaced with a larger data set from an NBA API or another NBA data source.
