# Alpha Analyzer Framework - System Design Document

## Executive Summary

The Alpha Analyzer Framework is a trading signal validation and analysis system designed for institutional trading operations. It validates the integrity of alpha signal distribution from Portfolio Managers (PMs) to individual traders and provides diagnostic capabilities for performance analysis.

## Business Context

### Trading Flow Overview
```
Portfolio Manager (PM) → Alpha Signal Generation → Signal Distribution → Trader Execution → Performance Analysis
                                  ↓                        ↓                    ↓
                            Merged Alpha              Split Alpha        Position Changes
                          (Consolidated)           (Per Trader)        (Actual Trades)
```

### Key Business Entities

1. **Portfolio Manager (PM)**: Generates high-level alpha signals for target positions
2. **Alpha Signal**: Desired absolute position target for a ticker at a specific time
3. **Trader/AlphaID**: Individual execution entity responsible for a portion of the alpha
4. **Time Event (ti)**: Discrete trading periods (e.g., 93000000 = 9:30:00 AM)
5. **Position**: Actual holdings vs. intended targets

## Data Flow Architecture

### Input Data Sources
```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   InCheckAlphaEv    │    │   MergedAlphaEv      │    │   SplitAlphaEv      │
│  (Input Signals)    │    │ (Consolidated Alpha) │    │ (Trader Allocation) │
│                     │    │                      │    │                     │
│ event|alphaid|time  │    │ event|alphaid|time   │    │ event|alphaid|time  │
│ ticker|volume       │    │ ticker|volume        │    │ ticker|volume       │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
           │                           │                           │
           └───────────────┬───────────────────┬───────────────────┘
                          │                   │
                          ▼                   ▼
                ┌─────────────────────┐    ┌─────────────────────┐
                │   SplitCtxEv        │    │   MarketDataEv      │
                │ (Position Context)  │    │  (Market Prices)    │
                │                     │    │                     │
                │ event|alphaid|time  │    │ event|alphaid|time  │
                │ ticker|realtime_pos │    │ ticker|last_price   │
                │ |realtime_long_pos  │    │ |prev_close_price   │
                │ |realtime_short_pos │    │                     │
                │ |realtime_avail_...│    │                     │
                └─────────────────────┘    └─────────────────────┘
```

### Optional Constraint Data
```
┌──────────────────────────┐
│   VposResEv              │
│ (PM Virtual Positions)   │
│                          │
│ time|ticker              │
│ |vpos                    │
│                          │
│ Special: time = -1       │
│ represents previous      │
│ day closing positions    │
└──────────────────────────┘
```

## Core Business Logic

### 1. Alpha Signal Distribution
**Concept**: PM generates a target position (alpha) which gets distributed among multiple traders.

```
PM Alpha Target: 28,000 shares AAPL
       ↓
Split Distribution:
├── Trader A (sSZE113): 14,000 shares
└── Trader B (sSZE114): 14,000 shares

Validation: Sum(Split Alpha) must equal Merged Alpha
```

### 2. Fill Rate Analysis
**Core Formula**: 
```
Fill Rate = Position_Change / Target_Alpha

Where:
- Position_Change = realtime_pos[T+1] - realtime_pos[T]  
- Target_Alpha = absolute position target from Split Alpha
- Time Offset: Compare time T alpha with time T+1 position
```

**Business Meaning**:
- Fill Rate = 1.0: Perfect execution (100% of target achieved)
- Fill Rate = 0.5: Under-filled (50% of target achieved)  
- Fill Rate = 1.2: Over-filled (120% of target achieved)
- Fill Rate = 0.0: No execution

### 3. T+1 Constraint (Risk Management)
**Rule**: PM cannot sell more shares than available from previous day position.

```
Constraint Logic:
1. Get closing position from previous day (time = -1)
2. Calculate required trade: trade_volume = target_alpha - current_vpos  
3. If trade_volume < 0 (selling):
   └── Assert: |trade_volume| ≤ previous_day_position

Business Purpose: Prevents naked short selling and over-leverage
```

### 4. Volume Rounding Rules
**Rule**: All trade volumes must be rounded to 100-share lots.

```
Trade Volume = split_volume - realtime_pos
Validation: Trade Volume % 100 == 0

Example:
- Target: 14,500 shares
- Current: 14,350 shares  
- Trade: 150 shares ✓ (divisible by 100)
```

