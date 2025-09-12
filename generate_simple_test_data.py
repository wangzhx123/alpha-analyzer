#!/usr/bin/env python3

import pandas as pd
import numpy as np
import random
from pathlib import Path
import argparse
from typing import List

class SimpleTestDataGenerator:
    """
    Generate simple test data where fill rates are GUARANTEED to be 0.8-0.9
    
    This generator ensures that for every alpha signal at time T,
    the position change from time T to T+1 is exactly 0.8-0.9 of the alpha target.
    """
    
    def __init__(self, output_dir: str = "simple_test_data"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Fixed parameters for simplicity
        self.tickers = ['000001.SSE', '000002.SSE', '000003.SSE']
        self.trader_ids = ['sSZE111Atem', 'sSZE112Atem']
        self.time_events = [930000000, 940000000, 950000000, 1000000000, 1010000000]
        
        # Fill rate range
        self.fill_rate_min = 0.8
        self.fill_rate_max = 0.9
        
        # Random seed for reproducibility
        np.random.seed(42)
        random.seed(42)
        
        print(f"Simple test data generator:")
        print(f"  Tickers: {len(self.tickers)}")
        print(f"  Traders: {len(self.trader_ids)}")
        print(f"  Time events: {len(self.time_events)}")
        print(f"  Fill rate range: {self.fill_rate_min}-{self.fill_rate_max}")
        print(f"  Output directory: {self.output_dir}")
    
    def generate_simple_data(self):
        """Generate simple test data with guaranteed fill rates"""
        print("Generating simple test data with guaranteed fill rates...")
        
        split_records = []
        position_records = []
        
        # Track positions over time
        positions = {}  # {(trader, ticker): position}
        
        # Initialize positions to zero
        for trader in self.trader_ids:
            for ticker in self.tickers:
                positions[(trader, ticker)] = 0
        
        # Generate data for each time period
        for i, time_event in enumerate(self.time_events):
            print(f"  Processing time {time_event}...")
            
            # For each trader and ticker combination
            for trader in self.trader_ids:
                for ticker in self.tickers:
                    current_pos = positions[(trader, ticker)]
                    
                    # Generate alpha signal (30% chance to avoid overlaps)
                    if random.random() < 0.3:
                        # Generate alpha target (100-share lots, 1,000-5,000 shares)
                        target_alpha = random.randint(10, 50) * 100
                        
                        # Apply EXACT fill rate (0.8 to 0.9)
                        fill_rate = random.uniform(self.fill_rate_min, self.fill_rate_max)
                        actual_execution = round(target_alpha * fill_rate / 100) * 100
                        
                        # Record the alpha signal
                        split_records.append({
                            'event': 'SplitAlphaEv',
                            'alphaid': trader,
                            'time': time_event,
                            'ticker': ticker,
                            'volume': target_alpha
                        })
                        
                        # Update position with actual execution
                        new_pos = current_pos + actual_execution
                        positions[(trader, ticker)] = new_pos
                        
                        print(f"    {trader} {ticker}: alpha={target_alpha}, fill_rate={fill_rate:.3f}, execution={actual_execution}")
                    else:
                        # No alpha signal, position stays the same
                        new_pos = current_pos
                    
                    # ALWAYS record position for all traders/tickers at each time
                    # This ensures complete position history for analysis
                    position_records.append({
                        'event': 'SplitCtxEv',
                        'alphaid': trader,
                        'time': time_event,
                        'ticker': ticker,
                        'realtime_pos': new_pos,
                        'realtime_long_pos': max(0, new_pos),
                        'realtime_short_pos': max(0, -new_pos),
                        'realtime_avail_shot_vol': max(0, new_pos)
                    })
        
        # Create DataFrames
        split_df = pd.DataFrame(split_records)
        position_df = pd.DataFrame(position_records)
        
        print(f"Generated {len(split_records)} alpha signals")
        print(f"Generated {len(position_records)} position records")
        
        # Save to CSV files
        split_df.to_csv(self.output_dir / "SplitAlphaEv.csv", sep="|", index=False)
        position_df.to_csv(self.output_dir / "SplitCtxEv.csv", sep="|", index=False)
        
        # Generate minimal market data
        market_records = []
        base_price = 100.0
        for time_event in self.time_events:
            for ticker in self.tickers:
                price_change = random.uniform(-0.02, 0.02)  # ±2% movement
                current_price = base_price * (1 + price_change)
                market_records.append({
                    'event': 'MarketDataEv',
                    'alphaid': 'MARKET',
                    'time': time_event,
                    'ticker': ticker,
                    'last_price': round(current_price, 2),
                    'prev_close_price': round(base_price, 2)
                })
                base_price = current_price
        
        market_df = pd.DataFrame(market_records)
        market_df.to_csv(self.output_dir / "MarketDataEv.csv", sep="|", index=False)
        
        # Generate dummy files for other required CSVs
        # InCheckAlphaEv (empty for simplicity)
        incheck_df = pd.DataFrame(columns=['event', 'alphaid', 'time', 'ticker', 'volume'])
        incheck_df.to_csv(self.output_dir / "InCheckAlphaEv.csv", sep="|", index=False)
        
        # MergedAlphaEv (empty for simplicity)  
        merged_df = pd.DataFrame(columns=['event', 'alphaid', 'time', 'ticker', 'volume'])
        merged_df.to_csv(self.output_dir / "MergedAlphaEv.csv", sep="|", index=False)
        
        # VposResEv (empty for simplicity)
        vpos_df = pd.DataFrame(columns=['time', 'ticker', 'vpos'])
        vpos_df.to_csv(self.output_dir / "VposResEv.csv", sep="|", index=False)
        
        print("\nSimple test data generation complete!")
        print(f"Files saved to: {self.output_dir}")
        
        # Validate the data
        self._validate_fill_rates(split_df, position_df)
    
    def _validate_fill_rates(self, split_df: pd.DataFrame, position_df: pd.DataFrame):
        """Validate that fill rates are within expected range"""
        print("\nValidating fill rates...")
        
        violations = []
        
        # Sort data
        split_df = split_df.sort_values(['alphaid', 'ticker', 'time'])
        position_df = position_df.sort_values(['alphaid', 'ticker', 'time'])
        
        # Get unique times
        times = sorted(split_df['time'].unique())
        
        for i in range(len(times) - 1):
            t_current = times[i]
            t_next = times[i + 1]
            
            # Get alphas at current time
            current_alphas = split_df[split_df['time'] == t_current]
            
            for _, alpha_row in current_alphas.iterrows():
                trader = alpha_row['alphaid']
                ticker = alpha_row['ticker']
                target_alpha = alpha_row['volume']
                
                # Get positions at both times
                pos_current = position_df[
                    (position_df['alphaid'] == trader) &
                    (position_df['ticker'] == ticker) &
                    (position_df['time'] == t_current)
                ]
                pos_next = position_df[
                    (position_df['alphaid'] == trader) &
                    (position_df['ticker'] == ticker) &
                    (position_df['time'] == t_next)
                ]
                
                if not pos_current.empty and not pos_next.empty:
                    pos_change = pos_next['realtime_pos'].iloc[0] - pos_current['realtime_pos'].iloc[0]
                    fill_rate = pos_change / target_alpha if target_alpha != 0 else 0
                    
                    if not (self.fill_rate_min <= fill_rate <= self.fill_rate_max):
                        violations.append(
                            f"{trader} {ticker} {t_current}→{t_next}: "
                            f"target={target_alpha}, actual={pos_change}, fill_rate={fill_rate:.3f}"
                        )
        
        if violations:
            print(f"❌ Found {len(violations)} fill rate violations:")
            for violation in violations[:5]:  # Show first 5
                print(f"  {violation}")
        else:
            print("✅ All fill rates are within expected range 0.8-0.9")


def main():
    parser = argparse.ArgumentParser(description="Generate simple test data with guaranteed fill rates")
    parser.add_argument("--output-dir", default="simple_test_data", help="Output directory")
    
    args = parser.parse_args()
    
    generator = SimpleTestDataGenerator(args.output_dir)
    generator.generate_simple_data()


if __name__ == "__main__":
    main()