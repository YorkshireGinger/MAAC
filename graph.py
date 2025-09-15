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
        description="The reasons behind the decision to BUY, SELL, or HOLD each ticker"
    ) 

# Graph state
class State(TypedDict):
    tickers: List[str]
    as_of_date: str
    today_date: str 
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
    
    def __init__(self):
        self.llm = self.setup_llm()
        self.the_graph = self.build_graph()

    def setup_llm(self):
        """Initalise the LLM of choice, currently Anthropic"""
        
        llm = ChatAnthropic(
            model=os.getenv("ANTHROPIC_MODEL"), 
            temperature=0, 
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        return llm

    # Graph Nodes
    def Valuation_Momentum_Agent(self, state: State):
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
            start_date=state['as_of_date'],
            end_date=state['today_date']
            )

        # Convert JSON output to string so it can be read by the LLM
        if not isinstance(tool_output, str):
            tool_output = json.dumps(tool_output)

        # Augment the LLM with structured output to ensure consistent formatting
        llm_structured_output = self.llm.with_structured_output(Recommendation)

        # Ask the LLM to provide recommendations based on the RSI data
        msg = llm_structured_output.invoke(
            [
                SystemMessage(
                    content="""As a valuation equity analyst, your primary responsibility 
                    is to analyze the RSI trends of a given universe of assets or portfolio 
                    over a time horizon. 
                    To complete the task, you must analyze the provided valuation/momentum data
                    of the asset or portfolio provided, identify trends and patterns
                    in valuation metrics over time, and interpret the implications
                    of these trends for investors or stakeholders. 
                    It is advised to BUY when RSI is < 30 as the stock is oversold,
                    HOLD when the RSI is between 30 and 70, and SELL when the RSI is > 70 as the 
                    stock is overbought.
                    You must assign a BUY, SELL, or HOLD recommendation for EACH ticker provided
                    with justification based on the analysis of the data provided.
                    """
                ),
                HumanMessage(content=tool_output),
            ]
        )

        logger.info("Valuation/Momentum Agent Answered!")

        return {"valuation_recommendation": msg}


    def News_Sentiment_Agent(self, state: State):
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

        # Convert JSON outputs to strings so they can be read by the LLM
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
                    content="""As a sentiment equity analyst your primary responsibility 
                    is to analyze the financial news; and analyze its implication and 
                    sentiment for investors. 
                    You will be provided with pre-processed news with pre-calculated 
                    sentiment scores for a set of TICKERS.
                    You must assign a BUY, SELL, or HOLD recommendation for EACH ticker 
                    providedwith justification based on the analysis of the data provided.
                    """
                ),
                HumanMessage(content=tool_output_all),
                HumanMessage(content=tool_output_summary),
            ]
        )

        logger.info("News/Sentiment Agent Answered!")

        return {"news_recommendation": msg}


    def Fundamental_Quality_Agent(self, state: State):
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

        # Run the fundamental agent tool to get fundamental scores
        tool_output = run_fundamental_agent_tool(
            tickers=state['tickers'],
            report_period_lte=state['today_date'],
            report_period_gte=state['as_of_date']
        )

        # Convert JSON output to string so it can be read by the LLM
        if not isinstance(tool_output, str):
            tool_output = json.dumps(tool_output)

        # Augment the LLM with structured output to ensure consistent formatting
        llm_structured_output = self.llm.with_structured_output(Recommendation)

        # Ask the LLM to provide recommendations based on the fundamental scores
        msg = llm_structured_output.invoke(
            [
                SystemMessage(
                    content="""As a fundamental financial equity analyst your primary 
                    responsibility is to analyze the most recent fundamental data provided 
                    for a provided set of TICKERS.
                    Your analysis should be based solely on the information that you have 
                    been given which aims to capture QUALITY companies.
                    A quality company is one that is able to consistently generate
                    strong earnings and cash flow growth, maintain high returns on invested 
                    capital, and sustain a healthy balance sheet with manageable levels of debt. 
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

        return {"fundamental_recommendation": msg}


    def Coordinator(self, state: State):
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
                    content=f"""You are a senior equity analyst.
                    Your task is to aggregate the recommendations from three different
                    analysts into a single, coherent recommendation for EACH ticker provided.
                    You have been provided with three distinct recommendations,
                    each accompanied by a justification. 
                    Your goal is to synthesize these inputs into one unified recommendation 
                    that reflects the collective insights of the individual analysts.
                    You MUST follow the following analyst voting system for your final 
                    recommendation:
                    3 x BUY = BUY
                    2 x BUY + 1 x HOLD = Use Judgement
                    2 x BUY + 1 x SELL = HOLD
                    3 x HOLD = HOLD
                    2 x HOLD + 1 x BUY = HOLD
                    2 x HOLD + 1 x SELL = SELL
                    3 x SELL = SELL
                    2 x SELL + 1 x BUY = HOLD
                    2 x SELL + 1 x HOLD = Use Judgement
                    'Use Judgement' means you must consider the reasoning behind each 
                    recommendation and weigh their arguments based on each analyst's 
                    conviction to arrive at a final decision.
                    You must use the information provided and do NOT USE any knowledge 
                    you have after {state['today_date']}. I repeat you MUST NOT use any 
                    knowledge or information after {state['today_date']}.
                    Your final output should be a single recommendation of either
                    BUY, SELL, or HOLD, along with a comprehensive justification
                    that encapsulates the key points from the three provided analyses.
                    """
                ),
                HumanMessage(content=state['valuation_recommendation'].model_dump_json()),
                HumanMessage(content=state['news_recommendation'].model_dump_json()),
                HumanMessage(content=state['fundamental_recommendation'].model_dump_json())
            ]
        )

        logger.info("Coordinator Agent Has Reached Consensus!")

        return {"coordinator_output": msg}

    def build_graph(self):
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