# Alpha Analyzer Framework

A **production-ready validation framework** for analyzing merge/split alpha trading systems. This framework is designed to validate both simulated test data and real production CSV exports from institutional trading platforms.

## **🎯 Project Purpose & Motivation**

### **Production Reality**
In production environments, sophisticated institutional trading platforms generate CSV exports containing:
- PM alpha signals from multiple Portfolio Managers
- Merged alpha results from complex consolidation algorithms
- Split alpha allocations using advanced risk-weighted distribution
- Trader execution results with real market constraints
- Position attribution data with complex reverse-mapping logic

### **Framework Goals**
1. **Validate Production Data**: Ensure data consistency, position balance, and signal flow correctness
2. **Performance Analysis**: Measure execution quality, fill rates, and system effectiveness
3. **System Validation**: Detect issues in merge/split logic before they impact trading
4. **Regulatory Compliance**: Verify T+1 constraints, position limits, and audit trail completeness

### **Current Implementation Status**
- ✅ **Production-Ready Framework**: Checkers and analyzers designed for real data validation
- ✅ **Test Data Generation**: Simplified algorithms create structurally correct test data
- 🔄 **Evolution Path**: Gradually enhance test data generation to match production complexity
- 🎯 **End Goal**: Framework seamlessly validates real production CSV exports

## **🏗️ System Architecture Overview**

### **Production Merge/Split Alpha Trading System**
The framework analyzes systems with this architecture:
1. **Multiple Portfolio Managers (PMs)** generate alpha signals (target positions)
2. **Merge System** consolidates PM signals using sophisticated algorithms
3. **Split System** distributes consolidated signals using risk-weighted allocation
4. **Traders** execute signals with real market constraints and capacity limits
5. **Position Attribution** reverse-maps trader results back to PM strategies

### **Framework Components**
```
🏭 Production System     📊 Analysis Framework     📈 Validation Results
├─ PM Alpha Generation   ├─ Data Loading           ├─ Fill Rate Analysis
├─ Merge Processing      ├─ Consistency Checkers   ├─ Position Validation
├─ Split Allocation      ├─ Performance Analyzers  ├─ Signal Flow Checks
├─ Trader Execution      ├─ Interactive Reporting  ├─ System Health Metrics
└─ Position Attribution  └─ Export Generation      └─ Compliance Validation
```

### **Current vs Production Data**
- **Test Data** (generated): Uses simplified algorithms for merge/split logic
- **Production Data** (future): Complex institutional trading system exports
- **Framework** (current): Handles both - designed for production complexity

## **Quick Start**

### **Generate Sample Data**
```bash
# Generate sample data with default settings (5 PMs, 5 traders, 100 tickers)
python3 generate_sample_data.py --num-tickers 100

# Custom configuration
python3 generate_sample_data.py --num-pm 10 --num-trader 8 --num-tickers 500 --fill-rate-min 0.85 --fill-rate-max 0.95
```

### **Analyze Data**
```bash
# Analyze single ticker across all time intervals
python3 main.py --csv-dir sample_data --analyze --ticker 000001.SSE --output /tmp

# Analyze multiple tickers  
python3 main.py --csv-dir sample_data --analyze --ticker 000001.SSE 000002.SSE --output /tmp

# Analyze specific time intervals
python3 main.py --csv-dir sample_data --analyze --ticker 000001.SSE --ti 940000000 950000000 --output /tmp
```

### **View Results**
Analysis generates timestamped reports in `/tmp/report-YYYYMMDD-HHMMSS/`:
- `fill_rate_TICKER.png` - Fill rate timeline charts
- `detail_report.txt` - Complete analysis details  
- `interactive_fill_rate_TICKER.html` - Interactive plots

## **System Architecture**

```
PMs → Alpha Signals → Merge → Split → Traders → Execution
 ↓         ↓           ↓       ↓        ↓         ↓
InCheck  MergedAlpha  Split  SplitCtx  VposRes  Analysis
```

### **Key Components**

- **Portfolio Managers (PMs)**: Generate target position signals with TVR logic
- **Merge System**: Consolidates PM signals by summing targets per ticker/time
- **Split System**: Divides merged targets evenly across all traders
- **Traders**: Execute signals with realistic fill rates (0.8-0.9)
- **Position Tracking**: Ensures PM virtual positions = Sum(trader positions)

### **📁 Data Files (CSV Format)**

> **Note**: These files can be either generated test data (current) or production system exports (future)

| File | Description | Key Field |
| `InCheckAlphaEv.csv` | PM alpha signals | Target positions |
| `MergedAlphaEv.csv` | Consolidated signals | Sum of PM targets |
| `SplitAlphaEv.csv` | Trader alpha signals | Even split of merged |
| `SplitCtxEv.csv` | Actual trader positions | Execution results |
| `VposResEv.csv` | PM virtual positions | Sum of trader positions |
| `MarketDataEv.csv` | Market price data | Price context |

## **Analysis Features**

