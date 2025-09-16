import unittest
import numpy as np
import pandas as pd
from datetime import date, timedelta

from backtest import Backtest

class TestSharpeRatio(unittest.TestCase):
    def test_sharpe_ratio_3m(self):
        # Simulate daily returns for 100 days
        np.random.seed(42)
        daily_returns = pd.Series(np.random.normal(0.001, 0.02, 100))
        # Use a known risk-free rate
        risk_free_rate_annual = 0.05

        # Create a dummy Backtest instance (minimal required args)
        bt = Backtest(
            tickers=['AAPL', 'MSFT', 'NVDA', 'TSLA'], 
            as_of_date="2025-06-08", 
            ai_recommendations={
                'AAPL': 'BUY', 
                'MSFT': 'BUY', 
                'NVDA': 'HOLD', 
                'TSLA': 'SELL'
            }
        )

        # Test the sharpe_ratio_3m method
        sharpe = bt.sharpe_ratio_3m(daily_returns, risk_free_rate_annual)

        # Sharpe ratio should be a float and not NaN
        self.assertIsInstance(sharpe, float)
        self.assertFalse(np.isnan(sharpe))

        # Check that the Sharpe ratio value is correct
        self.assertEqual(sharpe, -1.1104508622124218)

if __name__ == '__main__':
    unittest.main()
