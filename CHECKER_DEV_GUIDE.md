# Alpha Analyzer - Checker Development Guide

## Overview

The Alpha Analyzer framework provides a simple, extensible system for validating trading alpha signals through event-based (ti) processing. This guide shows how to develop custom checkers for your specific validation needs.

## Framework Architecture

### Core Components
- **AlphaAnalyzer**: Main orchestrator, loads CSV data and executes checkers
- **BaseChecker**: Abstract interface that all checkers must implement
- **CheckResult**: Standardized result format for all checker outputs
- **ConsoleReporter**: Formats and displays results with color coding

### Data Flow
1. **Input Data**: `InCheckAlphaEv.csv` - Raw alpha signals from upstream (event|alphaid|time|ticker|volume)
2. **Merged Data**: `MergedAlphaEv.csv` - Consolidated upstream alphas (event|alphaid|time|ticker|volume)
3. **Split Data**: `SplitAlphaEv.csv` - Split alphas to traders (event|alphaid|time|ticker|volume)
4. **Position Data**: `SplitCtxEv.csv` - Current positions and context (event|alphaid|time|ticker|realtime_pos|...)
5. **Market Data**: `MarketDataEv.csv` - Market prices (event|alphaid|time|ticker|last_price|prev_close_price) [optional]
6. **Validation**: Checkers analyze data per time event using pipe-delimited CSV format
7. **Reporting**: Results aggregated and displayed with pass/fail status

## Implementing a Custom Checker

### 1. Basic Checker Structure

```python
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_checker import BaseChecker, CheckResult

class MyCustomChecker(BaseChecker):
    @property
    def name(self) -> str:
        return "My Custom Validation"
    
    def check(self, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame, split_alpha_df: pd.DataFrame,
              realtime_pos_df: pd.DataFrame, market_df: pd.DataFrame = None) -> CheckResult:
        # Your validation logic here
        
        return CheckResult(
            checker_name=self.name,
            status="PASS",  # or "FAIL", "WARN", "ERROR"
            message="Validation completed",
            details=None  # Optional detailed breakdown
        )
```

### 2. CheckResult Status Codes
- **PASS**: Validation successful
- **FAIL**: Critical validation failure
- **WARN**: Non-critical issue detected
- **ERROR**: Checker encountered an exception

### 3. Working with DataFrames

You have full access to raw pandas DataFrames with these guaranteed columns:

**InCheck Alpha DataFrame (incheck_alpha_df)** - InCheckAlphaEv.csv:
- `event`: Event type (InCheckAlphaEv)
- `alphaid`: Alpha source identifier
- `time`: Time event index
- `ticker`: Trading symbol
- `volume`: Alpha volume

**Merged DataFrame (merged_df)** - MergedAlphaEv.csv:
- `event`: Event type (MergedAlphaEv)
- `alphaid`: Merged alpha identifier
- `time`: Time event index
- `ticker`: Trading symbol
- `volume`: Merged alpha volume

**Split Alpha DataFrame (split_alpha_df)** - SplitAlphaEv.csv:
- `event`: Event type (SplitAlphaEv)
- `alphaid`: Split alpha destination identifier
- `time`: Time event index
- `ticker`: Trading symbol
- `volume`: Split alpha volume

**Position DataFrame (realtime_pos_df)** - SplitCtxEv.csv:
- `event`: Event type (SplitCtxEv)
- `alphaid`: Trader identifier
- `time`: Time event index
- `ticker`: Trading symbol
- `realtime_pos`: Current position size
- `realtime_long_pos`: Long position size
- `realtime_short_pos`: Short position size
- `realtime_avail_shot_vol`: Available short volume

**Market DataFrame (market_df)** - MarketDataEv.csv [Optional]:
- `event`: Event type (MarketDataEv)
- `alphaid`: Market data source identifier
- `time`: Time event index
- `ticker`: Trading symbol
- `last_price`: Latest market price
- `prev_close_price`: Previous close price

### 4. Common Validation Patterns

#### Per-Time Event Validation
```python
def check(self, incheck_alpha_df, merged_df, split_alpha_df, realtime_pos_df, market_df=None):
    violations = []
    
    for time in merged_df['time'].unique():
        time_incheck = incheck_alpha_df[incheck_alpha_df['time'] == time]
        time_merged = merged_df[merged_df['time'] == time]
        time_split = split_alpha_df[split_alpha_df['time'] == time]
        time_positions = realtime_pos_df[realtime_pos_df['time'] == time]
        
        # Your per-event logic here
        if some_condition_fails:
            violations.append(f"time={time}: violation description")
    
    if violations:
        return CheckResult(
            checker_name=self.name,
            status="FAIL",
            message=f"Found {len(violations)} violations",
            details="\n".join(violations)
        )
    else:
        return CheckResult(
            checker_name=self.name,
            status="PASS",
            message="All validations passed"
        )
```

#### Data Merging for Complex Checks
```python
def check(self, incheck_alpha_df, merged_df, split_alpha_df, realtime_pos_df, market_df=None):
    # Merge split alphas with positions to calculate trade volumes
    merged = split_alpha_df.merge(
        realtime_pos_df,
        on=['time', 'alphaid', 'ticker'],
        how='left'
    )
    merged['realtime_pos'] = merged['realtime_pos'].fillna(0.0)
    merged['trade_volume'] = merged['volume'] - merged['realtime_pos']
    
    # Now validate the calculated trade_volume
    # ...
```

