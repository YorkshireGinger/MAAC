
import argparse
from datetime import date
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(as_of_date):
    """Entry point for running the Multi-Agent Alpha Copilot (MAAC) and Backtest."""
    
    # SET PARAMETERS
    tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA']
    today_date = date.today().strftime("%Y-%m-%d")

    # RUN TESTS

    # RUN GRAPH
    from graph import MAAC

    # Initiate the Multi-Agent AI
    logger.info("***Welcome to the PoC Multi-Agent AI called MAAC!"
            " (Multi-Agent Alpha Copilot)***")
    maac = MAAC()

    # Invoke the Multi-Agent AI
    logger.info("Starting the Multi-Agent AI ...")
    run = maac.the_graph.invoke(
        {
            "tickers": tickers, 
            "as_of_date": as_of_date,
            "today_date": today_date
        }
    )

    # Show final recommendations
    maac_recommendations = {}
    graph_output = run["coordinator_output"]
    for ticker, rec, just in zip(
        graph_output.tickers, 
        graph_output.recommendation, 
        graph_output.justification
    ):
        logger.info(f"\nTicker: {ticker}\nRecommendation: {rec}\nJustification: {just}\n{'-'*40}")
        maac_recommendations[ticker] = rec

    # RUN BACKTEST
    from backtest import Backtest

    # Initiate the Backtest
    logger.info("Starting the Backtest ...")
    backtest = Backtest(
        tickers=tickers, 
        as_of_date=as_of_date, 
        ai_recommendations=maac_recommendations
    )

    # Run the 3 month forward returns
    backtest_results = backtest.run_3m_fwd_returns()
    logger.info(f"3-Month Forward Returns - MAAC BUYs: {backtest_results[0]:.2%}, "
                f"All Tickers: {backtest_results[1]:.2%}")

    # Run the 3 month sharpe ratio
    buy_sharpe_ratio, benchmark_sharpe_ratio = backtest.run_3m_sharpe_ratio()
    logger.info(f"3-Month Sharpe Ratio - MAAC BUYs: {buy_sharpe_ratio:.2f}, "
                f"All Tickers: {benchmark_sharpe_ratio:.2f}")

    # Plot the cumulative returns
    backtest.run_plot_cumulative_returns_3m()
    logger.info("Cumulative Returns plot saved to 'cumulative_returns_3m.png'")

    logger.info("***Multi-Agent AI & Backtest Completed!***")

if __name__ == "__main__":
    """Entry point for running the Multi-Agent Alpha Copilot (MAAC) and Backtest."""

    # Set up argument parser for command line execution
    parser = argparse.ArgumentParser(description="Run MAAC with a specific as_of_date.")
    parser.add_argument(
        "--as_of_date", 
        type=str, 
        default="2025-01-02", 
        help="Date in YYYY-MM-DD format (default: 2025-01-02)"
    )
    args = parser.parse_args()

    # Call the main function with the parsed arguments
    main(args.as_of_date)

