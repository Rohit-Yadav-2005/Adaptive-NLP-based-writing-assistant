"""
Main FastAPI Application
Orchestrates the full NLP pipeline:
  Grammar Check → Domain Detection → Style Extraction → Style Filtering → Response
"""

import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from backend.db import init_db,save_document,get_documents
from backend.grammar import check_grammar, correct_text, get_explanations
from backend.domain import classify_domain, get_domain_advice
from backend.style import (
    extract_features,
    update_user_profile,
    update_user_feedback,
    get_user_profile,
)
from backend.utils import filter_suggestions, build_final_corrections
from backend.context import filter_by_context
from backend.ai_grammar import improve_text_neural, model_info

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# App setup
# -------------------------------------------------------------------
app = FastAPI(
    title="Adaptive Writing Assistant",
    description=(
        "Context-aware, personalized grammar correction API "
        "that adapts to user writing style and domain."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()

# -------------------------------------------------------------------
# Request / Response schemas
# -------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    user_id: str = Field(..., example="user_123")
    text: str = Field(
        ...,
        min_length=1,
        example="The experiment results was interesting.",
    )


class AnalyzeResponse(BaseModel):
    original_text: str
    corrected_text: str
    domain: str
    domain_confidence: float
    domain_advice: str
    style_profile: Dict[str, Any]
    corrections_applied: int
    corrections_skipped: int
    explanations: list


class HealthResponse(BaseModel):
    status: str
    version: str


class FeedbackRequest(BaseModel):
    user_id: str = Field(..., example="user_001")
    accepted: bool = Field(..., example=True)
    # Optional: could be extended later to identify which suggestion was
    # accepted/rejected. For now we track a coarse user preference.
    domain: Optional[str] = Field(None, example="academic")


# -------------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------------
@app.get("/", response_model=HealthResponse)
def health_check():
    """Simple health-check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    """
    Full analysis pipeline.

    1. Grammar check & correction
    2. Domain classification
    3. Style feature extraction
    4. Style-aware suggestion filtering
    5. Return combined results
    """
    text = request.text
    user_id = request.user_id

    try:
        # Step 1 – Grammar correction
        grammar_result = correct_text(text)
        errors = grammar_result["errors"]

        # Step 1.5 - Context Analysis (Step 3 in user spec)
        # Ensure suggestions don't fundamentally change the sentence meaning
        errors = filter_by_context(errors, text)

        # IMPORTANT: don't trust auto-corrected text directly; 
        # we rebuild it at the end
        corrected = text

        # Step 2 – Domain detection
        domain_result = classify_domain(text)
        domain = domain_result["domain"]
        domain_conf = domain_result["confidence"]
        advice = get_domain_advice(domain)

        # Step 3 – Style extraction & profile update
        features = extract_features(text)
        style_profile = update_user_profile(user_id, features)

        # Step 4 – Style-aware filtering
        filtered = filter_suggestions(errors, style_profile, domain)
        final = build_final_corrections(text, corrected, filtered)

        logger.debug("errors=%s filtered=%s final=%s", errors, filtered, final)

        return AnalyzeResponse(
            original_text=text,
            corrected_text=final["corrected_text"],
            domain=domain,
            domain_confidence=domain_conf,
            domain_advice=advice,
            style_profile=style_profile,
            corrections_applied=final["corrections_applied"],
            corrections_skipped=final["corrections_skipped"],
            explanations=final["explanations"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/profile/{user_id}")
def get_profile(user_id: str):
    """Retrieve the style profile for a given user."""
    profile = get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found.")
    return {"user_id": user_id, "profile": profile}


@app.post("/feedback")
def feedback(request: FeedbackRequest):
    """
    Lightweight feedback loop.

    We currently track accept/reject at the user level and use it to
    adjust how aggressively we apply longer replacements in future runs.
    """
    profile = update_user_feedback(request.user_id, request.accepted)
    return {"user_id": request.user_id, "profile": profile}

@app.post("/save")
def save_text(request: AnalyzeRequest):
    save_document(request.user_id,request.text)
    return {"status":"saved"}


@app.get("/documents/{user_id}")
def fetch_docs(user_id:str):
    docs=get_documents(user_id)
    return {"documents":docs}

@app.post("/ai-improve")
def ai_improve(request: AnalyzeRequest):
    """
    Neural seq2seq grammar polish (separate from LanguageTool /analyze).

    Model and prefix are configurable via GRAMMAR_AI_MODEL and GRAMMAR_AI_PREFIX
    (see backend/ai_grammar.py). Defaults to vennify/t5-base-grammar-correction.
    """
    improved = improve_text_neural(request.text)
    return {"improved_text": improved, "grammar_ai": model_info()}