"""
Style Analyzer Module
Uses spaCy to extract writing-style features and stores per-user profiles in JSON.
"""

import json
from pathlib import Path
from typing import Dict, Any

import spacy

# -------------------------------------------------------------------
# spaCy model – use small model for speed; upgrade to en_core_web_md
# for better accuracy.
# -------------------------------------------------------------------
_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback to a lightweight tokenizer + sentence segmenter.
            # This keeps the app/test runnable even if the full model
            # isn't installed yet.
            _nlp = spacy.blank("en")
            if "sentencizer" not in _nlp.pipe_names:
                _nlp.add_pipe("sentencizer")
    return _nlp


# -------------------------------------------------------------------
# Profile storage
# -------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PROFILE_FILE = DATA_DIR / "user_profiles.json"


def _load_profiles() -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if PROFILE_FILE.exists():
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def _save_profiles(profiles: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2)


# -------------------------------------------------------------------
# Feature extraction
# -------------------------------------------------------------------

def extract_features(text: str) -> Dict[str, Any]:
    """
    Extract writing-style features from the given text.

    Returns:
        Dict with:
          - avg_sentence_length   : average tokens per sentence
          - lexical_diversity     : unique tokens / total tokens  (TTR)
          - punctuation_frequency : punctuation marks per sentence
          - formality_score       : heuristic 0-1 (higher = more formal)
          - tone                  : 'formal' | 'neutral' | 'casual'
          - sentence_count        : number of sentences
          - total_tokens          : total word tokens
    """
    nlp = _get_nlp()
    doc = nlp(text)

    sentences = list(doc.sents)
    sentence_count = len(sentences)

    tokens = [t for t in doc if not t.is_space]
    word_tokens = [t for t in tokens if t.is_alpha]
    punct_tokens = [t for t in tokens if t.is_punct]

    total_tokens = len(word_tokens)
    unique_tokens = len({t.lemma_.lower() for t in word_tokens})

    avg_sentence_length = (
        round(total_tokens / sentence_count, 2) if sentence_count else 0
    )
    lexical_diversity = (
        round(unique_tokens / total_tokens, 4) if total_tokens else 0
    )
    punctuation_frequency = (
        round(len(punct_tokens) / sentence_count, 2) if sentence_count else 0
    )

    # Simple formality heuristic:
    #   formal markers: nouns, adjectives, prepositions
    #   casual markers: contractions (')
    #
    # If the spaCy model does not include a tagger (e.g., when falling
    # back to `spacy.blank("en")`), POS tags will be empty. In that
    # case, approximate tone using sentence length.
    formal_pos = {"NOUN", "ADJ", "ADP", "DET"}
    has_pos_tags = any(getattr(t, "pos_", "") for t in word_tokens)

    if not has_pos_tags:
        # Fallback heuristic when POS is unavailable
        if avg_sentence_length >= 12:
            tone = "formal"
            formality_score = 0.6
        elif avg_sentence_length >= 8:
            tone = "neutral"
            formality_score = 0.4
        else:
            tone = "casual"
            formality_score = 0.2
    else:
        casual_markers = [t for t in word_tokens if "'" in t.text]  # contractions
        formal_count = sum(1 for t in word_tokens if t.pos_ in formal_pos)

        formality_score = round(
            (formal_count / total_tokens - len(casual_markers) / max(total_tokens, 1)),
            4,
        ) if total_tokens else 0
        formality_score = max(0.0, min(1.0, formality_score))

        if formality_score >= 0.55:
            tone = "formal"
        elif formality_score >= 0.35:
            tone = "neutral"
        else:
            tone = "casual"

    return {
        "avg_sentence_length": avg_sentence_length,
        "lexical_diversity": lexical_diversity,
        "punctuation_frequency": punctuation_frequency,
        "formality_score": formality_score,
        "tone": tone,
        "sentence_count": sentence_count,
        "total_tokens": total_tokens,
    }


# -------------------------------------------------------------------
# User profile management
# -------------------------------------------------------------------

def update_user_profile(user_id: str, features: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the stored profile for `user_id` using an exponential moving average
    so the profile adapts gradually rather than snapping to every new sample.

    Returns the updated profile dict.
    """
    profiles = _load_profiles()
    alpha = 0.3  # weight for the new observation

    if user_id not in profiles:
        profiles[user_id] = dict(features)
        profiles[user_id]["sample_count"] = 1
    else:
        profile = profiles[user_id]
        for key, new_val in features.items():
            if isinstance(new_val, (int, float)) and key in profile:
                profile[key] = round(
                    alpha * new_val + (1 - alpha) * profile[key], 4
                )
            else:
                profile[key] = new_val  # overwrite non-numeric (e.g. tone)
        profile["sample_count"] = profile.get("sample_count", 0) + 1
        profiles[user_id] = profile

    _save_profiles(profiles)
    return profiles[user_id]


def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Retrieve the stored style profile for `user_id`.
    Returns an empty dict if the user has no profile yet.
    """
    profiles = _load_profiles()
    return profiles.get(user_id, {})


def update_user_feedback(user_id: str, accepted: bool) -> Dict[str, Any]:
    """
    Track whether users accepted/rejected suggestions.
    This enables lightweight personalization without heavy retraining.
    """
    profiles = _load_profiles()
    profile = profiles.get(user_id, {})
    profile["feedback_total"] = int(profile.get("feedback_total", 0)) + 1
    if accepted:
        profile["feedback_accept"] = int(profile.get("feedback_accept", 0)) + 1
    else:
        profile["feedback_reject"] = int(profile.get("feedback_reject", 0)) + 1

    total = max(1, profile["feedback_total"])
    profile["feedback_accept_rate"] = round(
        profile.get("feedback_accept", 0) / total, 4
    )

    profiles[user_id] = profile
    _save_profiles(profiles)
    return profile
