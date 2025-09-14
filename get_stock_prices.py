import requests
from dotenv import load_dotenv
import os
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_stock_prices(
    tickers,
    interval='day',
    interval_multiplier=5,
    start_date='2025-01-02',
    end_date='2025-01-20'
):
    """
    Fetch stock prices for a list of tickers from financialdatasets.ai API.

    Args:
        tickers (list): List of ticker symbols.
        interval (str): Interval type ('minute', 'day', 'week', 'month', 'year').
        interval_multiplier (int): Interval multiplier.
        start_date (str): Start date in 'YYYY-MM-DD' format.
        end_date (str): End date in 'YYYY-MM-DD' format.

    Returns:
        dict: Dictionary mapping tickers to their price data.
    """

    headers = {
        "X-API-KEY": os.getenv("FINANCIAL_DATASETS_API_KEY")
    }
    prices = []

    for i, ticker in enumerate(tickers):
        logger.debug(f"Fetching data for {ticker} ({i+1} / {len(tickers)})")
        url = (
            f'https://api.financialdatasets.ai/prices/'
            f'?ticker={ticker}'
            f'&interval={interval}'
            f'&interval_multiplier={interval_multiplier}'
            f'&start_date={start_date}'
            f'&end_date={end_date}'
        )
        response = requests.get(url, headers=headers)
        ticker_prices = response.json().get('prices')
        prices.extend(ticker_prices)
        logger.debug(f"Retrieved {len(ticker_prices)} records for {ticker}")
    return prices