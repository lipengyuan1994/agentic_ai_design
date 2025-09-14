"""Orchestrator agent for running stock technical analysis."""

import json
from typing import List

from core.agent import Agent
from data.data_fetcher import get_stock_data
from .indicator_worker import IndicatorWorker


class TechnicalAnalysisOrchestrator(Agent):
    """Coordinates fetching data, running indicators and summarising results."""

    def run(self, ticker: str, indicators: List[str], period: str = "1y") -> str:
        """Run the orchestrator for a given stock ticker.

        Args:
            ticker: Stock ticker symbol, e.g. ``AAPL``.
            indicators: List of indicator names to evaluate.
            period: Historical period passed to the data fetcher.

        Returns:
            Textual summary of the technical analysis.
        """

        # 1. Fetch stock data
        stock_data = get_stock_data(ticker, period=period)
        stock_json = stock_data.to_json()

        # 2. Create and run worker agents for each indicator
        worker_results: List[str] = []
        for indicator_name in indicators:
            worker = IndicatorWorker(indicator_name)
            result = worker.run(stock_json)
            worker_results.append(result)

        # 3. Summarize the results
        summary = self._summarize(worker_results, ticker)
        return summary

    def _summarize(self, results: List[str], ticker: str) -> str:
        """Summarise worker results into a brief report."""

        lines = []
        bullish = bearish = neutral = 0
        for item in results:
            data = json.loads(item)
            indicator = data.get("indicator", "Unknown")
            signal = data.get("signal", "N/A")
            details = data.get("details", "")
            lines.append(f"{indicator}: {signal} - {details}")

            key = signal.lower()
            if any(word in key for word in ["bull", "golden", "oversold"]):
                bullish += 1
            elif any(word in key for word in ["bear", "death", "overbought"]):
                bearish += 1
            else:
                neutral += 1

        # Determine overall sentiment
        if bullish > bearish and bullish > neutral:
            overall = "Bullish"
        elif bearish > bullish and bearish > neutral:
            overall = "Bearish"
        else:
            overall = "Neutral"

        report = [f"Technical analysis for {ticker}"]
        report.extend(f"- {line}" for line in lines)
        report.append(f"Overall signal: {overall}")
        return "\n".join(report)

