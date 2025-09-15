from core.worker import Worker
from core.models import IndicatorResult
import pandas as pd
import json
import importlib

class IndicatorWorker(Worker):
    """Worker for calculating a single technical indicator."""

    def __init__(self, indicator_name: str):
        self.indicator_name = indicator_name.lower()

    def run(self, stock_data_or_json, params: dict | None = None) -> IndicatorResult:
        """Runs the indicator calculation.

        Args:
            stock_data_or_json: A pandas DataFrame (preferred) or a JSON string of the stock data.
            params: Optional per-indicator parameters (e.g., window sizes).

        Returns:
            IndicatorResult with the results of the indicator calculation.
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
            
            # Resolve indicator class name robustly (handles acronyms and normal words)
            candidate_class_names = []
            if ' ' in self.indicator_name:
                candidate_class_names.append(self.indicator_name.title().replace(' ', '') + 'Indicator')
            else:
                base = self.indicator_name
                candidate_class_names.extend([
                    base.upper() + 'Indicator',     # e.g., RSIIndicator, MACDIndicator
                    base.title() + 'Indicator',     # e.g., NewsIndicator, ValueAnalysisIndicator
                    base.capitalize() + 'Indicator' # fallback
                ])
            indicator_class = None
            for name in candidate_class_names:
                if hasattr(indicator_module, name):
                    indicator_class = getattr(indicator_module, name)
                    break
            if indicator_class is None:
                raise AttributeError(f"No matching indicator class in module for {self.indicator_name}: tried {candidate_class_names}")
            indicator_instance = indicator_class()

            # Calculate the indicator with optional parameters
            result = indicator_instance.calculate(stock_data, params or {})
            # Normalize into a structured IndicatorResult
            if isinstance(result, dict):
                ir = IndicatorResult(**result)
            elif isinstance(result, IndicatorResult):
                ir = result
            else:
                ir = IndicatorResult(
                    indicator=self.indicator_name.title(),
                    signal="Error",
                    details=f"Unexpected indicator result type: {type(result)}",
                )
            # Ensure params are recorded for traceability
            return ir.model_copy(update={"meta": {**(ir.meta or {}), "params": params or {}}})
        except (ImportError, AttributeError) as e:
            return IndicatorResult(
                indicator=self.indicator_name.title(),
                signal="Error",
                details=f"Could not calculate indicator: {e}",
            )
