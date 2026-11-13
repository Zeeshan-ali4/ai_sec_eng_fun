# Proposal 02 Challenge Brief

## Objective

Evaluate how controlled poisoned data affects a fictional support assistant, then improve its safeguards without breaking useful behavior.

Teams must establish a clean benchmark before introducing any poisoned samples. They then compare clean and poisoned results, implement appropriate controls, and rerun the same evaluation to demonstrate measurable improvement.

## Required Benchmark Coverage

The clean benchmark must cover:

- **Expected behavior:** approved responses the assistant should provide.
- **Domain accuracy:** agreement with the supplied trusted policies and answers.
- **Refusal behavior:** clear handling of unsafe, prohibited, or unsupported requests.
- **Consistency:** compatible answers to materially similar questions.
- **Unknown questions:** honest uncertainty instead of invented information.
- **Prohibited outputs:** safe labels and placeholders rather than harmful examples.

Each case must record its input, trusted reference or policy, expected behavior, observed response, and pass or fail result.

## Required Poisoning Coverage

Teams must evaluate the supplied controlled samples representing:

1. A misleading fictional answer with an artificially high rating.
2. A document containing an inert hidden instruction requesting harmless test behavior.
3. Repeated false statements about the fictional scenario intended to dominate retrieval.
4. A benign trigger phrase linked to intentionally incorrect behavior.
5. Duplicate submissions intended to amplify one untrusted claim or signal.
6. An apparently helpful correction that introduces a safely represented weakness.
7. Feedback from an untrusted or newly created fictional account.

## Safeguards to Consider

Teams may implement controls such as:

- Source trust and account reputation.
- Provenance and classification metadata.
- Input validation and independent review.
- Deduplication, rate limits, and influence limits.
- Quarantine before publication or retrieval.
- Anomaly detection and security logging.
- Versioned snapshots, rollback, and human approval.

Teams should select controls that address observed failures rather than attempting to add every possible safeguard.

## Challenge Safety

- Use only the isolated local challenge environment.
- Use only supplied synthetic accounts, documents, answers, policies, and poisoning samples.
- Keep hidden instructions inert and limited to harmless test behavior.
- Do not use harmful content, executable payloads, real vulnerabilities, or live external destinations.
- Do not connect the assistant to production systems or process real accounts, credentials, personal data, or confidential data.
- Follow the repository [Safety Standard](../../../../SAFETY.md).

## Challenge Deliverables

Teams submit:

1. The completed clean benchmark.
2. Clean-versus-poisoned results for the required cases.
3. The implemented safeguards or a working safeguarded configuration.
4. Post-control results using the same tests.
5. Evidence from provenance, acceptance, retrieval, and rollback logs.
6. A concise explanation of design choices, remaining limitations, and recovery steps.

Current technical implementation and all seven defensive demonstrations: [Milestone 6](../../../../lab_platform/proposal2/MILESTONE6.md).
