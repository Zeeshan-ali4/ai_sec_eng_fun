# Proposal 02 — Milestone 4 clean baseline

Lumen Home is a fictional indoor smart-device company, distinct from Fakeford Motors. This milestone supplies clean approved answers, proposed corrections, provenance and a measurable baseline. It does not implement poisoning samples, weakened controls, embeddings, fine-tuning or a facilitator dashboard. Older Proposal 02 builder sketches describe future weak ingestion and Streamlit: use this guide for the current Flask implementation. Follow root `SAFETY.md`.

## Install and start (Windows PowerShell)

Run from the repository root, with approved Python 3.11+, Git, Ollama and a modern browser. Allow approximately 5 GB for the model and preferably 16 GB RAM. Model/hardware suitability and Windows execution still require local acceptance. No extra Python packages beyond the shared requirements are introduced.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r lab_platform/requirements.txt
ollama pull llama3.1:8b
ollama --version
ollama list
# Start Ollama's desktop application, or run this in a separate terminal:
ollama serve
# In the repository terminal:
.\.venv\Scripts\python.exe -m lab_platform.app
```

Open `http://127.0.0.1:5000/proposal-02`. Proposal 1 remains at `http://127.0.0.1:5000/`. On Linux/macOS replace `.\.venv\Scripts\python.exe` with `.venv/bin/python` and create the environment with `python3 -m venv .venv`.

Flask and Ollama must remain on loopback, with debug disabled. Use the module launcher, one process/worker, no public tunnels. The existing loopback-only Ollama client disables proxying, redirects, streaming and tools for plain chat. Defaults remain `llama3.1:8b`, temperature 0, seed 42, context 8192, prediction limit 768 and timeout 120 seconds. Existing `OLLAMA_*` settings apply; record overrides with each run. The browser waits 150 seconds; increasing model timeout requires adapting that timeout too. No real accounts, secrets, external actions, browsing, email, shell or model filesystem tools exist.

## Architecture and files

Browser → shared Flask host/origin/CSP boundaries → separate Proposal 2 blueprint → support service → deterministic retrieval → approved SQLite knowledge → plain shared Ollama client. Source JSON is a separate user-role reference message, never added to system instructions. The server owns all role assignments. Retrieved references show what was supplied, not proof the model used every record correctly.

- `routes.py`: `/proposal-02` and student APIs; no approval or global reset route.
- `knowledge_base.py`: validated clean seed, independent database, versions, checksums and events.
- `accounts.py` and `data/fictional_accounts.json`: five synthetic identity labels.
- `ingestion_service.py`: pending proposals, trusted local review, separate publication.
- `retrieval_service.py`: replaceable lexical ranking.
- `support_service.py`: independent bounded histories, reference messages and evidence.
- `benchmark.py`, `data/clean_benchmark.json`: 18 cases and isolated clean runner.
- `cli.py`: local organiser operations.
- `data/trusted_knowledge.json`: 24 ground-truth articles, dataset `lumen-clean-1`.
- `tests/test_baseline.py`: mocked integration and unit coverage.
- `templates/proposal2/index.html`, `static/proposal2/`: vanilla UI using shared styling.

Shared changes are module registration in `app.py`, a navigation link in `templates/index.html`, and documentation links in root README. Proposal 1 prompts, challenges, tools, scoring, fixtures, database utility and runbook are unchanged.

## Storage, trust and provenance

Active Proposal 2 data lives in `lab_platform/runtime/proposal2.sqlite3`, independent of Proposal 1's `lab.sqlite3`. Python tests can override `PROPOSAL2_DATABASE_PATH`; student APIs cannot choose paths. Reusing Proposal 1's connection utility supplies atomic transactions, busy timeout and the ~64 MiB quota without creating Proposal 1 tables in the new store. Startup validates fixtures before seeding; a missing or malformed fixture fails visibly rather than loading partial knowledge.

`p2_entries` stores `(id, version, status, JSON metadata)`. Each fixture includes topic, approved answer, unique source, classification, trust, version, stable timestamp, approval status, keywords, synthetic account and submission reference. `p2_submissions` preserves original text and account metadata, rating, timestamp, review and lifecycle status. `p2_events` contains timestamp, hashed session ID, event type and JSON evidence. `p2_meta` records dataset version. Students can inspect approved provenance through Knowledge Base; their own proposals/status through Your submissions. Organisers inspect all versions and evidence with `report`.

Trusted approved entries alone are retrievable. Pending and rejected proposals stay outside the knowledge table. Review approval alone does not publish. Publication creates a new approved version and marks an active corrected version `superseded`; retired records remain available locally until clean reset. Ratings and selected account trust never grant privileges or influence ranking. These are training identities, not authentication.

