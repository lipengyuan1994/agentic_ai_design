import pandas as pd
import yfinance as yf

def get_stock_data(ticker: str) -> pd.DataFrame:
    """Fetches historical stock data for the given ticker.

    Args:
        ticker: The stock ticker symbol.

    Returns:
        A pandas DataFrame with the historical stock data.
    """
    print(f"Fetching data for {ticker}...")
    stock = yf.Ticker(ticker)
    # Get historical market data
    hist = stock.history(period="1y")
    return hist
