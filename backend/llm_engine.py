import os
import json
import logging
from typing import Dict, Any
from google import genai

logger = logging.getLogger(__name__)

_client = None

def get_client():
    global _client
    if not _client:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EnvironmentError("GEMINI_API_KEY is not set. Please set it in your .env file.")
        _client = genai.Client(api_key=api_key)
    return _client

from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def _call_llm(client, prompt: str) -> str:
    response = client.models.generate_content(
        model='gemini-2.5-flash-lite',
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
    )
    return response.text

def analyze_and_improve_with_llm(text: str, style_profile: Dict[str, Any], target_style: str = "general", research_context: str = None) -> Dict[str, Any]:
    """
    Sends the text to Gemini via the new google-genai library.
    It returns a structured JSON payload.
    """
    client = get_client()
    
    # Pass style profile to influence corrections
    tone = style_profile.get("tone", "casual")
    style_guidance = f"The user writes in a {tone} tone. Emulate their personal voice while correcting."
    if target_style != "general":
        style_guidance += f" CRITICAL: The target document type is {target_style.upper()}. Adjust suggestions to match professional standards for this format."
    
    if research_context:
        style_guidance += f"\nBACKGROUND RESEARCH (Use this context for fact-checking and citations): \n{research_context}"

    prompt = f"""
    You are an expert Grammar and Writing Assistant. Analyze the following text carefully.
    
    User Text: "{text}"
    Style Guidance: {style_guidance}
    
    Respond STRICTLY in the following JSON format. Do not use markdown wrappers like ```json.
    {{
        "corrected_text": "The fully corrected text",
        "domain": "academic" | "casual" | "business" | "technical",
        "domain_confidence": 0.95,
        "domain_advice": "Brief advice based on domain",
        "corrections_applied": 2,
        "corrections_skipped": 0,
        "explanations": [
            {{
                "error_type": "Verb Tense",
                "original": "was",
                "suggestion": "were",
                "explanation": "Brief explanation of why"
            }}
        ]
    }}
    """
    
    try:
        response_text = _call_llm(client, prompt)
        return json.loads(response_text)
    except Exception as e:
        logger.error(f"LLM API Error: {e}")
        # Graceful fallback logic or raise error
        raise
