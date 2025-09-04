from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import pandas as pd


@dataclass
class AnalysisResult:
    analyzer_name: str
    summary: str
    plot_path: Optional[str] = None
    details: Optional[str] = None


class BaseAnalyzer(ABC):
    """
    Base class for all analyzers with 3 interface dimensions:
    1. analyze_overview() - All tickers, all times
    2. analyze_time_event(ti) - All tickers at specific time
    3. analyze_ticker_timeline(ticker) - Specific ticker across all times
    4. analyze_deep(ti, ticker) - Specific time + ticker combination
    
    Analyzers can implement any subset of these interfaces.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return analyzer name for reporting"""
        pass
    
    def supports_overview(self) -> bool:
        """Return True if analyzer supports overview analysis"""
        return True
    
    def supports_time_event(self) -> bool:
        """Return True if analyzer supports time event analysis"""
        return True
    
    def supports_ticker_timeline(self) -> bool:
        """Return True if analyzer supports ticker timeline analysis"""
        return True
    
    def supports_deep_analysis(self) -> bool:
        """Return True if analyzer supports deep analysis"""
        return True
    
    def analyze_overview(self, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame,
                        split_alpha_df: pd.DataFrame, realtime_pos_df: pd.DataFrame, 
                        market_df: pd.DataFrame = None) -> Optional[AnalysisResult]:
        """
        Interface 1: Overview analysis across all tickers and times
        Returns None if not supported by this analyzer
        """
        if not self.supports_overview():
            return None
        return self._analyze_overview(incheck_alpha_df, merged_df, split_alpha_df, realtime_pos_df, market_df)
    
    def analyze_time_event(self, ti: int, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame,
                          split_alpha_df: pd.DataFrame, realtime_pos_df: pd.DataFrame,
                          market_df: pd.DataFrame = None) -> Optional[AnalysisResult]:
        """
        Interface 2: Analysis for all tickers at specific time event
        Returns None if not supported by this analyzer
        """
        if not self.supports_time_event():
            return None
        return self._analyze_time_event(ti, incheck_alpha_df, merged_df, split_alpha_df, realtime_pos_df, market_df)
    
    def analyze_ticker_timeline(self, ticker: str, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame,
                               split_alpha_df: pd.DataFrame, realtime_pos_df: pd.DataFrame,
                               market_df: pd.DataFrame = None) -> Optional[AnalysisResult]:
        """
        Interface 3: Analysis for specific ticker across all times
        Returns None if not supported by this analyzer
        """
        if not self.supports_ticker_timeline():
            return None
        return self._analyze_ticker_timeline(ticker, incheck_alpha_df, merged_df, split_alpha_df, realtime_pos_df, market_df)
    
    def analyze_deep(self, ti: int, ticker: str, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame,
                    split_alpha_df: pd.DataFrame, realtime_pos_df: pd.DataFrame,
                    market_df: pd.DataFrame = None) -> Optional[AnalysisResult]:
        """
        Interface 4: Deep analysis for specific time + ticker combination
        Returns None if not supported by this analyzer
        """
        if not self.supports_deep_analysis():
            return None
        return self._analyze_deep(ti, ticker, incheck_alpha_df, merged_df, split_alpha_df, realtime_pos_df, market_df)
    
    # Protected methods to be implemented by subclasses
    def _analyze_overview(self, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame,
                         split_alpha_df: pd.DataFrame, realtime_pos_df: pd.DataFrame,
                         market_df: pd.DataFrame = None) -> AnalysisResult:
        """Override to implement overview analysis"""
        raise NotImplementedError(f"{self.name} does not support overview analysis")
    
    def _analyze_time_event(self, ti: int, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame,
                           split_alpha_df: pd.DataFrame, realtime_pos_df: pd.DataFrame,
                           market_df: pd.DataFrame = None) -> AnalysisResult:
        """Override to implement time event analysis"""
        raise NotImplementedError(f"{self.name} does not support time event analysis")
    
    def _analyze_ticker_timeline(self, ticker: str, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame,
                                split_alpha_df: pd.DataFrame, realtime_pos_df: pd.DataFrame,
                                market_df: pd.DataFrame = None) -> AnalysisResult:
        """Override to implement ticker timeline analysis"""
        raise NotImplementedError(f"{self.name} does not support ticker timeline analysis")
    
    def _analyze_deep(self, ti: int, ticker: str, incheck_alpha_df: pd.DataFrame, merged_df: pd.DataFrame,
                     split_alpha_df: pd.DataFrame, realtime_pos_df: pd.DataFrame,
                     market_df: pd.DataFrame = None) -> AnalysisResult:
        """Override to implement deep analysis"""
        raise NotImplementedError(f"{self.name} does not support deep analysis")