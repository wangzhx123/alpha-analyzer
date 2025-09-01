#!/usr/bin/env python3

import sys
from analyzer import AlphaAnalyzer
from reporter import ConsoleReporter
from checkers.alpha_sum_consistency import AlphaSumConsistencyChecker
from checkers.non_negative_trader import NonNegativeTraderChecker
from checkers.volume_rounding import VolumeRoundingChecker


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <data_directory>")
        print("Expected files in data_directory:")
        print("  - IncheckAlphaEv.csv (columns: ti,sid,ticker,target)")
        print("  - SplitAlphaEv.csv (columns: ti,sid,ticker,target)")
        print("  - RealtimePosEv.csv (columns: ti,sid,ticker,realtime_pos)")
        return 1
    
    data_dir = sys.argv[1]
    
    # Initialize analyzer and reporter
    analyzer = AlphaAnalyzer()
    reporter = ConsoleReporter()
    
    # Register checkers
    analyzer.add_checker(AlphaSumConsistencyChecker())
    analyzer.add_checker(NonNegativeTraderChecker())
    analyzer.add_checker(VolumeRoundingChecker())
    
    try:
        # Load data
        print(f"Loading data from: {data_dir}")
        analyzer.load_data(data_dir)
        
        # Print data summary
        summary = analyzer.get_data_summary()
        if summary:
            print(f"Data Summary:")
            print(f"  Input events (ti): {summary['input_events']}")
            print(f"  Output events (ti): {summary['output_events']}")
            print(f"  Realtime events (ti): {summary['realtime_events']}")
            print(f"  Input tickers: {summary['input_tickers']}")
            print(f"  Output tickers: {summary['output_tickers']}")
            print(f"  Realtime tickers: {summary['realtime_tickers']}")
        
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