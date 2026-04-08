"""
Grammar checking via LanguageTool (remote or local JVM) with a solid offline fallback.

language_tool_python exposes Match fields in snake_case (rule_id, error_length).
Using camelCase caused AttributeError whenever LanguageTool actually ran, so
corrections silently never applied for users with a working LT install.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_lt_tool: Optional[Any] = None
_lt_backend: Optional[str] = None  # "public" | "local" | None
_lt_init_ran: bool = False


def _append_error(
    errors: List[Dict[str, Any]],
    *,
    rule_id: str,
    category: str,
    message: str,
    context: str,
    offset: int,
    length: int,
    bad_text: str,
    replacements: List[str],
) -> None:
    if not replacements:
        return
    errors.append(
        {
            "rule_id": rule_id,
            "category": category,
            "message": message,
            "context": context,
            "offset": offset,
            "length": length,
            "bad_text": bad_text,
            "replacements": replacements[:3],
        }
    )


# -----------------------------------------------------------------------------
# Offline rules (used when LanguageTool is unavailable or returns nothing useful)
# -----------------------------------------------------------------------------
def _fallback_check_grammar(text: str) -> Dict[str, Any]:
    errors: List[Dict[str, Any]] = []

    # --- Subject–verb / agreement ---
    for m in re.finditer(r"\b(he|she|it)\s+go\b", text, flags=re.IGNORECASE):
        _append_error(
            errors,
            rule_id="FALLBACK_SV",
            category="GRAMMAR",
            message="Third-person singular needs a verb with -s.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=[f"{m.group(1)} goes"],
        )

    for m in re.finditer(r"\b(he|she|it)\s+need\b(?!\s+to\b)", text, flags=re.IGNORECASE):
        _append_error(
            errors,
            rule_id="FALLBACK_SV",
            category="GRAMMAR",
            message="Use singular verb form with he/she/it.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=[f"{m.group(1)} needs"],
        )

    for m in re.finditer(r"\b(we|you|they)\s+needs\b", text, flags=re.IGNORECASE):
        _append_error(
            errors,
            rule_id="FALLBACK_SV",
            category="GRAMMAR",
            message="Plural subject takes plural verb.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=[f"{m.group(1)} need"],
        )

    # "results was" / "findings was" / "statistics was" ...
    for m in re.finditer(
        r"\b(results|findings|statistics|figures|data)\s+was\b",
        text,
        flags=re.IGNORECASE,
    ):
        full = m.group(0)
        subj = m.group(1).lower()
        rep = f"{m.group(1)} were"
        _append_error(
            errors,
            rule_id="FALLBACK_AGREE",
            category="GRAMMAR",
            message="Plural subject requires a plural verb.",
            context=text,
            offset=m.start(),
            length=len(full),
            bad_text=full,
            replacements=[rep],
        )

    # "Me and him" or "Me and John" as subject -> "He and I" / "John and I"
    for m in re.finditer(r"\bMe\s+and\s+([A-Z][a-z]+|him|her)\b", text):
        name = m.group(1)
        rep = "He and I" if name.lower() == "him" else "She and I" if name.lower() == "her" else f"{name} and I"
        _append_error(
            errors,
            rule_id="FALLBACK_PRONOUN",
            category="GRAMMAR",
            message=f"Use '{rep}' as the subject of the sentence.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=[rep],
        )

    # single lowercase i
    for m in re.finditer(r"(?:^|\s)(i)(?=$|\s|[.,?!])", text):
        _append_error(
            errors,
            rule_id="FALLBACK_CAPITAL_I",
            category="CASING",
            message="The pronoun 'I' should be capitalized.",
            context=text,
            offset=m.start(1),
            length=1,
            bad_text="i",
            replacements=["I"],
        )

    # I seen
    for m in re.finditer(r"(?i)\b(I|we|they|he|she|it)\s+seen\b", text):
        base_subj = m.group(1)
        if base_subj.lower() == "i":
            subj_fixed = "I"
        else:
            subj_fixed = base_subj.capitalize() if base_subj[0].isupper() else base_subj.lower()
        rep = f"{subj_fixed} saw"
        _append_error(
            errors,
            rule_id="FALLBACK_SEEN_SAW",
            category="GRAMMAR",
            message="Use 'saw' instead of 'seen' as the simple past tense.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=[rep],
        )

    # Casual slang detection
    slang_map = {
        "wanna": "want to", "gonna": "going to", "u": "you", 
        "idk": "I don't know", "lol": "haha", "im": "I'm", "ur": "your"
    }
    for slang, formal in slang_map.items():
        for m in re.finditer(r"(?i)\b" + slang + r"\b", text):
            # Check if capitalized
            is_cap = m.group(0)[0].isupper()
            rep = formal.capitalize() if is_cap else formal
            _append_error(
                errors,
                rule_id="FALLBACK_SLANG",
                category="TYPOGRAPHY",
                message=f"Consider using '{rep}' in formal writing.",
                context=text,
                offset=m.start(),
                length=m.end() - m.start(),
                bad_text=m.group(0),
                replacements=[rep],
            )

    # n -> and
    for m in re.finditer(r"(?:^|\s)(n)(?=$|\s)", text):
        _append_error(
            errors,
            rule_id="FALLBACK_N_AND",
            category="TYPOS",
            message="Spell out 'and'.",
            context=text,
            offset=m.start(1),
            length=1,
            bad_text="n",
            replacements=["and"],
        )

    # tommorow -> tomorrow
    for m in re.finditer(r"(?i)\btommorow\b", text):
        is_cap = m.group(0)[0].isupper()
        rep = "Tomorrow" if is_cap else "tomorrow"
        _append_error(
            errors,
            rule_id="FALLBACK_SPELLING",
            category="MISSPELLING",
            message="Did you mean 'tomorrow'?",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=[rep],
        )

    # Fragments: "Heavy." or "Unforgiving." (Test case 4)
    # Match a sentence that consists of just one word starting with a capital letter
    for m in re.finditer(r"(?:[.?!]\s|^)([A-Z][a-z]+)\.(?=\s|$)", text):
        _append_error(
            errors,
            rule_id="CREATIVE_FRAGMENT",
            category="CREATIVE_FRAGMENT",
            message="Sentence fragment detected.",
            context=text,
            offset=m.start(1),
            length=len(m.group(1)) + 1,
            bad_text=m.group(1) + ".",
            replacements=[m.group(1).lower() + "."], # dummy replacement so it triggers utils.py
        )

    # "they has" -> "they have"
    for m in re.finditer(r"\bthey\s+has\b", text, flags=re.IGNORECASE):
        _append_error(
            errors,
            rule_id="FALLBACK_THEY_HAS",
            category="GRAMMAR",
            message="Subject–verb agreement",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=["they have"],
        )

    # Contractions: subject + "dont" -> "doesn't" / "don't" (not just "don't")
    for m in re.finditer(
        r"\b(I|you|we|they|he|she|it)\s+dont\b",
        text,
        flags=re.IGNORECASE,
    ):
        subj = m.group(1)
        sl = subj.lower()
        if sl in ("he", "she", "it"):
            rep = f"{subj} doesn't"
        else:
            rep = f"{subj} don't"
        _append_error(
            errors,
            rule_id="FALLBACK_CONTRACTION",
            category="GRAMMAR",
            message="Use the correct contraction and verb agreement.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=[rep],
        )

    # Bare "dont" -> "don't" (skip spans already handled as "X dont" above)
    for m in re.finditer(r"\bdont\b", text, flags=re.IGNORECASE):
        prefix = text[max(0, m.start() - 24) : m.start()]
        if re.search(r"\b(I|you|we|they|he|she|it)\s+$", prefix, flags=re.IGNORECASE):
            continue
        _append_error(
            errors,
            rule_id="FALLBACK_CONTRACTION",
            category="TYPOGRAPHY",
            message="Use an apostrophe in the contraction.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=["don't"],
        )

    for m in re.finditer(r"\bwont\b", text, flags=re.IGNORECASE):
        _append_error(
            errors,
            rule_id="FALLBACK_CONTRACTION",
            category="TYPOGRAPHY",
            message="Use an apostrophe in the contraction.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=["won't"],
        )

    for m in re.finditer(r"\bcant\b", text, flags=re.IGNORECASE):
        _append_error(
            errors,
            rule_id="FALLBACK_CONTRACTION",
            category="TYPOGRAPHY",
            message="Use an apostrophe in the contraction.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=["can't"],
        )

    for m in re.finditer(r"\bim\b", text, flags=re.IGNORECASE):
        _append_error(
            errors,
            rule_id="FALLBACK_CONTRACTION",
            category="TYPOGRAPHY",
            message="Use an apostrophe in the contraction.",
            context=text,
            offset=m.start(),
            length=m.end() - m.start(),
            bad_text=m.group(0),
            replacements=["I'm"],
        )

    # "everyday" vs "every day" before verbs
    for m in re.finditer(
        r"\beveryday\b\s+(run|go|eat|walk|do|try|use|see|look|feel|work)",
        text,
        flags=re.IGNORECASE,
    ):
        _append_error(
            errors,
            rule_id="FALLBACK_EVERYDAY",
            category="GRAMMAR",
            message="Use 'every day' when meaning 'each day'.",
            context=text,
            offset=m.start(),
            length=8,
            bad_text="everyday",
            replacements=["every day"],
        )

    suggestions = [f'{e["bad_text"]} → {e["replacements"][0]}' for e in errors if e["replacements"]]

    return {
        "errors": errors,
        "suggestions": suggestions,
        "error_count": len(errors),
    }


def _merge_errors_dedupe(
    primary: List[Dict[str, Any]], secondary: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Prefer LanguageTool spans; add fallback errors that do not overlap same offset."""
    seen = {(e["offset"], e["length"]) for e in primary}
    out = list(primary)
    for e in secondary:
        key = (e["offset"], e["length"])
        if key not in seen:
            seen.add(key)
            out.append(e)
    out.sort(key=lambda x: x["offset"])
    return out


