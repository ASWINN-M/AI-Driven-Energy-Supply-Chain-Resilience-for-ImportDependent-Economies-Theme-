import json
import os
import sys
from typing import Dict, Any, TypedDict
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    raw_payload: Dict[str, Any]
    corridor_name: str
    extracted_metrics: Dict[str, float]
    final_risk_score: float
    alert_triggered: bool
    reroute_recommendation: str

def ingest_node(state: AgentState) -> Dict[str, Any]:
    """Extracts base routing context from incoming payload."""
    payload = state["raw_payload"]
    return {"corridor_name": payload.get("corridor", "Strait of Hormuz")}

def extract_node(state: AgentState) -> Dict[str, Any]:
    """Normalizes raw unstructured signals into 0-100 scoring metrics."""
    raw = state["raw_payload"]
    
    metrics = {
        "geo_index": min(float(raw.get("geopolitical_severity_1_to_10", 0)) * 10, 100.0),
        "price_jump_pct": float(raw.get("brent_price_delta_pct", 0.0)),
        "maritime_threat": min(float(raw.get("active_maritime_incidents", 0)) * 25.0, 100.0),
        "spr_cover_days": float(raw.get("current_spr_buffer_days", 9.5))
    }
    return {"extracted_metrics": metrics}

def score_node(state: AgentState) -> Dict[str, Any]:
    """Applies weighted multi-factor risk model."""
    m = state["extracted_metrics"]
    
    # Static weights tuned for historical shock elasticity
    w_geo, w_price, w_mar, w_spr = 0.35, 0.25, 0.25, 0.15
    
    n_geo = m["geo_index"]
    n_price = min((m["price_jump_pct"] / 8.0) * 100.0, 100.0) 
    n_mar = m["maritime_threat"]
    n_spr = max(0.0, ((9.5 - m["spr_cover_days"]) / 9.5) * 100.0) if m["spr_cover_days"] < 9.5 else 0.0

    raw_score = (n_geo * w_geo) + (n_price * w_price) + (n_mar * w_mar) + (n_spr * w_spr)
    
    return {"final_risk_score": round(min(max(raw_score, 0.0), 100.0), 2)}

def alert_node(state: AgentState) -> Dict[str, Any]:
    """Evaluates score against operational thresholds and triggers mitigation."""
    score = state["final_risk_score"]
    corridor = state["corridor_name"]
    threshold = 70.0 
    
    if score < threshold:
        return {
            "alert_triggered": False,
            "reroute_recommendation": f"Status Nominal. {corridor} operational."
        }
    
    # Fallback deterministic advisory if live LLM generation is bypassed
    advisory = (
        f"CRITICAL VULNERABILITY ({score}/100): Reroute protocol activated for {corridor}. "
        "Recommend immediate diversion of 35% of pending Middle Eastern sour crude volume to West African "
        "(Bonny Light) spot tenders. Reallocate 2 available VLCC supertankers to the US Gulf Coast corridor "
        "to prevent drawing down the 9.5-day Strategic Petroleum Reserve."
    )
    
    return {
        "alert_triggered": True,
        "reroute_recommendation": advisory
    }

def build_payload(risk_events: list, price_signal: dict) -> dict:
    """
    Converts Person A's graph output into the raw_payload format
    that Person B's pipeline expects.
    """
    if not risk_events:
        return {}

    # Pick the highest severity event as the trigger
    top_event = max(risk_events, key=lambda e: e.get("severity", 1))

    return {
        "corridor": top_event.get("corridor", "Strait of Hormuz"),
        "geopolitical_severity_1_to_10": top_event.get("severity", 1) * 2,  # scale 1-5 → 2-10
        "brent_price_delta_pct": price_signal.get("change_7d_pct", 0.0) or 0.0,
        "active_maritime_incidents": sum(
            1 for e in risk_events
            if e.get("event_type") == "military_incident"
        ),
        "current_spr_buffer_days": 9.5,  # static for now, can wire real data later
        "headline_trigger": top_event.get("summary", "")
    }
# Pipeline Orchestration
workflow = StateGraph(AgentState)

workflow.add_node("ingest", ingest_node)
workflow.add_node("extract", extract_node)
workflow.add_node("score", score_node)
workflow.add_node("alert", alert_node)

workflow.add_edge("ingest", "extract")
workflow.add_edge("extract", "score")
workflow.add_edge("score", "alert")
workflow.add_edge("alert", END)

workflow.set_entry_point("ingest")
app = workflow.compile()

if __name__ == "__main__":
    # Import Person A's graph output
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Data_Extraction'))
    from graph import graph as person_a_graph, initial_state

    # Run Person A's pipeline
    person_a_output = person_a_graph.invoke(initial_state)

    # Bridge: convert to Person B's format
    payload = build_payload(
        risk_events=person_a_output["risk_events"],
        price_signal=person_a_output["price_signal"]
    )

    print("Payload from Person A:", json.dumps(payload, indent=2))

    # Run Person B's scoring pipeline
    result = app.invoke({"raw_payload": payload})

    output = {
        "timestamp": "2026-06-22T20:50:00Z",
        "corridor": result["corridor_name"],
        "disruption_probability_score": result["final_risk_score"],
        "threshold_breached": result["alert_triggered"],
        "executable_action": result["reroute_recommendation"]
    }

    sys.stdout.write(json.dumps(output, indent=2) + "\n")