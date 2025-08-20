# HealthStack – Medical Conversation Visualizer & “Why” Engine

HealthStack is a web app that visualizes an 8-month patient–clinician conversation and lets users ask **why** certain decisions were made.  
It answers strictly from the chat history using a lightweight RAG pipeline powered by **Gemini 1.5 Flash**.

Frontend (Vercel): https://visualization-app.vercel.app/  
Backend (Render):  https://visualization-app-9ill.onrender.com

--------------------------------------------------------------------------------
1) FEATURES
--------------------------------------------------------------------------------
• Timeline View
  - Whats-app-style chat bubbles (right-aligned for Rohan, left for others)
  - Colored bubbles with timestamps

• Ask Why (Chatbot)
  - Retrieval-Augmented Generation (RAG) over the conversation JSON
  - Concise answers, with timestamp citations for traceability
  - Embeddings + generation via Gemini (text-embedding-004 + 1.5 Flash)

• Dashboard (WIP)
  - Placeholder for consultation metrics (aggregation from JSON)

• Deployment-Ready
  - Frontend on Vercel, backend on Render
  - Both services pull directly from this GitHub repo

--------------------------------------------------------------------------------
2) ARCHITECTURE
--------------------------------------------------------------------------------
HealthStack/
│
├─ backend/                        # Flask API (Gemini + pickle vector store)
│  ├─ app.py                       # /       (health), /ask (RAG QA)
│  ├─ requirements.txt             # flask, flask-cors, numpy, scikit-learn, etc.
│  ├─ Procfile                     # gunicorn app:app
│  ├─ .env.example                 # GEMINI_API_KEY=
│  └─ whatsapp_chat_rohan_full.json
│
├─ public/                         # optional static copy for Timeline
│  └─ whatsapp_chat_rohan_full.json
│
├─ src/                            # React (Vite + MUI)
│  ├─ components/                  # TopNav, Message, etc.
│  ├─ pages/                       # Timeline.jsx, AskWhy.jsx, Dashboard.jsx
│  ├─ theme.js
│  ├─ App.jsx                      # routes: /, /why, /dashboard
│  └─ main.jsx
│
├─ vercel.json                     # frontend hosting config
├─ render.yaml (optional)          # infra config (alternative)
└─ README.md / readme.txt

RAG Flow (lightweight):
1) For each message: create an embedding with Gemini **text-embedding-004**.
2) Store [vectors, texts, metadata] in a **pickle file** (vector_store.pkl).
3) At query: embed the question → cosine similarity → take top-K snippets.
4) Build a prompt with these snippets + the question → **Gemini 1.5 Flash** → answer with timestamp citations.

Note: We avoid heavy vector DBs on Render free tier to prevent OOM/timeouts.

--------------------------------------------------------------------------------
3) LIVE LINKS
--------------------------------------------------------------------------------
• Web App (Vercel): https://visualization-app.vercel.app/
• API (Render):     https://visualization-app-9ill.onrender.com

--------------------------------------------------------------------------------
4) DATA FORMAT
--------------------------------------------------------------------------------
backend/whatsapp_chat_rohan_full.json is an array of messages:
{
  "name": "Rohan",
  "side": "right",            // "right" for Rohan, "left" for others
  "text": "My HRV was low midweek—should I rest?",
  "time": "2025-04-08 18:45:00"
}

Optional future field:
  "consultation_minutes": number | null

Timeline uses `side` for bubble alignment; Ask Why uses `name`, `text`, and `time`.

--------------------------------------------------------------------------------
5) QUICK START (LOCAL)
--------------------------------------------------------------------------------
Backend (Flask)
---------------
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt

# Create .env (copy from .env.example)
# GEMINI_API_KEY=your_key_here

python app.py
# First run: builds vector_store.pkl automatically
# Subsequent runs: loads the pickle and starts instantly

Test the API locally:
- curl (macOS/Linux/Git Bash):
  curl -X POST http://127.0.0.1:5000/ask \
    -H "Content-Type: application/json" \
    -d '{"question":"Why was ApoB level a concern?"}'

