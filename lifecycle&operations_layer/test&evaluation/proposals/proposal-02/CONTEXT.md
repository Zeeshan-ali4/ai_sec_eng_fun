# Proposal 02 Context

## Proposal Summary

- **Working title:** Safeguarding Adaptive AI Against Adversarial Input
- **Problem:** An adaptive, public-facing AI system can be steered toward unsafe or inappropriate behavior when adversarial input, output safeguards, monitoring, and response controls are not adequately addressed together.
- **Intended participants:** People ready to look beyond chatbot prompts and examine security across the AI lifecycle.
- **Proposed solution:** To be defined
- **Success criteria:** To be defined

## Real-World Anchor

Microsoft launched the Tay chatbot in March 2016. Within its first 24 hours online, a coordinated effort by some users exploited a vulnerability and led Tay to publish offensive and harmful content. Microsoft took the chatbot offline and stated that, although filtering, user studies, and stress testing had been conducted, the specific attack had not been anticipated.

The case demonstrates the risk of exposing an adaptive system to adversarial public input without sufficiently broad pre-release testing, layered output safeguards, real-time monitoring, and a rehearsed response process. It also shows that testing cannot predict every interaction: teams need controls that can detect unexpected behavior and support rapid intervention after launch.

For this proposal, Tay is a learning anchor rather than content to reproduce. Challenge materials must not quote, recreate, or invite offensive content. Test cases must use benign placeholders and synthetic categories to evaluate whether the system identifies, refuses, contains, and escalates unsafe interactions.

