from core.orchestrator import Orchestrator
from core.models import IndicatorResult, AnalysisReport, SummaryResult, OrchestratorPlan
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

        # 1b. LLM-based planning: decide which indicators to run and why
        plan = self._plan(ticker=ticker, requested_indicators=indicators, period=period)
        # Prefer rich plan items; fall back to simple list of names
        if plan.plan_items:
            planned_items = plan.plan_items
        else:
            names = plan.plan_indicators or indicators or ["RSI", "MACD", "Bollinger Bands", "Moving Average"]
            planned_items = [OrchestratorPlan.IndicatorPlanItem(name=n, params={}) for n in names]

        # 2. Create and run worker agents for each indicator concurrently
        worker_results: list[IndicatorResult] = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(IndicatorWorker(item.name).run, stock_data, item.params): item for item in planned_items}
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result()
                    worker_results.append(result)
                except Exception as exc:
                    item = futures[future]
                    print(f'{item.name} generated an exception: {exc}')

        # 3. Summarize the results
        summary = self._summarize(worker_results, plan)

        # 4. Build structured analysis report
        analysis = AnalysisReport(
            ticker=ticker,
            period=period,
            generated_at=datetime.now(),
            indicators=worker_results,
            summary=summary,
            plan=plan,
        )

        # 5. Save the report (Markdown only)
        report_path = self._save_report(ticker, analysis)

        return report_path

    def _summarize(self, results: list[IndicatorResult], plan: OrchestratorPlan | None = None) -> SummaryResult:
        """Summarizes the results from the worker agents.

        Args:
            results: A list of JSON strings from the worker agents.

        Returns:
            A summary of the technical analysis.
        """
        payload = [r.model_dump() for r in results]
        plan_block = ""
        if plan:
            plan_block = (
                f"Ticker: {plan.ticker}\nPeriod: {plan.period}\n"
                f"Requested: {plan.requested_indicators}\nPlanned: {plan.plan_indicators}\n"
                f"Rationale: {plan.rationale or ''}\nStrategy: {plan.strategy or ''}\n\n"
            )
        prompt = (
            "You are summarizing a technical analysis using the following planning context and indicator results.\n\n"
            + plan_block
            + "Indicator results (JSON):\n"
            + json.dumps(payload)
            + "\n\nProvide a clear, concise Markdown summary of the stock's technical outlook."
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
            if plan:
                lines.append(f"Plan: {', '.join(plan.plan_indicators)}")
                if plan.rationale:
                    lines.append(f"Rationale: {plan.rationale}")
            for item in results:
                lines.append(f"- {item.indicator}: {item.signal}. {item.details or ''}")
            lines.append(f"\n(Note: Used local fallback summary due to: {e})")
            return SummaryResult(summary_text="\n".join(lines), method="local_fallback")

    def _plan(self, ticker: str, requested_indicators: list | None, period: str) -> OrchestratorPlan:
        """LLM-based orchestration plan for which indicators to compute and why.

        Falls back to a deterministic plan using the requested indicators (or defaults) if LLM is unavailable.
        """
        default_indicators = ["RSI", "MACD", "Bollinger Bands", "Moving Average"]
        base = OrchestratorPlan(
            ticker=ticker,
            period=period,
            requested_indicators=requested_indicators or default_indicators,
        )
        try:
            if not config.OPENAI_API_KEY:
                raise RuntimeError("OPENAI_API_KEY not configured")
            global client
            if client is None:
                client = OpenAI(api_key=config.OPENAI_API_KEY)
            model_name = "gpt-4-turbo"
            system = (
                "You are an expert trading assistant and orchestrator. Given a stock ticker and possible indicators, "
                "propose an ordered list of indicators to compute and explain why. For each indicator, include parameters (e.g., window sizes). "
                "Respond ONLY with JSON matching the schema: "
                "{\"plan_items\":[{\"name\":string,\"params\":object}], \"plan_indicators\": string[], \"rationale\": string, \"strategy\": string, \"max_workers\": number}."
            )
            user = (
                f"Ticker: {ticker}\nPeriod: {period}\nRequested indicators: {requested_indicators or default_indicators}. "
                "Consider typical retail/quant workflows and choose a sensible order."
            )
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content or "{}"
            data = json.loads(content)
            # Build plan items with sensible defaults if not provided
            def default_params_for(name: str) -> dict:
                name_low = name.lower()
                if name_low == "rsi":
                    return {"period": 14}
                if name_low == "macd":
                    return {"fast": 12, "slow": 26, "signal": 9}
                if name_low in ("bollinger bands", "bollinger_bands", "bollinger-bands"):
                    return {"window": 20, "stddev": 2}
                if name_low in ("moving average", "moving_average", "moving-average"):
                    return {"short_window": 50, "long_window": 200}
                return {}
            raw_items = data.get("plan_items") or []
            if raw_items:
                plan_items = [
                    OrchestratorPlan.IndicatorPlanItem(name=it.get("name"), params=it.get("params") or default_params_for(it.get("name", "")))
                    for it in raw_items if it and it.get("name")
                ]
            else:
                names = data.get("plan_indicators") or (requested_indicators or default_indicators)
                plan_items = [OrchestratorPlan.IndicatorPlanItem(name=n, params=default_params_for(n)) for n in names]

            plan = OrchestratorPlan(
                ticker=ticker,
                period=period,
                requested_indicators=requested_indicators or default_indicators,
                plan_indicators=[it.name for it in plan_items],
                plan_items=plan_items,
                rationale=data.get("rationale"),
                strategy=data.get("strategy"),
                max_workers=data.get("max_workers"),
            )
            return plan
        except Exception:
            # Fallback: use requested list or defaults
            base.plan_indicators = requested_indicators or default_indicators
            # populate basic plan_items with default params
            def default_params_for(name: str) -> dict:
                name_low = name.lower()
                if name_low == "rsi":
                    return {"period": 14}
                if name_low == "macd":
                    return {"fast": 12, "slow": 26, "signal": 9}
                if name_low in ("bollinger bands", "bollinger_bands", "bollinger-bands"):
                    return {"window": 20, "stddev": 2}
                if name_low in ("moving average", "moving_average", "moving-average"):
                    return {"short_window": 50, "long_window": 200}
                return {}
            base.plan_items = [OrchestratorPlan.IndicatorPlanItem(name=n, params=default_params_for(n)) for n in base.plan_indicators]
            base.rationale = "Fallback plan: using requested indicators (or defaults) due to unavailable LLM or parsing error."
            base.strategy = "Compute indicators in given order and summarize."
            return base

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

        date_str = datetime.now().strftime("%Y%m%d")
        # Markdown report with explicit technical suffix
        md_path = os.path.join(reports_dir, f"{ticker}_{date_str}_technical.md")

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
