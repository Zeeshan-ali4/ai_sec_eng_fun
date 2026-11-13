# Milestone 6.1: Investigator Mode

[Host & Organiser Runbook](../../lifecycle&operations_layer/test&evaluation/proposals/proposal-02/HOST_FACILITATOR_RUNBOOK.md) covers complete installation, all seven investigations, trusted recovery and workshop facilitation.

Open `http://127.0.0.1:5000/proposal-02/poisoning` after the startup in
[IMPLEMENTATION.md](IMPLEMENTATION.md). Follow root `SAFETY.md`.

## Learning and protection

New tabs default to **Investigator**. Learning mode is independent of **Vulnerable /
Hardened** protection. Changing learning mode makes no API call and changes no
records, model settings, trust, review permissions or evidence. Guided retains the
seven prepared demonstrations described in [MILESTONE6.md](MILESTONE6.md).

Investigator shows an incident, objective, accurate target scope, permitted testing,
tools and an eight-stage workflow. It starts with a blank answer and question,
neutral rating 3 and an ordinary source label. Choose a fictional account freely;
this is metadata, not authentication. You may revisit stages and retry at any time.
Progress through the interface does not establish attack success.

Guided shows the weakness, trusted reference, controlled trigger and demonstration
instructions immediately. Selecting a fresh scenario while Guided loads its sample
and question. Switching modes preserves your draft. **Use Guided Example** explicitly
asks before replacing question, answer, rating, account and source label. It retains
notes, sandbox state and evidence. Returning to a scenario restores its saved draft.

## Independent investigation

1. Explore approved Knowledge Base in the clean support app (link opens another tab).
2. Write a hypothesis in the worksheet.
3. Choose a legitimate question within the displayed scope; ask the clean snapshot.
4. Write your own harmless fictional conflicting claim or inert document instruction.
5. Choose metadata, submit manually and ask the current sandbox with the same question.
6. Inspect the concise outcome and actual response, then expand full comparison,
   ranking and technical JSON for scores, sources and ingestion decisions.
7. Switch protection mode, keep the same four input fields, submit and query again.
   Record the difference in your worksheet. Individual queries show the current stage
   and its available clean baseline; they do not merge unrelated manual experiments.
8. Explain the result, reset each tested protection mode and query again to check recovery.

**Run automated comparison — optional** remains available without a gate. Try a manual
experiment first. Replay submits the identical four fields to both modes and makes
three separate actual Ollama calls. It adds to existing history; reset both modes
first for a fresh comparison. Never treat acceptance, retrieval or changed wording
as proof of incorrect claims. Refusal can coexist with retrieval manipulation.
Marker quotation is not proof of instruction following. No semantic grader exists.
Missing Ollama means no observed model response; retrieval evidence is still useful.

## Seven scopes and hints

| Scenario | Investigation scope and objective |
| --- | --- |
| DP-001 | LK-005 warranty: compare ratings/account metadata and retrieval priority. |
| DP-002 | LK-001 Hub setup: distinguish document acceptance, retrieval and instruction following. |
| DP-003 | LK-006 returns: compare repeated claims across distinct synthetic sources. |
| DP-004 | LK-005 warranty: compare queries with/without a controlled retrieval trigger, not model-weight training. |
| DP-005 | LK-006 returns: compare exact same-source duplicates and independent source counts. |
| DP-006 | LK-005 warranty/exclusions: distinguish a proposed correction from an authorised policy change. |
| DP-007 | LK-005 warranty: compare fictional account reputation and ratings. |

Backend targets and inherited keywords are unchanged. Arbitrary topics, trigger
phrases and correction targets are unsupported. Students design wording, questions
and metadata within these scopes. Three scenario-specific hints are centralised in
`static/proposal2/investigation.js`: conceptual, investigative, then practical.
Reveal one at a time; the count is visible. Failures never reveal hints automatically.
The final DP-004 hint supplies `starlight mode`; DP-003/005 distinguish distinct-source
repetition from same-source duplication. Hints carry no penalty and survive protection
switches. Guided examples are educational aids, not protected secrets; existing APIs
still return compatible scenario metadata.

