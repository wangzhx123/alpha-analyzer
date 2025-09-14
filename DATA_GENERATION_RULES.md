# Test Data Generation Rules

This document specifies **ALL** rules used to generate test data that mimics production merge/split alpha trading system exports.

## **🎯 Purpose & Context**

### **Test Data vs Production Reality**
- **Test Data**: Simplified algorithms create structurally correct CSV files for framework validation
- **Production Data**: Complex institutional trading systems export similar CSV structure with sophisticated algorithms
- **Framework Goal**: Same validation code works on both test and production data

### **Current Implementation Status**
- ✅ **Correct Structure**: Test data matches production CSV format exactly
- ⚙️ **Simplified Logic**: Uses basic algorithms (sum, divide) instead of complex production algorithms
- 🔄 **Evolution Path**: Will gradually enhance algorithms to closer match production complexity
- 🎯 **End Goal**: Test data indistinguishable from production data structurally

## **📋 Test System Overview**

> **Note**: This describes current simplified test data generation. Production systems use more sophisticated algorithms.

The test merge/split system simulation:
1. **Multiple PMs** generate target positions with TVR logic → **InCheckAlphaEv.csv**
2. **Simple Merge** sums all PM targets by ticker/time → **MergedAlphaEv.csv**
3. **Even Split** divides merged targets equally among traders → **SplitAlphaEv.csv**
4. **Fill Rate Execution** applies 0.8-0.9 fill rates → **SplitCtxEv.csv**
5. **Direct Attribution** sums trader positions back to PMs → **VposResEv.csv**

## **TICKER GENERATION RULES**
1. **Ticker Universe**: Generate specified number of tickers (default: 1000)
2. **Ticker Format**: 50% SSE stocks (`XXXXXX.SSE`), 50% SZSE stocks (`XXXXXX.SZSE`)
3. **Ticker Numbering**: Sequential from `000001` to `NNNNNN`
4. **PM Ticker Overlap**: 80-90% common tickers across all PMs + unique tickers per PM

## **TIME INTERVAL RULES**
5. **Time Ranges**: Default morning [930000000, 1130000000] + afternoon [1300000000, 1500000000]
6. **Time Step**: 10000000 nanoseconds (10 minutes) intervals
7. **Time Generation**: Include both start and end times in ranges
8. **Time Ordering**: All intervals sorted chronologically

## **PM (PORTFOLIO MANAGER) RULES**
9. **PM ID Format**: `PM_001BUCS`, `PM_002BUCS`, etc.
10. **PM Count**: Configurable via `--num-pm` (default: 5)
11. **PM Ticker Overlap**: 80-90% common tickers + some unique tickers per PM
12. **PM Position Initialization**: First time seeing ticker → random target 1000-5000 × 100
13. **PM TVR Logic**: All tickers change by ±[0.1, 0.6] × previous target
14. **TVR Formula**: `New target = Previous target ± random(0.1, 0.6) × Previous target`
15. **PM Target Minimum**: Ensure all targets ≥ 0 (non-negative positions)

## **TRADER RULES**
16. **Trader ID Format**: `TRADER_001Atem`, `TRADER_002Atem`, etc.
17. **Trader Count**: Configurable via `--num-trader` (default: 5)
18. **Even Split Logic**: ALL traders participate in ALL signals
19. **Split Calculation**: `Trader Target = Merged Target ÷ Number of Traders`
20. **Remainder Distribution**: Distribute remainder to first few traders
21. **Complete Coverage**: Every ticker with merged target gets split to all traders

## **POSITION EXECUTION RULES**
22. **Fill Rate Range**: Configurable via `--fill-rate-min` and `--fill-rate-max` (default: 0.8-0.9)
23. **Fill Rate Application**: `actual_trade = intended_trade × random_fill_rate`
24. **Intended Trade Calculation**: `intended_trade = target_position - current_position`
25. **Position Update**: `new_position = current_position + actual_trade`
26. **Position Floor**: All positions ≥ 0 (no negative positions allowed)
27. **Direction Consistency**: Traders strictly follow trade direction (buy = position increases only)
28. **Zero Trade Handling**: If intended_trade = 0 → no fill rate applied, position unchanged

## **MARKET DATA RULES**
29. **Market Coverage**: ALL tickers at ALL time intervals (no filtering)
30. **Market ID**: Always `MARKET` for all market data
31. **Price Generation**: Base price 10.0-200.0, prev_price ±5% variation, current_price ±2% from prev
32. **Price Format**: 2 decimal places

## **CSV FILE STRUCTURE RULES**

### **InCheckAlphaEv.csv (PM Alpha Signals)**
33. **Format**: `event|alphaid|time|ticker|volume`
34. **Event Type**: Always `InCheckAlphaEv`
35. **AlphaID**: PM ID (e.g., `PM_001BUCS`)
36. **Volume Field**: Target position (NOT trade volume)
37. **Coverage**: ALL PM tickers at ALL time intervals

### **SplitAlphaEv.csv (Trader Alpha Signals)**
38. **Format**: `event|alphaid|time|ticker|volume`
39. **Event Type**: Always `SplitAlphaEv`
40. **AlphaID**: Trader ID (e.g., `TRADER_001Atem`)
41. **Volume Field**: Trader target position (split from merged)
42. **Coverage**: ALL merged targets split to ALL traders

