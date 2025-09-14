# %%
import os
from dotenv import load_dotenv
import json
import logging

from typing import TypedDict, List
from IPython.display import Image, display
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic

from agents import (
    run_valuation_agent_tool, 
    run_news_sentiment_agent_tool, 
    run_fundamental_agent_tool
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialise an LLM
llm = ChatAnthropic(
    model="claude-sonnet-4-20250514", 
    temperature=0, 
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
)

# Schemas for input/output validation
class Recomendation(BaseModel):
    ticker: List[str] = Field(...,
        description="The tickers in question"
    )
    recomendation: List[str] = Field(...,
        description="Either BUY, SELL, or HOLD related to the ticker"
    )
    justification: List[str] = Field(...,
        description="The reasons behind the decision to BUY, SELL, or HOLD each ticker"
    ) 

# Graph state
class State(TypedDict):
    tickers: List[str]
    as_of_date: str
    today_date: str 
    llm_1_recomendation: Recomendation
    llm_2_recomendation: Recomendation
    llm_3_recomendation: Recomendation
    combined_output: Recomendation

# Graph Nodes
def Valuation_Momentum_Agent(state: State):
    """
    Valuation/Momentum Agent – uses market prices to compute a simple score 
    (e.g., recent total return vs volatility or another well-justified rule) 
    → BUY/HOLD/SELL.
    """
    logger.info("Valuation/Momentum Agent Called ...")

    tool_output = run_valuation_agent_tool(
        tickers=state['tickers'],
        start_date=state['as_of_date'],
        end_date=state['today_date']
        )
    
    if not isinstance(tool_output, str):
        tool_output = json.dumps(tool_output)

    # Augment the LLM with structured output
    llm_structured_output = llm.with_structured_output(Recomendation)

    msg = llm_structured_output.invoke(
        [
            SystemMessage(
                content="""As a valuation equity analyst, your pri
mary responsibility is to analyze the RSI trends of a
given universe of assets or portfolio over an extended time horizon. To com
plete the task, you must analyze the provided valuation/momentum data
of the asset or portfolio provided, identify trends and patterns
in valuation metrics over time, and interpret the implications
of these trends for investors or stakeholders. 
You must assign a BUY, SELL, or HOLD recommendation for EACH ticker provided
with justification based on the analysis of the data provided.
"""
            ),
            HumanMessage(content=tool_output),
        ]
    )

    logger.info("Valuation/Momentum Agent Answered!")

    return {"llm_1_recomendation": msg}


def News_Sentiment_Agent(state: State):
    """Second LLM call to generate story"""

    logger.info("News/Sentiment Agent Called ...")

    tool_output_all, tool_output_summary = run_news_sentiment_agent_tool()
    # Convert JSON outputs to strings
    if not isinstance(tool_output_all, str):
        tool_output_all = json.dumps(tool_output_all)
    if not isinstance(tool_output_summary, str):
        tool_output_summary = json.dumps(tool_output_summary)
    # Augment the LLM with structured output
    llm_structured_output = llm.with_structured_output(Recomendation)

    msg = llm_structured_output.invoke(
        [
            SystemMessage(
                content="""As a sentiment equity analyst your pri
mary responsibility is to analyze the financial news;
and analyze its implication and sentiment for investors or
stakeholders. 
You will be provided with pre-processed news with pre-calculated sentiment scores for a set of TICKERS.
You must assign a BUY, SELL, or HOLD recommendation for EACH ticker provided
with justification based on the analysis of the data provided.
"""
            ),
            HumanMessage(content=tool_output_all),
            HumanMessage(content=tool_output_summary),
        ]
    )

    logger.info("News/Sentiment Agent Answered!")

    return {"llm_2_recomendation": msg}


def Fundamental_Quality_Agent(state: State):
    """Third LLM call to generate poem"""

    logger.info("Fundamental/Analyst Agent Called ...")

    tool_output = run_fundamental_agent_tool(
        tickers=state['tickers'],
        report_period_lte=state['today_date'],
        report_period_gte=state['as_of_date']
    )

    if not isinstance(tool_output, str):
        tool_output = json.dumps(tool_output)

    # Augment the LLM with structured output
    llm_structured_output = llm.with_structured_output(Recomendation)

    msg = llm_structured_output.invoke(
        [
            SystemMessage(
                content="""As a fundamental financial equity
analyst your primary responsibility is to analyze the most
recent fundamental data provided for a provided set of TICKERS.
Your analysis should be based solely on the
information that you have been given. 
You will be given scores for each company. It is advised to BUY
when the fundamental scores are > 6, HOLD when the scores are between 4 and 6,
and SELL when the scores are < 4.
You must assign a BUY, SELL, or HOLD recommendation for EACH ticker provided
with justification based on the analysis of the data provided.
"""
            ),
            HumanMessage(content=tool_output)
        ]
    )

    logger.info("Fundamental/Analyst Agent Answered!")

    return {"llm_3_recomendation": msg}


def Coordinator(state: State):
    
    logger.info("Coordinator Agent Called ...")

    # Augment the LLM with structured output
    llm_structured_output = llm.with_structured_output(Recomendation)

    msg = llm_structured_output.invoke(
        [
            SystemMessage(
                content="""You are an expert financial equity analyst.
Your task is to aggregate the recommendations from three different
analysts into a single, coherent recommendation for EACH ticker provided.
You have been provided with three distinct recommendations,
each accompanied by a justification. Your goal is to synthesize
these inputs into one unified recommendation that reflects
the collective insights of the individual analysts.
You must consider the reasoning behind each recommendation
and weigh their arguments to arrive at a final decision.
Your final output should be a single recommendation of either
BUY, SELL, or HOLD, along with a comprehensive justification
that encapsulates the key points from the three provided analyses.
"""
            ),
            HumanMessage(content=state['llm_1_recomendation'].model_dump_json()),
            HumanMessage(content=state['llm_2_recomendation'].model_dump_json()),
            HumanMessage(content=state['llm_3_recomendation'].model_dump_json())
        ]
    )

    logger.info("Coordinator Agent Has Reached Consensus!")

    return {"combined_output": msg}


logger.info("Building the Agents ...")
# Build workflow
parallel_builder = StateGraph(State)

# Add nodes
parallel_builder.add_node("Valuation/Momentum Agent", Valuation_Momentum_Agent)
parallel_builder.add_node("News Sentiment Agent", News_Sentiment_Agent)
parallel_builder.add_node("Fundemental/Quality Agent", Fundamental_Quality_Agent)
parallel_builder.add_node("Coordinator", Coordinator )

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

# Show workflow
display(Image(parallel_workflow.get_graph().draw_mermaid_png()))

# Invoke
logger.info("Starting the workflow ...")
state = parallel_workflow.invoke(
    {"tickers": ["AAPL", "MSFT", "NVDA", "TSLA"], 
    "as_of_date": "2025-01-01", 
    "today_date": "2025-09-12"}
)

# Show final output
graph_output = state["combined_output"]
for ticker, rec, just in zip(graph_output.ticker, graph_output.recomendation, graph_output.justification):
    logger.info(f"Ticker: {ticker}\nRecommendation: {rec}\nJustification: {just}\n{'-'*40}")
