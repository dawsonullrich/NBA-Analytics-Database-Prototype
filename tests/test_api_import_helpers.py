import unittest

from api_import import (
    build_advanced_frame,
    convert_minutes,
    has_played_minutes,
)


class ApiImportHelperTest(unittest.TestCase):
    def test_convert_minutes_handles_common_nba_formats(self):
        self.assertEqual(convert_minutes("23:24"), 23.4)
        self.assertEqual(convert_minutes("PT34M20.00S"), 34.33)
        self.assertEqual(convert_minutes("12.5"), 12.5)

    def test_has_played_minutes_filters_blank_or_zero_rows(self):
        self.assertFalse(has_played_minutes(""))
        self.assertFalse(has_played_minutes("0:00"))
        self.assertFalse(has_played_minutes("PT00M00.00S"))
        self.assertTrue(has_played_minutes("8:15"))

    def test_build_advanced_frame_averages_player_metrics(self):
        totals = {
            101: {
                "games": 2,
                "usage_rate": 0.5,
                "true_shooting_pct": 1.2,
                "player_efficiency_rating": 0.4,
                "offensive_rating": 240.0,
                "defensive_rating": 220.0,
            }
        }

        frame = build_advanced_frame(totals, "2023-24")

        self.assertEqual(len(frame), 1)
        self.assertEqual(frame.loc[0, "player_id"], 101)
        self.assertEqual(frame.loc[0, "usage_rate"], 0.25)
        self.assertEqual(frame.loc[0, "true_shooting_pct"], 0.6)
        self.assertEqual(frame.loc[0, "offensive_rating"], 120.0)


if __name__ == "__main__":
    unittest.main()
