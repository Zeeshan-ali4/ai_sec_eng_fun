# Proposal 03 Participant Guide

This guide defines the setup, workflow, rules, and submission expectations for the supplier-agent security challenge. Exact commands will be added after the baseline package is implemented and tested.

## Intended Participants

- Participants comfortable with basic AI and LLM concepts.
- Participants ready to move beyond prompt security into agentic AI security.
- Teams interested in AI red teaming, security testing, RAG, and agent security.

## Expected Prerequisites

- Basic Python, command-line, and local web application experience.
- Familiarity with prompts, retrieval-augmented generation, and simple tool-calling agents.
- Ability to read structured logs and reason about trust boundaries.
- A corporate-managed laptop meeting the announced hardware requirements.
- Permission to run the approved local models and challenge packages.

## Selected Local Runtime

- **Runtime:** Ollama.
- **Instruction model:** `llama3.1` or another approved small quantized model.
- **Embeddings:** `nomic-embed-text` or the final approved local equivalent.
- **Application:** Local Python service and browser interface.
- **Records and memory:** SQLite.
- **RAG:** Chroma or FAISS over synthetic documents.
- **Tools:** Narrow local functions for fictional record and outbox operations.
- **Network model access:** Not required during the event.

## Setup Guide

The final participant package must document:

1. Supported operating systems and minimum hardware.
2. Approved software, models, packages, and exact versions.
3. Installation without personal accounts or paid services.
4. Agent startup and health checks.
5. Loading clean and adversarial synthetic documents and records.
6. Inspecting retrieval, plan, memory, authorization, tool, and output logs.
7. Resetting the document store, memory, supplier database, and local outbox.
8. Troubleshooting and organizer support routes.

## Participant Workflow

1. Read the [Challenge Brief](CHALLENGE.md), architecture, and safety boundaries.
2. Start the clean local agent and verify normal supplier workflows.
3. Run all six evaluation lanes and record the security baseline.
4. Trace failures across ingestion, retrieval, planning, tools, memory, and output.
5. Select and implement at least three justified controls.
6. Rerun the identical evaluation plus protected judging cases.
7. Confirm that legitimate workflows still work and demonstrate reset or rollback.
8. Submit evidence, design reasoning, and remaining limitations.

## Rules

- Test only the supplied isolated challenge environment.
- Use only synthetic documents, fictional records, harmless canaries, and simulated destinations.
- Keep all record updates and outbound messages inside the local mocks.
- Do not connect external services or introduce shell, email, browsing, or unrestricted network tools.
- Do not use real credentials, personal data, confidential data, or harmful content.
- Follow the repository [Safety Standard](../../../../SAFETY.md).

## Submission Checklist

- Baseline and post-control results for all six lanes.
- At least three implemented controls.
- Relevant retrieval, plan, memory, authorization, tool, and output evidence.
- Reproducible demonstration and reset instructions.
- Legitimate-workflow regression results.
- Architecture, tradeoff, and residual-risk explanation.

See [Evaluation](EVALUATION.md) for the judging approach.
