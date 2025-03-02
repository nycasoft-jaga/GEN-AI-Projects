import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load CSV file
csv_path = r"C:\Users\rishi\Desktop\Twitter.api\ipl_tweets_v2.csv"
tweets_df = pd.read_csv(csv_path)

# Convert 'Date' to datetime
tweets_df['Date'] = pd.to_datetime(tweets_df['Date'], errors='coerce')

# Group tweets by date
tweets_per_day = tweets_df.groupby(tweets_df['Date'].dt.date).size()

# Plot tweet trends
plt.figure(figsize=(12, 6))
sns.lineplot(x=tweets_per_day.index, y=tweets_per_day.values, marker='o')
plt.xticks(rotation=45)
plt.xlabel("Date")
plt.ylabel("Number of Tweets")
plt.title("IPL Tweet Trends Over Time")
plt.grid(True)

# Ensure plot displays
plt.show()
