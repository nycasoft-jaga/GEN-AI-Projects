import pandas as pd
from textblob import TextBlob

# Load tweets dataset
tweets_df = pd.read_csv("ipl_tweets_v2.csv")

# Function to get sentiment polarity
def get_sentiment(text):
    return TextBlob(text).sentiment.polarity

# Apply sentiment analysis
tweets_df["Sentiment_Score"] = tweets_df["Tweet"].apply(get_sentiment)

# Categorize sentiment as Positive, Neutral, or Negative
tweets_df["Sentiment"] = tweets_df["Sentiment_Score"].apply(lambda x: "Positive" if x > 0 else ("Negative" if x < 0 else "Neutral"))

# Display results
print(tweets_df[["Tweet", "Sentiment_Score", "Sentiment"]].head())

# Save the results to a new CSV file
tweets_df.to_csv("tweets_sentiment_analysis.csv", index=True)
