# Target Alpha Management System - Business Analysis

## What System Are We Analyzing?

This document describes my understanding of the **Target Alpha Management System** - the institutional trading platform that generates the data we analyze. The system consists of **two complementary subsystems** that work together to manage trading signals and position attribution.

## System Overview

### Dual-System Architecture
```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                    Institutional Trading Platform (Dual-System)                            │
│                                                                                             │
│ SYSTEM 1: MERGE SYSTEM (Alpha Processing)                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐│
│  │ Multiple    │    │ Alpha       │    │ Merge       │    │ Split       │    │ Traders     ││
│  │ Portfolio   │ → │ Checking    │ → │ Processing  │ → │ Processing  │ → │ (Execution  ││
│  │ Managers    │    │ (Validation)│    │ (Groups)    │    │ (Allocation)│    │ Engines)    ││
│  │ (PMs)       │    │             │    │             │    │             │    │             ││
│  └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘│
│       │                    │                    │                    │                    │ │
│    PM1,PM2,PM3        InCheckAlphaEv      MergedAlphaEv        SplitAlphaEv        Trading   │
│    Independent        (Post-validation    (Post-merge         (Per-trader         Execution │
│    alpha signals     alpha signals)      group results)      allocations)                  │
│                                                                                             │
│                                                   ▲                                         │
│                                                   │                                         │
│                                     ┌─────────────┴─────────────┐                           │
│                                     │                           │                           │
│                                     │    SYSTEM 2: SPLITVPOS SYSTEM (Position Attribution) │
│  ┌─────────────┐    ┌─────────────┐ │   ┌─────────────┐    ┌─────────────┐                 │
│  │ PM Virtual  │ ← │ SplitVPos   │◄┘   │ Position    │ ← │ Trader      │                 │
│  │ Positions   │    │ Processing  │     │ Attribution │    │ Realtime    │                 │
│  │ (VposResEv) │    │ (Reverse)   │     │ & Mapping   │    │ Positions   │                 │
│  └─────────────┘    └─────────────┘     └─────────────┘    └─────────────┘                 │
│         │                    │                    │                    │                   │
│    PM-level            Split virtual      Reverse mapping         SplitCtxEv              │
│    virtual positions   position results   of trader positions     (Trader positions)     │
│    for risk mgmt       back to PMs        back to PMs                                     │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Core Business Model

The system operates on a **dual-system architecture** with bidirectional data flow:

### **SYSTEM 1: MERGE SYSTEM** (Forward Flow: PMs → Traders)
**Purpose**: Process and distribute trading alphas from Portfolio Managers to execution traders

1. **Alpha Generation**: Multiple Portfolio Managers independently generate alpha signals per ticker per time event
2. **Alpha Checking**: Validate alpha signals for correctness and compliance before merging
3. **Merge Processing**: Consolidate multiple PM alphas into groups, handle conflicts and netting
4. **Split Processing**: Distribute merged group targets across multiple execution traders
5. **Trade Execution**: Individual traders execute their allocated portions

### **SYSTEM 2: SPLITVPOS SYSTEM** (Reverse Flow: Traders → PMs) 
**Purpose**: Attribute trader positions back to originating Portfolio Managers

6. **Position Tracking**: Monitor trader realtime positions and executions
7. **Position Attribution**: Reverse-map trader positions back to originating PM strategies
8. **Virtual Position Generation**: Create PM-level virtual positions for risk management
9. **Risk Management**: Enable PM-level constraint validation and performance attribution

## Data Flow Architecture

### System 1: Merge System Data Flow

#### Phase 1: Alpha Generation & Validation
```
PM1 Alpha Ideas → PM1 Signals → Alpha Checking → InCheckAlphaEv.csv
PM2 Alpha Ideas → PM2 Signals → Alpha Checking → (Post-validation signals)
PM3 Alpha Ideas → PM3 Signals → Alpha Checking → Ready for merging
```

#### Phase 2: Merge Processing
```
InCheckAlphaEv → Merge Engine → Group Formation → Conflict Resolution → MergedAlphaEv.csv
                     │              │                    │
               Multiple PMs    Split into groups    Handle opposing
               contributing    based on strategy    signals (netting)
```

#### Phase 3: Split Processing & Execution
```
MergedAlphaEv → Split Engine → Trader Allocation → SplitAlphaEv.csv
                     │              │
              Per-group targets   Risk-based split
              distributed to      across traders
              available traders
                     │
                     ▼
              Trader Execution → Realtime Positions → SplitCtxEv.csv
