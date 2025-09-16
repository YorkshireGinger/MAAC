import pandas as pd
from data.get_stock_prices import get_stock_prices
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Valuation/Momentum Agent Tools
def calculate_rsi(prices, period=14) -> pd.Series:

    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def run_valuation_agent_tool(
    tickers,
    start_date,
    end_date,
    interval='day',
    interval_multiplier=1,
    rsi_period=14
) -> str:
    logger.info(f"Starting Valuation/Momentum Tool ...")

    # Get daily prices from API
    daily_prices = get_stock_prices(
        tickers=tickers,
        interval=interval,
        interval_multiplier=interval_multiplier,
        start_date=start_date,
        end_date=end_date
    )

    # Convert to DataFrame
    daily_prices_df = pd.DataFrame(daily_prices)

    # Calculate RSI for each ticker
    working_rsi_df = daily_prices_df.groupby('ticker')['close'].apply(
        lambda x: calculate_rsi(x, rsi_period)
    )

    # Reformat DataFrame
    working_rsi_df = working_rsi_df.reset_index().rename(
        columns={'close': f'rsi_{rsi_period}'}
    ).drop(columns=['level_1'])

    # Merge rolling RSI with date column to create a series
    rsi_df = working_rsi_df.merge(
        daily_prices_df[['time']],
        how='left',
        left_index=True,
        right_index=True
    )

    # Convert to JSON string for better LLM ingestion
    rsi_json = rsi_df.to_json(orient='records', date_format='iso')

    logger.info("Valuation/Momentum Tool Completed!")

    return rsi_json


# News/Sentiment Agent Tool
import json
from data.sentiment_stock_news import analyze_headline_sentiment
import numpy as np

def run_news_sentiment_agent_tool(
    run_news_pipeline=False, 
    news_file='data/stock_news.json', 
    output_file='data/ticker_news_sentiment_scores.json'
) -> tuple[dict, dict]:
    
    logger.info("Starting News/Sentiment Tool ...")

    # With more time we could automate the news fetching 
    if run_news_pipeline:
        logger.debug("Running news pipeline...")
        # TODO use the news fetching and sentiment analysis code here
    # But for now I am using pre-written news data
    else:
        logger.debug("Collecting pre-written news...")

        # Load pre-written news data
        with open(news_file, 'r') as f:
            stock_news = json.load(f)
            logger.debug(f"Loaded news for {len(stock_news)} tickers.")
        
        # Analyze sentiment for each headline and snippet using VADER
        sentiment_scores = {}
        for ticker, news_items in stock_news.items():
            sentiment_scores[ticker] = []
            for item in news_items:
                headline = item.get('headline', '')
                snippet = item.get('snippet', '')
                headline_score = analyze_headline_sentiment(headline)
                snippet_score = analyze_headline_sentiment(snippet)
                sentiment_scores[ticker].append({
                    'headline': headline,
                    'snippet': snippet,
                    'headline_score': headline_score,
                    'snippet_score': snippet_score
                })

        # Save sentiment scores for each headline & to output file
        with open(output_file, 'w') as f:
            json.dump(sentiment_scores, f, indent=2)
            logger.debug(f"Sentiment scores saved to {output_file}.")

        # Calculate average and median sentiment scores for each ticker
        # TODO could add a weighted average that weights most recent articles 
        # more or that weights extreme sentiment more as these are the stories 
        # that may move price
        summary_scores = {}
        for ticker, items in sentiment_scores.items():
            # Get all scores
            snippet_scores = [
                item['snippet_score']['compound']
                for item in items
                if 'compound' in item['snippet_score']
            ]
            # Calculate average and median
            if snippet_scores:
                avg = float(np.mean(snippet_scores))
                median = float(np.median(snippet_scores))
            else:
                avg = None
                median = None
            # Using VADER thresholds assign overall sentiment score
            summary_scores[ticker] = {
                'average_snippet_sentiment_value': avg,
                'average_snippet_sentiment': (
                    'negative' if avg is not None and avg < -0.05 else
                    'positive' if avg is not None and avg > 0.05 else
                    'neutral'
                ),
                'median_snippet_sentiment_value': median,
                'median_snippet_sentiment': (
                    'negative' if median is not None and median < -0.05 else
                    'positive' if median is not None and median > 0.05 else
                    'neutral'
                )
            }

        logger.info("News/Sentiment Tool Completed!")

        return sentiment_scores, summary_scores