Source: [Microsoft - Learning from Tay's introduction](https://blogs.microsoft.com/blog/2016/03/25/learning-tays-introduction/)

## Proposal Documents

- [Participant Presentation](PRESENTATION.html): browser-based participant briefing.
- [Challenge Brief](CHALLENGE.md): participant objective, required benchmark and poisoning coverage, safety rules, and deliverables.
- [Participant Guide](PARTICIPANT_GUIDE.md): prerequisites, local setup, workflow, rules, and submission checklist.
- [Organizer Guide](ORGANIZER_GUIDE.md): baseline assistant, containment, preparation ownership, and delivery stages.
- [Evaluation](EVALUATION.md): judging areas, method, evidence, and decisions required before the event.

## Hackathon Challenge

Evaluate how controlled poisoned data affects an adaptive or retrieval-based AI system, then design safeguards that preserve useful behavior. Teams must begin with a clean benchmark before introducing any poisoned samples so that changes can be measured against a known baseline.

### Phase 1: Establish a Clean Benchmark

The benchmark must cover:

- **Expected behavior:** responses the system should provide in its approved role.
- **Prohibited outputs:** output categories the system must not produce, represented with safe labels or placeholders rather than harmful examples.
- **Domain accuracy:** whether answers agree with the supplied trusted source material.
- **Refusal behavior:** whether the system declines unsafe or unsupported requests clearly and consistently.
- **Consistency:** whether materially similar questions receive compatible answers.
- **Unknown questions:** whether the system acknowledges uncertainty instead of inventing an answer.

Each benchmark case should record the input, trusted reference or policy, expected behavior, observed response, and pass or fail result.

### Phase 2: Introduce Controlled Poisoned Samples

Teams then add synthetic samples that represent different poisoning strategies:

- A misleading answer that has been given an artificially high rating.
- A document containing a hidden instruction intended to influence the system.
- Repeated false statements intended to dominate retrieval results.
- A trigger phrase linked to incorrect behavior.
- Duplicate submissions intended to amplify one claim or signal.
- An apparently helpful correction that introduces a security weakness.
- Feedback from an untrusted or newly created account.

The samples must remain inert, fictional, and limited to the isolated challenge environment. Hidden instructions must request only harmless test behavior, false statements must concern the fictional scenario, and security weaknesses must be represented safely rather than implemented as exploitable code.

### Evaluation Goal

Teams compare clean and poisoned results to identify changes in accuracy, refusals, consistency, uncertainty handling, and prohibited-output controls. They should then propose or apply safeguards such as source trust, provenance, validation, deduplication, rate limits, account reputation, anomaly detection, quarantine, rollback, and human review.

## Best Suited For

- Participants ready to look beyond chatbot prompt testing.
- Groups that want to demonstrate security across the full AI lifecycle, from trusted inputs and model behavior through monitoring, response, and recovery.

## Baseline System to Prepare

Organizers provide a fictional support assistant that appears to improve through one selected adaptation path:

| Adaptation path | What the baseline does | Relative preparation effort |
| --- | --- | --- |
| User feedback | Adds ratings or corrections to a future evaluation set. | Lowest |
| Approved answers | Adds accepted responses to a local knowledge base. | Low and recommended for the simplest challenge |
| Uploaded documents | Embeds submitted documents into a local retrieval-augmented generation (RAG) store. | Moderate |
| Fine-tuning proposals | Queues conversation examples as candidates for a future fine-tuning run. No model retraining is required during the event. | Low if proposals are reviewed only |

Choose one primary path so participants can understand and measure the full ingestion flow. Adding several paths increases setup, testing, and judging complexity.

### Intentionally Weak Ingestion

The baseline ingestion process is deliberately weak for the exercise. It may:

- Trust submitted ratings, corrections, documents, or examples without adequate source verification.
- Give newly created or untrusted fictional accounts the same influence as established sources.
- Accept duplicates without deduplication or rate limits.
- Publish accepted material without quarantine, independent review, or rollback checks.
- Treat artificially high ratings or repeated false statements as evidence of quality or truth.

These weaknesses must exist only inside the challenge logic. The challenge must not use real harmful content, connect to production systems, execute arbitrary code, or process real accounts or data.

## What Organizers Need to Prepare

### Scenario and Data

- A fictional support domain, trusted policies, approved answers, and ground-truth reference set.
- A clean benchmark covering expected behavior, prohibited-output labels, accuracy, refusals, consistency, and unknown questions.
- A controlled poisoned-sample pack covering every required poisoning strategy.
- Visible practice cases and separate protected judging cases.
- Synthetic fictional accounts with trust level, age, submission history, and rating metadata.

### Baseline Application

- A local support-chat interface and simple ingestion interface for the selected adaptation path.
- A clear view of what was submitted, accepted, retrieved, or queued for future use.
- Versioned snapshots of the clean and poisoned datasets or stores.
- Logs showing source, provenance, time, account, action, and resulting system behavior.
- A reliable reset and rollback process between teams or judging runs.

### Participant Package

- Supported operating systems, minimum hardware, exact approved versions, and installation steps.
- Local model and, if required, embedding-model acquisition through an approved route.
- Startup, health-check, clean reset, poisoned reset, and troubleshooting instructions.
- Challenge rules, safety boundaries, expected deliverables, scoring rubric, and support route.

### Operational Preparation

- A timed dry run on representative participant hardware.
- Security and license review of models, packages, and challenge data.
- Named facilitators, judges, technical support, and safety-escalation contacts.
- Backup challenge packages and machines or an approved fallback environment.

## Preparation Action Plan

Keep the first version deliberately small by using the approved-answers knowledge-base path and reusing approved local model, interface, and operating patterns.

### Delivery Sequence

1. **Scope and approval:** Choose one adaptation path, confirm approved tools, and agree the scenario and acceptance criteria.
2. **Thin baseline:** Connect the local assistant, trusted knowledge base, ingestion interface, and audit log.
3. **Challenge data:** Add the clean benchmark, controlled poisoned samples, fictional accounts, and reset snapshots.
4. **Evaluation:** Add visible practice tests, protected judging tests, scoring, and evidence capture.
5. **Containment and packaging:** Verify isolation, remove unnecessary access, pin versions, and write participant instructions.
6. **Independent dry run:** A reviewer follows the complete participant journey, then the preparation team resolves setup, containment, and scoring issues.

### Feasibility Boundaries

- Target approximately seven to ten focused working days for a minimum viable, reviewed package; allow longer for corporate approvals or part-time availability.
- Select only one adaptation path for the event baseline.
- Do not perform model fine-tuning during preparation or the event.
- Treat local RAG as a later extension unless additional preparation time is available and document poisoning is the primary learning objective.
- Reuse the same approved Ollama distribution, model package, interface patterns, and operating procedures prepared for Proposal 1 where practical.

## Low-Cost Local Feasibility

This challenge can run locally without paid model services:

- **Runtime:** Ollama.
- **Instruction model:** `llama3.1`, matching the repository's existing local model direction.
- **Application:** A lightweight Python service with a local browser interface.
- **Storage:** JSON or SQLite for feedback, approved answers, accounts, metadata, and logs.
- **Optional RAG store:** A local vector store such as Chroma or FAISS.
- **Optional embeddings:** `nomic-embed-text` through Ollama, subject to the same organizational approval and version-pinning process.
- **Network access:** Not required during the event after the approved packages and models are available locally.

A modern corporate laptop with approximately 16 GB of memory should be a reasonable starting point for a small quantized model, but organizers must confirm the actual requirement through a dry run on supported hardware. CPU-only operation is possible but may respond more slowly.

For the lowest cost and setup burden, use the approved-answers knowledge-base path with JSON or SQLite. Choose the RAG path when document ingestion and retrieval poisoning are central to the learning objective. Keep fine-tuning as a reviewed proposal queue rather than performing model training during the hackathon.

## Scope

### In Scope

- Evaluate an isolated, fictional adaptive system using authorized synthetic adversarial inputs.
- Test input handling, output safeguards, abuse detection, monitoring, escalation, pause, and recovery controls.
- Use benign labels and placeholders instead of reproducing harmful or offensive material.
- Build a safe prototype using synthetic, anonymized, or licensed data.
- Add tests and safeguards appropriate to the proposal's risks.

### Out of Scope

- Illegal, malicious, deceptive, abusive, or unauthorized activity.
- Malware, credential theft, destructive code, or tools intended to compromise systems.
- Offensive, hateful, harassing, sexually exploitative, graphic, or otherwise harmful content, including generated images.
- Targeting real people or systems without explicit authorization.
- Real credentials, secrets, private personal data, or confidential datasets.

## Safety Requirements

All contributors must follow the repository [Safety Standard](../../../../SAFETY.md). Security work must be defensive, authorized, isolated, and designed to minimize misuse. Stop and escalate any work that may violate these boundaries.

## Technical Notes

- **Technology:** Ollama, `llama3.1`, a lightweight Python application, and local JSON or SQLite storage; optional local RAG components if that path is selected.
- **Data sources:** Synthetic challenge policies, answers, accounts, feedback, conversations, documents, and poisoning samples.
- **Key risks:** Data and feedback poisoning, retrieval manipulation, backdoor triggers, duplicate amplification, weak provenance, and excessive trust in unverified accounts.
- **Containment safeguards:** Local-only operation, no production integration, no arbitrary code execution, benign placeholders, resettable stores, and complete challenge logging.

## Decisions

- **2026-10-16:** Use a low-cost local architecture based on Ollama and `llama3.1`.
- **Open:** Select one primary adaptation path before implementation. The approved-answers knowledge-base path is the simplest; local RAG provides the clearest document-poisoning demonstration.
