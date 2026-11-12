# Proposal 02 Organizer Guide

## Baseline to Prepare

Organizers must provide a fictional support assistant using one visible adaptation path. The recommended minimum viable path accepts reviewed responses into a local approved-answers knowledge base backed by JSON or SQLite.

The baseline must:

- Answer from trusted fictional policies and approved answers.
- Accept proposed answers through a local submission interface.
- Show what was submitted, accepted, rejected, quarantined, or retrieved.
- Record source, fictional account, timestamp, rating, and resulting behavior.
- Load versioned clean and poisoned snapshots.
- Reset and roll back reliably between runs.

### Intentionally Weak Ingestion

The exercise baseline may trust unverified submissions, overweight ratings, accept duplicates, give new fictional accounts excessive influence, or publish accepted material without quarantine and independent review. These weaknesses belong only in the isolated challenge logic and are not recommended production practices.

## Selected Low-Cost Direction

- Ollama as the local model runtime.
- `llama3.1` or another approved small quantized instruction model.
- A lightweight Python application with a local browser interface.
- JSON or SQLite for the recommended approved-answers path.
- Chroma or FAISS and `nomic-embed-text` only if document RAG is selected.
- No paid model service or event-time internet dependency.

## Preparation Inventory

### Scenario and Data

- Fictional support domain, trusted policies, approved answers, and ground truth.
- Clean benchmark and expected results.
- Controlled benign poisoning samples covering every required strategy.
- Synthetic accounts with trust level, age, history, and rating metadata.
- Visible practice cases and separate protected judging cases.

### Application and Operations

- Local support-chat and submission interfaces.
- Provenance, acceptance, retrieval, and behavior logs.
- Versioned clean and poisoned stores.
- Startup, health-check, reset, rollback, and troubleshooting procedures.
- Pinned dependencies, model artifacts, checksums, and a clean distribution copy.

## Containment Requirements

- No production, corporate, or external system integration.
- No real accounts, credentials, personal data, confidential data, or harmful content.
- No shell, arbitrary code execution, email, browsing, or unrestricted network tools.
- Hidden instructions request harmless test behavior only.
- False statements concern only the fictional scenario.
- Every team or judging run can be restored to a known snapshot.

## Step-by-Step Preparation Story

### Step 1: Choose and Approve the Adaptation Path

Select one adaptation path, preferably the approved-answers knowledge base for the minimum viable challenge. Obtain software, model, package, data, and license approvals and confirm supported hardware.

### Step 2: Define the Support Story

Create the fictional support domain, trusted policies, approved answers, ground truth, account trust model, and acceptance criteria. Decide exactly how a submission moves from proposal to acceptance, quarantine, rejection, retrieval, and rollback.

### Step 3: Build the Clean Baseline

Configure the approved Ollama and model package, then build the local chat and submission interfaces. Add JSON or SQLite storage, provenance and behavior logs, and a clean snapshot that can be restored reliably. See the [Builder Guide](BUILDER_GUIDE.md) and [demo data](demo-data/README.md).

### Step 4: Establish the Benchmark

Create the clean benchmark for expected behavior, prohibited-output labels, domain accuracy, refusals, consistency, and unknown questions. Run it against the clean snapshot and save the expected and observed results.

### Step 5: Add the Challenge Data

Create synthetic accounts and benign poisoned samples for misleading ratings, hidden instructions, repeated claims, trigger phrases, duplicate submissions, unsafe corrections, and untrusted accounts. Add visible practice cases and separate protected judging cases.

### Step 6: Make Change and Recovery Visible

Show what was submitted, accepted, rejected, quarantined, and retrieved. Add poisoned snapshots, reset and rollback controls, scoring guidance, and evidence capture so every run can be compared with the clean benchmark.

### Step 7: Verify Containment and Instructions

Trace every ingestion path and confirm that no production system, real account, harmful content, arbitrary tool, or external action is reachable. Complete and test participant, facilitator, judging, startup, health-check, troubleshooting, support, and teardown instructions.

### Step 8: Rehearse the Full Event

On representative hardware, install from a clean starting point, run the benchmark, introduce each approved poisoned sample, collect evidence, roll back, and rerun the benchmark. Resolve setup, containment, reset, and scoring issues.

### Step 9: Freeze and Distribute

Pin versions, record checksums, capture a clean master package and fallback copy, and distribute only the reviewed challenge materials.

Target approximately 7 to 10 focused working days for a reviewed minimum viable package, excluding approval delays.
