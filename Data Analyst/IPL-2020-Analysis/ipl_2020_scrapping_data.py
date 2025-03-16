# Standard library imports
import time
import random
import traceback
import os
import csv
from datetime import datetime

# Third-party imports
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from googleapiclient.discovery import build
import praw

# Constants
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.6943.142 Safari/537.36"
}

# API Credentials (Replace with your own)
YOUTUBE_API_KEY = "AIzaSyCKo47rqEf-yVwgL-b8geS7xSBAY4Vo-NQ" 
REDDIT_CLIENT_ID = "lGrgvHO5nw_yVaiHPF20lA" 
REDDIT_CLIENT_SECRET = "ydWjmQ0UAJK3zsYYREWMzuDCqpIUOA" 
REDDIT_USER_AGENT = "python:IPL2020Scraper:1.0 (by u/Jumpy_Outcome8485)"  

# URLs
REDIFF_URL = "https://www.rediff.com/cricket/special/ipl2020-poll-who-will-win-ipl-2020/20200918.htm"
CRICBUZZ_URL = "https://www.cricbuzz.com/cricket-series/3130/indian-premier-league-2020/points-table"
IPLT20_URL = "https://www.iplt20.com/stats/2020"
YOUTUBE_PLAYLIST_ID = "PLwCtun-cAHbNgFby9WuKkCzT9RDeT9YxG"
REDDIT_QUERY = "IPL 2020"
NDTV_URL = "https://sports.ndtv.com/ipl-2020/stats"

# -----------------------------------
# Initialize driver functions
# -----------------------------------
def init_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument(f'--user-agent={HEADERS["User-Agent"]}')
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(30)
        return driver
    except Exception as e:
        print(f"Error initializing Chrome driver: {str(e)}")
        return None

# -----------------------------------
# Scraping Functions
# -----------------------------------

# 1. Rediff IPL 2020 Poll
def scrape_rediff_ipl2020():
    print("Scraping Rediff IPL 2020 poll...")
    driver = init_driver()
    if not driver:
        return
    
    try:
        driver.get(REDIFF_URL)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Extract title
        title = soup.find("h1")
        title_text = title.get_text(strip=True) if title else "No title found"
        
        # IPL 2020-specific keywords and teams
        ipl_keywords = ["IPL 2020", "IPL", "2020", "season", "UAE", "September 19"]
        ipl_teams = [
            "Mumbai Indians", "Chennai Super Kings", "Delhi Capitals", "Sunrisers Hyderabad",
            "Royal Challengers Bangalore", "Kolkata Knight Riders", "Kings XI Punjab", "Rajasthan Royals"
        ]
        
        # Extract IPL 2020-related content
        paragraphs = soup.find_all("p")
        article_text = []
        teams_mentioned = []
        
        for p in paragraphs:
            text = p.get_text(strip=True)
            if (any(keyword in text for keyword in ipl_keywords) or 
                any(team in text for team in ipl_teams)) and len(text) > 20:
                article_text.append(text)
                for team in ipl_teams:
                    if team in text and team not in teams_mentioned:
                        teams_mentioned.append(team)
        
        article_content = "\n".join(article_text) if article_text else "No IPL 2020-related content found"
        
        print(f"Article Title: {title_text}")
        print("\nIPL 2020-Related Content:\n", article_content)
        print("\nIPL Teams Mentioned:")
        for team in teams_mentioned:
            print(f"- {team}")
        
        # Save to CSV
        data = {
            "Title": [title_text],
            "IPL 2020 Content": [article_content],
            "Teams Mentioned": [", ".join(teams_mentioned)]
        }
        df = pd.DataFrame(data)
        df.to_csv("rediff_ipl_2020_content.csv", index=False)
        print("\nData saved to rediff_ipl_2020_content.csv")
    
    except Exception as e:
        print(f"Error scraping Rediff: {e}")
    finally:
        driver.quit()

