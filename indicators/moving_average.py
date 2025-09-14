"""Simple moving average crossover indicator."""

from .base_indicator import BaseIndicator
import pandas as pd


class MovingAverageIndicator(BaseIndicator):
    """Calculates 50/200 day moving average crossovers."""

    def calculate(self, stock_data: pd.DataFrame) -> dict:
        """Return crossover signal based on 50 and 200 day MAs."""

        short_term_ma = stock_data["Close"].rolling(window=50).mean().iloc[-1]
        long_term_ma = stock_data["Close"].rolling(window=200).mean().iloc[-1]

        if short_term_ma > long_term_ma:
            signal = "Golden Cross"
        elif short_term_ma < long_term_ma:
            signal = "Death Cross"
        else:
            signal = "Neutral"

        return {
            "indicator": "Moving Average",
            "signal": signal,
            "details": f"50-day MA {short_term_ma:.2f} vs 200-day MA {long_term_ma:.2f}",
        }

