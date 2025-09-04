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

# 2. Time Event Analysis (all tickers at ti=93000000)
python main.py --csv-dir production_data --ti 93000000

# 3. Ticker Timeline Analysis (000001.SZE across all times)  
python main.py --csv-dir production_data --ticker "000001.SZE"

# 4. Deep Analysis (specific ti+ticker combination)
python main.py --csv-dir production_data --ti 93000000 --ticker "000001.SZE"
```

### Required CSV Files (Pipe-Delimited)
- `InCheckAlphaEv.csv` - Input alpha events
- `SplitAlphaEv.csv` - Split alpha events  
- `SplitCtxEv.csv` - Position context
- `MergedAlphaEv.csv` - Merged upstream alpha [optional]
- `MarketDataEv.csv` - Market data [optional]
- `PMVirtualPosEv.csv` - PM virtual positions [optional, enables T+1 constraint checking]

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

## Key Features

✅ **Auto-Loading**: Drop checkers in `checkers/` directory - no registration needed  
✅ **Multi-Interface**: Different detail levels based on parameters  
✅ **Clean Design**: Single analyzer with intelligent behavior  
✅ **Production Ready**: Robust error handling and data validation  
✅ **Extensible**: Easy to add new checkers and analyzers