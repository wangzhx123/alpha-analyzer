import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class DirectionConsistencyChecker(BaseChecker):
    """
    Validates that traders strictly follow trade direction consistency.
    Rules 27, 66: If trade direction is buy, then next position should only be
    larger than or equal to current position (and vice versa for sell).
    """

    @property
    def name(self) -> str:
        return "Trade Direction Consistency"

    def check(
        self,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> CheckResult:
        """Check that position changes respect trade direction consistency"""

        violations = []
        total_trades = 0
        valid_trades = 0

        # Get unique time periods sorted
        time_periods = sorted(realtime_pos_df['time'].unique())

        for i in range(len(time_periods) - 1):
            current_time = time_periods[i]
            next_time = time_periods[i + 1]

            # Get positions at current and next time
            current_positions = realtime_pos_df[realtime_pos_df['time'] == current_time]
            next_positions = realtime_pos_df[realtime_pos_df['time'] == next_time]

            # Get alpha targets at current time (targets for next period)
            current_alphas = split_alpha_df[split_alpha_df['time'] == current_time]

            # Merge to get target, current position, and next position
            merged_data = current_alphas.merge(
                current_positions[['alphaid', 'ticker', 'realtime_pos']],
                on=['alphaid', 'ticker'],
                how='inner',
                suffixes=('', '_current')
            ).merge(
                next_positions[['alphaid', 'ticker', 'realtime_pos']],
                on=['alphaid', 'ticker'],
                how='inner',
                suffixes=('_current', '_next')
            )

            for _, row in merged_data.iterrows():
                target_pos = row['volume']
                current_pos = row['realtime_pos_current'] if pd.notna(row['realtime_pos_current']) else 0
                next_pos = row['realtime_pos_next'] if pd.notna(row['realtime_pos_next']) else 0

                total_trades += 1

                # Determine intended trade direction
                intended_trade = target_pos - current_pos
                actual_trade = next_pos - current_pos

                # Skip if no intended trade
                if abs(intended_trade) < 1e-6:
                    valid_trades += 1
                    continue

                # Check direction consistency
                direction_violation = False

                if intended_trade > 0:  # Buy direction
                    # Next position should be >= current position
                    if next_pos < current_pos - 1e-6:  # Allow small floating point tolerance
                        direction_violation = True
                        violation_type = "BUY_DECREASED"
                elif intended_trade < 0:  # Sell direction
                    # Next position should be <= current position
                    if next_pos > current_pos + 1e-6:  # Allow small floating point tolerance
                        direction_violation = True
                        violation_type = "SELL_INCREASED"

                if direction_violation:
                    violations.append({
                        'time_period': f"{current_time}→{next_time}",
                        'alphaid': row['alphaid'],
                        'ticker': row['ticker'],
                        'target_pos': target_pos,
                        'current_pos': current_pos,
                        'next_pos': next_pos,
                        'intended_trade': intended_trade,
                        'actual_trade': actual_trade,
                        'violation_type': violation_type
                    })
                else:
                    valid_trades += 1

        if violations:
            # Group violations by type and time period
            buy_violations = [v for v in violations if v['violation_type'] == 'BUY_DECREASED']
            sell_violations = [v for v in violations if v['violation_type'] == 'SELL_INCREASED']

            details_lines = []

            if buy_violations:
                details_lines.append(f"BUY Direction Violations ({len(buy_violations)}):")
                violations_by_time = {}
                for v in buy_violations:
                    period = v['time_period']
                    if period not in violations_by_time:
                        violations_by_time[period] = []
                    violations_by_time[period].append(v)

                for period in sorted(violations_by_time.keys())[:3]:  # Show first 3 time periods
                    period_violations = violations_by_time[period]
                    details_lines.append(f"  {period}: {len(period_violations)} violations")

                    for v in period_violations[:2]:  # Show first 2 per time period
                        details_lines.append(
                            f"    {v['alphaid']}/{v['ticker']}: {v['current_pos']:.0f}→{v['next_pos']:.0f} "
                            f"(intended buy {v['intended_trade']:.0f}, but position decreased)"
                        )

            if sell_violations:
                details_lines.append(f"SELL Direction Violations ({len(sell_violations)}):")
                violations_by_time = {}
                for v in sell_violations:
                    period = v['time_period']
                    if period not in violations_by_time:
                        violations_by_time[period] = []
                    violations_by_time[period].append(v)

                for period in sorted(violations_by_time.keys())[:3]:  # Show first 3 time periods
                    period_violations = violations_by_time[period]
                    details_lines.append(f"  {period}: {len(period_violations)} violations")

                    for v in period_violations[:2]:  # Show first 2 per time period
                        details_lines.append(
                            f"    {v['alphaid']}/{v['ticker']}: {v['current_pos']:.0f}→{v['next_pos']:.0f} "
                            f"(intended sell {v['intended_trade']:.0f}, but position increased)"
                        )

            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {len(violations)} direction consistency violations out of {total_trades} total trades",
                details="\n".join(details_lines)
            )
        else:
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All {valid_trades} trades follow correct direction consistency (buy increases positions, sell decreases positions)"
            )