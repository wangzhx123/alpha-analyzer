import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class VolumeRoundingChecker(BaseChecker):
    """
    Checks that allocated trade volumes are rounded to 100 shares.
    Trade volume = split volume - realtime position
    For each trader (alphaid) and ticker combination, verifies trade volume is divisible by 100.
    """
    
    @property
    def name(self) -> str:
        return "Volume Rounding (100 shares)"
    
    def check(self, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame, split_alpha_df: pd.DataFrame, 
              realtime_pos_df: pd.DataFrame, market_df: pd.DataFrame = None) -> CheckResult:
        """Check that all trade volumes (split_volume - realtime_pos) are rounded to 100 shares"""
        
        # Merge split alphas with positions on time, alphaid, ticker
        merged = split_alpha_df.merge(
            realtime_pos_df, 
            on=['time', 'alphaid', 'ticker'], 
            how='left', 
            suffixes=('', '_pos')
        )
        
        # Handle missing realtime positions (assume 0 if not found)
        merged['realtime_pos'] = merged['realtime_pos'].fillna(0.0)
        
        # Calculate trade volume = split_volume - realtime_pos
        merged['trade_volume'] = merged['volume'] - merged['realtime_pos']
        
        # Find volumes that are not rounded to 100 shares
        # Use modulo 100 with small tolerance for floating point precision
        tolerance = 1e-6
        unrounded_volumes = merged[abs(merged['trade_volume'] % 100) > tolerance].copy()
        
        if len(unrounded_volumes) > 0:
            # Group by time to show violations per event
            violations_by_time = []
            
            for time in sorted(unrounded_volumes['time'].unique()):
                time_violations = unrounded_volumes[unrounded_volumes['time'] == time]
                violations_by_time.append(
                    f"time={time}: {len(time_violations)} unrounded volumes"
                )
                
                # Show specific violations for this time (limit to 5 per time for readability)
                for _, row in time_violations.head(5).iterrows():
                    remainder = row['trade_volume'] % 100
                    violations_by_time.append(
                        f"    alphaid={row['alphaid']}, ticker={row['ticker']}: "
                        f"split={row['volume']:.1f}, pos={row['realtime_pos']:.1f}, "
                        f"trade_vol={row['trade_volume']:.1f} (remainder={remainder:.1f})"
                    )
                
                if len(time_violations) > 5:
                    violations_by_time.append(f"    ... and {len(time_violations) - 5} more")
            
            details = "\n".join(violations_by_time)
            
            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {len(unrounded_volumes)} trade volumes not rounded to 100 shares across {len(unrounded_volumes['time'].unique())} time events",
                details=details
            )
        else:
            total_trades = len(merged)
            time_count = merged['time'].nunique()
            
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All {total_trades} trade volumes are properly rounded to 100 shares across {time_count} time events"
            )