## System Architecture

### Component Design
```
┌─────────────────────────────────────────────────────────────────┐
│                        Alpha Analyzer Framework                  │
├─────────────────────────────────────────────────────────────────┤
│                           main.py                               │
│                   (CLI Interface + Auto-Loading)                │
├─────────────────────────────────────────────────────────────────┤
│                        AlphaAnalyzer                            │
│                   (Data Loading + Orchestration)                │
├─────────────┬───────────────────────────┬───────────────────────┤
│   Checkers  │                          │      Analyzers        │
│ (Validation)│                          │    (Insights)         │
│             │                          │                       │
│  ┌─────────┐│     ┌─────────────────┐   │   ┌──────────────────┐│
│  │ Alpha   ││     │                 │   │   │   Fill Rate      ││
│  │ Sum     ││     │   Base Classes  │   │   │   Analyzer       ││
│  │Consistency    │                 │   │   │                  ││
│  └─────────┘│     │  ┌─────────────┐│   │   │ 4 Interfaces:    ││
│             │     │  │BaseChecker  ││   │   │ • Overview       ││
│  ┌─────────┐│     │  └─────────────┘│   │   │ • Time Event     ││
│  │Non-Neg  ││     │  ┌─────────────┐│   │   │ • Ticker Timeline││
│  │Split    ││     │  │BaseAnalyzer ││   │   │ • Deep Analysis  ││
│  │Alpha    ││     │  └─────────────┘│   │   └──────────────────┘│
│  └─────────┘│     │                 │   │                       │
│             │     │                 │   │   ┌──────────────────┐│
│  ┌─────────┐│     │                 │   │   │   Future         ││
│  │Volume   ││     │                 │   │   │   Analyzers      ││
│  │Rounding ││     │                 │   │   │   (Market Impact,││
│  └─────────┘│     │                 │   │   │    Risk, etc.)   ││
│             │     │                 │   │   └──────────────────┘│
│  ┌─────────┐│     │                 │   │                       │
│  │PM T+1   ││     │                 │   │                       │
│  │Constraint│     │                 │   │                       │
│  └─────────┘│     └─────────────────┘   │                       │
└─────────────┴───────────────────────────┴───────────────────────┘
```

### Interface Architecture

#### Four Analysis Dimensions
```
┌──────────────┬─────────────────┬──────────────────────────────────┐
│  Interface   │     Scope       │            Use Case              │
├──────────────┼─────────────────┼──────────────────────────────────┤
│ Overview     │ All × All       │ High-level system health         │
│              │ (tickers×times) │ Overall performance metrics      │
├──────────────┼─────────────────┼──────────────────────────────────┤
│ Time Event   │ All × Specific  │ Alpha allocation at specific time│
│              │ (tickers×ti)    │ Cross-ticker performance compare │
├──────────────┼─────────────────┼──────────────────────────────────┤
│ Ticker       │ Specific × All  │ Ticker performance over time     │
│ Timeline     │ (ticker×times)  │ Trend analysis, consistency      │
├──────────────┼─────────────────┼──────────────────────────────────┤
│ Deep         │ Specific × Spec │ Detailed diagnostics             │
│ Analysis     │ (ticker×ti)     │ Trade-by-trade breakdown         │
└──────────────┴─────────────────┴──────────────────────────────────┘
```

## Data Processing Pipeline

### Phase 1: Data Ingestion & Validation
```
CSV Files → Pipe Delimiter Parsing → Column Validation → Data Type Conversion
     ↓               ↓                        ↓                     ↓
File exists?    Correct format?       Required columns?    Time preprocessing
                                                          ('nil_last_alpha' → -1)
```

### Phase 2: Validation (Checkers)
```
All Data → Parallel Checker Execution → Results Aggregation → Pass/Fail Status
    ↓              ↓                          ↓                    ↓
Load once    Independent validation    Color-coded output    Exit code for CI/CD
```

### Phase 3: Analysis (Analyzers)  
```
All Data + Interface Parameters → Analyzer Selection → Analysis Execution → Visualization
       ↓                              ↓                     ↓                ↓
Complete dataset              Based on ti/ticker        Custom logic     Plots + Metrics
                             combination provided      per interface
```

