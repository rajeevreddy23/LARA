# 🌌 LARA — Personal AI Operating System

> **LARA** is a persistent, voice-and-text personal AI assistant modeled on JARVIS: calm, dry wit, proactive, context-aware, capable of executing sandboxed tools/skills, and reasoning across long-running projects with cognitive memory and risk guardrails.

**Upgrade status (October 24, 2026):** Phase 1 audit and blocker fixes are complete. This is a local development app; several capabilities described below remain partial. Python execution is temporarily disabled because the former host subprocess did not provide isolation. See [the audit and phased backlog](docs/PHASE1_AUDIT.md) for verified behavior and remaining work. Local fallback supports limited rules and tools, not full AI reasoning.

---

## 🚀 Quickstart Guide

### 1. Backend Setup (FastAPI Orchestrator)

```bash
cd backend
python -m venv venv

# Activate Virtual Environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
```

*(Optional)* In `backend/.env`, set your `GEMINI_API_KEY`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```
*(If left unset, LARA runs in local memory/tool fallback mode with full functionality).*

**Start Backend:**
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
- Interactive Swagger API Docs: `http://localhost:8000/docs`
- System Health Telemetry: `http://localhost:8000/api/health`

---

### 2. Frontend Setup (Next.js Cyberpunk HUD)

```bash
cd frontend
npm install
npm run dev
```
Open **`http://localhost:3000`** in Google Chrome, Microsoft Edge, or Safari.

---

### 3. Voice Activation ("Hey LARA")

1. Click **`ENABLE WAKE-WORD`** in the top navigation header.
2. Say clearly: **"Hey LARA"**
   - You will hear the ascending acoustic JARVIS chime and the central **AudioOrb** will glow **Emerald Green**.
3. Speak your directive:
   - *"What is your current system status?"*
   - *"Remind me to check the deployment logs tomorrow at 10 AM"*
   - *"Run code: print([x**2 for x in range(5)])"*
   - *"Deliver an executive briefing"*
4. LARA will process your speech, execute any required skills, render the response in the HUD, and **speak the answer aloud** in a calm voice.

---

## 🏗️ Phase-Gated Architecture & Capabilities

### 🧠 Phase 1 — Identity & Memory
- **Persona Contract**: Calm, dry wit, concise in casual mode (1–3 sentences), thorough in briefing mode. Zero conversational filler (*"As an AI..."*).
- **Structured Long-Term Memory**: Firestore / Local JSON store tracking user facts (`user_facts`) and active projects (`projects`) namespaced per user.
- **Semantic Vector Recall**: Vector embeddings with cosine similarity search for *"remember when I..."* queries.
- **Autonomous Extractor**: Automatically discovers and records facts and project mentions from natural conversation.
- **Memory Intel HUD**: Click **`INTEL`** on the top bar to inspect and edit your knowledge graph.

### 🛠️ Phase 2 — Tool/Skill Registry
- **`run_code`**: Sandboxed Python script execution runner with 5-second timeout and stdout/stderr capture.
- **`calendar_reminders`**: Calendar events & reminder manager (create, list, delete).
- **`web_search`**: Real-time live web knowledge lookup.
- **Intent Router**: Automatically classifies and dispatches user directives to tools before model synthesis.

### 🎙️ Phase 3 — Voice Layer
- **Continuous Wake-Word**: Hands-free background listener for *"Hey LARA"*, *"LARA"*, *"Hi LARA"*.
- **Speech-to-Text (STT) & Speech Synthesis (TTS)**.
- **Web Audio Chime**: Synthetic two-tone acoustic JARVIS chime.
- **Multi-State AudioOrb**: Visual reactor reflecting `idle`, `listening`, `thinking`, and `speaking` states.

### ⚡ Phase 4 — Proactivity Engine
- **Background Scheduler**: Async background daemon inspecting pending reminders and tracked projects.
- **Proactive WebSocket Broadcaster**: Pushes unprompted alerts and notifications to connected clients.
- **Autonomous Executive Briefing**: Compiles calendar items, open project tasks, and telemetry on schedule or on demand.
- **Intelligent Follow-Up Engine**: Follows up on open action items (e.g. *"Following up on BEKKI: Have you checked the deploy logs?"*).

### 🛡️ Phase 5 — Guardrails & Safety
- **Risk Guardian Gatekeeper**: Assesses risk levels (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`). Mutating/destructive actions halt execution and require explicit user authorization (*"Confirm"* or click *Authorize*).
- **Immutable Audit Trail**: Structured logging of all tool decisions, risk evaluations, and execution outcomes in `data/audit_log.json`.

---

## 🧪 Running the Test Suites

Run the full end-to-end regression test suite across all 5 phases:
```bash
cd backend
python -m pytest -q
```
Pytest uses temporary memory storage, disables Gemini and speech network calls, and tests current behavior. Code-runner tests verify that execution fails closed until the isolated runner is available. The legacy standalone scripts do not load pytest's test isolation; use pytest for routine checks. Dependency and UTC timestamp deprecation warnings remain.
