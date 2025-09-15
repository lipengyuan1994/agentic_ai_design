from .base_indicator import BaseIndicator
import pandas as pd


class BollingerBandsIndicator(BaseIndicator):
    """Calculates Bollinger Bands using rolling mean and stddev, honoring params."""

    def calculate(self, stock_data: pd.DataFrame, params: dict | None = None) -> dict:
        p = params or {}
        window = int(p.get("window", 20))
        stddev = float(p.get("stddev", 2))

        close = stock_data["Close"].astype(float)
        ma = close.rolling(window).mean()
        sd = close.rolling(window).std()
        upper_band = ma + stddev * sd
        lower_band = ma - stddev * sd

        price = float(close.iloc[-1])
        upper = float(upper_band.iloc[-1])
        lower = float(lower_band.iloc[-1])

        if price > upper:
            signal = "Price above upper band"
        elif price < lower:
            signal = "Price below lower band"
        else:
            signal = "Trading within bands"

        return {
            "indicator": "Bollinger Bands",
            "signal": signal,
            "details": f"BB(window={window}, std={stddev}): price={price:.2f}, lower={lower:.2f}, upper={upper:.2f}",
        }
