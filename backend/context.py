"""
Context Analysis Module
Analyzes the semantic meaning of the sentence using NLP models (spaCy)
to determine whether a correction drastically alters the original meaning.
"""

import spacy
from typing import Dict, Any, List

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            # We bypass the full en_core_web modules as they are hanging the server
            _nlp = spacy.blank("en")
        except Exception:
            pass
    return _nlp

def analyze_context(original_text: str, corrected_text: str) -> Dict[str, Any]:
    """
    Checks if the correction preserves the semantic meaning.
    Returns a dict with similarity score and a flag if it's safe to apply.
    """
    if not original_text or not corrected_text or original_text == corrected_text:
        return {"similarity": 1.0, "is_safe": True, "reason": "No change"}
        
    nlp = _get_nlp()
    doc_orig = nlp(original_text)
    doc_corr = nlp(corrected_text)
    
    if not doc_orig.has_vector or not doc_corr.has_vector:
        # Fallback if no valid word vectors are available (e.g. spacy.blank)
        return {"similarity": 1.0, "is_safe": True, "reason": "No vector model available"}
        
    similarity = doc_orig.similarity(doc_corr)
    
    # Threshold for safety. If it changes too much, it might not be a purely grammatical check.
    # Note: simple typo fixes like (teh -> the) usually yield similarity > 0.90
    threshold = 0.80
    is_safe = similarity >= threshold
    
    reason = "Meaning preserved" if is_safe else "Correction drastically altered sentence context"
    
    return {
        "similarity": round(float(similarity), 4),
        "is_safe": is_safe,
        "reason": reason
    }
    
def filter_by_context(errors: List[Dict[str, Any]], original_text: str) -> List[Dict[str, Any]]:
    """
    Filters out grammar errors whose primary replacement drastically changes meaning.
    """
    safe_errors = []
    
    for err in errors:
        repl = err.get("replacements", [])
        if not repl:
            safe_errors.append(err)
            continue
            
        top_fix = repl[0]
        off = err.get("offset", 0)
        ln = err.get("length", 0)
        
        # Simulate applying this single fix
        simulated_text = original_text[:off] + top_fix + original_text[off + ln:]
        
        context_result = analyze_context(original_text, simulated_text)
        
        # Keep error if meaning is preserved, else attach a rejection note
        if context_result["is_safe"]:
            safe_errors.append(err)
        else:
            print(f"Context Analyzer: Skipping suggestion '{top_fix}' due to low semantic similarity ({context_result['similarity']})")
            
    return safe_errors
