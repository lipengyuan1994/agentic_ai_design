from abc import ABC, abstractmethod
import pandas as pd

class BaseIndicator(ABC):
    """Abstract base class for technical indicators."""

    @abstractmethod
    def calculate(self, stock_data: pd.DataFrame) -> dict:
        """Calculates the indicator and returns the result.

        Args:
            stock_data: A pandas DataFrame with the historical stock data.

        Returns:
            A dictionary containing the indicator's signal and details.
        """
        pass
