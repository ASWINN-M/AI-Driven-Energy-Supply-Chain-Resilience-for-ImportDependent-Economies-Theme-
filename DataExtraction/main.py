import requests
from dotenv import load_dotenv
import os

load_dotenv()

api = os.getenv("NewsAPI")
def fetch_hormuz_headlines(page_size=20):
    params = {
        "q": "strait of hormuz",
        "sortBy": "publishedAt",
        "apiKey": api,
        "pageSize": 5
    }

    response = requests.get("https://newsapi.org/v2/everything", params=params)
    response.raise_for_status()
    articles = response.json().get("articles", [])
    return [
            {
                "headline": a["title"],
                "snippet": a.get("description", "")
            }
            for a in articles
            if a.get("title")
        ]