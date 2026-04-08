"""
Style-aware correction filter.

Takes raw grammar suggestions and filters them using the user's style profile so
the system avoids stylistic over-correction — without blocking real grammar fixes.
"""

from typing import Any, Dict, List, Set

# LanguageTool category ids are uppercase. Anything that fixes objective errors
# should be applied; STYLE / CLARITY tweaks may be relaxed for casual users.
_CRITICAL_CATEGORIES: Set[str] = {
    "GRAMMAR",
    "TYPOS",
    "TYPOGRAPHY",
    "CASING",
    "PUNCTUATION",
    "CONFUSED_WORDS",
    "REDUNDANCY",
    "TYPOS_STYLE",  # some builds use this
    "MISSPELLING",
}

# Suggestions that only polish wording (not wrong grammar) — length filter may apply.
_STYLE_LIKE_CATEGORIES: Set[str] = {
    "STYLE",
    "PLAIN_ENGLISH",
    "CLARITY",
    "READABILITY",
    "CREATIVE_WRITING",
}


def _is_critical(category: str) -> bool:
    c = (category or "").upper()
    return c in _CRITICAL_CATEGORIES or c.startswith("GRAMMAR")


def _is_style_like(category: str) -> bool:
    return (category or "").upper() in _STYLE_LIKE_CATEGORIES


def filter_suggestions(
    errors: List[Dict[str, Any]],
    style_profile: Dict[str, Any],
    domain: str,  # reserved for domain-aware rules
) -> List[Dict[str, Any]]:
    _ = domain
    tone = style_profile.get("tone", "neutral")
    avg_len = float(style_profile.get("avg_sentence_length", 15) or 15)
    accept_rate = float(style_profile.get("feedback_accept_rate", 0.5) or 0.5)

    filtered: List[Dict[str, Any]] = []

    for err in errors:
        e = dict(err)
        e["apply"] = True
        e["filter_reason"] = "Accepted"

        category = err.get("category", "") or ""
        bad = err.get("bad_text", "")
        repl = err.get("replacements", [])
        top = repl[0] if repl else ""

        # ------------------------------------------------------------------
        # 1. Objective grammar / spelling / punctuation: always apply first
        # ------------------------------------------------------------------
        if _is_critical(category):
            e["apply"] = True
            e["filter_reason"] = "Grammar or spelling fix"
            filtered.append(e)
            continue

        # ------------------------------------------------------------------
        # 2. Casual tone: allow intentional slang; do NOT skip missing apostrophes
        #    ("dont" is a typo, not the same as "gonna").
        # ------------------------------------------------------------------
        informal_words = {"gonna", "wanna", "u", "idk", "lol", "im"}
        if tone == "casual" and bad.lower() in informal_words:
            e["apply"] = False
            e["filter_reason"] = "Allowed informal usage"

        # ------------------------------------------------------------------
        # 3. Length control — only for style-like suggestions (not grammar)
        # ------------------------------------------------------------------
        factor = 2.5 if accept_rate >= 0.6 else 2.0
        if (
            _is_style_like(category)
            and avg_len < 12
            and top
            and len(top) > len(bad) * factor
        ):
            e["apply"] = False
            e["filter_reason"] = "Verbose for short-sentence style"

        # ------------------------------------------------------------------
        # 4. Non-critical, non-style: default apply (e.g. uncategorized fallback)
        # ------------------------------------------------------------------
        filtered.append(e)

    return filtered


def build_final_corrections(
    original_text: str,
    corrected_text: str,
    filtered_errors: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Apply accepted replacements onto the original text (right-to-left) and
    attach explanations.
    """
    applied = [e for e in filtered_errors if e.get("apply")]
    skipped = [e for e in filtered_errors if not e.get("apply")]

    accepted_replacements: List[tuple] = []
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
    next_end = len(original_text)
    for off, ln, replacement in accepted_replacements:
        if off + ln > next_end:
            continue
        final_text = final_text[:off] + replacement + final_text[off + ln :]
        next_end = off

    explanations: List[Dict[str, Any]] = []
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
