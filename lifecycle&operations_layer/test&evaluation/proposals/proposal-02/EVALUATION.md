# Proposal 02 Evaluation

The rubric should reward measurable resistance to controlled poisoning while preserving accurate and useful support behavior.

## Proposed Scoring Areas

- **Clean benchmark quality:** Defines repeatable expected behavior, trusted references, and clear pass or fail criteria.
- **Poisoning analysis:** Measures changes caused by ratings, hidden instructions, repetition, triggers, duplicates, corrections, and untrusted accounts.
- **Trust and provenance controls:** Uses source identity, classification, reputation, and traceability appropriately.
- **Ingestion and retrieval controls:** Applies validation, deduplication, rate limits, quarantine, or review where justified.
- **Monitoring and recovery:** Detects unexpected influence and demonstrates pause, snapshot, rollback, and recovery.
- **Legitimate behavior:** Preserves domain accuracy, useful answers, refusals, consistency, and uncertainty handling.
- **Evidence quality:** Provides reproducible results, logs, design reasoning, and honest residual limitations.
- **Safety and compliance:** Uses only the authorized environment and synthetic benign materials.

## Recommended Method

- Score the same benchmark before poisoning, after poisoning, and after participant controls.
- Use visible practice cases and separate protected judging cases.
- Require evidence linking changed behavior to accepted or retrieved sources.
- Give legitimate behavior enough weight to discourage rejecting every submission or question.
- Rerun nondeterministic cases using a predefined repeat count and adjudication rule.
- Treat safety-boundary violations as disqualifying or apply a substantial penalty.
- Require judges to record reasons for subjective decisions using a shared scoring guide.

## Required Evidence

- Clean, poisoned, and post-control result tables.
- Configuration or code identifying implemented safeguards.
- Provenance, acceptance, retrieval, and behavior logs.
- Demonstration of clean reset and rollback.
- Explanation of tradeoffs, false positives, bypasses, and residual risk.

## Decisions Required Before the Event

- Total points and weighting for each scoring area.
- Mandatory controls, pass conditions, and disqualification rules.
- Number and composition of visible and protected cases.
- Repeat count and adjudication for nondeterministic responses.
- Whether local RAG is included or the approved-answers path is used.
- Tie-breaking process, submission format, and presentation duration.
