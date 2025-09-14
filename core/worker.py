"""Core utilities for worker agents."""

from abc import ABC, abstractmethod
import pandas as pd
import json


class Worker(ABC):
    """Abstract base class for workers that process stock data."""

    @abstractmethod
    def run(self, stock_data_json: str) -> str:
        """Run the worker on provided stock data.

        Args:
            stock_data_json: Stock data encoded as a JSON string.

        Returns:
            A JSON string containing the worker's output.
        """
        raise NotImplementedError


def run(indicator: str, stock_data_json: str) -> str:
    """Legacy helper for computing indicators.

    This function is retained for backward compatibility with the early
    prototype orchestrator. New code should subclass :class:`Worker` instead
    of using this helper directly.
    """
    stock_data = pd.read_json(stock_data_json)

    # In a real implementation, you would have a separate function for each
    # indicator. For simplicity, we'll just return a dummy result.
    result = {
        "indicator": indicator,
        "signal": "Neutral",
        "details": f"Calculation for {indicator} not implemented.",
    }

    if indicator == "RSI":
        result["signal"] = "Oversold"
        result["details"] = "RSI is at 25, indicating the stock may be oversold."
    elif indicator == "MACD":
        result["signal"] = "Bullish Crossover"
        result["details"] = "MACD line has crossed above the signal line."
    elif indicator == "Bollinger Bands":
        result["signal"] = "Trading within bands"
        result["details"] = (
            "The stock is trading within the upper and lower Bollinger Bands."
        )
    elif indicator == "Moving Average":
        result["signal"] = "Golden Cross"
        result["details"] = (
            "The 50-day moving average has crossed above the 200-day moving average."
        )

    return json.dumps(result)

