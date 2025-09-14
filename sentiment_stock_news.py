# %%
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_headline_sentiment(text: str) -> dict:
    logger.debug(f"Analyzing sentiment for text: {text}")   
    analyzer = SentimentIntensityAnalyzer()
    score = analyzer.polarity_scores(text)
    logger.debug(f"Sentiment score for text: {score}")   
    return score


# from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# model_name = "ProsusAI/finbert"
# tokenizer = AutoTokenizer.from_pretrained(model_name)
# model = AutoModelForSequenceClassification.from_pretrained(model_name)

# # Create sentiment analysis pipeline
# finbert = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# headlines = [
#     "Apple reports record quarterly earnings",
#     "Tesla stock plunges after disappointing delivery numbers",
#     "Federal Reserve hints at interest rate hike"
# ]

# results = finbert(headlines)
# for headline, sentiment in zip(headlines, results):
#     print(f"{headline} → {sentiment['label']} ({sentiment['score']:.2f})")
