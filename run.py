
import argparse
from datetime import date, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(as_of_date):
    """Entry point for running the Multi-Agent Alpha Copilot (MAAC) and Backtest."""
    
    # SET PARAMETERS
    tickers = ['AAPL', 'MSFT', 'NVDA', 'TSLA']
    # End data is ~4 months before as_of_date to allow for atleast one earnings report (US)
    # to be used for fundamnetal metrics in fundamental agent
    data_start_date = (date.fromisoformat(as_of_date) - timedelta(days=120)).strftime("%Y-%m-%d")

    # RUN GRAPH
    from graph import MAAC

    # Initiate the Multi-Agent AI
    logger.info("***Welcome to the PoC Multi-Agent AI called MAAC!"
            " (Multi-Agent Alpha Copilot)***")
    logger.info("Starting the Multi-Agent AI ...")
    maac = MAAC()

    # Invoke the Multi-Agent AI
    run = maac.the_graph.invoke(
        {
            "tickers": tickers, 
            "as_of_date": as_of_date,
            "data_start_date": data_start_date
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
    # Set up argument parser for command line execution
    parser = argparse.ArgumentParser(description="Run MAAC with a specific as_of_date.")
    parser.add_argument(
        "--as_of_date", 
        type=str, 
        default="2025-01-02", 
        help="Date in YYYY-MM-DD format (default: 2025-01-02)"
    )
    args = parser.parse_args()

    # Check if as_of_date is in expected format
    try:
        as_of_date_obj = date.fromisoformat(args.as_of_date)
    except ValueError:
        logger.error(f"Invalid date format for as_of_date: {args.as_of_date}. "
                     f"Use YYYY-MM-DD.")
        exit(1)

    # Check if as_of_date is more than 100 days before today so the backtest can run
    latest_date = date.today() - timedelta(days=100)
    if as_of_date_obj > latest_date:
        logger.error(f"as_of_date must be more than 100 days before today "
                     f"(any date before {latest_date.strftime('%Y-%m-%d')}). "
                     f"You provided: {args.as_of_date}")
        exit(1)

    # Call the main function with the validated argument
    main(args.as_of_date)

