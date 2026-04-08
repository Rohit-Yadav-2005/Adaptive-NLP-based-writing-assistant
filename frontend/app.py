"""Streamlit frontend for the Adaptive Writing Assistant."""

import requests
import streamlit as st

API_URL = "http://127.0.0.1:8000"
st.set_page_config(
    page_title="Adaptive Writing Assistant",
    page_icon="🪄",
    layout="wide",
    initial_sidebar_state="expanded",
)

backend_ok = True
try:
    requests.get(f"{API_URL}", timeout=2)
except:
    backend_ok = False
if not backend_ok:
    st.error("🚨 Backend not running. Start backend first.")
st.markdown(
    """
    <style>
    :root{
      --bg:#0b1020;
      --card:#121a2f;
      --muted:#9cb0d8;
      --text:#e8efff;
      --accent:#7c9dff;
      --accent-2:#57e3b0;
      --warn:#ffb86b;
    }
    .stApp{
      background: radial-gradient(1000px 420px at 10% -10%, #1a2a57 0%, transparent 60%),
                  radial-gradient(1000px 420px at 90% -20%, #1c3a4f 0%, transparent 60%),
                  var(--bg);
    }
    .block-container{padding-top:.35rem;padding-bottom:2rem;}
    /* Hide Streamlit's top header/toolbar (e.g., Deploy button) */
    header, div[data-testid="stHeader"], div[data-testid="stToolbar"]{
      display:none !important;
    }
    .hero{
      background: linear-gradient(160deg, rgba(124,157,255,.16), rgba(87,227,176,.10));
      border: 1px solid rgba(255,255,255,.09);
      border-radius: 16px;
      padding: 1.15rem 1.2rem 1rem 1.2rem;
      margin-bottom: .75rem;
      box-shadow: 0 8px 24px rgba(0,0,0,.22);
    }
    .topbar-row{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap: 1rem;
      margin-bottom:.55rem;
    }
    .hero-title{
      margin: 0;
      font-size: 1.72rem;
      font-weight: 900;
      letter-spacing: -0.02em;
      color: var(--text);
    }
    .logo-mark{
      display:flex;
      align-items:center;
      gap:.55rem;
      font-weight: 900;
      color: var(--text);
    }
    .logo-mark .mark{
      width: 34px;
      height: 34px;
      border-radius: 12px;
      display:inline-flex;
      align-items:center;
      justify-content:center;
      background: rgba(124,157,255,.18);
      border: 1px solid rgba(124,157,255,.35);
    }
    .hero h1{margin:.1rem 0 .4rem 0;font-size:1.8rem;color:var(--text);}
    .hero p{margin:0;color:var(--muted);}
    .chip{
      display:inline-block;padding:.24rem .62rem;border-radius:999px;
      font-size:.76rem;font-weight:700;color:#dfe8ff;
      border:1px solid rgba(255,255,255,.10);margin-right:.35rem;
      background:rgba(255,255,255,.05);
    }
    .hero-meta{
      margin-top:.6rem;
      display:flex;
      gap:.6rem;
      flex-wrap:wrap;
    }
    .meta-pill{
      padding:.28rem .62rem;
      border-radius:10px;
      background:rgba(255,255,255,.04);
      border:1px solid rgba(255,255,255,.08);
      color:#d9e6ff;
      font-size:.78rem;
      font-weight:600;
    }
    .domain-chip{display:inline-block;padding:.35rem .75rem;border-radius:999px;color:white;font-weight:700;font-size:.82rem;}
    .domain-academic{background:#7b61ff;}
    .domain-casual{background:#25b37e;}
    .domain-business{background:#f38e3c;}
    .panel{
      background: linear-gradient(180deg, rgba(255,255,255,.03), rgba(255,255,255,.01));
      border: 1px solid rgba(255,255,255,.09);
      border-radius: 14px;
      padding: .85rem 1rem;
      margin-bottom: .85rem;
    }
    .examples-wrap{
      background: linear-gradient(180deg, rgba(255,255,255,.025), rgba(255,255,255,.008));
      border: 1px solid rgba(255,255,255,.08);
      border-radius: 14px;
      padding: .52rem .65rem .65rem .65rem;
      margin-bottom: .75rem;
    }
    .panel-title{font-size:1rem;font-weight:700;color:var(--text);margin:0 0 .35rem 0;}
    .panel-sub{color:var(--muted);font-size:.92rem;margin:0;}
    .result-box{
      border-left:4px solid var(--accent-2);
      background:rgba(87,227,176,.09);
      border-radius:12px;
      padding:.8rem .9rem;
      color:var(--text);
      margin-top:.4rem;
      margin-bottom:.2rem;
      line-height:1.45;
      font-size:1rem;
    }
    .explain-card{
      border:1px solid rgba(255,255,255,.08);
      border-radius:12px;
      padding:.65rem .75rem;
      margin:.35rem 0;
      background:rgba(255,255,255,.02);
    }
    .small-note{color:var(--muted);font-size:.85rem;}
    div[data-testid="metric-container"]{
      background:linear-gradient(180deg,#131c35,#11172a);
      border:1px solid rgba(255,255,255,.09);
      padding:.65rem .75rem;
      border-radius:12px;
    }
    .stTextArea textarea{
      background:#0f1730 !important;
      color:#e8efff !important;
      border:1px solid rgba(255,255,255,.15) !important;
      border-radius:12px !important;
      font-size:16px !important;
    }
    /* Extra: hide deploy button element if it exists */
    [data-testid="stDeployButton"], .stDeployButton, [data-testid="deploy-button"]{
      display:none !important;
    }
    footer{
      visibility:hidden;
    }
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
      background-color: #0b1121 !important;
      border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    .sidebar-header {
      font-size: 1.15rem;
      font-weight: 800;
      color: var(--accent);
      margin-bottom: 0.75rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      padding-bottom: 0.5rem;
    }
    .pipeline-step {
      background: linear-gradient(145deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
      border: 1px solid rgba(255,255,255,0.05);
      padding: 0.6rem 0.8rem;
      border-radius: 8px;
      margin-bottom: 0.5rem;
      font-size: 0.9rem;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 0.6rem;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .pipeline-step-number {
      background: var(--accent);
      color: #0b1020;
      border-radius: 50%;
      min-width: 22px;
      height: 22px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-weight: 900;
      font-size: 0.8rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <div class="topbar-row">
        <div class="logo-mark">
          <span class="mark">🪄</span>
          <span>Adaptive Writing Assistant</span>
        </div>
        <div>
          <span class="chip">AI Proofreading</span>
        </div>
      </div>
      <h1 class="hero-title">Proofread like a pro. Stay like you.</h1>
      <p>Paste text, then get grammar fixes that adapt to your tone and writing habits—without over-correcting.</p>
      <div class="hero-meta">
        <span class="meta-pill">Grammar + Clarity</span>
        <span class="meta-pill">Personalized Tone</span>
        <span class="meta-pill">Clear Explanations</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# Shared state + quick examples (prefills the editor)
# -------------------------------------------------------------------
if "input_text" not in st.session_state:
    st.session_state["input_text"] = ""

examples = {
    "Academic sample": "The methodology employed in this investigation utilizes a comprehensive framework for systematic analysis of dependent variables.",
    "Casual sample": "hey what's up? i'm gonna grab some food. wanna come?",
    "Business sample": "The report shows that revenue was down, so we needs to cut costs.",
}

with st.sidebar:
    st.markdown('<div class="sidebar-header">⚙️ Workspace</div>', unsafe_allow_html=True)
    user_id = st.text_input(
        "User ID",
        value="user_001",
        help="Used to maintain your writing style profile.",
    )
    st.caption("Your profile evolves as you analyze more text.")

    if st.button("Load Style Profile", use_container_width=True):
        try:
            resp = requests.get(f"{API_URL}/profile/{user_id}", timeout=10)
            if resp.status_code == 200:
                st.json(resp.json().get("profile", {}))
            else:
                st.info("No profile found yet. Analyze text to create one.")
        except requests.ConnectionError:
            st.error("Backend unavailable at 127.0.0.1:8000")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">ℹ️ Pipeline</div>', unsafe_allow_html=True)
    
    steps = [
        "Grammar check",
        "Domain detection",
        "Style extraction",
        "Over-correction filtering",
        "Explain each correction"
    ]
    for i, step in enumerate(steps, 1):
        st.markdown(
            f'<div class="pipeline-step"><span class="pipeline-step-number">{i}</span> {step}</div>',
            unsafe_allow_html=True
        )

left, right = st.columns([1.2, 1], gap="large")

with left:
    st.markdown(
        '<div class="panel"><p class="panel-title">Input Text</p>'
        '<p class="panel-sub">Paste a sentence or paragraph to analyze.</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="examples-wrap">', unsafe_allow_html=True)
    st.markdown("**Quick Examples**")
    st.caption("Prefill the editor")
    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        if st.button("Academic", use_container_width=True):
            st.session_state["input_text"] = examples["Academic sample"]
            st.rerun()
    with ex2:
        if st.button("Casual", use_container_width=True):
            st.session_state["input_text"] = examples["Casual sample"]
            st.rerun()
    with ex3:
        if st.button("Business", use_container_width=True):
            st.session_state["input_text"] = examples["Business sample"]
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    text = st.text_area(
        "Your text",
        label_visibility="collapsed",
        height=185,
        placeholder="Example: The experiment results was interesting and we needs to investigate more.",
        key="input_text",
    )

    submit = st.button("Analyze & Improve", type="primary", use_container_width=True)
    ai_button = st.button("✨ Improve with AI", use_container_width=True)

with right:
    st.markdown(
        '<div class="panel"><p class="panel-title">What You Get</p>'
        '<p class="panel-sub">Corrected text, detected domain, style metrics, and per-error explanations.</p></div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="small-note">Tip: Try academic, business, and casual text to compare behavior.</div>',
        unsafe_allow_html=True,
    )

if submit and not text.strip():
    st.warning("Please enter some text first.")

if submit and text.strip():
    with st.spinner("Analyzing text..."):
        try:
            resp = requests.post(
                f"{API_URL}/analyze",
                json={"user_id": user_id, "text": text},
                timeout=180,
            )
            if resp.status_code == 200:
                st.session_state["analysis_data"] = resp.json()
                st.session_state["ai_improved"] = None # clear any previous AI improvement
            else:
                st.error(f"API error: {resp.text}")
        except requests.exceptions.ReadTimeout:
            st.error("⏳ Server is taking too long. Please try again.")
        except requests.exceptions.ConnectionError:
            st.error(
                "Cannot connect to backend at `http://127.0.0.1:8000`.\n\n"
                "Run:\n"
                "`python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload`"
            )

# Render the output if available in session_state
if "analysis_data" in st.session_state and st.session_state["analysis_data"]:
    data = st.session_state["analysis_data"]
    sp = data.get("style_profile", {})

    st.markdown("---")
    c1, c2 = st.columns([1.2, 1], gap="large")

    with c1:
        st.markdown("### ✅ Corrected Text")
        st.markdown(
            f'<div class="result-box">{data.get("corrected_text", "")}</div>',
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown("### 🧭 Domain")
        domain = data.get("domain", "casual")
        conf = float(data.get("domain_confidence", 0.0))
        badge_class = f"domain-{domain}" if domain in {
            "academic",
            "casual",
            "business",
        } else "domain-casual"
        st.markdown(
            f'<span class="domain-chip {badge_class}">{domain.upper()} · {conf:.0%}</span>',
            unsafe_allow_html=True,
        )
        st.info(data.get("domain_advice", ""))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Applied", data.get("corrections_applied", 0))
    m2.metric("Skipped", data.get("corrections_skipped", 0))
    m3.metric("Formality", f'{sp.get("formality_score", 0):.2f}')
    m4.metric("Lexical Diversity", f'{sp.get("lexical_diversity", 0):.2f}')

    st.markdown("### 📌 Correction Explanations")
    explanations = data.get("explanations", [])
    if explanations:
        for i, exp in enumerate(explanations, start=1):
            with st.expander(
                f'{i}. {exp.get("error_type", "Issue")}: '
                f'`{exp.get("original", "")}` → `{exp.get("suggestion", "")}`'
            ):
                st.markdown(
                    f'<div class="explain-card"><b>Reason:</b> {exp.get("explanation", "")}</div>',
                    unsafe_allow_html=True,
                )
                note = exp.get("filter_note")
                if note:
                    st.caption(f"Filter note: {note}")
    else:
        st.success("No issues found. Your text looks clean.")

    st.markdown("### 🎨 Updated Style Profile")
    p1, p2, p3 = st.columns(3)
    p1.metric("Avg Sentence Length", sp.get("avg_sentence_length", "—"))
    p2.metric("Tone", str(sp.get("tone", "—")).title())
    p3.metric("Samples", sp.get("sample_count", "—"))

    st.markdown("### 🙋 Feedback")
    f1, f2 = st.columns(2)
    with f1:
        if st.button("👍 This correction quality is good", use_container_width=True):
            try:
                fb_resp = requests.post(
                    f"{API_URL}/feedback",
                    json={"user_id": user_id, "accepted": True},
                    timeout=10,
                )
                if fb_resp.status_code == 200:
                    st.success("Saved feedback. Thanks!")
                else:
                    st.warning("Could not save feedback right now.")
            except:
                st.error("Connection failed.")
    with f2:
        if st.button("👎 Too aggressive / not my style", use_container_width=True):
            try:
                fb_resp = requests.post(
                    f"{API_URL}/feedback",
                    json={"user_id": user_id, "accepted": False},
                    timeout=10,
                )
                if fb_resp.status_code == 200:
                    st.success("Saved feedback. We will adapt.")
                else:
                    st.warning("Could not save feedback right now.")
            except:
                st.error("Connection failed.")

if ai_button and text.strip():
    with st.spinner("🤖 AI is improving your text..."):
        try:
            resp = requests.post(
                f"{API_URL}/ai-improve",
                json={"user_id": user_id, "text": text},
                timeout=180,
            )

            if resp.status_code == 200:
                result = resp.json()
                improved = result.get("improved_text", text)

                st.markdown("### 🤖 AI Improved Version")
                st.markdown(
                    f'<div class="result-box">{improved}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.error("AI improvement failed.")

        except requests.exceptions.ReadTimeout:
            st.error("⏳ AI took too long. Try shorter text.")
        except requests.exceptions.ConnectionError:
            st.error("🚨 Cannot connect to backend.")