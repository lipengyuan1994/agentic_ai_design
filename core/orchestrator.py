
from openai import OpenAI
import json
import data.data_fetcher as data_fetcher
import core.worker as worker
import config

client = OpenAI(api_key=config.OPENAI_API_KEY)

def run(ticker: str) -> str:
    """Runs the technical analysis orchestrator for a given stock ticker.

    Args:
        ticker: The stock ticker to analyze.

    Returns:
        A summary of the technical analysis.
    """
    # 1. Fetch stock data
    stock_data = data_fetcher.get_stock_data(ticker)

    # 2. Define the technical indicators to calculate
    indicators = ["RSI", "MACD", "Bollinger Bands", "Moving Average"]

    # 3. Create and run worker agents for each indicator
    worker_results = []
    for indicator in indicators:
        result = worker.run(indicator, stock_data.to_json())
        worker_results.append(result)

    # 4. Summarize the results
    summary = summarize(worker_results)

    return summary

def summarize(results: list) -> str:
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
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a financial analyst specializing in technical analysis."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content