# Fundamental/Analyst Agent Tool
from data.get_stock_financial_metrics import get_stock_financial_metrics
import pandas as pd

def run_fundamental_agent_tool(
    tickers,
    report_period_lte,
    report_period_gte,
    period='ttm',
    limit=1
) -> str:
    
    # TODO Calc a metric to how good/bad each metric is relative to its peers 
    # or to its own history - this could a percentile or z-score - as absolute
    # values aren't as useful as relative ones

    logger.info("Starting Fundamental/Analyst Tool ...")

    # Get financial metrics from API
    stock_financial_metrics = get_stock_financial_metrics(
        tickers=tickers,
        report_period_lte=report_period_lte,
        report_period_gte=report_period_gte,
        period=period,
        limit=limit
    )

    # Convert to DataFrame
    financial_metrics_df = pd.DataFrame(stock_financial_metrics)

    # Select the Quality Metrics we want to use
    financial_metrics_df_cut = (
        financial_metrics_df
        .loc[:,['ticker', 'fiscal_period', 'period',
        'price_to_earnings_ratio', 'free_cash_flow_growth',
        'return_on_invested_capital', 'debt_to_equity',
        'earnings_per_share', 'free_cash_flow_per_share',
        'interest_coverage']]
        .copy()
    )

    # Calculate an extra metric earnings to free cash flow ratio
    financial_metrics_df_cut['earnings_to_fcf'] = (
        financial_metrics_df_cut['earnings_per_share'] /
        financial_metrics_df_cut['free_cash_flow_per_share']
    )

    # Define scorecard thresholds for each metric
    def score_pe(pe):
        if pd.isna(pe):
            return 0
        if pe < 30:
            return 2
        elif pe < 50:
            return 1
        else:
            return 0

    def score_fcf_growth(fcf_growth):
        if pd.isna(fcf_growth):
            return 0
        if fcf_growth > 0.25:
            return 2
        elif fcf_growth > 0.1:
            return 1
        else:
            return 0

    def score_roic(roic):
        if pd.isna(roic):
            return 0
        if roic > 0.25:
            return 2
        elif roic > 0.1:
            return 1
        else:
            return 0

    def score_debt_to_equity(dte):
        if pd.isna(dte):
            return 0
        if dte < 0.5:
            return 2
        elif dte < 1:
            return 1
        else:
            return 0

    def score_interest_coverage(ic):
        if pd.isna(ic):
            return 2
        if ic > 10:
            return 2
        elif ic > 4:
            return 1
        else:
            return 0
        
    def score_earnings_to_fcf(e_fcf):
        if pd.isna(e_fcf):
            return 0
        if 0.9 <= e_fcf <= 1.1:
            return 2
        elif (0.7 <= e_fcf < 0.9) or (1.1 < e_fcf <= 1.3):
            return 1
        else:
            return 0

    # Apply scoring functions to each row
    financial_metrics_df_cut['pe_score'] = financial_metrics_df_cut['price_to_earnings_ratio'].apply(score_pe)
    financial_metrics_df_cut['fcf_growth_score'] = financial_metrics_df_cut['free_cash_flow_growth'].apply(score_fcf_growth)
    financial_metrics_df_cut['earnings_to_fcf_score'] = financial_metrics_df_cut['earnings_to_fcf'].apply(score_earnings_to_fcf)
    financial_metrics_df_cut['roic_score'] = financial_metrics_df_cut['return_on_invested_capital'].apply(score_roic)
    financial_metrics_df_cut['debt_to_equity_score'] = financial_metrics_df_cut['debt_to_equity'].apply(score_debt_to_equity)
    financial_metrics_df_cut['interest_coverage_score'] = financial_metrics_df_cut['interest_coverage'].apply(score_interest_coverage)

    # Sum up the scores for a total score per ticker
    financial_metrics_df_cut['fundamental_score'] = (
        financial_metrics_df_cut['pe_score'] +
        financial_metrics_df_cut['fcf_growth_score'] +
        financial_metrics_df_cut['earnings_to_fcf_score'] +
        financial_metrics_df_cut['roic_score'] +
        financial_metrics_df_cut['debt_to_equity_score'] +
        financial_metrics_df_cut['interest_coverage_score']
    )

    # Convert to JSON for better LLM ingestion
    financial_metrics_json = financial_metrics_df_cut.to_json(orient='records', date_format='iso')

    logger.info("Fundamental/Analyst Tool Completed!")
    
    return financial_metrics_json
