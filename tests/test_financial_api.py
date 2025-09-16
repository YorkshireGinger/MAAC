import unittest
from datetime import date, timedelta
import os

# Import functions from your repo
from data.get_stock_prices import get_stock_prices
from data.get_stock_news import fetch_stock_news
from data.get_stock_financial_metrics import get_stock_financial_metrics

class TestFinancialAPI(unittest.TestCase):
    def setUp(self):
        # Use a ticker that should always work
        self.tickers = ['AAPL']
        self.data_start_date = (date.today() - timedelta(days=100+120)).strftime('%Y-%m-%d')
        self.as_of_date = (date.today() - timedelta(days=100)).strftime('%Y-%m-%d')

    def test_get_stock_prices(self):
        prices = get_stock_prices(
            tickers=self.tickers,
            interval='day',
            interval_multiplier=1,
            start_date=self.data_start_date,
            end_date=self.as_of_date
        )
        self.assertIsInstance(prices, list)
        self.assertGreater(len(prices), 0, "No price data returned from API.")

    def test_fetch_stock_news(self):
        news = fetch_stock_news(
            tickers=self.tickers,
            start_date=self.data_start_date,
            end_date=self.as_of_date
        )
        self.assertIsInstance(news, dict)
        self.assertIn('AAPL', news)
        self.assertIsInstance(news['AAPL'], list)

    def test_get_stock_financial_metrics(self):
        metrics = get_stock_financial_metrics(
            tickers=self.tickers,
            report_period_lte=self.as_of_date,
            report_period_gte=self.data_start_date,
            period='ttm',
            limit=1
        )
        self.assertIsInstance(metrics, list)
        self.assertGreater(len(metrics), 0, "No financial metrics returned from API.")


if __name__ == '__main__':
    unittest.main()
