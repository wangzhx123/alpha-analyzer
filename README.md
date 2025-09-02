# Alpha Analyzer Framework

A simple, extensible framework for analyzing trading alpha signals with event-based (ti) processing.

## Overview

This framework validates input alpha signals from PMs against output split alphas assigned to traders, ensuring data consistency and business rule compliance across time-indexed events. It supports realtime position tracking and complex validation rules.

## Quick Start

### Installation
```bash
# Create virtual environment with uv
uv venv
source .venv/bin/activate
uv pip install pandas pyyaml
```

### Usage
```bash
python main.py <data_directory>
```

### Required CSV Files (Production Format)
All files use pipe-delimited format (`|`):
- `InCheckAlphaEv.csv` - Input alpha events (columns: event|alphaid|time|ticker|volume)
- `MergedAlphaEv.csv` - Merged upstream alpha (columns: event|alphaid|time|ticker|volume) [optional]
- `SplitAlphaEv.csv` - Split alpha events (columns: event|alphaid|time|ticker|volume)
- `SplitCtxEv.csv` - Position context (columns: event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol)
- `MarketDataEv.csv` - Market data (columns: event|alphaid|time|ticker|last_price|prev_close_price) [optional]

## Built-in Checkers

1. **Alpha Sum Consistency**: Verifies that merged alpha sum equals split alpha sum for each time event
2. **Non-Negative Split Alpha**: Ensures all split alpha volumes are >= 0 for each time event
3. **Volume Rounding (100 shares)**: Validates that trade volumes (split_volume - realtime_pos) are rounded to 100 shares

## Adding New Checkers

See **[CHECKER_DEV_GUIDE.md](CHECKER_DEV_GUIDE.md)** for comprehensive development guide.

Quick example:
```python
from base_checker import BaseChecker, CheckResult

class MyCustomChecker(BaseChecker):
    @property
    def name(self) -> str:
        return "My Custom Check"
    
    def check(self, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame, split_alpha_df: pd.DataFrame, 
              realtime_pos_df: pd.DataFrame, market_df: pd.DataFrame = None) -> CheckResult:
        # Your validation logic here - full access to raw DataFrames
        # Group by time, merge dataframes, use any pandas operations
        
        return CheckResult(
            checker_name=self.name,
            status="PASS",  # or "FAIL", "WARN", "ERROR"
            message="Check completed successfully",
            details=None  # Optional detailed breakdown
        )
```

Then register in `main.py`:
```python
analyzer.add_checker(MyCustomChecker())
```

## Sample Output

### Success Case
```
============================================================
ALPHA ANALYZER RESULTS
============================================================
Total Checks: 3
Passed: 3
Failed: 0
Warnings: 0
Errors: 0

[PASS] Alpha Sum Consistency
    All 2 time events have consistent alpha sums

[PASS] Non-Negative Split Alpha
    All 10 split alpha volumes are non-negative across 2 time events

[PASS] Volume Rounding (100 shares)
    All 10 trade volumes are properly rounded to 100 shares across 2 time events

✅ ALL CHECKS PASSED
```

### Failure Case
```
[FAIL] Volume Rounding (100 shares)
    Found 2 trade volumes not rounded to 100 shares across 2 time events
    Details:
      time=93000000: 1 unrounded volumes
          alphaid=sSZE114Atem, ticker=000002.SZE: split=-100.0, pos=250.0, trade_vol=-350.0 (remainder=50.0)
      time=93100000: 1 unrounded volumes
          alphaid=sSZE113Atem, ticker=000001.SZE: split=9475.0, pos=1350.0, trade_vol=8125.0 (remainder=25.0)

❌ ANALYSIS FAILED - 1 critical issues
```

## Project Structure

```
alpha_analyzer/
├── analyzer.py                      # Main AlphaAnalyzer class
├── base_checker.py                  # BaseChecker interface + CheckResult
├── reporter.py                      # ConsoleReporter for formatted output
├── checkers/
│   ├── alpha_sum_consistency.py     # Sum consistency checker
│   ├── non_negative_trader.py       # Non-negative checker
│   └── volume_rounding.py           # Volume rounding checker
├── production_data/                 # Example CSV files
├── main.py                          # Entry point
├── requirements.txt                 # Dependencies
├── CHECKER_DEV_GUIDE.md            # Comprehensive development guide
└── README.md                       # This file
```

## Key Features

- **Simple Interface**: Just implement one `check()` method
- **Full Data Access**: Raw pandas DataFrames for maximum flexibility  
- **Event-based Processing**: Built-in support for time-indexed (ti) validation
- **Extensible**: Drop in new checkers with zero framework changes
- **Clear Reporting**: Color-coded console output with detailed failure information
- **Production Ready**: Error handling, data validation, and robust CSV loading