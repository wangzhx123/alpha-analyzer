# Alpha Analyzer Framework

A simple, extensible framework for analyzing trading alpha signals with event-based (ti) processing.

## Overview

This framework validates input alpha signals from PMs against output split alphas assigned to traders, ensuring data consistency and business rule compliance across time-indexed events. It supports realtime position tracking and complex validation rules.

## Quick Start

### Installation
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install pandas
```

### Usage
```bash
python main.py <data_directory>
```

### Required CSV Files
- `IncheckAlphaEv.csv` - Input alpha events (columns: ti,sid,ticker,target)
- `SplitAlphaEv.csv` - Output split events (columns: ti,sid,ticker,target)
- `RealtimePosEv.csv` - Realtime positions (columns: ti,sid,ticker,realtime_pos)

## Built-in Checkers

1. **Alpha Sum Consistency**: Verifies that total input alpha equals total output alpha for each ti event
2. **Non-Negative Trader Alpha**: Ensures all trader alpha targets are >= 0 for each ti event
3. **Volume Rounding (100 shares)**: Validates that trade volumes (target - realtime_pos) are rounded to 100 shares

## Adding New Checkers

See **[CHECKER_DEV_GUIDE.md](CHECKER_DEV_GUIDE.md)** for comprehensive development guide.

Quick example:
```python
from base_checker import BaseChecker, CheckResult

class MyCustomChecker(BaseChecker):
    @property
    def name(self) -> str:
        return "My Custom Check"
    
    def check(self, input_df: pd.DataFrame, output_df: pd.DataFrame, 
              realtime_pos_df: pd.DataFrame) -> CheckResult:
        # Your validation logic here - full access to raw DataFrames
        # Group by ti, merge dataframes, use any pandas operations
        
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
    All 2 ti events have consistent alpha sums

[PASS] Non-Negative Trader Alpha
    All 9 trader alphas are non-negative across 2 ti events

[PASS] Volume Rounding (100 shares)
    All 9 trade volumes are properly rounded to 100 shares across 2 ti events

✅ ALL CHECKS PASSED
```

### Failure Case
```
[FAIL] Volume Rounding (100 shares)
    Found 7 trade volumes not rounded to 100 shares across 2 ti events
    Details:
      ti=1001: 5 unrounded volumes
          sid=T1, ticker=AAPL: target=900.0, pos=150.0, volume=750.0 (remainder=50.0)
          sid=T1, ticker=GOOGL: target=250.0, pos=75.0, volume=175.0 (remainder=75.0)
          ...

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
├── sample_data/                     # Example CSV files
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