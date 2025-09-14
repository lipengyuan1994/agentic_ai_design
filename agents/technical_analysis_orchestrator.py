from core.orchestrator import Orchestrator
from core.models import IndicatorResult, AnalysisReport, SummaryResult
from openai import OpenAI
import json
from data.data_fetcher import get_stock_data
from .indicator_worker import IndicatorWorker
import config
import concurrent.futures
import os
from datetime import datetime
import yfinance as yf

client = None  # Lazily initialized when needed

class TechnicalAnalysisOrchestrator(Orchestrator):
    """Orchestrator for performing technical analysis on a stock."""

    def run(self, ticker: str, indicators: list) -> str:
        """Runs the technical analysis orchestrator for a given stock ticker.

        Args:
            ticker: The stock ticker to analyze.
            indicators: A list of indicator names to calculate.

        Returns:
            The path to the saved analysis report.
        """
        # 1. Fetch stock data
        period = "1y"
        stock_data = get_stock_data(ticker)

        # 2. Create and run worker agents for each indicator concurrently
        worker_results: list[IndicatorResult] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(IndicatorWorker(indicator_name).run, stock_data): indicator_name for indicator_name in indicators}
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    worker_results.append(result)
                except Exception as exc:
                    indicator_name = futures[future]
                    print(f'{indicator_name} generated an exception: {exc}')

        # 3. Summarize the results
        summary = self._summarize(worker_results)

        # 4. Build structured analysis report
        analysis = AnalysisReport(
            ticker=ticker,
            period=period,
            generated_at=datetime.now(),
            indicators=worker_results,
            summary=summary,
        )

        # 5. Save the report (Markdown only)
        report_path = self._save_report(ticker, analysis)

        return report_path

    def _summarize(self, results: list[IndicatorResult]) -> SummaryResult:
        """Summarizes the results from the worker agents.

        Args:
            results: A list of JSON strings from the worker agents.

        Returns:
            A summary of the technical analysis.
        """
        payload = [r.model_dump() for r in results]
        prompt = (
            "Please summarize the following technical analysis results into a coherent report:\n\n"
            + json.dumps(payload)
            + "\n\nProvide a clear and concise summary of the stock's technical outlook."
        )

        try:
            if not config.OPENAI_API_KEY:
                raise RuntimeError("OPENAI_API_KEY not configured")
            global client
            if client is None:
                client = OpenAI(api_key=config.OPENAI_API_KEY)
            model_name = "gpt-4-turbo"
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a financial analyst specializing in technical analysis."},
                    {"role": "user", "content": prompt},
                ],
            )
            summary_text = response.choices[0].message.content
            return SummaryResult(summary_text=summary_text, method="openai", model=model_name)
        except Exception as e:
            # Fallback: simple, local summary if OpenAI is unavailable
            lines = ["Technical Analysis Summary:"]
            for item in results:
                lines.append(f"- {item.indicator}: {item.signal}. {item.details or ''}")
            lines.append(f"\n(Note: Used local fallback summary due to: {e})")
            return SummaryResult(summary_text="\n".join(lines), method="local_fallback")

    def _save_report(self, ticker: str, analysis: AnalysisReport) -> str:
        """Saves the analysis report to a markdown file.

        Args:
            ticker: The stock ticker.
            analysis: Structured analysis report.

        Returns:
            The path to the saved report.
        """
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        date_str = datetime.now().strftime("%Y-%m-%d")
        # Markdown report
        md_path = os.path.join(reports_dir, f"{ticker}_{date_str}.md")

        # Resolve display name locally here to keep changes scoped to report generation
        stock_name = self._resolve_stock_name(ticker)
        header = f"### Technical Analysis Report: {stock_name}\n\n"
        with open(md_path, "w") as f:
            f.write(header + analysis.summary.summary_text)

        return md_path

    def _resolve_stock_name(self, ticker: str) -> str:
        """Best-effort resolution of a human-readable stock name.

        Uses yfinance metadata; falls back to the ticker when unavailable.
        """
        try:
            stock = yf.Ticker(ticker)
            info = getattr(stock, "info", {}) or {}
            name = info.get("shortName") or info.get("longName")
            return name or ticker
        except Exception:
            return ticker
