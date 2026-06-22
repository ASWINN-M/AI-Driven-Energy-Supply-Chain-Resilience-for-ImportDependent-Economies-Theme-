import requests
from psycopg.raw_cursor import RawCursor
from dotenv import load_dotenv
import os

load_dotenv()

api = os.getenv("NewsAPI")

params = {
    "q": "strait of hormuz",
    "sortBy": "publishedAt",
    "apiKey": api,
    "pageSize": 5
}

response = requests.get("https://newsapi.org/v2/everything", params=params)