## Submit, review and publish

Choose any fictional account in Submit Knowledge, optionally select a correction target, enter topic and proposed answer, optional explanation/rating, and submit. It must appear as pending and must not change the clean checksum or chatbot's sources. Account IDs are checked, fields are allowlisted, topic ≤200 characters, answer ≤2000, explanation ≤1000 and rating integer 1–5. Each signed session may store up to 100 proposals (including archived proposals); a new process/browser identity does not bypass the database disk quota. Chat messages are ≤2000 characters, responses ≤6000, HTTP bodies ≤16 KiB.

Review is a trusted local OS workflow; it is never selected by the fictional account dropdown. Stop Flask before organiser mutations to avoid stale in-memory conversations or concurrent review work. In a second terminal, inspect the report and use the actual submission ID shown by the UI:

```powershell
.\.venv\Scripts\python.exe -m lab_platform.proposal2.cli report > lab_platform/runtime/p2-report.json
.\.venv\Scripts\python.exe -m lab_platform.proposal2.cli review 1 --decision approved
# Approval is not publication. Inspect the approved review before this explicit step:
.\.venv\Scripts\python.exe -m lab_platform.proposal2.cli publish 1
# Alternative for another pending proposal:
.\.venv\Scripts\python.exe -m lab_platform.proposal2.cli review 2 --decision rejected
.\.venv\Scripts\python.exe -m lab_platform.app
```

Use only commands appropriate to existing pending IDs; approval/rejection cannot be repeated, and only approved proposals can publish. The report traces Submitted → Reviewed → Approved/Rejected → Published with source/account/submission/reviewer/version. Refresh status and knowledge in the browser after restarting. New answers receive `LS-…` IDs; reviewed sources use `LUMEN-SUB-…`. Corrections retain their `LK-…` identity with an incremented version. A correction whose target is no longer active fails publication. The organiser is responsible for factual/content review, including conflicting or duplicate proposals.

## Retrieval and conversation

Lowercase ASCII words/numbers are extracted from the question and each approved topic/keyword list; common stop words are removed. Score is the count of shared distinct tokens. Positive matches sort by descending score, then entry ID, then descending version. Identical normalised topic/answer pairs are collapsed; at most three records are returned. Ties are stable. No rating boost or LLM relevance decision exists. Unknown questions with zero matches receive a server-owned uncertainty answer without a model call. Broad product words can still retrieve loosely relevant records: this intentionally simple method is not semantic search.

Short pronoun follow-ups combine the latest question with the previous user question from the same session. At most six complete turns, 128 histories, one-hour idle expiry and 22,000 bytes of assembled context are retained. Requests/resets serialize within the Proposal 2 service. Evidence persists independently. Reset conversation clears only the current history and retains evidence. Separate browser profiles/private windows have independent signed sessions; tabs share cookies. Restarting Flask clears memory and rotates the signing key; old evidence remains locally accessible to organisers.

## Clean benchmark

```powershell
.\.venv\Scripts\python.exe -m lab_platform.proposal2.cli benchmark > lab_platform/runtime/p2-benchmark.json
```

The runner creates a temporary database from the clean fixture, uses a fresh conversation for each of 18 cases, and removes that temporary database afterward. It neither resets nor inherits the live knowledge store. The complete report is also persisted as a `benchmark` event in the live Proposal 2 database. JSON includes expected question/reference/behaviour/criteria/category/sources, observed source IDs and scores, answer, baseline SHA-256, dataset version, model name/options and model health/digest when available. Missing Ollama is recorded per case as an error, never a semantic pass. The two no-match cases remain useful without inference.

Retrieval checks compare expected sources with observed sources (zero expected requires zero observed). All semantic outcomes require human review even when retrieval passes. Conservative grounding flags identify citations to unretrieved entries, absent entry citations and novel numeric claims; they are review signals and may have false positives. They do not establish factual correctness. Manually compare each generated answer against the full reference and criteria; record review outcomes in a separate locally retained copy. The model does not grade itself. Data/ranking are deterministic; model output is not guaranteed deterministic. Record actual Ollama version, model digest, Git commit, OS/hardware and timings alongside reports.

## Clean reset and retention

Stop Flask first. Export a report if required by the local evidence retention policy, then run:

```powershell
.\.venv\Scripts\python.exe -m lab_platform.proposal2.cli report > lab_platform/runtime/p2-before-reset.json
.\.venv\Scripts\python.exe -m lab_platform.proposal2.cli reset --confirm
.\.venv\Scripts\python.exe -m lab_platform.proposal2.cli status
.\.venv\Scripts\python.exe -m lab_platform.app
```

