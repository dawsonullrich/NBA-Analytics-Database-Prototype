import sqlite3
import unittest

from benchmark_framework import benchmark_framework
from database_setup import create_database, load_all_data


TOP_SCORING_QUERY = """
    SELECT
        p.first_name || ' ' || p.last_name AS player,
        t.abbreviation AS team,
        g.game_date,
        s.points
    FROM player_game_stats s
    JOIN players p ON s.player_id = p.player_id
    JOIN teams t ON p.team_id = t.team_id
    JOIN games g ON s.game_id = g.game_id
    ORDER BY s.points DESC
    LIMIT 5
"""


TEAM_SUMMARY_QUERY = """
    SELECT
        t.abbreviation AS team,
        ROUND(AVG(s.points), 2) AS average_points
    FROM player_game_stats s
    JOIN players p ON s.player_id = p.player_id
    JOIN teams t ON p.team_id = t.team_id
    GROUP BY t.team_id, t.abbreviation
    ORDER BY average_points DESC
"""


INJURY_QUERY = """
    SELECT i.status
    FROM injuries i
    WHERE i.status != 'Available'
"""


class DatabaseFrameworkTest(unittest.TestCase):
    def setUp(self):
        self.connection = create_database(":memory:")
        self.loaded_counts = load_all_data(self.connection)

    def tearDown(self):
        self.connection.close()

    def test_csv_loader_loads_expected_rows(self):
        expected_counts = {
            "teams": 4,
            "players": 8,
            "games": 4,
            "player_game_stats": 16,
            "injuries": 3,
            "advanced_player_metrics": 8,
        }

        self.assertEqual(self.loaded_counts, expected_counts)

    def test_foreign_keys_are_valid(self):
        errors = self.connection.execute("PRAGMA foreign_key_check").fetchall()

        self.assertEqual(errors, [])

    def test_schema_indexes_exist(self):
        index_rows = self.connection.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'index'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()
        index_names = {row[0] for row in index_rows}

        self.assertIn("idx_players_team", index_names)
        self.assertIn("idx_player_stats", index_names)
        self.assertIn("idx_stats_points", index_names)
        self.assertIn("idx_injuries_status", index_names)
        self.assertIn("idx_offensive_rating", index_names)

    def test_top_scoring_query_returns_sorted_results(self):
        rows = self.connection.execute(TOP_SCORING_QUERY).fetchall()
        points = [row[3] for row in rows]

        self.assertEqual(rows[0][0], "Jayson Tatum")
        self.assertEqual(rows[0][3], 37)
        self.assertEqual(points, sorted(points, reverse=True))

    def test_team_summary_includes_all_teams(self):
        rows = self.connection.execute(TEAM_SUMMARY_QUERY).fetchall()
        teams = {row[0] for row in rows}

        self.assertEqual(teams, {"BOS", "DEN", "LAL", "MIL"})
        self.assertEqual(rows[0][0], "MIL")

    def test_injury_query_excludes_available_players(self):
        statuses = [row[0] for row in self.connection.execute(INJURY_QUERY)]

        self.assertEqual(statuses, ["Questionable", "Questionable"])

    def test_points_index_is_used_for_top_scoring_sort(self):
        query_plan = self.connection.execute("""
            EXPLAIN QUERY PLAN
            SELECT player_id, game_id, points
            FROM player_game_stats
            ORDER BY points DESC
            LIMIT 5
        """).fetchall()
        plan_text = " ".join(str(row) for row in query_plan)

        self.assertIn("idx_stats_points", plan_text)


class BenchmarkFrameworkTest(unittest.TestCase):
    def test_benchmark_returns_individual_framework_parts(self):
        results = benchmark_framework(iterations=1)
        parts = {row["part"] for row in results}

        self.assertIn("schema_creation_and_indexes", parts)
        self.assertIn("load_csv_player_game_stats", parts)
        self.assertIn("query_top_scoring", parts)
        self.assertIn("pandas_statistics_module", parts)
        self.assertIn("foreign_key_validation", parts)


if __name__ == "__main__":
    unittest.main()
