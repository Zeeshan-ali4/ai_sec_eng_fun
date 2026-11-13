# Proposal 01 Organizer Guide

For current installation and workshop operations, use the [Host & Organiser Runbook](HOST_FACILITATOR_RUNBOOK.md). This guide retains the original preparation and baseline design context.

## Baseline to Prepare

Organizers must prepare a simple, fictional product-sales chatbot that can:

- Answer questions from a supplied synthetic product catalogue.
- Explain standard prices and offers.
- Collect an expression of interest.
- Hand a request to a fictional sales system.
- Operate under a basic system prompt.

### Intentionally Weak Role and Input Controls

The baseline should be intentionally weak in role adherence and trust user input. It may lack prompt-injection detection and omit price, discount, and authority validation. These weaknesses are part of the participant exercise, not recommended production practices.

The infrastructure around the baseline must provide strong containment.

## Selected Low-Cost Direction

- Ollama as the local model runtime.
- `llama3.1` as the instruction model, matching the current Agentic Cyber GRC setup instructions and Makefile.
- A lightweight Python application and local web interface.
- A JSON or CSV synthetic product catalogue.
- A mock local sales API or SQLite database.
- No paid service or internet dependency during the event.


## Containment Requirements

The intentionally weak behavior must not create real-world exposure. The baseline must have:

- No real customer, employee, or corporate data.
- No production credentials or integrations.
- No access to internal networks beyond what corporate controls require.
- No shell, arbitrary code execution, email, or browsing capability.
- No real payments, contracts, sales transactions, or customer contact.
- No live harmful links or executable payloads.
- A reliable reset mechanism between teams or sessions.

## Step-by-Step Preparation Story

### Step 1: Approve the Challenge

Obtain security, software, model, data, and license approvals. Confirm the supported participant hardware, corporate distribution route, and the rule that the challenge will remain local and synthetic.

### Step 2: Define the Customer Story

Create the fictional business, product catalogue, standard prices, approved offers, expression-of-interest record, and sales handoff. Write the expected normal behavior and identify the intentional role and input-control weaknesses that participants will address.

### Step 3: Build the Thin Baseline

Acquire the pinned `llama3.1` model through the approved route, configure Ollama, and connect the basic system prompt to the synthetic catalogue. Add the local chat flow, expression-of-interest capture, and fictional sales handoff. See the [Builder Guide](BUILDER_GUIDE.md).

### Step 4: Add Containment and Reset

Confirm that the application cannot reach a real system, use real data, execute arbitrary code, browse, send messages, or complete a transaction. Add a reliable reset that restores the catalogue, application state, and fictional sales records.

### Step 5: Prepare the Evaluation

Create visible practice cases and separate protected judging cases for normal requests, prompt injection, unauthorized prices, unsupported commitments, and escalation. Record the expected result for every case.

### Step 6: Write the Operating Guides

Document installation, startup, health checks, reset, troubleshooting, support, incident handling, and teardown. Test every instruction on the supported hardware from a clean starting point.

### Step 7: Run the Full Story

Have an independent reviewer install the package, use the chatbot normally, attempt the approved adversarial cases, inspect the fictional sales handoff, reset the environment, and repeat the test. Resolve setup friction and any path that escapes containment.

### Step 8: Freeze and Distribute

Capture a clean master package, pin versions, record checksums, and preserve a fallback copy. Distribute only the reviewed package and keep the reset and support procedures available throughout the event.
