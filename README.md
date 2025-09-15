# Agentic AI Design – Stock Analysis Orchestrator

A small, agent-style Python project that fetches historical stock data, computes a set of technical indicators with worker agents, and produces a human-readable summary report. It also includes a value analysis worker that evaluates fundamentals and valuation. Summaries are generated via OpenAI if available, with a clear local fallback when it isn’t.

## What It Does
- Fetches historical price data for a ticker (via `yfinance`) and caches it in `data_hist/`.
- Spawns worker agents to compute indicators concurrently.
- Summarizes results using OpenAI (GPT-4 Turbo) when configured, or a simple local fallback summary otherwise.
- Uses Pydantic models for structured outputs.
- Uses an optional LLM-based orchestrator to plan which indicators to run and why (falls back to a deterministic plan when OpenAI is unavailable).
- Supports value analysis via a dedicated worker and orchestrator.
- Fetches recent news headlines and stores them in a Markdown report; also creates a final combined report.

## Repository Structure
- `main.py` – CLI entry point.
- `agents/` – Orchestrators and workers (technical indicators, value analysis).
- `core/` – Minimal abstract base classes for orchestrator/worker.
- `data/` – Project data (not required for running; cache lives in `data_hist/`).
- `data_hist/` – CSV cache for historical data (auto-created).
- `indicators/` – Indicator implementations (sample, placeholder logic).
- `reports/` – Output reports (auto-created).

## Requirements
- Python 3.10+
- Packages (install with `pip install -r requirements.txt`):
  - `pandas`, `yfinance`, `openai`, `pydantic`
- Network access to fetch data from Yahoo Finance on the first run for a given ticker/period. Subsequent runs can use cached CSVs from `data_hist/`.
- Optional: OpenAI API key for LLM summarization.

## OpenAI Usage
- Environment variable: `OPENAI_API_KEY`
- Model: `gpt-4-turbo`
- Behavior: If the key is missing or any API call fails, the orchestrator falls back to a local, deterministic summary assembled from indicator outputs.
  - The orchestrator also attempts an LLM planning step to choose/sequence indicators with rationale; this planning step similarly falls back to a deterministic plan.

## Quick Start
1) Create and activate a virtual environment (recommended)
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

2) Install dependencies
```
pip install -r requirements.txt
```

3) (Optional) Configure OpenAI
```
export OPENAI_API_KEY=your_api_key_here  # Windows PowerShell: $Env:OPENAI_API_KEY="your_api_key_here"
```

4) Run (defaults to both technical and value)
```
python main.py AAPL
```
- Default indicators: `RSI`, `MACD`, `Bollinger Bands`, `Moving Average`
- You can provide a custom subset:
```
python main.py AAPL --indicators RSI MACD
```

Value-only analysis:
```
python main.py AAPL --analysis value
```

Run only one type if desired:
```
python main.py AAPL --analysis technical
python main.py AAPL --analysis value
```

Include recent news headlines (works with any mode):
```
python main.py AAPL --news
```

5) Output
- Technical: `reports/<TICKER>_<YYYYMMDD>_technical.md`
- Value: `reports/<TICKER>_<YYYYMMDD>_value.md`
- News: `reports/<TICKER>_news_<YYYYMMDD>.md`
- Final combined: `reports/<TICKER>_<YYYYMMDD>_final.md`

## Data Fetching & Caching
- Price data is fetched with `yfinance` and cached to `data_hist/<TICKER>_<period>.csv`.
- On subsequent runs, the cache is used when present. If network is unavailable, ensure the cache exists for your ticker.

## Indicators
Included sample indicators (with placeholder logic meant for demonstration):
- `RSI` → `indicators/rsi.py` → class `RSIIndicator`
- `MACD` → `indicators/macd.py` → class `MACDIndicator`
- `Bollinger Bands` → `indicators/bollinger_bands.py` → class `BollingerBandsIndicator`
- `Moving Average` → `indicators/moving_average.py` → class `MovingAverageIndicator`

Extend or replace the placeholder logic with real calculations (e.g., using `pandas-ta`). Each indicator should implement `calculate(self, stock_data: pd.DataFrame) -> dict` and return a dict like:
```
{
  "indicator": "RSI",
  "signal": "Oversold",
  "details": "RSI is currently at 28."
}
```

## How It Works (High Level)
- `TechnicalAnalysisOrchestrator.run(ticker, indicators)`
  - Fetches a `pandas.DataFrame` via `data/data_fetcher.py`.
  - Submits work to `IndicatorWorker` in a thread pool; each worker calculates one indicator.
  - Workers return `IndicatorResult` Pydantic models; orchestrator builds an `AnalysisReport` Pydantic model.
  - Summarizes results via OpenAI (if configured) or local fallback.
  - Writes a Markdown report to `reports/`.

## Structured Output (Pydantic)
- Workers return `IndicatorResult` (indicator, signal, details, optional meta).
- Orchestrator aggregates into `AnalysisReport` with `SummaryResult`.
- Final output is Markdown; structured models are used internally (you can serialize them yourself if needed).

## Troubleshooting
- OpenAI not configured: You’ll still get a valid local summary with a note about the fallback.
- No internet: Ensure a cached CSV exists in `data_hist/` for your ticker/period.
- Intel MKL warning: You may see a CPU capability warning from MKL; it’s informational and does not block execution.
- Pandas/JSON serialization errors: The system passes `DataFrame` objects to workers directly (no JSON round‑trip) to avoid such issues.

## Development Notes
- Add new indicators to `indicators/` and export a class named like `<Name>Indicator` (e.g., `RSIIndicator`).
- Indicators are loaded dynamically from their module names derived from the indicator label (e.g., "Bollinger Bands" → `indicators/bollinger_bands.py` → `BollingerBandsIndicator`).
- Reports are plain Markdown; feel free to enhance formatting or include charts.

## Example
```
# Default indicator set
python main.py MSFT

# Custom indicators
python main.py TSLA --indicators "Bollinger Bands" RSI
```

The resulting report appears in `reports/` with the ticker and current date.

## Value Analysis
- Worker: `agents/value_analysis_worker.py` → class `ValueAnalysisWorker`
- Orchestrator: `agents/value_analysis_orchestrator.py` → class `ValueAnalysisOrchestrator`
- Uses yfinance fundamentals (e.g., P/E, P/B, margins, ROE, revenue growth, FCF yield, leverage) to compute a heuristic score and signal:
  - Signals: Undervalued/Quality, Reasonable, Mixed/Neutral, Overvalued/Risky
- Report path: `reports/<TICKER>_<YYYYMMDD>_value.md`
  - If OpenAI is configured, a concise Markdown summary is generated; otherwise a local fallback is used.
