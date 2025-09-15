"""Moving Average Convergence Divergence indicator."""

from .base_indicator import BaseIndicator
import pandas as pd


class MACDIndicator(BaseIndicator):
    """Compute MACD line and signal line crossover, honoring params."""

    def calculate(self, stock_data: pd.DataFrame, params: dict | None = None) -> dict:
        p = params or {}
        fast = int(p.get("fast", 12))
        slow = int(p.get("slow", 26))
        signal_p = int(p.get("signal", 9))

        close = stock_data["Close"].astype(float)
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_p, adjust=False).mean()

        macd_value = float(macd_line.iloc[-1])
        signal_value = float(signal_line.iloc[-1])

        if macd_value > signal_value:
            signal = "Bullish Crossover"
        elif macd_value < signal_value:
            signal = "Bearish Crossover"
        else:
            signal = "Neutral"

        return {
            "indicator": "MACD",
            "signal": signal,
            "details": f"MACD(fast={fast}, slow={slow}, signal={signal_p}) → {macd_value:.2f} vs {signal_value:.2f}",
        }
