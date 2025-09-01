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
    def check(self, input_df: pd.DataFrame, output_df: pd.DataFrame, realtime_pos_df: pd.DataFrame) -> CheckResult:
        """
        Run the check on input, output and realtime position data
        Args:
            input_df: DataFrame loaded from IncheckAlphaEv.csv (columns: ti,sid,ticker,target)
            output_df: DataFrame loaded from SplitAlphaEv.csv (columns: ti,sid,ticker,target)
            realtime_pos_df: DataFrame loaded from RealtimePosEv.csv (columns: ti,sid,ticker,realtime_pos)
        Returns:
            CheckResult with status and message
        """
        pass