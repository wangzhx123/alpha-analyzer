import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult


class PMConstraintChecker(BaseChecker):
    """
    Checks T+1 settlement rule: PM cannot sell shares bought on the same day.
    
    T+1 Rule: You must hold positions for at least 1 day before selling.
    
    Logic:
    1. Start with previous day closing position (settled shares that can be sold)
    2. Track intra-day net buys/sells to maintain available sellable quantity
    3. Available to sell = previous_day_position + min(0, net_intraday_trade)
    4. For each sell trade, check if sell_volume <= available_sellable_shares
    
    Example:
    - Previous day: 8000 shares
    - Today 9:30: Sell 2000 → Available: 8000 - 2000 = 6000 
    - Today 9:31: Buy 2000 → Available: still 6000 (can't sell same-day buys)
    - Today 9:32: Try sell 7000 → VIOLATION (only 6000 available)
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
        Check T+1 settlement rule: Cannot sell shares bought on same day
        
        T+1 Logic:
        1. Start with previous day closing position (fully settled, sellable)
        2. For each trade chronologically:
           - If selling: reduce available sellable shares
           - If buying: do NOT increase available sellable shares (T+1 rule)
        3. Available_to_sell = previous_day_position + min(0, cumulative_net_trades)
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
        
        # For each ticker, track T+1 constraint
        for ticker in all_tickers:
            # Initialize with previous day closing position (settled shares)
            ticker_vpos_data = self.pm_virtual_pos_df[self.pm_virtual_pos_df['ticker'] == ticker]
            closing_row = ticker_vpos_data[ticker_vpos_data['time'] == -1]
            
            if closing_row.empty:
                previous_day_position = 0  # No previous settled position
            else:
                previous_day_position = closing_row['virtual_position'].iloc[0]
            
            # Available to sell starts with previous day position
            available_to_sell = previous_day_position
            current_virtual_pos = previous_day_position
            
            # Get all alpha targets for this ticker, sorted chronologically
            ticker_alphas = merged_df[
                (merged_df['ticker'] == ticker) & (merged_df['time'] != -1)
            ].sort_values('time')
            
            # Track T+1 constraint through the day
            for _, alpha_row in ticker_alphas.iterrows():
                time_event = alpha_row['time']
                target_position = alpha_row['volume']
                
                # Calculate required trade volume
                trade_volume = target_position - current_virtual_pos
                
                # Check T+1 constraint for selling
                if trade_volume < 0:  # Selling
                    required_sell = abs(trade_volume)
                    
                    if required_sell > available_to_sell:
                        violations.append({
                            'time': time_event,
                            'ticker': ticker,
                            'target_position': target_position,
                            'previous_day_position': previous_day_position,
                            'current_virtual_pos': current_virtual_pos,
                            'required_sell': required_sell,
                            'available_to_sell': available_to_sell,
                            'excess_sell': required_sell - available_to_sell,
                            'trade_volume': trade_volume
                        })
                    else:
                        # Update available after successful sell (reduces sellable shares)
                        available_to_sell -= required_sell
                
                elif trade_volume > 0:  # Buying
                    # Buying does NOT increase available_to_sell due to T+1 rule
                    # New shares cannot be sold until next day
                    pass
                
                # Update current virtual position for next iteration
                current_virtual_pos = target_position
        
        if violations:
            details_lines = []
            total_violations = len(violations)
            total_excess = sum(v['excess_sell'] for v in violations)
            
            details_lines.append(f"Found {total_violations} T+1 settlement rule violations:")
            details_lines.append("(Cannot sell shares bought on same day)")
            
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
                        f"    {v['ticker']}: prev_day={v['previous_day_position']:.0f}, "
                        f"current_pos={v['current_virtual_pos']:.0f}, "
                        f"need_sell={v['required_sell']:.0f}, "
                        f"sellable={v['available_to_sell']:.0f}, "
                        f"excess={v['excess_sell']:.0f}"
                    )
                
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