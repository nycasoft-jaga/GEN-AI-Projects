# IPL 2020 Analysis

## Project Overview

Cricket is a cornerstone of Indian culture, and the Indian Premier League (IPL) 2020, held in the UAE amidst a global pandemic, captivated fans with thrilling matches, including back-to-back super overs. This project aims to analyze the online chatter surrounding IPL 2020 by scraping and processing data from social media platforms, news portals, and cricket commentary sites. Our goal is to uncover trends, predict the tournament winner (or compare predictions with actual results if available), and perform in-depth sentiment and text analysis.

### Objective
- Track and analyze IPL 2020 discussions across social media (Twitter, Facebook, etc.), news sites, and forums.
- Scrape live commentary sites like Cricinfo and Cricbuzz to study trends and fan reactions.
- Predict the IPL 2020 winner based on social media and textual data, even if results are already out, and compare predictions with outcomes.
- Analyze media coverage and sentiment for your favorite IPL team at an aspect level (beyond just positive/negative/neutral).
- Leverage data visualization, statistical techniques, NLP, and topic modeling to derive insights.

---

## Instructions for Developers

### General Guidelines
- **Hands-On Work**: This is a collaborative project requiring active coding and analysis. Each team member must contribute to the codebase and final presentation.
- **Submission**: One codebase will be submitted as a group, accompanied by a group presentation on valuation day.
- **Data Sources**: You are not limited to provided sources—explore any relevant, publicly available datasets (e.g., tweets, news articles, Google Trends).

### Project Structure
Organize your repository as follows:
  IPL-2020-Analysis/
  ├── data/                  # Store raw and processed datasets (e.g., tweets, scraped articles)
  ├── scripts/              # Python/R scripts for scraping, analysis, and visualization
  │   ├── data_collection/  # Scripts for scraping and fetching data
  │   ├── analysis/         # Scripts for NLP, sentiment analysis, and statistics
  │   └── visualization/    # Scripts for generating charts and plots
  ├── docs/                 # Documentation (e.g., this README, additional notes)
  ├── output/               # Visualizations, prediction results, and reports
  └── README.md             # Project overview and instructions

To create subdirectories (e.g., `data_collection` inside `scripts`):
- On GitHub: Use the "Create new file" option and specify the path (e.g., `scripts/data_collection/scrape_twitter.py`).
- Locally: Use `mkdir -p scripts/data_collection`, add files, then commit and push.

### Setup Instructions
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/nycasoft-jaga/IPL-2020-Analysis.git
   cd IPL-2020-Analysis
   
2. **Install Dependencies**:
Ensure Python 3.x is installed.
Install required libraries (example, adjust as needed):
  ```bash
      pip install tweepy beautifulsoup4 requests pandas matplotlib seaborn nltk scikit-learn
  ```
3. **API Access:**
    - Twitter: Sign up for Twitter Developer access (Premium Sandbox is free with 50 requests/month, up to 5,000 tweets). See Twitter Premium API.
    - Store API keys in a .env file (not tracked by Git) and load them securely in scripts.
4. **Coding Standards:**
    - Use meaningful variable names and comments.
    - Modularize code (e.g., separate scraping, analysis, and visualization).

### Data Sources
- **Social Media**: Twitter, Facebook, Instagram, WhatsApp (if accessible).
- **Third-Party Sites**: Historical tweet archives (e.g., via Twitter API).
- **Google Trends**: Search trends for IPL matches.
- **News Portals**: NDTV, Star Sports, online archives.
- **Commentary Sites**: Cricbuzz, Cricinfo, www.iplt20.com.
