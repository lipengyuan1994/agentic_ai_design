"""Moving Average Convergence Divergence indicator."""

from .base_indicator import BaseIndicator
import pandas as pd


class MACDIndicator(BaseIndicator):
    """Compute MACD line and signal line crossover."""

    def calculate(self, stock_data: pd.DataFrame) -> dict:
        ema12 = stock_data["Close"].ewm(span=12, adjust=False).mean()
        ema26 = stock_data["Close"].ewm(span=26, adjust=False).mean()
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()

        macd_value = macd_line.iloc[-1]
        signal_value = signal_line.iloc[-1]

        if macd_value > signal_value:
            signal = "Bullish Crossover"
        elif macd_value < signal_value:
            signal = "Bearish Crossover"
        else:
            signal = "Neutral"

        return {
            "indicator": "MACD",
            "signal": signal,
            "details": f"MACD {macd_value:.2f} vs signal {signal_value:.2f}",
        }

