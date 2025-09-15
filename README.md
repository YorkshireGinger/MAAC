# MAAC: Multi-Agent Alpha Copilot

## Overview

MAAC (Multi-Agent Alpha Copilot) is a proof-of-concept AI system for financial analysis and investment recommendations. It orchestrates several specialized agents—each responsible for a distinct aspect of equity analysis (valuation/momentum, news sentiment, and fundamental quality)—and combines their outputs into a unified recommendation. The system also includes a backtesting module to evaluate the performance of its recommendations.

**Key Features:**
- Multi-agent architecture for stock analysis
- Integrates valuation/momentum, news sentiment, and fundamental analysis
- Uses Anthropic's Claude model for LLM-based reasoning
- Fetches real stock price, news, and financial data via API
- Backtests recommendations over a 3-month forward period
- Plots and logs performance metrics

## Requirements

- Tested on Ubuntu (WSL2 on Windows 11)
- Tested using Python 3.12
- API keys for [financialdatasets.ai](https://financialdatasets.ai/) and [Anthropic](https://www.anthropic.com/)
- See `requirements.txt` for all Python dependencies

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YorkshireGinger/MAAC.git
   cd MAAC
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup & Initiate Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env` or create a `.env` file in the root directory.
   - Add your API keys:
     ```env
     FINANCIAL_DATASETS_API_KEY="<your-financialdatasets-api-key>"
     ANTHROPIC_API_KEY="<your-anthropic-api-key>"
     ANTHROPIC_MODEL="claude-sonnet-4-20250514"
     ```

## Usage

Run the main pipeline from the terminal within the initated venv:

```bash
python run.py --as_of_date YYYY-MM-DD
```
- `--as_of_date`: The analysis start date in `YYYY-MM-DD` format where BUY portfolio is constructed. Defaults to `2025-01-02` if not provided.

Example:
```bash
python run.py --as_of_date 2025-01-02
```

## What Happens When You Run It?
1. **MAAC Orchestration:**
   - The system analyzes a set of tickers (default: AAPL, MSFT, NVDA, TSLA) using three agents:
     - Valuation/Momentum (RSI)
     - News/Sentiment (VADER)
     - Fundamental/Quality (financial metrics)
   - Each agent fetches real data and produces recommendations.
   - The LLM (Anthropic Claude) coordinates and combines these into a final recommendation for each ticker.
   - The repo uses [LangGraph](https://langchain-ai.github.io/langgraph/tutorials/workflows/) to implement a router workflow.

    - The following diagram illustrates the MAAC workflow:

      ![MAAC Graph](maac_graph.png)

 
2. **Backtesting:**
   - The system simulates a 3-month forward period from the `as_of_date`.
   - It calculates and logs:
     - 3-month forward returns for MAAC "BUY" tickers vs all tickers
     - Annualized Sharpe ratios for both portfolios
     - Plots cumulative returns and saves the plot as `cumulative_returns_3m.png`

3. **Logging:**
   - All key steps and results are logged to the terminal for transparency.

4. **Expected Output**

```
INFO:__main__:***Welcome to the PoC Multi-Agent AI called MAAC! (Multi-Agent Alpha Copilot)***
INFO:__main__:Starting the Multi-Agent AI ...
INFO:graph:Building the Agents ...
INFO:graph:Agents built!
<IPython.core.display.Image object>
INFO:graph:Fundamental/Analyst Agent Called ...
INFO:agents:Starting Fundamental/Analyst Tool ...
INFO:graph:News/Sentiment Agent Called ...
INFO:agents:Starting News/Sentiment Tool ...
INFO:graph:Valuation/Momentum Agent Called ...
INFO:agents:Starting Valuation/Momentum Tool ...
INFO:agents:News/Sentiment Tool Completed!
INFO:agents:Valuation/Momentum Tool Completed!
INFO:agents:Fundamental/Analyst Tool Completed!
INFO:httpx:HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
INFO:graph:Valuation/Momentum Agent Answered!
INFO:httpx:HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
INFO:graph:Fundamental/Analyst Agent Answered!
INFO:httpx:HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
INFO:graph:News/Sentiment Agent Answered!
INFO:graph:Coordinator Agent Called ...
INFO:httpx:HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
INFO:graph:Coordinator Agent Has Reached Consensus!
INFO:__main__:
Ticker: AAPL
Recommendation: BUY
Justification: AAPL receives a BUY recommendation based on 2 BUY + 1 HOLD votes. The technical analysis shows neutral RSI (58.05), but sentiment analysis reveals strong positive sentiment (0.145) driven by revolutionary AR glasses launch, health tech partnerships, and renewable energy investments. Fundamental analysis supports this with exceptional ROIC of 49.6% and healthy cash conversion (earnings-to-FCF ratio of 1.03). Despite high P/E ratio of 30.3, the company's innovation pipeline, strong profitability metrics, and multiple growth catalysts justify a bullish outlook.
----------------------------------------
INFO:__main__:
Ticker: MSFT
Recommendation: HOLD
Justification: MSFT receives a HOLD recommendation based on 1 BUY + 2 HOLD votes. Technical analysis shows neutral RSI (52.78) after extreme volatility. While sentiment analysis is strongly positive (0.194 average sentiment) with cloud growth, AI investments, and Surface device launches, fundamental analysis raises valuation concerns with high P/E ratio of 36.3 and elevated earnings-to-FCF ratio of 1.42. The strong ROIC of 45.7% and positive FCF growth of 3.2% are offset by valuation metrics, warranting a cautious HOLD approach.
----------------------------------------
INFO:__main__:
Ticker: NVDA
Recommendation: BUY
Justification: NVDA receives a BUY recommendation based on 1 BUY + 2 HOLD votes, requiring judgment. The fundamental analysis strongly supports BUY with the highest score of 8, exceptional ROIC of 112.2%, and outstanding financial strength. Despite neutral technical indicators (RSI 49.73) and mixed sentiment due to GPU pricing concerns, the company's superior profitability, strong position in AI boom, next-gen GPU launches, and data center expansion provide compelling long-term growth prospects that outweigh near-term headwinds.
----------------------------------------
INFO:__main__:
Ticker: TSLA
Recommendation: HOLD
Justification: TSLA receives a HOLD recommendation based on 1 SELL + 2 HOLD votes. Technical analysis shows concerning overbought conditions (RSI 75.56), suggesting potential downside risk. Sentiment analysis reveals mixed signals with modest positive sentiment (0.078) but significant concerns around Autopilot safety and production delays. Fundamental analysis highlights major weaknesses with extremely high P/E ratio of 168.7, declining FCF growth of -17.6%, and poor ROIC of 9.4%. While next-gen battery technology and record profits provide some support, the combination of technical, fundamental, and operational challenges warrants a cautious HOLD until clearer improvement emerges.
----------------------------------------
INFO:__main__:Starting the Backtest ...
INFO:__main__:3-Month Forward Returns - MAAC BUYs: -14.18%, All Tickers: -15.63%
INFO:__main__:3-Month Sharpe Ratio - MAAC BUYs: -1.46, All Tickers: -1.67
INFO:__main__:Cumulative Returns plot saved to 'cumulative_returns_3m.png'
INFO:__main__:***Multi-Agent AI & Backtest Completed!***
```

## File Structure
- `run.py` — Main entry point for running the MAAC pipeline
- `graph.py` — Multi-agent orchestration and LLM logic
- `agents.py` — Agent tools for valuation, sentiment, and fundamentals
- `backtest.py` — Backtesting and performance evaluation
- `data/` — Data fetching utilities and news/sentiment analysis
- `requirements.txt` — Python dependencies
- `.env` — Environment variables (API keys)

## Notes
- The system is a proof-of-concept and will require further tuning for production use.
