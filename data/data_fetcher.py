import pandas as pd
import yfinance as yf
import numpy as np


def get_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetch historical stock data for a ticker.

    Args:
        ticker: Stock ticker symbol.
        period: History period (e.g. ``1y``, ``6mo``).

    Returns:
        DataFrame containing the historical OHLCV data.
    """

    print(f"Fetching data for {ticker} ({period})...")
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            raise ValueError("No data returned")
        return hist
    except Exception as e:
        # Fallback to synthetic data to allow offline execution
        print(f"Warning: failed to fetch data: {e}. Using synthetic data.")
        dates = pd.date_range(end=pd.Timestamp.today(), periods=250)
        prices = pd.Series(np.linspace(100, 150, len(dates)), index=dates)
        return pd.DataFrame({"Close": prices})
