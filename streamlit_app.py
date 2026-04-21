"""
🧠 NeuroLingo — Streamlit Cloud Edition
AI-powered communication bridge for neurodiverse individuals.
"""

import json
import time
import random
import streamlit as st
from google import genai
from google.genai import errors

# ──────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────
API_KEYS = st.secrets.get("GEMINI_API_KEYS", [])
MODEL = "gemini-2.5-flash"

if "key_idx" not in st.session_state:
    st.session_state.key_idx = 0
if "history" not in st.session_state:
    st.session_state.history = []


def get_client() -> genai.Client:
    """Return a Gemini client using the current active key."""
    if not API_KEYS:
        st.error("⚠️ No API keys configured. Add `GEMINI_API_KEYS` to `.streamlit/secrets.toml`.")
        st.stop()
    return genai.Client(api_key=API_KEYS[st.session_state.key_idx])


def rotate_key():
    """Rotate to the next available API key."""
    if len(API_KEYS) > 1:
        st.session_state.key_idx = (st.session_state.key_idx + 1) % len(API_KEYS)


def call_gemini(prompt: str, retries: int = 3) -> str:
    """Call Gemini with automatic key rotation and retry on 429 / network errors."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            client = get_client()
            resp = client.models.generate_content(model=MODEL, contents=prompt)
            return resp.text
        except Exception as exc:
            last_err = exc
            msg = str(exc)
            is_retryable = False
            if isinstance(exc, errors.APIError) and (exc.code == 429 or "RESOURCE_EXHAUSTED" in msg):
                rotate_key()
                is_retryable = True
            elif any(k in msg for k in ("429", "RESOURCE_EXHAUSTED", "10054", "forcibly closed", "ConnectionReset")):
                rotate_key()
                is_retryable = True

            if not is_retryable or attempt == retries:
                raise
            time.sleep(min(2 ** attempt + random.uniform(0, 1), 15))
    raise last_err  # type: ignore


def strip_md(text: str) -> str:
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:-3].strip()
    elif text.startswith("```"):
        text = text[3:-3].strip()
    return text


# ──────────────────────────────────────────────
# AI Pipeline
# ──────────────────────────────────────────────
def analyze(text: str) -> dict:
    prompt = f"""
    Analyze the following text from a user communicating socially.
    Extract:
    1. intent: True intent of the message.
    2. tone: Tone (e.g., formal, passive-aggressive, sincere).
    3. figurative_language: Boolean if idioms/metaphors are used.
    4. ambiguity: Level of ambiguity (Low, Medium, High).

    Text: "{text}"

    Respond ONLY with a valid JSON object:
    {{"intent":"string","tone":"string","figurative_language":bool,"ambiguity":"string"}}
    """
    try:
        return json.loads(strip_md(call_gemini(prompt)))
    except Exception:
        return {"intent": "Unknown", "tone": "Unknown", "figurative_language": False, "ambiguity": "Unknown"}


def translate(text: str, analysis: dict) -> dict:
    gen_prompt = f"""
    You translate neurotypical socially ambiguous text into literal, structured meaning for neurodiverse individuals.
    Original: "{text}"
    Analysis: {json.dumps(analysis)}

    Extract:
    1. action: Core action requested or implied.
    2. urgency: Urgency level (Low, Medium, High).
    3. meaning: Clear, literal explanation without idioms or passive phrasing.

    Respond ONLY with a JSON object:
    {{"action":"string","urgency":"string","meaning":"string"}}
    """
    try:
        raw = json.loads(strip_md(call_gemini(gen_prompt)))

        ver_prompt = f"""
        You are a Verifier AI. Check this translation against the original for accuracy.
        Original: "{text}"
        Generated: {json.dumps(raw)}

        Return ONLY a JSON object:
        {{"is_accurate":bool,"corrected_meaning":"string","clarity_score":number_0_to_100}}
        """
        ver = json.loads(strip_md(call_gemini(ver_prompt)))

        meaning = ver.get("corrected_meaning", raw.get("meaning", ""))
        if isinstance(meaning, dict):
            meaning = meaning.get("meaning", "Meaning unknown")

        return {
            "action": raw.get("action", ""),
            "urgency": raw.get("urgency", "Low"),
            "meaning": meaning,
            "clarity_score": ver.get("clarity_score", 80),
        }
    except Exception as e:
        return {"action": "Error", "urgency": "Unknown", "meaning": str(e), "clarity_score": 0}


# ──────────────────────────────────────────────
# Page Config & Custom CSS
# ──────────────────────────────────────────────
st.set_page_config(page_title="NeuroLingo", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0B0F19 0%, #0F172A 50%, #0B0F19 100%); }
    [data-testid="stSidebar"] { background: #0F172A; border-right: 1px solid rgba(255,255,255,0.05); }
    h1, h2, h3, h4, h5, h6 { color: #e2e8f0 !important; }
    p, li, span, label, div { color: #cbd5e1; }
    .glass-card {
        background: rgba(30,41,59,0.7);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(12px);
        margin-bottom: 1rem;
    }
    .meaning-card {
        background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.05));
        border: 1px solid rgba(99,102,241,0.2);
        border-left: 4px solid #6366f1;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        margin: 0.75rem 0;
    }
    .metric-box {
        background: rgba(15,23,42,0.6);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 0.75rem 1rem;
        text-align: center;
    }
    .urgency-high { color: #f87171; font-weight: 700; }
    .urgency-medium { color: #fbbf24; font-weight: 700; }
    .urgency-low { color: #4ade80; font-weight: 700; }
    .tag {
        display: inline-block;
        background: rgba(99,102,241,0.15);
        color: #a5b4fc;
        border-radius: 8px;
        padding: 0.25rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .stTextInput > div > div > input {
        background: rgba(30,41,59,0.8) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 12px !important;
        color: #e2e8f0 !important;
        padding: 0.75rem 1rem !important;
        font-size: 1rem !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: rgba(99,102,241,0.5) !important;
        box-shadow: 0 0 0 2px rgba(99,102,241,0.15) !important;
    }
    .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 8px 25px rgba(99,102,241,0.3) !important;
    }
    .score-high { color: #4ade80; font-weight: 800; font-size: 1.5rem; }
    .score-med  { color: #fbbf24; font-weight: 800; font-size: 1.5rem; }
    .score-low  { color: #f87171; font-weight: 800; font-size: 1.5rem; }
    .header-gradient {
        background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    [data-testid="stMarkdownContainer"] code {
        background: rgba(99,102,241,0.15);
        color: #a5b4fc;
        padding: 0.15rem 0.4rem;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 NeuroLingo")
    st.caption("AI Communication Bridge")
    st.divider()

    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    st.markdown("##### 📜 Recent Decodes")
    if not st.session_state.history:
        st.caption("No messages decoded yet.")
    for i, item in enumerate(reversed(st.session_state.history[-15:])):
        urgency = item["translation"]["urgency"]
        icon = "🔴" if urgency == "High" else "🟡" if urgency == "Medium" else "🟢"
        with st.expander(f"{icon} {item['original'][:40]}…" if len(item['original']) > 40 else f"{icon} {item['original']}"):
            st.write(f"**Meaning:** {item['translation']['meaning']}")

    st.divider()
    st.caption("Powered by Google Gemini 2.5 Flash")


# ──────────────────────────────────────────────
# Main Area
# ──────────────────────────────────────────────
st.markdown('<h1><span class="header-gradient">NeuroLingo</span></h1>', unsafe_allow_html=True)
st.markdown("Decode socially ambiguous language into clear, literal meaning.")
st.markdown("")

# Example suggestions
examples = [
    "Maybe we should revisit this.",
    "I'll get to it when I can.",
    "That's an interesting approach…",
    "Let's put a pin in that for now.",
]

cols = st.columns(len(examples))
selected_example = None
for i, ex in enumerate(examples):
    if cols[i].button(ex, key=f"ex_{i}", use_container_width=True):
        selected_example = ex

# Input
user_input = st.text_input(
    "Message to decode",
    value=selected_example or "",
    placeholder="Paste a confusing message here…",
    label_visibility="collapsed",
)

if st.button("🔍 Decode Message", use_container_width=True, disabled=not user_input.strip()):
    with st.spinner("Analyzing intent, tone, and hidden meaning…"):
        analysis = analyze(user_input.strip())
        translation = translate(user_input.strip(), analysis)

    # Save to history
    st.session_state.history.append({
        "original": user_input.strip(),
        "analysis": analysis,
        "translation": translation,
    })

    # ── Result Display ──
    st.markdown("---")

    # Core Meaning Card
    clarity = translation["clarity_score"]
    score_cls = "score-high" if clarity >= 80 else "score-med" if clarity >= 50 else "score-low"

    st.markdown(f"""
    <div class="meaning-card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
            <span style="font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.15em; color:#818cf8;">✨ Core Meaning</span>
            <span class="{score_cls}">{clarity}%</span>
        </div>
        <p style="font-size:1.15rem; color:#f1f5f9; font-weight:500; line-height:1.6; margin:0;">
            {translation['meaning']}
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Metrics Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-box">
            <div style="font-size:0.6rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.25rem;">Intent</div>
            <div style="color:#e2e8f0; font-weight:600; font-size:0.9rem;">{analysis['intent']}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-box">
            <div style="font-size:0.6rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.25rem;">Tone</div>
            <div style="color:#e2e8f0; font-weight:600; font-size:0.9rem;">{analysis['tone']}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-box">
            <div style="font-size:0.6rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.25rem;">Action</div>
            <div style="color:#e2e8f0; font-weight:600; font-size:0.9rem;">{translation['action']}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        urg = translation["urgency"]
        urg_cls = f"urgency-{urg.lower()}"
        st.markdown(f"""<div class="metric-box">
            <div style="font-size:0.6rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.25rem;">Urgency</div>
            <div class="{urg_cls}" style="font-size:0.9rem;">{'🔴' if urg=='High' else '🟡' if urg=='Medium' else '🟢'} {urg}</div>
        </div>""", unsafe_allow_html=True)

    # Tags
    tags_html = ""
    if analysis.get("figurative_language"):
        tags_html += '<span class="tag">🎭 Figurative Language</span>'
    if analysis.get("ambiguity") and analysis["ambiguity"] != "Low":
        tags_html += f'<span class="tag">🧩 Ambiguity: {analysis["ambiguity"]}</span>'
    if tags_html:
        st.markdown(f"<div style='margin-top:0.75rem;'>{tags_html}</div>", unsafe_allow_html=True)


# ── Footer ──
st.markdown("---")
st.caption("🧠 NeuroLingo is an AI-powered bridge. Messages are analyzed by Google Gemini 2.5 Flash.")
