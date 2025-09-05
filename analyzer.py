from typing import List
import pandas as pd
from pathlib import Path
from base_checker import BaseChecker, CheckResult
from base_analyzer import BaseAnalyzer, AnalysisResult


class AlphaAnalyzer:
    def __init__(self):
        self.checkers: List[BaseChecker] = []
        self.analyzers: List[BaseAnalyzer] = []
        self.incheck_alpha_df = None
        self.merged_df = None
        self.split_alpha_df = None
        self.realtime_pos_df = None
        self.market_df = None
    
    def add_checker(self, checker: BaseChecker):
        """Register a new checker"""
        self.checkers.append(checker)
    
    def add_analyzer(self, analyzer: BaseAnalyzer):
        """Register a new analyzer"""
        self.analyzers.append(analyzer)
    
    def load_data(self, data_dir: str):
        """
        Load CSV files with production format (pipe-delimited):
        - InCheckAlphaEv.csv: event|alphaid|time|ticker|volume
        - MergedAlphaEv.csv: event|alphaid|time|ticker|volume  
        - SplitAlphaEv.csv: event|alphaid|time|ticker|volume
        - SplitCtxEv.csv: event|alphaid|time|ticker|realtime_pos|realtime_long_pos|realtime_short_pos|realtime_avail_shot_vol
        - MarketDataEv.csv: event|alphaid|time|ticker|last_price|prev_close_price (optional)
        """
        data_path = Path(data_dir)
        
        # Load input alpha events (InCheckAlphaEv.csv)
        input_file = data_path / "InCheckAlphaEv.csv"
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
        
        self.incheck_alpha_df = pd.read_csv(input_file, delimiter='|')
        self._validate_columns(self.incheck_alpha_df, "incheck_alpha", {'event', 'alphaid', 'time', 'ticker', 'volume'})
        self._preprocess_time_column(self.incheck_alpha_df)
        
        # Load merged alpha events (MergedAlphaEv.csv) - represents merged upstream alpha
        merged_file = data_path / "MergedAlphaEv.csv"
        if merged_file.exists():
            self.merged_df = pd.read_csv(merged_file, delimiter='|')
            self._validate_columns(self.merged_df, "merged", {'event', 'alphaid', 'time', 'ticker', 'volume'})
        else:
            # If no merged file, use incheck as merged
            self.merged_df = self.incheck_alpha_df.copy()
        self._preprocess_time_column(self.merged_df)
        
        # Load split alpha events (SplitAlphaEv.csv)  
        output_file = data_path / "SplitAlphaEv.csv"
        if not output_file.exists():
            raise FileNotFoundError(f"Split alpha file not found: {output_file}")
        
        self.split_alpha_df = pd.read_csv(output_file, delimiter='|')
        self._validate_columns(self.split_alpha_df, "split_alpha", {'event', 'alphaid', 'time', 'ticker', 'volume'})
        self._preprocess_time_column(self.split_alpha_df)
        
        # Load split context (SplitCtxEv.csv) - contains position data
        ctx_file = data_path / "SplitCtxEv.csv"
        if not ctx_file.exists():
            raise FileNotFoundError(f"Split context file not found: {ctx_file}")
        
        self.realtime_pos_df = pd.read_csv(ctx_file, delimiter='|')
        self._validate_columns(self.realtime_pos_df, "split context", {
            'event', 'alphaid', 'time', 'ticker', 'realtime_pos', 
            'realtime_long_pos', 'realtime_short_pos', 'realtime_avail_shot_vol'
        })
        self._preprocess_time_column(self.realtime_pos_df)
        
        # Load market data (MarketDataEv.csv) - optional
        market_file = data_path / "MarketDataEv.csv"
        if market_file.exists():
            self.market_df = pd.read_csv(market_file, delimiter='|')
            self._validate_columns(self.market_df, "market data", {
                'event', 'alphaid', 'time', 'ticker', 'last_price', 'prev_close_price'
            })
            self._preprocess_time_column(self.market_df)
        else:
            self.market_df = None
        
        market_records = len(self.market_df) if self.market_df is not None else 0
        print(f"Loaded {len(self.incheck_alpha_df)} incheck records, {len(self.merged_df)} merged records, "
              f"{len(self.split_alpha_df)} split records, {len(self.realtime_pos_df)} position records, "
              f"and {market_records} market data records")
    
    def _validate_columns(self, df: pd.DataFrame, data_type: str, required_cols: set):
        """Validate that required columns exist"""
        missing_cols = required_cols - set(df.columns)
        
        if missing_cols:
            raise ValueError(f"{data_type} data missing required columns: {missing_cols}")
    
    def _preprocess_time_column(self, df: pd.DataFrame):
        """Convert non-digit time values to -1 (represents previous day closing)"""
        if 'time' in df.columns:
            # Convert non-numeric time values to -1
            df['time'] = pd.to_numeric(df['time'], errors='coerce').fillna(-1).astype(int)
    
    @staticmethod
    def is_previous_day_position(time_value: int) -> bool:
        """
        Check if a time value represents a previous day position.
        
        Previous day positions are identified by:
        - time == -1 (traditional closing position marker)  
        - time < 93000000 (before 9:30:00 AM market open)
        
        Args:
            time_value: Integer time value
            
        Returns:
            True if this represents a previous day position
        """
        return time_value == -1 or time_value < 93000000
    
    def run_checks(self) -> List[CheckResult]:
        """Execute all registered checkers"""
        if (self.incheck_alpha_df is None or self.merged_df is None or 
            self.split_alpha_df is None or self.realtime_pos_df is None):
            raise RuntimeError("Data not loaded. Call load_data() first.")
        
        results = []
        for checker in self.checkers:
            try:
                result = checker.check(self.incheck_alpha_df, self.merged_df, self.split_alpha_df, 
                                     self.realtime_pos_df, self.market_df)
                results.append(result)
            except Exception as e:
                error_msg = f"Checker failed: {str(e)}"
                results.append(CheckResult(
                    checker_name=checker.name,
                    status="ERROR",
                    message=error_msg
                ))
        return results
    
    def run_analysis(self, ti=None, ticker=None) -> List[AnalysisResult]:
        """Execute analyzers based on interface"""
        if (self.incheck_alpha_df is None or self.merged_df is None or 
            self.split_alpha_df is None or self.realtime_pos_df is None):
            raise RuntimeError("Data not loaded. Call load_data() first.")
        
        results = []
        
        for analyzer in self.analyzers:
            try:
                result = None
                
                if ti is not None and ticker is not None:
                    # Interface 4: Deep analysis
                    result = analyzer.analyze_deep(ti, ticker, self.incheck_alpha_df, self.merged_df,
                                                  self.split_alpha_df, self.realtime_pos_df, self.market_df)
                elif ti is not None:
                    # Interface 2: Time event analysis
                    result = analyzer.analyze_time_event(ti, self.incheck_alpha_df, self.merged_df,
                                                        self.split_alpha_df, self.realtime_pos_df, self.market_df)
                elif ticker is not None:
                    # Interface 3: Ticker timeline analysis
                    result = analyzer.analyze_ticker_timeline(ticker, self.incheck_alpha_df, self.merged_df,
                                                             self.split_alpha_df, self.realtime_pos_df, self.market_df)
                else:
                    # Interface 1: Overview analysis
                    result = analyzer.analyze_overview(self.incheck_alpha_df, self.merged_df,
                                                      self.split_alpha_df, self.realtime_pos_df, self.market_df)
                
                if result is not None:
                    results.append(result)
                    
            except Exception as e:
                error_result = AnalysisResult(
                    analyzer_name=analyzer.name,
                    summary=f"Analysis failed: {str(e)}"
                )
                results.append(error_result)
        
        return results
    
    def get_data_summary(self):
        """Get basic statistics about loaded data"""
        if (self.incheck_alpha_df is None or self.merged_df is None or 
            self.split_alpha_df is None or self.realtime_pos_df is None):
            return None
        
        incheck_times = self.incheck_alpha_df['time'].nunique()
        merged_times = self.merged_df['time'].nunique()
        split_times = self.split_alpha_df['time'].nunique()
        pos_times = self.realtime_pos_df['time'].nunique()
        
        incheck_tickers = self.incheck_alpha_df['ticker'].nunique()
        merged_tickers = self.merged_df['ticker'].nunique()
        split_tickers = self.split_alpha_df['ticker'].nunique()
        pos_tickers = self.realtime_pos_df['ticker'].nunique()
        
        market_times = 0
        market_tickers = 0
        if self.market_df is not None:
            market_times = self.market_df['time'].nunique()
            market_tickers = self.market_df['ticker'].nunique()
        
        return {
            'incheck_events': incheck_times,
            'merged_events': merged_times,
            'split_events': split_times,
            'position_events': pos_times,
            'market_events': market_times,
            'incheck_tickers': incheck_tickers,
            'merged_tickers': merged_tickers,
            'split_tickers': split_tickers,
            'position_tickers': pos_tickers,
            'market_tickers': market_tickers
        }