#### Statistical Validation
```python
def check(self, incheck_alpha_df, merged_df, split_alpha_df, realtime_pos_df, market_df=None):
    # Example: Check for outliers in volume values
    for time in split_alpha_df['time'].unique():
        time_data = split_alpha_df[split_alpha_df['time'] == time]
        volumes = time_data['volume'].abs()
        
        q75, q25 = volumes.quantile([0.75, 0.25])
        iqr = q75 - q25
        upper_bound = q75 + 1.5 * iqr
        
        outliers = time_data[time_data['volume'].abs() > upper_bound]
        if len(outliers) > 0:
            # Report outliers...
```

## Built-in Checkers

### 1. AlphaSumConsistencyChecker
- **Purpose**: Ensures total input alpha equals total output alpha per ti
- **Logic**: `sum(input_targets_per_ti) == sum(output_targets_per_ti)`
- **Use Case**: Verify no alpha is lost or created during split process

### 2. NonNegativeTraderChecker  
- **Purpose**: Ensures all trader alpha targets are non-negative
- **Logic**: `all(output_targets >= 0)`
- **Use Case**: Enforce business rule against short positions

### 3. VolumeRoundingChecker
- **Purpose**: Validates trade volumes are rounded to 100 shares
- **Logic**: `(target - realtime_pos) % 100 == 0`
- **Use Case**: Ensure compliance with lot size requirements

## Deployment Steps

### 1. Create Your Checker
```bash
# Create new checker file
touch checkers/my_custom_checker.py
```

### 2. Implement the Logic
```python
# Follow the patterns shown above
```

### 3. Register the Checker
```python
# In main.py, add:
from checkers.my_custom_checker import MyCustomChecker

# In the main() function:
analyzer.add_checker(MyCustomChecker())
```

### 4. Test Your Checker
```bash
python3 main.py sample_data
```

## Best Practices

### Error Handling
```python
def check(self, input_df, output_df, realtime_pos_df):
    try:
        # Your validation logic
        result = perform_validation()
        return CheckResult(...)
    except Exception as e:
        # Framework will catch this and report as ERROR
        raise ValueError(f"Validation failed: {str(e)}")
```

### Performance Considerations
- Use vectorized pandas operations instead of loops where possible
- Group operations by `ti` for event-based processing
- Cache expensive calculations when checking multiple conditions

### Reporting Guidelines
- **Message**: Concise summary (1 line)
- **Details**: Specific violations with context (ti, sid, ticker)
- **Limit Details**: Show first 5-10 violations per ti to avoid spam
- **Include Counts**: Always mention how many items failed

### Testing Your Checker
1. **Happy Path**: Create data that should pass
2. **Failure Cases**: Create data with known violations
3. **Edge Cases**: Empty data, missing tickers, single ti events
4. **Error Cases**: Invalid data types, missing columns

## Example: Risk Limit Checker

```python
class RiskLimitChecker(BaseChecker):
    def __init__(self, max_position_size=1000000):
        self.max_position_size = max_position_size
    
    @property
    def name(self) -> str:
        return f"Risk Limit (max {self.max_position_size:,})"
    
    def check(self, input_df, output_df, realtime_pos_df):
        # Calculate final positions: realtime_pos + trade_volume
        merged = output_df.merge(
            realtime_pos_df,
            on=['ti', 'sid', 'ticker'],
            how='left'
        )
        merged['realtime_pos'] = merged['realtime_pos'].fillna(0.0)
        merged['final_position'] = merged['realtime_pos'] + (merged['target'] - merged['realtime_pos'])
        
        # Find positions exceeding limit
        violations = merged[merged['final_position'].abs() > self.max_position_size]
        
        if len(violations) > 0:
            details = []
            for ti in violations['ti'].unique():
                ti_violations = violations[violations['ti'] == ti]
                details.append(f"ti={ti}: {len(ti_violations)} positions exceed limit")
                
                for _, row in ti_violations.head(3).iterrows():
                    details.append(
                        f"  {row['sid']}/{row['ticker']}: "
                        f"final_pos={row['final_position']:,.0f}"
                    )
            
            return CheckResult(
                checker_name=self.name,
                status="FAIL",
                message=f"Found {len(violations)} positions exceeding risk limit",
                details="\n".join(details)
            )
        else:
            return CheckResult(
                checker_name=self.name,
                status="PASS",
                message=f"All positions within {self.max_position_size:,} limit"
            )
```

## Framework Extension Points

### Custom Data Sources
- Modify `AlphaAnalyzer.load_data()` to support additional CSV files
- Update `BaseChecker.check()` signature to pass new data
- Maintain backward compatibility by making new parameters optional

### Custom Reporting
- Extend `ConsoleReporter` or create new reporter classes
- Add JSON, HTML, or database output formats
- Implement alerting systems for critical failures

### Dynamic Checker Loading
- Implement plugin system to auto-discover checkers
- Add configuration file support for checker parameters
- Enable/disable checkers based on environment

## Troubleshooting

### Common Issues
1. **Import Errors**: Check sys.path.append() in your checker file
2. **DataFrame Columns**: Verify expected columns exist before accessing
3. **Missing Data**: Handle cases where merges return empty results
4. **Floating Point**: Use tolerance when comparing decimal values

### Debugging Tips
- Print DataFrame shapes and columns during development
- Use `.head()` and `.describe()` to inspect data
- Test with minimal sample data first
- Add logging for complex validation logic

This framework provides maximum flexibility while maintaining simplicity - you have full access to raw data and complete control over validation logic!