from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from . import model, main
from .fetch_price import fetch_brent_prices, get_price_delta


# 1. STATE — just data that flows through the graph.
# Define exactly the fields your pipeline needs, nothing more.
class NewsState(TypedDict):
    headlines: List[dict]        # raw input: [{"headline": "...", "snippet": "..."}, ...]
    risk_events: List[dict]      # output of extraction: structured JSON per headline
    prices: List[dict]           # recent price series from EIA
    price_signal: dict           # computed deltas / signals for scoring


# 2. NODES — plain functions. Each takes the current state, returns updates to it.

def fetch_news_node(state: NewsState) -> dict:
    """
    In a real run this would call NewsAPI. For now it can just pass through
    headlines that were already loaded into state before the graph started.
    """
    headlines = main.fetch_hormuz_headlines(page_size=20)
    return {"headlines": headlines}


def fetch_price_node(state: NewsState) -> dict:
    """
    Pull recent Brent prices and compute a simple price signal used by scoring.
    """
    try:
        prices = fetch_brent_prices(days=30)
        signal = get_price_delta(prices)
    except Exception:
        prices = []
        signal = {"latest_price": None, "change_1d_pct": None, "change_7d_pct": None}

    return {"prices": prices, "price_signal": signal}


def extract_risk_node(state: NewsState) -> dict:
    """
    Runs your extraction function over every headline currently in state.
    """
    risk_events = []
    for item in state["headlines"]:
        headline = item.get("headline")
        snippet = item.get("snippet", "")
        result = model.extract_risk_from_headline(headline, snippet)
        risk_events.append(result)
    return {"risk_events": risk_events}


# 3. BUILD THE GRAPH

graph_builder = StateGraph(NewsState)

graph_builder.add_node("fetch_news", fetch_news_node)
graph_builder.add_node("fetch_price", fetch_price_node)
graph_builder.add_node("extract_risk", extract_risk_node)

graph_builder.add_edge(START, "fetch_news")
graph_builder.add_edge("fetch_news", "fetch_price")
graph_builder.add_edge("fetch_price", "extract_risk")
graph_builder.add_edge("extract_risk", END)

graph = graph_builder.compile()

initial_state = {
        "headlines": [],
        "risk_events": [],
}
if __name__ == "__main__":
    

    final_state = graph.invoke(initial_state)

    print("\n--- Final risk events ---")
    for event in final_state["risk_events"]:
        print(event)