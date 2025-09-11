#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from analyzer import AlphaAnalyzer
from base_checker import CheckResult
from typing import List


def main():
    parser = argparse.ArgumentParser(
        description="Alpha Analyzer Framework - Validate and analyze trading alpha signals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Analysis modes:
  1. --csv-dir DIR: Full validation (all checkers from plugins)
  2. --csv-dir DIR --ti TIME: Analyze specific time event
  3. --csv-dir DIR --ticker TICKER: Analyze ticker across all times
  4. --csv-dir DIR --ti TIME --ticker TICKER: Deep analysis for specific combo
        """,
    )

    parser.add_argument(
        "--csv-dir", required=True, help="Directory containing CSV data files"
    )

    parser.add_argument(
        "--ti", type=int, help="Analyze specific time event (e.g. 93000000)"
    )

    parser.add_argument("--ticker", help='Analyze specific ticker (e.g. "000001.SZE")')

    parser.add_argument(
        "--detail", action="store_true", 
        help="Dump filtered data to CSV files for inspection (saves to current directory)"
    )

    parser.add_argument(
        "--version", action="version", version="Alpha Analyzer Framework 2.0"
    )

    args = parser.parse_args()
    csv_dir = args.csv_dir

    try:
        # Initialize analyzer
        analyzer = AlphaAnalyzer()

        # Auto-load all checkers and analyzers
        load_all_checkers(analyzer, csv_dir)
        load_all_analyzers(analyzer)

        # Load data with optional filtering for performance
        print(f"Loading data from: {csv_dir}")
        if args.ti or args.ticker:
            print(f"Applying data filters: ti={args.ti}, ticker={args.ticker}")
        analyzer.load_data(csv_dir, ti_filter=args.ti, ticker_filter=args.ticker)

        # Dump filtered data if --detail requested
        if args.detail:
            dump_filtered_data(analyzer, args.ti, args.ticker)

        # Run checks
        results = analyzer.run_checks()

        # Display results
        print_results(results)

        # Run analysis based on mode
        run_analysis_mode(analyzer, args.ti, args.ticker)

        # Exit with appropriate code
        failed_count = sum(1 for r in results if r.status in ["FAIL", "ERROR"])
        return 0 if failed_count == 0 else 1

    except Exception as e:
        print(f"Error: {str(e)}")
        return 1


def print_results(results: List[CheckResult]):
    """Simple results printing"""
    colors = {
        "PASS": "\033[92m",  # Green
        "FAIL": "\033[91m",  # Red
        "WARN": "\033[93m",  # Yellow
        "ERROR": "\033[91m",  # Red
        "RESET": "\033[0m",  # Reset
    }

    print("\n" + "=" * 60)
    print("ALPHA ANALYZER RESULTS")
    print("=" * 60)

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
        color = colors.get(result.status, colors["RESET"])
        print(f"[{color}{result.status}{colors['RESET']}] {result.checker_name}")
        print(f"    {result.message}")

        if result.details:
            for line in result.details.split("\n"):
                if line.strip():
                    print(f"      {line}")
        print()

    # Final status
    if failed == 0 and errors == 0:
        print(f"{colors['PASS']}✅ ALL CHECKS PASSED{colors['RESET']}")
    else:
        failure_count = failed + errors
        print(
            f"{colors['FAIL']}❌ ANALYSIS FAILED - {failure_count} critical issues{colors['RESET']}"
        )


def load_all_checkers(analyzer: AlphaAnalyzer, csv_dir: str):
    """Auto-load all checkers from checkers directory"""
    import importlib
    import inspect
    from pathlib import Path
    from base_checker import BaseChecker

    checkers_dir = Path(__file__).parent / "checkers"
    loaded_count = 0

    # Scan for checker files
    for py_file in checkers_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        module_name = f"checkers.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)

            # Find checker classes in the module
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseChecker)
                    and obj != BaseChecker
                ):

                    # Special handling for PM constraint checker
                    if "pm_constraint" in py_file.name.lower():
                        pm_file = Path(csv_dir) / "VposResEv.csv"
                        if pm_file.exists():
                            import pandas as pd

                            pm_df = pd.read_csv(pm_file, delimiter="|")
                            checker = obj(pm_df)
                        else:
                            continue  # Skip if no PM data
                    elif name == "AlphaSumConsistencyChecker":
                        checker = obj({})  # Pass empty config
                    else:
                        checker = obj()  # Default constructor

                    analyzer.add_checker(checker)
                    loaded_count += 1

        except Exception as e:
            print(f"Warning: Failed to load checker from {py_file.name}: {e}")

    print(f"Loaded {loaded_count} checkers")


def load_all_analyzers(analyzer: AlphaAnalyzer):
    """Auto-load all analyzers from analyzers directory"""
    import importlib
    import inspect
    from pathlib import Path
    from base_analyzer import BaseAnalyzer

    analyzers_dir = Path(__file__).parent / "analyzers"
    if not analyzers_dir.exists():
        return

    loaded_count = 0

    # Scan for analyzer files
    for py_file in analyzers_dir.glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        module_name = f"analyzers.{py_file.stem}"
        try:
            module = importlib.import_module(module_name)

            # Find analyzer classes in the module
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, BaseAnalyzer)
                    and obj != BaseAnalyzer
                ):

                    analyzer_instance = obj()
                    analyzer.add_analyzer(analyzer_instance)
                    loaded_count += 1

        except Exception as e:
            print(f"Warning: Failed to load analyzer from {py_file.name}: {e}")

    print(f"Loaded {loaded_count} analyzers")


def run_analysis_mode(analyzer: AlphaAnalyzer, ti: int = None, ticker: str = None):
    """Run analysis in different modes based on ti/ticker filters"""

    if ti and ticker:
        # Interface 4: Deep analysis for specific ti + ticker
        print(f"\n🔍 DEEP ANALYSIS MODE")
    elif ti:
        # Interface 2: All tickers at specific time
        print(f"\n📊 TIME EVENT ANALYSIS MODE")
    elif ticker:
        # Interface 3: Specific ticker across all times
        print(f"\n📈 TICKER TIMELINE ANALYSIS MODE")
    else:
        # Interface 1: Overview mode
        print(f"\n📊 OVERVIEW ANALYSIS MODE")

    # Run all analyzers with the specified interface
    results = analyzer.run_analysis(ti=ti, ticker=ticker)
    print_analysis_results(results)


def dump_filtered_data(analyzer: AlphaAnalyzer, ti_filter=None, ticker_filter=None):
    """Dump filtered data to CSV files for inspection in /tmp directory"""
    import os
    from datetime import datetime
    
    # Use /tmp directory for output
    output_dir = "/tmp"
    
    # Create descriptive filename suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filter_desc = []
    if ti_filter:
        filter_desc.append(f"ti{ti_filter}")
    if ticker_filter:
        filter_desc.append(f"ticker{ticker_filter.replace('.', '_')}")
    
    if filter_desc:
        suffix = f"_{'_'.join(filter_desc)}_{timestamp}"
    else:
        suffix = f"_full_{timestamp}"
    
    print(f"\n🔍 DETAIL MODE: Dumping filtered data to {output_dir}...")
    
    # Dump each dataframe to CSV
    files_created = []
    
    if analyzer.incheck_alpha_df is not None and len(analyzer.incheck_alpha_df) > 0:
        filename = f"detail_InCheckAlphaEv{suffix}.csv"
        filepath = os.path.join(output_dir, filename)
        analyzer.incheck_alpha_df.to_csv(filepath, sep="|", index=False)
        files_created.append(f"{filename} ({len(analyzer.incheck_alpha_df)} records)")
    
    if analyzer.merged_df is not None and len(analyzer.merged_df) > 0:
        filename = f"detail_MergedAlphaEv{suffix}.csv"
        filepath = os.path.join(output_dir, filename)
        analyzer.merged_df.to_csv(filepath, sep="|", index=False)
        files_created.append(f"{filename} ({len(analyzer.merged_df)} records)")
    
    if analyzer.split_alpha_df is not None and len(analyzer.split_alpha_df) > 0:
        filename = f"detail_SplitAlphaEv{suffix}.csv"
        filepath = os.path.join(output_dir, filename)
        analyzer.split_alpha_df.to_csv(filepath, sep="|", index=False)
        files_created.append(f"{filename} ({len(analyzer.split_alpha_df)} records)")
    
    if analyzer.realtime_pos_df is not None and len(analyzer.realtime_pos_df) > 0:
        filename = f"detail_SplitCtxEv{suffix}.csv"
        filepath = os.path.join(output_dir, filename)
        analyzer.realtime_pos_df.to_csv(filepath, sep="|", index=False)
        files_created.append(f"{filename} ({len(analyzer.realtime_pos_df)} records)")
    
    if analyzer.market_df is not None and len(analyzer.market_df) > 0:
        filename = f"detail_MarketDataEv{suffix}.csv"
        filepath = os.path.join(output_dir, filename)
        analyzer.market_df.to_csv(filepath, sep="|", index=False)
        files_created.append(f"{filename} ({len(analyzer.market_df)} records)")
    
    # Create summary file
    summary_filename = f"detail_SUMMARY{suffix}.txt"
    summary_filepath = os.path.join(output_dir, summary_filename)
    with open(summary_filepath, 'w') as f:
        f.write("ALPHA ANALYZER - FILTERED DATA DUMP\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Filter Applied:\n")
        f.write(f"  Time (ti): {ti_filter if ti_filter else 'None'}\n")
        f.write(f"  Ticker: {ticker_filter if ticker_filter else 'None'}\n\n")
        
        f.write("Files Created:\n")
        for file_info in files_created:
            f.write(f"  - {file_info}\n")
        
        f.write(f"\nData Summary:\n")
        f.write(f"  InCheck Alpha: {len(analyzer.incheck_alpha_df) if analyzer.incheck_alpha_df is not None else 0:,} records\n")
        f.write(f"  Merged Alpha: {len(analyzer.merged_df) if analyzer.merged_df is not None else 0:,} records\n")
        f.write(f"  Split Alpha: {len(analyzer.split_alpha_df) if analyzer.split_alpha_df is not None else 0:,} records\n")
        f.write(f"  Position Data: {len(analyzer.realtime_pos_df) if analyzer.realtime_pos_df is not None else 0:,} records\n")
        f.write(f"  Market Data: {len(analyzer.market_df) if analyzer.market_df is not None else 0:,} records\n")
        
        # Add data ranges
        f.write(f"\nData Ranges:\n")
        if analyzer.incheck_alpha_df is not None and len(analyzer.incheck_alpha_df) > 0:
            times = sorted(analyzer.incheck_alpha_df['time'].unique())
            tickers = sorted(analyzer.incheck_alpha_df['ticker'].unique())
            f.write(f"  Time Range: {times[0]} to {times[-1]} ({len(times)} unique times)\n")
            f.write(f"  Tickers: {len(tickers)} unique ({tickers[0]} to {tickers[-1] if len(tickers) > 1 else tickers[0]})\n")
    
    files_created.append(f"{summary_filename} (summary)")
    
    print(f"   Created {len(files_created)} files:")
    for file_info in files_created:
        print(f"     📄 {file_info}")
    
    print(f"   💾 Files saved to: {output_dir}")


def print_analysis_results(results):
    """Print analysis results"""
    for result in results:
        print(f"\n📊 {result.analyzer_name}")
        print(f"   {result.summary}")

        if result.plot_path:
            print(f"   📈 Plot saved: {result.plot_path}")

        if result.details:
            for line in result.details.split("\\n"):
                if line.strip():
                    print(f"   {line}")


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
