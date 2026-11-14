# LARA Phase 1 audit

Audited October 24, 2026. Scope: inspect the existing app, preserve existing work, repair immediate blockers, and establish the backlog for phases 2–6. No live Gemini requests, email sends, WhatsApp messages, or system-control actions were used for verification.

## Existing structure

- `backend/app/main.py`: FastAPI entry point, CORS, scheduler lifespan.
- `backend/app/api/router.py`: chat, health, memory, tool execution, approvals, audit logs, briefings, follow-ups, device info, mail, files, apps, and TTS endpoints.
- `backend/app/api/websocket.py`: chat socket and proactive event registration.
- `backend/app/services/llm_service.py`: Gemini SDK initialization, fallback responses, regex intent dispatch, memory context construction, single and compound tool calls.
- `backend/app/memory/`: local JSON facts/projects/sessions, optional Firestore integration, vector recall, and regex extraction.
- `backend/app/skills/`: search, reminders, Python, Windows system/file controls, email, and WhatsApp integrations.
- `backend/app/guardrails/`: risk classification, in-memory approval tickets, JSON audit history.
- `backend/app/proactivity/`: periodic worker and briefing generator.
- `frontend/src/app/`: Next.js App Router, global HUD styles, main dashboard.
- `frontend/src/components/`: chat, message/tool output, animated visualizers, memory inspector, approval modal, alert banner, mail/files/apps, and device bridge.
- `frontend/src/hooks/useVoiceAssistant.ts`: browser speech recognition and synthesis, wake phrase matching, manual listening, echo suppression, and neural audio playback.
- `backend/background_lara.py`: optional Windows background voice daemon, distinct from browser voice.

## Feature audit

| Feature | Exists | Broken, partial, or missing | Completion phase |
| --- | --- | --- | --- |
| Persistent memory | JSON facts, projects and sessions; vector search; profile and upsert routes; memory HUD | All facts/projects enter every prompt. Saved session history is not supplied to Gemini. No fact/project/episodic delete lifecycle or consistent editing. Offline vectors use process-randomized Python hashes, so persistence across restarts is unreliable. Embedding model/version is not recorded. JSON writes lack transactional concurrency guarantees. Firestore project reads still use the local cache. | 2 |
| Agent orchestration | Regex single/compound intent routing and sequential calls | No planner abstraction, retries, dependency handling, task persistence or safe automatic continuation after approval. Socket streaming splits a finished response into words; it does not stream model output or intermediate steps. Synchronous Gemini calls block async handlers. No swappable provider interface. | 2 |
| Tools | DuckDuckGo instant answers, JSON reminder create/list/delete, Python tool interface, additional Windows integrations | Instant answers are not comprehensive web search. Reminder times are free text; no snooze/recurrence or validated date handling. Former Python subprocess had host filesystem/network access and no CPU/memory/output limits; execution is now disabled pending a real sandbox. Additional system/WhatsApp integrations contain shell/UI automation and need stronger parameter boundaries. | 3 |
| Approval | Risk metadata, tickets, approve/reject endpoint, HUD modal, decision logs | Direct execution and compound calls bypassed the guardian; repaired. Tickets lacked owner checks; repaired for supplied user IDs. IDs are still caller-supplied, not authenticated identities. Tickets are not durable, expiring, or scoped to a resumed plan. No full safe/approval/blocked policy. Audit JSON is rewritten, not immutable/tamper-evident. | 3 |
| Voice | Browser interim transcripts, wake phrase matching, manual mic controls, TTS fallback, state visualizers | Browser recognition is not a dedicated local wake-word engine or a server audio stream. Browser compatibility and permission handling need end-to-end work; mic errors are stored in the hook but not fully shown in the HUD. Backend Edge TTS/gTTS dependencies are absent from requirements; gTTS is blocking and network synthesis is unbounded. No real microphone test performed. | 4 |
| Proactivity | Async 45-second scheduler, project follow-ups, on-demand briefing, socket broadcaster, polled alert banner | Pending reminders are shown regardless of due time. Only the first alert is broadcast; repeated events are not deduplicated. No daily briefing schedule, browser notifications, delivery persistence or user-scoped socket subscriptions. Frontend currently polls every 15 seconds rather than subscribing. | 5 |
| HUD and delivery | Responsive styled React dashboard, loading/error UI, conversation, tool results, memory, approvals and alerts | No dedicated task/reminder/briefing management panels. Approval results were discarded and replaced with another chat request; repaired. No deployment configuration, accessibility/visual QA or complete frontend test coverage. The old lint script lacks configured lint tooling. | 6 |

## Phase 1 changes

1. Routed direct tool calls through the existing guardian and added safe-call audit logging. Compound calls now assess each step and stop before a risky action. Completed steps are retained in the response; later steps require a new request until the planner can resume them in phase 2.
2. Required approval for WhatsApp mutations, host system/file actions and unclassified tools. Reminder completion now uses the deletion gate.
3. Added random ticket IDs and owner checks before consuming tickets. Tickets cannot be approved/rejected by a different supplied user ID or replayed after consumption. This does not replace authentication.
4. Disabled the unsafe host Python runner and removed its execution path. The registered tool returns `sandbox_unavailable`; user approval cannot re-enable host execution.
5. Rejected empty reminder deletion targets, which previously matched every reminder.
6. Fixed search query encoding using HTTP query parameters and stopped reporting successful search when no answer/provider response exists.
7. Restricted HTTP CORS and browser WebSocket origins to configured frontend origins. Changed the default bind address to loopback and resolved the backend `.env` relative to the backend directory.
8. Displayed actual approval execution results in chat, propagated approval errors and corrected failed-execution status reporting.
9. Added ignore rules and removed `backend/.env` from the Git index while keeping the local file. Existing commits still contain its prior contents; any actual credentials committed there need rotation. Existing tracked generated files and private data also remain a repository-hygiene follow-up; ignore rules alone do not remove previously tracked files.
10. Added isolated pytest storage, disabled Gemini/speech network calls during tests, declared async test support, fixed Windows test-output handling and updated legacy assertions to match the disabled runner. Search unit tests use a controlled provider response.

## Validation

- Full backend pytest suite passes, including approval bypass/owner/replay, blocked host execution, reminder targeting, search failure, origin restrictions and app lifespan coverage.
- TypeScript check and Next.js production build pass.
- Started FastAPI on loopback port 8011 with temporary data and Gemini disabled; live health, fallback chat, memory profile, tool listing and briefing requests returned HTTP 200.
- Started the production frontend on loopback port 3100 and verified HTTP 200.
- Real Gemini inference, neural speech services, microphone permissions, Windows automation and external messaging remain unverified integrations. Existing tests do not establish sandbox availability or full feature completeness.
- Current dependencies emit Starlette/httpx and naive UTC timestamp deprecation warnings. Dependency locking and upgrades remain phase 6 work.

## Engineering backlog before deployment

Authentication/authorization is absent; supplied user IDs are not a security boundary. There is no rate limiter, comprehensive parameter schemas, request/output size policy, global sanitized error handling, production structured logging or hardened deployment. File browsing exposes arbitrary directory metadata. Synchronous disk/cloud/mail/system work still runs inside async paths. Existing stores include demonstration records (including sample mail), which must not be presented as live account data. Complete these items before any public or shared-network deployment.

Next: phase 2 extends the memory layer and introduces a provider interface and resumable planner without replacing working HUD components or registered skills.