## Worksheet and persistence

Expand **Investigation worksheet — notes and export**.
Hypothesis, attack design, observed evidence, defensive comparison and conclusion are
freely editable. Markdown/JSON downloads include scenario ID/title, current learning
mode, timestamp and up to 100 query identifiers with protection mode, stage and
generation. IDs are table-local, so retain the mode. Exports contain only notes and
these identifiers, not account details, system prompts or hidden scoring data.
Markdown escapes HTML and formatting characters; JSON preserves the exact entered notes.
The separate technical evidence download is unchanged and contains SQLite records.

Learning preference is tab-local `sessionStorage`, keyed by the server evidence session. Drafts, hints, notes and identifiers
are keyed by the hashed server evidence session and scenario, shared across protection
modes within that tab. Refresh retains them. Closing a tab normally clears them;
browser session restoration or tab duplication may restore/copy session storage.
Separate tabs can keep different notes while sharing the same server cookie/sandbox.
A new browser profile or server signing-key change creates a separate evidence session.
Notes are not authoritative SQLite evidence and never enter model context. Storage
failure shows a warning; export before refreshing. Use browser site-data clearing to
remove all local notes/preferences (this also clears cookies). Export first.

**Restart learning** confirms before clearing only the selected scenario’s notes and
hint count; it keeps the draft and experiment references. **Reset current scenario**
resets only the selected server session/scenario/protection dataset, retaining old
SQLite evidence and browser notes/hints. Neither is forensic evidence deletion.
Trusted local organiser recovery remains as documented in Milestone 6.

## Optional PowerShell API exercise

No terminal is required. Optional task: without the browser’s Inject button, submit
a fictional record through the local API and inspect whether retrieval order changes.
Use only the student APIs below. Review, approval, publication, quarantine and rollback
are trusted local organiser operations, unavailable through student HTTP APIs.

PowerShell has its own cookie session; it does not automatically share the browser
sandbox. Keep `-WebSession $labSession` on subsequent calls. Start Flask locally first.
Run from the repository root; choose your own fictional text and question in scope.

```powershell
$base = 'http://127.0.0.1:5000/proposal-02/poisoning/api'
# GET state; create and retain a signed cookie session
$state = Invoke-RestMethod "$base/state" -SessionVariable labSession
$state.scenarios | Select-Object id, title, target_id, topic
# POST JSON: choose scenario and protection independently
Invoke-RestMethod "$base/select" -WebSession $labSession -Method Post -ContentType 'application/json' -Body '{"scenario_id":"DP-001"}'
Invoke-RestMethod "$base/mode" -WebSession $labSession -Method Post -ContentType 'application/json' -Body '{"mode":"vulnerable"}'
$question = Read-Host 'Your warranty question'
$cleanBody = @{question=$question;stage='clean'} | ConvertTo-Json
$clean = Invoke-RestMethod "$base/query" -WebSession $labSession -Method Post -ContentType 'application/json' -Body $cleanBody
$payload = @{answer=(Read-Host 'Your fictional conflicting claim');account_id='new';rating=3;source_label='api-practice'}
$payloadBody = $payload | ConvertTo-Json
Invoke-RestMethod "$base/inject" -WebSession $labSession -Method Post -ContentType 'application/json' -Body $payloadBody
$currentBody = @{question=$question;stage='current'} | ConvertTo-Json
$current = Invoke-RestMethod "$base/query" -WebSession $labSession -Method Post -ContentType 'application/json' -Body $currentBody
$current | ConvertTo-Json -Depth 40
$current.sources | Select-Object rank, source_id, trust_level, score
# Repeat identical payload and question against the independent hardened dataset
Invoke-RestMethod "$base/mode" -WebSession $labSession -Method Post -ContentType 'application/json' -Body '{"mode":"hardened"}'
Invoke-RestMethod "$base/inject" -WebSession $labSession -Method Post -ContentType 'application/json' -Body $payloadBody
$protected = Invoke-RestMethod "$base/query" -WebSession $labSession -Method Post -ContentType 'application/json' -Body $currentBody
$protected | ConvertTo-Json -Depth 40
# GET exports both protection modes for this session/scenario
Invoke-WebRequest "$base/export" -WebSession $labSession -OutFile lab_platform/runtime/investigation-evidence.json
# POST reset affects the currently selected hardened sandbox only
Invoke-RestMethod "$base/reset" -WebSession $labSession -Method Post -ContentType 'application/json' -Body '{}'
Invoke-RestMethod "$base/query" -WebSession $labSession -Method Post -ContentType 'application/json' -Body $currentBody
```

