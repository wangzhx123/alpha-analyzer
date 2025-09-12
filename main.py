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
        "--ti", type=int, nargs='*', help="Optional: Analyze specific time events (default: all times if --ticker provided)"
    )

    parser.add_argument(
        "--ticker", nargs='*', help='Required for --analyze: Specific tickers to analyze (e.g. "000001.SSE" "000002.SSE")'
    )

    parser.add_argument(
        "--detail", action="store_true", 
        help="Dump filtered data to CSV files for inspection (saves to current directory)"
    )

    parser.add_argument(
        "--check", action="store_true",
        help="Only run checkers (skip analyzers)"
    )

    parser.add_argument(
        "--analyze", action="store_true", 
        help="Only run analyzers (skip checkers)"
    )

    parser.add_argument(
        "--sample", type=int, metavar="N",
        help="For unfiltered analysis, sample N records for performance (default: require filters)"
    )

    parser.add_argument(
        "--output", default="/tmp", 
        help="Output directory for reports and plots (default: /tmp)"
    )

    parser.add_argument(
        "--version", action="version", version="Alpha Analyzer Framework 2.0"
    )

    args = parser.parse_args()
    csv_dir = args.csv_dir

    try:
        # Initialize analyzer
        analyzer = AlphaAnalyzer()

        # Conditionally load checkers and/or analyzers
        if not args.analyze:  # Load checkers unless --analyze flag is used
            load_all_checkers(analyzer, csv_dir)
        if not args.check:   # Load analyzers unless --check flag is used
            load_all_analyzers(analyzer)

        # Load data with optional filtering for performance
        print(f"Loading data from: {csv_dir}")
        if args.ti or args.ticker:
            print(f"Applying data filters: ti={args.ti}, ticker={args.ticker}")
        
        # Handle different loading strategies for checkers vs analyzers
        if not args.analyze:
            # For checkers, use single ti/ticker filtering (checkers need consistent data)
            single_ti = args.ti[0] if args.ti else None
            single_ticker = args.ticker[0] if args.ticker else None
            analyzer.load_data(csv_dir, ti_filter=single_ti, ticker_filter=single_ticker)
        else:
            # For analyzers, we'll load data on-demand per analysis
            analyzer.csv_dir = csv_dir  # Store for on-demand loading

        # Dump filtered data if --detail requested
        if args.detail:
            dump_filtered_data(analyzer, args.ti, args.ticker, args.output)

        # Run checks only if checkers were loaded
        if not args.analyze:
            results = analyzer.run_checks()
            print_results(results)
        else:
            results = []

        # Run analysis only if analyzers were loaded
        if not args.check:
            if not args.ticker:
                print("⚠️ ANALYZERS REQUIRE TICKER FILTERING: Use --ticker TICKER for analysis")
                print("   Examples:")
                print("     --ticker 000001.SSE                    (analyze ticker across all time intervals)")
                print("     --ticker 000001.SSE 000002.SSE         (analyze multiple tickers)")
                print("     --ticker 000001.SSE --ti 940000000     (analyze ticker at specific time)")
                print("   Skipping analyzers for performance reasons.")
            else:
                # Run analysis for each combination of ti/ticker
                run_filtered_analysis(analyzer, args.ti, args.ticker, args.output)

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


