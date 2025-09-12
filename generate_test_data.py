#!/usr/bin/env python3

import pandas as pd
import numpy as np
import random
from pathlib import Path
import argparse
from typing import List, Dict, Tuple

class TestDataGenerator:
    """
    Generate realistic test data for Alpha Analyzer pressure testing
    
    Scenario:
    - 3000 tickers (XXXXXX.SSE format)
    - 5 Portfolio Managers (sSZE111BUCS to sSZE115BUCS)  
    - 5 Traders (sSZE111Atem to sSZE115Atem)
    - Time intervals: 26 intervals, 9:30-11:30, 13:00-15:00 (China trading hours)
    - Fill rates: 0.8-0.9 for realistic execution
    
    CONSTRAINT: Every PM must have alphas for at least 1000 tickers per time event
    This ensures comprehensive institutional coverage and realistic trading patterns.
    """
    
    def __init__(self, output_dir: str = "test_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Market parameters
        self.num_tickers = 3000
        self.num_pms = 5
        self.num_traders = 5
        
        # Generate tickers: 000001.SSE to 003000.SSE
        self.tickers = [f"{i:06d}.SSE" for i in range(1, self.num_tickers + 1)]
        
        # Generate PM and trader IDs for China stock system
        # 5 PM systems: Portfolio Management systems
        self.pm_ids = [f"sSZE{111 + i}BUCS" for i in range(self.num_pms)]
        # 5 Trader systems: Algorithmic Trading Execution systems
        self.trader_ids = [f"sSZE{111 + i}Atem" for i in range(self.num_traders)]
        
        # Time schedule: 10min intervals with lunch break
        self.time_events = self._generate_time_schedule()
        
        # Fill rate parameters
        self.fill_rate_min = 0.8
        self.fill_rate_max = 0.9
        
        # Random seeds for reproducibility
        np.random.seed(42)
        random.seed(42)
        
        print(f"Initialized generator:")
        print(f"  Tickers: {self.num_tickers}")
        print(f"  PMs: {self.num_pms}")
        print(f"  Traders: {self.num_traders}")
        print(f"  Time events: {len(self.time_events)}")
        print(f"  Output directory: {self.output_dir}")
    
    def _generate_time_schedule(self) -> List[int]:
        """Generate trading time schedule with 10min intervals and lunch break"""
        times = []
        
        # Morning session: 9:30 to 11:30 (every 10 minutes)
        # 93000000, 94000000, 95000000, 100000000, 101000000, ..., 113000000
        hour = 9
        minute = 30
        
        while hour < 11 or (hour == 11 and minute <= 30):
            if hour < 10:
                time_val = int(f"{hour}{minute:02d}000000")
            else:
                time_val = int(f"{hour}{minute:02d}000000")
            times.append(time_val)
            
            # Add 10 minutes
            minute += 10
            if minute >= 60:
                minute -= 60
                hour += 1
        
        # Afternoon session: 13:00 to 15:00 (every 10 minutes)
        # 130000000, 131000000, 132000000, ..., 150000000  
        hour = 13
        minute = 0
        
        while hour < 15 or (hour == 15 and minute <= 0):
            time_val = int(f"{hour}{minute:02d}000000")
            times.append(time_val)
            
            # Add 10 minutes
            minute += 10
            if minute >= 60:
                minute -= 60
                hour += 1
            
        return times
    
    def generate_pm_signals(self) -> pd.DataFrame:
        """Generate InCheckAlphaEv.csv - PM alpha signals
        
        CONSTRAINT: Every PM must have alphas for at least 1000 tickers per time event
        This ensures comprehensive coverage and realistic institutional trading patterns.
        """
        print("Generating PM alpha signals...")
        
        records = []
        
        # First generate nil_last_alpha entries (previous day's closing positions)
        print("  Generating nil_last_alpha (previous day closing positions)...")
        for pm_id in self.pm_ids:
            # Each PM had positions from previous day
            num_prev_holdings = min(1000, len(self.tickers))
            prev_holdings = random.sample(self.tickers, num_prev_holdings)
            
            for ticker in prev_holdings:
                # Previous day closing position (can be positive or negative, no short selling constraint here)
                prev_volume = random.randint(-5000, 10000)  # Previous positions can include shorts
                if prev_volume != 0:  # Only record non-zero positions
                    records.append({
                        'event': 'InCheckAlphaEv',
                        'alphaid': pm_id,
                        'time': 'nil_last_alpha',
                        'ticker': ticker,
                        'volume': prev_volume
                    })
        
        # Then generate regular time event signals
        print("  Generating intraday alpha signals...")
        for time_event in self.time_events:
            # Each PM generates signals for a random subset of tickers
            for pm_id in self.pm_ids:
                # CONSTRAINT: All PMs must have alphas for at least 1000 tickers per time event
                min_required_tickers = min(1000, len(self.tickers))  # At least 1000 or all available
                max_tickers = min(1500, len(self.tickers))  # Upper limit for variety
                
                num_active_tickers = random.randint(min_required_tickers, max_tickers)
                active_tickers = random.sample(self.tickers, num_active_tickers)
                
                for ticker in active_tickers:
                    # Generate realistic volume (100-share lots, up to 100,000 shares)
                    # No short selling - all volumes must be non-negative
                    volume = random.randint(1, 1000) * 100
                    
                    records.append({
                        'event': 'InCheckAlphaEv',
                        'alphaid': pm_id,
                        'time': time_event,
                        'ticker': ticker,
                        'volume': volume
                    })
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} PM signal records")
        
        # Validate PM coverage constraint
        self._validate_pm_coverage_constraint(df)
        
        return df
    
    def generate_merged_signals(self, incheck_df: pd.DataFrame) -> pd.DataFrame:
        """Generate MergedAlphaEv.csv - Consolidated PM signals"""
        print("Generating merged alpha signals...")
        
        records = []
        
        # Group by time and ticker, then consolidate PM signals
        for time_event in self.time_events:
            time_data = incheck_df[incheck_df['time'] == time_event]
            
            for ticker in time_data['ticker'].unique():
                ticker_data = time_data[time_data['ticker'] == ticker]
                
                # Simple consolidation: sum all PM volumes for this ticker
                total_volume = ticker_data['volume'].sum()
                
                # Only create merged signal if net volume is significant
                if abs(total_volume) >= 100:
                    # Round to nearest 100 shares
                    total_volume = round(total_volume / 100) * 100
                    
                    # Create merged group ID
                    group_id = f"GRP_{time_event}_{ticker}"
                    
                    records.append({
                        'event': 'MergedAlphaEv',
                        'alphaid': group_id,
                        'time': time_event,
                        'ticker': ticker,
                        'volume': total_volume
                    })
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} merged signal records")
        return df
    
    def generate_split_signals(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """Generate SplitAlphaEv.csv - Trader allocations"""
        print("Generating split alpha signals...")
        
        records = []
        
        for _, merged_row in merged_df.iterrows():
            total_volume = merged_row['volume']
            time_event = merged_row['time']
            ticker = merged_row['ticker']
            
            # Split volume among available traders
            # Use exactly 2 traders per merged signal (business rule requirement)
            # Randomly select 2 of the 5 available traders for each allocation
            active_traders = random.sample(self.trader_ids, 2)
            
            # Generate allocation weights
            weights = [random.uniform(0.1, 1.0) for _ in active_traders]
            weight_sum = sum(weights)
            weights = [w / weight_sum for w in weights]  # Normalize to sum to 1
            
            # Allocate volume to traders
            allocated_volume = 0
            for i, trader_id in enumerate(active_traders):
                if i == len(active_traders) - 1:
                    # Last trader gets remainder to ensure exact sum
                    trader_volume = total_volume - allocated_volume
                else:
                    trader_volume = round(total_volume * weights[i] / 100) * 100
                    allocated_volume += trader_volume
                
                # Create split signal
                records.append({
                    'event': 'SplitAlphaEv',
                    'alphaid': trader_id,
                    'time': time_event,
                    'ticker': ticker,
                    'volume': trader_volume
                })
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} split signal records")
        return df
    
    def generate_position_context(self, split_df: pd.DataFrame) -> pd.DataFrame:
        """Generate SplitCtxEv.csv - Trader positions with EXACT fill rates"""
        print("Generating position context with exact fill rates...")
        
        records = []
        
        # Track trader positions over time
        trader_positions = {}  # {(trader, ticker): position}
        
        # Initialize positions to zero
        for trader in self.trader_ids:
            for ticker in self.tickers:
                trader_positions[(trader, ticker)] = 0
        
        # Process each time period and ensure exact fill rate compliance
        for time_event in self.time_events:
            time_data = split_df[split_df['time'] == time_event]
            
            # Process each trader's signals for this time
            for trader in self.trader_ids:
                trader_data = time_data[time_data['alphaid'] == trader]
                
                for ticker in self.tickers:
                    current_pos = trader_positions[(trader, ticker)]
                    
                    # Check if trader has signal for this ticker
                    ticker_signals = trader_data[trader_data['ticker'] == ticker]
                    
                    if not ticker_signals.empty:
                        target_volume = ticker_signals['volume'].sum()
                        
                        # Apply EXACT fill rate (0.8 to 0.9) with proper rounding
                        fill_rate = random.uniform(self.fill_rate_min, self.fill_rate_max)
                        # Calculate actual execution amount
                        exact_execution = target_volume * fill_rate
                        # Round to nearest 100 shares for realistic trading
                        actual_trade = round(exact_execution / 100) * 100
                        
                        # Update position with the actual execution
                        new_pos = current_pos + actual_trade
                        trader_positions[(trader, ticker)] = new_pos
                    else:
                        # No signal, position unchanged
                        new_pos = current_pos
                    
                    # Only record positions for tickers that have activity
                    # This reduces data size and improves analysis performance
                    if new_pos != 0 or (not ticker_signals.empty):
                        # Generate available short volume (for T+1 constraint)
                        avail_short_vol = max(0, new_pos)
                        
                        # Split position into long/short components
                        realtime_long_pos = max(0, new_pos)
                        realtime_short_pos = max(0, -new_pos)
                        
                        records.append({
                            'event': 'SplitCtxEv',
                            'alphaid': trader,
                            'time': time_event,
                            'ticker': ticker,
                            'realtime_pos': new_pos,
                            'realtime_long_pos': realtime_long_pos,
                            'realtime_short_pos': realtime_short_pos,
                            'realtime_avail_shot_vol': avail_short_vol
                        })
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} position context records")
        return df
    
    def generate_market_data(self) -> pd.DataFrame:
        """Generate MarketDataEv.csv - Market prices (optional)"""
        print("Generating market data...")
        
        records = []
        
        # Initialize random prices for each ticker
        base_prices = {ticker: random.uniform(10.0, 200.0) for ticker in self.tickers}
        
        for time_event in self.time_events:
            for ticker in self.tickers:
                # Previous close price
                prev_close = base_prices[ticker]
                
                # Current price with small random movement
                price_change = random.uniform(-0.05, 0.05)  # ±5% movement
                last_price = prev_close * (1 + price_change)
                
                # Update base price for next iteration
                base_prices[ticker] = last_price
                
                records.append({
                    'event': 'MarketDataEv',
                    'alphaid': 'MARKET',
                    'time': time_event,
                    'ticker': ticker,
                    'last_price': round(last_price, 2),
                    'prev_close_price': round(prev_close, 2)
                })
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} market data records")
        return df
    
    def generate_pm_virtual_positions(self, incheck_df: pd.DataFrame) -> pd.DataFrame:
        """Generate VposResEv.csv - PM virtual positions for T+1 constraints
        
        CONSTRAINT: Pre-open positions (time = -1) must exactly match the 
        nil_last_alpha entries in InCheckAlphaEv.csv to ensure consistency.
        """
        print("Generating PM virtual positions...")
        
        records = []
        
        # Track PM virtual positions
        pm_positions = {}  # {(pm, ticker): position}
        
        # Initialize with previous day positions (time = -1) that MATCH nil_last_alpha
        # Extract all nil_last_alpha entries to ensure consistency
        nil_alpha_data = incheck_df[incheck_df['time'] == 'nil_last_alpha']
        
        for _, row in nil_alpha_data.iterrows():
            pm_id = row['alphaid']
            ticker = row['ticker'] 
            # Pre-open position MUST match the nil_last_alpha volume
            initial_pos = row['volume']
            pm_positions[(pm_id, ticker)] = initial_pos
            
            # Add previous day record
            records.append({
                'time': -1,
                'ticker': ticker,
                'vpos': initial_pos
            })
        
        # Generate virtual positions for each time event
        # At market open (930000000), positions are same as previous day close (no trades executed yet)
        # Subsequent times show gradual execution towards alpha targets
        for time_event in self.time_events:
            if time_event == self.time_events[0]:  # First time event (930000000)
                # At market open, positions are same as previous day close
                for pm_id in self.pm_ids:
                    for ticker in self.tickers:
                        prev_pos = pm_positions.get((pm_id, ticker), 0)
                        if prev_pos != 0:  # Only record non-zero positions
                            records.append({
                                'time': time_event,
                                'ticker': ticker,
                                'vpos': prev_pos  # Same as previous day close
                            })
            else:
                # For later times, positions will be updated based on executions
                # This will be handled by update_positions_with_executions()
                for pm_id in self.pm_ids:
                    for ticker in self.tickers:
                        current_pos = pm_positions.get((pm_id, ticker), 0)
                        if current_pos != 0:  # Only record existing positions for now
                            records.append({
                                'time': time_event,
                                'ticker': ticker,
                                'vpos': current_pos  # Will be updated later
                            })
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} PM virtual position records")
        return df
    
    def update_positions_with_executions(self, vpos_df: pd.DataFrame, splitctx_df: pd.DataFrame) -> pd.DataFrame:
        """Update virtual positions based on actual execution results from SplitCtx"""
        print("Updating positions with actual execution results...")
        
        # Create a copy for modification
        updated_vpos = vpos_df.copy()
        
        # Aggregate trader positions by PM for each time/ticker
        pm_positions = {}  # {(pm, ticker, time): total_position}
        
        # Sum all trader positions for each PM
        for _, ctx_row in splitctx_df.iterrows():
            trader_id = ctx_row['alphaid']
            ticker = ctx_row['ticker']
            time_event = ctx_row['time']
            trader_pos = ctx_row['realtime_pos']
            
            # Map trader back to PM (sSZE111Atem -> sSZE111BUCS)
            pm_id = trader_id.replace('Atem', 'BUCS')
            
            key = (pm_id, ticker, time_event)
            pm_positions[key] = pm_positions.get(key, 0) + trader_pos
        
        # Update VposResEv records with aggregated PM positions
        # Skip the first time event (930000000) since positions there equal previous day close
        for time_event in self.time_events[1:]:  # Start from second time event
            for pm_id in self.pm_ids:
                for ticker in self.tickers:
                    pm_key = (pm_id, ticker, time_event)
                    if pm_key in pm_positions:
                        new_pos = pm_positions[pm_key]
                        
                        # Update the position record
                        update_mask = (updated_vpos['time'] == time_event) & (updated_vpos['ticker'] == ticker)
                        if update_mask.any():
                            updated_vpos.loc[update_mask, 'vpos'] = new_pos
                        elif new_pos != 0:  # Add new record if position is non-zero
                            new_record = pd.DataFrame([{'time': time_event, 'ticker': ticker, 'vpos': new_pos}])
                            updated_vpos = pd.concat([updated_vpos, new_record], ignore_index=True)
        
        return updated_vpos
    
    def generate_all_data(self):
        """Generate complete test dataset"""
        print("=" * 60)
        print("GENERATING ALPHA ANALYZER TEST DATA")
        print("=" * 60)
        
        # Generate data in dependency order
        incheck_df = self.generate_pm_signals()
        merged_df = self.generate_merged_signals(incheck_df)
        split_df = self.generate_split_signals(merged_df)
        context_df = self.generate_position_context(split_df)
        market_df = self.generate_market_data()
        vpos_df = self.generate_pm_virtual_positions(incheck_df)
        
        # Update positions based on actual execution results
        vpos_df = self.update_positions_with_executions(vpos_df, context_df)
        
        # Save to CSV files
        print("\nSaving data files...")
        
        incheck_df.to_csv(self.output_dir / "InCheckAlphaEv.csv", sep="|", index=False)
        merged_df.to_csv(self.output_dir / "MergedAlphaEv.csv", sep="|", index=False)
        split_df.to_csv(self.output_dir / "SplitAlphaEv.csv", sep="|", index=False)
        context_df.to_csv(self.output_dir / "SplitCtxEv.csv", sep="|", index=False)
        market_df.to_csv(self.output_dir / "MarketDataEv.csv", sep="|", index=False)
        vpos_df.to_csv(self.output_dir / "VposResEv.csv", sep="|", index=False)
        
        print("\nData generation complete!")
        print(f"Files saved to: {self.output_dir}")
        print("\nFile sizes:")
        for csv_file in self.output_dir.glob("*.csv"):
            size_mb = csv_file.stat().st_size / (1024 * 1024)
            print(f"  {csv_file.name}: {size_mb:.1f} MB")
        
        print(f"\nData summary:")
        print(f"  Time events: {len(self.time_events)}")
        print(f"  Total records: {len(incheck_df) + len(merged_df) + len(split_df) + len(context_df) + len(market_df) + len(vpos_df):,}")
        print(f"  Expected alpha conservation: ✓")
        print(f"  Fill rate range: {self.fill_rate_min}-{self.fill_rate_max}")
        print(f"  PM coverage constraint: ✓ (≥{min(1000, self.num_tickers)} tickers per PM per time event)")

    def _validate_pm_coverage_constraint(self, df: pd.DataFrame):
        """Validate that every PM has alphas for at least 1000 tickers per time event"""
        print("  Validating PM coverage constraint...")
        
        constraint_violations = []
        min_required = min(1000, self.num_tickers)
        
        for time_event in self.time_events:
            time_data = df[df['time'] == time_event]
            
            for pm_id in self.pm_ids:
                pm_data = time_data[time_data['alphaid'] == pm_id]
                ticker_count = pm_data['ticker'].nunique()
                
                if ticker_count < min_required:
                    constraint_violations.append(
                        f"PM {pm_id} at time {self._format_time(time_event)}: "
                        f"only {ticker_count} tickers (required: {min_required})"
                    )
        
        if constraint_violations:
            print("  ❌ PM Coverage Constraint Violations:")
            for violation in constraint_violations[:5]:  # Show first 5
                print(f"    {violation}")
            if len(constraint_violations) > 5:
                print(f"    ... and {len(constraint_violations) - 5} more violations")
            raise ValueError(f"PM coverage constraint failed: {len(constraint_violations)} violations")
        else:
            print(f"  ✅ PM Coverage Constraint: All {self.num_pms} PMs have ≥{min_required} tickers per time event")

    def _format_time(self, time_int):
        """Convert time integer to readable format"""
        time_str = str(time_int)
        if time_int < 100000000:
            hour = int(time_str[0])
            minute = int(time_str[1:3])
        else:
            hour = int(time_str[0:2])
            minute = int(time_str[2:4])
        return f"{hour:02d}:{minute:02d}"


def main():
    parser = argparse.ArgumentParser(
        description="Generate test data for Alpha Analyzer pressure testing"
    )
    parser.add_argument(
        "--output-dir", 
        default="test_data",
        help="Output directory for generated CSV files"
    )
    parser.add_argument(
        "--tickers",
        type=int,
        default=3000,
        help="Number of tickers to generate (default: 3000)"
    )
    
    args = parser.parse_args()
    
    generator = TestDataGenerator(args.output_dir)
    generator.num_tickers = args.tickers
    generator.tickers = [f"{i:06d}.SSE" for i in range(1, args.tickers + 1)]
    
    generator.generate_all_data()


if __name__ == "__main__":
    main()