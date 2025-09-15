"""News analysis indicator: fetch latest headlines and assess impact."""

from .base_indicator import BaseIndicator
import pandas as pd
import yfinance as yf
import re
from typing import List
import config

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore


class NewsIndicator(BaseIndicator):
    """Fetch and summarize recent news for a ticker, infer likely impact."""

    def calculate(self, stock_data: pd.DataFrame, params: dict | None = None) -> dict:
        p = params or {}
        ticker = p.get("ticker")
        n = int(p.get("top_n", 6))

        headlines: List[str] = []
        try:
            if ticker:
                t = yf.Ticker(ticker)
                items = (t.news or [])[:n]
                for it in items:
                    title = (it or {}).get("title")
                    if title:
                        headlines.append(str(title))
        except Exception:
            pass

        if not headlines:
            # No network/news available
            return {
                "indicator": "News",
                "signal": "Neutral",
                "details": "No recent news available or network restricted.",
            }

        # Prefer LLM-based impact summary if available
        if getattr(config, "OPENAI_API_KEY", None) and OpenAI is not None:
            try:
                client = OpenAI(api_key=config.OPENAI_API_KEY)
                prompt = (
                    "You are a financial news analyst. Given these recent headlines for the stock, "
                    "summarize the key themes in 3-5 bullet points, then assess the likely near-term impact on the stock as Positive, Negative, or Neutral and explain why.\n\n"
                    + "\n".join(f"- {h}" for h in headlines)
                )
                resp = client.chat.completions.create(
                    model="gpt-4-turbo",
                    messages=[
                        {"role": "system", "content": "You write concise, investor-friendly analyses."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                )
                text = resp.choices[0].message.content or ""
                # Simple extraction of signal keyword
                m = re.search(r"\b(Positive|Negative|Neutral)\b", text, flags=re.IGNORECASE)
                signal = m.group(1).capitalize() if m else "Neutral"
                return {
                    "indicator": "News",
                    "signal": signal,
                    "details": text.strip(),
                }
            except Exception:
                pass

        # Heuristic fallback sentiment from keywords
        text = " ".join(headlines).lower()
        pos_kw = ["beats", "upgrade", "record", "surge", "growth", "strong", "outperform"]
        neg_kw = ["miss", "downgrade", "probe", "lawsuit", "recall", "fall", "weak", "cut"]
        pos = sum(k in text for k in pos_kw)
        neg = sum(k in text for k in neg_kw)
        if pos > neg:
            signal = "Positive"
        elif neg > pos:
            signal = "Negative"
        else:
            signal = "Neutral"

        details = "Headlines:\n" + "\n".join(f"- {h}" for h in headlines)
        return {
            "indicator": "News",
            "signal": signal,
            "details": details,
        }

