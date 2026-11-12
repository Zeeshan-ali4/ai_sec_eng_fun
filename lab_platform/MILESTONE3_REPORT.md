# Milestone 3 implementation report

Implemented on `feature/ai-lab-milestone-03`, starting from clean Milestone 2 commit `2f55fa7`. Scope stops at Milestone 3.

## Delivered

All five challenges have registry definitions, vulnerable/hardened modes, isolated histories and working state, server evaluation, local instructor review, reset support and student UI. Original vulnerable dealership chat and the strictly validated sales tool remain available. Hardened responses use deterministic public-data rendering; no protected canary or edited document is sent to a model. Synthetic canaries are runtime-only, session/run-specific and absent from student metadata and ordinary evidence transcripts. SQLite migrations preserve prior records. Reference demo-data was not changed.

| Challenge | Status | Evaluation |
| --- | --- | --- |
| CH-001 role manipulation | Implemented; reuses Milestone 2 | Inconclusive/manual, heuristic labelled |
| CH-002 commercial statements | Implemented; authoritative hardened pricing/status | Semantic claims manual; invalid action-record status deterministic |
| CH-003 synthetic disclosure | Implemented | Exact assistant disclosure, excluding retained user-supplied values |
| CH-004 weak filters | Implemented | Independent acceptance, disclosure and output bypass results |
| CH-005 document injection | Implemented | Controlled per-session revision/provenance; semantic influence manual |

## Files

Created: `lab_platform/challenges/__init__.py`, `challenges/registry.py`, `security/__init__.py`, `security/weak_controls.py`, `security/hardened_controls.py`, `security/evaluations.py`, `data/challenge_documents/support-001.txt`, `tests/test_milestone3.py`, and this report (paths after the first are relative to `lab_platform/`).

Modified: root `README.md`; `lab_platform/README.md`, `app.py`, `challenge_service.py`, `chat_service.py`, `database.py`, `event_logger.py`, `instructor.py`, `static/app.js`, `static/style.css`, `templates/index.html`, `tests/test_api.py`. The legacy cookie assertion now checks decoded fields instead of matching a two-character string against random signature bytes.

## Validation

84 automated tests pass, including the 54 previous Milestone 1/2 cases. Ollama is mocked; SQLite integration cases use temporary databases. Python compileall, JavaScript syntax and Git whitespace checks pass. Migration test upgrades a legacy attempts table twice and preserves historical content/decisions. No original reference files were modified; no real secrets, runtime values or unsafe tools are included in the changes.

Headless system Chromium/Playwright exercised challenge/mode selection, authoritative Nomad answers, document editing/revisions and hardened source exclusion. Checked laptop 1366×900 and mobile 390×900: no horizontal overflow or JavaScript errors. Flask started on 127.0.0.1 with model-unavailable feedback. Screenshots and browser scripts remain in ignored `work/`; no runtime evidence is committed.

## Unverified behaviour and limitations

Ollama is not installed in this environment. Real `llama3.1:8b` attack responses, generation options/digest/hardware, tool compatibility and Windows/macOS startup have not been verified. Run the reproducible two-mode acceptance matrix in README locally; attack success varies.

The owner-confirmed role escalation, invented 10% discount, false deposit/reservation, rejected sales-tool call and false `ENQ-001` save claim are preserved in README. The known sales-tool compatibility defect remains unresolved; its schema/validation were not weakened. A model claim does not prove an application write.

Hardened mode trades conversational flexibility and model-driven interest writing for deterministic public responses. Original interest writing remains in vulnerable mode. Keyword indicators are not semantic proof; encoded-disclosure detection covers a finite set of harmless representations. The process and OS/database account are trusted; this is not production authentication or a tamper-resistant audit store. No live model comparison results are claimed.

## Startup, acceptance and review

From repository root, in one terminal: `ollama pull llama3.1:8b`, then `ollama serve` if not already running. In another:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r lab_platform/requirements.txt
.venv/bin/python -m lab_platform.app
```

Open http://127.0.0.1:5000. Choose each challenge, restart it, run the README acceptance prompt/document in vulnerable mode, then repeat it unchanged in hardened mode. Inspect evaluations/component results, source revisions and tool flags; submit the latest completed attempt. Verify ordinary vehicle/offer/test-drive questions and separate private-browser sessions. Conversation reset retains working state; challenge reset restores the selected document/rotates the selected canary while preserving evidence.

Local instructors review full evidence and override semantic/inconclusive decisions without changing original evaluations:

```sh
.venv/bin/python -m lab_platform.instructor report > lab_platform/runtime/report.json
.venv/bin/python -m lab_platform.instructor decide --attempt 1 --decision 'Passed'
```

Stop Flask before full resets and archive evidence first: `.venv/bin/python -m lab_platform.instructor reset-lab --confirm`, then restart Flask. No global reset or scoring write is exposed over HTTP. Full operating instructions, trust boundaries, limits and per-challenge test matrix are in README.

The user explicitly approved publishing feature/ai-lab-milestone-03 and creating a pull request against main. The pull request description contains this implementation summary and validation results.
