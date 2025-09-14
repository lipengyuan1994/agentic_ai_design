from .base_indicator import BaseIndicator
import pandas as pd

class RSIIndicator(BaseIndicator):
    """Calculates the Relative Strength Index (RSI)."""

    def calculate(self, stock_data: pd.DataFrame) -> dict:
        """Calculates the RSI.

        Args:
            stock_data: A pandas DataFrame with historical stock data.

        Returns:
            A dictionary with the RSI signal and details.
        """
        # This is a placeholder for the actual RSI calculation.
        # In a real implementation, you would use a library like pandas-ta.
        rsi_value = 30  # Dummy value

        signal = "Neutral"
        if rsi_value < 30:
            signal = "Oversold"
        elif rsi_value > 70:
            signal = "Overbought"

        return {
            "indicator": "RSI",
            "signal": signal,
            "details": f"RSI is currently at {rsi_value}."
        }
