import os
import json
import spacy
import subprocess

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

PROFILE_FILE = "data/user_profiles.json"
ALPHA = 0.1 # EMA factor

def _load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    with open(PROFILE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _save_profiles(profiles):
    os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
    with open(PROFILE_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

def extract_features(text: str) -> dict:
    doc = nlp(text)
    sentences = list(doc.sents)
    tokens = [token for token in doc if not token.is_punct and not token.is_space]
    
    sentence_count = len(sentences)
    total_tokens = len(tokens)
    
    avg_sentence_length = total_tokens / sentence_count if sentence_count > 0 else 0
    unique_words = len(set(token.lower_ for token in tokens))
    lexical_diversity = unique_words / total_tokens if total_tokens > 0 else 0
    
    punctuation_count = sum(1 for token in doc if token.is_punct)
    punctuation_frequency = punctuation_count / sentence_count if sentence_count > 0 else 0
    
    # Simple form of formality
    formal_words = [
        "therefore", "however", "furthermore", "thus", "hence",
        "report", "review", "client", "meeting", "attached",
        "discuss", "team", "dear"
    ]
    formality_score = sum(1 for token in tokens if token.lower_ in formal_words) / total_tokens if total_tokens > 0 else 0
    
    tone = "casual"
    if formality_score > 0.05:
        tone = "formal"
    elif formality_score > 0.01:
        tone = "neutral"
        
    return {
        "avg_sentence_length": avg_sentence_length,
        "lexical_diversity": lexical_diversity,
        "punctuation_frequency": punctuation_frequency,
        "formality_score": formality_score,
        "tone": tone,
        "sentence_count": sentence_count,
        "total_tokens": total_tokens
    }

def get_user_profile(user_id: str) -> dict:
    profiles = _load_profiles()
    return profiles.get(user_id, None)

def update_user_profile(user_id: str, features: dict) -> dict:
    profiles = _load_profiles()
    
    if user_id not in profiles:
        profile = features.copy()
        profile["sample_count"] = 1
        profiles[user_id] = profile
    else:
        profile = profiles[user_id]
        # EMA update
        for k, v in features.items():
            if isinstance(v, (int, float)):
                old_val = profile.get(k, 0)
                profile[k] = (1 - ALPHA) * old_val + ALPHA * v
        profile["sample_count"] = profile.get("sample_count", 0) + 1
        profile["tone"] = features.get("tone", profile.get("tone", "casual"))
    
    _save_profiles(profiles)
    return profile

def update_user_feedback(user_id: str, accepted: bool) -> dict:
    profiles = _load_profiles()
    if user_id not in profiles:
        profiles[user_id] = {}
        
    profile = profiles[user_id]
    
    # Initialize feedback counters if they don't exist
    profile["feedback_total"] = profile.get("feedback_total", 0) + 1
    if accepted:
        profile["feedback_accept"] = profile.get("feedback_accept", 0) + 1
    else:
        profile["feedback_reject"] = profile.get("feedback_reject", 0) + 1
        
    profile["feedback_accept_rate"] = profile["feedback_accept"] / profile["feedback_total"]
    
    _save_profiles(profiles)
    return profile
