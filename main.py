from agents.technical_analysis_orchestrator import TechnicalAnalysisOrchestrator
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run a technical analysis on a stock.")
    parser.add_argument("ticker", type=str, help="The stock ticker to analyze.")
    parser.add_argument(
        "--indicators",
        nargs="+",
        default=["RSI", "MACD", "Bollinger Bands", "Moving Average", "EMA"],
        help="A list of technical indicators to calculate.",
    )
    parser.add_argument(
        "--period",
        type=str,
        default="1y",
        help="History period to fetch (e.g. 6mo, 1y, 5y).",
    )
    args = parser.parse_args()

    # Initialize and run the orchestrator.
    orchestrator = TechnicalAnalysisOrchestrator()
    result = orchestrator.run(args.ticker, args.indicators, period=args.period)
    print(result)

if __name__ == '__main__':
    main()
