# Data Generation Rules and Assumptions

This document lists **ALL** rules and assumptions used during sample data generation for the Alpha Analyzer system.

**⚠️ DEPRECATED**: This document contains the original incorrect assumptions that were corrected based on user feedback. See `SYSTEM_UNDERSTANDING.md` for the correct system architecture.

## **Corrections Applied:**
- ✅ PM ticker overlap implemented (80-90% common tickers)
- ✅ ID format: `PM_001BUCS`, `TRADER_001Atem`  
- ✅ TVR logic: `New target = Previous target ± random(0.1, 0.6) × Previous target`
- ✅ Even trader split: Merged alpha divided equally among all traders
- ✅ MergedAlphaEv derived from sum of PM alphas
- ✅ No filtering: ALL tickers covered in ALL files
- ✅ Direction consistency: Buy means position increases only

## **TICKER GENERATION RULES**
1. **Ticker Universe**: Generate `num_pm × min_tickers_per_pm + 500` total tickers
2. **Ticker Format**: 50% SSE stocks (`XXXXXX.SSE`), 50% SZSE stocks (`XXXXXX.SZSE`) 
3. **Ticker Numbering**: Sequential from `000001` to `NNNNNN`
4. **Ticker Distribution**: Randomly shuffle all tickers before assignment

## **TIME INTERVAL RULES**
5. **Time Ranges**: Default morning [930000000, 1130000000] + afternoon [1300000000, 1500000000]
6. **Time Step**: 10000000 nanoseconds (10 minutes) intervals
7. **Time Generation**: Include both start and end times in ranges
8. **Time Ordering**: All intervals sorted chronologically

## **PM (PORTFOLIO MANAGER) RULES**
9. **PM ID Format**: `PM001BUCS`, `PM002BUCS`, etc.
10. **PM Count**: Configurable via `--num-pm` (default: 5)
11. **PM Ticker Assignment**: Each PM gets exactly `min_tickers_per_pm` tickers per time interval
12. **PM Ticker Selection**: Sequential assignment from shuffled ticker pool (no overlap between PMs)
comment to 12: "no, of course we should have overlap ticker between pms, otherwise, why would we need such a merge alpha system at first place??"
13. **PM Position Initialization**: First time seeing ticker → random target 1000-5000 × 100
14. **PM Decision Logic**: 40% maintain, 20% close, 40% new target for existing tickers
comment to 14: no, we need more tvr here. say all ticker's alpha volume change from [0.1, 0.6] of their prev alpha target.
15. **PM Maintain Rule**: If maintain → target = previous target
16. **PM Close Rule**: If close → target = 0  
17. **PM New Target Rule**: If new target → random 1000-5000 × 100

## **TRADER RULES**
18. **Trader ID Format**: `TR001Atem`, `TR002Atem`, etc.
comment to 18: make it more explicit: for PM is PM_001/002... for trader, it's TRADER_001/002 ...
19. **Trader Count**: Configurable via `--num-trader` (default: 5)
20. **Trader Target Selection**: Each trader handles ~20% of total PM non-zero targets
21. **Trader Target Sampling**: Random sample from all PM targets across all PMs
22. **Trader Target Allocation**: Trader gets 60%-100% of selected PM target
23. **Trader Signal Filter**: Only generate signals for targets > 0
comment to 20-23: no, i still don't understand. our to-be-analyzed system, will merge and split all received alphas, and split evenly(current simple split algo) to all traders. that means, for a certain ticker, say merged target is 5000, then all 5 traders will get a 1000 alpha target for them to trader!!not just sampled!so your current understanding is totally wrong!!!

## **POSITION EXECUTION RULES**
24. **Fill Rate Range**: Configurable via `--fill-rate-min` and `--fill-rate-max` (default: 0.8-0.9)
25. **Fill Rate Application**: `actual_trade = intended_trade × random_fill_rate`
26. **Intended Trade Calculation**: `intended_trade = target_position - current_position`
27. **Position Update**: `new_position = current_position + actual_trade`
28. **Position Floor**: All positions ≥ 0 (no negative positions allowed)
29. **Zero Trade Handling**: If intended_trade = 0 → no fill rate applied, position unchanged

## **MARKET DATA RULES**
30. **Market Ticker Selection**: Random 2000 tickers per time interval (or all if < 2000)
31. **Market ID**: Always `MARKET` for all market data
32. **Price Generation**: Base price 10.0-200.0, prev_price ±5% variation, current_price ±2% from prev
33. **Price Format**: 2 decimal places

## **CSV FILE STRUCTURE RULES**

### **InCheckAlphaEv.csv (PM Alpha Signals)**
34. **Format**: `event|alphaid|time|ticker|volume`
35. **Event Type**: Always `InCheckAlphaEv`
36. **AlphaID**: PM ID (e.g., `PM001BUCS`)
37. **Volume Field**: Target position (NOT trade volume)
38. **Record Count**: `num_pm × min_tickers_per_pm × num_time_intervals`

