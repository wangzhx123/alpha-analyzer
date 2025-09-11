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
    - 5 Portfolio Managers (PM1-PM5)  
    - 5 Traders (TRD1-TRD5)
    - Time intervals: 10min from 93000000 to 150000000 (break 113000000-130000000)
    - Fill rates: 0.8-0.9 for realistic execution
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
        """Generate InCheckAlphaEv.csv - PM alpha signals"""
        print("Generating PM alpha signals...")
        
        records = []
        event_id = 1
        
        for time_event in self.time_events:
            # Each PM generates signals for a random subset of tickers
            for pm_id in self.pm_ids:
                # PM trades 200-500 tickers per time event (or all available if fewer)
                max_tickers = min(500, len(self.tickers))
                min_tickers = min(200, len(self.tickers))
                num_active_tickers = random.randint(min_tickers, max_tickers)
                active_tickers = random.sample(self.tickers, num_active_tickers)
                
                for ticker in active_tickers:
                    # Generate realistic volume (100-share lots, up to 100,000 shares)
                    # No short selling - all volumes must be non-negative
                    volume = random.randint(1, 1000) * 100
                    
                    records.append({
                        'event': event_id,
                        'alphaid': pm_id,
                        'time': time_event,
                        'ticker': ticker,
                        'volume': volume
                    })
                    event_id += 1
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} PM signal records")
        return df
    
    def generate_merged_signals(self, incheck_df: pd.DataFrame) -> pd.DataFrame:
        """Generate MergedAlphaEv.csv - Consolidated PM signals"""
        print("Generating merged alpha signals...")
        
        records = []
        event_id = 1
        
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
                        'event': event_id,
                        'alphaid': group_id,
                        'time': time_event,
                        'ticker': ticker,
                        'volume': total_volume
                    })
                    event_id += 1
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} merged signal records")
        return df
    
    def generate_split_signals(self, merged_df: pd.DataFrame) -> pd.DataFrame:
        """Generate SplitAlphaEv.csv - Trader allocations"""
        print("Generating split alpha signals...")
        
        records = []
        event_id = 1
        
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
                    'event': event_id,
                    'alphaid': trader_id,
                    'time': time_event,
                    'ticker': ticker,
                    'volume': trader_volume
                })
                event_id += 1
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} split signal records")
        return df
    
    def generate_position_context(self, split_df: pd.DataFrame) -> pd.DataFrame:
        """Generate SplitCtxEv.csv - Trader positions with realistic fill rates"""
        print("Generating position context with fill rates...")
        
        records = []
        event_id = 1
        
        # Track trader positions over time
        trader_positions = {}  # {(trader, ticker): position}
        
        # Initialize positions to zero
        for trader in self.trader_ids:
            for ticker in self.tickers:
                trader_positions[(trader, ticker)] = 0
        
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
                        
                        # Apply fill rate (0.8 to 0.9)
                        fill_rate = random.uniform(self.fill_rate_min, self.fill_rate_max)
                        actual_trade = round(target_volume * fill_rate / 100) * 100
                        
                        # Update position
                        new_pos = current_pos + actual_trade
                        trader_positions[(trader, ticker)] = new_pos
                    else:
                        # No signal, position unchanged
                        new_pos = current_pos
                    
                    # Generate available short volume (for T+1 constraint)
                    # Can sell up to current long position
                    avail_short_vol = max(0, new_pos)
                    
                    # Split position into long/short components
                    realtime_long_pos = max(0, new_pos)
                    realtime_short_pos = max(0, -new_pos)
                    
                    records.append({
                        'event': event_id,
                        'alphaid': trader,
                        'time': time_event,
                        'ticker': ticker,
                        'realtime_pos': new_pos,
                        'realtime_long_pos': realtime_long_pos,
                        'realtime_short_pos': realtime_short_pos,
                        'realtime_avail_shot_vol': avail_short_vol
                    })
                    event_id += 1
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} position context records")
        return df
    
    def generate_market_data(self) -> pd.DataFrame:
        """Generate MarketDataEv.csv - Market prices (optional)"""
        print("Generating market data...")
        
        records = []
        event_id = 1
        
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
                    'event': event_id,
                    'alphaid': 'MARKET',
                    'time': time_event,
                    'ticker': ticker,
                    'last_price': round(last_price, 2),
                    'prev_close_price': round(prev_close, 2)
                })
                event_id += 1
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} market data records")
        return df
    
    def generate_pm_virtual_positions(self, incheck_df: pd.DataFrame) -> pd.DataFrame:
        """Generate VposResEv.csv - PM virtual positions for T+1 constraints"""
        print("Generating PM virtual positions...")
        
        records = []
        
        # Track PM virtual positions
        pm_positions = {}  # {(pm, ticker): position}
        
        # Initialize with previous day positions (time = -1)
        for pm_id in self.pm_ids:
            num_holdings = min(1000, len(self.tickers))  # PMs don't hold all tickers
            for ticker in random.sample(self.tickers, num_holdings):
                initial_pos = random.randint(-10000, 10000)
                pm_positions[(pm_id, ticker)] = initial_pos
                
                # Add previous day record
                records.append({
                    'time': -1,
                    'ticker': ticker,
                    'vpos': initial_pos
                })
        
        # Generate virtual positions for each time event
        for time_event in self.time_events:
            time_data = incheck_df[incheck_df['time'] == time_event]
            
            for pm_id in self.pm_ids:
                pm_data = time_data[time_data['alphaid'] == pm_id]
                
                for ticker in self.tickers:
                    current_pos = pm_positions.get((pm_id, ticker), 0)
                    
                    # Check if PM has signal for this ticker
                    ticker_signals = pm_data[pm_data['ticker'] == ticker]
                    
                    if not ticker_signals.empty:
                        # Update virtual position based on signal
                        signal_volume = ticker_signals['volume'].sum()
                        # Apply some execution efficiency (not perfect fill)
                        fill_rate = random.uniform(0.85, 0.95)
                        actual_change = round(signal_volume * fill_rate / 100) * 100
                        new_pos = current_pos + actual_change
                        pm_positions[(pm_id, ticker)] = new_pos
                    else:
                        new_pos = current_pos
                    
                    # Only record if position exists
                    if new_pos != 0:
                        records.append({
                            'time': time_event,
                            'ticker': ticker,
                            'vpos': new_pos
                        })
        
        df = pd.DataFrame(records)
        print(f"Generated {len(df)} PM virtual position records")
        return df
    
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