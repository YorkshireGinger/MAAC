# %%
import pandas as pd
from get_stock_prices import get_stock_prices
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Valuation/Momentum Agent – uses market prices to compute a simple score
def calculate_rsi(prices, period=14):
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
):
    logger.info(f"Starting Valuation/Momentum Tool ...")
    daily_prices = get_stock_prices(
        tickers=tickers,
        interval=interval,
        interval_multiplier=interval_multiplier,
        start_date=start_date,
        end_date=end_date
    )
    daily_prices_df = pd.DataFrame(daily_prices)
    working_rsi_df = daily_prices_df.groupby('ticker')['close'].apply(
        lambda x: calculate_rsi(x, rsi_period)
    )
    working_rsi_df = working_rsi_df.reset_index().rename(
        columns={'close': f'rsi_{rsi_period}'}
    ).drop(columns=['level_1'])
    rsi_df = working_rsi_df.merge(
        daily_prices_df[['time']],
        how='left',
        left_index=True,
        right_index=True
    )
    rsi_json = rsi_df.to_json(orient='records', date_format='iso')
    logger.info("Valuation/Momentum Tool Completed!")
    return rsi_json

# %%
# News/Sentiment Agent – uses news headlines to compute a sentiment score
import json
from sentiment_stock_news import analyze_headline_sentiment
import numpy as np

def run_news_sentiment_agent_tool(
    run_news_pipeline=False, 
    news_file='stock_news.json', 
    output_file='ticker_news_sentiment_scores.json'
    ):
    logger.info("Starting News/Sentiment Tool ...")
    if run_news_pipeline:
        logger.debug("Running news pipeline...")
        # TODO use the news fetching and sentiment analysis code here
    else:
        logger.debug("Collecting pre-written news...")
        with open(news_file, 'r') as f:
            stock_news = json.load(f)
        logger.debug(f"Loaded news for {len(stock_news)} tickers.")
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

        with open(output_file, 'w') as f:
            json.dump(sentiment_scores, f, indent=2)
            logger.debug(f"Sentiment scores saved to {output_file}.")

        # TODO could add a weighted average that weights most recent articles more or that weights extreme sentiment more as these are the stories that may move price
        summary_scores = {}
        for ticker, items in sentiment_scores.items():
            snippet_scores = [item['snippet_score']['compound'] for item in items if 'compound' in item['snippet_score']]
            if snippet_scores:
                avg = float(np.mean(snippet_scores))
                median = float(np.median(snippet_scores))
            else:
                avg = None
                median = None
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

# %%
# Fundamental/Analyst Agent – uses fundamental data to compute a simple score
from get_stock_financial_metrics import get_stock_financial_metrics
import pandas as pd

def run_fundamental_agent_tool(
    tickers,
    report_period_lte,
    report_period_gte,
    period='ttm',
    limit=1
):
    # TODO choose better signals/metrics to return
    # TODO add some gauge as to how good/bad each metric is relative to its peers - this could a percentile
    logger.info("Starting Fundamental/Analyst Tool ...")
    stock_financial_metrics = get_stock_financial_metrics(
        tickers=tickers,
        report_period_lte=report_period_lte,
        report_period_gte=report_period_gte,
        period=period,
        limit=limit
    )
    financial_metrics_df = pd.DataFrame(stock_financial_metrics)
    financial_metrics_df_cut = (
        financial_metrics_df
        .loc[:,['ticker', 'fiscal_period', 'period',
        'price_to_earnings_ratio', 'peg_ratio',
        'return_on_invested_capital', 'debt_to_equity',
        'operating_income_growth']]
        .copy()
    )

    # Define scorecard thresholds for each metric
    def score_pe(pe):
        if pd.isna(pe):
            return 0
        if pe < 10:
            return 3
        elif pe < 20:
            return 2
        elif pe < 30:
            return 1
        else:
            return 0

    def score_peg(peg):
        if pd.isna(peg):
            return 0
        if peg < 1:
            return 3
        elif peg < 2:
            return 2
        elif peg < 3:
            return 1
        else:
            return 0

    def score_roic(roic):
        if pd.isna(roic):
            return 0
        if roic > 0.2:
            return 3
        elif roic > 0.1:
            return 2
        elif roic > 0.05:
            return 1
        else:
            return 0

    def score_debt_to_equity(dte):
        if pd.isna(dte):
            return 0
        if dte < 0.5:
            return 3
        elif dte < 1:
            return 2
        elif dte < 2:
            return 1
        else:
            return 0

    def score_op_income_growth(growth):
        if pd.isna(growth):
            return 0
        if growth > 0.2:
            return 3
        elif growth > 0.1:
            return 2
        elif growth > 0.05:
            return 1
        else:
            return 0

    # Apply scoring functions to each row
    financial_metrics_df_cut['pe_score'] = financial_metrics_df_cut['price_to_earnings_ratio'].apply(score_pe)
    financial_metrics_df_cut['peg_score'] = financial_metrics_df_cut['peg_ratio'].apply(score_peg)
    financial_metrics_df_cut['roic_score'] = financial_metrics_df_cut['return_on_invested_capital'].apply(score_roic)
    financial_metrics_df_cut['debt_to_equity_score'] = financial_metrics_df_cut['debt_to_equity'].apply(score_debt_to_equity)
    financial_metrics_df_cut['op_income_growth_score'] = financial_metrics_df_cut['operating_income_growth'].apply(score_op_income_growth)

    # Sum up the scores for a total score per ticker
    financial_metrics_df_cut['fundamental_score'] = (
        financial_metrics_df_cut['pe_score'] +
        financial_metrics_df_cut['peg_score'] +
        financial_metrics_df_cut['roic_score'] +
        financial_metrics_df_cut['debt_to_equity_score'] +
        financial_metrics_df_cut['op_income_growth_score']
    )

    financial_metrics_json = financial_metrics_df_cut.to_json(orient='records', date_format='iso')
    logger.info("Fundamental/Analyst Tool Completed!")
    return financial_metrics_json

# %%
