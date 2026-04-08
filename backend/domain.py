"""
FAST Domain Classification (Zero-Shot AI)
Uses HuggingFace zero-shot classifier to categorize text into domains.
Falls back to heuristic keywords if the model fails to load.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

_classifier: Any = None
HAS_CLASSIFIER = False


def _get_classifier():
    global _classifier, HAS_CLASSIFIER
    if _classifier is None and not HAS_CLASSIFIER:
        try:
            from transformers import pipeline

            logger.info(
                "Loading HuggingFace zero-shot classifier (may take a moment on first run)..."
            )
            _classifier = pipeline(
                "zero-shot-classification",
                model="valhalla/distilbart-mnli-12-3",
            )
            HAS_CLASSIFIER = True
            logger.info("Zero-shot classifier loaded.")
        except Exception as e:
            HAS_CLASSIFIER = False
            _classifier = False
            logger.warning(
                "Zero-shot classifier failed to load (%s); using keyword fallback.", e
            )
    return _classifier


def _heuristic_classify(text: str) -> Dict[str, Any]:
    text = text.lower()
    
    # Priority for direct business indicators, even if grammar is casual
    business_indicators = ["meeting", "project", "client", "deadline", "ceo", "business", "corp", "review", "report", "attached"]
    if any(word in text for word in business_indicators):
        return {"domain": "business", "confidence": 0.9, "all_scores": {"business": 0.9}}

    if any(word in text for word in ["research", "study", "analysis", "paper", "hypothesis", "theory"]):
        return {"domain": "academic", "confidence": 0.8, "all_scores": {}}

    # Technical
    if any(word in text for word in ["code", "software", "api", "database", "server", "linux"]):
        return {"domain": "technical", "confidence": 0.8, "all_scores": {}}

    return {"domain": "casual", "confidence": 0.8, "all_scores": {}}


def classify_domain(text: str) -> Dict[str, Any]:
    # Heuristics check first: Override zero-shot for strong business vocabulary
    heuristic = _heuristic_classify(text)
    if heuristic["domain"] == "business" and heuristic["confidence"] > 0.85:
        return heuristic

    classifier = _get_classifier()
    
    if HAS_CLASSIFIER and classifier:
        try:
            candidate_labels = ["academic", "business", "technical", "casual"]
            result = classifier(text, candidate_labels)
            
            top_domain = result["labels"][0]
            top_score = result["scores"][0]
            
            all_scores = {label: score for label, score in zip(result["labels"], result["scores"])}
            
            return {
                "domain": top_domain,
                "confidence": round(float(top_score), 4),
                "all_scores": all_scores
            }
        except Exception as e:
            logger.warning("Classifier inference failed: %s", e)
            return _heuristic_classify(text)
    
    return _heuristic_classify(text)


def get_domain_advice(domain: str) -> str:
    advice_map = {
        "academic": "Use formal tone, structured sentences, and objective language.",
        "casual": "Informal tone is fine. Be natural.",
        "business": "Be concise, professional, and action-oriented.",
        "technical": "Be precise, unambiguous, and explain technical terms clearly if necessary.",
    }
    return advice_map.get(domain, "General writing advice.")