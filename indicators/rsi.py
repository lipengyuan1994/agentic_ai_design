"""Relative Strength Index indicator."""

from .base_indicator import BaseIndicator
import pandas as pd


class RSIIndicator(BaseIndicator):
    """Compute RSI and produce a signal, honoring params like period/thresholds."""

    def calculate(self, stock_data: pd.DataFrame, params: dict | None = None) -> dict:
        p = params or {}
        period = int(p.get("period", 14))
        oversold = float(p.get("oversold", 30))
        overbought = float(p.get("overbought", 70))

        close = stock_data["Close"].astype(float)
        delta = close.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.rolling(period).mean()
        roll_down = down.rolling(period).mean()
        rs = roll_up / roll_down
        rsi = 100 - (100 / (1 + rs))
        rsi_value = float(rsi.iloc[-1])

        if rsi_value < oversold:
            signal = "Oversold"
        elif rsi_value > overbought:
            signal = "Overbought"
        else:
            signal = "Neutral"

        return {
            "indicator": "RSI",
            "signal": signal,
            "details": f"RSI(period={period}) is {rsi_value:.2f}; thresholds {oversold}/{overbought}",
        }
