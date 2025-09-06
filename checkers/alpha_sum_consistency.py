import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class AlphaSumConsistencyChecker(BaseChecker):
    """
    Checks that merged_alpha.sum == split_alpha.sum for each time event.
    The merged alpha represents the consolidated upstream alpha that should equal
    the sum of all split alphas distributed to traders.
    """

    def __init__(self, config=None):
        """Initialize with config dict to access global settings"""
        self.config = config or {}
        # Default tolerance if no config
        self.tolerance = 1e-6

    @property
    def name(self) -> str:
        return "Alpha Sum Consistency"

    def check(
        self,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> CheckResult:
        """Check that total merged alpha equals total split alpha for each time event"""

        # Get tolerance from config or use default
        tolerance = self.config.get("alpha_sum_tolerance", self.tolerance)

        # Group by time and sum volumes for merged and split alphas
        merged_sums = merged_df.groupby("time")["volume"].sum().round(6)
        split_sums = split_alpha_df.groupby("time")["volume"].sum().round(6)

        mismatches = []
        all_times = set(merged_sums.index) | set(split_sums.index)

        for time in sorted(all_times):
            merged_sum = merged_sums.get(time, 0.0)
            split_sum = split_sums.get(time, 0.0)

            # Check for mismatch (using configurable tolerance for floating point)
            if abs(merged_sum - split_sum) > tolerance:
                mismatches.append(
                    f"time={time}: merged_sum={merged_sum:.6f}, split_sum={split_sum:.6f}"
                )

        if mismatches:
            details = "\n".join(mismatches)
            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {len(mismatches)} time events with sum mismatches",
                details=details,
            )
        else:
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All {len(all_times)} time events have consistent alpha sums",
            )
