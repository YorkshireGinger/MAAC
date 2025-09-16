import os
from dotenv import load_dotenv
import json
import logging
from datetime import date

from typing import TypedDict, List
from IPython.display import Image, display
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from datetime import datetime, timedelta

from agents import (
    run_valuation_agent_tool, 
    run_news_sentiment_agent_tool, 
    run_fundamental_agent_tool
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Schema for structured output of agents
class Recommendation(BaseModel):
    tickers: List[str] = Field(...,
        description="The tickers in question"
    )
    recommendation: List[str] = Field(...,
        description="Either BUY, SELL, or HOLD related to the ticker"
    )
    justification: List[str] = Field(...,
        description="The reasons behind the decision to BUY, SELL, or HOLD related to the ticker"
    ) 

# Graph state
class State(TypedDict):
    tickers: List[str]
    as_of_date: str
    data_start_date: str 
    valuation_recommendation: Recommendation
    news_recommendation: Recommendation
    fundamental_recommendation: Recommendation
    coordinator_output: Recommendation

class MAAC:
    """MAAC (Multi-Agent Alpha Copilot)
    
    This class implements a multi-agent AI system for financial analysis and 
    investment recommendations.
    It orchestrates several specialized agents—each responsible for a distinct 
    aspect of equity analysis (valuation/momentum, news sentiment, and 
    fundamental quality)—and combines their outputs into a unified recommendation.

    Attributes:
        llm: The language model instance used for generating structured outputs 
        and recommendations.
        the_graph: The Langgraph graph connecting all agent nodes.
    """
    
    def __init__(self) -> None:
        self.llm = self.setup_llm()
        self.the_graph = self.build_graph()

    def setup_llm(self) -> ChatAnthropic:
        """Initalise the LLM of choice, currently Anthropic"""
        
        llm = ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL"), 
            temperature=0, 
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        return llm

    # Graph Nodes
    def Valuation_Momentum_Agent(self, state: State) -> dict:
        """Analyzes valuation and momentum data for a set of tickers over 
        a specified time period and generates a BUY, HOLD, or SELL recommendation 
        for each ticker.
        Args:
            state (State): A dictionary-like object containing the current state 
            of the graph variables.
        Returns:
            dict: A dictionary with a single key 'valuation_recommendation' containing 
            the structured output Recommendation, the recommendations and justifications 
            for each ticker.
        """

        logger.info("Valuation/Momentum Agent Called ...")

        # Run the valuation agent tool to get RSI data
        tool_output = run_valuation_agent_tool(
            tickers=state['tickers'],
            start_date=state['data_start_date'],
            end_date=state['as_of_date']
            )
        
        # Convert to string so it can be read by the LLM
        if not isinstance(tool_output, str):
            tool_output = json.dumps(tool_output)

        # Augment the LLM with structured output to ensure consistent formatting
        llm_structured_output = self.llm.with_structured_output(Recommendation)

        # Ask the LLM to provide recommendations based on the RSI data
        msg = llm_structured_output.invoke(
            [
                SystemMessage(
                    content=f"""Your role:
- Valuation & Momentum Equity Analyst

Your task:
- Analyze the RSI (Relative Strength Index) trends of EACH ticker over a defined 
time horizon to understand market momentum and optimal buy entry timing.
- Identify trends and patterns in valuation metrics over time.
- Interpret the implications of these trends for investors looking to enter the market as of {state['as_of_date']}.
- Assign a single recommendation for EACH ticker: BUY, HOLD, or SELL with a clear justification.

RSI‑based rules (single source of truth):
- RSI < 30 → BUY (stock is oversold)
- RSI between 30 and 70 (inclusive) → HOLD (neutral momentum)
- RSI > 70 → SELL (stock is overbought)

Strict information constraint:
- Do NOT use any knowledge or information after {state['as_of_date']}.
- Only use the RSI and valuation/momentum data provided in the prompt.
- Do not infer or assume market conditions from outside sources.

Process:
- For each ticker, review the provided RSI value and any relevant valuation/momentum trends.
- Apply the RSI‑based rules above to determine the recommendation.
- Provide a clear, concise justification for the recommendation, explicitly referencing the 
RSI value and any notable valuation/momentum patterns from the provided dataset.

Examples (for reference; do not change rules):
- Example A: RSI = 25 → Rule “RSI < 30” → BUY.
- Example B: RSI = 55 → Rule “RSI between 30 and 70” → HOLD.
- Example C: RSI = 82 → Rule “RSI > 70” → SELL.

Prohibitions:
- Do not reinterpret or generalize the RSI rules.
- Do not use any external market knowledge, news, or events beyond {state['as_of_date']}.
- Do not omit the justification — every recommendation must be explained using the provided 
RSI and valuation/momentum data.

Reminder:
- All content must adhere to {state['as_of_date']}.
- Follow the provided output schema exactly.
"""
                ),
                HumanMessage(content=tool_output),
            ]
        )

        logger.info("Valuation/Momentum Agent Answered!")
        logger.info(f"------- Valuation/Momentum Agent Recommendation --------")
        for ticker, rec, just in zip(
            msg.tickers, 
            msg.recommendation, 
            msg.justification
        ):
            logger.info(f"\nTicker: {ticker}\nRecommendation: {rec}\nJustification: {just}\n{'-'*40}")


        return {"valuation_recommendation": msg}


    def News_Sentiment_Agent(self, state: State) -> dict:
        """Analyzes financial news sentiment for a set of tickers and generates investment 
        recommendations.
        Args:
            state (State): A dictionary-like object containing the current state 
            of the graph variables.
        Returns:
            dict: A dictionary containing the LLM's structured recommendation output under 
            the key 'news_recommendation'.
            """


        logger.info("News/Sentiment Agent Called ...")

        # Run the news sentiment agent tool to get sentiment scores
        tool_output_all, tool_output_summary = run_news_sentiment_agent_tool()

        # Convert dict outputs to strings so they can be read by the LLM
        if not isinstance(tool_output_all, str):
            tool_output_all = json.dumps(tool_output_all)
        if not isinstance(tool_output_summary, str):
            tool_output_summary = json.dumps(tool_output_summary)

        # Augment the LLM with structured output to ensure consistent formatting
        llm_structured_output = self.llm.with_structured_output(Recommendation)

        # Ask the LLM to provide recommendations based on the sentiment scores
        msg = llm_structured_output.invoke(
            [
                SystemMessage(
                    content=f"""Your role:
- News Sentiment Equity Analyst

Your task:
- Analyze the financial news sentiment provided for a set of TICKERS as of {state['as_of_date']}.
- Assess the implications for investors based solely on the provided data.
- Assign a single recommendation for EACH ticker: BUY, HOLD, or SELL with a clear justification.

Data provided:
- Pre‑processed financial news with sentiment scores.
- Pre‑calculated sentiment scores for each ticker.

Strict information constraint:
- Do NOT use any knowledge or information after {state['as_of_date']}.
- Only use the news data and sentiment scores provided in the prompt.
- Do not infer or assume sentiment from outside sources.

Sentiment‑based guidance (single source of truth):
- Overall Positive sentiment → BUY
- Overall Neutral or mixed sentiment → HOLD
- Overall Negative sentiment → SELL

Process:
- For each ticker, review the pre‑calculated sentiment score and any relevant news context provided.
- Map the sentiment score to a recommendation using the sentiment‑based guidance above.
- Provide a clear, concise justification for the recommendation, explicitly referencing the sentiment 
score and any notable news drivers from the provided dataset.
- Ensure the justification explains the likely investor reaction based on sentiment.

Examples (for reference; do not change rules):
- Example A: Sentiment score = Positive → BUY.
- Example B: Sentiment score = Neutral → HOLD.
- Example C: Sentiment score = Negative → SELL.

Prohibitions:
- Do not reinterpret or generalize the sentiment mapping rules.
- Do not use any external news, events, or market knowledge beyond {state['as_of_date']}.
- Do not omit the justification — every recommendation must be explained using the provided 
sentiment data.

Reminder:
- All content must adhere to {state['as_of_date']}.
- Follow the provided output schema exactly.
"""
                ),
                HumanMessage(content=tool_output_all),
                HumanMessage(content=tool_output_summary),
            ]
        )

        logger.info("News/Sentiment Agent Answered!")
        logger.info(f"------- News/Sentiment Agent Recommendation --------")
        for ticker, rec, just in zip(
            msg.tickers, 
            msg.recommendation, 
            msg.justification
        ):
            logger.info(f"\nTicker: {ticker}\nRecommendation: {rec}\nJustification: {just}\n{'-'*40}")


        return {"news_recommendation": msg}


    def Fundamental_Quality_Agent(self, state: State) -> dict:
        """Analyzes fundamental financial data for a set of tickers and generates 
        investment recommendations.

        Args:
            state (State): A dictionary-like object containing the current state 
            of the graph variables.

        Returns:
            dict: A dictionary with the key 'fundamental_recommendation' containing 
            the model's recommendations and justifications.
        """

        logger.info("Fundamental/Analyst Agent Called ...")

        # Minus 90 days, approx a quarter, to ensure we don't use earnings data that 
        # has not yet been released as of the as_of_date. Leakage control.
        as_of_date_minus_90 = (datetime.strptime(state['as_of_date'], "%Y-%m-%d")
                                - timedelta(days=90)).strftime("%Y-%m-%d")
        data_start_date_minus_90 = (datetime.strptime(state['data_start_date'], "%Y-%m-%d") 
                                    - timedelta(days=90)).strftime("%Y-%m-%d")

        # Run the fundamental agent tool to get fundamental scores
        tool_output = run_fundamental_agent_tool(
            tickers=state['tickers'],
            report_period_lte=as_of_date_minus_90,
            report_period_gte=data_start_date_minus_90
        )       

        # Convert to string so it can be read by the LLM
        if not isinstance(tool_output, str):
            tool_output = json.dumps(tool_output)

        # Augment the LLM with structured output to ensure consistent formatting
        llm_structured_output = self.llm.with_structured_output(Recommendation)

        # Ask the LLM to provide recommendations based on the fundamental scores
        msg = llm_structured_output.invoke(
            [
                SystemMessage(
                    content=f"""Your role:
- Fundamental Equity Analyst that focuses on Quality factors

Your task:
- Analyze the most recent fundamental data provided for a set of TICKERS as of {state['as_of_date']}.
- Assess each company’s quality based solely on the provided data.
- Assign a single recommendation for EACH ticker: BUY, HOLD, or SELL with a clear justification.

Definition of a quality company:
- Consistently generates strong earnings that are matched with free cash flow and cash flow growth.
- Maintains high returns on invested capital (ROIC).
- Sustains a healthy balance sheet with manageable debt levels.

Scoring rules (single source of truth):
- Score > 6 → BUY
- Score between 4 and 6 (inclusive) → HOLD
- Score < 4 → SELL

Strict information constraint:
- Do NOT use any knowledge or information after {state['as_of_date']}.
- Only use the data provided in the prompt.
- Do not infer or assume values not explicitly given.

Process:
- For each ticker, read the provided fundamental score.
- Apply the scoring rules above to determine the recommendation.
- Provide a comprehensive justification for the recommendation, explicitly referencing the 
relevant data points (e.g., earnings growth, ROIC, debt levels) from the provided dataset.
- Ensure the justification aligns with the definition of a quality company.

Examples (for reference; do not change rules):
- Example A: Score = 7.2 → Rule “Score > 6” → BUY.
- Example B: Score = 5.0 → Rule “Score between 4 and 6” → HOLD.
- Example C: Score = 3.5 → Rule “Score < 4” → SELL.

Prohibitions:
- Do not reinterpret or generalize the scoring rules.
- Do not use any external market knowledge, news, or events beyond {state['as_of_date']}.
- Do not omit the justification — every recommendation must be explained using the provided data.

Reminder:
- All content must adhere to {state['as_of_date']}.
- Follow the provided output schema exactly.
"""
                ),
                HumanMessage(content=tool_output)
            ]
        )

        logger.info("Fundamental/Quality Agent Answered!")
        logger.info(f"------- Fundamental/Quality Agent Recommendation --------")
        for ticker, rec, just in zip(
            msg.tickers, 
            msg.recommendation, 
            msg.justification
        ):
            logger.info(f"\nTicker: {ticker}\nRecommendation: {rec}\nJustification: {just}\n{'-'*40}")

        return {"fundamental_recommendation": msg}


    def Coordinator(self, state: State) -> dict:
        """Aggregates recommendations from three different analysts (valuation, news, and 
        fundamental) into a single, unified recommendation for each ticker.

        Args:
            state (State): A dictionary-like object containing the current state 
            of the graph variables.
        Returns:
            dict: A dictionary with the key 'coordinator_output' containing the synthesized 
            recommendation and justification.
        """
        
        logger.info("Coordinator Agent Called ...")

        # Augment the LLM with structured output to ensure consistent formatting
        llm_structured_output = self.llm.with_structured_output(Recommendation)

        # Ask the LLM to combine the recommendations from the three agents
        msg = llm_structured_output.invoke(
            [
                SystemMessage(
                    content=f"""Your role:
- Equity Portfolio Manager

Your task:
- Synthesize these three analysts’ recommendations (valuation/momentum, news sentiment, 
fundamental/quality) into a single recommendation for EACH ticker.

Your Goal:
- Your final output should be a single recommendation for EACH ticker of either BUY, 
SELL, or HOLD, along with a comprehensive justification that encapsulates the key 
points from the three provided analyses.

Strict information constraint:
- Do NOT use any knowledge after {state['as_of_date']}.

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

Hard constraint on UJ:
- “Use Your Judgement” is allowed ONLY in these two cases: (2×BUY + 1×HOLD) and 
(2×SELL + 1×HOLD).
- In ALL other cases, you MUST NOT use judgment. Apply the matrix directly.

Process:
1) Count votes (BUY, HOLD, SELL).
2) Map counts to the final recommendation using the decision rules above.
3) Only if the result is UJ, explicitly state that this is part of the voting process 
and weigh the analysts’ reasoning and conviction to decide BUY/SELL/HOLD.

Examples (for reference; do not change rules):
- Example A: Votes = [HOLD, HOLD, BUY] → Counts {{BUY:1,HOLD:2,SELL:0}} → Rule “2×HOLD + 1×BUY → HOLD”
 → HOLD.
- Example B: Votes = [BUY, BUY, HOLD] → Counts {{BUY:2,HOLD:1,SELL:0}} → Rule “2×BUY + 1×HOLD → UJ”
 → Use judgment to choose final recommendation.
- Example C: Votes = [SELL, SELL, HOLD] → Counts {{BUY:0,HOLD:1,SELL:2}} → Rule “2×SELL + 1×HOLD → UJ”
 → Use judgment to choose final recommendation.

Prohibitions:
- Do not reinterpret or generalize the decision rules.
- Do not output “Use Your Judgement” as the final recommendation. It is a step, not an 
output label.
- Do not use judgment for any case except the two explicitly listed.

Reminder:
- All content must adhere to {state['as_of_date']}.
- Follow the output schema strictly.
"""
                ),
                HumanMessage(content=state['valuation_recommendation'].model_dump_json()),
                HumanMessage(content=state['news_recommendation'].model_dump_json()),
                HumanMessage(content=state['fundamental_recommendation'].model_dump_json())
            ]
        )

        logger.info("Coordinator Agent Has Reached Consensus!")

        return {"coordinator_output": msg}

    def build_graph(self) -> StateGraph:
        logger.info("Building the Agents ...")
        # Set up the graph with state variables
        parallel_builder = StateGraph(State)

        # Add nodes
        parallel_builder.add_node("Valuation/Momentum Agent", self.Valuation_Momentum_Agent)
        parallel_builder.add_node("News Sentiment Agent", self.News_Sentiment_Agent)
        parallel_builder.add_node("Fundemental/Quality Agent", self.Fundamental_Quality_Agent)
        parallel_builder.add_node("Coordinator", self.Coordinator)

        # Add edges to connect nodes
        parallel_builder.add_edge(START, "Valuation/Momentum Agent")
        parallel_builder.add_edge(START, "News Sentiment Agent")
        parallel_builder.add_edge(START, "Fundemental/Quality Agent")
        parallel_builder.add_edge("Valuation/Momentum Agent", "Coordinator")
        parallel_builder.add_edge("News Sentiment Agent", "Coordinator")
        parallel_builder.add_edge("Fundemental/Quality Agent", "Coordinator")
        parallel_builder.add_edge("Coordinator", END)
        parallel_workflow = parallel_builder.compile()
        logger.info("Agents built!")

        # Show and save workflow
        img_bytes = parallel_workflow.get_graph().draw_mermaid_png()
        display(Image(img_bytes))
        with open("maac_graph.png", "wb") as f:
            f.write(img_bytes)

        return parallel_workflow