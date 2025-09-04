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
        """
        Check T+1 sellable constraints with intra-day virtual position tracking
        
        Enhanced Logic:
        1. Start with previous day closing virtual position (time = -1)
        2. Track virtual position changes chronologically through the day
        3. For each alpha target, check if required sell <= current accumulated virtual position
        4. Update virtual position after each time event for next constraint check
        """
        
        if self.pm_virtual_pos_df is None:
            return CheckResult(
                checker_name=self.name,
                status="ERROR",
                message="PM virtual position data not provided"
            )
        
        violations = []
        
        # Get all unique tickers to track
        all_tickers = set(merged_df['ticker'].unique()) | set(self.pm_virtual_pos_df['ticker'].unique())
        
        # For each ticker, track virtual position chronologically
        for ticker in all_tickers:
            # Initialize with previous day closing position
            ticker_vpos_data = self.pm_virtual_pos_df[self.pm_virtual_pos_df['ticker'] == ticker]
            closing_row = ticker_vpos_data[ticker_vpos_data['time'] == -1]
            
            if closing_row.empty:
                current_virtual_pos = 0  # No previous position
            else:
                current_virtual_pos = closing_row['virtual_position'].iloc[0]
            
            # Get all alpha targets for this ticker, sorted chronologically
            ticker_alphas = merged_df[
                (merged_df['ticker'] == ticker) & (merged_df['time'] != -1)
            ].sort_values('time')
            
            # Track position changes through the day
            for _, alpha_row in ticker_alphas.iterrows():
                time_event = alpha_row['time']
                target_position = alpha_row['volume']
                
                # Calculate required trade volume from current virtual position
                trade_volume = target_position - current_virtual_pos
                
                # Check T+1 constraint for selling
                if trade_volume < 0:  # Selling
                    required_sell = abs(trade_volume)
                    
                    # Available to sell = current virtual position (can't sell more than we have)
                    available_to_sell = max(0, current_virtual_pos)
                    
                    if required_sell > available_to_sell:
                        violations.append({
                            'time': time_event,
                            'ticker': ticker,
                            'target_position': target_position,
                            'current_virtual_pos': current_virtual_pos,
                            'required_sell': required_sell,
                            'available_to_sell': available_to_sell,
                            'excess_sell': required_sell - available_to_sell,
                            'trade_volume': trade_volume
                        })
                
                # Update virtual position for next time event
                # (Assuming the alpha target represents the achieved virtual position)
                current_virtual_pos = target_position
        
        if violations:
            details_lines = []
            total_violations = len(violations)
            total_excess = sum(v['excess_sell'] for v in violations)
            
            details_lines.append(f"Found {total_violations} T+1 constraint violations (intra-day tracking):")
            
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
                        f"vpos_before={v['current_virtual_pos']:.0f}, "
                        f"trade={v['trade_volume']:.0f}, "
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
            # Count total alpha targets checked
            total_checked = len(merged_df[merged_df['time'] != -1])
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All {total_checked} PM alpha targets respect T+1 sellable constraints (intra-day tracking)"
            )