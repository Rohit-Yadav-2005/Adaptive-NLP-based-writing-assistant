"""
FAST Domain Classification (NO AI MODEL)
"""

from typing import Dict, Any

def classify_domain(text: str) -> Dict[str, Any]:
    text = text.lower()

    if any(word in text for word in ["research", "study", "analysis", "paper"]):
        return {"domain": "academic", "confidence": 0.9, "all_scores": {}}

    if any(word in text for word in ["meeting", "project", "client", "deadline"]):
        return {"domain": "business", "confidence": 0.9, "all_scores": {}}

    return {"domain": "casual", "confidence": 0.9, "all_scores": {}}


def get_domain_advice(domain: str) -> str:
    advice_map = {
        "academic": "Use formal tone and structured sentences.",
        "casual": "Informal tone is fine.",
        "business": "Be concise and professional.",
    }
    return advice_map.get(domain, "General writing advice.")