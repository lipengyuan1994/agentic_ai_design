import pandas as pd
import yfinance as yf
import os

def get_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """Fetches historical stock data for the given ticker, using a local cache if available.

    Args:
        ticker: The stock ticker symbol.
        period: The time period for the data (e.g., "1y", "6mo").

    Returns:
        A pandas DataFrame with the historical stock data.
    """
    cache_dir = "data_hist"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    file_path = os.path.join(cache_dir, f"{ticker}_{period}.csv")

    if os.path.exists(file_path):
        print(f"Loading data for {ticker} from cache...")
        return pd.read_csv(file_path, index_col=0, parse_dates=True)
    else:
        print(f"Fetching data for {ticker} from yfinance...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        hist.to_csv(file_path)
        return hist
