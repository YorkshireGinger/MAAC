# MAAC
Multi Agent Alpha Copilot (MAAC) is an AI agentic framework to enhance the efficiency of active investor workflows. 

## Data collection

I have pre-ran the sentiment snd will not let this run for your runtime as it takes too long to pip install whcih goes against the brief of being quick and simple. Here you could use uv. 

I have actually used VADER as it was quicker to install, though may misjudge thr sentiment of finance jargon. Nevertheless, for headlines and short snippets, in addiiton to this being a PoC, it will do. These are thresholds recomended by the creators.


Sentiment	Compound Score Range
Positive	≥ 0.05
Neutral	> –0.05 and < 0.05
Negative	≤ –0.05


Model	Speed	Accuracy	Domain-Specific	Best For
FinBERT	Medium	High	✅ Yes	Deep financial analysis
VADER	Fast	Medium	❌ No	Quick scans, social media
BERT + FPB	Medium	High	✅ Yes	Headlines, reports
SVM + TF-IDF	Fast	Medium	❌ No	Custom, interpretable

to collect the news I have used the news endpoint with the api. They have their own sentiment but I have ran my own for robustness. They only provide headline and link to the story, so this time I have just manully extracted the key points. With more time you could automate this. 

ideas for fundamental/quality 
forward p/e
div yield
free cash flow |(consistent growth)
roic
roce 
roe (consistent)
d/e
current ratio
earnings/fcf
earnings quality
capex/assets or revenues


## Where did I use a copilot
`sentiment_stock_news` all of it. I had heard of FinBERT but didn't know how to code it up.
the creation of fake news healdines and snippets
the packaging of code into fucntions once tested
