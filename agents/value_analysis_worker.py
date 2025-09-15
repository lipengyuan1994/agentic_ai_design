from __future__ import annotations

from core.worker import Worker
from core.models import IndicatorResult
from dataclasses import dataclass
from typing import Any, Dict, Optional
import yfinance as yf


@dataclass
class _Metric:
    label: str
    value: Optional[float]
    weight: int


class ValueAnalysisWorker(Worker):
    """Worker that computes a heuristic value/fundamental assessment for a ticker.

    Uses yfinance to pull commonly used fundamental fields and produces a simple
    score-based signal along with the raw metrics in meta for transparency.
    """

    def __init__(self, ticker: str):
        self.ticker = ticker

    def run(self, *_args, **_kwargs) -> IndicatorResult:
        stock = yf.Ticker(self.ticker)
        info: Dict[str, Any] = getattr(stock, "info", {}) or {}

        # Extract key metrics (may be None)
        trailing_pe = _safe_float(info.get("trailingPE"))
        forward_pe = _safe_float(info.get("forwardPE"))
        price_to_book = _safe_float(info.get("priceToBook"))
        price_to_sales = _safe_float(info.get("priceToSalesTrailing12Months"))
        dividend_yield = _safe_float(info.get("dividendYield"))  # typically fraction (e.g., 0.01 == 1%)
        profit_margins = _safe_float(info.get("profitMargins"))
        operating_margins = _safe_float(info.get("operatingMargins"))
        roe = _safe_float(info.get("returnOnEquity"))
        revenue_growth = _safe_float(info.get("revenueGrowth"))
        debt_to_equity = _safe_float(info.get("debtToEquity"))
        current_ratio = _safe_float(info.get("currentRatio"))
        quick_ratio = _safe_float(info.get("quickRatio"))
        market_cap = _safe_float(info.get("marketCap"))
        free_cash_flow = _safe_float(info.get("freeCashflow"))

        fcf_yield = _safe_div(free_cash_flow, market_cap) if free_cash_flow and market_cap else None

        # Heuristic scoring
        score = 0
        rationales: list[str] = []

        def adjust(points: int, reason: str):
            nonlocal score
            score += points
            rationales.append(f"{('+' if points>=0 else '')}{points}: {reason}")

        # P/E (prefer lower vs growth caveat)
        if trailing_pe is not None:
            if trailing_pe < 15:
                adjust(2, f"Trailing P/E {trailing_pe:.1f} < 15")
            elif trailing_pe < 25:
                adjust(1, f"Trailing P/E {trailing_pe:.1f} < 25")
            elif trailing_pe > 35:
                adjust(-2, f"Trailing P/E {trailing_pe:.1f} > 35")
            elif trailing_pe > 25:
                adjust(-1, f"Trailing P/E {trailing_pe:.1f} > 25")

        # P/B
        if price_to_book is not None:
            if price_to_book < 1.0:
                adjust(2, f"P/B {price_to_book:.2f} < 1.0")
            elif price_to_book < 2.0:
                adjust(1, f"P/B {price_to_book:.2f} < 2.0")
            elif price_to_book > 5.0:
                adjust(-2, f"P/B {price_to_book:.2f} > 5.0")
            elif price_to_book > 3.0:
                adjust(-1, f"P/B {price_to_book:.2f} > 3.0")

        # FCF Yield
        if fcf_yield is not None:
            if fcf_yield > 0.08:
                adjust(2, f"FCF yield {fcf_yield:.2%} > 8%")
            elif fcf_yield > 0.04:
                adjust(1, f"FCF yield {fcf_yield:.2%} > 4%")
            elif fcf_yield < 0.00:
                adjust(-2, f"FCF yield {fcf_yield:.2%} < 0%")
            elif fcf_yield < 0.02:
                adjust(-1, f"FCF yield {fcf_yield:.2%} < 2%")

        # Profit margins
        if profit_margins is not None:
            if profit_margins > 0.15:
                adjust(2, f"Profit margin {profit_margins:.1%} > 15%")
            elif profit_margins > 0.08:
                adjust(1, f"Profit margin {profit_margins:.1%} > 8%")
            elif profit_margins < 0.00:
                adjust(-2, f"Profit margin {profit_margins:.1%} < 0%")
            elif profit_margins < 0.03:
                adjust(-1, f"Profit margin {profit_margins:.1%} < 3%")

        # ROE
        if roe is not None:
            if roe > 0.15:
                adjust(2, f"ROE {roe:.1%} > 15%")
            elif roe > 0.08:
                adjust(1, f"ROE {roe:.1%} > 8%")
            elif roe < 0.00:
                adjust(-2, f"ROE {roe:.1%} < 0%")
            elif roe < 0.05:
                adjust(-1, f"ROE {roe:.1%} < 5%")

        # Revenue growth
        if revenue_growth is not None:
            if revenue_growth > 0.10:
                adjust(1, f"Revenue growth {revenue_growth:.1%} > 10%")
            elif revenue_growth < 0.00:
                adjust(-1, f"Revenue growth {revenue_growth:.1%} < 0%")

        # Leverage
        if debt_to_equity is not None:
            if debt_to_equity < 50:  # yfinance uses percentage points sometimes; keep lenient
                adjust(2, f"Debt/Equity {debt_to_equity:.1f} < 50")
            elif debt_to_equity < 100:
                adjust(1, f"Debt/Equity {debt_to_equity:.1f} < 100")
            elif debt_to_equity > 200:
                adjust(-2, f"Debt/Equity {debt_to_equity:.1f} > 200")
            elif debt_to_equity > 150:
                adjust(-1, f"Debt/Equity {debt_to_equity:.1f} > 150")

        # Liquidity
        if current_ratio is not None:
            if current_ratio > 2.0:
                adjust(1, f"Current ratio {current_ratio:.2f} > 2.0")
            elif current_ratio < 1.0:
                adjust(-1, f"Current ratio {current_ratio:.2f} < 1.0")

        # Final signal
        if score >= 4:
            signal = "Undervalued/Quality"
        elif score >= 1:
            signal = "Reasonable"
        elif score <= -3:
            signal = "Overvalued/Risky"
        else:
            signal = "Mixed/Neutral"

        details = (
            f"Value score {score}. Key points: " + "; ".join(rationales[:8]) + ("; ..." if len(rationales) > 8 else "")
        )

        meta = {
            "metrics": {
                "trailingPE": trailing_pe,
                "forwardPE": forward_pe,
                "priceToBook": price_to_book,
                "priceToSales": price_to_sales,
                "dividendYield": dividend_yield,
                "profitMargins": profit_margins,
                "operatingMargins": operating_margins,
                "returnOnEquity": roe,
                "revenueGrowth": revenue_growth,
                "debtToEquity": debt_to_equity,
                "currentRatio": current_ratio,
                "quickRatio": quick_ratio,
                "marketCap": market_cap,
                "freeCashflow": free_cash_flow,
                "fcfYield": fcf_yield,
            },
            "score": score,
            "rationales": rationales,
        }

        return IndicatorResult(
            indicator="Value Analysis",
            signal=signal,
            details=details,
            meta=meta,
        )


def _safe_float(x: Any) -> Optional[float]:
    try:
        return float(x) if x is not None else None
    except Exception:
        return None


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    try:
        if a is None or b is None or b == 0:
            return None
        return float(a) / float(b)
    except Exception:
        return None

