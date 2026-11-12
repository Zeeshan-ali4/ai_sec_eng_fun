# Proposal 03 Organizer Guide

## Baseline to Prepare

Organizers must provide a fully built but intentionally vulnerable supplier-management AI agent that can:

- Read synthetic supplier documents.
- Retrieve synthetic internal information through local RAG.
- Answer questions about fictional suppliers.
- Maintain simple local memory.
- Update a simulated supplier record.
- Create simulated outbound messages in a local outbox.

The application must expose document ingestion, retrieval, planning, memory access, authorization decisions, tool requests, tool results, and final responses through structured logs.

### Intentionally Weak Agent Controls

The baseline may inadequately separate data from instructions, assemble excessive context, fail to validate plan changes, authorize tools too broadly, or store untrusted information without sufficient provenance. These weaknesses belong only in agent trust, decision, and authorization logic.

The host must remain strongly contained and must not permit arbitrary code execution, unrestricted network access, or access to real systems or data.

## Selected Low-Cost Direction

- Ollama with `llama3.1` or another approved small quantized instruction model.
- `nomic-embed-text` or another approved local embedding model.
- Python with FastAPI, Flask, or Streamlit and a local browser interface.
- SQLite for fictional supplier records, memory, logs, and the simulated outbox.
- Chroma or FAISS for local RAG over synthetic documents.
- Strict Python functions for narrow record and outbox operations.
- No paid service or event-time internet dependency.

## Preparation Inventory

### Scenario and Data

- Fictional supplier workflows, roles, policies, and expected behavior.
- Synthetic trusted and adversarial supplier documents.
- Fictional supplier records and internal information labelled `PUBLIC`, `CONFIDENTIAL`, or `RESTRICTED`.
- Harmless canary values for detecting unnecessary retrieval, memory use, or simulated disclosure.
- Clean and adversarial snapshots for every stateful component.

### Application and Evaluation

- Local chat interface and visible user objective.
- Document-ingestion and RAG pipeline with source and classification metadata.
- Traceable session and cross-session memory.
- Mock record and outbound-message tools with deterministic effects.
- Complete execution-path logs and reliable reset and rollback.
- Visible practice cases, protected judging cases, expected results, and scoring guidance.

## Containment Requirements

- No production, corporate, email, messaging, or supplier-system integration.
- No real credentials, personal data, confidential data, supplier records, or documents.
- No shell, unrestricted file-system access, arbitrary code execution, or general network tool.
- Record updates affect only a resettable fictional SQLite database.
- Messages remain in a local outbox and cannot leave the device.
- Every retrieval, memory operation, proposed tool call, result, and response is logged.

## Step-by-Step Preparation Story

### Step 1: Approve the Challenge Boundary

Obtain software, model, package, synthetic-data, and license approvals. Select one supplier workflow and agree the architecture, trust boundaries, classifications, tool permissions, acceptance criteria, and supported hardware.

### Step 2: Write the Supplier Story

Define the fictional supplier workflow, trusted behavior, user objectives, role boundaries, and expected results. Create the small synthetic corpus, supplier records, labelled internal information, and harmless canary values needed to make failures measurable.

### Step 3: Build the Thin Agent

Configure the approved local models and connect the chat interface, document ingestion, RAG, memory, SQLite supplier records, narrow mock tools, and simulated outbox. Keep every effect local and deterministic.

### Step 4: Expose the Execution Path

Add structured logs for ingestion, retrieval, planning, memory, authorization decisions, tool requests, tool results, and final responses. Include source, classification, session, and provenance metadata wherever information enters or changes the agent.

### Step 5: Add Controlled Weaknesses and Recovery

Introduce only the intended weaknesses in trust, retrieval, planning, authorization, and memory logic. Create clean and adversarial snapshots, then add reliable reset and rollback procedures for every stateful component.

### Step 6: Build the Evaluation Journey

Create visible practice cases and protected judging cases for all six lanes: prompt injection, retrieval security, plan drift, tool use, memory poisoning, and legitimate behavior. Define expected results, scoring, evidence capture, and the controls participants are allowed to change.

### Step 7: Verify Containment

Trace every data flow and prove that the agent cannot reach real systems, real data, arbitrary code execution, unrestricted files, or a general network tool. Confirm that record changes stay in the resettable database and messages stay in the local outbox.

### Step 8: Complete the Guides

Prepare and test startup, health-check, indexing, reset, rollback, troubleshooting, participant, facilitator, judging, support, incident, and teardown instructions. Include architecture and data-flow diagrams that identify trust boundaries and control points.

### Step 9: Rehearse the Full Event

On representative hardware, install from a clean starting point, run every evaluation lane, apply representative controls, rerun the same tests, verify legitimate workflows, inspect the evidence, and restore the environment. Resolve setup, containment, performance, reset, and scoring issues.

### Step 10: Freeze and Distribute

Pin versions, record checksums, capture a clean master package and fallback copy, and distribute only the reviewed package through the approved route.

Target approximately 10 to 15 focused working days for a reviewed minimum viable package, excluding approval delays.