def _languagetool_check_grammar(text: str, tool: Any) -> Dict[str, Any]:
    matches = tool.check(text)
    errors: List[Dict[str, Any]] = []

    for match in matches:
        if not match.replacements:
            continue

        off = int(match.offset)
        ln = int(match.error_length)
        bad = text[off : off + ln]

        errors.append(
            {
                "rule_id": match.rule_id,
                "category": match.category,
                "message": match.message,
                "context": match.context,
                "offset": off,
                "length": ln,
                "bad_text": bad,
                "replacements": list(match.replacements)[:3],
            }
        )

    suggestions = [f'{e["bad_text"]} → {e["replacements"][0]}' for e in errors if e["replacements"]]

    return {
        "errors": errors,
        "suggestions": suggestions,
        "error_count": len(errors),
    }


def _init_language_tool() -> Tuple[Optional[Any], Optional[str]]:
    """
    Try backends in order (override with LANGUAGETOOL_MODE):
      - auto (default): local JVM server, then public API
      - local: JVM only
      - public: languagetool.org API only
      - off: skip LanguageTool
    """
    import language_tool_python

    mode = os.environ.get("LANGUAGETOOL_MODE", "auto").strip().lower()
    if mode in ("off", "0", "false", "no"):
        logger.info("LanguageTool disabled via LANGUAGETOOL_MODE.")
        return None, None

    lt_version = os.environ.get("LANGUAGETOOL_VERSION", "").strip()

    def try_local() -> Tuple[Optional[Any], Optional[str]]:
        try:
            kwargs: Dict[str, Any] = {"language": "en-US"}
            if lt_version:
                kwargs["language_tool_download_version"] = lt_version
            t = language_tool_python.LanguageTool(**kwargs)
            logger.info("LanguageTool: local JVM server ready.")
            return t, "local"
        except Exception as e:
            logger.warning("LanguageTool local init failed: %s", e)
            return None, None

    def try_public() -> Tuple[Optional[Any], Optional[str]]:
        try:
            t = language_tool_python.LanguageToolPublicAPI("en-US")
            logger.info("LanguageTool: using public HTTPS API (rate limits may apply).")
            return t, "public"
        except Exception as e:
            logger.warning("LanguageTool public API init failed: %s", e)
            return None, None

    if mode == "local":
        return try_local()
    if mode == "public":
        return try_public()

    # auto
    t, backend = try_local()
    if t is not None:
        return t, backend
    t, backend = try_public()
    if t is not None:
        return t, backend
    return None, None