`--confirm` is mandatory. Reset replaces active and historical knowledge versions with original fixture entries/versions, archives all submissions (preserving their original content and review), retains every event/benchmark report, and appends a reset event. Published knowledge remains traceable in publication events. Restart clears in-memory history. Status must show `state: clean`, 24 entries and `lumen-clean-1`; the canonical approved-entry SHA-256 must match the pre-change clean reference. `modified` means active knowledge differs. Pending proposals alone do not change active state.

Reset never opens or deletes Proposal 1 data. It is not evidence deletion or forensic erasure. Runtime databases, screenshots and reports are Git-ignored; keep exports there. The trusted OS user is responsible for approved evidence retention, backups, access and eventual deletion of the Proposal 2 database/exports with Flask stopped. The quota can halt writes: archive under the local retention policy before capacity is reached. No silent evidence eviction occurs.

## Verification and real-model acceptance

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/health
Invoke-RestMethod http://127.0.0.1:5000/proposal-02/api/baseline
Invoke-RestMethod http://127.0.0.1:5000/proposal-02/api/chat -Method Post -ContentType 'application/json' -Body '{"message":"How long is the warranty?"}'
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q lab_platform
node --check lab_platform/static/app.js
node --check lab_platform/static/proposal2/app.js
```

Real Ollama acceptance has **not** been executed in this environment. Before teaching, record exact observations for:

1. Ask warranty duration: answer should state two years, cite `LK-005`, and display its approved source.
2. Ask the lunar branch address: acknowledge insufficient approved information, no sources or invented address.
3. Propose a harmless warranty correction as ordinary customer: pending status, original warranty still active.
4. Stop Flask, locally review then publish, restart: approved correction/version is retrieved and influences the answer.
5. Inspect Knowledge Base and local report: source, customer, submission, review and version are traceable.
6. Stop Flask, confirmed clean reset, restart: original two-year answer/version/checksum restored; evidence retained.
7. Visit Proposal 1: CH-001–005, vulnerable/hardened selection, evidence and CH-004 no-tool boundary still work.
8. Run benchmark: inspect all expected/observed fields and manually adjudicate semantics; never report retrieval passes as model accuracy.

## Troubleshooting and limitations

- Model unavailable: start local Ollama, check `ollama list` includes exact `llama3.1:8b`, then check `/api/health`. Unknown questions intentionally need no model. No remote fallback exists.
- Unchanged answer after approval: publish separately, restart Flask and refresh the browser. Check source IDs/version rather than relying on generated prose.
- Pending proposal missing: use the submitting browser profile; process restart changes signed identity. Organiser report retains records.
- Clean fixture failure: restore tracked JSON and retry; do not edit runtime SQL to bypass validation.
- No relevant source: lexical coverage is limited; inspect keywords or propose a reviewed answer. Broad terms can retrieve extra references.
- Checksum changed: compare approved entries/versions against fixtures and publication events, then use the documented reset if appropriate.
- Storage error: retain approved evidence and resolve local capacity/permissions; the app fails closed with a generic error.

One trusted local process/OS account is assumed; there is no enterprise authentication, tamper-resistant audit store or hostile-user hosting. Account metadata is synthetic. Manual factual review is essential; prompt separation reduces accidental instruction mixing but cannot prove model resistance to prompt injection or hallucination. No model output is executed. Real inference, Windows/macOS behaviour, performance and human usefulness remain acceptance tasks. Stop after Milestone 4; later weak ingestion, seven poisoning exercises, full RAG and facilitator materials are out of scope.

## Validation recorded for this change

On 13 November 2026, the complete mocked suite passed **160 tests** (103 existing Proposal 1 tests plus 57 Proposal 2 cases). Python compilation and both JavaScript syntax checks passed. Chromium/Playwright at 1440×1000 and 390×1000 verified knowledge loading, unavailable-model errors, no-match answers, pending submissions, literal HTML text rendering, conversation reset, Proposal 1 navigation, no horizontal overflow and no JavaScript page errors. A real local organiser CLI review → publication → reset → report cycle passed; the Proposal 1 SQLite file's byte checksum stayed unchanged. The clean approved-entry checksum was `64cad669b2280829b21318f0750e2fbeb61254e7780310e4f7abb886a111b49f`.

A CLI benchmark without Ollama recorded 18/18 expected-source retrieval checks, 16 model errors and two no-match responses requiring manual review. This is **not** a real-model accuracy result. Ollama is absent here; actual inference, model digest, hardware latency, and Windows/macOS acceptance remain unverified. Runtime evidence and browser screenshots remain ignored local files.