```

### System 2: SplitVPos System Data Flow

#### Phase 4: Position Attribution (Reverse Flow)
```
SplitCtxEv.csv → Position Attribution → SplitVPos Processing → VposResEv.csv
(Trader positions)    (Reverse mapping)    (PM attribution)      (PM virtual positions)
       │                     │                     │                      │
   Actual trader         Map positions         Calculate PM           Used for T+1
   holdings and         back to source        virtual positions      constraints
   available volumes    PM strategies         per ticker/time        and risk mgmt
```

## Business Entities & Roles

### Portfolio Managers (PMs)
- **Role**: Strategy specialists generating independent alpha signals
- **Responsibility**: Generate target position signals per ticker per time event
- **Independence**: Each PM operates with separate research, models, and risk appetites
- **Diversity**: May have conflicting signals (PM1: +10K, PM2: -5K for same ticker)
- **Data Output**: Alpha signals that feed into InCheckAlphaEv.csv after validation

### Merge System Components

#### Alpha Checking Engine
- **Role**: Validate PM alpha signals before merging
- **Function**: Ensure signal quality, compliance, and readiness for processing
- **Business Value**: Prevent invalid signals from affecting downstream systems
- **Data Output**: InCheckAlphaEv.csv (validated alpha signals)

#### Merge Processing Engine
- **Role**: Consolidate multiple PM signals into coherent groups
- **Function**: 
  - **Group Formation**: Organize alphas into logical groups based on strategy/risk
  - **Conflict Resolution**: Handle opposing signals through netting and prioritization
  - **Signal Aggregation**: Combine complementary signals efficiently
  - **Risk Balancing**: Ensure merged groups are executable and risk-appropriate
- **Business Value**: Optimize execution efficiency while preserving alpha signal integrity
- **Data Output**: MergedAlphaEv.csv (consolidated group targets)

#### Split Processing Engine  
- **Role**: Distribute merged targets across execution traders
- **Function**: 
  - **Capacity Allocation**: Consider trader capacity, limits, and specialization
  - **Risk Distribution**: Spread execution risk across multiple traders
  - **Execution Optimization**: Match targets to trader capabilities
- **Data Output**: SplitAlphaEv.csv (per-trader allocations)

### Execution Layer

#### Traders / Execution Engines
- **Role**: Execution specialists (human or algorithmic)
- **Examples**: `sSZE113Atem`, `sSZE114Atem` (likely algorithmic trading systems)
- **Responsibility**: Execute allocated alpha targets within risk limits and market constraints
- **Input**: Split alpha allocations from Split Processing Engine
- **Output**: Realtime position changes and available volumes (SplitCtxEv.csv)

### SplitVPos System Components

#### Position Attribution Engine
- **Role**: Map trader positions back to originating PM strategies
- **Function**: 
  - **Position Aggregation**: Collect all trader realtime positions
  - **Source Attribution**: Determine which PM strategies contributed to each position
  - **Proportional Allocation**: Distribute trader positions back to PMs proportionally
- **Input**: SplitCtxEv.csv (trader realtime positions)
- **Challenges**: Complex reverse mapping with multiple contribution sources

#### SplitVPos Processing Engine
- **Role**: Generate PM-level virtual positions for management purposes
- **Function**: 
  - **Virtual Position Calculation**: Create PM-specific position views
  - **Risk Attribution**: Enable PM-level risk management and constraints
  - **Performance Attribution**: Support PM performance measurement
- **Output**: VposResEv.csv (PM virtual positions)
- **Business Purpose**: Enable T+1 constraint validation and PM-level risk management

## Data File Definitions

### InCheckAlphaEv.csv
**Content**: Post-validation alpha signals from Portfolio Managers
**Structure**: event|alphaid|time|ticker|volume
**Business Meaning**: PM alpha signals that have passed checking and are ready for merging
**Example**: PM wants 10,000 shares of AAPL at 9:30 AM after validation

### MergedAlphaEv.csv  
**Content**: Consolidated alpha targets after merge processing
**Structure**: event|alphaid|time|ticker|volume
**Business Meaning**: Group-level targets after PM signal consolidation and conflict resolution
**Example**: Merged group target of 15,000 shares AAPL (from multiple PM inputs)

### SplitAlphaEv.csv
**Content**: Per-trader alpha allocations from split processing
**Structure**: event|alphaid|time|ticker|volume  
**Business Meaning**: Individual trader targets derived from merged group targets
**Example**: Trader A allocated 7,500 shares, Trader B allocated 7,500 shares

### SplitCtxEv.csv
**Content**: Trader realtime positions and available volumes
**Structure**: event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol
**Business Meaning**: Actual trader holdings and T+1-compliant sellable volumes
**Example**: Trader holds 1,200 shares with 1,200 available to sell

### VposResEv.csv
**Content**: PM virtual positions from SplitVPos processing
**Structure**: time|ticker|vpos
**Business Meaning**: PM-level virtual positions for risk management and T+1 constraints
**Example**: PM virtual position of 5,000 shares used for constraint validation

## Time-Based Event Processing

### Time Event Structure (ti)
- **Format**: `93000000` = 9:30:00 AM (market open)
- **Frequency**: Multiple events per day (possibly every minute or on significant events)
- **Previous Day Positions**: 
  - `time = -1` (traditional closing position marker)
  - `time < 93000000` (any time before 9:30:00 AM market open)

### Event Sequence Example
```
Day N-1 Close (ti = -1 or < 93000000):
├── PM virtual positions: 5,000 shares AAPL
└── Store as previous day reference for T+1 constraints

