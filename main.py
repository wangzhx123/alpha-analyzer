#!/usr/bin/env python3

import argparse
import sys
import yaml
from pathlib import Path
from analyzer import AlphaAnalyzer
from base_checker import CheckResult
from typing import List


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
        '--config',
        '-c',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Alpha Analyzer Framework 1.0'
    )
    
    args = parser.parse_args()
    csv_dir = args.csv_dir
    
    try:
        # Load configuration
        config_path = Path(args.config)
        config = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
        else:
            print(f"Warning: Configuration file {config_path} not found, using defaults")
        
        # Initialize analyzer
        analyzer = AlphaAnalyzer()
        
        # Load default checkers with config access
        from checkers.alpha_sum_consistency import AlphaSumConsistencyChecker
        from checkers.non_negative_trader import NonNegativeTraderChecker
        from checkers.volume_rounding import VolumeRoundingChecker
        
        analyzer.add_checker(AlphaSumConsistencyChecker(config))
        analyzer.add_checker(NonNegativeTraderChecker())
        analyzer.add_checker(VolumeRoundingChecker())
        
        # Load data
        print(f"Loading data from: {csv_dir}")
        analyzer.load_data(csv_dir)
        
        # Run analysis
        results = analyzer.run_checks()
        
        # Display results
        print_results(results)
        
        # Exit with appropriate code
        failed_count = sum(1 for r in results if r.status in ['FAIL', 'ERROR'])
        return 0 if failed_count == 0 else 1
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


def print_results(results: List[CheckResult]):
    """Simple results printing"""
    colors = {
        'PASS': '\033[92m',    # Green
        'FAIL': '\033[91m',    # Red  
        'WARN': '\033[93m',    # Yellow
        'ERROR': '\033[91m',   # Red
        'RESET': '\033[0m'     # Reset
    }
    
    print("\n" + "="*60)
    print("ALPHA ANALYZER RESULTS")
    print("="*60)
    
    # Count results by status
    passed = sum(1 for r in results if r.status == "PASS")
    failed = sum(1 for r in results if r.status == "FAIL")
    warnings = sum(1 for r in results if r.status == "WARNING")
    errors = sum(1 for r in results if r.status == "ERROR")
    
    print(f"Total Checks: {len(results)}")
    print(f"Passed: {colors['PASS']}{passed}{colors['RESET']}")
    print(f"Failed: {colors['FAIL']}{failed}{colors['RESET']}")
    print(f"Warnings: {colors['WARN']}{warnings}{colors['RESET']}")
    print(f"Errors: {colors['ERROR']}{errors}{colors['RESET']}")
    print()
    
    # Print individual results
    for result in results:
        color = colors.get(result.status, colors['RESET'])
        print(f"[{color}{result.status}{colors['RESET']}] {result.checker_name}")
        print(f"    {result.message}")
        
        if result.details:
            for line in result.details.split('\n'):
                if line.strip():
                    print(f"      {line}")
        print()
    
    # Final status
    if failed == 0 and errors == 0:
        print(f"{colors['PASS']}✅ ALL CHECKS PASSED{colors['RESET']}")
    else:
        failure_count = failed + errors
        print(f"{colors['FAIL']}❌ ANALYSIS FAILED - {failure_count} critical issues{colors['RESET']}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)