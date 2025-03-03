import pandas as pd
import matplotlib.pyplot as plt
import re

# Sentiment analysis library
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# 1. Load the CSV file
df = pd.read_csv("ipl_tweets.csv")

# Quick check of the data
print("Data preview:")
print(df.head())
print("\nData info:")
print(df.info())

# 2. Data Cleaning
# Remove duplicates based on text (if you have multiple duplicates)
df.drop_duplicates(subset='text', inplace=True)

# Create a function to clean the tweet text
def clean_text(text):
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    # Remove mentions (e.g., @username)
    text = re.sub(r'@\w+', '', text)
    # Remove non-alphanumeric characters (except spaces)
    text = re.sub(r'[^A-Za-z0-9\s]+', '', text)
    # Convert to lowercase
    text = text.lower().strip()
    return text

# Apply the cleaning function
df['clean_text'] = df['text'].apply(clean_text)

# 3. Exploratory Data Analysis (EDA)
# For example, let's see how many tweets per user (just a quick check)
top_users = df['username'].value_counts().head(10)
print("\nTop 10 users by tweet count:")
print(top_users)

# Optional: Plot top users
plt.figure(figsize=(8, 5))
top_users.plot(kind='bar')
plt.title("Top 10 Users by Tweet Count")
plt.xlabel("Username")
plt.ylabel("Number of Tweets")
plt.tight_layout()
plt.show()

# 4. Sentiment Analysis with VADER
analyzer = SentimentIntensityAnalyzer()

def get_sentiment_score(text):
    scores = analyzer.polarity_scores(text)
    return scores['compound']

# Apply sentiment analysis
df['sentiment_score'] = df['clean_text'].apply(get_sentiment_score)

# Classify into Positive, Negative, Neutral
def classify_sentiment(score):
    if score >= 0.05:
        return 'Positive'
    elif score <= -0.05:
        return 'Negative'
    else:
        return 'Neutral'

df['sentiment'] = df['sentiment_score'].apply(classify_sentiment)

# Check sentiment distribution
sentiment_counts = df['sentiment'].value_counts()
print("\nSentiment distribution:")
print(sentiment_counts)

# Plot the sentiment distribution
plt.figure(figsize=(6, 4))
sentiment_counts.plot(kind='bar', color=['green', 'red', 'blue'])
plt.title("Sentiment Distribution of IPL Tweets")
plt.xlabel("Sentiment")
plt.ylabel("Number of Tweets")
plt.tight_layout()
plt.show()

# 5. (Optional) Time-Series Analysis
# If 'created_at' column exists, convert to datetime and analyze trends over time
if 'created_at' in df.columns:
    # Convert created_at to datetime if not already
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    
    # Drop any rows with invalid dates
    df.dropna(subset=['created_at'], inplace=True)
    
    # Group by date
    daily_counts = df.groupby(df['created_at'].dt.date).size()
    
    plt.figure(figsize=(10, 5))
    plt.plot(daily_counts.index, daily_counts.values, marker='o')
    plt.title("Number of IPL Tweets Over Time")
    plt.xlabel("Date")
    plt.ylabel("Tweet Count")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

print("\nAnalysis complete! Check out the plots and data above.")
