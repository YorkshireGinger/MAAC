import requests
from dotenv import load_dotenv
import os
import json
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
) -> list[dict]:

    headers = {
        "X-API-KEY": os.getenv("FINANCIAL_DATASETS_API_KEY")
    }
    
    try:
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

        # Save to JSON file
        with open(f"data/{report_period_gte}-{report_period_lte}_financial_metrics_data.json", "w") as f:
            json.dump(financial_metrics, f)

    except Exception as e:
        logger.debug(f"Error fetching financial metrics: {e}. Loading from local JSON file.")
        # Load from JSON file
        with open(f"data/{report_period_gte}-{report_period_lte}_financial_metrics_data.json", "r") as f:
            financial_metrics = json.load(f)

    return financial_metrics