# 2. Cricbuzz Points Table
def scrape_cricbuzz_points():
    print("Scraping Cricbuzz points table...")
    driver = init_driver()
    if not driver:
        return
    
    try:
        driver.get(CRICBUZZ_URL)
        wait = WebDriverWait(driver, 20)
        table_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table.cb-srs-pnts")))
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.select_one("table.cb-srs-pnts")
        if not table:
            raise Exception("Points table not found")
        
        headers = [th.get_text(strip=True) for th in table.find('tr').find_all(['th', 'td'])][:8]
        rows = [[td.get_text(strip=True) for td in tr.find_all('td')][:8] for tr in table.find_all('tr')[1:] if tr.find_all('td')]
        
        df = pd.DataFrame(rows, columns=headers)
        df = df.replace('', pd.NA).dropna(how='all')
        
        print(f"Successfully scraped points table with {len(df)} rows")
        df.to_csv('cricbuzz_points_table.csv', index=False)
        print("Data saved to cricbuzz_points_table.csv")
    
    except Exception as e:
        print(f"Error scraping Cricbuzz: {e}")
        traceback.print_exc()
    finally:
        driver.quit()

# 3. IPLT20 Stats
def scrape_iplt20_stats():
    print("Scraping IPLT20 stats...")
    driver = init_driver(headless=False)  # Non-headless for tab interaction
    if not driver:
        return
    
    folder_name = "ipl_stats_2020_temp"
    try:
        driver.get(IPLT20_URL)
        time.sleep(5)
        
        def extract_table_data():
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            tables = soup.find_all("table")
            return [[col.text.strip() for col in row.find_all(["td", "th"])] for table in tables for row in table.find_all("tr")] if tables else None
        
        def save_to_csv(data, tab_name):
            if not data:
                return []
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            filename = f"{folder_name}/{tab_name}_table.csv"
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(data)
            return [filename]
        
        # Scrape Season tab
        season_data = extract_table_data()
        season_files = save_to_csv(season_data, "season")
        
        # Switch to Records tab
        records_tab = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Records')]"))
        )
        driver.execute_script("arguments[0].click();", records_tab)
        time.sleep(5)
        records_data = extract_table_data()
        records_files = save_to_csv(records_data, "records")
        
        # Merge CSV files
        csv_files = season_files + (records_files if 'records_files' in locals() else [])
        if csv_files:
            dfs = [pd.read_csv(f) for f in csv_files]
            merged_df = pd.concat(dfs, ignore_index=True)
            merged_df.to_csv("ipl_stats_2020_merged.csv", index=False)
            print("Merged data saved to ipl_stats_2020_merged.csv")
            for f in csv_files:
                os.remove(f)
            if not os.listdir(folder_name):
                os.rmdir(folder_name)
    
    except Exception as e:
        print(f"Error scraping IPLT20: {e}")
    finally:
        driver.quit()

# 4. YouTube Playlist
def scrape_youtube_playlist():
    print("Scraping YouTube playlist...")
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    
    def get_playlist_videos(playlist_id):
        videos = []
        next_page_token = None
        while True:
            request = youtube.playlistItems().list(
                part="snippet", playlistId=playlist_id, maxResults=50, pageToken=next_page_token
            )
            response = request.execute()
            for item in response["items"]:
                videos.append({
                    "title": item["snippet"]["title"],
                    "video_id": item["snippet"]["resourceId"]["videoId"]
                })
            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
        return videos
    
    def get_video_comments(video_id):
        comments = []
        next_page_token = None
        while True:
            try:
                request = youtube.commentThreads().list(
                    part="snippet", videoId=video_id, maxResults=100, pageToken=next_page_token
                )
                response = request.execute()
                for item in response["items"]:
                    comments.append(item["snippet"]["topLevelComment"]["snippet"]["textOriginal"])
                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            except Exception as e:
                print(f"Error fetching comments for {video_id}: {e}")
                break
        return comments
    
    video_list = get_playlist_videos(YOUTUBE_PLAYLIST_ID)
    print(f"Found {len(video_list)} videos in the playlist.")
    
    all_data = []
    for video in video_list:
        video["comments"] = get_video_comments(video["video_id"])
        all_data.append(video)
        print(f"Scraped {len(video['comments'])} comments for: {video['title']}")
    
    df = pd.DataFrame(all_data)
    df.to_csv("youtube_playlist_data.csv", index=False)
    print("Data saved to youtube_playlist_data.csv")

