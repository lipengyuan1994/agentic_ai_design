"""Exponential Moving Average crossover indicator."""

from .base_indicator import BaseIndicator
import pandas as pd


class EMAIndicator(BaseIndicator):
    """Checks the relationship between 12 and 26 day EMAs."""

    def calculate(self, stock_data: pd.DataFrame) -> dict:
        ema12 = stock_data["Close"].ewm(span=12, adjust=False).mean().iloc[-1]
        ema26 = stock_data["Close"].ewm(span=26, adjust=False).mean().iloc[-1]

        if ema12 > ema26:
            signal = "EMA12 above EMA26"
        elif ema12 < ema26:
            signal = "EMA12 below EMA26"
        else:
            signal = "EMA12 equals EMA26"

        return {
            "indicator": "EMA",
            "signal": signal,
            "details": f"EMA12 {ema12:.2f} vs EMA26 {ema26:.2f}",
        }

