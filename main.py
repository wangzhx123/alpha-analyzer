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

        # Load data
        print(f"Loading data from: {csv_dir}")
        analyzer.load_data(csv_dir)

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