## Business Rules Implementation

### 1. Alpha Conservation Law
```python
# Business Rule: Total alpha must be conserved through distribution
for each time_event:
    merged_alpha_sum = sum(MergedAlphaEv[time_event].volume)
    split_alpha_sum = sum(SplitAlphaEv[time_event].volume)
    assert abs(merged_alpha_sum - split_alpha_sum) < tolerance
```

### 2. Non-Negative Position Rule  
```python
# Business Rule: Traders cannot hold negative split positions
for each split_alpha_event:
    assert split_alpha_event.volume >= 0
```

### 3. Fill Rate Calculation
```python
# Business Logic: Measure execution effectiveness
def calculate_fill_rate(target_alpha, position_t, position_t1):
    position_change = position_t1 - position_t
    if abs(target_alpha) < 1e-6:  # Avoid division by zero
        return 0.0
    return position_change / target_alpha
```

### 4. Risk Constraint Enforcement
```python
# Business Rule: T+1 sellable constraint
def validate_pm_constraint(target_alpha, current_pos, previous_day_pos):
    required_trade = target_alpha - current_pos
    if required_trade < 0:  # Selling position
        max_sellable = previous_day_pos
        assert abs(required_trade) <= max_sellable
```

## Performance Metrics & KPIs

### System Health Metrics
- **Validation Pass Rate**: % of checks passing
- **Data Completeness**: % of expected records present
- **Processing Time**: End-to-end analysis duration

### Trading Performance Metrics
- **Mean Fill Rate**: Average execution effectiveness
- **Fill Rate Distribution**: Spread of execution quality
- **Perfect Fill Rate**: % of trades with 95-105% fill rate
- **Execution Consistency**: Standard deviation of fill rates

### Risk Metrics
- **Constraint Violations**: Count of T+1 rule violations
- **Position Drift**: Deviation from intended targets
- **Rounding Compliance**: % of properly rounded trades

## Usage Patterns & Operations

### Production Validation Pipeline
```bash
# Automated validation in CI/CD
python main.py --csv-dir /prod/data/2024-01-15
# Exit code 0 = success, 1 = failure
# Blocking deployment if critical issues found
```

### Diagnostic Investigation
```bash
# Deep dive into specific issues
python main.py --csv-dir /prod/data/2024-01-15 --ti 93000000 --ticker "AAPL"
# Detailed trade-by-trade analysis
# Visual plots for pattern recognition
```

### Performance Monitoring
```bash
# Regular performance assessment  
python main.py --csv-dir /prod/data/2024-01-15 --ticker "AAPL"
# Timeline analysis for trend identification
# Fill rate deterioration detection
```

## Extensibility Points

### Adding New Checkers
```python
class CustomChecker(BaseChecker):
    def check(self, ...): 
        # Custom validation logic
        return CheckResult(...)
        
# Drop in checkers/ directory → Auto-loaded
```

### Adding New Analyzers
```python  
class MarketImpactAnalyzer(BaseAnalyzer):
    def supports_overview(self): return False
    def supports_deep_analysis(self): return True
    
    def _analyze_deep(self, ti, ticker, ...):
        # Price impact analysis for specific trades
        return AnalysisResult(...)
        
# Drop in analyzers/ directory → Auto-loaded
```

## Security & Compliance Considerations

### Data Protection
- No credential discovery capabilities
- Defensive security focus only
- Production data isolation

### Audit Trail
- Structured result logging
- Configuration-free operation
- Deterministic analysis results

### Risk Management
- Built-in constraint validation
- Over-leverage prevention
- Position limit enforcement

## Future Enhancement Opportunities

### Advanced Analytics
- **Market Impact Analysis**: Price movement correlation with trade size
- **Latency Analysis**: Execution delay impact on performance  
- **Risk Attribution**: Position concentration and diversification metrics
- **Regime Analysis**: Performance across different market conditions

### Operational Improvements
- **Real-time Processing**: Stream processing for live validation
- **Dashboard Integration**: Web interface for interactive analysis
- **Alert System**: Automated notification for threshold breaches
- **Historical Trending**: Long-term performance pattern recognition

This system provides a robust foundation for alpha signal validation and trading performance analysis while maintaining clean architecture for future enhancements.