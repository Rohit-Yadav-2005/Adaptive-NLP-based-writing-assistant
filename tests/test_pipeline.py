"""
Test cases for the Adaptive Writing Assistant pipeline.
Run with:  python -m pytest tests/ -v
"""

import sys
import os

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.grammar import check_grammar, correct_text, get_explanations
from backend.style import extract_features
from backend.utils import build_final_corrections


# ===================================================================
# Grammar module tests
# ===================================================================

class TestGrammar:

    def test_detects_subject_verb_agreement(self):
        result = check_grammar("The experiment results was interesting.")
        assert result["error_count"] > 0
        # Should flag at least one grammar error with content tied to "was"
        assert any(
            ("was" in e.get("bad_text", "").lower())
            or ("results" in e.get("context", "").lower())
            or ("agreement" in e.get("message", "").lower())
            for e in result["errors"]
        )

    def test_corrects_text(self):
        result = correct_text("She dont like pizza.")
        corrected = result["corrected_text"]
        assert "doesn't" in corrected or "does not" in corrected

    def test_no_errors_on_clean_text(self):
        result = check_grammar("The weather is beautiful today.")
        # LanguageTool sometimes flags punctuation/formatting edge-cases;
        # we allow at most 1 low-signal issue for robustness.
        assert result["error_count"] <= 1

    def test_suggestions_returned(self):
        result = correct_text("He go to school every day.")
        assert len(result["suggestions"]) > 0

    def test_explanations(self):
        grammar = check_grammar("Me and him went to the store.")
        explanations = get_explanations(grammar["errors"])
        assert len(explanations) > 0
        assert all("explanation" in e for e in explanations)


# ===================================================================
# Style module tests
# ===================================================================

class TestStyle:

    def test_extract_features_academic(self):
        academic_text = (
            "The methodology employed in this investigation utilizes "
            "a comprehensive framework for systematic analysis of the "
            "dependent variables within the experimental paradigm."
        )
        features = extract_features(academic_text)
        assert features["avg_sentence_length"] > 10
        assert features["tone"] in ("formal", "neutral")

    def test_extract_features_casual(self):
        casual_text = "hey what's up? i'm gonna grab some food. wanna come?"
        features = extract_features(casual_text)
        assert features["avg_sentence_length"] < 10

    def test_lexical_diversity_range(self):
        text = "The cat sat on the mat. The cat is a good cat."
        features = extract_features(text)
        assert 0 <= features["lexical_diversity"] <= 1

    def test_sentence_count(self):
        text = "First sentence. Second sentence. Third sentence."
        features = extract_features(text)
        assert features["sentence_count"] == 3


# ===================================================================
# Integration-style comparison
# ===================================================================

class TestIntegration:

    def test_pipeline_produces_corrections(self):
        """End-to-end: an obviously wrong sentence should yield corrections."""
        text = "Their going to the store and they needs milk."
        grammar_result = correct_text(text)
        assert grammar_result["corrected_text"] != text
        assert len(grammar_result["errors"]) > 0

    def test_clean_sentence_no_changes(self):
        text = "She walks to the park every morning."
        grammar_result = correct_text(text)
        assert grammar_result["corrected_text"] == text


class TestStyleAwareCorrection:
    def test_build_final_corrections_applies_accepted_replacements(self):
        original = "The experiment results was interesting."
        off = original.index("was")
        filtered_errors = [
            {
                "apply": True,
                "offset": off,
                "length": len("was"),
                "replacements": ["were"],
                "category": "GRAMMAR",
                "bad_text": "was",
                "message": "subject-verb agreement",
            }
        ]

        final = build_final_corrections(
            original_text=original,
            corrected_text=original,
            filtered_errors=filtered_errors,
        )
        assert "results were" in final["corrected_text"]
        assert final["corrections_applied"] == 1
        assert final["corrections_skipped"] == 0

    def test_build_final_corrections_skips_unaccepted_replacements(self):
        original = "The experiment results was interesting."
        off = original.index("was")
        filtered_errors = [
            {
                "apply": False,
                "offset": off,
                "length": len("was"),
                "replacements": ["were"],
                "category": "GRAMMAR",
                "bad_text": "was",
                "message": "subject-verb agreement",
            }
        ]

        final = build_final_corrections(
            original_text=original,
            corrected_text=original,
            filtered_errors=filtered_errors,
        )
        assert final["corrected_text"] == original
        assert final["corrections_applied"] == 0
        assert final["corrections_skipped"] == 1
