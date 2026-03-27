"""
Style-Aware Correction Filter
Takes raw grammar suggestions and filters/modifies them based on the
user's writing-style profile so the system avoids over-correction.
"""

from typing import List, Dict, Any


def filter_suggestions(errors, style_profile, domain):
    tone=style_profile.get("tone","neutral")
    avg_len=style_profile.get("avg_sentence_length",15)
    accept_rate=float(style_profile.get("feedback_accept_rate",0.5)or 0.5)

    filtered=[]

    for err in errors:
        e=dict(err)
        e["apply"]=True
        e["filter_reason"]="Accepted"

        rule_id=err.get("rule_id","")
        category=err.get("category","")
        bad=err.get("bad_text","")
        repl=err.get("replacements",[])
        top=repl[0] if repl else ""

        # ----------------------------
        # 1. ALWAYS APPLY CRITICAL ERRORS
        # ----------------------------
        critical={"GRAMMAR","TYPOS","CONFUSED_WORDS","PUNCTUATION"}
        if category in critical:
            e["apply"]=True
            e["filter_reason"]="Critical grammar fix"
            filtered.append(e)
            continue

        # ----------------------------
        # 2. CASUAL TONE HANDLING
        # ----------------------------
        informal_words={"gonna","wanna","u","im","dont","idk","lol"}
        if tone=="casual":
            if bad.lower() in informal_words:
                e["apply"]=False
                e["filter_reason"]="Allowed informal usage"

        # ----------------------------
        # 3. LENGTH CONTROL (ANTI OVER-CORRECTION)
        # ----------------------------
        factor=2.5 if accept_rate>=0.6 else 2.0
        if avg_len<12 and top and len(top)>len(bad)*factor:
            e["apply"]=False
            e["filter_reason"]="Too verbose for user style"

        # ----------------------------
        # 4. TYPOGRAPHY SKIP (CASUAL DOMAIN ONLY)
        # ----------------------------
        if domain=="casual" and category in {"TYPOGRAPHY","WHITESPACE"}:
            e["apply"]=False
            e["filter_reason"]="Typography ignored in casual writing"

        # ----------------------------
        # 5. SAFETY CHECK (NEVER SKIP CRITICAL)
        # ----------------------------
        if category in critical:
            e["apply"]=True
            e["filter_reason"]="Critical grammar fix"

        filtered.append(e)

    return filtered


def build_final_corrections(
    original_text: str,
    corrected_text: str,
    filtered_errors: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Produce the final output combining the corrected text with
    per-error explanations.

    Returns:
        Dict with 'corrected_text', 'corrections_applied', 'corrections_skipped',
        and 'explanations'.
    """
    # Apply only accepted replacements back onto the original text.
    # This keeps skipped suggestions from being silently applied.
    applied = [e for e in filtered_errors if e.get("apply")]
    skipped = [e for e in filtered_errors if not e.get("apply")]

    accepted_replacements = []
    for e in applied:
        top_fix = e.get("replacements", [])
        if not top_fix:
            continue
        replacement = top_fix[0]
        off = int(e.get("offset", 0))
        ln = int(e.get("length", 0))
        if ln <= 0:
            continue
        accepted_replacements.append((off, ln, replacement))

    accepted_replacements.sort(key=lambda x: x[0], reverse=True)

    final_text = original_text
    # When applying from right-to-left, we can avoid index shifting issues.
    # If overlapping replacements exist, we skip the newer overlapping one.
    next_end = len(original_text)
    for off, ln, replacement in accepted_replacements:
        if off + ln > next_end:
            continue
        final_text = final_text[:off] + replacement + final_text[off + ln :]
        next_end = off

    explanations = []
    for e in applied:
        replacements = e.get("replacements", [])
        top_fix = replacements[0] if replacements else "N/A"
        explanations.append(
            {
                "error_type": e["category"],
                "original": e["bad_text"],
                "suggestion": top_fix,
                "explanation": e["message"],
                "filter_note": e.get("filter_reason", ""),
            }
        )

    return {
        "corrected_text": final_text,
        "corrections_applied": len(applied),
        "corrections_skipped": len(skipped),
        "explanations": explanations,
    }
