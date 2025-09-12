#!/usr/bin/env python3
"""
Generate corrected realistic trading data based on user feedback.
Implements proper merge/split system with overlapping tickers and correct TVR logic.
"""
import random
import csv
import argparse
from pathlib import Path
from collections import defaultdict

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate corrected realistic trading data")
    
    parser.add_argument("--num-pm", type=int, default=5, 
                       help="Number of PMs (default: 5)")
    parser.add_argument("--num-trader", type=int, default=5,
                       help="Number of traders (default: 5)")
    parser.add_argument("--num-tickers", type=int, default=1000,
                       help="Total number of tickers in universe (default: 1000)")
    
    # Time interval configuration
    parser.add_argument("--ti-ranges", nargs='+', default=["930000000,1130000000", "1300000000,1500000000"],
                       help="Time ranges in format 'start,end' (default: morning and afternoon sessions)")
    parser.add_argument("--ti-interval", type=int, default=10000000,
                       help="Time interval step in nanoseconds (default: 10000000 = 10 minutes)")
    
    # Fill rate configuration
    parser.add_argument("--fill-rate-min", type=float, default=0.8,
                       help="Minimum fill rate (default: 0.8)")
    parser.add_argument("--fill-rate-max", type=float, default=0.9,
                       help="Maximum fill rate (default: 0.9)")
    
    # TVR configuration
    parser.add_argument("--tvr-min", type=float, default=0.1,
                       help="Minimum TVR change factor (default: 0.1)")
    parser.add_argument("--tvr-max", type=float, default=0.6,
                       help="Maximum TVR change factor (default: 0.6)")
    
    parser.add_argument("--output-dir", default="sample_data",
                       help="Output directory for CSV files (default: sample_data)")
    
    return parser.parse_args()

