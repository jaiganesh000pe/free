"""Optional LLM helper. Agents fall back to heuristics if no key is set."""
import json, requests
from .config import Config

def ask_json(system, user, max_tokens=800):
    if not Config.ANTHROPIC_API_KEY:
        return None
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": Config.ANTHROPIC_API_KEY,
                     "anthropic-version": "2023-06-01"},
            json={"model": Config.ANTHROPIC_MODEL, "max_tokens": max_tokens,
                  "system": system + " Respond with JSON only.",
                  "messages": [{"role": "user", "content": user}]},
            timeout=40)
        text = r.json()["content"][0]["text"].strip().strip("`")
        return json.loads(text[text.find("{"):text.rfind("}") + 1])
    except Exception:
        return None
