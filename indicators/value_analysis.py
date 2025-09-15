"""Value analysis indicator: basic valuation metrics and quick take."""

from .base_indicator import BaseIndicator
import pandas as pd
import yfinance as yf


class ValueAnalysisIndicator(BaseIndicator):
    """Fetch basic valuation data and provide a quick assessment."""

    def calculate(self, stock_data: pd.DataFrame, params: dict | None = None) -> dict:
        p = params or {}
        ticker = p.get("ticker")

        pe = None
        pb = None
        peg = None
        mc = None
        try:
            if ticker:
                t = yf.Ticker(ticker)
                info = getattr(t, "info", {}) or {}
                pe = info.get("trailingPE") or info.get("forwardPE")
                pb = info.get("priceToBook")
                peg = info.get("pegRatio")
                mc = info.get("marketCap")
        except Exception:
            pass

        details_parts = []
        if pe is not None:
            details_parts.append(f"P/E: {pe:.2f}")
        if pb is not None:
            details_parts.append(f"P/B: {pb:.2f}")
        if peg is not None:
            details_parts.append(f"PEG: {peg:.2f}")
        if mc is not None:
            details_parts.append(f"Market Cap: {mc:,}")

        details = ", ".join(details_parts) if details_parts else "Valuation data unavailable (network/cache)."

        # Naive signal heuristic
        signal = "Neutral"
        try:
            if pe is not None and pe < 15:
                signal = "Potentially Undervalued"
            if peg is not None and peg < 1.0:
                signal = "Growth Undervalued"
            if pe is not None and pe > 35:
                signal = "Potentially Overvalued"
        except Exception:
            pass

        return {
            "indicator": "Value Analysis",
            "signal": signal,
            "details": details,
        }

