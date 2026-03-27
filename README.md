# ✍️ Adaptive NLP-Based Writing Assistant

> Context-aware, personalized grammar correction that adapts to your writing style.

## 🏗 Architecture

```
User Text
    │
    ▼
┌────────────────────┐
│  Grammar Checker   │  language_tool_python
│  (detect & fix)    │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Domain Classifier  │  HuggingFace zero-shot (BART-large-MNLI)
│ (academic/casual/  │
│  business)         │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Style Analyzer    │  spaCy  →  per-user JSON profiles
│  (sentence length, │
│   diversity, tone) │
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Style-Aware Filter │  Avoids over-correction
│ (keep / skip each  │
│  suggestion)       │
└────────┬───────────┘
         │
         ▼
     Response JSON
```

## 📂 Project Structure

```
project/
├── backend/
│   ├── main.py        # FastAPI app & /analyze endpoint
│   ├── grammar.py     # Grammar detection & correction
│   ├── domain.py      # Zero-shot domain classification
│   ├── style.py       # Style feature extraction & user profiles
│   └── utils.py       # Style-aware suggestion filter
├── frontend/
│   └── app.py         # Streamlit UI
├── data/              # User profiles (auto-generated)
├── models/            # (reserved for fine-tuned models)
├── tests/
│   └── test_pipeline.py
├── requirements.txt
└── README.md
```

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Note: `language-tool-python` typically requires **Java 17+**. If Java is older, grammar correction will fall back to lightweight rule-based fixes.

### 2. Start the backend (FastAPI)

```bash
uvicorn backend.main:app --reload --port 8000
```

### 3. Start the frontend (Streamlit)

```bash
streamlit run frontend/app.py
```

### 4. Use the API directly

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_001", "text": "The experiment results was interesting."}'
```

## 📡 API Reference

### `POST /analyze`

**Request body:**

| Field     | Type   | Description                     |
|-----------|--------|---------------------------------|
| `user_id` | string | Unique identifier for the user  |
| `text`    | string | Text to analyze and correct     |

**Response:**

| Field                 | Type   | Description                             |
|-----------------------|--------|-----------------------------------------|
| `original_text`       | string | The input text                          |
| `corrected_text`      | string | Grammar-corrected text                  |
| `domain`              | string | Detected domain (academic/casual/business) |
| `domain_confidence`   | float  | Confidence score for domain prediction  |
| `domain_advice`       | string | Writing advice for the detected domain  |
| `style_profile`       | object | User's accumulated style features       |
| `corrections_applied` | int    | Number of corrections applied           |
| `corrections_skipped` | int    | Number of corrections skipped (style filter) |
| `explanations`        | array  | Per-correction explanations             |

### `GET /profile/{user_id}`

Returns the stored style profile for the given user.

### `POST /feedback` (optional)

Lets the assistant learn whether you prefer stricter or more permissive corrections.

**Request body:**

- `user_id`: string
- `accepted`: boolean

**Example:**

```bash
curl -X POST http://127.0.0.1:8000/feedback ^
  -H "Content-Type: application/json" ^
  -d "{\"user_id\":\"user_001\",\"accepted\":true}"
```

The backend updates `feedback_accept_rate` in your saved style profile, which is then used by the style-aware filtering step.

## 🧪 Testing

```bash
python -m pytest tests/ -v
```

## 🔑 Key Features

- **Grammar Detection**: Uses LanguageTool (200+ rules). LanguageTool may require **Java 17+**; if unavailable, the app falls back to lightweight rule-based fixes.
- **Domain Classification**: Zero-shot BART classifier detects academic, casual, or business writing
- **Style Adaptation**: Builds a per-user profile using exponential moving average
- **Smart Filtering**: Avoids over-correction by respecting user style and domain context
- **Explanations**: Every correction includes error type, suggestion, and reasoning

## ⚙️ Tech Stack

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python, FastAPI                   |
| NLP      | spaCy, language_tool_python, HuggingFace Transformers |
| Frontend | Streamlit                         |
| Storage  | JSON file (user profiles)         |
