import os
from dotenv import load_dotenv
import main
import json
from langgraph.graph import StateGraph, START , END , MessagesState
from langchain_core.prompts import ChatPromptTemplate
from google import genai 

load_dotenv()

api = os.getenv("google_api_key")

client = genai.Client(api_key=api)

SYSTEM_PROMPT = """You are a geopolitical risk extraction agent for an energy supply chain monitoring system.
 
You will be given a single news headline (and sometimes a short snippet). Extract structured risk information from it.
 
Respond with ONLY a JSON object, no markdown formatting, no backticks, no explanation. Use exactly this schema:
 
{
  "corridor": "Strait of Hormuz" | "Red Sea" | "Persian Gulf" | "Other" | "None",
  "supplier": "Iran" | "Saudi Arabia" | "UAE" | "Iraq" | "Other" | "None",
  "event_type": "sanctions" | "military_incident" | "shipping_disruption" | "price_shock" | "diplomatic" | "other",
  "severity": 1-5,
  "summary": "one short sentence summarizing the risk signal"
}
 
Rules:
- severity 1 = minor/routine, 5 = major disruption (e.g. closure, attack, war)
- If the headline has no real supply chain risk signal, set event_type to "other" and severity to 1
- corridor and supplier should be "None" if not clearly mentioned
- Always return valid JSON. Never add text before or after the JSON object."""


def extract_risk_from_headline(headline: str, snippet: str = "") -> dict:
    """
    Takes a headline (and optional snippet), sends it to Gemini with the
    system prompt above, and returns a parsed Python dict matching the schema.
    """

    user_message = f"Headline: {headline}"
    if snippet:
        user_message += f"\nSnippet: {snippet}"
    
    full_prompt = SYSTEM_PROMPT + "\n\n" + user_message

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=full_prompt
    )

    raw_text = response.text.strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        raw_text = raw_text.replace("json", "", 1).strip()
    
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        print("Failed to parse JSON. Raw response:")
        print(raw_text)
        return {
            "corridor": "None",
            "supplier": "None",
            "event_type": "other",
            "severity": 1,
            "summary": "Failed to extract risk signal"
        }

# if __name__ == "__main__":
#     # Example usage
#     test_headlines = [
#         "US imposes new sanctions on Iranian oil exports amid Hormuz tensions",
#         "Houthi forces strike commercial vessel in Red Sea shipping lane",
#         "Brent crude rises 3% on Gulf supply concerns",
#         "Local football team wins regional championship",  # control case, should be low severity
#     ]
 
#     for h in test_headlines:
#         result = extract_risk_from_headline(h)
#         print(f"\nHeadline: {h}")
#         print(f"Extracted: {json.dumps(result, indent=2)}")