import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class NonNegativeTraderChecker(BaseChecker):
    """
    Checks that all trader alpha targets are non-negative for each ti event.
    This checker only examines the output data (trader alphas).
    """
    
    @property
    def name(self) -> str:
        return "Non-Negative Trader Alpha"
    
    def check(self, input_df: pd.DataFrame, output_df: pd.DataFrame, realtime_pos_df: pd.DataFrame) -> CheckResult:
        """Check that all trader alpha targets are >= 0 for each ti"""
        
        # Find negative trader alphas
        negative_alphas = output_df[output_df['target'] < 0].copy()
        
        if len(negative_alphas) > 0:
            # Group by ti to show violations per event
            violations_by_ti = []
            
            for ti in sorted(negative_alphas['ti'].unique()):
                ti_negatives = negative_alphas[negative_alphas['ti'] == ti]
                violations_by_ti.append(
                    f"ti={ti}: {len(ti_negatives)} negative alphas (min={ti_negatives['target'].min():.6f})"
                )
                
                # Show specific violations for this ti (limit to 5 per ti for readability)
                for _, row in ti_negatives.head(5).iterrows():
                    violations_by_ti.append(
                        f"    sid={row['sid']}, ticker={row['ticker']}, target={row['target']:.6f}"
                    )
                
                if len(ti_negatives) > 5:
                    violations_by_ti.append(f"    ... and {len(ti_negatives) - 5} more")
            
            details = "\n".join(violations_by_ti)
            
            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {len(negative_alphas)} negative trader alphas across {len(negative_alphas['ti'].unique())} ti events",
                details=details
            )
        else:
            total_records = len(output_df)
            ti_count = output_df['ti'].nunique()
            
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All {total_records} trader alphas are non-negative across {ti_count} ti events"
            )