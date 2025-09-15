from .base_indicator import BaseIndicator
import pandas as pd


class MovingAverageIndicator(BaseIndicator):
    """Calculates Moving Averages and crossovers, honoring params."""

    def calculate(self, stock_data: pd.DataFrame, params: dict | None = None) -> dict:
        p = params or {}
        short_window = int(p.get("short_window", 50))
        long_window = int(p.get("long_window", 200))

        close = stock_data["Close"].astype(float)
        short_ma = close.rolling(short_window).mean()
        long_ma = close.rolling(long_window).mean()

        s_val = float(short_ma.iloc[-1])
        l_val = float(long_ma.iloc[-1])

        if s_val > l_val:
            signal = "Golden Cross"
        elif s_val < l_val:
            signal = "Death Cross"
        else:
            signal = "Neutral"

        return {
            "indicator": "Moving Average",
            "signal": signal,
            "details": f"MA(short={short_window})={s_val:.2f} vs MA(long={long_window})={l_val:.2f}",
        }
