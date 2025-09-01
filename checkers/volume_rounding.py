import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class VolumeRoundingChecker(BaseChecker):
    """
    Checks that allocated trade volumes are rounded to 100 shares.
    Trade volume = alpha target - realtime position
    For each trader (sid) and ticker combination, verifies trade volume is divisible by 100.
    """
    
    @property
    def name(self) -> str:
        return "Volume Rounding (100 shares)"
    
    def check(self, input_df: pd.DataFrame, output_df: pd.DataFrame, realtime_pos_df: pd.DataFrame) -> CheckResult:
        """Check that all trade volumes (target - realtime_pos) are rounded to 100 shares"""
        
        # Merge output (trader alphas) with realtime positions on ti, sid, ticker
        merged = output_df.merge(
            realtime_pos_df, 
            on=['ti', 'sid', 'ticker'], 
            how='left', 
            suffixes=('', '_pos')
        )
        
        # Handle missing realtime positions (assume 0 if not found)
        merged['realtime_pos'] = merged['realtime_pos'].fillna(0.0)
        
        # Calculate trade volume = target - realtime_pos
        merged['trade_volume'] = merged['target'] - merged['realtime_pos']
        
        # Find volumes that are not rounded to 100 shares
        # Use modulo 100 with small tolerance for floating point precision
        tolerance = 1e-6
        unrounded_volumes = merged[abs(merged['trade_volume'] % 100) > tolerance].copy()
        
        if len(unrounded_volumes) > 0:
            # Group by ti to show violations per event
            violations_by_ti = []
            
            for ti in sorted(unrounded_volumes['ti'].unique()):
                ti_violations = unrounded_volumes[unrounded_volumes['ti'] == ti]
                violations_by_ti.append(
                    f"ti={ti}: {len(ti_violations)} unrounded volumes"
                )
                
                # Show specific violations for this ti (limit to 5 per ti for readability)
                for _, row in ti_violations.head(5).iterrows():
                    remainder = row['trade_volume'] % 100
                    violations_by_ti.append(
                        f"    sid={row['sid']}, ticker={row['ticker']}: "
                        f"target={row['target']:.1f}, pos={row['realtime_pos']:.1f}, "
                        f"volume={row['trade_volume']:.1f} (remainder={remainder:.1f})"
                    )
                
                if len(ti_violations) > 5:
                    violations_by_ti.append(f"    ... and {len(ti_violations) - 5} more")
            
            details = "\n".join(violations_by_ti)
            
            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {len(unrounded_volumes)} trade volumes not rounded to 100 shares across {len(unrounded_volumes['ti'].unique())} ti events",
                details=details
            )
        else:
            total_trades = len(merged)
            ti_count = merged['ti'].nunique()
            
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All {total_trades} trade volumes are properly rounded to 100 shares across {ti_count} ti events"
            )