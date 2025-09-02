#!/usr/bin/env python3

import argparse
import sys
from analyzer import AlphaAnalyzer
from reporter import ConsoleReporter
from checkers.alpha_sum_consistency import AlphaSumConsistencyChecker
from checkers.non_negative_trader import NonNegativeTraderChecker
from checkers.volume_rounding import VolumeRoundingChecker


def main():
    parser = argparse.ArgumentParser(
        description="Alpha Analyzer Framework - Validate trading alpha signals with event-based processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Expected files in data directory:
  - InCheckAlphaEv.csv     Input alpha events (event|alphaid|time|ticker|volume)
  - MergedAlphaEv.csv      Merged upstream alpha (event|alphaid|time|ticker|volume) [optional]
  - SplitAlphaEv.csv       Split alpha events (event|alphaid|time|ticker|volume)
  - SplitCtxEv.csv         Position context (event|alphaid|time|ticker|realtime_pos|...)
  - MarketDataEv.csv       Market data (event|alphaid|time|ticker|last_price|prev_close_price) [optional]

Note: Time field supports 'nil_last_alpha' string which gets converted to -1 (closing positions)
        """
    )
    
    parser.add_argument(
        'csv_dir',
        metavar='CSV_DIRECTORY',
        help='Directory containing CSV data files'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Alpha Analyzer Framework 1.0'
    )
    
    args = parser.parse_args()
    csv_dir = args.csv_dir
    
    # Initialize analyzer and reporter
    analyzer = AlphaAnalyzer()
    reporter = ConsoleReporter()
    
    # Register checkers
    analyzer.add_checker(AlphaSumConsistencyChecker())
    analyzer.add_checker(NonNegativeTraderChecker())
    analyzer.add_checker(VolumeRoundingChecker())
    
    try:
        # Load data
        print(f"Loading data from: {csv_dir}")
        analyzer.load_data(csv_dir)
        
        # Print data summary
        summary = analyzer.get_data_summary()
        if summary:
            print(f"Data Summary:")
            print(f"  InCheck events (time): {summary['incheck_events']}")
            print(f"  Merged events (time): {summary['merged_events']}")
            print(f"  Split events (time): {summary['split_events']}")
            print(f"  Position events (time): {summary['position_events']}")
            print(f"  Market events (time): {summary['market_events']}")
            print(f"  InCheck tickers: {summary['incheck_tickers']}")
            print(f"  Merged tickers: {summary['merged_tickers']}")
            print(f"  Split tickers: {summary['split_tickers']}")
            print(f"  Position tickers: {summary['position_tickers']}")
            print(f"  Market tickers: {summary['market_tickers']}")
        
        # Run analysis
        results = analyzer.run_checks()
        
        # Print results
        reporter.print_results(results)
        
        # Exit with appropriate code
        failed_count = sum(1 for r in results if r.status in ['FAIL', 'ERROR'])
        return 0 if failed_count == 0 else 1
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)