def run_filtered_analysis(analyzer: AlphaAnalyzer, ti_list=None, ticker_list=None, output_dir="/tmp"):
    """Run analysis for combinations of ti/ticker filters"""
    
    from pathlib import Path
    import datetime
    
    # Create output directory structure
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    report_dir = Path(output_dir) / f"report-{timestamp}"
    report_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Reports will be saved to: {report_dir}")
    
    # Normalize inputs to lists
    ti_values = ti_list if ti_list else [None]
    ticker_values = ticker_list if ticker_list else [None]
    
    # Run analysis for each combination
    for ti in ti_values:
        for ticker in ticker_values:
            if ti and ticker:
                print(f"\n🔍 DEEP ANALYSIS: ti={ti}, ticker={ticker}")
            elif ti:
                print(f"\n📊 TIME EVENT ANALYSIS: ti={ti}")
            elif ticker:
                print(f"\n📈 TICKER ANALYSIS: {ticker}")
            
            # Load data with specific filtering for this analysis
            print(f"Loading filtered data for ti={ti}, ticker={ticker}...")
            try:
                # Pass output directory to analyzer
                analyzer.output_dir = report_dir
                analyzer.load_data(analyzer.csv_dir, ti_filter=ti, ticker_filter=ticker)
                results = analyzer.run_analysis(ti=ti, ticker=ticker)
                print_analysis_results(results)
            except Exception as e:
                print(f"❌ Analysis failed for ti={ti}, ticker={ticker}: {str(e)}")
    
    print(f"\n📊 All reports saved to: {report_dir}")


def run_analysis_mode(analyzer: AlphaAnalyzer, ti: int = None, ticker: str = None):
    """Legacy function - kept for backward compatibility"""
    run_filtered_analysis(analyzer, [ti] if ti else None, [ticker] if ticker else None)


def dump_filtered_data(analyzer: AlphaAnalyzer, ti_filter=None, ticker_filter=None, output_dir="/tmp"):
    """Dump filtered data to CSV files for inspection"""
    import os
    from datetime import datetime
    from pathlib import Path
    
    # Create debug data directory  
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    debug_dir = Path(output_dir) / f"debug-{timestamp}"
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    # Create descriptive filename suffix
    filter_desc = []
    if ti_filter:
        ti_val = ti_filter[0] if isinstance(ti_filter, list) else ti_filter
        filter_desc.append(f"ti{ti_val}")
    if ticker_filter:
        ticker_val = ticker_filter[0] if isinstance(ticker_filter, list) else ticker_filter
        filter_desc.append(f"ticker{ticker_val.replace('.', '_')}")
    
    if filter_desc:
        suffix = f"_{'_'.join(filter_desc)}_{timestamp.replace('-', '_')}"
    else:
        suffix = f"_full_{timestamp.replace('-', '_')}"
    
    print(f"\n🔍 DETAIL MODE: Dumping filtered data to {output_dir}...")
    
    # Dump each dataframe to CSV
    files_created = []
    
    if analyzer.incheck_alpha_df is not None and len(analyzer.incheck_alpha_df) > 0:
        filename = f"detail_InCheckAlphaEv{suffix}.csv"
        filepath = debug_dir / filename
        analyzer.incheck_alpha_df.to_csv(filepath, sep="|", index=False)
        files_created.append(f"{filename} ({len(analyzer.incheck_alpha_df)} records)")
    
    if analyzer.merged_df is not None and len(analyzer.merged_df) > 0:
        filename = f"detail_MergedAlphaEv{suffix}.csv"
        filepath = debug_dir / filename
        analyzer.merged_df.to_csv(filepath, sep="|", index=False)
        files_created.append(f"{filename} ({len(analyzer.merged_df)} records)")
    
    if analyzer.split_alpha_df is not None and len(analyzer.split_alpha_df) > 0:
        filename = f"detail_SplitAlphaEv{suffix}.csv"
        filepath = debug_dir / filename
        analyzer.split_alpha_df.to_csv(filepath, sep="|", index=False)
        files_created.append(f"{filename} ({len(analyzer.split_alpha_df)} records)")
    
    if analyzer.realtime_pos_df is not None and len(analyzer.realtime_pos_df) > 0:
        filename = f"detail_SplitCtxEv{suffix}.csv"
        filepath = debug_dir / filename
        analyzer.realtime_pos_df.to_csv(filepath, sep="|", index=False)
        files_created.append(f"{filename} ({len(analyzer.realtime_pos_df)} records)")
    
    if analyzer.market_df is not None and len(analyzer.market_df) > 0:
        filename = f"detail_MarketDataEv{suffix}.csv"
        filepath = debug_dir / filename
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
    
    print(f"   💾 Files saved to: {debug_dir}")


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
