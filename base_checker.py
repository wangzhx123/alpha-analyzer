from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import pandas as pd


@dataclass
class CheckResult:
    checker_name: str
    status: str  # "PASS" | "FAIL" | "WARN" | "ERROR"
    message: str
    details: Optional[str] = None


class BaseChecker(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Return checker name for reporting"""
        pass

    @abstractmethod
    def check(
        self,
        incheck_alpha_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        split_alpha_df: pd.DataFrame,
        realtime_pos_df: pd.DataFrame,
        market_df: pd.DataFrame = None,
    ) -> CheckResult:
        """
        Run the check on incheck, merged, split, position and market data
        Args:
            incheck_alpha_df: DataFrame from InCheckAlphaEv.csv (columns: event|alphaid|time|ticker|volume)
            merged_df: DataFrame from MergedAlphaEv.csv (columns: event|alphaid|time|ticker|volume)
            split_alpha_df: DataFrame from SplitAlphaEv.csv (columns: event|alphaid|time|ticker|volume)
            realtime_pos_df: DataFrame from SplitCtxEv.csv (columns: event|alphaid|time|ticker|realtime_pos|...)
            market_df: Optional DataFrame from MarketDataEv.csv (columns: event|alphaid|time|ticker|last_price|prev_close_price)
        Returns:
            CheckResult with status and message
        """
        pass
