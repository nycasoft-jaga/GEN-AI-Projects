import requests
from bs4 import BeautifulSoup

url = "https://www.sportskeeda.com/cricket/ipl-2020-rating-team-s-chances-winning-tournament"
response = requests.get(url)
soup = BeautifulSoup(response.text, 'html.parser')

content = soup.find('div', class_='content-holder')
if content:
    print(content.get_text(strip=True))
else:
    print("Failed to find article content.")