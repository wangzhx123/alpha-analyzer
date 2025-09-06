#!/usr/bin/env python3

import unittest
import pandas as pd
import tempfile
import os
from pathlib import Path

# Import the components we want to test
from analyzer import AlphaAnalyzer
from checkers.alpha_sum_consistency import AlphaSumConsistencyChecker
from checkers.non_negative_trader import NonNegativeTraderChecker
from checkers.volume_rounding import VolumeRoundingChecker


class TestAlphaCheckers(unittest.TestCase):

    def setUp(self):
        """Set up test data based on production data structure"""
        self.temp_dir = tempfile.mkdtemp()

        # Create test data files similar to production_data
        self.create_test_data_files()

        # Initialize analyzer
        self.analyzer = AlphaAnalyzer()
        self.analyzer.add_checker(AlphaSumConsistencyChecker())
        self.analyzer.add_checker(NonNegativeTraderChecker())
        self.analyzer.add_checker(VolumeRoundingChecker())

    def tearDown(self):
        """Clean up temporary files"""
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_data_files(self):
        """Create test CSV files with known good data"""

        # InCheckAlphaEv.csv - Input alpha events
        incheck_data = """event|alphaid|time|ticker|volume
InCheckAlphaEv|sSZE113BUCS|93000000|000001.SZE|14000
InCheckAlphaEv|sSZE114BUCS|93000000|000001.SZE|14000
InCheckAlphaEv|sSZE113BUCS|93000000|000002.SZE|4000
InCheckAlphaEv|sSZE114BUCS|93000000|000002.SZE|4500"""

        # MergedAlphaEv.csv - Merged alpha (should sum to same as split)
        merged_data = """event|alphaid|time|ticker|volume
MergedAlphaEv|sSZEMNG500|93000000|000001.SZE|28000
MergedAlphaEv|sSZEMNG500|93000000|000002.SZE|8500"""

        # SplitAlphaEv.csv - Split alpha (should sum to same as merged)
        split_data = """event|alphaid|time|ticker|volume
SplitAlphaEv|sSZE113Atem|93000000|000001.SZE|14000
SplitAlphaEv|sSZE114Atem|93000000|000001.SZE|14000
SplitAlphaEv|sSZE113Atem|93000000|000002.SZE|4250
SplitAlphaEv|sSZE114Atem|93000000|000002.SZE|4250"""

        # SplitCtxEv.csv - Position context
        context_data = """event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol
SplitCtxEv|sSZE113Atem|93000000|000001.SZE|1200|1200|0|1200
SplitCtxEv|sSZE114Atem|93000000|000001.SZE|1800|1800|0|1800
SplitCtxEv|sSZE113Atem|93000000|000002.SZE|150|150|0|150
SplitCtxEv|sSZE114Atem|93000000|000002.SZE|250|250|0|250"""

        # MarketDataEv.csv - Market data
        market_data = """event|alphaid|time|ticker|last_price|prev_close_price
MarketDataEv|MktData|93000000|000001.SZE|10.50|10.25
MarketDataEv|MktData|93000000|000002.SZE|15.75|15.50"""

        # Write files
        files = {
            "InCheckAlphaEv.csv": incheck_data,
            "MergedAlphaEv.csv": merged_data,
            "SplitAlphaEv.csv": split_data,
            "SplitCtxEv.csv": context_data,
            "MarketDataEv.csv": market_data,
        }

        for filename, content in files.items():
            with open(Path(self.temp_dir) / filename, "w") as f:
                f.write(content)

    def test_data_loading(self):
        """Test that data loads correctly"""
        self.analyzer.load_data(self.temp_dir)

        # Verify data was loaded
        self.assertIsNotNone(self.analyzer.incheck_alpha_df)
        self.assertIsNotNone(self.analyzer.merged_df)
        self.assertIsNotNone(self.analyzer.split_alpha_df)
        self.assertIsNotNone(self.analyzer.realtime_pos_df)
        self.assertIsNotNone(self.analyzer.market_df)

        # Verify record counts
        self.assertEqual(len(self.analyzer.incheck_alpha_df), 4)
        self.assertEqual(len(self.analyzer.merged_df), 2)
        self.assertEqual(len(self.analyzer.split_alpha_df), 4)
        self.assertEqual(len(self.analyzer.realtime_pos_df), 4)
        self.assertEqual(len(self.analyzer.market_df), 2)

    def test_alpha_sum_consistency_pass(self):
        """Test alpha sum consistency checker with good data"""
        self.analyzer.load_data(self.temp_dir)
        checker = AlphaSumConsistencyChecker()

        result = checker.check(
            self.analyzer.incheck_alpha_df,
            self.analyzer.merged_df,
            self.analyzer.split_alpha_df,
            self.analyzer.realtime_pos_df,
            self.analyzer.market_df,
        )

        self.assertEqual(result.status, "PASS")
        self.assertIn("consistent alpha sums", result.message)

    def test_alpha_sum_consistency_fail(self):
        """Test alpha sum consistency checker with mismatched data"""
        self.analyzer.load_data(self.temp_dir)

        # Modify split data to create mismatch
        self.analyzer.split_alpha_df.loc[0, "volume"] = (
            15000  # Change from 14000 to 15000
        )

        checker = AlphaSumConsistencyChecker()
        result = checker.check(
            self.analyzer.incheck_alpha_df,
            self.analyzer.merged_df,
            self.analyzer.split_alpha_df,
            self.analyzer.realtime_pos_df,
            self.analyzer.market_df,
        )

        self.assertEqual(result.status, "FAIL")
        self.assertIn("sum mismatches", result.message)

    def test_non_negative_trader_pass(self):
        """Test non-negative trader checker with good data"""
        self.analyzer.load_data(self.temp_dir)
        checker = NonNegativeTraderChecker()

        result = checker.check(
            self.analyzer.incheck_alpha_df,
            self.analyzer.merged_df,
            self.analyzer.split_alpha_df,
            self.analyzer.realtime_pos_df,
            self.analyzer.market_df,
        )

        self.assertEqual(result.status, "PASS")
        self.assertIn("non-negative", result.message)

    def test_non_negative_trader_fail(self):
        """Test non-negative trader checker with negative volume"""
        self.analyzer.load_data(self.temp_dir)

        # Add negative volume
        self.analyzer.split_alpha_df.loc[0, "volume"] = -1000

        checker = NonNegativeTraderChecker()
        result = checker.check(
            self.analyzer.incheck_alpha_df,
            self.analyzer.merged_df,
            self.analyzer.split_alpha_df,
            self.analyzer.realtime_pos_df,
            self.analyzer.market_df,
        )

        self.assertEqual(result.status, "FAIL")
        self.assertIn("negative", result.message)

    def test_volume_rounding_pass(self):
        """Test volume rounding checker with properly rounded data"""
        self.analyzer.load_data(self.temp_dir)

        # Ensure all trade volumes are divisible by 100
        # Trade volume = split_volume - realtime_pos
        # Example: 14000 - 1200 = 12800 (divisible by 100)

        checker = VolumeRoundingChecker()
        result = checker.check(
            self.analyzer.incheck_alpha_df,
            self.analyzer.merged_df,
            self.analyzer.split_alpha_df,
            self.analyzer.realtime_pos_df,
            self.analyzer.market_df,
        )

        self.assertEqual(result.status, "PASS")
        self.assertIn("properly rounded", result.message)

    def test_volume_rounding_fail(self):
        """Test volume rounding checker with unrounded data"""
        self.analyzer.load_data(self.temp_dir)

        # Create unrounded trade volume: 14050 - 1200 = 12850 (not divisible by 100)
        self.analyzer.split_alpha_df.loc[0, "volume"] = 14050

        checker = VolumeRoundingChecker()
        result = checker.check(
            self.analyzer.incheck_alpha_df,
            self.analyzer.merged_df,
            self.analyzer.split_alpha_df,
            self.analyzer.realtime_pos_df,
            self.analyzer.market_df,
        )

        self.assertEqual(result.status, "FAIL")
        self.assertIn("not rounded", result.message)

    def test_time_preprocessing(self):
        """Test that nil_last_alpha gets converted to -1"""
        # Create data with nil_last_alpha
        nil_data = """event|alphaid|time|ticker|volume
InCheckAlphaEv|sSZE113BUCS|nil_last_alpha|000001.SZE|12000
InCheckAlphaEv|sSZE113BUCS|93000000|000001.SZE|14000"""

        # Write test file
        test_file = Path(self.temp_dir) / "InCheckAlphaEv.csv"
        with open(test_file, "w") as f:
            f.write(nil_data)

        # Create minimal required files
        minimal_merged = "event|alphaid|time|ticker|volume\n"
        minimal_split = "event|alphaid|time|ticker|volume\n"
        minimal_ctx = "event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol\n"

        with open(Path(self.temp_dir) / "MergedAlphaEv.csv", "w") as f:
            f.write(minimal_merged)
        with open(Path(self.temp_dir) / "SplitAlphaEv.csv", "w") as f:
            f.write(minimal_split)
        with open(Path(self.temp_dir) / "SplitCtxEv.csv", "w") as f:
            f.write(minimal_ctx)

        self.analyzer.load_data(self.temp_dir)

        # Check that nil_last_alpha was converted to -1
        time_values = self.analyzer.incheck_alpha_df["time"].unique()
        self.assertIn(-1, time_values)
        self.assertIn(93000000, time_values)

    def test_full_analyzer_workflow(self):
        """Test the complete analyzer workflow"""
        self.analyzer.load_data(self.temp_dir)

        # Run all checks
        results = self.analyzer.run_checks()

        # Should have 3 results (one per checker)
        self.assertEqual(len(results), 3)

        # All should pass with good data
        for result in results:
            self.assertEqual(result.status, "PASS")

        # Verify checker names
        checker_names = [r.checker_name for r in results]
        expected_names = [
            "Alpha Sum Consistency",
            "Non-Negative Split Alpha",
            "Volume Rounding (100 shares)",
        ]
        for name in expected_names:
            self.assertIn(name, checker_names)

    def test_missing_files_error(self):
        """Test that missing required files raise appropriate errors"""
        empty_dir = tempfile.mkdtemp()

        with self.assertRaises(FileNotFoundError):
            self.analyzer.load_data(empty_dir)

        import shutil

        shutil.rmtree(empty_dir)

    def test_data_summary(self):
        """Test data summary generation"""
        self.analyzer.load_data(self.temp_dir)
        summary = self.analyzer.get_data_summary()

        self.assertIsNotNone(summary)
        self.assertEqual(summary["incheck_events"], 1)  # One time event: 93000000
        self.assertEqual(summary["merged_events"], 1)
        self.assertEqual(summary["split_events"], 1)
        self.assertEqual(summary["position_events"], 1)
        self.assertEqual(summary["market_events"], 1)

        self.assertEqual(summary["incheck_tickers"], 2)  # 000001.SZE, 000002.SZE
        self.assertEqual(summary["merged_tickers"], 2)
        self.assertEqual(summary["split_tickers"], 2)


if __name__ == "__main__":
    unittest.main()
