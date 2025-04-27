import os
import logging
import requests

RASA_URL = os.getenv("RASA_URL", "http://rasa:5005")

async def parse_intent(text: str) -> dict:
    try:
        response = requests.post(f"{RASA_URL}/model/parse", json={"text": text})
        response.raise_for_status()
        data = response.json()
        return {
            "intent": data["intent"]["name"],
            "confidence": data["intent"]["confidence"],
            "text": data.get("text", text)
        }
    except Exception as e:
        logging.error(f"Failed to parse intent: {e}", exc_info=True)
        return {"intent": "out_of_scope", "confidence": 0.0, "text": text}