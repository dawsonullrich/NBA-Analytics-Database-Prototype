import argparse
import sqlite3
from pathlib import Path
from time import perf_counter

import pandas as pd

from database_setup import DATA_DIR, TABLE_FILES, create_database, load_csv


PROJECT_DIR = Path(__file__).resolve().parent


QUERIES = {
    "top_scoring": """
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
    "team_summary": """
        SELECT
            t.abbreviation AS team,
            ROUND(AVG(s.points), 2) AS average_points,
            ROUND(AVG(s.rebounds), 2) AS average_rebounds,
            ROUND(AVG(s.assists), 2) AS average_assists
        FROM player_game_stats s
        JOIN players p ON s.player_id = p.player_id
        JOIN teams t ON p.team_id = t.team_id
        GROUP BY t.team_id, t.abbreviation
        ORDER BY average_points DESC
    """,
    "injury_report": """
        SELECT
            p.first_name || ' ' || p.last_name AS player,
            t.abbreviation AS team,
            i.report_date,
            i.status,
            i.description
        FROM injuries i
        JOIN players p ON i.player_id = p.player_id
        JOIN teams t ON p.team_id = t.team_id
        WHERE i.status != 'Available'
        ORDER BY i.report_date DESC
    """,
    "advanced_leaders": """
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
}


def time_step(label, function):
    start_time = perf_counter()
    result = function()
    elapsed_ms = (perf_counter() - start_time) * 1000
    return {
        "part": label,
        "elapsed_ms": round(elapsed_ms, 4),
        "result": result,
    }


def load_data_with_timing(connection):
    results = []

    for table_name, file_name in TABLE_FILES.items():
        csv_path = DATA_DIR / file_name
        results.append(time_step(
            f"load_csv_{table_name}",
            lambda table_name=table_name, csv_path=csv_path: load_csv(
                connection,
                table_name,
                csv_path,
            ),
        ))

    commit_result = time_step("database_commit", connection.commit)
    results.append(commit_result)
    return results


def run_query_benchmarks(connection, iterations):
    results = []

    for query_name, query in QUERIES.items():
        def run_query(query=query):
            for _ in range(iterations):
                connection.execute(query).fetchall()
            return f"{iterations} runs"

        results.append(time_step(f"query_{query_name}", run_query))

    return results


def run_statistics_benchmark(connection, iterations):
    statistical_query = """
        SELECT
            p.first_name || ' ' || p.last_name AS player,
            s.minutes_played,
            s.points,
            s.rebounds,
            s.assists,
            s.turnovers
        FROM player_game_stats s
        JOIN players p ON s.player_id = p.player_id
    """

    def run_statistics():
        for _ in range(iterations):
            dataframe = pd.read_sql_query(statistical_query, connection)
            dataframe.describe()
            dataframe[[
                "minutes_played",
                "points",
                "rebounds",
                "assists",
                "turnovers",
            ]].corr()
        return f"{iterations} runs"

    return time_step("pandas_statistics_module", run_statistics)


def run_query_plan_check(connection):
    query_plan = connection.execute("""
        EXPLAIN QUERY PLAN
        SELECT player_id, game_id, points
        FROM player_game_stats
        ORDER BY points DESC
        LIMIT 5
    """).fetchall()

    return "; ".join(str(row) for row in query_plan)


def benchmark_framework(iterations):
    results = []

    schema_result = time_step(
        "schema_creation_and_indexes",
        lambda: create_database(":memory:"),
    )
    connection = schema_result["result"]
    schema_result["result"] = "SQLite in-memory database ready"
    results.append(schema_result)

    results.extend(load_data_with_timing(connection))
    results.extend(run_query_benchmarks(connection, iterations))
    results.append(run_statistics_benchmark(connection, iterations))
    results.append(time_step("query_plan_check", lambda: run_query_plan_check(connection)))
    results.append(time_step(
        "foreign_key_validation",
        lambda: len(connection.execute("PRAGMA foreign_key_check").fetchall()),
    ))

    connection.close()
    return results


def print_results(results):
    print("Individual Framework Performance")
    print("part | elapsed_ms | result")
    print("-" * 90)

    for row in results:
        print(f"{row['part']} | {row['elapsed_ms']} | {row['result']}")


def save_results(results, output_path):
    dataframe = pd.DataFrame(results)
    dataframe.to_csv(output_path, index=False)


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark the individual parts of the NBA analytics framework.",
    )
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument(
        "--output",
        default=None,
        help="Optional CSV path for saving benchmark results.",
    )
    args = parser.parse_args()

    results = benchmark_framework(args.iterations)
    print_results(results)

    if args.output:
        save_results(results, args.output)
        print(f"\nSaved benchmark results to {args.output}")


if __name__ == "__main__":
    main()
