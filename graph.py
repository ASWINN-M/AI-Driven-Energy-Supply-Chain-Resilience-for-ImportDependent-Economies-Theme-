from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
import model  # your extract_risk_from_headline function lives here


# 1. STATE — just data that flows through the graph.
# Define exactly the fields your pipeline needs, nothing more.
class NewsState(TypedDict):
    headlines: List[dict]        # raw input: [{"headline": "...", "snippet": "..."}, ...]
    risk_events: List[dict]      # output of extraction: structured JSON per headline


# 2. NODES — plain functions. Each takes the current state, returns updates to it.

def fetch_news_node(state: NewsState) -> dict:
    """
    In a real run this would call NewsAPI. For now it can just pass through
    headlines that were already loaded into state before the graph started.
    """
    return {"headlines": state["headlines"]}


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
graph_builder.add_node("extract_risk", extract_risk_node)

graph_builder.add_edge(START, "fetch_news")
graph_builder.add_edge("fetch_news", "extract_risk")
graph_builder.add_edge("extract_risk", END)

graph = graph_builder.compile()


if __name__ == "__main__":
    initial_state = {
        "headlines": [
            {"headline": "US imposes new sanctions on Iranian oil exports amid Hormuz tensions"},
            {"headline": "Houthi forces strike commercial vessel in Red Sea shipping lane"},
            {"headline": "Local football team wins regional championship"},
        ],
        "risk_events": [],
    }

    final_state = graph.invoke(initial_state)

    print("\n--- Final risk events ---")
    for event in final_state["risk_events"]:
        print(event)