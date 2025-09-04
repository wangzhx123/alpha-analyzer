import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class PMConstraintChecker(BaseChecker):
    """
    Checks T+1 rule: PM cannot sell more than available from previous day position.
    
    Logic:
    1. Get PM virtual position at closing (time = -1, nil_last_alpha)
    2. For each current alpha target, calculate required trade volume:
       trade_volume = target_alpha - current_virtual_position
    3. If trade_volume < 0 (selling), check if abs(trade_volume) <= available_position
    """
    
    def __init__(self, pm_virtual_pos_df=None):
        """Initialize with PM virtual position data"""
        self.pm_virtual_pos_df = pm_virtual_pos_df
    
    @property
    def name(self) -> str:
        return "PM T+1 Sellable Constraint"
    
    def check(self, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame, split_alpha_df: pd.DataFrame, 
              realtime_pos_df: pd.DataFrame, market_df: pd.DataFrame = None) -> CheckResult:
        """Check that PM selling doesn't exceed available position from previous day"""
        
        if self.pm_virtual_pos_df is None:
            return CheckResult(
                checker_name=self.name,
                status="ERROR",
                message="PM virtual position data not provided"
            )
        
        # Get closing positions (time = -1, represents previous day closing)
        closing_positions = self.pm_virtual_pos_df[self.pm_virtual_pos_df['time'] == -1]
        
        # Get current day merged alphas (target positions)
        current_alphas = merged_df[merged_df['time'] != -1]
        
        # Get current PM virtual positions for trade volume calculation
        current_positions = self.pm_virtual_pos_df[self.pm_virtual_pos_df['time'] != -1]
        
        violations = []
        
        # Group by time to check each time event
        for time_event in sorted(current_alphas['time'].unique()):
            time_alphas = current_alphas[current_alphas['time'] == time_event]
            time_positions = current_positions[current_positions['time'] == time_event]
            
            for _, alpha_row in time_alphas.iterrows():
                ticker = alpha_row['ticker']
                target_position = alpha_row['volume']  # Target absolute position
                
                # Find current virtual position for this ticker at this time
                current_pos_row = time_positions[time_positions['ticker'] == ticker]
                if current_pos_row.empty:
                    # If no current position, assume 0
                    current_virtual_pos = 0
                else:
                    current_virtual_pos = current_pos_row['virtual_position'].iloc[0]
                
                # Calculate required trade volume
                trade_volume = target_position - current_virtual_pos
                
                # Check constraint only for selling (negative trade volume)
                if trade_volume < 0:
                    # Find available position from previous day closing
                    closing_row = closing_positions[closing_positions['ticker'] == ticker]
                    
                    if closing_row.empty:
                        available_to_sell = 0
                    else:
                        available_to_sell = closing_row['virtual_position'].iloc[0]
                    
                    # Check if selling more than available
                    required_sell = abs(trade_volume)
                    if required_sell > available_to_sell:
                        violations.append({
                            'time': time_event,
                            'ticker': ticker,
                            'target_position': target_position,
                            'current_position': current_virtual_pos,
                            'required_sell': required_sell,
                            'available_to_sell': available_to_sell,
                            'excess_sell': required_sell - available_to_sell
                        })
        
        if violations:
            details_lines = []
            total_violations = len(violations)
            total_excess = sum(v['excess_sell'] for v in violations)
            
            details_lines.append(f"Found {total_violations} T+1 constraint violations:")
            
            # Group by time for better readability
            violations_by_time = {}
            for v in violations:
                time_key = v['time']
                if time_key not in violations_by_time:
                    violations_by_time[time_key] = []
                violations_by_time[time_key].append(v)
            
            for time_event in sorted(violations_by_time.keys()):
                time_violations = violations_by_time[time_event]
                details_lines.append(f"  time={time_event}: {len(time_violations)} violations")
                
                for v in time_violations[:5]:  # Show first 5 violations per time
                    details_lines.append(
                        f"    {v['ticker']}: target={v['target_position']:.0f}, "
                        f"current={v['current_position']:.0f}, "
                        f"need_sell={v['required_sell']:.0f}, "
                        f"available={v['available_to_sell']:.0f}, "
                        f"excess={v['excess_sell']:.0f}"
                    )
                
                if len(time_violations) > 5:
                    details_lines.append(f"    ... and {len(time_violations) - 5} more violations")
            
            details = "\n".join(details_lines)
            
            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {total_violations} T+1 constraint violations (total excess: {total_excess:.0f})",
                details=details
            )
        else:
            total_checked = len(current_alphas)
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All {total_checked} PM alpha targets respect T+1 sellable constraints"
            )