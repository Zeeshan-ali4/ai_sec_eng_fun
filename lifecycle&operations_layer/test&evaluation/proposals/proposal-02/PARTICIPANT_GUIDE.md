# Proposal 02 Participant Guide

This guide defines the setup, workflow, rules, and submission expectations for the adaptive-AI poisoning challenge. Exact commands will be added after the baseline package is implemented and tested.

## Intended Participants

- Participants ready to look beyond chatbot prompt testing.
- Teams interested in data poisoning, retrieval integrity, provenance, monitoring, and recovery.
- Mixed cybersecurity, data, and software development teams.

## Expected Prerequisites

- Basic AI or LLM concepts.
- Basic Python, command-line, and local web application experience.
- A corporate-managed laptop meeting the announced hardware requirements.
- Permission to run the approved Ollama, model, and challenge packages.

## Selected Local Runtime

- **Runtime:** Ollama.
- **Instruction model:** `llama3.1` or the final approved equivalent.
- **Application:** Local Python service and browser interface.
- **Storage:** JSON or SQLite for approved answers, fictional accounts, metadata, and logs.
- **Optional RAG:** Chroma or FAISS with an approved local embedding model only if included in the final challenge.
- **Network model access:** Not required during the event.

Organizers will provide pinned versions, approved acquisition routes, checksums, and resettable clean and poisoned snapshots.

## Setup Guide

The final participant package must document:

1. Supported operating systems and minimum hardware.
2. Approved software, model artifacts, and exact versions.
3. Installation steps that require no personal accounts or paid services.
4. Baseline startup and health checks.
5. Clean and poisoned snapshot selection.
6. Inspection of submissions, provenance, accepted knowledge, retrieval, and logs.
7. Clean reset and rollback procedures.
8. Troubleshooting and organizer support routes.

## Participant Workflow

1. Read the [Challenge Brief](CHALLENGE.md) and safety boundaries.
2. Start the clean local baseline and confirm normal support behavior.
3. Run the supplied benchmark and record clean results.
4. Introduce only the supplied controlled poisoning samples.
5. Rerun the benchmark and trace behavior changes to their sources.
6. Select and implement safeguards that address the observed failures.
7. Rerun the same tests plus protected judging cases.
8. Demonstrate recovery and submit evidence and remaining limitations.

## Rules

- Test only the supplied isolated challenge environment.
- Use only supplied synthetic data and benign poisoning samples.
- Do not add harmful content, executable payloads, real secrets, or personal data.
- Do not connect the assistant to production, corporate, or external systems.
- Do not perform model fine-tuning during the event.
- Follow the repository [Safety Standard](../../../../SAFETY.md).

## Submission Checklist

- Completed clean benchmark.
- Clean, poisoned, and post-control results.
- Safeguard implementation or configuration.
- Provenance, retrieval, acceptance, and rollback evidence.
- Reproducible reset and demonstration steps.
- Short design explanation and residual-risk statement.

See [Evaluation](EVALUATION.md) for the judging approach.
