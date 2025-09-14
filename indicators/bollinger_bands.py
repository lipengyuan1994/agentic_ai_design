"""Bollinger Bands indicator."""

from .base_indicator import BaseIndicator
import pandas as pd


class BollingerBandsIndicator(BaseIndicator):
    """Compute Bollinger Bands and derive a price position signal."""

    def calculate(self, stock_data: pd.DataFrame) -> dict:
        window = 20
        ma = stock_data["Close"].rolling(window).mean()
        std = stock_data["Close"].rolling(window).std()
        upper_band = (ma + 2 * std).iloc[-1]
        lower_band = (ma - 2 * std).iloc[-1]
        current_price = stock_data["Close"].iloc[-1]

        if current_price > upper_band:
            signal = "Price above upper band"
        elif current_price < lower_band:
            signal = "Price below lower band"
        else:
            signal = "Within bands"

        return {
            "indicator": "Bollinger Bands",
            "signal": signal,
            "details": (
                f"Price {current_price:.2f}, lower {lower_band:.2f}, upper {upper_band:.2f}"
            ),
        }

