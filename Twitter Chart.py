import pandas as pd
from textblob import TextBlob
import matplotlib.pyplot as plt

# Load tweets dataset
tweets_df = pd.read_csv("ipl_tweets_v2.csv")

# Function to get sentiment polarity
def get_sentiment(text):
    return TextBlob(text).sentiment.polarity

# Apply sentiment analysis
tweets_df["Sentiment_Score"] = tweets_df["Tweet"].apply(get_sentiment)
tweets_df["Sentiment"] = tweets_df["Sentiment_Score"].apply(lambda x: "Positive" if x > 0 else ("Negative" if x < 0 else "Neutral"))

# Display sample results
print(tweets_df[["Tweet", "Sentiment_Score", "Sentiment"]].head())

# Function to identify team mentions in tweets (if no "Team" column exists)
teams = ['CSK', 'MI', 'KKR', 'RCB', 'DC', 'KXIP', 'RR', 'SRH']
def get_team(tweet):
    for team in teams:
        if team in tweet.upper():
            return team
    return None

# Add team column if not present
if "Team" not in tweets_df.columns:
    tweets_df["Team"] = tweets_df["Tweet"].apply(get_team)

# Drop rows with no team identified
tweets_df = tweets_df.dropna(subset=["Team"])

# Calculate average sentiment per team
team_sentiment = tweets_df.groupby("Team")["Sentiment_Score"].mean().reindex(teams, fill_value=0)

# Display team sentiment
print("\nAverage Sentiment Score per Team:")
print(team_sentiment)

# Save results
tweets_df.to_csv("tweets_sentiment_analysis.csv", index=False)

# Bar chart for team sentiment
plt.figure(figsize=(10, 6))
team_sentiment.plot(kind='bar', color='purple')
plt.title('Average Sentiment Score per Team (IPL 2020 Tweets)', fontsize=14)
plt.xlabel('Teams', fontsize=12)
plt.ylabel('Average Sentiment Score', fontsize=12)
plt.ylim(-1, 1)
for i, v in enumerate(team_sentiment):
    plt.text(i, v + 0.05 if v >= 0 else v - 0.1, f"{v:.2f}", ha='center', fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Save chart
plt.savefig('team_sentiment.png', dpi=300, bbox_inches='tight')
plt.close()
print("Chart saved as 'team_sentiment.png'")
