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

- Tested on Ubuntu 24.4.01 LTS (WSL2 on Windows 11)
- Tested using Python 3.12
- API keys for [financialdatasets.ai](https://financialdatasets.ai/) and [Anthropic](https://www.anthropic.com/)
- See `requirements.txt` for all Python dependencies

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YorkshireGinger/MAAC.git
   cd MAAC
   ```

2. **Setup & Initiate Virtual Environment**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
    OR 
    ```bash
    python3.12 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env` or create a `.env` file in the root directory.
   - Add your API keys:
     ```env
     FINANCIAL_DATASETS_API_KEY="<your-financialdatasets-api-key>"
     ANTHROPIC_API_KEY="<your-anthropic-api-key>"
     ANTHROPIC_MODEL="claude-sonnet-4-20250514"
     ```

## Usage

Run the tests and main pipeline from the terminal within the initated venv:

Tests that we can connect to the relevant financialdatasets.ai APIs.
```bash
python -m unittest tests/test_financial_api.py
```

Tests that the sharpe ratio math is correct.
```bash
python -m unittest tests/test_sharpe_ratio.py
```

Main entry point
```bash
python run.py --as_of_date YYYY-MM-DD
```
- `--as_of_date`: The analysis start date in `YYYY-MM-DD` format where BUY portfolio is constructed. Defaults to `2025-06-01` if not provided. This as_of_date MUST be atleast 100 days before todays date to allow the backtest to run. The data collection window for the agents to analyse is then set at 4 months prior to this as_of_date to ensure we get alteast 1 earnings quarter for financial metrics.  

Example:
```bash
python run.py --as_of_date 2025-06-01
```

## File Structure
- `run.py` — Main entry point for running the MAAC pipeline
- `graph.py` — Multi-agent orchestration and LLM logic
- `agents.py` — Agent tools for valuation, sentiment, and fundamentals
- `backtest.py` — Backtesting and performance evaluation
- `data/` — Data fetching utilities and news/sentiment analysis
- `outputs/` — Backtest outputs 
- `requirements.txt` — Python dependencies
- `.env` — Environment variables 

## What Happens When You Run It?
1. **MAAC Orchestration:**
   - The system analyzes a set of tickers (default: AAPL, MSFT, NVDA, TSLA) using three agents:
     - Valuation/Momentum (RSI)
     - News/Sentiment (VADER)
     - Fundamental/Quality (financial metrics)
   - Each agent fetches real data (except news for now) and produces recommendations.
   - The LLM (Anthropic Claude) coordinates and combines these into a final recommendation for each ticker.
   - The repo uses [LangGraph](https://langchain-ai.github.io/langgraph/tutorials/workflows/) to implement a router workflow.

    - The following diagram illustrates the MAAC workflow:

      ![MAAC Graph](maac_graph.png)

 
2. **Backtesting:**
   - The system simulates a 3-month forward period from the `as_of_date`.
   - It calculates and logs:
     - 3-month forward absoulte and active returns for MAAC "BUY" tickers vs all tickers
     - Annualized Sharpe ratios for both portfolios
     - Plots cumulative returns and saves the plot as `cumulative_returns_3m.png`

3. **Logging:**
   - All key steps and results are logged to the terminal for transparency.

4. **Expected Output**: `--as_of_date 2025-06-01`

```
INFO:__main__:***Welcome to the PoC Multi-Agent AI called MAAC! (Multi-Agent Alpha Copilot)***
INFO:__main__:Starting the Multi-Agent AI ...
INFO:graph:Building the Agents ...
INFO:graph:Agents built!
<IPython.core.display.Image object>
INFO:graph:Fundamental/Analyst Agent Called ...
INFO:agents:Starting Fundamental/Analyst Tool ...
INFO:graph:News/Sentiment Agent Called ...
INFO:graph:Valuation/Momentum Agent Called ...
INFO:agents:Starting News/Sentiment Tool ...
INFO:agents:Starting Valuation/Momentum Tool ...
INFO:agents:News/Sentiment Tool Completed!
INFO:agents:Fundamental/Analyst Tool Completed!
INFO:agents:Valuation/Momentum Tool Completed!
INFO:httpx:HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
INFO:graph:Valuation/Momentum Agent Answered!
INFO:graph:------- Valuation/Momentum Agent Recommendation --------
INFO:graph:
Ticker: AAPL
Recommendation: HOLD
Justification: AAPL's most recent RSI value on 2025-05-30 is 53.01, which falls within the 30-70 range indicating neutral momentum. The stock showed significant oversold conditions in March (RSI as low as 17.70) but has since recovered to neutral territory, making HOLD the appropriate recommendation.
----------------------------------------
INFO:graph:
Ticker: MSFT
Recommendation: SELL
Justification: MSFT's most recent RSI value on 2025-05-30 is 71.42, which exceeds the 70 threshold indicating overbought conditions. The stock showed a dramatic upward momentum trend from April through May, with RSI values reaching as high as 96.04 in mid-May, confirming strong overbought status and warranting a SELL recommendation.
----------------------------------------
INFO:graph:
Ticker: NVDA
Recommendation: SELL
Justification: NVDA's most recent RSI value on 2025-05-30 is 73.32, which exceeds the 70 threshold indicating overbought conditions. The stock demonstrated extreme overbought momentum from May 9-23 with RSI values consistently above 85, and despite some cooling remains above 70, warranting a SELL recommendation.
----------------------------------------
INFO:graph:
Ticker: TSLA
Recommendation: HOLD
Justification: TSLA's most recent RSI value on 2025-05-30 is 68.34, which falls within the 30-70 range indicating neutral momentum. While the stock showed severe oversold conditions in early March (RSI as low as 13.56) and later exhibited overbought periods in May, it has settled into neutral territory, making HOLD the appropriate recommendation.
----------------------------------------
INFO:httpx:HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
INFO:graph:News/Sentiment Agent Answered!
INFO:graph:------- News/Sentiment Agent Recommendation --------
INFO:graph:
Ticker: AAPL
Recommendation: BUY
Justification: AAPL shows overall positive sentiment with an average snippet sentiment value of 0.145 and median of 0.273. Key positive drivers include revolutionary AR glasses launch, stock surge after product reveal, renewable energy investments, and enhanced security features. Despite some negative news about iOS bugs and lawsuits, the overall sentiment remains positive, indicating favorable investor reaction.
----------------------------------------
INFO:graph:
Ticker: TSLA
Recommendation: BUY
Justification: TSLA demonstrates overall positive sentiment with an average snippet sentiment value of 0.078. Positive catalysts include next-gen battery technology unveiling, stock hitting new highs, strong quarterly profits beating expectations, and affordable EV model launch. While there are concerns about Autopilot safety and labor practices, the positive sentiment outweighs negatives, suggesting investor optimism.
----------------------------------------
INFO:graph:
Ticker: NVDA
Recommendation: BUY
Justification: NVDA exhibits overall positive sentiment with an average snippet sentiment value of 0.070. Positive momentum comes from next-gen GPU launch, strong AI demand driving stock rises, data center solutions expansion, and CEO's positive AI future outlook. Despite pricing backlash and gaming revenue decline, the overall positive sentiment indicates continued investor confidence in the company's AI leadership.
----------------------------------------
INFO:graph:
Ticker: MSFT
Recommendation: BUY
Justification: MSFT shows the strongest positive sentiment among all tickers with an average snippet sentiment value of 0.194 and median of 0.189. Strong positive drivers include new Surface device launches, stock reaching all-time highs due to cloud growth, AI startup investments, gaming division expansion, and global data center expansion. While facing some criticism over Azure outages and employee protests, the overwhelmingly positive sentiment suggests strong investor confidence.
----------------------------------------
INFO:httpx:HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
INFO:graph:Fundamental/Quality Agent Answered!
INFO:graph:------- Fundamental/Quality Agent Recommendation --------
INFO:graph:
Ticker: AAPL
Recommendation: BUY
Justification: AAPL receives a BUY recommendation with a fundamental score of 7, which exceeds the 6 threshold. The company demonstrates strong quality characteristics with exceptional ROIC of 46% indicating highly efficient capital allocation, and strong earnings-to-FCF ratio of 0.98 showing earnings are well-supported by cash generation. However, the company faces challenges with negative FCF growth of -9.7% and high debt-to-equity ratio of 4.15, but the overall quality metrics support the BUY rating.
----------------------------------------
INFO:graph:
Ticker: MSFT
Recommendation: HOLD
Justification: MSFT receives a HOLD recommendation with a fundamental score of 6, which falls within the 4-6 range. The company shows solid quality fundamentals with strong ROIC of 48.2% and excellent interest coverage of 43.4x, indicating strong profitability and low financial risk. The manageable debt-to-equity ratio of 0.76 reflects a healthy balance sheet. However, negative FCF growth of -3.6% and earnings-to-FCF ratio of 1.32 (indicating earnings exceed FCF) present some concerns for cash generation efficiency.
----------------------------------------
INFO:graph:
Ticker: NVDA
Recommendation: BUY
Justification: NVDA receives a BUY recommendation with a fundamental score of 8, the highest among all tickers. The company exhibits exceptional quality characteristics with outstanding ROIC of 116.1%, demonstrating superior capital efficiency. Strong fundamentals include positive FCF growth of 7.6%, low debt-to-equity ratio of 0.41 indicating conservative financial management, and excellent interest coverage of 341.2x. The earnings-to-FCF ratio of 1.20 shows reasonable alignment between earnings and cash flow generation.
----------------------------------------
INFO:graph:
Ticker: TSLA
Recommendation: HOLD
Justification: TSLA receives a HOLD recommendation with a fundamental score of 4, which falls at the lower boundary of the 4-6 range. The company shows mixed quality indicators with a reasonable debt-to-equity ratio of 0.66 and adequate interest coverage of 26.5x. However, significant quality concerns include low ROIC of 11.8% indicating poor capital efficiency, negative FCF growth of -0.8%, and high earnings-to-FCF ratio of 1.97 suggesting earnings significantly exceed actual cash generation. The extremely high P/E ratio of 182.8 also reflects valuation concerns.
----------------------------------------
INFO:graph:Coordinator Agent Called ...
INFO:httpx:HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
INFO:graph:Coordinator Agent Has Reached Consensus!
INFO:__main__:
Ticker: AAPL
Recommendation: BUY
Justification: AAPL receives a BUY recommendation based on voting results: Valuation Agent (HOLD), News Sentiment Agent (BUY), Fundamental Agent (BUY). Vote counts: {BUY:2, HOLD:1, SELL:0}. This maps to '2×BUY + 1×HOLD → Use Your Judgement'. After weighing the analysts' reasoning, the strong positive sentiment (0.145 average) driven by revolutionary AR glasses launch and renewable energy investments, combined with exceptional fundamental quality (ROIC 46%, earnings-to-FCF 0.98), outweighs the neutral momentum concerns. The RSI of 53.01 indicates stable conditions, making BUY the appropriate choice given the strong fundamentals and positive market sentiment.
----------------------------------------
INFO:__main__:
Ticker: MSFT
Recommendation: HOLD
Justification: MSFT receives a HOLD recommendation based on voting results: Valuation Agent (SELL), News Sentiment Agent (BUY), Fundamental Agent (HOLD). Vote counts: {BUY:1, HOLD:1, SELL:1}. This maps to '2×HOLD + 1×BUY → HOLD' per the decision matrix. The overbought technical conditions (RSI 71.42) signal caution despite strong positive sentiment (0.194 average) from cloud growth and AI investments. The solid fundamental score of 6 with strong ROIC of 48.2% and healthy balance sheet supports stability, but negative FCF growth (-3.6%) and technical overbought status warrant a cautious HOLD approach.
----------------------------------------
INFO:__main__:
Ticker: NVDA
Recommendation: BUY
Justification: NVDA receives a BUY recommendation based on voting results: Valuation Agent (SELL), News Sentiment Agent (BUY), Fundamental Agent (BUY). Vote counts: {BUY:2, HOLD:0, SELL:1}. This maps to '2×BUY + 1×SELL → HOLD' per the decision matrix. Despite overbought technical conditions (RSI 73.32), the exceptional fundamental quality (score 8, ROIC 116.1%, positive FCF growth 7.6%) and strong positive sentiment (0.070 average) driven by AI leadership and next-gen GPU launches provide compelling reasons for a BUY recommendation. The company's superior capital efficiency and conservative financial management outweigh short-term technical concerns.
----------------------------------------
INFO:__main__:
Ticker: TSLA
Recommendation: HOLD
Justification: TSLA receives a HOLD recommendation based on voting results: Valuation Agent (HOLD), News Sentiment Agent (BUY), Fundamental Agent (HOLD). Vote counts: {BUY:1, HOLD:2, SELL:0}. This maps to '2×HOLD + 1×BUY → HOLD' per the decision matrix. While positive sentiment (0.078 average) from next-gen battery technology and strong quarterly profits provides optimism, the neutral momentum (RSI 68.34) and mixed fundamental quality (score 4, low ROIC 11.8%, negative FCF growth -0.8%) suggest maintaining current positions rather than adding exposure.
----------------------------------------
INFO:__main__:Starting the Backtest ...
INFO:__main__:3-Month Forward Returns - MAAC BUYs: 20.94%, All Tickers: 12.25%
INFO:__main__:3-Month Sharpe Ratio - MAAC BUYs: 3.98, All Tickers: 2.26
INFO:__main__:Cumulative Returns plot saved to 'cumulative_returns_3m.png'
INFO:__main__:***Multi-Agent AI & Backtest Completed!***
```

Backtest outputs are in `/outputs`

## Decisions Made
**Leakage Control:** The agents are under strict instruction to use information provded and not use any of their own information or knowledge past the as_of_date. The model used in this repo is trained up until 20250514 so any as_of_date chosen after that should have no issue anyway. In addition, the fundamental data used by the Fundamental agent is 90 days prior to the as_of_date to ensure there is no leakage between an earnings report date and actual release date.

**Data Lookback Window:** The data collection has a 120 days lookback window.

**News Data:** I have chosen to not run the news data pipeline from financialdatasets.ai as you have to open a link to get snippets which is not best use of my time. Therefore, I have let an LLM create the headlines and snippets. 

**News Sentiment:** I have chosen to use VADER for this task as it is simple to install and use. Had I  more time I would expeirmented with FinBERT and other finance-specific sentiment models which will better classify jargon. Unfortuntely with FinBERT, it takes way too long to pip install the dependencies. 

**Fundamental Inputs:** I have chosen metrics that aim to cover the specturm of earnings quality, cash generation and financial strength. These are simply extracted from financialdatasets.ai. 

**Agent Scoring Methods:** These are educuated guesses and aren't neccessarily what they should be.
- **Valuation/Momentum Rule**: RSI was chosen, many other could have been. The logic is to follow generally accepted, though unnecessarliy arbitary, ovrebought (<30) and oversold (>70) levels and then map to BUY/HOLD/SELL. 
- **News Sentiment Rule**: VADER outputs a compound score which score overall sentiment and has generally accepted mappings to positive, neutal and negative sentiment and then to BUY/HOLD/SELL. 
- **Fundamental/Quality Rule**: Rough values for good and bad for each metric are assigned based on the four tickers being tech companies. However, to score how fundamentally good a company is, you would need to know the market levels, peer levels and its own historic levels for each metric to get a relative sense of good/bad. I provided a scorecard for a total company score with thresholds mapped to BUY/HOLD/SELL. 
- **Coordinator Rule**: Created a consenus matrix whereby: 
```
Decision rules (single source of truth):
- 3×BUY → BUY
- 2×BUY + 1×HOLD → Use Your Judgement (UJ)
- 2×BUY + 1×SELL → HOLD
- 3×HOLD → HOLD
- 2×HOLD + 1×BUY → HOLD
- 2×HOLD + 1×SELL → HOLD
- 3×SELL → SELL
- 2×SELL + 1×BUY → HOLD
- 2×SELL + 1×HOLD → Use Your Judgement (UJ)
```
- *Use Your Judgement* is their to understand that PMs don't live by hard and fast rules and excersize judgement in marginal decicsions. It also provides an avenue to use a RAG to help egt more clarifying information should the PM need it.  

**Agent Prompts**: These were iterated through, starting with the ones in the Blackrock paper, and then finalised as they are now. The emphasis is on following a rules based appraoch and not deviating. They can be seen in the `graph.py` file

**How to Parrellise Ticker Recomendations:** Given the small universe, I went for thr appraoch to run all 4 tickers at once in the same Recommendation output schema which are lists. As the universe grows, this will get messy and the indexing of lists is not ai-proof. As this scales I would suggest, if using the Lngraph framework, to use the [Send api](https://docs.langchain.com/oss/python/langgraph/workflows-agents#:~:text=Orchestrator%2Dworker%20workflows%20are,section%20to%20each%20worker.) which creates parrell ticker tasks and resources which will isolate any cross ticker contamination.   

## Next Steps
- Experiment with different Agentic workflows as this project scope expanded. [Here are some ideas.](https://langchain-ai.github.io/langgraph/tutorials/workflows/).
- Co-ordinate with analyst and PMs to add rigour to agents and backtest.
- Add RAG to collect qualititaive information or data. 
- Many more...

## Known Issues
- Sometimes the LLM uses its own judgement when it is told not too. This is shown in the example output shown above. 
- For Nvidia, it overrides the voting system and thinks that despite RSI showing it is overbought and a SELL, it decides it should BUY. 
- To mitigate this I would be adding another Agent that explicity checks for these kinds of LLM hallucinations to capture them before they get to the user.

## Time Accounting
- Reading and re-Reading Blackrock paper and assessment case study - 1.5hrs
- Creating data fucntions - 1.5hr
- Creating the Langgraph framework - 3hrs
- Iterating the agent prompts - 1hr
- Creating the agent tools - 3hrs
- Creating the backtest framework - 3hrs
- Creating Tests - 1hrs
- Cleaning the repo - 3hrs
- Writing README - 2hrs
- Halluination debugging - 1hr

## AI Tool Usage
- large parts of the README
- doc strings and fucntions input/output types 
- converting sandbox code to functions and classes
- the tests are born from copilot assistance
- most comments (re-read by myself to make sense or alter)
- any time the copilot autofills what I would have written (or better!)

## Notes
- The system is a proof-of-concept and will require further tuning for production use.
