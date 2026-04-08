"""
Neural grammar correction (seq2seq) for the /ai-improve endpoint.

Uses Hugging Face AutoModelForSeq2SeqLM + generate() so it works on Transformers v5+
(where the ``text2text-generation`` pipeline task was removed).

JFLEG-style T5 models work best on short sentences; we split on . ! ? before inference.

Environment:
  GRAMMAR_AI_MODEL   - Hugging Face model id (default: vennify/t5-base-grammar-correction).
  GRAMMAR_AI_PREFIX  - Input prefix override. Empty string for no-prefix models
                       (e.g. visheratin/t5-efficient-mini-grammar-correction).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

_MODEL_PRESETS: Dict[str, Dict[str, str]] = {
    "vennify/t5-base-grammar-correction": {"prefix": "grammar: "},
    "visheratin/t5-efficient-mini-grammar-correction": {"prefix": ""},
    "visheratin/t5-efficient-tiny-grammar-correction": {"prefix": ""},
}

_default_model = "vennify/t5-base-grammar-correction"

_model = None
_tokenizer = None
_device = None
_loaded_model_id: Optional[str] = None
_load_failed: bool = False


def _effective_model_id() -> str:
    return os.environ.get("GRAMMAR_AI_MODEL", _default_model).strip() or _default_model


def _effective_prefix(model_id: str) -> str:
    explicit = os.environ.get("GRAMMAR_AI_PREFIX")
    if explicit is not None:
        return explicit
    preset = _MODEL_PRESETS.get(model_id)
    if preset is not None:
        return preset["prefix"]
    if "t5" in model_id.lower() and "visheratin" not in model_id.lower():
        return "grammar: "
    return ""


def _split_sentences(text: str) -> List[str]:
    text = text.strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = [p.strip() for p in parts if p.strip()]
    return out if out else [text]


def _strip_prompt_echo(s: str, prefix: str) -> str:
    s = s.strip()
    if not prefix:
        return s
    if s.startswith(prefix):
        return s[len(prefix) :].strip()
    pl = prefix.lower()
    if s.lower().startswith(pl):
        return s[len(prefix) :].strip()
    return s


def _pick_device():
    import torch

    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def get_seq2seq() -> Tuple[Optional[object], Optional[object], Optional[object]]:
    """Lazy-load tokenizer + model (works with Transformers 4.x and 5.x)."""
    global _model, _tokenizer, _device, _loaded_model_id, _load_failed

    model_id = _effective_model_id()
    if _load_failed and _loaded_model_id == model_id:
        return None, None, None
    if _model is not None and _tokenizer is not None and _loaded_model_id == model_id:
        return _model, _tokenizer, _device

    try:
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        logger.info("Loading grammar AI model: %s", model_id)
        tok = AutoTokenizer.from_pretrained(model_id)
        m = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        m.eval()
        dev = _pick_device()
        m = m.to(dev)

        _tokenizer = tok
        _model = m
        _device = dev
        _loaded_model_id = model_id
        _load_failed = False
        logger.info("Grammar AI model on device: %s", dev)
    except Exception as e:
        logger.exception("Failed to load grammar AI model: %s", e)
        _model = None
        _tokenizer = None
        _device = None
        _loaded_model_id = model_id
        _load_failed = True

    return _model, _tokenizer, _device


def _generate_batch(
    prompts: List[str], max_new_tokens: int
) -> List[str]:
    import torch

    model, tokenizer, device = get_seq2seq()
    if model is None or tokenizer is None:
        return []

    inputs = tokenizer(
        prompts,
        padding=True,
        truncation=True,
        max_length=512,
        return_tensors="pt",
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        out_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            num_beams=5,
            do_sample=False,
        )

    return tokenizer.batch_decode(out_ids, skip_special_tokens=True)


def improve_text_neural(text: str, *, max_new_tokens: int = 128) -> str:
    """
    Run seq2seq grammar correction. Returns original text if the model is unavailable.
    """
    if not text.strip():
        return text

    model, _, _ = get_seq2seq()
    if model is None:
        return text

    model_id = _effective_model_id()
    prefix = _effective_prefix(model_id)
    sentences = _split_sentences(text)
    if not sentences:
        return text

    try:
        prompts = [f"{prefix}{s}" if prefix else s for s in sentences]
        decoded = _generate_batch(prompts, max_new_tokens=max_new_tokens)
        if len(decoded) != len(sentences):
            logger.warning("Grammar AI batch size mismatch; returning original.")
            return text

        corrected: List[str] = []
        for sent, raw in zip(sentences, decoded):
            fixed = _strip_prompt_echo(raw, prefix)
            corrected.append(fixed if fixed else sent)

        if len(corrected) == 1:
            return corrected[0]
        return " ".join(corrected)
    except Exception as e:
        logger.exception("Grammar AI inference failed: %s", e)
        return text


def model_info() -> Dict[str, str]:
    mid = _effective_model_id()
    ok = get_seq2seq()[0] is not None
    return {
        "model_id": mid,
        "prefix": _effective_prefix(mid),
        "default_model": _default_model,
        "loaded": str(ok),
    }
