import pandas as pd
from tqdm import tqdm
import re

# Enable progress_apply
tqdm.pandas()

# Load your DataFrame (modify this according to your actual data source)
# Example: If you're loading from a CSV file
tweets_df = pd.read_csv(r"C:\Users\rishi\Desktop\Twitter.api\deliveries.csv")  # Update with your actual file path

# Check if the 'tweet' column exists
if 'tweet' not in tweets_df.columns:
    print("Error: 'tweet' column not found in DataFrame. Available columns:", tweets_df.columns)
else:
    # Define the text cleaning function
    def clean_text(text):
        text = text.lower()  # Convert text to lowercase
        text = re.sub(r'http\S+', '', text)  # Remove URLs
        text = re.sub(r'@\w+', '', text)  # Remove mentions
        text = re.sub(r'#\w+', '', text)  # Remove hashtags
        text = re.sub(r'[^a-zA-Z\s]', '', text)  # Remove special characters
        text = re.sub(r'\s+', ' ', text).strip()  # Remove extra whitespace
        return text
    
    # Apply the function only if the column exists
    tweets_df['clean_text'] = tweets_df['tweet'].progress_apply(clean_text)

# Print the first few rows to check
print(tweets_df.head())  # Change the number to display more rows if needed