def get_language_tool_instance() -> Tuple[Optional[Any], Optional[str]]:
    """Lazy singleton; safe to call from workers after import."""
    global _lt_tool, _lt_backend, _lt_init_ran
    if _lt_init_ran:
        return _lt_tool, _lt_backend
    _lt_init_ran = True
    _lt_tool, _lt_backend = _init_language_tool()
    return _lt_tool, _lt_backend


def check_grammar(text: str) -> Dict[str, Any]:
    tool, backend = get_language_tool_instance()

    if tool is None:
        return _fallback_check_grammar(text)

    try:
        lt_result = _languagetool_check_grammar(text, tool)
    except Exception as e:
        logger.exception("LanguageTool check failed; using offline rules: %s", e)
        return _fallback_check_grammar(text)

    # Merge offline catches LanguageTool can miss (and strengthen when LT is rate-limited)
    fb = _fallback_check_grammar(text)
    merged = _merge_errors_dedupe(lt_result["errors"], fb["errors"])
    suggestions = [f'{e["bad_text"]} → {e["replacements"][0]}' for e in merged if e["replacements"]]

    return {
        "errors": merged,
        "suggestions": suggestions,
        "error_count": len(merged),
    }


def correct_text(text: str) -> Dict[str, Any]:
    """
    Run the grammar checker and build a fully corrected string by applying every
    detected replacement (ignores style filtering — use the /analyze pipeline for that).
    """
    from backend.utils import build_final_corrections

    result = check_grammar(text)
    errors = result["errors"]
    forced = [{**e, "apply": True, "filter_reason": "all fixes applied"} for e in errors]
    merged = build_final_corrections(text, text, forced)
    return {
        "corrected_text": merged["corrected_text"],
        "errors": errors,
        "suggestions": result["suggestions"],
        "error_count": result["error_count"],
    }


def get_explanations(errors: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    return [
        {
            "error_type": e["category"],
            "bad_text": e["bad_text"],
            "suggestion": e["replacements"][0] if e["replacements"] else "",
            "explanation": e["message"],
        }
        for e in errors
    ]
