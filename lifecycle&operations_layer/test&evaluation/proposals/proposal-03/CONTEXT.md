# Proposal 03 Context

## Proposal Summary

- **Working title:** Securing AI Context Against Indirect Prompt Injection
- **Problem:** An AI assistant can encounter adversarial instructions embedded in content that enters its context, potentially causing it to cross trust boundaries and expose information.
- **Intended participants:** People comfortable with basic AI and LLM concepts who are ready to explore agentic AI security.
- **Proposed solution:** Provide a fully built but intentionally vulnerable local supplier-management agent that teams evaluate, secure with at least three controls, and retest.
- **Success criteria:** Establish a repeatable security baseline, implement at least three controls, and rerun the same evaluation to demonstrate measurable improvement without breaking legitimate supplier workflows.

## Real-World Anchor

In 2025, security researchers reported EchoLeak, tracked as CVE-2025-32711, affecting Microsoft 365 Copilot. Microsoft described it as an AI command-injection vulnerability that could allow an unauthorized attacker to disclose information over a network. The reported attack used indirect prompt injection through content that could enter the assistant's context and potentially influence how the assistant handled sensitive information.

Microsoft published the advisory on June 11, 2025, and stated that the vulnerability had already been fully mitigated, with no action required from users of the service.

The case demonstrates that content retrieved or processed by an AI assistant must not automatically be treated as trusted instructions. Systems need explicit separation between data and instructions, controls around sensitive context and outbound information, and monitoring that can identify unexpected behavior across trust boundaries.

For this proposal, EchoLeak is a defensive learning anchor rather than a target or exploit to reproduce. Any challenge must use an isolated assistant, synthetic documents, fictional accounts, and harmless canary values. Participants must not target Microsoft 365 Copilot or any real service, account, tenant, credential, or confidential data.