Day N Trading:
├── ti = 93000000 (9:30 AM): 
│   ├── PM generates alpha → InCheckAlphaEv  
│   ├── Merge processing → MergedAlphaEv
│   ├── Split processing → SplitAlphaEv
│   ├── Trader execution → SplitCtxEv
│   └── Position attribution → VposResEv
│
├── ti = 93100000 (9:31 AM): [Repeat cycle]
└── ... continues throughout trading day
```

## Risk Management & Constraints

### T+1 Sellable Constraint (Cross-System)
**Business Purpose**: Prevent violation of T+1 settlement rules

**System 1 Role**: Use realtime_avail_shot_vol from SplitCtxEv for execution decisions
**System 2 Role**: Generate PM virtual positions in VposResEv for constraint validation

**How it works**:
```
1. SplitVPos System generates PM virtual positions (VposResEv.csv)
2. Previous day positions establish sellable baseline
3. Merge System uses SplitCtxEv available volumes for execution
4. Both systems coordinate to enforce T+1 settlement compliance
```

### Volume Rounding Rules
**Business Purpose**: Standard market lot compliance
**Implementation**: All actual trades must be in 100-share increments

## System Integration Points

### Forward Integration (Merge → SplitVPos)
- **Split Alpha → Position Attribution**: SplitAlphaEv.csv drives position attribution logic
- **Trader Positions → PM Attribution**: SplitCtxEv.csv feeds SplitVPos processing

### Reverse Integration (SplitVPos → Merge)
- **PM Virtual Positions → Risk Constraints**: VposResEv.csv enables T+1 constraint validation
- **Available Volumes → Execution Limits**: SplitCtxEv.csv constrains trading decisions

## Key Business Questions This System Answers

### Merge System Questions:
1. **"Are PM alphas being processed correctly?"** → InCheckAlphaEv validation
2. **"Is signal consolidation working effectively?"** → MergedAlphaEv vs InCheckAlphaEv analysis  
3. **"Are trader allocations optimal?"** → SplitAlphaEv distribution analysis
4. **"Is execution meeting targets?"** → SplitCtxEv vs SplitAlphaEv fill rate analysis

### SplitVPos System Questions:
5. **"Which PM strategies are performing?"** → VposResEv attribution analysis
6. **"Are T+1 constraints being respected?"** → VposResEv constraint validation
7. **"Is position attribution accurate?"** → SplitCtxEv to VposResEv mapping validation
8. **"What are the true PM-level risks?"** → VposResEv risk analysis

### Cross-System Questions:
9. **"Is the overall system healthy?"** → End-to-end data flow validation
10. **"Are both systems synchronized?"** → Cross-system consistency checks

## System Performance Characteristics

### What Good Performance Looks Like
```
Merge System:
├── High Alpha Conservation (InCheck → Merged → Split sums match)
├── Efficient Conflict Resolution (optimal signal netting)
├── Balanced Trader Allocation (even capacity utilization)
└── High Fill Rates (execution meets targets)

SplitVPos System:  
├── Accurate Position Attribution (trader pos → PM pos mapping)
├── Timely Virtual Position Updates (real-time PM risk views)
├── Zero T+1 Violations (proper constraint enforcement)
└── Consistent Cross-System Data (synchronized views)
```

### What Bad Performance Indicates
```
Merge System Issues:
├── Signal Leakage (alpha sums don't conserve)
├── Poor Conflict Resolution (ineffective netting)
├── Unbalanced Allocation (trader capacity issues)
└── Low Fill Rates (execution problems)

SplitVPos System Issues:
├── Attribution Errors (incorrect PM position mapping)
├── Stale Virtual Positions (delayed risk updates)  
├── T+1 Violations (constraint system failures)
└── Cross-System Inconsistency (synchronization problems)
```

This dual-system architecture enables sophisticated institutional trading with proper risk management, performance attribution, and regulatory compliance through coordinated forward and reverse data flows.