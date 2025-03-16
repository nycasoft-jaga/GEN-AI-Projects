import pandas as pd
from textblob import TextBlob
import re

# Team mapping for standardization
team_mapping = {
    'DC': 'Delhi Capitals', 'MI': 'Mumbai Indians', 'PBKS': 'Kings XI Punjab',
    'RR': 'Rajasthan Royals', 'RCB': 'Royal Challengers Bangalore', 
    'SRH': 'Sunrisers Hyderabad', 'CSK': 'Chennai Super Kings', 'KKR': 'Kolkata Knight Riders'
}

# Step 1: Compile Stats from Batting Files
def compile_batting_stats():
    # Load all batting CSVs
    files = ['ndtv_sports_batting.csv', 'ndtv_sports_bowling.csv', 'ndtv_sports_fielding.csv', 'ndtv_sports_team.csv']
    dfs = [pd.read_csv(f) for f in files]
    
    # Standardize column names across files (some variation in order)
    for df in dfs:
        df.columns = df.columns.str.lower().str.strip()  # Normalize column names
    
    # Combine all data
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Extract team from player name and clean it
    combined_df['Team'] = combined_df['player'].str.extract(r'([A-Z]{2,4})$', expand=False).map(team_mapping)
    combined_df['Player'] = combined_df['player'].str.replace(r'([A-Z]{2,4})$', '', regex=True).str.strip()
    
    # Clean 'score' (highest score) and convert to numeric
    combined_df['score'] = combined_df['score'].str.replace(r'\*', '', regex=True).astype(float, errors='ignore')
    
    # Convert metrics to numeric, filling NaN with 0 where appropriate
    numeric_cols = ['runs', 'sr', 'avg', '4s', '6s', '50s', '100s', '0s', 'score']
    for col in numeric_cols:
        combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce').fillna(0)
    
    # Drop duplicates (same player, same metric) and irrelevant columns
    compiled_stats = combined_df.drop(columns=['no.', 'table']).drop_duplicates(subset=['Player', 'Team'])
    
    # Aggregate stats per player (e.g., max values for each metric)
    compiled_stats = compiled_stats.groupby(['Player', 'Team']).agg({
        'runs': 'max', 'sr': 'max', 'avg': 'max', '4s': 'max', '6s': 'max',
        '50s': 'max', '100s': 'max', '0s': 'max', 'score': 'max'
    }).reset_index()
    
    # Save to CSV
    compiled_stats.to_csv('ndtv_sports_cleaned_data_stats.csv', index=False)
    print("Compiled NDTV Sports stats saved to 'ndtv_sports_cleaned_data_stats.csv'")
    print(compiled_stats.head())

# Step 2: Aggregate Fan Opinions
def aggregate_fan_opinions():
    # Load opinions CSV
    opinions = pd.read_csv('reddit_ipl_2020_expert_opinions.csv')
    
    # Define team keywords
    teams = {
        'Mumbai Indians': ['mumbai indians', 'mi', 'rohit sharma', 'pollard'],
        'Delhi Capitals': ['delhi capitals', 'dc', 'shikhar dhawan'],
        'Kings XI Punjab': ['kings xi punjab', 'kxip', 'kl rahul', 'punjab'],
        'Rajasthan Royals': ['rajasthan royals', 'rr', 'ben stokes'],
        'Royal Challengers Bangalore': ['royal challengers bangalore', 'rcb', 'virat kohli', 'kohli'],
        'Sunrisers Hyderabad': ['sunrisers hyderabad', 'srh', 'david warner'],
        'Chennai Super Kings': ['chennai super kings', 'csk', 'ms dhoni', 'dhoni'],
        'Kolkata Knight Riders': ['kolkata knight riders', 'kkr', 'dinesh karthik']
    }
    
    # Sentiment analysis function
    def categorize_sentiment(text):
        if pd.isna(text) or text == 'N/A':
            return 'neutral'
        blob = TextBlob(str(text))
        polarity = blob.sentiment.polarity
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    # Categorize sentiment and assign teams
    opinions['Sentiment'] = opinions['comment_text'].apply(categorize_sentiment)
    opinions['Team'] = 'Unknown'
    
    for team, keywords in teams.items():
        pattern = '|'.join(keywords)
        mask = opinions['comment_text'].str.lower().str.contains(pattern, na=False)
        opinions.loc[mask, 'Team'] = team
    
    # Filter out noise (comments not about IPL teams)
    opinions_cleaned = opinions[opinions['Team'] != 'Unknown']
    
    # Aggregate by team and sentiment
    sentiment_summary = opinions_cleaned.groupby(['Team', 'Sentiment']).size().unstack(fill_value=0)
    sentiment_summary.to_csv('expert_opinions_cleaned_data_summary.csv')
    print("Fan opinions summary saved to 'expert_opinions_cleaned_data_summary.csv'")
    print(sentiment_summary)

# Step 3: Standardize Metrics (already handled in compile_batting_stats)
# Step 4: Filter Noise (handled in both functions)

# Main execution
def main():
    print("Starting data cleaning...")
    compile_batting_stats()
    aggregate_fan_opinions()
    print("Data cleaning completed.")

if __name__ == "__main__":
    main()