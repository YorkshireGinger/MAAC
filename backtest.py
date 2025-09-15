from data.get_stock_prices import get_stock_prices
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Backtest:
    """Backtest class for evaluating AI-driven stock recommendations 
    over a 3-month forward period.
    This class provides methods to:
    - Fetch and prepare historical stock price data for a given set 
    of tickers and an as-of date.
    - Calculate 3-month forward returns for each ticker and compare 
    the performance of AI-recommended "BUY" tickers versus all tickers.
    - Compute and compare the annualized Sharpe ratio of the "BUY" 
    portfolio and a benchmark portfolio over the 3-month period.
    - Plot cumulative returns for both the "BUY" and benchmark portfolios.
`    """

    def __init__(self, tickers, as_of_date, ai_recommendations):
        self.tickers = tickers
        self.as_of_date = as_of_date
        self.end_date_3m = (pd.to_datetime(self.as_of_date) + pd.DateOffset(months=3)).strftime("%Y-%m-%d")
        self.ai_recommendations = ai_recommendations
        self.prepare_backtest_data()


    def prepare_backtest_data(self):
        
        logger.debug("Fetching historical stock prices for backtest...")

        # Call the API to get daily prices
        daily_prices = get_stock_prices(
            tickers=self.tickers,
            interval='day',
            interval_multiplier=1,
            start_date=self.as_of_date,
            end_date=self.end_date_3m
        )
        # Convert to DataFrame
        prices_df = pd.DataFrame(daily_prices)
        # Convert 'time' column to datetime with YYYY-MM-DD format
        prices_df['time'] = pd.to_datetime(prices_df['time'])
        # Sort for correct calculation
        self.prices_df = prices_df.sort_values(['ticker', 'time'])
        
        # make ai recommendations dataframe
        self.ai_recommendations_df = pd.DataFrame(self.ai_recommendations.items(), columns=['ticker', 'recommendation'])

        logger.debug("Backtest data preparation complete.")

    def run_3m_fwd_returns(self):
        
        logger.debug("Calculating 3-month forward returns...")

        # copy prices_df to avoid modifying original
        prices_df = self.prices_df.copy()

        # Ensure prices_df is sorted by ticker and time
        prices_df = prices_df.sort_values(['ticker', 'time'])

        # Calculate 3-month forward return per ticker 
        three_month_df = (
            prices_df.groupby('ticker')
            .agg(first_close=('close', 'first'), last_close=('close', 'last'))
            .reset_index()
        )
        three_month_df['3m_forward_return'] = (
            three_month_df['last_close'] / three_month_df['first_close'] - 1
        )

        # Joinw with AI recommendations so can create BUY vs All comparison
        three_month_ai_rec_df = three_month_df.merge(
            self.ai_recommendations_df, 
            on='ticker', 
            how='inner'
        )

        # find equal weighted returns for BUYs vs all tickers
        buy_returns = (
            three_month_ai_rec_df[three_month_ai_rec_df['recommendation'] == 'BUY']
            ['3m_forward_return']
            .mean()
        )
        all_returns = three_month_ai_rec_df['3m_forward_return'].mean()

        logger.debug("3-month forward returns calculation complete.")

        return buy_returns, all_returns



    def sharpe_ratio_3m(
        self, 
        daily_returns: pd.Series, 
        risk_free_rate_annual: float = 0.05
    ) -> float:
        """Calculate the annualized Sharpe ratio for the next 3 months of daily returns."""
        
        # Ensure sorted by date
        daily_returns = daily_returns.sort_index()

        # Convert annual risk-free rate to daily
        trading_days = 252
        rf_daily = (1 + risk_free_rate_annual) ** (1 / trading_days) - 1

        # Excess daily returns
        excess_daily = daily_returns - rf_daily

        # Daily Sharpe
        sharpe_daily = excess_daily.mean() / excess_daily.std(ddof=1)

        # Annualize
        sharpe_annualized = sharpe_daily * np.sqrt(trading_days)

        return sharpe_annualized

    def run_3m_sharpe_ratio(self):
        
        # copy prices_df to avoid modifying original
        prices_df = self.prices_df.copy()

        # Ensure prices_df is sorted by ticker and time
        prices_df = prices_df.sort_values(['ticker', 'time'])
        
        # Calculate daily returns per ticker
        prices_df['daily_return'] = prices_df.groupby('ticker')['close'].pct_change()

        # Merge with AI recommendations to filter for BUYs
        prices_recommendations_df = prices_df.merge(self.ai_recommendations_df, on='ticker', how='inner')
        buy_prices_df = prices_recommendations_df[prices_recommendations_df['recommendation'] == 'BUY']

        # Equal weight daily returns across tickers for BUYs portfolio and benchmark portfolio
        buy_daily_returns = buy_prices_df.groupby(['time'])['daily_return'].mean().reset_index()
        benchmark_daily_returns = prices_recommendations_df.groupby(['time'])['daily_return'].mean().reset_index()

        # Replace first row daily_return NaN with 0 as starting point 
        buy_daily_returns.loc[0, 'daily_return'] = 0
        benchmark_daily_returns.loc[0, 'daily_return'] = 0

        # compute sharpe ratios
        buy_sharpe_ratio = self.sharpe_ratio_3m(
            daily_returns=buy_daily_returns.set_index('time')['daily_return'],
            risk_free_rate_annual=0.05 # assuming 5% annual risk-free rate, 
        )

        benchmark_sharpe_ratio = self.sharpe_ratio_3m(
            daily_returns=benchmark_daily_returns.set_index('time')['daily_return'],
            risk_free_rate_annual=0.05 # assuming 5% annual risk-free rate
        )

        # save down for plotting later
        self.buy_daily_returns = buy_daily_returns
        self.benchmark_daily_returns = benchmark_daily_returns

        return buy_sharpe_ratio, benchmark_sharpe_ratio

    def plot_cumulative_returns_3m(
        self,
        buy_daily_returns: pd.Series, 
        benchmark_daily_returns: pd.Series, 
        title: str = "Cumulative 3M Return: BUY Portfolio vs Benchmark"
    ) -> None:
        """
        Plot the cumulative return over the last 3 months for both BUY
        portfolio and benchmark as a PNG chart.
        """
        buy_daily_returns = buy_daily_returns.sort_index()
        benchmark_daily_returns = benchmark_daily_returns.sort_index()

        buy_cumulative = (buy_daily_returns + 1).cumprod() - 1
        benchmark_cumulative = (benchmark_daily_returns + 1).cumprod() - 1

        plt.figure(figsize=(10, 5))
        plt.plot(buy_cumulative.index, buy_cumulative.values * 100, label='BUY Portfolio')
        plt.plot(benchmark_cumulative.index, benchmark_cumulative.values * 100, label='Benchmark Portfolio')
        plt.title(title)
        plt.xlabel("Date")
        plt.ylabel("Cumulative Return (%)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("outputs/cumulative_3m_return_comparison.png")
        plt.close()

    def run_plot_cumulative_returns_3m(self):
        # Plot cumulative 3m return for BUY portfolio and benchmark
        self.plot_cumulative_returns_3m(
            buy_daily_returns=self.buy_daily_returns.set_index('time')['daily_return'],
            benchmark_daily_returns=self.benchmark_daily_returns.set_index('time')['daily_return'],
            title="Cumulative 3M Return - BUY Portfolio vs Benchmark"
        )
