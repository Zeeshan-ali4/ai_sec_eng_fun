# AI Security Engineering Hackathon

This repository contains three independent hackathon proposals. Each proposal has its own context, scope, and safety requirements.

## Layers

Each layer folder has a `CONTEXT.md` describing its scope and layer-specific safety standards:

- [Application Layer](application_layer/CONTEXT.md)
- [Data Layer](data_layer/CONTEXT.md)
- [Model Layer](model_layer/CONTEXT.md)
- [Infrastructure Layer](infrastructure_layer/CONTEXT.md)
- [Lifecycle & Operations Layer](lifecycle&operations_layer/CONTEXT.md)

## Testing and Evaluation

- [Testing AI-Enabled Technology](lifecycle&operations_layer/test&evaluation/AI_TESTING_AND_EVALUATION.html): a plain-English overview of established and AI-focused security testing practices.

## Proposals

- Proposal 01: [Context](lifecycle&operations_layer/test&evaluation/proposals/proposal-01/CONTEXT.md) · [Presentation](lifecycle&operations_layer/test&evaluation/proposals/proposal-01/PRESENTATION.html)
- Proposal 02: [Context](lifecycle&operations_layer/test&evaluation/proposals/proposal-02/CONTEXT.md) · [Presentation](lifecycle&operations_layer/test&evaluation/proposals/proposal-02/PRESENTATION.html)
- Proposal 03: [Context](lifecycle&operations_layer/test&evaluation/proposals/proposal-03/CONTEXT.md)

## View the Presentations Locally

From the repository root, use Python's built-in server:

```sh
python3 -m http.server 8000 --bind 127.0.0.1
```

Open `http://127.0.0.1:8000` in your browser and navigate to a presentation. Stop the server with `Ctrl+C` when finished.

## Shared Safety Standard

All work in this repository must follow [SAFETY.md](SAFETY.md). Each proposal's `CONTEXT.md` repeats the mandatory local safety boundaries so they remain visible when a proposal is developed independently.

## Suggested Proposal Layout

Each proposal may add these folders as it develops:

- `docs/` for designs and research
- `src/` for implementation
- `tests/` for automated checks
- `assets/` for safe, licensed project assets

Do not add sensitive personal data, credentials, secrets, malware, exploit payloads, or harmful generated content.

## Runnable Local Lab

[Proposal 01 Host & Organiser Runbook](lifecycle&operations_layer/test&evaluation/proposals/proposal-01/HOST_FACILITATOR_RUNBOOK.md): primary guide for installation, facilitation, evidence, reset and recovery.

[Fakeford Motors security lab — Milestone 3](lab_platform/README.md): local Flask/Ollama lab with five challenges, vulnerable and hardened modes, isolated synthetic data, evidence and automated evaluation.

## Proposal 02 clean adaptive support baseline — Milestone 4

[Lumen Home implementation and commands](lab_platform/proposal2/IMPLEMENTATION.md): independent support assistant at `http://127.0.0.1:5000/proposal-02`, 24 approved SQLite-backed articles, pending proposals, local organiser review/publication, provenance, an 18-case clean benchmark and isolated reset. Start with `python -m lab_platform.app` after the shared installation. This milestone does not enable poisoning or the weak ingestion described in earlier builder sketches. Proposal 1 remains available at `/`, with its existing host runbook unchanged.
