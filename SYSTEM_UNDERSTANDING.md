# Alpha Analyzer System Understanding

## **🎯 Framework Purpose & Context**

The Alpha Analyzer is a **production-ready validation framework** designed to analyze merge/split alpha trading systems. This document explains both the target production system architecture and the current framework implementation.

### **🏭 Production vs 🧪 Test Environment Context**

| Aspect | Production Reality | Current Test Data |
|--------|-------------------|-------------------|
| **Merge Logic** | Complex risk-weighted algorithms | Simple summation (`sum(PM_targets)`) |
| **Split Logic** | Advanced capacity/specialization-based | Even division (`merged_target / num_traders`) |
| **Position Attribution** | Multi-strategy reverse mapping | Direct summation (`sum(trader_positions)`) |
| **Data Source** | Real trading system CSV exports | Generated via `generate_sample_data.py` |
| **Constraints** | Real T+1, risk limits, market impact | Simplified fill rates (0.8-0.9) |

### **🛠️ Framework Design Philosophy**
- **Built for Production**: All checkers/analyzers handle real-world complexity
- **Test Data Simulation**: Current data generation mimics production structure
- **Evolutionary Approach**: Gradually enhance test data realism without changing validation logic
- **Future-Proof**: Framework seamlessly transitions from test to production data

## **📊 System Architecture**

> **Note**: This shows the target production system. Current test data uses simplified versions of these processes.

### **🔄 Data Flow Pipeline**
```
Portfolio Managers (PMs) → Alpha Signals → Merge System → Split System → Traders → Execution
         ↓                      ↓              ↓             ↓           ↓
   InCheckAlphaEv.csv    MergedAlphaEv.csv  SplitAlphaEv.csv  SplitCtxEv.csv  VposResEv.csv
```

### **🏢 Component Roles**

> **Production Complexity**: Real systems use sophisticated algorithms. Test data uses simplified versions.

1. **Portfolio Managers (PMs)**
   - Generate target position signals for tickers
   - Multiple PMs can trade overlapping ticker universes
   - Targets change over time with TVR (Target Volume Ratio) logic
   - IDs: `PM_001BUCS`, `PM_002BUCS`, etc.

2. **Merge System**
   - Consolidates all PM signals for same ticker/time
   - Sums all PM targets: `Merged Target = Sum(All PM targets for ticker)`
   - Creates consolidated alpha signals

3. **Split System** 
   - Divides merged targets evenly across all traders
   - Each trader gets: `Trader Target = Merged Target / Num Traders`
   - Ensures all traders participate in every signal

4. **Traders**
   - Execute the split alpha signals in the market
   - Subject to fill rate constraints (typically 0.8-0.9)
   - IDs: `TRADER_001Atem`, `TRADER_002Atem`, etc.

5. **Position Tracking**
   - **Production**: Complex reverse attribution with multi-strategy mapping
   - **Test Data**: Simple summation: `PM VPos = Sum(Trader Positions)`
   - **Framework**: Validates position consistency regardless of complexity

## **🧠 Universal Concepts**

> **Note**: These concepts apply to both production and test data

### **Alpha Signals = Target Positions**
- **CRITICAL**: Alpha signals represent **target positions**, NOT trade volumes
- Intended trade = Target position - Current position
- Fill rate = Actual trade / Intended trade

### **TVR (Target Volume Ratio)**
- PM targets change over time with realistic variation
- New target = Previous target ± random(0.1, 0.6) × Previous target
- Provides realistic turnover and trading activity

### **Fill Rate Analysis**
- Measures execution quality: How well traders achieve intended trades
- Expected range: 0.8-0.9 (realistic market execution constraints)
- Direction consistency: Buy orders only increase positions

### **Position Alignment**
- At BOD (Beginning of Day): Trader positions sum equals PM virtual positions
- Ensures system consistency and proper position tracking
- VPos calculation derives PM positions from actual trader executions

## **CSV File Structure**

### **InCheckAlphaEv.csv** (PM Alpha Signals)
```
event|alphaid|time|ticker|volume
InCheckAlphaEv|PM_001BUCS|930000000|000001.SSE|250000
```
- **Volume field**: Target position (NOT trade volume)
- Contains all PM target signals for all tickers/times

### **MergedAlphaEv.csv** (Consolidated Signals)  
```
event|alphaid|time|ticker|volume
MergedAlphaEv|GRP_930000000_000001.SSE|930000000|000001.SSE|1250000
```
- **Volume field**: Sum of all PM targets for same ticker/time
- Derived calculation: Sum(InCheckAlphaEv volumes) by ticker/time

### **SplitAlphaEv.csv** (Trader Alpha Signals)
```
event|alphaid|time|ticker|volume
SplitAlphaEv|TRADER_001Atem|930000000|000001.SSE|250000
```
- **Volume field**: Trader's portion of merged target
- Even split: Each trader gets `Merged Target / Num Traders`

