from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import random

# Setup Chrome options
options = Options()
options.add_argument("--headless")  
options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT {random.randint(6,10)}.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90,110)}.0.4472.{random.randint(100,999)} Safari/537.36")
options.add_argument("--disable-blink-features=AutomationControlled")

# Start WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("https://www.espncricinfo.com/story/mumbai-indians-vs-delhi-capitals-ipl-2020-final-fantasy-pick-team-predictions-1238801")

# Get the page source and parse it
soup = BeautifulSoup(driver.page_source, "html.parser")
print(soup.prettify())  # Inspect if content loads

driver.quit()
