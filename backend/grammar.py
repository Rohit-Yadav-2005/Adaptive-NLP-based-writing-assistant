"""
Grammar Module - STABLE VERSION (NO AI BLOCKING)
"""

import re
from typing import List, Dict, Any


# -----------------------------
# FALLBACK RULES
# -----------------------------
def _fallback_check_grammar(text: str) -> Dict[str, Any]:
    errors = []

    # he go → he goes
    for m in re.finditer(r"\b(he|she|it)\s+go\b", text, flags=re.IGNORECASE):
        errors.append({
            "rule_id":"GO",
            "category":"GRAMMAR",
            "message":"Verb form",
            "context":text,
            "offset":m.start(),
            "length":m.end()-m.start(),
            "bad_text":m.group(0),
            "replacements":[f"{m.group(1)} goes"],
        })

    # dont → don't
    for m in re.finditer(r"\bdont\b", text, flags=re.IGNORECASE):
        errors.append({
            "rule_id":"DONT",
            "category":"GRAMMAR",
            "message":"Missing apostrophe",
            "context":text,
            "offset":m.start(),
            "length":m.end()-m.start(),
            "bad_text":m.group(0),
            "replacements":["don't"],
        })

    # everyday → every day
    for m in re.finditer(r"\beveryday\b", text, flags=re.IGNORECASE):
        errors.append({
            "rule_id":"EVERYDAY",
            "category":"GRAMMAR",
            "message":"Incorrect usage",
            "context":text,
            "offset":m.start(),
            "length":m.end()-m.start(),
            "bad_text":m.group(0),
            "replacements":["every day"],
        })

    # they has → they have
    for m in re.finditer(r"\bthey\s+has\b", text, flags=re.IGNORECASE):
        errors.append({
            "rule_id":"THEY_HAS",
            "category":"GRAMMAR",
            "message":"Subject-verb agreement",
            "context":text,
            "offset":m.start(),
            "length":m.end()-m.start(),
            "bad_text":m.group(0),
            "replacements":["they have"],
        })

    suggestions = [f'{e["bad_text"]} → {e["replacements"][0]}' for e in errors]

    return {
        "errors": errors,
        "suggestions": suggestions,
        "error_count": len(errors)
    }


# -----------------------------
# PUBLIC FUNCTIONS
# -----------------------------
def check_grammar(text: str) -> Dict[str, Any]:
    return _fallback_check_grammar(text)


def correct_text(text: str) -> Dict[str, Any]:
    print("FAST RESPONSE")

    result = check_grammar(text)

    return {
        "corrected_text": text,
        "errors": result["errors"],
        "suggestions": result["suggestions"],
        "error_count": result["error_count"],
    }


def get_explanations(errors: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [
        {
            "error_type": e["category"],
            "bad_text": e["bad_text"],
            "suggestion": e["replacements"][0],
            "explanation": e["message"],
        }
        for e in errors
    ]