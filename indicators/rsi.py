"""Relative Strength Index indicator."""

from .base_indicator import BaseIndicator
import pandas as pd


class RSIIndicator(BaseIndicator):
    """Compute the 14-day RSI and produce a signal."""

    def calculate(self, stock_data: pd.DataFrame) -> dict:
        delta = stock_data["Close"].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.rolling(14).mean()
        roll_down = down.rolling(14).mean()
        rs = roll_up / roll_down
        rsi = 100 - (100 / (1 + rs))
        rsi_value = rsi.iloc[-1]

        if rsi_value < 30:
            signal = "Oversold"
        elif rsi_value > 70:
            signal = "Overbought"
        else:
            signal = "Neutral"

        return {
            "indicator": "RSI",
            "signal": signal,
            "details": f"RSI is currently at {rsi_value:.2f}",
        }

