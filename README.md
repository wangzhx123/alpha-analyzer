# Alpha Analyzer Framework

A clean, multi-interface framework for validating and analyzing trading alpha signals with event-based processing.

## Design Philosophy

**Two Primary Use Cases:**
1. **Post-Check (Validation)**: Automated validation in production pipelines  
2. **Post-Analyze (Diagnostic)**: Deep investigation of production issues

**Four Analysis Interfaces:**
- **Overview**: All tickers, all times (high-level insights)
- **Time Event**: All tickers at specific time (allocation analysis)  
- **Ticker Timeline**: Specific ticker across all times (performance trends)
- **Deep Analysis**: Specific time + ticker (detailed diagnostics)

## Quick Start

### Installation
```bash
uv venv && source .venv/bin/activate
uv pip install pandas matplotlib
```

### Usage Patterns
```bash
# 1. Validation + Overview Analysis
python main.py --csv-dir production_data

# 2. Time Event Analysis (all tickers at ti=930000000)
python main.py --csv-dir production_data --ti 930000000

# 3. Ticker Timeline Analysis (000001.SSE across all times)  
python main.py --csv-dir production_data --ticker "000001.SSE"

# 4. Deep Analysis (specific ti+ticker combination)
python main.py --csv-dir production_data --ti 930000000 --ticker "000001.SSE"

# 5. Debug Mode - Export filtered data for inspection
python main.py --csv-dir production_data --ticker "000001.SSE" --detail
```

### Required CSV Files (Pipe-Delimited)
- `InCheckAlphaEv.csv` - Input alpha events
- `SplitAlphaEv.csv` - Split alpha events  
- `SplitCtxEv.csv` - Position context
- `MergedAlphaEv.csv` - Merged upstream alpha [optional]
- `MarketDataEv.csv` - Market data [optional]
- `VposResEv.csv` - PM virtual positions [optional, enables T+1 constraint checking]

## Auto-Loaded Checkers

**All checkers in `checkers/` directory are automatically loaded:**

1. **Alpha Sum Consistency**: Merged alpha sum = split alpha sum per time event
2. **Non-Negative Split Alpha**: All split volumes ≥ 0  
3. **Volume Rounding**: Trade volumes rounded to 100 shares
4. **PM T+1 Sellable Constraint**: PM can't sell more than previous day position

## Analysis Interfaces

### Interface 1: Overview Analysis
**Scope**: All tickers across all time periods  
**Usage**: `--csv-dir production_data`
```
📊 Fill Rate Overview (All Tickers & Times):
   Total trades: 6 | Analyzable: 6
   Mean fill rate: 0.007
   Best performer: 000002.SZE (0.012)
   Worst performer: 000001.SZE (0.000)
   📈 Plot saved: fill_rate_overview.png
```

### Interface 2: Time Event Analysis  
**Scope**: All tickers at specific time event  
**Usage**: `--csv-dir production_data --ti 93000000`
```
📊 Fill Rate Analysis (ti=93000000, All Tickers):
   Tickers analyzed: 3
   Overall mean fill rate: 0.008
   Per-ticker performance:
     000001.SZE: 0.000 (2 trades)
     000002.SZE: 0.012 (2 trades)
     000003.SZE: 0.011 (1 trades)
   📈 Plot saved: fill_rate_ti_93000000.png
```

### Interface 3: Ticker Timeline Analysis
**Scope**: Specific ticker across all time periods  
**Usage**: `--csv-dir production_data --ticker "000001.SZE"`
```
📊 Fill Rate Timeline (000001.SZE, All Times):
   Time periods: 2
   Overall mean fill rate: 0.005
   Timeline performance:
     ti=93000000: 0.000 (2 trades)
     ti=93100000: 0.011 (2 trades)
   📈 Plot saved: fill_rate_000001.SZE.png
```

### Interface 4: Deep Analysis
**Scope**: Specific time + ticker combination  
**Usage**: `--csv-dir production_data --ti 93000000 --ticker "000001.SZE"`
```
📊 Detailed Fill Analysis (ti=93000000, ticker=000001.SZE):
   Trade-by-trade breakdown:
     sSZE113Atem: target=14000, actual=0, fill_rate=0.000
     sSZE114Atem: target=14000, actual=0, fill_rate=0.000
   📈 Detailed plot saved: fill_rate_detailed_93000000_000001.SZE.png
```

