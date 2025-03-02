from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

def scrape_ipl_results(url):
    # Set up Selenium WebDriver
    service = Service(executable_path=r"C:\Users\rishi\Downloads\chromedriver-win64 (2)\chromedriver-win64\chromedriver.exe")  # Verify this path
    driver = webdriver.Chrome(service=service)

    try:
        # Fetch the webpage
        driver.get(url)
        print("Page loaded. Waiting for match content...")
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "ds-flex"))
        )

        # Get the full rendered HTML
        html_content = driver.page_source
        with open("page_source.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("HTML saved to 'page_source.html'")

        # Parse the HTML content
        soup = BeautifulSoup(html_content, "html.parser")

        # Find match result blocks (using ds-p-4 as found)
        match_blocks = soup.find_all("div", class_=lambda x: x and 'ds-p-4' in x)

        # Debugging
        if not match_blocks:
            print("No match blocks found with 'ds-p-4'.")
            print("Snippet of HTML for inspection:")
            print(soup.prettify()[:2000])
            return
        else:
            print(f"Found {len(match_blocks)} potential match blocks with 'ds-p-4':")
            for block in match_blocks[:5]:
                print(block.get('class'))
            # Print content of first few blocks for inspection
            print("\nSample match block content:")
            for block in match_blocks[:3]:
                print(block.prettify()[:500])  # Limit output for readability

        # Extract data
        data = []
        for block in match_blocks:
            try:
                # Match info (adjust based on inspection)
                match_info_elem = block.find("div", class_="ds-text-tight-xs ds-truncate ds-text-typo-mid3 ds-mb-2") or \
                                 block.find("span", class_="ds-text-tight-xs")
                match_info = match_info_elem.text.strip() if match_info_elem else "N/A"

                # Team names
                teams = block.find_all("p", class_=["ds-text-tight-s ds-font-bold ds-capitalize ds-truncate",
                                                  "ds-text-tight-m ds-font-bold ds-capitalize ds-truncate"])
                team1 = teams[0].text.strip() if teams else "N/A"
                team2 = teams[1].text.strip() if len(teams) > 1 else "N/A"

                # Scores
                scores = block.find_all("strong")
                team1_score = scores[0].text.strip() if scores else "N/A"
                team2_score = scores[1].text.strip() if len(scores) > 1 else "N/A"

                # Result
                result_elem = block.find("p", class_="ds-text-tight-s ds-font-medium ds-truncate ds-text-typo")
                result = result_elem.text.strip() if result_elem else "N/A"

                data.append({
                    "Match Info": match_info,
                    "Team 1": team1,
                    "Team 2": team2,
                    "Team 1 Score": team1_score,
                    "Team 2 Score": team2_score,
                    "Result": result
                })
            except Exception as e:
                print(f"Error processing a match block: {e}")
                continue

        # Save to CSV with error handling
        if data:
            df = pd.DataFrame(data)
            try:
                df.to_csv("ipl_2020_results.csv", index=False)
                print("Data scraped and saved to 'ipl_2020_results.csv'")
                print(df.head())
            except PermissionError:
                alt_path = "ipl_2020_results_alt.csv"
                df.to_csv(alt_path, index=False)
                print(f"Permission denied for 'ipl_2020_results.csv'. Saved to '{alt_path}' instead.")
                print(df.head())
        else:
            print("No data extracted.")

    except Exception as e:
        print(f"Error during scraping: {e}")
    finally:
        driver.quit()

# URL for IPL 2020/21 match results
url = "https://www.espncricinfo.com/series/ipl-2020-21-1210595/match-results"

# Call the function
scrape_ipl_results(url)