A query can return HTTP 503 with recorded retrieval and a null answer when Ollama
is unavailable; Windows PowerShell may throw. Inspect exported evidence before
retrying; start local Ollama and confirm `llama3.1:8b`. No remote fallback exists.
Submission limits, validation and quotas are the existing Milestone 6 limits.

## Facilitation and troubleshooting

Select Guided, choose DP-001, explicitly load its example if a draft is present,
ask clean, inject and compare. Explain actual observed differences. Switch to
Investigator and ask students to design their own tests. Encourage a hypothesis
before offering the next hint; reveal practical hints when students are stuck.
Returning to Guided for troubleshooting preserves their work. No facilitator account
or separate authority is introduced. Follow Milestone 6 for all seven demonstrations.

If nothing is retrieved, check the configured target/topic and lexical question terms.
If a claim is retrieved but not adopted, record both facts; do not mark automatic
success. If history affects a comparison, export, reset both modes and repeat the same
sequence. On refresh, displayed model tables start empty; SQLite evidence remains
exportable and query IDs remain in the worksheet. Export notes before closing a tab.

## Validation

From repository root, after the shared installation:

```sh
python -m pytest -q
python -m compileall -q lab_platform
node --check lab_platform/static/app.js
node --check lab_platform/static/proposal2/app.js
node --check lab_platform/static/proposal2/poisoning.js
node --check lab_platform/static/proposal2/investigation.js
node --test lab_platform/proposal2/tests/investigation.test.cjs
```

Optional browser tests in `test_investigator_browser.py` use Playwright/Chromium if
already installed (`CHROMIUM_PATH` selects an executable). They use real Flask/SQLite
and a mocked model; skipped browser tests do not constitute browser acceptance.
Real Ollama and Windows PowerShell execution require local acceptance. No new runtime
dependency, ingestion mechanism or security-policy modification is introduced.

### Verification recorded on 13 November 2026

- Complete repository suite: **265 passed**, including 11 Chromium browser cases
  against actual loopback Flask/temporary SQLite with a mocked Ollama client.
- Node guidance checks: **8 passed**. Python compilation, all four JavaScript syntax
  checks and `git diff --check` passed.
- Browser checks covered all seven initial views and progressive hints, explicit
  example replacement/cancellation, manual weak/hardened submissions, quarantine,
  optional real-backend replay, reset, safe HTML-like notes, both downloaded formats,
  refresh, new-session and shared-cookie tab isolation, disabled browser storage,
  no page errors, and mobile overflow at 390 pixels. Desktop screenshots were also
  inspected at 1440 pixels. Notes were absent from model messages and authoritative
  exports; clean knowledge and Proposal 1 database bytes remained unchanged.
- No real Ollama executable/service was available; a loopback `/api/tags` probe failed
  to connect. No actual model effectiveness, semantic success or Windows PowerShell
  execution is claimed. Browser automation is optional development tooling and is
  not added to runtime requirements.
- Security services, routes, ranking, registry weights, fixtures, model settings,
  original tests and Proposal 1 implementation have no changes in this milestone.