## Architecture

```
alpha_analyzer/
├── main.py                    # Entry point with auto-loading
├── analyzer.py               # Multi-interface analyzer
├── base_checker.py          # Checker interface
├── checkers/                # Auto-loaded validation plugins
│   ├── alpha_sum_consistency.py
│   ├── non_negative_trader.py  
│   ├── volume_rounding.py
│   └── pm_constraint_checker.py
└── production_data/         # Sample CSV files
```

## Fill Rate Analysis Logic

**Core Concept**: Compare alpha targets at time T with actual position changes at time T+1
- **Target Alpha**: Absolute position target (from `SplitAlphaEv.csv`)
- **Position Change**: `realtime_pos[T+1] - realtime_pos[T]` (from `SplitCtxEv.csv`)
- **Fill Rate**: `position_change / target_alpha`

**Interface-Specific Analysis**:
- **Overview**: Distribution histogram, best/worst performers
- **Time Event**: Bar chart comparing tickers at specific time
- **Ticker Timeline**: Line chart showing performance over time  
- **Deep Analysis**: 2x2 dashboard with detailed breakdown

## Performance Features

### 🚀 **Smart Data Filtering**
The analyzer now includes intelligent filtering for massive performance improvements:

- **Time Filtering (`--ti`)**: Process only specific time events (99%+ data reduction)
- **Ticker Filtering (`--ticker`)**: Process only specific tickers (99%+ data reduction)  
- **Combined Filtering**: Process specific time+ticker combinations for focused analysis
- **Progress Indicators**: Real-time feedback showing exactly what's being processed

### 📊 **Debug & Inspection Tools**

- **`--detail` Flag**: Export filtered data to `/tmp/` for inspection
- **Timestamped Files**: Automatic file naming with filters and timestamps
- **Summary Reports**: Comprehensive data range and filter summaries
- **Clean Output**: All debug files and plots saved to `/tmp/` (no workspace clutter)

### ⚡ **Example Performance Gains**
```bash
# Large dataset: 944K records → 218 records (99.98% reduction)
python main.py --csv-dir final_pressure_test --ticker "000001.SSE"

# Time-specific: 944K records → 36K records (96% reduction)  
python main.py --csv-dir final_pressure_test --ti 930000000

# Deep analysis: 944K records → 8 records (99.999% reduction)
python main.py --csv-dir final_pressure_test --ti 930000000 --ticker "000001.SSE"
```

## Key Features

✅ **Auto-Loading**: Drop checkers in `checkers/` directory - no registration needed  
✅ **Multi-Interface**: Different detail levels based on parameters  
✅ **Smart Filtering**: Massive performance gains through intelligent data filtering
✅ **Debug Tools**: Export filtered data and plots for detailed inspection
✅ **Progress Tracking**: Real-time feedback on data processing steps
✅ **Clean Design**: Single analyzer with intelligent behavior  
✅ **Production Ready**: Robust error handling and data validation  
✅ **Extensible**: Easy to add new checkers and analyzers

## Pressure Testing

### Generate Test Data
```bash
# Generate realistic China stock market test data
python generate_test_data.py --output-dir my_test_data --tickers 3000

# Generates:
# - 3,000 tickers (000001.SSE to 003000.SSE)
# - 5 Portfolio Managers (sSZE111BUCS to sSZE115BUCS)  
# - 5 Traders (sSZE111Atem to sSZE115Atem)
# - 26 time events (9:30-11:30, 13:00-15:00, 10min intervals)
# - ~944K records, ~42MB realistic trading data
```

### Test Data Features
- ✅ **No Short Selling**: All volumes ≥ 0 (China market compliance)
- ✅ **Realistic Fill Rates**: 80-90% execution efficiency  
- ✅ **Proper Time Encoding**: Valid China trading hours (930000000 = 9:30 AM)
- ✅ **Business Rule Compliance**: Exactly 2 traders per allocation, 100-share lots
- ✅ **T+1 Constraints**: Previous day positions for realistic constraint testing