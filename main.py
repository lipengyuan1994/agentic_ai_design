
from agents.technical_analysis_orchestrator import TechnicalAnalysisOrchestrator
import argparse


def main():
    parser = argparse.ArgumentParser(description='Run a technical analysis on a stock.')
    parser.add_argument('ticker', type=str, help='The stock ticker to analyze.')
    parser.add_argument('--indicators', nargs='+', default=["RSI", "MACD", "Bollinger Bands", "Moving Average"], help='A list of technical indicators to calculate.')











    args = parser.parse_args()

    # Initialize and run the orchestrator.
    orchestrator = TechnicalAnalysisOrchestrator()
    result = orchestrator.run(args.ticker, args.indicators)
    print(result)

if __name__ == '__main__':
    main()