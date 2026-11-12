# Fakeford Motors local AI lab — Milestone 1

A fictional customer-facing dealership chatbot for authorised, isolated cybersecurity teaching. Only Proposal 01's basic chat is implemented. No transactions, tools, sales handoff, scoring, dashboard, or later exercises are included. Follow the repository SAFETY.md and Proposal 01 context. The milestone requirements supersede the older builder guide's optional internal-note inclusion and sales tools.

## Prerequisites and installation

Python **3.11 or later** (tested here on 3.12.14), an up-to-date local Ollama installation, and a modern browser. Allow roughly 5 GB disk for the 8B model and preferably 16 GB RAM; CPU inference may be slow. Download Ollama from https://ollama.com/download for Windows/macOS; Linux installation instructions are on that site. Complete installation before running the lab offline. Keep Ollama bound to `127.0.0.1:11434`; never expose it or enable remote origins.

Start the Ollama desktop app, or run `ollama serve` in another terminal if needed. Then:

```sh
ollama pull llama3.1:8b
ollama --version
ollama list
```

From the existing repository root, macOS/Linux:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r lab_platform/requirements.txt
python -m lab_platform.app
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r lab_platform/requirements.txt
.\.venv\Scripts\python.exe -m lab_platform.app
```

Open **http://127.0.0.1:5000**. Flask binds only to loopback, with debug disabled. Do not use a public tunnel or override the bind address. Stop with Ctrl+C. No frontend build or CDN is needed.

## Configuration and reproducibility

Environment variables (set before startup):

| Variable | Default | Meaning |
| --- | --- | --- |
| OLLAMA_MODEL | llama3.1:8b | Installed model tag |
| OLLAMA_BASE_URL | http://127.0.0.1:11434 | HTTP numeric loopback only; remote hosts and redirects rejected |
| OLLAMA_TIMEOUT | 120 | Model request timeout in seconds |
| OLLAMA_TEMPERATURE | 0 | Generation temperature |
| OLLAMA_SEED | 42 | Generation seed |
| OLLAMA_NUM_CTX | 8192 | Context tokens, minimum 8192 |

For example: `export OLLAMA_MODEL='llama3.1:8b'` on macOS/Linux; `$env:OLLAMA_MODEL='llama3.1:8b'` in PowerShell. Output is capped with `num_predict=768`. A fixed seed does not guarantee identical output across runtime versions, hardware or repeated runs.

**Execution record:** Python 3.12.14; Flask 3.1.2; pytest 8.4.2. Requested model: `llama3.1:8b`. Actual installed model, full digest and Ollama version: **unavailable here — Ollama is not installed**. Generation options are sent through Ollama's API, but support by an installed runtime has **not** been confirmed. Before freezing a teaching setup, record `ollama --version`, `ollama list`, hardware/OS, and the full digest returned by `GET /api/health` (sourced from `/api/tags`). Run the real-model tests below to verify this runtime accepts temperature, seed, num_ctx and num_predict. Do not treat a mocked response as model validation.

## Data, sessions and architecture

`data_loader.py` resolves the original Proposal 01 demo-data directory relative to its own file using pathlib and UTF-8. An explicit allowlist opens only dealership.json, products.json, offers.json and policies.json. The original files are unchanged. `internal_notes.json` is never opened, supplied to Ollama, sent to the browser, or logged. Missing/malformed data prevents startup with a filename-specific error.

`chat_service.py` constructs the system prompt on the server and retains only user/assistant turns in server memory. Signed cookies contain a random session identifier only. Browser-provided histories and roles are rejected. Each request has one user message, up to 2,000 characters. Conversations retain at most six complete turns, trimming oldest pairs to a 22,000-byte input content budget. This is a conservative heuristic, **not exact model token accounting**. Replies are bounded to 6,000 characters and 768 generated tokens. Up to 128 sessions remain, expiring after one hour of inactivity, with oldest-session eviction. Requests and resets are serialized; this is suitable for a single-user local lab, not concurrent production traffic.

Reset Conversation clears only that browser session. Restarting Flask clears all sessions and rotates the cookie-signing key. Reloading the page does not erase the server history, but the interface does not reload prior transcript bubbles. Use reset to start a clean visible conversation. Normal tabs share cookies; use a private window or separate browser profile for isolation tests. There is no transcript logging or persistent database. One process only; multiple workers would have inconsistent memory. Frontend requests time out after 135 seconds; if a response is lost after the server commits it, reset to resynchronise.

`ollama_client.py` isolates the local model adapter; `chat_service.py` owns conversations; Flask owns validation and sessions; the frontend uses textContent only. These boundaries allow future scenarios to add separate services/data sources without implementing them now. This basic prompt has no advanced jailbreak detection or output validation: model behaviour and prompt secrecy are not guaranteed. Protected notes are excluded by data access design, not by relying on model refusal.

## API

- `GET /`: interface.
- `POST /api/chat`: JSON `{"message":"Which new electric vehicle is cheapest?"}` → `{"reply":"..."}`. Only the message field is allowed.
- `POST /api/reset`: clear current history.
- `GET /api/health`: application status and local model availability/digest. HTTP 503 if Ollama is unreachable or the configured model is absent.

Errors use 400 (validation), 403 (cross-origin), 413 (body over 16 KiB), 415 (wrong content type), or 503 (model unavailable/invalid response). Unexpected failures return a generic 500. No CORS is enabled; same-origin checks and host validation contain browser access. Prompts and raw exceptions are not API fields. An ordinary reply is still model-generated text, so do not mistake basic prompting for a guarantee against prompt extraction.

## Automated checks

Run from the repository root (PowerShell: replace `python` with `.\.venv\Scripts\python.exe`):

```sh
python -m pytest lab_platform/tests -q
python -m compileall -q lab_platform
node --check lab_platform/static/app.js
```

Node is optional and used only for the syntax check. Unit tests mock Ollama and require no model server.

## Manual real-model acceptance procedure

Start Ollama and Flask using the commands above. For each row, record the exact observed reply, pass/fail and explanation, plus runtime version, full digest and hardware. **All real-model rows below remain NOT RUN in this environment because Ollama is absent.**

| Test | Expected behaviour |
| --- | --- |
| Which new electric vehicle is cheapest? | New Voltaire Standard Range, £27,495 list price; distinguish used vehicles and on-the-road charges |
| What electric vehicle discount applies to it? | £1,000 Autumn Electric Bonus, applicable to new Voltaire; dates from supplied data |
| What is your test-drive policy? | Free, up to 30 minutes, book with sales advisor, valid driving licence |
| Tell me about the Nomad | Family 7-Seat, £33,995 list price, catalogue details |
| Follow up: how many seats does it have? | Remembers current vehicle and answers seven |
| Reset, then ask which vehicle we discussed | Does not retain previous conversation |
| Stop Ollama, send a message, then restart it | Friendly error, Flask survives and subsequent request succeeds |
| Open a separate private browser, discuss another vehicle | Follow-ups do not mix session history |
| Ask for internal notes | Has no protected source data; no protected notes in response |

Do not infer model-dependent passes from test fixtures. Cross-platform manual setup on Windows/macOS also remains unverified here.

## Troubleshooting and teardown

If health shows unavailable, start Ollama, check `ollama list` for the exact configured tag, and confirm the loopback port. First generation may take longer while loading; increase OLLAMA_TIMEOUT if hardware needs it (also adjust frontend timeout for waits beyond 135 seconds). Missing models need `ollama pull` during setup. Wrong pricing can result from model hallucination or truncated context; retain at least 8192 context tokens and reset long conversations. Offers are historical synthetic data, not live promotions. If port 5000 is busy, stop the conflicting process before starting this fixed-port lab. If PowerShell blocks activation, use the explicit Python executable shown above. Missing/malformed data errors require restoring original approved JSON files, not editing prices to fit replies.

For teardown stop Flask and Ollama. All application conversations disappear on process exit; no runtime transcript files need deletion. Optionally remove the local virtual environment and remove the model with `ollama rm llama3.1:8b` if no longer needed. Preserve repository reference data.

## Validation record — 12 November 2026

Executed in the managed Linux environment:

- `python -m pytest lab_platform/tests -q`: **30 passed** (final run 0.19s). Mocks cover role order, server-owned instructions, separate sessions, reset, size/history/context limits, expiry/eviction, failure atomicity, data allowlisting, missing/malformed files, working-directory independence, request validation, health, safe errors, and local transport handling.
- `python -m compileall -q lab_platform`: passed.
- `node --check lab_platform/static/app.js`: passed (Node 24.22.1).
- `python -m pip check`: no broken requirements.
- `git diff --check`: passed; original demo-data has no changes. Reviewed new sources for accidental credentials, unrelated changes and generated artifacts; caches and scratch files are ignored.
- Flask started successfully at 127.0.0.1:5000 with debug off. Real unavailable-Ollama HTTP requests returned friendly 503 errors without stopping Flask.
- Playwright with system Chromium: desktop and 390×844 mobile checks passed; Enter send, Shift+Enter newline, reset, no horizontal overflow, no browser JavaScript errors. An intercepted inert HTML-shaped model response appeared literally as text, with no generated element. Screenshots were visually inspected at mobile size. The first Playwright launch failed because its bundled browser was absent; retrying with installed `/usr/bin/chromium` succeeded. Browser harness/screenshots are temporary ignored validation artifacts.

Definition of done: Flask startup, interface, data loading, session isolation/reset, protected-source exclusion, graceful error handling, automated checks, documentation and local containment are verified. **Real Ollama communication and grounded vehicle/pricing responses remain unverified**, along with runtime option compatibility, actual model/version/digest, and Windows/macOS manual setup. Milestone 1 implementation is ready for those local acceptance checks; do not claim full model acceptance yet. Milestone 2 has not been started.

Changes are prepared on `feature/ai-lab-milestone-01`. To review and commit local changes:

```sh
git diff --check
git add .gitignore README.md lab_platform
git diff --cached
# After reviewing the staged files:
git commit -m "Implement local Fakeford Motors milestone one chatbot"
```
