"""
Merge Engine Checker - Validates alpha merging with group concept

This checker validates the dual-phase merging process:
1. Multiple PM alphas → Merged groups (via MergedAlphaEv) 
2. Merged groups → Individual traders (via SplitAlphaEv)

Business Logic:
- Multiple PMs generate independent alpha signals per ticker/time
- These signals are merged into predefined groups (like sSZEMNG500)
- Groups then distribute alphas to specific traders based on allocation rules
- Total volume must be conserved through both phases
"""

from base_checker import BaseChecker, CheckResult
import pandas as pd
from collections import defaultdict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from analyzer import AlphaAnalyzer


class MergeEngineChecker(BaseChecker):
    @property
    def name(self) -> str:
        return "Merge Engine Validator"
        
    def check(self, in_check_alpha_df, merged_alpha_df, split_alpha_df, 
              split_ctx_df, market_data_df):
        """
        Validate the dual-phase alpha merging process:
        PM Alphas → Merged Groups → Split to Traders
        """
        try:
            issues = []
            
            # Phase 1: Validate PM Alphas → Merged Groups
            merge_issues = self._validate_pm_to_groups(in_check_alpha_df, merged_alpha_df)
            issues.extend(merge_issues)
            
            # Phase 2: Validate Merged Groups → Split to Traders  
            split_issues = self._validate_groups_to_traders(merged_alpha_df, split_alpha_df)
            issues.extend(split_issues)
            
            # Phase 3: Validate Group Allocation Rules
            allocation_issues = self._validate_group_allocation_rules(split_alpha_df)
            issues.extend(allocation_issues)
            
            # Separate warnings from failures
            warnings = [issue for issue in issues if issue.startswith("⚠️")]
            failures = [issue for issue in issues if not issue.startswith("⚠️")]
            
            if not failures:
                if warnings:
                    return CheckResult(
                        checker_name=self.name,
                        status="WARNING",
                        message=f"Merge engine validation passed with {len(warnings)} warnings",
                        details=f"Validated {len(merged_alpha_df)} group merges and {len(split_alpha_df)} trader allocations\n" + 
                               "\n".join(warnings)
                    )
                else:
                    return CheckResult(
                        checker_name=self.name,
                        status="PASS", 
                        message="All merge engine validations passed",
                        details=f"Validated {len(merged_alpha_df)} group merges and {len(split_alpha_df)} trader allocations"
                    )
            else:
                all_issues = failures + warnings
                return CheckResult(
                    checker_name=self.name,
                    status="FAIL",
                    message=f"Found {len(failures)} merge engine violations and {len(warnings)} warnings",
                    details="\n".join(all_issues)
                )
                
        except Exception as e:
            return CheckResult(
                checker_name=self.name,
                status="ERROR",
                message=f"Error during merge engine validation: {str(e)}"
            )
    
    def _validate_pm_to_groups(self, in_check_df, merged_df):
        """
        Phase 1: Validate PM signals merge correctly into groups
        
        Business Rule: If no data with nil_last_alpha for a PM, the closing position defaults to zero.
        This means we need to account for all active PMs when validating closing positions.
        """
        issues = []
        
        # Get all unique PMs from the dataset to handle missing closing positions
        all_pms = set(in_check_df['alphaid'].unique())
        
        # For each time/ticker combination, calculate expected PM totals
        merged_groups = merged_df.groupby(['time', 'ticker'])['volume'].sum().reset_index()
        
        for _, merged_row in merged_groups.iterrows():
            time_val = merged_row['time']
            ticker = merged_row['ticker']
            merged_total = merged_row['volume']
            
            # Calculate PM total for this time/ticker, accounting for missing = 0
            pm_total = 0
            pm_entries = in_check_df[
                (in_check_df['time'] == time_val) & 
                (in_check_df['ticker'] == ticker)
            ]
            
            if AlphaAnalyzer.is_previous_day_position(time_val):  # Previous day positions
                # For closing positions, missing PM data means 0
                # Sum all PM entries that exist, others default to 0
                pm_total = pm_entries['volume'].sum()
                
                # Count how many PMs have this ticker at closing
                pms_with_closing_data = set(pm_entries['alphaid'].unique())
                
                # For debugging: show which PMs contribute to this closing position
                pm_breakdown = pm_entries.groupby('alphaid')['volume'].sum()
                pm_details = ", ".join([f"{pm}: {vol}" for pm, vol in pm_breakdown.items()])
                missing_pms = all_pms - pms_with_closing_data
                
            else:  # Regular trading hours
                # For regular trading, all contributing PMs should have data
                pm_total = pm_entries['volume'].sum()
            
            # Validate conservation
            if abs(pm_total - merged_total) > 1e-6:
                if AlphaAnalyzer.is_previous_day_position(time_val):
                    issues.append(
                        f"PM→Group violation at ti={time_val}, ticker={ticker}: "
                        f"PM total={pm_total} (from: {pm_details}), "
                        f"Merged total={merged_total}, diff={pm_total - merged_total}. "
                        f"Missing PMs default to 0: {missing_pms if missing_pms else 'none'}"
                    )
                else:
                    issues.append(
                        f"PM→Group violation at ti={time_val}, ticker={ticker}: "
                        f"PM total={pm_total}, Merged total={merged_total}, "
                        f"diff={pm_total - merged_total}"
                    )
        
        return issues
    
    def _validate_groups_to_traders(self, merged_df, split_df):
        """Phase 2: Validate merged groups distribute correctly to traders"""
        issues = []
        
        # Group by time and ticker
        merged_groups = merged_df.groupby(['time', 'ticker'])['volume'].sum().reset_index()
        split_groups = split_df.groupby(['time', 'ticker'])['volume'].sum().reset_index()
        
        # Create lookup dictionaries
        merged_totals = {}
        for _, row in merged_groups.iterrows():
            key = (row['time'], row['ticker'])
            merged_totals[key] = row['volume']
            
        split_totals = {}
        for _, row in split_groups.iterrows():
            key = (row['time'], row['ticker'])
            split_totals[key] = row['volume']
        
        # Validate conservation: Merged inputs = Split outputs
        for key in merged_totals:
            merged_total = merged_totals[key]
            split_total = split_totals.get(key, 0)
            
            if abs(merged_total - split_total) > 1e-6:
                time_val, ticker = key
                issues.append(
                    f"Group→Trader violation at ti={time_val}, ticker={ticker}: "
                    f"Merged total={merged_total}, Split total={split_total}, "
                    f"diff={merged_total - split_total}"
                )
        
        # Check for orphaned split alphas (no corresponding merged input)
        for key in split_totals:
            if key not in merged_totals:
                time_val, ticker = key
                issues.append(
                    f"Orphaned split alpha at ti={time_val}, ticker={ticker}: "
                    f"volume={split_totals[key]} (no corresponding merged input)"
                )
        
        return issues
    
    def _validate_group_allocation_rules(self, split_df):
        """Phase 3: Validate that group-to-trader allocation follows predefined rules"""
        issues = []
        
        # Analyze allocation patterns
        trader_patterns = defaultdict(set)
        
        for _, row in split_df.iterrows():
            alphaid = row['alphaid']
            time_ticker = (row['time'], row['ticker'])
            trader_patterns[alphaid].add(time_ticker)
        
        # Basic validation: Check if allocation is consistent
        # (This is where predefined rules would be checked)
        
        # Example rule: Each ticker should be allocated to exactly 2 traders
        allocation_counts = defaultdict(int)
        for _, row in split_df.iterrows():
            key = (row['time'], row['ticker'])
            allocation_counts[key] += 1
        
        for key, count in allocation_counts.items():
            if count != 2:  # Expecting exactly 2 traders per ticker
                time_val, ticker = key
                issues.append(
                    f"Allocation rule violation at ti={time_val}, ticker={ticker}: "
                    f"Expected 2 traders, got {count}"
                )
        
        return issues