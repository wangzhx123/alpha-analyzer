# Alpha Analyzer System Understanding

## **Overview**
The Alpha Analyzer is a framework for analyzing the performance of a **merge/split alpha trading system**. This system takes alpha signals from multiple Portfolio Managers (PMs), merges them, and splits the consolidated signals across multiple traders for execution.

## **System Architecture**

### **Data Flow**
```
Portfolio Managers (PMs) → Alpha Signals → Merge System → Split System → Traders → Execution
         ↓                      ↓              ↓             ↓           ↓
   InCheckAlphaEv.csv    MergedAlphaEv.csv  SplitAlphaEv.csv  SplitCtxEv.csv  VposResEv.csv
```

### **Component Roles**

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
   - Tracks actual positions achieved by traders
   - Calculates PM virtual positions from trader execution results
   - Ensures position consistency: `PM VPos = Sum(Trader Positions)`

## **Key Concepts**

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

## **Analysis Capabilities**

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

## **Key Insights from Data Generation**

1. **Ticker Overlap is Essential**: PMs must trade overlapping tickers for merge system to work
2. **Even Split Logic**: All traders participate equally in all signals
3. **Position Consistency**: System maintains mathematical balance between PM and trader positions
4. **Realistic Constraints**: Fill rates and TVR provide market-realistic behavior
5. **Complete Coverage**: All tickers, all times, no filtering - represents full system operation

## **System Benefits**

- **Risk Distribution**: Spreads execution across multiple traders
- **Signal Consolidation**: Combines PM expertise through merging
- **Performance Measurement**: Quantifies execution quality through fill rates
- **System Validation**: Ensures proper operation of merge/split logic
- **Operational Insights**: Identifies performance issues and optimization opportunities

This understanding enables effective analysis of real merge/split alpha trading systems in production environments.