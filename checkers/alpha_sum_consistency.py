import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class AlphaSumConsistencyChecker(BaseChecker):
    """
    Checks that alphatype_alpha.sum == trader_alpha.sum for each ti event.
    Assumes input data represents alphatype alphas and output data represents trader alphas.
    """
    
    @property
    def name(self) -> str:
        return "Alpha Sum Consistency"
    
    def check(self, input_df: pd.DataFrame, output_df: pd.DataFrame, realtime_pos_df: pd.DataFrame) -> CheckResult:
        """Check that total input alpha equals total output alpha for each ti"""
        
        # Group by ti and sum targets for input (alphatype) and output (trader)
        input_sums = input_df.groupby('ti')['target'].sum().round(6)
        output_sums = output_df.groupby('ti')['target'].sum().round(6)
        
        mismatches = []
        all_tis = set(input_sums.index) | set(output_sums.index)
        
        for ti in sorted(all_tis):
            input_sum = input_sums.get(ti, 0.0)
            output_sum = output_sums.get(ti, 0.0)
            
            # Check for mismatch (using small tolerance for floating point)
            if abs(input_sum - output_sum) > 1e-6:
                mismatches.append(f"ti={ti}: input_sum={input_sum:.6f}, output_sum={output_sum:.6f}")
        
        if mismatches:
            details = "\n".join(mismatches)
            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {len(mismatches)} ti events with sum mismatches",
                details=details
            )
        else:
            return CheckResult(
                checker_name=self.name,
                status="PASS", 
                message=f"All {len(all_tis)} ti events have consistent alpha sums"
            )