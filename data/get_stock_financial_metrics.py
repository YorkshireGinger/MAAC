import requests
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()

def get_stock_financial_metrics(
    tickers: list[str], 
    report_period_lte: str, 
    report_period_gte: str,
    period: str = 'ttm',
    limit: int = 1
    ):

    headers = {
        "X-API-KEY": os.getenv("FINANCIAL_DATASETS_API_KEY")
    }
    financial_metrics = []
    for i, ticker in enumerate(tickers):
        logger.debug(f"Fetching data for {ticker} ({i+1} / {len(tickers)})")
        url = (
            f'https://api.financialdatasets.ai/financial-metrics'
            f'?ticker={ticker}'
            f'&period={period}'
            f'&report_period_lte={report_period_lte}'
            f'&report_period_gte={report_period_gte}'
            f'&limit={limit}'
        )
        response = requests.get(url, headers=headers)
        ticker_financial_metrics = response.json().get('financial_metrics')
        financial_metrics.extend(ticker_financial_metrics)
        logger.debug(f"Retrieved {len(ticker_financial_metrics) if ticker_financial_metrics else 0} records for {ticker}")
    
    return financial_metrics
