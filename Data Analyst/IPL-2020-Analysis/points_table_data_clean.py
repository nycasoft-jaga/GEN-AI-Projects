import pandas as pd

# Load the points table from a CSV file
points_table = pd.read_csv('ipl_2020_points_table.csv')

# Display the first few rows to inspect the data
print("Initial Data:")
print(points_table.head())

# Check for missing values
print("\nMissing Values:")
print(points_table.isnull().sum())

# Convert 'Points' column to numeric, handling any errors
points_table['Points'] = pd.to_numeric(points_table['Points'], errors='coerce')

# Drop rows with missing critical data (e.g., Points or Team)
points_table.dropna(subset=['Team', 'Points'], inplace=True)

# Remove duplicates, if any
points_table.drop_duplicates(inplace=True)

# Display cleaned data
print("\nCleaned Data:")
print(points_table.head())