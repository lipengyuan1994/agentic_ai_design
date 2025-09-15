from __future__ import annotations

from core.orchestrator import Orchestrator
from datetime import datetime, timezone
import os
import yfinance as yf


class NewsOrchestrator(Orchestrator):
    """Fetches recent headlines for a ticker and writes them to Markdown."""

    def run(self, ticker: str, days: int = 7, limit: int = 50) -> str:
        news_items = self._fetch_news(ticker)

        # Filter by days and cap by limit
        cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
        filtered = [n for n in news_items if _pub_ts(n) and _pub_ts(n) >= cutoff]
        if limit:
            filtered = filtered[:limit]

        path = self._save_news_markdown(ticker, filtered)
        return path

    def _fetch_news(self, ticker: str):
        try:
            return yf.Ticker(ticker).news or []
        except Exception:
            return []

    def _save_news_markdown(self, ticker: str, items: list[dict]) -> str:
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)

        date_compact = datetime.now().strftime("%Y%m%d")
        md_path = os.path.join(reports_dir, f"{ticker}_news_{date_compact}.md")

        # Header
        lines: list[str] = []
        lines.append(f"### News Headlines: {ticker}\n")
        if not items:
            lines.append("No recent news found.\n")
        else:
            for n in items:
                title = n.get("title") or "Untitled"
                link = n.get("link") or ""
                publisher = n.get("publisher") or n.get("source") or ""
                ts = _pub_ts(n)
                when = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else ""
                lines.append(f"- {when} – {publisher}: [{title}]({link})")

        with open(md_path, "w") as f:
            f.write("\n".join(lines) + "\n")

        return md_path


def _pub_ts(n: dict | None):
    if not n:
        return None
    # yfinance typically provides providerPublishTime (seconds epoch)
    ts = n.get("providerPublishTime") or n.get("published_at") or n.get("time_published")
    try:
        if isinstance(ts, (int, float)):
            return float(ts)
        # some feeds use string epoch
        if isinstance(ts, str) and ts.isdigit():
            return float(ts)
    except Exception:
        return None
    return None

