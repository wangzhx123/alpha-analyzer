import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class NonNegativeTraderChecker(BaseChecker):
    """
    Checks that all split alpha volumes are non-negative for each time event.
    This checker examines the split output data to ensure no negative positions.
    """
    
    @property
    def name(self) -> str:
        return "Non-Negative Split Alpha"
    
    def check(self, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame, split_alpha_df: pd.DataFrame, 
              realtime_pos_df: pd.DataFrame, market_df: pd.DataFrame = None) -> CheckResult:
        """Check that all split alpha volumes are >= 0 for each time event"""
        
        # Find negative split alphas
        negative_alphas = split_alpha_df[split_alpha_df['volume'] < 0].copy()
        
        if len(negative_alphas) > 0:
            # Group by time to show violations per event
            violations_by_time = []
            
            for time in sorted(negative_alphas['time'].unique()):
                time_negatives = negative_alphas[negative_alphas['time'] == time]
                violations_by_time.append(
                    f"time={time}: {len(time_negatives)} negative volumes (min={time_negatives['volume'].min():.6f})"
                )
                
                # Show specific violations for this time (limit to 5 per time for readability)
                for _, row in time_negatives.head(5).iterrows():
                    violations_by_time.append(
                        f"    alphaid={row['alphaid']}, ticker={row['ticker']}, volume={row['volume']:.6f}"
                    )
                
                if len(time_negatives) > 5:
                    violations_by_time.append(f"    ... and {len(time_negatives) - 5} more")
            
            details = "\n".join(violations_by_time)
            
            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {len(negative_alphas)} negative split volumes across {len(negative_alphas['time'].unique())} time events",
                details=details
            )
        else:
            total_records = len(split_alpha_df)
            time_count = split_alpha_df['time'].nunique()
            
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All {total_records} split alpha volumes are non-negative across {time_count} time events"
            )