- PowerShell (Windows):
  Invoke-WebRequest -Uri "http://127.0.0.1:5000/ask" `
    -Method POST `
    -Body '{"question":"Why was ApoB level a concern?"}' `
    -ContentType "application/json"

Frontend (React + Vite)
-----------------------
# from repo root (or wherever your frontend lives)
npm install
npm run dev
# open http://localhost:5173

If you use an env for the API:
  VITE_BACKEND_URL=http://127.0.0.1:5000
Otherwise, ensure AskWhy.jsx points at the correct backend URL.

--------------------------------------------------------------------------------
6) API REFERENCE
--------------------------------------------------------------------------------
GET /
  Health check
  → { "status": "Backend running with pickle-based RAG!" }

POST /ask
  Body:
    { "question": "Why was ApoB level a concern?" }
  Success:
    { "answer": "ApoB was a concern because ... (2025-02-20 10:00:00)" }
  Errors:
    400 – missing/empty `question`
    500 – upstream model or embedding failure

Model & Limits:
  • Embeddings: Gemini text-embedding-004
  • Generation: Gemini 1.5 Flash
  • Rate limiting: per-minute limit (no daily/project token cap in this app’s setup)

--------------------------------------------------------------------------------
7) DEPLOYMENT
--------------------------------------------------------------------------------
Backend (Render)
----------------
• Start Command:  gunicorn app:app
• Env Vars:       GEMINI_API_KEY
• requirements.txt must include:
  flask
  flask-cors
  python-dotenv
  google-generativeai
  numpy
  scikit-learn
  gunicorn

Tip: Generate vector_store.pkl locally (first run) and commit it, so Render doesn’t
     embed on startup (avoids timeouts/OOM on free tier).

Verify after deploy:
Invoke-WebRequest -Uri "https://visualization-app-9ill.onrender.com/ask" `
  -Method POST `
  -Body '{"question":"Why was ApoB level a concern?"}' `
  -ContentType "application/json"

Frontend (Vercel)
-----------------
• Build: Vite (default `npm run build`)
• If using env for API base:
  VITE_BACKEND_URL=https://visualization-app-9ill.onrender.com
• Deploy the repo; Vercel auto-detects Vite.

--------------------------------------------------------------------------------
8) TROUBLESHOOTING
--------------------------------------------------------------------------------
• Render WORKER TIMEOUT or SIGKILL / OOM
  - Ensure you’re using the pickle-based backend (no ChromaDB).
  - Confirm vector_store.pkl exists in backend/ and is committed.

• “gunicorn: command not found”
  - Add `gunicorn` to requirements.txt and set Start Command to `gunicorn app:app`.

• CORS / Frontend can’t reach API
  - flask-cors is enabled; ensure the frontend calls the correct base URL.

• Slow first response on Render
  - Free tier cold start; subsequent calls are faster.

• Gemini rate limit errors
  - Gemini enforces per-minute limits; retry after a short pause.

--------------------------------------------------------------------------------
9) DEVELOPMENT NOTES
--------------------------------------------------------------------------------
• Retrieval: cosine similarity over Gemini embeddings (scikit-learn + numpy)
• K: top 5 snippets for the answer prompt
• Prompt asks for timestamp citations to reduce hallucinations
• Styling: MUI + custom theme; bubbles aligned by `side`

--------------------------------------------------------------------------------
10) EXTENSIBILITY / FUTURE SCOPE
--------------------------------------------------------------------------------
• Implement Dashboard aggregation (consultation_minutes per person)
• Authentication (patient/clinician access)
• Richer charts & exports (e.g., “Visit Summary” PDFs)
• Multi-patient datasets, search filters, facets
• Optionally swap retrieval to FAISS or a managed vector DB when moving off free tier

--------------------------------------------------------------------------------
11) SECURITY & DATA
--------------------------------------------------------------------------------
• Keep GEMINI_API_KEY in env vars (Render/Vercel)
• Treat conversation data as PHI; ensure anonymization before making repos public

--------------------------------------------------------------------------------
12) CREDITS
--------------------------------------------------------------------------------
Built by Pranjal Choubay and Tanay Singh Lodhi.  
Embeddings & generation by Gemini 1.5 Flask.

