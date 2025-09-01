from typing import List
import pandas as pd
from pathlib import Path
from base_checker import BaseChecker, CheckResult


class AlphaAnalyzer:
    def __init__(self):
        self.checkers: List[BaseChecker] = []
        self.input_df = None
        self.output_df = None
        self.realtime_pos_df = None
    
    def add_checker(self, checker: BaseChecker):
        """Register a new checker"""
        self.checkers.append(checker)
    
    def load_data(self, data_dir: str):
        """
        Load CSV files with expected columns:
        - IncheckAlphaEv.csv: ti,sid,ticker,target
        - SplitAlphaEv.csv: ti,sid,ticker,target
        - RealtimePosEv.csv: ti,sid,ticker,realtime_pos
        """
        data_path = Path(data_dir)
        
        # Load input data (IncheckAlphaEv.csv)
        input_file = data_path / "IncheckAlphaEv.csv"
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        self.input_df = pd.read_csv(input_file)
        self._validate_columns(self.input_df, "input", {'ti', 'sid', 'ticker', 'target'})
        
        # Load output data (SplitAlphaEv.csv)  
        output_file = data_path / "SplitAlphaEv.csv"
        if not output_file.exists():
            raise FileNotFoundError(f"Output file not found: {output_file}")
        
        self.output_df = pd.read_csv(output_file)
        self._validate_columns(self.output_df, "output", {'ti', 'sid', 'ticker', 'target'})
        
        # Load realtime position data (RealtimePosEv.csv)
        realtime_file = data_path / "RealtimePosEv.csv"
        if not realtime_file.exists():
            raise FileNotFoundError(f"Realtime position file not found: {realtime_file}")
        
        self.realtime_pos_df = pd.read_csv(realtime_file)
        self._validate_columns(self.realtime_pos_df, "realtime position", {'ti', 'sid', 'ticker', 'realtime_pos'})
        
        print(f"Loaded {len(self.input_df)} input records, {len(self.output_df)} output records, and {len(self.realtime_pos_df)} realtime position records")
    
    def _validate_columns(self, df: pd.DataFrame, data_type: str, required_cols: set):
        """Validate that required columns exist"""
        missing_cols = required_cols - set(df.columns)
        
        if missing_cols:
            raise ValueError(f"{data_type} data missing required columns: {missing_cols}")
    
    def run_checks(self) -> List[CheckResult]:
        """Execute all registered checkers"""
        if self.input_df is None or self.output_df is None or self.realtime_pos_df is None:
            raise RuntimeError("Data not loaded. Call load_data() first.")
        
        results = []
        for checker in self.checkers:
            try:
                result = checker.check(self.input_df, self.output_df, self.realtime_pos_df)
                results.append(result)
            except Exception as e:
                results.append(CheckResult(
                    checker_name=checker.name,
                    status="ERROR",
                    message=f"Checker failed: {str(e)}"
                ))
        return results
    
    def get_data_summary(self):
        """Get basic statistics about loaded data"""
        if self.input_df is None or self.output_df is None or self.realtime_pos_df is None:
            return None
        
        input_tis = self.input_df['ti'].nunique()
        output_tis = self.output_df['ti'].nunique()
        realtime_tis = self.realtime_pos_df['ti'].nunique()
        input_tickers = self.input_df['ticker'].nunique()
        output_tickers = self.output_df['ticker'].nunique()
        realtime_tickers = self.realtime_pos_df['ticker'].nunique()
        
        return {
            'input_events': input_tis,
            'output_events': output_tis,
            'realtime_events': realtime_tis,
            'input_tickers': input_tickers,
            'output_tickers': output_tickers,
            'realtime_tickers': realtime_tickers
        }