import os
import requests
from dotenv import load_dotenv

load_dotenv()

EIA_API_KEY = os.getenv("eia_api_key")

# Brent crude spot price series on EIA's open data API
BRENT_SERIES_ID = "RBRTE"  # daily Brent spot price, $/barrel


def fetch_brent_prices(days: int = 30) -> list:
    """
    Pulls the most recent `days` of Brent crude spot prices from EIA.
    Returns a list of {"date": "YYYY-MM-DD", "price": float}, most recent first.
    """
    url = "https://api.eia.gov/v2/petroleum/pri/spt/data/"
    params = {
        "api_key": EIA_API_KEY,
        "frequency": "daily",
        "data[0]": "value",
        "facets[series][]": BRENT_SERIES_ID,
        "sort[0][column]": "period",
        "sort[0][direction]": "desc",
        "offset": 0,
        "length": days,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    records = data.get("response", {}).get("data", [])

    prices = [
        {"date": r["period"], "price": float(r["value"])}
        for r in records
        if r.get("value") is not None
    ]
    return prices


def get_price_delta(prices: list) -> dict:
    """
    Takes the price list (most recent first) and computes simple deltas
    that the scoring step can use as a risk signal.
    """
    if len(prices) < 2:
        return {"latest_price": None, "change_1d_pct": None, "change_7d_pct": None}

    latest = prices[0]["price"]
    prev_day = prices[1]["price"]
    week_ago = prices[6]["price"] if len(prices) > 6 else prices[-1]["price"]

    return {
        "latest_price": latest,
        "change_1d_pct": round((latest - prev_day) / prev_day * 100, 2),
        "change_7d_pct": round((latest - week_ago) / week_ago * 100, 2),
    }


if __name__ == "__main__":
    prices = fetch_brent_prices(days=30)

    print(f"Fetched {len(prices)} days of Brent crude prices\n")
    for p in prices[:5]:
        print(p)

    deltas = get_price_delta(prices)
    print("\n--- Price signal for scoring ---")
    print(deltas)