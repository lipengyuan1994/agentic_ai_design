from core.orchestrator import run as Orchestrator
from openai import OpenAI
import json
from data.data_fetcher import get_stock_data
from .indicator_worker import IndicatorWorker
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

class TechnicalAnalysisOrchestrator(Orchestrator):
    """Orchestrator for performing technical analysis on a stock."""

    def run(self, ticker: str, indicators: list) -> str:
        """Runs the technical analysis orchestrator for a given stock ticker.

        Args:
            ticker: The stock ticker to analyze.
            indicators: A list of indicator names to calculate.

        Returns:
            A summary of the technical analysis.
        """
        # 1. Fetch stock data
        stock_data = get_stock_data(ticker)

        # 2. Create and run worker agents for each indicator
        worker_results = []
        for indicator_name in indicators:
            worker = IndicatorWorker(indicator_name)
            result = worker.run(stock_data.to_json())
            worker_results.append(result)

        # 3. Summarize the results
        summary = self._summarize(worker_results)

        return summary

    def _summarize(self, results: list) -> str:
        """Summarizes the results from the worker agents.

        Args:
            results: A list of JSON strings from the worker agents.

        Returns:
            A summary of the technical analysis.
        """
        prompt = f"""Please summarize the following technical analysis results into a coherent report:

        {json.dumps(results)}

        Provide a clear and concise summary of the stock's technical outlook."""

        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=[
                {"role": "system", "content": "You are a financial analyst specializing in technical analysis."},
                {"role": "user", "content": prompt}
            ]
        )

        return response.choices[0].message.content
