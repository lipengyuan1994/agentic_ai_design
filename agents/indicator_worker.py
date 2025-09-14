from core.worker import Worker
from core.models import IndicatorResult
import pandas as pd
import json
import importlib

class IndicatorWorker(Worker):
    """Worker for calculating a single technical indicator."""

    def __init__(self, indicator_name: str):
        self.indicator_name = indicator_name.lower()

    def run(self, stock_data_or_json) -> IndicatorResult:
        """Runs the indicator calculation.

        Args:
            stock_data_json: A JSON string of the stock data.

        Returns:
            A JSON string with the results of the indicator calculation.
        """
        # Accept a DataFrame directly (preferred), or a JSON string for backward compatibility
        if isinstance(stock_data_or_json, pd.DataFrame):
            stock_data = stock_data_or_json
        else:
            stock_data = pd.read_json(stock_data_or_json)

        try:
            # Dynamically import the indicator module
            module_name = self.indicator_name.replace(' ', '_')
            indicator_module = importlib.import_module(f"indicators.{module_name}")
            
            # The indicator class is expected to be named like 'RSIIndicator'
            if ' ' in self.indicator_name:
                class_name_prefix = self.indicator_name.title().replace(' ', '')
                indicator_class_name = f"{class_name_prefix}Indicator"
            else:
                indicator_class_name = f"{self.indicator_name.upper()}Indicator"
            indicator_class = getattr(indicator_module, indicator_class_name)
            indicator_instance = indicator_class()

            # Calculate the indicator
            result = indicator_instance.calculate(stock_data)
            # Normalize into a structured IndicatorResult
            if isinstance(result, dict):
                return IndicatorResult(**result)
            elif isinstance(result, IndicatorResult):
                return result
            else:
                return IndicatorResult(
                    indicator=self.indicator_name.title(),
                    signal="Error",
                    details=f"Unexpected indicator result type: {type(result)}",
                )
        except (ImportError, AttributeError) as e:
            return IndicatorResult(
                indicator=self.indicator_name.title(),
                signal="Error",
                details=f"Could not calculate indicator: {e}",
            )
