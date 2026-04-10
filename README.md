# 🚀 Nexus AI: Enterprise Writing Platform (V2.1)

Nexus AI has been transformed from a local NLP script into a high-performance, enterprise-grade distributed platform. It now features professional team workspaces, cryptographic authentication, and cloud-powered semantic reasoning.

## ✨ Evolution Summary
- **Before**: 2GB+ local ML models, slow load times, no user management.
- **After**: Sleek React/Vite frontend, JWT-protected FastAPI backend, and high-availability Gemini API integration.

## 🏗️ Technical Stack
- **Frontend**: React 18, Vite, Tailwind CSS, Framer Motion, Lucide.
- **Backend**: FastAPI, SQLAlchemy (SQLite), JWT (jose/passlib).
- **Core AI**: Google Gemini 2.5 Flash-Lite (Low latency cluster).

## 🛠️ Getting Started

### 1. Prerequisites
- Node.js (v18+)
- Python (v3.10+)

### 2. Backend Setup
1. `pip install -r requirements.txt`
2. Create/Update your `.env` file:
   ```env
   GEMINI_API_KEY=your_key_here
   JWT_SECRET_KEY=your_long_secret_string
   ```
3. Start the engine: `uvicorn backend.main:app --reload --port 8000`

### 3. Frontend Setup
1. `cd frontend-enterprise`
2. `npm install`
3. `npm run dev`

## 📂 Project Structure
- `backend/`: FastAPI server with SQLAlchemy models and Auth logic.
- `frontend-enterprise/`: Modern React project with dashboard and editor.
- `data/`: SQLite database (enterprise_v2.db).
- `venv/`: Shared python virtual environment.

---
*Built for the Enterprise. Powered by Nexus AI.*
| Field                 | Type   | Description                             |
|-----------------------|--------|-----------------------------------------|
| `original_text`       | string | The input text                          |
| `corrected_text`      | string | Grammar-corrected text                  |
| `domain`              | string | Detected domain (academic/casual/business) |
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