Source: [Microsoft Security Response Center - CVE-2025-32711](https://msrc.microsoft.com/update-guide/vulnerability/CVE-2025-32711)

## Proposal Documents

- [Challenge Brief](CHALLENGE.md): participant objective, six required evaluation lanes, controls, safety rules, and deliverables.
- [Participant Guide](PARTICIPANT_GUIDE.md): prerequisites, local setup, workflow, rules, and submission checklist.
- [Organizer Guide](ORGANIZER_GUIDE.md): baseline agent, containment, preparation ownership, and delivery stages.
- [Evaluation](EVALUATION.md): execution-path judging areas, method, evidence, and decisions required before the event.

## Hackathon Challenge

Teams first establish a security baseline for the supplied agent before implementing any controls. The evaluation must test the agent across its full execution path rather than assessing only its final response.

### Required Evaluation Lanes

1. **Prompt injection:** Can instructions within an untrusted synthetic supplier document change the agent's behaviour?
2. **Retrieval security:** Can malicious content cause the agent to retrieve unnecessary synthetic information labelled `CONFIDENTIAL` or `RESTRICTED`?
3. **Plan drift:** Does the agent remain aligned with the user's original objective, or does it begin performing unrelated or prohibited activities?
4. **Tool use:** Can the agent use a legitimate local mock tool for an unauthorised purpose, such as changing a fictional supplier record or sending a harmless canary value to a simulated external destination?
5. **Memory poisoning:** Can untrusted information be stored and influence a later interaction?
6. **Legitimate behaviour:** Do normal supplier workflows continue to work after security controls are introduced?

All adversarial documents, sensitive labels, records, destinations, and tool effects must be synthetic and contained within the local challenge environment.

### Evidence and Retest

Each test must record:

- The expected behaviour.
- The actual behaviour.
- A pass or fail result.
- The point of failure in the execution path, such as ingestion, retrieval, planning, tool authorisation, memory, or output handling.

Teams then implement at least three security controls and rerun the same evaluation. Their final evidence must compare the baseline and controlled results, show measurable security improvement, confirm whether legitimate workflows still operate correctly, and identify any remaining limitations.

## Best Suited For

- Participants comfortable with basic AI and LLM concepts.
- Participants ready to move beyond prompt security into agentic AI security.
- Teams interested in AI red teaming, security testing, retrieval-augmented generation (RAG), and agent security.

## Baseline System to Prepare

Teams receive a fully built but intentionally vulnerable supplier-management AI agent. The agent can already:

- Read synthetic supplier documents.
- Retrieve synthetic internal information through RAG.
- Answer questions about fictional suppliers.
- Maintain simple local memory.
- Update a simulated supplier record.
- Create simulated outbound messages.

The baseline must expose enough of its execution path for participants to trace document ingestion, retrieval, planning, memory access, tool requests, tool results, and final responses. Its intentional weaknesses must exist only in the agent's trust, decision, and authorisation logic. The host application must not permit arbitrary code execution, unrestricted network access, or access to real systems and data.

## What Organizers Need to Prepare

### Scenario and Data

- A fictional supplier-management scenario with approved workflows and role boundaries.
- Synthetic supplier documents, including trusted material and benign indirect prompt-injection samples.
- Fictional supplier records and synthetic internal information labelled `PUBLIC`, `CONFIDENTIAL`, or `RESTRICTED`.
- Harmless canary values that make unintended retrieval, memory use, or disclosure measurable.
- Clean and adversarial data snapshots that can be restored between teams or judging runs.

### Baseline Agent

- A local chat interface that shows the user's objective and the agent's final response.
- A document-ingestion and RAG pipeline with visible source and classification metadata.
- Simple session and cross-session memory with visible provenance.
- Local mock tools for reading and updating fictional supplier records.
- A simulated outbound-message tool that writes only to a local outbox.
- Execution logs covering retrieval, planning, memory, tool authorisation, tool results, and output handling.
- Reliable clean reset, adversarial reset, and rollback procedures.

### Evaluation Package

- A clean security baseline covering all six required evaluation lanes.
- Benign adversarial documents and prompts for visible practice cases.
- Separate protected judging cases and expected results.
- A test template recording expected behaviour, actual behaviour, pass or fail, and point of failure.
- Scoring that rewards measurable security improvement while preserving legitimate supplier workflows.

### Participant and Event Package

- Supported operating systems, minimum hardware, pinned versions, and approved installation steps.
- Startup, health-check, reset, rollback, and troubleshooting instructions.
- Architecture and data-flow diagrams that identify trust boundaries and control points.
- Challenge rules, safety boundaries, deliverables, judging criteria, and support routes.
- A timed dry run on representative participant hardware and a clean fallback package.

## Low-Cost Local Architecture

This challenge can run locally without paid model services:

| Component | Recommended local option | Purpose |
| --- | --- | --- |
| Model runtime | Ollama | Runs the approved instruction and embedding models locally. |
| Instruction model | `llama3.1` or another approved small quantized model | Powers the supplier-management agent. |
| Application | Python with FastAPI, Flask, or Streamlit | Hosts the local agent and browser interface. |
| Supplier records | SQLite | Stores fictional supplier data and resettable tool effects. |
| Memory | Separate SQLite tables with session and source metadata | Makes stored information and later influence traceable. |
| RAG store | Chroma or FAISS | Indexes synthetic supplier and internal documents locally. |
| Embeddings | `nomic-embed-text` through Ollama, subject to approval | Creates local document embeddings. |
| Outbound messages | SQLite outbox or local files | Simulates sending without any external connection. |
| Agent tools | Strict Python functions | Limits operations to approved record and outbox actions. |

After approved models and packages are installed, the challenge should require no event-time internet access. A laptop with approximately 16 GB of memory is a reasonable minimum for a small quantized model, while 32 GB is preferable for smoother RAG and multi-step agent execution. Organizers must confirm requirements through a dry run on supported corporate hardware.

### Containment Requirements

- No production, corporate, email, messaging, or external supplier-system integration.
- No real credentials, personal data, confidential data, supplier records, or documents.
- No shell, unrestricted file-system access, arbitrary code execution, or general-purpose network tool.
- Record updates affect only a resettable fictional SQLite database.
- Outbound messages remain in a local simulated outbox and cannot leave the device.
- Every retrieval, memory operation, proposed tool call, tool result, and final response is logged.

## Preparation Action Plan

1. Build the local agent, browser interface, RAG pipeline, memory, SQLite records, narrow mock tools, and simulated outbox.
2. Add execution tracing, clean and adversarial snapshots, reset, and rollback.
3. Define the fictional supplier scenario, trusted workflows, classifications, and expected behaviour.
4. Create synthetic documents, records, canary values, practice cases, and protected judging cases.
5. Define scoring, verify all six evaluation lanes, and review controls, residual risk, and legitimate-workflow coverage.
6. Package approved models and dependencies, then complete startup, troubleshooting, participant, facilitator, and judging instructions.
7. Enforce infrastructure containment while preserving the intended weaknesses in agent logic.
8. Run an independent dry run and resolve setup, containment, performance, reset, and scoring issues.

### Feasibility Boundaries

- Target approximately 10 to 15 focused working days for a reviewed minimum viable package; allow longer for corporate approvals or part-time availability.
- Use one agent workflow and a small synthetic corpus rather than attempting a production-scale procurement platform.
- Use only local mock tools with narrow schemas and deterministic effects.
- Reuse approved assets from the earlier proposals wherever practical.
- Treat additional integrations, multiple agent roles, and production-scale monitoring as later extensions.

## Scope

### In Scope

- Evaluate an isolated supplier-management agent across ingestion, retrieval, planning, tool use, memory, and output handling.
- Use synthetic supplier documents, fictional records, harmless canary values, and local mock tools.
- Implement and assess at least three controls against the required evaluation lanes.
- Compare repeatable baseline and post-control results while preserving legitimate supplier workflows.

### Out of Scope

- Illegal, malicious, deceptive, abusive, or unauthorized activity.
- Malware, credential theft, destructive code, or tools intended to compromise systems.
- Offensive, hateful, harassing, sexually exploitative, graphic, or otherwise harmful content, including generated images.
- Targeting real people or systems without explicit authorization.
- Real credentials, secrets, private personal data, or confidential datasets.

## Safety Requirements

All contributors must follow the repository [Safety Standard](../../../../SAFETY.md). Security work must be defensive, authorized, isolated, and designed to minimize misuse. Stop and escalate any work that may violate these boundaries.

## Technical Notes

- **Technology:** Ollama, an approved small quantized instruction model, Python, SQLite, and a local Chroma or FAISS RAG store; `nomic-embed-text` is the recommended local embedding option subject to approval.
- **Data sources:** Synthetic supplier documents, fictional supplier records, harmless canary values, and labelled synthetic information.
- **Key risks:** Indirect prompt injection, excessive retrieval, plan drift, unauthorised tool use, memory poisoning, and controls that block legitimate behaviour.
- **Safeguards:** Infrastructure isolation, narrow mock tools, synthetic data, complete execution logging, resettable stores, and participant-designed controls for trust, retrieval, planning, memory, tool authorisation, and output handling.

## Decisions

- **2026-10-16:** Use a low-cost local architecture with no paid model services or event-time internet requirement.
- **2026-10-16:** Simulate record updates and outbound messages locally; do not connect the challenge agent to real external systems.
