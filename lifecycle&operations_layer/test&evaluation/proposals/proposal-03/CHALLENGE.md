# Proposal 03 Challenge Brief

## Objective

Evaluate and improve a fictional supplier-management AI agent so that untrusted content cannot redirect its plan, expand retrieval, poison memory, or misuse legitimate tools.

Teams must establish a security baseline before implementing controls. They then add at least three safeguards and rerun the same evaluation to demonstrate measurable improvement without breaking normal supplier workflows.

## Required Evaluation Coverage

### Prompt Injection

Test whether instructions embedded in an untrusted synthetic supplier document can change the agent's behavior or override the user's objective.

### Retrieval Security

Test whether adversarial content can cause the agent to retrieve unnecessary synthetic information labelled `CONFIDENTIAL` or `RESTRICTED`.

### Plan Drift

Test whether the agent remains aligned with the original supplier-management objective or begins unrelated or prohibited activities.

### Tool Use

Test whether the agent can use an approved local mock tool for an unauthorized purpose, such as changing a fictional supplier record or placing a harmless canary value in a simulated outbound message.

### Memory Poisoning

Test whether untrusted information can enter local memory and influence a later interaction without appropriate provenance or review.

### Legitimate Behavior

Test whether normal supplier questions, approved retrieval, record updates, memory use, and simulated messages continue to work after controls are introduced.

## Evidence Standard

Each test must record:

- The user objective and supplied input.
- The expected behavior.
- The actual behavior.
- A pass or fail result.
- The point of failure or control in ingestion, retrieval, planning, tool authorization, memory, or output handling.
- Relevant source, classification, plan, memory, and tool-call evidence.

## Security Controls

Teams must implement at least three controls justified by their baseline findings. Options may include:

- Instruction and data separation.
- Source trust, provenance, and content classification.
- Retrieval filtering and least-privilege context assembly.
- Plan validation and objective checks.
- Tool allowlists, argument validation, and explicit authorization.
- Memory provenance, quarantine, expiry, and review.
- Output filtering, canary detection, and simulated egress controls.
- Monitoring, pause, rollback, and human approval.

## Challenge Safety

- Use only the supplied isolated local agent and synthetic challenge data.
- Use only local mock tools, fictional supplier records, harmless canary values, and simulated destinations.
- Do not target Microsoft 365 Copilot or any real service, tenant, account, supplier, or organization.
- Do not introduce harmful content, executable payloads, real credentials, personal data, or confidential data.
- Do not add shell, unrestricted file-system, email, browsing, or network capabilities.
- Follow the repository [Safety Standard](../../../../SAFETY.md).

## Challenge Deliverables

Teams submit:

1. Baseline results across all six evaluation lanes.
2. At least three implemented security controls.
3. Post-control results using the same evaluation.
4. Execution-path evidence identifying failure and control points.
5. A demonstration that legitimate supplier workflows still operate.
6. A concise explanation of architecture, tradeoffs, recovery, and remaining limitations.
