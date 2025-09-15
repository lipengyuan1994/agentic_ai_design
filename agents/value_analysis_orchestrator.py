from __future__ import annotations

from core.orchestrator import Orchestrator
from core.models import IndicatorResult, AnalysisReport, SummaryResult, OrchestratorPlan
from openai import OpenAI
from datetime import datetime
import json
import os
import yfinance as yf

from .value_analysis_worker import ValueAnalysisWorker
import config


client = None  # Lazily initialized when needed


class ValueAnalysisOrchestrator(Orchestrator):
    """Orchestrator for performing value/fundamental analysis on a stock."""

    def run(self, ticker: str) -> str:
        # Run a single value-analysis worker
        worker = ValueAnalysisWorker(ticker)
        result: IndicatorResult = worker.run()

        # Summarize the result (LLM with fallback)
        summary = self._summarize([result])

        # Build and save analysis report
        analysis = AnalysisReport(
            ticker=ticker,
            period="n/a",
            generated_at=datetime.now(),
            indicators=[result],
            summary=summary,
            plan=self._fake_plan(ticker),
        )

        report_path = self._save_report(ticker, analysis)
        return report_path

    def _fake_plan(self, ticker: str) -> OrchestratorPlan:
        # Provide a minimal plan-like object so downstream stays consistent
        return OrchestratorPlan(
            ticker=ticker,
            period="n/a",
            requested_indicators=["Value Analysis"],
            plan_indicators=["Value Analysis"],
            plan_items=[OrchestratorPlan.IndicatorPlanItem(name="Value Analysis", params={})],
            rationale=(
                "Evaluate fundamental metrics such as P/E, P/B, margins, ROE, revenue growth, FCF yield, and leverage to form a value thesis."
            ),
            strategy="Compute metrics from company fundamentals and score heuristically.",
        )

    def _summarize(self, results: list[IndicatorResult]) -> SummaryResult:
        payload = [r.model_dump() for r in results]
        prompt = (
            "You are a financial analyst specializing in value investing.\n"
            "Given the following fundamental metrics and heuristic score, write a concise Markdown summary of the business quality and valuation. "
            "Include highlights on margins, growth, returns on capital, leverage, and whether valuation appears attractive.\n\n"
            f"Results (JSON):\n{json.dumps(payload)}\n\n"
            "Be balanced and note caveats when data is missing."
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
                    {"role": "system", "content": "You are a value-focused equity analyst."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            summary_text = response.choices[0].message.content
            return SummaryResult(summary_text=summary_text, method="openai", model=model_name)
        except Exception as e:
            # Fallback: simple summary
            r = results[0]
            meta = r.meta or {}
            score = meta.get("score")
            details = r.details or ""
            lines = [
                "Value Analysis Summary:",
                f"Signal: {r.signal}",
                f"Score: {score}",
                details,
                "\n(Note: Used local fallback summary due to unavailability of LLM)",
            ]
            if e:
                lines[-1] = lines[-1][:-1] + f": {e})"
            return SummaryResult(summary_text="\n".join(lines), method="local_fallback", model=None)

    def _save_report(self, ticker: str, analysis: AnalysisReport) -> str:
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        date_str = datetime.now().strftime("%Y%m%d")
        md_path = os.path.join(reports_dir, f"{ticker}_{date_str}_value.md")

        stock_name = self._resolve_stock_name(ticker)
        header = f"### Value Analysis Report: {stock_name}\n\n"
        with open(md_path, "w") as f:
            f.write(header + analysis.summary.summary_text)
        return md_path

    def _resolve_stock_name(self, ticker: str) -> str:
        try:
            stock = yf.Ticker(ticker)
            info = getattr(stock, "info", {}) or {}
            name = info.get("shortName") or info.get("longName")
            return name or ticker
        except Exception:
            return ticker
