from agents.technical_analysis_orchestrator import TechnicalAnalysisOrchestrator
from agents.value_analysis_orchestrator import ValueAnalysisOrchestrator
from agents.news_orchestrator import NewsOrchestrator
import argparse
import os
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(description='Run a stock analysis (technical, value, news, or any combination).')
    parser.add_argument('ticker', type=str, help='The stock ticker to analyze.')
    parser.add_argument('--indicators', nargs='+', default=["RSI", "MACD", "Bollinger Bands", "Moving Average"], help='A list of technical indicators to calculate.')
    parser.add_argument('--analysis', choices=['technical', 'value', 'both'], default='both', help='Type of analysis to run.')
    parser.add_argument('--news', action='store_true', help='Fetch and store recent news headlines to a report file.')

    args = parser.parse_args()

    outputs = []
    if args.analysis in ('technical', 'both'):
        orchestrator = TechnicalAnalysisOrchestrator()
        outputs.append(orchestrator.run(args.ticker, args.indicators))

    if args.analysis in ('value', 'both'):
        v_orchestrator = ValueAnalysisOrchestrator()
        outputs.append(v_orchestrator.run(args.ticker))

    if args.news:
        n_orchestrator = NewsOrchestrator()
        outputs.append(n_orchestrator.run(args.ticker))

    final_path = _combine_reports_for_today(args.ticker)
    if final_path:
        outputs.append(final_path)

    for path in outputs:
        print(path)


def _combine_reports_for_today(ticker: str) -> str | None:
    reports_dir = 'reports'
    if not os.path.exists(reports_dir):
        return None

    today_compact = datetime.now().strftime('%Y%m%d')

    parts = []
    tech_path = os.path.join(reports_dir, f"{ticker}_{today_compact}_technical.md")
    if os.path.exists(tech_path):
        parts.append(("Technical Analysis", tech_path))
    val_path = os.path.join(reports_dir, f"{ticker}_{today_compact}_value.md")
    if os.path.exists(val_path):
        parts.append(("Value Analysis", val_path))
    news_path = os.path.join(reports_dir, f"{ticker}_news_{today_compact}.md")
    if os.path.exists(news_path):
        parts.append(("News", news_path))

    if not parts:
        return None

    final_path = os.path.join(reports_dir, f"{ticker}_{today_compact}_final.md")
    lines = [f"### Final Combined Report: {ticker}", ""]
    for title, p in parts:
        try:
            with open(p, 'r') as f:
                content = f.read().strip()
        except Exception:
            content = f"(Could not read {p})"
        lines.append(f"## {title}")
        lines.append("")
        lines.append(content)
        lines.append("")

    with open(final_path, 'w') as f:
        f.write("\n".join(lines).strip() + "\n")

    return final_path


if __name__ == '__main__':
    main()