### **SplitCtxEv.csv (Actual Positions)**
43. **Format**: `event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol`
44. **Event Type**: Always `SplitCtxEv`
45. **AlphaID**: Trader ID
46. **Position Fields**: `realtime_pos = realtime_long_pos`, `realtime_short_pos = 0`, `realtime_avail_shot_vol = realtime_pos`
47. **Position Calculation**: Based on fill rate applied to intended trades
48. **BOD Alignment**: At market open, positions aligned with PM pre-open vpos (sum should be equal)

### **VposResEv.csv (PM Virtual Positions)**
49. **Format**: `event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol`
50. **Event Type**: Always `VposResEv`
51. **AlphaID**: PM ID
52. **Virtual Position Logic**: Sum all trader positions for same ticker (exactly equal)
53. **Position Fields**: Same structure as SplitCtxEv

### **MergedAlphaEv.csv (Consolidated Signals)**
54. **Format**: `event|alphaid|time|ticker|volume`
55. **Event Type**: Always `MergedAlphaEv`
56. **AlphaID Format**: `GRP_{time}_{ticker}`
57. **Volume Calculation**: Sum of ALL PM targets for same ticker/time
58. **Data Derivation**: DERIVED from InCheckAlphaEv (sum of all PM alphas)
59. **Coverage**: ALL tickers with PM targets (no filtering)

### **MarketDataEv.csv (Market Prices)**
59. **Format**: `event|alphaid|time|ticker|last_price|prev_close_price`
60. **Event Type**: Always `MarketDataEv`
61. **AlphaID**: Always `MARKET`

## **CROSS-CSV ALIGNMENT RULES**
60. **Time Consistency**: All CSVs use same time intervals generated from ranges
61. **Complete Coverage**: Market data covers ALL tickers in universe (no filtering)
62. **PM-Trader Relationship**: M:N relationship (default 5 PMs : 5 Traders)
63. **Position Inheritance**: Trader positions carry forward between time intervals
64. **PM Target Evolution**: PM targets evolve with TVR logic
65. **Fill Rate Constraint**: Actual positions reflect fill rates applied to intended trades
66. **Direction Consistency**: Trade direction strictly followed (buy = position increases only)

## **DATA VOLUME ASSUMPTIONS**
67. **PM Signal Density**: Every PM generates signal for every assigned ticker at every time interval
68. **Trader Signal Coverage**: ALL traders get targets for ALL merged signals (no filtering)
69. **Position Completeness**: Every trader reports position for every ticker at every time interval
70. **Market Data Coverage**: Market data generated for ALL tickers at ALL time intervals

## **RANDOMIZATION RULES**
71. **Ticker Assignment**: Common tickers (80-90%) + unique tickers per PM
72. **TVR Randomness**: Each PM target change uses random factor [0.1, 0.6]
73. **Fill Rate Randomness**: Each trade gets independent random fill rate within range
74. **Price Randomness**: Each price movement is independent random walk
75. **Target Randomness**: Initial targets are random multiples of 100 in range 100000-500000

**Total: 75 explicit rules for test data generation**

> **Framework Note**: These rules generate test data only. The same validation framework will work unchanged on real production data with complex algorithms.

---

## **⚙️ Test Data Configuration Parameters**

> **Note**: These control test data generation only. Production data comes from real trading systems.

- `--num-pm`: Number of PMs (default: 5)
- `--num-trader`: Number of traders (default: 5)
- `--num-tickers`: Total ticker universe size (default: 1000)
- `--ti-ranges`: Time ranges (default: morning + afternoon sessions)
- `--ti-interval`: Time step in nanoseconds (default: 10000000)
- `--fill-rate-min/max`: Fill rate range for test execution (default: 0.8-0.9)
- `--tvr-min/max`: TVR change range for test PM behavior (default: 0.1-0.6)
- `--output-dir`: Output directory for test CSV files (default: sample_data)

## **Generated Files**
- `InCheckAlphaEv.csv`: PM alpha target signals (input to merge)
- `MergedAlphaEv.csv`: Consolidated alpha signals (sum of PM targets)
- `SplitAlphaEv.csv`: Trader alpha signals (even split of merged targets)
- `SplitCtxEv.csv`: Actual trader positions (with fill rates applied)
- `VposResEv.csv`: PM virtual positions (sum of trader positions)
- `MarketDataEv.csv`: Market price data (complete universe coverage)

## **📊 Test Data Flow Summary**
```
🧪 Test Data Generation Pipeline:
PM Signals → Simple Merge → Even Split → Fill Rate Execution → Direct Attribution
InCheckAlphaEv → MergedAlphaEv → SplitAlphaEv → SplitCtxEv → VposResEv

🏭 Production Reality (Future):
PM Signals → Complex Merge → Risk-Weighted Split → Real Execution → Advanced Attribution
Same CSV Structure → Same Validation Framework → Same Analysis Results
```

## **🔄 Algorithm Evolution Roadmap**

### **Phase 1: Basic Structure (Current)**
- ✅ Simple sum for merge logic
- ✅ Even division for split logic
- ✅ Direct sum for position attribution
- ✅ Realistic fill rates and TVR changes

### **Phase 2: Enhanced Realism (Future)**
- 🔄 Risk-weighted merge algorithms
- 🔄 Capacity-aware split allocation
- 🔄 Multi-strategy position attribution
- 🔄 Advanced market constraints

### **Phase 3: Production-Level (Target)**
- 🎯 Complex merge with conflict resolution
- 🎯 Trader specialization-based splits
- 🎯 Real-time position attribution
- 🎯 Full regulatory compliance simulation