### **Fill Rate Analysis**
- **Primary Metric**: Execution quality measurement
- **Calculation**: `Fill Rate = Actual Trade / Intended Trade`  
- **Expected Range**: 0.8-0.9 for realistic systems
- **Outputs**: Timeline charts, statistical summaries

### **System Validation**
- **Data Consistency**: Validates alignment between CSV files
- **Position Balance**: Ensures mathematical consistency
- **Signal Flow**: Validates merge/split calculations

### **Performance Insights**
- **Trade Counting**: Number of executed trades per interval
- **Direction Consistency**: Validates buy/sell adherence
- **Temporal Patterns**: Identifies performance trends over time

## **⚙️ Configuration**

### **Test Data Generation Parameters**
> **Note**: These parameters control the simplified test data generation. Production systems use more complex algorithms.
```bash
--num-pm            # Number of Portfolio Managers (default: 5)
--num-trader        # Number of traders (default: 5) 
--num-tickers       # Total ticker universe size (default: 1000)
--ti-ranges         # Trading time ranges (default: morning + afternoon)
--ti-interval       # Time step in nanoseconds (default: 10 minutes)
--fill-rate-min/max # Fill rate range (default: 0.8-0.9)
--tvr-min/max       # TVR change range (default: 0.1-0.6)
```

### **Analysis Options**
```bash
--csv-dir           # Data directory (required)
--analyze           # Run analyzers only
--ticker            # Specific tickers to analyze (required for --analyze)
--ti                # Specific time intervals (optional)
--output            # Report output directory (default: /tmp)
```

## **🧠 Key Concepts**

> **Universal Concepts**: These apply to both test data and production systems

### **Alpha = Target Position**
- Alpha signals represent **target positions**, not trade volumes
- Intended trade = Target position - Current position
- This is fundamental to correct fill rate calculations

### **TVR (Target Volume Ratio)**
- Realistic target position changes over time
- Formula: `New target = Previous target ± random(0.1, 0.6) × Previous target`
- Provides market-realistic turnover patterns

### **Merge/Split Logic**
- **Merge**: `Merged Target = Sum(All PM targets for same ticker/time)`
- **Split**: `Trader Target = Merged Target / Number of Traders`
- Ensures all traders participate in all signals

### **Position Consistency**
- At all times: `PM Virtual Position = Sum(All trader positions for same ticker)`
- Maintains mathematical balance in the system
- Critical for system validation

## **Analysis Interfaces**

### **1. Single Ticker Timeline**
```bash
python3 main.py --csv-dir sample_data --analyze --ticker 000001.SSE --output /tmp
```
- Shows fill rate performance across all time intervals
- Identifies temporal patterns and execution consistency

### **2. Multi-Ticker Comparison**  
```bash
python3 main.py --csv-dir sample_data --analyze --ticker 000001.SSE 000002.SSE --output /tmp
```
- Compares execution quality across different securities
- Identifies ticker-specific performance characteristics

### **3. Time-Specific Deep Dive**
```bash
python3 main.py --csv-dir sample_data --analyze --ticker 000001.SSE --ti 940000000 --output /tmp
```
- Detailed analysis of specific time intervals
- Useful for investigating execution anomalies

## **📚 Documentation**

- `SYSTEM_UNDERSTANDING.md` - Framework architecture and evolution path
- `TARGET_SYSTEM_ANALYSIS.md` - Production system specification (target architecture)
- `DATA_GENERATION_RULES.md` - Test data generation rules (current simplified algorithms)
- `ALPHA_POSITION_CONCEPT.md` - Universal concepts for both test and production data
- `CHECKER_DEV_GUIDE.md` - Guide for developing validation checkers

## **🚀 Evolution Roadmap**

### **Phase 1: Foundation (Current)**
- ✅ Production-ready validation framework
- ✅ Basic test data generation with correct structure
- ✅ Core checkers and analyzers

### **Phase 2: Enhanced Simulation**
- 🔄 More realistic merge algorithms (risk-weighted, capacity-aware)
- 🔄 Advanced split logic (trader specialization, market impact)
- 🔄 Complex position attribution (multi-strategy reverse mapping)

### **Phase 3: Production Integration**
- 🎯 Validate real production CSV exports
- 🎯 Real-time monitoring and alerting
- 🎯 Advanced performance analytics

### **Phase 4: Optimization**
- 🎯 System performance recommendations
- 🎯 Algorithmic trading strategy insights
- 🎯 Risk management enhancements

## **Examples**

### **Realistic Performance**
```
Fill Rate Analysis Results:
  ti=930000000: 0.850 (5.0 trades)
  ti=940000000: 0.824 (5.0 trades) 
  ti=950000000: 0.752 (5.0 trades)
```
- Fill rates in 0.8-0.9 range ✅
- All 5 traders executing ✅
- Consistent performance pattern ✅

### **System Validation**
```
Data Consistency Checks:
  PM targets: 42 records
  Merged signals: 42 records (sum validation ✅)
  Trader signals: 210 records (5 traders × 42 ✅)
  Position records: 210 records (complete coverage ✅)
```

This framework enables comprehensive analysis of merge/split alpha trading systems for performance optimization and system validation.