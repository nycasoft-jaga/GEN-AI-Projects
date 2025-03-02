

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load the match dataset
csv_path = r"C:\Users\rishi\Desktop\Twitter.api\deliveries.csv" # Update if needed
matches_df = pd.read_csv(csv_path)

# 🔍 Print available columns
print("Columns in dataset:", matches_df.columns)

# 🔹 1. Most Mentioned Teams (Batting & Bowling)
team_counts = matches_df['batting_team'].value_counts() + matches_df['bowling_team'].value_counts()

plt.figure(figsize=(10, 5))
sns.barplot(x=team_counts.index, y=team_counts.values, palette="coolwarm")
plt.xticks(rotation=45)
plt.xlabel("Teams")
plt.ylabel("Mentions (Batting + Bowling)")
plt.title("Most Mentioned Teams")
plt.show()

# 🔹 2. Top Batsmen by Total Runs
top_batsmen = matches_df.groupby("batsman")["batsman_runs"].sum().sort_values(ascending=False).head(10)

plt.figure(figsize=(10, 5))
sns.barplot(x=top_batsmen.index, y=top_batsmen.values, palette="magma")
plt.xticks(rotation=45)
plt.xlabel("Batsman")
plt.ylabel("Total Runs")
plt.title("Top 10 Batsmen by Runs")
plt.show()

# 🔹 3. Top Bowlers by Wickets Taken
wicket_data = matches_df.dropna(subset=['player_dismissed'])
top_bowlers = wicket_data["bowler"].value_counts().head(10)

plt.figure(figsize=(10, 5))
sns.barplot(x=top_bowlers.index, y=top_bowlers.values, palette="viridis")
plt.xticks(rotation=45)
plt.xlabel("Bowler")
plt.ylabel("Wickets Taken")
plt.title("Top 10 Bowlers by Wickets")
plt.show()

# 🔹 4. Runs Per Over Distribution
over_runs = matches_df.groupby("over")["total_runs"].sum()

plt.figure(figsize=(10, 5))
sns.lineplot(x=over_runs.index, y=over_runs.values, marker='o', color='red')
plt.xticks(range(1, 21))
plt.xlabel("Over Number")
plt.ylabel("Total Runs Scored")
plt.title("Total Runs Scored Per Over")
plt.grid(True)
plt.show()