def generate_tickers(count):
    """Generate ticker universe (SSE and SZSE stocks)"""
    tickers = []
    # SSE stocks (000001-999999)
    for i in range(1, count//2 + 1):
        tickers.append(f"{i:06d}.SSE")
    # SZSE stocks (000001-999999) 
    for i in range(1, count - count//2 + 1):
        tickers.append(f"{i:06d}.SZSE")
    return tickers

def generate_time_intervals_from_ranges(ti_ranges, interval):
    """Generate time intervals from multiple ranges with given step"""
    intervals = []
    for range_str in ti_ranges:
        start_str, end_str = range_str.split(',')
        start, end = int(start_str), int(end_str)
        current = start
        while current <= end:
            intervals.append(current)
            current += interval
    return sorted(intervals)

def assign_overlapping_tickers(all_tickers, num_pms):
    """
    Assign tickers to PMs with heavy overlap (80-90% common tickers).
    Each PM gets most tickers + some unique ones.
    """
    pm_tickers = {}
    
    # Common tickers (80-90% of all tickers)
    common_ratio = random.uniform(0.8, 0.9)
    num_common = int(len(all_tickers) * common_ratio)
    common_tickers = random.sample(all_tickers, num_common)
    
    for i in range(num_pms):
        pm_id = f"PM_{i+1:03d}BUCS"
        
        # Start with common tickers
        pm_ticker_set = set(common_tickers)
        
        # Add some unique tickers (10-20% of remaining)
        remaining_tickers = [t for t in all_tickers if t not in common_tickers]
        if remaining_tickers:
            unique_count = random.randint(len(remaining_tickers)//10, len(remaining_tickers)//5)
            unique_tickers = random.sample(remaining_tickers, min(unique_count, len(remaining_tickers)))
            pm_ticker_set.update(unique_tickers)
        
        pm_tickers[pm_id] = sorted(list(pm_ticker_set))
    
    return pm_tickers

def generate_market_data(time_intervals, all_tickers):
    """Generate market price data for ALL tickers at ALL time intervals"""
    data = []
    
    for ti in time_intervals:
        for ticker in all_tickers:
            # Generate realistic price movement
            base_price = random.uniform(10.0, 200.0)
            prev_price = base_price * random.uniform(0.95, 1.05)
            current_price = prev_price * random.uniform(0.98, 1.02)
            
            data.append([
                "MarketDataEv", "MARKET", str(ti), ticker, 
                f"{current_price:.2f}", f"{prev_price:.2f}"
            ])
    
    return data

def generate_incheck_alpha_data(pm_tickers, time_intervals, tvr_range):
    """Generate PM alpha signals with proper TVR and overlapping tickers"""
    data = []
    pm_positions = defaultdict(dict)  # Track PM positions over time
    
    for ti in time_intervals:
        for pm_id, tickers in pm_tickers.items():
            for ticker in tickers:
                if ticker not in pm_positions[pm_id]:
                    # Initial target position
                    target_pos = random.randint(1000, 5000) * 100
                else:
                    # Apply TVR: Previous target ± random(0.1, 0.6) × Previous target
                    prev_target = pm_positions[pm_id][ticker]
                    tvr_factor = random.uniform(*tvr_range)
                    change_direction = random.choice([-1, 1])
                    change = int(prev_target * tvr_factor * change_direction)
                    target_pos = max(0, prev_target + change)  # Ensure non-negative
                
                pm_positions[pm_id][ticker] = target_pos
                
                data.append([
                    "InCheckAlphaEv", pm_id, str(ti), ticker, str(target_pos)
                ])
    
    return data, pm_positions

def generate_merged_alpha_data(pm_positions, time_intervals, all_tickers):
    """Generate MergedAlphaEv by summing ALL PM alphas for each ticker/time"""
    data = []
    
    for ti in time_intervals:
        for ticker in all_tickers:
            # Sum all PM targets for this ticker at this time
            total_target = 0
            for pm_id, positions in pm_positions.items():
                if ticker in positions:
                    total_target += positions[ticker]
            
            if total_target > 0:  # Only include if there's actual target
                alpha_id = f"GRP_{ti}_{ticker}"
                data.append([
                    "MergedAlphaEv", alpha_id, str(ti), ticker, str(total_target)
                ])
    
    return data

def generate_split_alpha_data(merged_targets, trader_ids, time_intervals, all_tickers):
    """Generate trader alpha signals by splitting merged targets EVENLY to ALL traders"""
    data = []
    trader_targets = defaultdict(dict)
    
    # Create merged_targets lookup
    merged_lookup = {}
    for ti in time_intervals:
        merged_lookup[ti] = {}
    
    for record in merged_targets:
        _, alpha_id, time_str, ticker, volume_str = record
        ti = int(time_str)
        volume = int(volume_str)
        merged_lookup[ti][ticker] = volume
    
    for ti in time_intervals:
        for ticker in all_tickers:
            if ticker in merged_lookup[ti]:
                merged_target = merged_lookup[ti][ticker]
                # Split evenly among ALL traders
                target_per_trader = merged_target // len(trader_ids)
                remainder = merged_target % len(trader_ids)
                
                for i, trader_id in enumerate(trader_ids):
                    trader_target = target_per_trader
                    # Distribute remainder to first few traders
                    if i < remainder:
                        trader_target += 1
                    
                    if trader_target > 0:
                        trader_targets[trader_id][ticker] = trader_target
                        data.append([
                            "SplitAlphaEv", trader_id, str(ti), ticker, str(trader_target)
                        ])
    
    return data, trader_targets

def generate_split_ctx_data(trader_targets, trader_ids, time_intervals, all_tickers, fill_rate_range):
    """Generate actual trader positions with controlled fill rates and direction consistency"""
    data = []
    actual_positions = defaultdict(dict)
    
    # Initialize all positions to 0
    for trader_id in trader_ids:
        for ticker in all_tickers:
            actual_positions[trader_id][ticker] = 0
    
    for ti in time_intervals:
        for trader_id in trader_ids:
            for ticker in all_tickers:
                current_pos = actual_positions[trader_id][ticker]
                
                # Get target for this trader/ticker/time
                target_key = (trader_id, ticker)
                target_pos = 0
                
                # Find target from trader_targets data
                for record in trader_targets:
                    if len(record) >= 5:
                        _, record_trader_id, record_time, record_ticker, record_volume = record
                        if (record_trader_id == trader_id and 
                            int(record_time) == ti and 
                            record_ticker == ticker):
                            target_pos = int(record_volume)
                            break
                
                intended_trade = target_pos - current_pos
                
                if intended_trade != 0:
                    # Apply fill rate
                    fill_rate = random.uniform(*fill_rate_range)
                    actual_trade = int(intended_trade * fill_rate)
                    
                    # Direction consistency: ensure we move toward target
                    if intended_trade > 0:  # Buy direction
                        actual_trade = max(0, actual_trade)  # Only positive trades
                    else:  # Sell direction
                        actual_trade = min(0, actual_trade)  # Only negative trades
                    
                    new_position = current_pos + actual_trade
                else:
                    new_position = current_pos
                
                # Ensure non-negative position
                new_position = max(0, new_position)
                actual_positions[trader_id][ticker] = new_position
                
                # Output position record for every trader/ticker/time
                data.append([
                    "SplitCtxEv", trader_id, str(ti), ticker, str(new_position),
                    str(new_position), "0", str(new_position)
                ])
    
    return data, actual_positions

def generate_vpos_data(actual_positions, pm_tickers, time_intervals):
    """Generate PM virtual positions by summing trader positions for same ticker"""
    data = []
    
    for ti in time_intervals:
        for pm_id, tickers in pm_tickers.items():
            for ticker in tickers:
                # Sum all trader positions for this ticker
                total_trader_pos = 0
                for trader_id, positions in actual_positions.items():
                    total_trader_pos += positions.get(ticker, 0)
                
                # PM vpos = sum of trader positions (exactly equal)
                vpos = total_trader_pos
                
                data.append([
                    "VposResEv", pm_id, str(ti), ticker, str(vpos),
                    str(vpos), "0", str(vpos)
                ])
    
    return data

def write_csv(filename, headers, data, output_dir):
    """Write data to CSV file"""
    filepath = Path(output_dir) / filename
    filepath.parent.mkdir(exist_ok=True)
    
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f, delimiter='|')
        writer.writerow(headers)
        for row in data:
            writer.writerow(row)
    
    print(f"Generated {filename} with {len(data)} records")

def main():
    args = parse_args()
    
    # Generate configurations from args
    time_intervals = generate_time_intervals_from_ranges(args.ti_ranges, args.ti_interval)
    fill_rate_range = (args.fill_rate_min, args.fill_rate_max)
    tvr_range = (args.tvr_min, args.tvr_max)
    
    # Generate IDs with correct format
    pm_ids = [f"PM_{i:03d}BUCS" for i in range(1, args.num_pm + 1)]
    trader_ids = [f"TRADER_{i:03d}Atem" for i in range(1, args.num_trader + 1)]
    
    # Generate ticker universe
    all_tickers = generate_tickers(args.num_tickers)
    
    # Assign overlapping tickers to PMs
    pm_tickers = assign_overlapping_tickers(all_tickers, args.num_pm)
    
    print("Generating corrected realistic trading data...")
    print(f"Configuration: {args.num_pm} PMs, {args.num_trader} traders, {args.num_tickers} total tickers")
    print(f"Time intervals: {len(time_intervals)} from ranges {args.ti_ranges} (step: {args.ti_interval})")
    print(f"Fill rate range: {args.fill_rate_min}-{args.fill_rate_max}")
    print(f"TVR range: {args.tvr_min}-{args.tvr_max}")
    print(f"PM ticker overlap: Heavy overlap with some unique tickers per PM")
    print(f"Output directory: {args.output_dir}")
    
    # Generate all data in correct order
    market_data = generate_market_data(time_intervals, all_tickers)
    incheck_data, pm_positions = generate_incheck_alpha_data(pm_tickers, time_intervals, tvr_range)
    merged_data = generate_merged_alpha_data(pm_positions, time_intervals, all_tickers)
    split_alpha_data, trader_targets = generate_split_alpha_data(merged_data, trader_ids, time_intervals, all_tickers)
    split_ctx_data, actual_positions = generate_split_ctx_data(split_alpha_data, trader_ids, time_intervals, all_tickers, fill_rate_range)
    vpos_data = generate_vpos_data(actual_positions, pm_tickers, time_intervals)
    
    # Write CSV files
    write_csv("MarketDataEv.csv", 
              ["event", "alphaid", "time", "ticker", "last_price", "prev_close_price"],
              market_data, args.output_dir)
    
    write_csv("InCheckAlphaEv.csv",
              ["event", "alphaid", "time", "ticker", "volume"],
              incheck_data, args.output_dir)
    
    write_csv("MergedAlphaEv.csv",
              ["event", "alphaid", "time", "ticker", "volume"],
              merged_data, args.output_dir)
    
    write_csv("SplitAlphaEv.csv",
              ["event", "alphaid", "time", "ticker", "volume"], 
              split_alpha_data, args.output_dir)
    
    write_csv("SplitCtxEv.csv",
              ["event", "alphaid", "time", "ticker", "realtime_pos", 
               "realtime_long_pos", "realtime_short_pos", "realtime_avail_shot_vol"],
              split_ctx_data, args.output_dir)
    
    write_csv("VposResEv.csv",
              ["event", "alphaid", "time", "ticker", "realtime_pos",
               "realtime_long_pos", "realtime_short_pos", "realtime_avail_shot_vol"],
              vpos_data, args.output_dir)
    
    print(f"\n✅ All CSV files generated successfully!")
    print(f"Total tickers: {len(all_tickers)}")
    print(f"PM alpha signals: {len(incheck_data)}")
    print(f"Merged alpha signals: {len(merged_data)}")  
    print(f"Trader signals: {len(split_alpha_data)}")
    print(f"Time intervals generated: {time_intervals}")
    
    # Show PM ticker overlap stats
    print(f"\n📊 PM Ticker Overlap Statistics:")
    for pm_id, tickers in pm_tickers.items():
        print(f"  {pm_id}: {len(tickers)} tickers")

if __name__ == "__main__":
    main()