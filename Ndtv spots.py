from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_ipl_results(url):
    # Set up Selenium WebDriver
    service = Service(executable_path=r"C:\Users\rishi\Downloads\chromedriver-win64 (2)\chromedriver-win64\chromedriver.exe")  # Update with your ChromeDriver path
    driver = webdriver.Chrome(service=service)

    try:
        # Fetch the webpage
        driver.get(url)
        print("Page loaded. Waiting for match content...")
        # Wait for match blocks to appear
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "sp-scr_wrp"))
        )

        # Get the full rendered HTML
        html_content = driver.page_source
        with open("ipl_page_source.html", "w", encoding="utf-8") as f:
            f.write(html_content)  # Save for inspection
        print("HTML saved to 'ipl_page_source.html'")

        # Parse the HTML content
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all match result blocks
        match_blocks = soup.find_all("div", class_="sp-scr_wrp")

        # Debugging
        if not match_blocks:
            print("No match blocks found with class 'sp-scr_wrp'.")
            print("Snippet of HTML for inspection:")
            print(soup.prettify()[:2000])
            return
        else:
            print(f"Found {len(match_blocks)} match blocks.")

        # Extract data
        data = []
        for block in match_blocks:
            try:
                # Match info (date and details)
                date_elem = block.find_previous("h2", class_="scr-pag_ttl2 schedulecontainer")
                date = date_elem.text.strip() if date_elem else "N/A"
                details_elem = block.find("div", class_="scr_txt-ony")
                details = details_elem.text.strip() if details_elem else ""
                match_info = f"{date} - {details}" if details else date

                # Team names (from scr_tm-nm classes)
                team_elems = block.find_all("div", class_="scr_tm-nm")
                team1 = team_elems[0].text.strip() if team_elems else "N/A"
                team2 = team_elems[1].text.strip() if len(team_elems) > 1 else "N/A"

                # Scores (from scr_tm-run or scr_tm-scr spans)
                score_elems = block.find_all("span", class_=["scr_tm-run", "scr_tm-scr"])
                team1_score = score_elems[0].text.strip() if score_elems else "N/A"
                team2_score = score_elems[1].text.strip() if len(score_elems) > 1 else "N/A"

                # Result (from scr_dt-red or scr_inf-wrp)
                result_elem = block.find("div", class_="scr_dt-red")
                result = result_elem.text.strip() if result_elem else "N/A"

                # Append data
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

        # Save to CSV
        if data:
            df = pd.DataFrame(data)
            try:
                df.to_csv("ipl_2020_results.csv", index=False)
                print("Data scraped and saved to 'ipl_2020_results.csv'")
                print(df.head())  # Show first few rows
            except PermissionError as e:
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

# URL for IPL 2020 results
url = "https://sports.ndtv.com/ipl-2020/results"

# Call the function
scrape_ipl_results(url)