import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class PMConstraintChecker(BaseChecker):
    """
    Checks T+1 settlement rule using SplitCtxEv data for available sellable volumes.
    
    T+1 Rule: Cannot sell shares bought on same day (T+1 settlement).
    
    Logic:
    1. Use realtime_avail_shot_vol from SplitCtxEv.csv as available sellable volume
    2. This volume already accounts for T+1 constraints and cross-PM merging
    3. For each sell trade, check if required_sell <= sum(available_sellable_volumes)
    4. The system pre-calculates sellable amounts considering the merging mechanism
    
    Data Source: SplitCtxEv.csv contains:
    - realtime_pos: Current position
    - realtime_avail_shot_vol: Available volume that can be sold (T+1 compliant)
    """
    
    def __init__(self, pm_virtual_pos_df=None):
        """Initialize - pm_virtual_pos_df parameter kept for compatibility"""
        pass  # We now use SplitCtxEv data directly from the check method parameters
    
    @property
    def name(self) -> str:
        return "PM T+1 Sellable Constraint"
    
    def check(self, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame, split_alpha_df: pd.DataFrame, 
              realtime_pos_df: pd.DataFrame, market_df: pd.DataFrame = None) -> CheckResult:
        """
        Check T+1 settlement rule using SplitCtxEv available sellable volume data
        
        Logic:
        1. Use realtime_avail_shot_vol from SplitCtxEv.csv for available sellable volume
        2. For each alpha target requiring selling, check against available volume
        3. The system already calculates T+1-compliant sellable amounts
        """
        
        violations = []
        
        # Get all time events to check (exclude closing positions)
        time_events = sorted([t for t in split_alpha_df['time'].unique() if t != -1])
        
        for time_event in time_events:
            # Get alpha targets for this time
            time_alphas = split_alpha_df[split_alpha_df['time'] == time_event]
            
            # Get available sellable volumes from SplitCtxEv for this time
            time_positions = realtime_pos_df[realtime_pos_df['time'] == time_event]
            
            # Group by ticker to check T+1 constraints
            for ticker in time_alphas['ticker'].unique():
                ticker_alphas = time_alphas[time_alphas['ticker'] == ticker]
                ticker_positions = time_positions[time_positions['ticker'] == ticker]
                
                # Calculate total alpha target for this ticker
                total_alpha_target = ticker_alphas['volume'].sum()
                
                # Calculate total current position and available sellable volume
                total_current_pos = ticker_positions['realtime_pos'].sum() if not ticker_positions.empty else 0
                total_available_sellable = ticker_positions['realtime_avail_shot_vol'].sum() if not ticker_positions.empty else 0
                
                # Calculate required trade volume
                trade_volume = total_alpha_target - total_current_pos
                
                # Check T+1 constraint for selling
                if trade_volume < 0:  # Selling required
                    required_sell = abs(trade_volume)
                    
                    if required_sell > total_available_sellable:
                        # Get trader-level details for violation reporting
                        trader_details = []
                        for _, pos_row in ticker_positions.iterrows():
                            trader_details.append(f"{pos_row['alphaid']}:{pos_row['realtime_avail_shot_vol']}")
                        
                        violations.append({
                            'time': time_event,
                            'ticker': ticker,
                            'total_alpha_target': total_alpha_target,
                            'total_current_pos': total_current_pos,
                            'required_sell': required_sell,
                            'available_sellable': total_available_sellable,
                            'excess_sell': required_sell - total_available_sellable,
                            'trader_details': trader_details
                        })
        
        if violations:
            details_lines = []
            total_violations = len(violations)
            total_excess = sum(v['excess_sell'] for v in violations)
            
            details_lines.append(f"Found {total_violations} T+1 settlement rule violations:")
            details_lines.append("(Using SplitCtxEv available sellable volumes)")
            
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
                        f"    {v['ticker']}: target={v['total_alpha_target']:.0f}, "
                        f"current_pos={v['total_current_pos']:.0f}, "
                        f"need_sell={v['required_sell']:.0f}, "
                        f"available={v['available_sellable']:.0f}, "
                        f"excess={v['excess_sell']:.0f}"
                    )
                    details_lines.append(f"      Trader sellable: {', '.join(v['trader_details'])}")
                
                if len(time_violations) > 5:
                    details_lines.append(f"    ... and {len(time_violations) - 5} more violations")
            
            details = "\n".join(details_lines)
            
            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {total_violations} T+1 settlement violations (total excess: {total_excess:.0f})",
                details=details
            )
        else:
            # Count total alpha targets checked
            total_checked = len(merged_df[merged_df['time'] != -1])
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All {total_checked} PM alpha targets respect T+1 settlement rule"
            )