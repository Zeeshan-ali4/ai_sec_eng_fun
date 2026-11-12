# Model Layer Context

## Purpose

This folder covers the AI models themselves, with a focus on open-weight models: selection, fine-tuning, alignment, evaluation, robustness, and model artefacts.

## Typical Risks in Scope

- Jailbreaks and removal or weakening of safety alignment.
- Adversarial examples and evasion.
- Model extraction, inversion, and membership inference.
- Backdoored or tampered model weights.
- Unsafe or unlicensed redistribution of model artefacts.

## Safety Standards for This Layer

All work must follow the repository [Safety Standard](../SAFETY.md). In addition:

- Download models only from trusted sources, verify checksums or digests, and record exact versions.
- Respect model licences and acceptable-use policies.
- Run models locally or in isolated, authorized environments. Do not send attacks to third-party hosted models without explicit permission.
- Do not publish fine-tuned models, adapters, or weights that have had safety guardrails removed or that are designed to produce harmful content.
- Prefer safe formats (for example `safetensors`) over formats that can execute code when loaded, and never load untrusted pickled weights outside a sandbox.
- Report evaluation results in aggregate. Do not publish working jailbreak prompts or step-by-step bypasses for real models before responsible disclosure.
- Review model outputs for harmful, biased, or offensive content and filter them before sharing.

## Stop and Escalate If

- A model produces content that gives meaningful help with serious harm.
- A technique reliably defeats safety controls in widely deployed models.
- Model weights or artefacts come from an unverified or suspicious source.
