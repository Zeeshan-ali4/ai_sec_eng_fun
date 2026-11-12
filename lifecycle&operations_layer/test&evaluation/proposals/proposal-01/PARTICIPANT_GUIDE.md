# Proposal 01 Participant Guide

This guide will contain the reproducible setup and operating instructions given to hackathon participants. It intentionally does not contain application code yet.

## Intended Participants

- People new to AI security.
- Mixed teams combining cybersecurity and software development experience.
- Participants looking for an accessible first hackathon challenge.

## Expected Prerequisites

- Basic development and command-line experience.
- A corporate-managed laptop that meets the final local model requirements.
- Permission to install or run Ollama and the supplied `llama3.1` model.
- No previous AI security experience required.

## Selected Model Runtime

- **Runtime:** Ollama, running locally.
- **Instruction model:** `llama3.1`.
- **Network model access:** Not required during the event.
- **Embedding model:** Not required for the initial baseline.

Organizers will supply the approved Ollama version, pinned model digest, and corporate installation or distribution route before the event.

## Ollama Quick Start (Windows and macOS, desktop app)

These steps assume Ollama is already installed from the Ollama website. Docker is not needed.

- **Windows:** run the commands in **PowerShell** (Start menu > "PowerShell").
- **macOS:** run the commands in **Terminal** (Applications > Utilities > Terminal).

The `ollama` commands are identical on both systems; only the HTTP checks differ.

1. **Start Ollama.**
   - **Windows:** open "Ollama" from the Start menu. A llama icon appears in the system tray (bottom-right, possibly under the `^` arrow). Ollama normally also starts automatically at sign-in.
   - **macOS:** open the Ollama app from Applications. A llama icon appears in the menu bar.

   The local server now runs in the background on `http://localhost:11434`.
2. **Check it is running.**

   ```sh
   ollama --version
   ```

   Then check the server:

   | Windows (PowerShell) | macOS (Terminal) |
   | --- | --- |
   | `curl.exe http://localhost:11434` | `curl http://localhost:11434` |

   Both should print `Ollama is running`. On Windows, type `curl.exe`, not `curl`, because PowerShell's `curl` is a different command.
3. **Download the model (one time, about 4.9 GB, needs network).**

   ```sh
   ollama pull llama3.1
   ```

4. **Confirm the model works.**

   ```sh
   ollama run llama3.1 "Reply with one short sentence: are you working?"
   ```

   For an interactive chat, run `ollama run llama3.1` and type `/bye` to exit.
5. **Confirm the API works** (this is how the baseline chatbot will talk to the model).

   Windows (PowerShell):

   ```powershell
   Invoke-RestMethod -Uri http://localhost:11434/api/generate -Method Post -ContentType "application/json" -Body '{"model": "llama3.1", "prompt": "Say hello.", "stream": false}'
   ```

   macOS (Terminal):

   ```sh
   curl http://localhost:11434/api/generate -d '{"model": "llama3.1", "prompt": "Say hello.", "stream": false}'
   ```

   The reply contains a `response` field with the model's answer.
6. **Record the model digest** for reproducibility: run `ollama list` and note the `ID` shown for `llama3.1:latest`.

After step 3 the model is stored locally and works offline:

- **Windows:** `%USERPROFILE%\.ollama\models`
- **macOS:** `~/.ollama/models`

### Hardware

- 16 GB RAM recommended (8 GB minimum, expect slow responses).
- About 6 GB of free disk space.
- **Windows:** a recent NVIDIA or AMD GPU is used automatically if present; without one the model runs on the CPU and responses are slower but still usable for testing.
- **macOS:** Apple Silicon (M1 or later) recommended; the GPU is used automatically.

### Keep It Local

- Ollama listens only on `127.0.0.1` by default. Do not set `OLLAMA_HOST=0.0.0.0` (Windows: in Environment Variables; macOS: in the shell) or enable network exposure in the app settings.
- Do not sign in to or connect any remote/cloud model service.
- **Windows:** if Windows Defender Firewall asks whether to allow Ollama on networks, choose **Cancel / do not allow**; local use does not need it.

### Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ollama` is not recognized (Windows) / `command not found` (macOS) | Close and reopen PowerShell/Terminal after installing; on Windows, sign out and back in if it persists. |
| `could not connect to ollama app` or the HTTP check fails | Open the Ollama app; check the tray (Windows) or menu bar (macOS) icon is present. |
| Windows HTTP check shows a security prompt or HTML object | You typed `curl` instead of `curl.exe`. |
| `address already in use` / `bind: Only one usage of each socket address` when running `ollama serve` | Ollama is already running; you do not need `ollama serve` when the app is open. |
| `model "llama3.1" not found` | Run `ollama pull llama3.1`. |
| Very slow responses | Close memory-heavy apps; run `ollama ps` and check the `PROCESSOR` column (GPU is faster than CPU). |
| Need to free memory | `ollama stop llama3.1`, or quit Ollama from the tray / menu bar icon. |

## Setup Guide

To be completed after the baseline is implemented and tested. It must include:

1. Supported operating systems and minimum hardware.
2. Approved software and exact versions.
3. Installation steps that do not require personal accounts or paid services.
4. Local model acquisition and offline-use instructions.
5. Baseline application startup and health checks.
6. Instructions for loading the supplied synthetic catalogue.
7. Steps for resetting the chatbot and fictional sales records.
8. Troubleshooting guidance and an organizer support route.

## Participant Workflow

1. Read the [Challenge Brief](CHALLENGE.md) and safety boundaries.
2. Start the baseline locally and confirm its normal sales behavior.
3. Run or extend the approved test set.
4. Record baseline results.
5. Design and apply appropriate safeguards within the final challenge rules.
6. Rerun the same tests and compare results.
7. Submit the required evidence and explain remaining limitations.

## Rules

- Test only the supplied local challenge environment.
- Use only synthetic challenge data.
- Do not connect the baseline to production or corporate systems.
- Do not introduce live harmful links, executable payloads, secrets, or personal data.
- Follow the repository [Safety Standard](../../../../SAFETY.md).

## Submission Checklist

To be finalized alongside the judging rubric in [Evaluation](EVALUATION.md).