### **SplitAlphaEv.csv (Trader Alpha Signals)**
39. **Format**: `event|alphaid|time|ticker|volume`
40. **Event Type**: Always `SplitAlphaEv`  
41. **AlphaID**: Trader ID (e.g., `TR001Atem`)
42. **Volume Field**: Trader target position
43. **Filter Rule**: Only include non-zero targets
comment to 43, not sure what you said here, but we don't need any filter rule actually. just split the merged alpha target across traders, and trader just trade it according current pos!

### **SplitCtxEv.csv (Actual Positions)**
44. **Format**: `event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol`
45. **Event Type**: Always `SplitCtxEv`
46. **AlphaID**: Trader ID
47. **Position Fields**: `realtime_pos = realtime_long_pos`, `realtime_short_pos = 0`, `realtime_avail_shot_vol = realtime_pos`
48. **Position Calculation**: Based on fill rate applied to intended trades
comment: and yes, it represents the current realtime pos for every trader! at the BOD(93000000), it reflects the open position (should aligned with the pm's pre-open vpos, sum should be equal for both pm and traders)

### **VposResEv.csv (PM Virtual Positions)**
49. **Format**: `event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol`
50. **Event Type**: Always `VposResEv`
51. **AlphaID**: PM ID
52. **Virtual Position Logic**: Sum all trader positions for same ticker × random(0.8, 1.2)
53. **Position Fields**: Same structure as SplitCtxEv

### **MergedAlphaEv.csv (Consolidated Signals)**
54. **Format**: `event|alphaid|time|ticker|volume`
55. **Event Type**: Always `MergedAlphaEv`
56. **AlphaID Format**: `GRP_{time}_{ticker}`
57. **Ticker Selection**: Random 500 tickers per time interval (or all if < 500)
comment to 57: again, no such ticker selection thing!!! treat them all as equal!
58. **Volume Range**: Random 5000-20000
comment to 58: no!!!! the merged alpha data should be derived from the InCheckAlphaEv!!!! i.e. sum_of_all(Incehckedalpha) based on how many merged alphaid are there (by default, currently we only merge all pm's alpha to one merged alphaid, and then split it later)

### **MarketDataEv.csv (Market Prices)**
59. **Format**: `event|alphaid|time|ticker|last_price|prev_close_price`
60. **Event Type**: Always `MarketDataEv`
61. **AlphaID**: Always `MARKET`

## **CROSS-CSV ALIGNMENT RULES**
62. **Time Consistency**: All CSVs use same time intervals generated from ranges
63. **Ticker Consistency**: Market data covers superset of all traded tickers
comment: NO, should cover them all!!!
64. **PM-Trader Relationship**: Traders get subsets of PM targets (no direct 1:1 mapping)
comment: yes, but we now assume it's 5 vs 5 (but of course, could be any M:N)
65. **Position Inheritance**: Trader positions carry forward between time intervals
66. **PM Position Inheritance**: PM targets carry forward with maintain/close/new logic
67. **Fill Rate Constraint**: Actual positions always ≤ target positions due to fill rates < 1.0
comment: also, we assume that, trader will strictly follow the trade signal, that is, if the trade dirction is buy, then next ti, the trader's pos should be only larger than or equal to current ti's

## **DATA VOLUME ASSUMPTIONS**
68. **PM Signal Density**: Every PM generates signal for every assigned ticker at every time interval
69. **Trader Signal Sparsity**: Traders only generate signals for non-zero targets (filtered)
70. **Position Completeness**: Every trader reports position (including 0) for every ticker they've ever traded
71. **Market Data Coverage**: Market data generated for active trading tickers only
comment to above: NOnonononono!! all! the whole universe! no fitlering thing ever involved!

## **RANDOMIZATION RULES** 
72. **Ticker Shuffling**: Global ticker list shuffled once before all assignments
73. **PM Decision Randomness**: Each PM decision (maintain/close/new) is independent random choice
74. **Fill Rate Randomness**: Each trade gets independent random fill rate within range
75. **Price Randomness**: Each price movement is independent random walk
76. **Target Randomness**: New targets are random multiples of 100 in range 100000-500000

**Total: 76 explicit rules and assumptions used in data generation**

---

## **Configuration Parameters**
- `--num-pm`: Number of PMs (default: 5)
- `--num-trader`: Number of traders (default: 5)
- `--min-tickers-per-pm`: Minimum tickers per PM per interval (default: 1000)
- `--ti-ranges`: Time ranges (default: morning + afternoon sessions)
- `--ti-interval`: Time step in nanoseconds (default: 10000000)
- `--fill-rate-min/max`: Fill rate range (default: 0.8-0.9)
- `--output-dir`: Output directory (default: sample_data)

## **Generated Files**
- `InCheckAlphaEv.csv`: PM alpha target signals
- `SplitAlphaEv.csv`: Trader alpha signals  
- `SplitCtxEv.csv`: Actual trader positions
- `VposResEv.csv`: PM virtual positions
- `MergedAlphaEv.csv`: Consolidated alpha signals
- `MarketDataEv.csv`: Market price data
