from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from Severity_Score.score import app as scoring_pipeline, build_payload
from Data_Extraction.graph import graph as person_a_graph, initial_state

api = FastAPI()

api.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@api.get("/risk")
def get_risk():
    person_a_output = person_a_graph.invoke(initial_state)
    payload = build_payload(
        risk_events=person_a_output["risk_events"],
        price_signal=person_a_output["price_signal"]
    )
    result = scoring_pipeline.invoke({"raw_payload": payload})
    return {
        "corridor": result["corridor_name"],
        "disruption_probability_score": result["final_risk_score"],
        "threshold_breached": result["alert_triggered"],
        "executable_action": result["reroute_recommendation"]
    }