# 5. Reddit Expert Opinions
def scrape_reddit_expert_opinions():
    print("Scraping Reddit expert opinions...")
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    
    posts_data = []
    search_results = reddit.subreddit("all").search(REDDIT_QUERY, limit=100)
    
    for submission in search_results:
        post_data = {
            "title": submission.title,
            "selftext": submission.selftext if submission.selftext else "N/A",
            "score": submission.score,
            "comments": []
        }
        submission.comments.replace_more(limit=0)
        for comment in submission.comments.list():
            if len(comment.body) > 100 or any(char.isdigit() for char in comment.body):
                post_data["comments"].append({
                    "author": comment.author.name if comment.author else "[deleted]",
                    "text": comment.body,
                    "score": comment.score
                })
        if post_data["comments"]:
            posts_data.append(post_data)
    
    print(f"Found {len(posts_data)} posts with potential expert comments for '{REDDIT_QUERY}'.")
    
    flattened_data = []
    for post in posts_data:
        flattened_data.append({"type": "post", "title": post["title"], "score": post["score"], "comment_text": "N/A"})
        for comment in post["comments"]:
            flattened_data.append({"type": "comment", "title": post["title"], "score": post["score"], "comment_text": comment["text"]})
    
    df = pd.DataFrame(flattened_data)
    df.to_csv("reddit_ipl_2020_expert_opinions.csv", index=False)
    print("Data saved to reddit_ipl_2020_expert_opinions.csv")

# 6. NDTV Sports Stats (Updated to Combine Files)
def scrape_ndtv_sports():
    print("Scraping NDTV Sports stats...")
    driver = init_driver(headless=False)
    if not driver:
        return
    
    def table_to_df(table):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        rows = [[td.get_text(strip=True) for td in tr.find_all("td")] for tr in table.find_all("tr")[1:] if tr.find_all("td")]
        return pd.DataFrame(rows, columns=headers) if rows else None
    
    def combine_and_clean_csv_files(tab):
        csv_files = [f for f in os.listdir() if f.startswith(f"ndtv_{tab.lower()}_") and f.endswith(".csv")]
        if not csv_files:
            print(f"No CSV files found for {tab} to combine.")
            return
        
        combined_df = pd.DataFrame()
        for csv_file in csv_files:
            df = pd.read_csv(csv_file)
            table_name = csv_file.replace(f"ndtv_{tab.lower()}_", "").replace(".csv", "").replace("_", " ").title()
            df["Table"] = table_name  # Add a column to identify the source table
            combined_df = pd.concat([combined_df, df], ignore_index=True)
        
        output_file = f"ndtv_sports_{tab.lower()}.csv"
        combined_df.to_csv(output_file, index=False)
        print(f"Combined {len(csv_files)} {tab} files into {output_file}")
        
        # Delete individual CSV files
        for csv_file in csv_files:
            os.remove(csv_file)
            print(f"Deleted {csv_file}")
    
    try:
        driver.get(NDTV_URL)
        wait = WebDriverWait(driver, 30)
        
        tabs = ["Batting", "Bowling", "Fielding", "Team"]
        all_tables = {tab: {} for tab in tabs}
        
        for tab in tabs:
            tab_link = wait.until(EC.presence_of_element_located((By.XPATH, f"//a[@data-id='{tab}']")))
            driver.execute_script("arguments[0].click();", tab_link)
            print(f"Clicked {tab} tab.")
            time.sleep(5)
            
            soup = BeautifulSoup(driver.page_source, "html.parser")
            tab_div = soup.find("div", class_=f"stats-listing {tab}") or soup.find("div", class_=lambda x: x and "stats-listing" in x)
            if tab_div:
                tables = tab_div.find_all("table", class_="sts_tbl")
                print(f"Found {len(tables)} tables in {tab} tab.")
                for i, table in enumerate(tables):
                    title_elem = table.find_previous("h3", class_="sts_dtl-ttl")
                    title = title_elem.find("span").get_text(strip=True) if title_elem else f"{tab} Table {i+1}"
                    df = table_to_df(table)
                    if df is not None:
                        filename = f"ndtv_{tab.lower()}_{title.lower().replace(' ', '_')}.csv"
                        df.to_csv(filename, index=False)
                        print(f"Saved {filename}")
            else:
                print(f"No stats div found for {tab} tab.")
            
            # Combine and clean up files for this tab
            combine_and_clean_csv_files(tab)
    
    except Exception as e:
        print(f"Error scraping NDTV: {e}")
    finally:
        driver.quit()

# -----------------------------------
# Main execution
# -----------------------------------
def main():
    print("Starting IPL 2020 data scraping...")
    
    # Uncomment the scrapers you want to run
    scrape_rediff_ipl2020()
    scrape_cricbuzz_points()
    scrape_iplt20_stats()
    scrape_youtube_playlist()
    scrape_reddit_expert_opinions()
    scrape_ndtv_sports()
    
    print("Scraping completed. Check CSV files for results.")

if __name__ == "__main__":
    main()