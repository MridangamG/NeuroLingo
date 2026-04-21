<p align="center">
  <img src="https://img.shields.io/badge/AI-Powered-6366f1?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Next.js-16-000?style=for-the-badge&logo=nextdotjs" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" />
</p>

# 🧠 NeuroLingo

**NeuroLingo** is an AI-powered communication bridge that translates socially nuanced, vague, or figurative language into clear, literal, and actionable meaning — designed for neurodiverse individuals, non-native speakers, and anyone who struggles to decode hidden context in everyday conversations.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **🔍 Analyze Mode** | Paste any confusing message and get its literal meaning, intent, tone, urgency, and a suggested action — instantly. |
| **🎙️ Ambient Live Mode** | Real-time continuous speech recognition (via Web Speech API). Place your device on a table and NeuroLingo passively transcribes the conversation, highlighting ambiguous or figurative statements with instant "Literal Meaning Detected" cards. |
| **🗣️ Voice I/O** | Speech-to-Text (Gemini multimodal) and Text-to-Speech (gTTS) for fully hands-free interaction. |
| **🤖 Dual-Agent Pipeline** | A *Generator* agent translates the meaning, then a *Verifier* agent cross-checks accuracy and assigns a Clarity Score (0–100) to prevent hallucination. |
| **🔑 API Key Rotation** | Automatic fallback to secondary API keys on `429 RESOURCE_EXHAUSTED` errors, with exponential backoff and jitter for resilience. |
| **🔄 Network Resilience** | Graceful retry on transient network errors (`WinError 10054`, `ConnectionReset`, `httpx` timeouts). |
| **💾 Conversation History** | All decoded messages are persisted to a local SQLite database and displayed in a sidebar for quick reference. |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                │
│  ┌───────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Analyze   │  │ Ambient Live │  │  History      │  │
│  │ Mode      │  │ Mode         │  │  Sidebar      │  │
│  └─────┬─────┘  └──────┬───────┘  └──────┬───────┘  │
└────────┼───────────────┼────────────────┼───────────┘
         │               │                │
         ▼               ▼                ▼
┌─────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                    │
│                                                      │
│  ┌──────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ NLP      │  │ LLM       │  │ Voice Service    │  │
│  │ Engine   │  │ Pipeline  │  │ (STT + TTS)      │  │
│  │(Analyzer)│  │(Gen+Verify│  │                  │  │
│  └────┬─────┘  └─────┬─────┘  └────────┬─────────┘  │
│       │              │                  │            │
│       ▼              ▼                  ▼            │
│  ┌──────────────────────────────────────────────┐   │
│  │     Retry Engine (Key Rotation + Backoff)     │   │
│  └──────────────────────┬───────────────────────┘   │
│                         │                            │
│                         ▼                            │
│              ┌─────────────────────┐                 │
│              │   Google Gemini API │                 │
│              │   (gemini-2.5-flash)│                 │
│              └─────────────────────┘                 │
│                                                      │
│  ┌──────────────────────────────────────────────┐   │
│  │           SQLite (SQLAlchemy ORM)             │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+
- **Node.js** 18+
- A **Google Gemini API Key** ([Get one here](https://aistudio.google.com/apikey))

### 1. Clone the Repository

```bash
git clone https://github.com/MridangamG/NeuroLingo.git
cd NeuroLingo
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

**Configure your API Key** in `backend/app/core/config.py`:

```python
GEMINI_API_KEYS: list[str] = [
    "YOUR_PRIMARY_API_KEY",
    "YOUR_FALLBACK_API_KEY",  # Optional
]
```

**Start the backend server:**

```bash
uvicorn app.main:app --reload
# Runs on http://localhost:8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:3000
```

### 4. Open in Browser

Navigate to **http://localhost:3000** and start decoding! 🎉

---

## 📂 Project Structure

```
NeuroLingo/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   │   ├── chat.py       # /chat/ and /chat/history endpoints
│   │   │   ├── analysis.py   # /analysis/ endpoint
│   │   │   └── voice.py      # /voice/transcribe and /voice/synthesize
│   │   ├── core/
│   │   │   ├── config.py     # App settings & API keys
│   │   │   └── database.py   # SQLAlchemy engine & session
│   │   ├── models/
│   │   │   └── communication.py  # CommunicationLog ORM model
│   │   ├── services/
│   │   │   ├── nlp_engine.py     # Intent, tone & ambiguity analyzer
│   │   │   ├── llm.py            # Generator + Verifier translation pipeline
│   │   │   ├── voice_service.py  # STT (Gemini) + TTS (gTTS)
│   │   │   └── retry.py          # Key rotation & exponential backoff
│   │   └── main.py           # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── src/app/
│   │   ├── page.tsx          # Main UI (Analyze + Live Mode)
│   │   ├── globals.css       # Design system & animations
│   │   └── layout.tsx        # Root layout
│   ├── package.json
│   └── next.config.ts
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4, TypeScript |
| **Backend** | FastAPI, Uvicorn, Pydantic |
| **AI/ML** | Google Gemini 2.5 Flash (Multimodal), gTTS |
| **Database** | SQLite + SQLAlchemy |
| **Speech** | Web Speech API (browser), Gemini Audio (server) |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/chat/` | Analyze & translate a message |
| `GET` | `/api/v1/chat/history` | Retrieve conversation history |
| `POST` | `/api/v1/analysis/` | NLP analysis only (intent, tone, etc.) |
| `POST` | `/api/v1/voice/transcribe` | Speech-to-Text (audio file upload) |
| `POST` | `/api/v1/voice/synthesize` | Text-to-Speech (returns MP3 audio) |

---

## 🎯 Use Cases

- **Neurodivergent individuals** decoding passive-aggressive emails, vague instructions, or social cues.
- **Non-native speakers** understanding idioms, sarcasm, and cultural context.
- **Professionals** clarifying ambiguous workplace communication.
- **Live meetings** with Ambient Mode for real-time social decoding.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ for inclusive communication.
</p>
