import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time

# Headers to mimic browser
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}

# Initialize Selenium driver
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in background
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

# 1. Cricbuzz - Points Table
def scrape_cricbuzz():
    url = "https://www.cricbuzz.com/cricket-series/3130/indian-premier-league-2020/points-table"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the points table
        table = soup.find('table', class_='table cb-srs-pnts')
        if not table:
            print("Cricbuzz: Points table not found.")
            return
        
        # Debug: Print raw table HTML to inspect structure
        print("Cricbuzz: Raw table HTML sample:")
        print(table.prettify()[:500])  # First 500 chars for inspection
        
        rows = table.find_all('tr')
        data = []
        for row in rows[1:]:  # Skip header
            cols = row.find_all('td')[:8]
            # Filter out nested elements and keep only main data
            team_data = [col.text.strip() for col in cols if col.text.strip()]  # Ignore empty cells
            data.append(team_data)
        
        if not data:
            print("Cricbuzz: No data extracted from table.")
            return
        
        # Dynamically assign column names based on first row length
        num_cols = len(data[0])
        print(f"Cricbuzz: Number of columns detected: {num_cols}")
        print(f"Cricbuzz: Raw data sample: {data[0]}")  # Debug output
        
        columns = [f"Col_{i+1}" for i in range(num_cols)]
        df = pd.DataFrame(data, columns=columns)
        df.to_csv('cricbuzz_ipl2020_points.csv', index=False)
        print("Cricbuzz: Points table scraped successfully.")
        
    except Exception as e:
        print(f"Cricbuzz: Error - {e}")

# 2. ESPNcricinfo - Batting Stats
def scrape_espncricinfo():
    url = "https://www.espncricinfo.com/records/tournament/batting-most-runs-career/indian-premier-league-2020-21-13533"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        table = soup.find('table', class_='ds-table')
        if not table:
            print("ESPNcricinfo: Stats table not found.")
            return
        
        rows = table.find_all('tr')
        data = []
        for row in rows[1:]:  # Skip header
            cols = row.find_all('td')
            if len(cols) > 1:
                player_data = [col.text.strip() for col in cols]
                data.append(player_data)
        
        num_cols = len(data[0])
        columns = [f"Col_{i+1}" for i in range(num_cols)]
        df = pd.DataFrame(data, columns=columns)
        df.to_csv('espncricinfo_ipl2020_batting.csv', index=False)
        print("ESPNcricinfo: Batting stats scraped successfully.")
        print(f"Raw data sample: {data[0]}")
    except Exception as e:
        print(f"ESPNcricinfo: Error - {e}")

# 3. IPLT20.com - Points Table (Selenium)
def scrape_iplt20(driver):
    url = "https://www.iplt20.com/points-table/men/2020"
    try:
        driver.get(url)
        driver.implicitly_wait(10)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table', class_='ih-td-tab')
        if not table:
            print("IPLT20: Points table not found.")
            return
        
        rows = table.find_all('tr')
        data = []
        for row in rows[1:]:  # Skip header
            cols = row.find_all('td')
            team_data = [col.text.strip() for col in cols]
            data.append(team_data)
        
        num_cols = len(data[0])
        columns = [f"Col_{i+1}" for i in range(num_cols)]
        df = pd.DataFrame(data, columns=columns)
        df.to_csv('iplt20_ipl2020_points.csv', index=False)
        print("IPLT20: Points table scraped successfully.")
        print(f"Raw data sample: {data[0]}")
    except Exception as e:
        print(f"IPLT20: Error - {e}")

# Main execution
def main():
    print("Starting web scraping for IPL 2020 data...")
    
    driver = init_driver()
    
    scrape_cricbuzz()
    time.sleep(2)
    scrape_espncricinfo()
    time.sleep(2)
    scrape_iplt20(driver)
    time.sleep(2)
    
    driver.quit()
    print("Scraping completed. Check CSV files for results.")

if __name__ == "__main__":
    main()