### **SplitCtxEv.csv** (Actual Trader Positions)
```
event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol
SplitCtxEv|TRADER_001Atem|930000000|000001.SSE|200000|200000|0|200000
```
- **realtime_pos**: Actual position achieved after fill rate application
- Shows execution results with market constraints

### **VposResEv.csv** (PM Virtual Positions)
```
event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol  
VposResEv|PM_001BUCS|930000000|000001.SSE|1000000|1000000|0|1000000
```
- **realtime_pos**: PM's virtual position = Sum(All trader positions for ticker)
- Calculated from actual trader execution results

### **MarketDataEv.csv** (Market Prices)
```
event|alphaid|time|ticker|last_price|prev_close_price
MarketDataEv|MARKET|930000000|000001.SSE|99.26|99.61
```
- Market price information for all tickers/times
- Used for market context in analysis

## **📈 Framework Analysis Capabilities**

> **Production-Ready**: These analyzers work on both test and production data

### **Fill Rate Analysis**
- **Primary Metric**: Measures execution quality
- **Calculation**: `Fill Rate = (Actual Position Change) / (Intended Position Change)`
- **Expected Range**: 0.8-0.9 for realistic system performance
- **Reports**: Timeline charts, statistical summaries

### **Trade Volume Analysis** 
- **Trade Count**: Number of actual trades executed per interval
- **Direction Consistency**: Validates buy/sell direction adherence
- **Position Tracking**: Ensures positions evolve correctly over time

### **System Validation**
- **Data Consistency**: Validates alignment between all CSV files
- **Position Balance**: Ensures PM virtual positions = Sum(Trader positions)
- **Signal Flow**: Validates merge/split calculations are correct

## **Usage Patterns**

### **Single Ticker Analysis**
```bash
python3 main.py --csv-dir sample_data --analyze --ticker 000001.SSE --output /tmp
```
- Analyzes one ticker across all time intervals
- Shows fill rate timeline and execution patterns

### **Multi-Ticker Analysis**
```bash  
python3 main.py --csv-dir sample_data --analyze --ticker 000001.SSE 000002.SSE --output /tmp
```
- Compares execution across multiple tickers
- Identifies ticker-specific performance patterns

### **Time-Specific Analysis**
```bash
python3 main.py --csv-dir sample_data --analyze --ticker 000001.SSE --ti 940000000 --output /tmp
```
- Deep dive into specific time intervals
- Detailed execution analysis for critical periods
- Works identically for test data and future production data

## **🔍 Framework Validation Insights**

### **Current Test Data Characteristics**
1. **Ticker Overlap**: 80-90% common tickers across PMs (essential for merge system)
2. **Even Split**: All traders get equal allocation (simplified version)
3. **Position Consistency**: Mathematical balance maintained (production requirement)
4. **Realistic Constraints**: Fill rates 0.8-0.9 (simplified market behavior)
5. **Complete Coverage**: No filtering - full system representation

### **Production System Expectations**
1. **Complex Merge**: Risk-weighted, capacity-aware consolidation algorithms
2. **Advanced Split**: Trader specialization, market impact, liquidity-based allocation
3. **Sophisticated Attribution**: Multi-level reverse mapping with strategy decomposition
4. **Real Constraints**: T+1 settlement, regulatory limits, real-time risk management
5. **Performance Optimization**: Dynamic algorithm adjustment based on market conditions

## **🎯 Framework Benefits**

### **For Test Data Analysis**
- **Algorithm Validation**: Ensures merge/split logic correctness
- **Data Structure Verification**: Validates CSV format and relationships
- **Performance Baseline**: Establishes expected fill rate ranges
- **System Understanding**: Builds knowledge of merge/split concepts

### **For Production Data Analysis**
- **Risk Distribution Validation**: Verifies execution spread across traders
- **Signal Consolidation Quality**: Measures merge algorithm effectiveness
- **Performance Measurement**: Quantifies real execution quality
- **System Health Monitoring**: Detects operational issues in real-time
- **Regulatory Compliance**: Ensures T+1 and risk limit adherence
- **Optimization Insights**: Identifies algorithmic improvement opportunities

## **🚀 Evolution Path**

```
Phase 1 (Current):    Test Data + Production Framework
                     ├─ Simplified algorithms in generate_sample_data.py
                     └─ Full validation framework in analyzer.py

Phase 2 (Enhanced):   Realistic Test Data + Production Framework
                     ├─ Complex merge/split algorithms in test data
                     └─ Same validation framework (no changes needed)

Phase 3 (Production): Real Data + Production Framework
                     ├─ Actual trading system CSV exports
                     └─ Same validation framework (seamless transition)
```

This evolutionary approach enables **continuous framework development** while gradually increasing data realism, ensuring the validation logic is production-ready from day one.