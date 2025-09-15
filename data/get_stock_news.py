import requests
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def fetch_stock_news(tickers, start_date, end_date):
    
    headers = {
        "X-API-KEY": os.getenv("FINANCIAL_DATASETS_API_KEY")
    }
    news = {}
    for i, ticker in enumerate(tickers):
        logger.debug(f"Fetching data for {ticker} ({i+1} / {len(tickers)})")
        url = (
            f'https://api.financialdatasets.ai/news/'
            f'?ticker={ticker}'
            f'&start_date={start_date}'
            f'&end_date={end_date}'
        )
        response = requests.get(url, headers=headers)
        ticker_news = response.json().get('news')
        news[ticker] = ticker_news
        logger.debug(f"Retrieved {len(ticker_news)} records for {ticker}")
    return news
