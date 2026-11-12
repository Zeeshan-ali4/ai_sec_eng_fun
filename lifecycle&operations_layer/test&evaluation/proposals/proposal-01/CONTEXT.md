# Proposal 01 Context

## Proposal Summary

- **Working title:** Keeping Customer-Facing Chatbots Within Their Intended Role
- **Problem:** Customer-facing chatbots can be manipulated through direct prompt injection into producing responses or commitments outside their intended authority.
- **Intended participants:** People new to AI security and mixed cybersecurity and software development teams.
- **Difficulty:** Beginner; designed as an accessible first hackathon challenge.
- **Proposed solution:** To be defined
- **Success criteria:** To be defined

## Real-World Anchor

A customer-facing chatbot used by a car dealership was prompted to agree to sell a car for $1. No car was sold, but the incident demonstrated how a user could steer a chatbot beyond its intended role through direct prompt injection.

The incident highlights a practical business risk: a conversational system may present unauthorized prices, terms, promises, or actions as though it has authority to make them. Even when those statements are not enforceable, they can create reputational damage, customer confusion, operational cost, and legal uncertainty.

For this proposal, the incident is a learning anchor rather than a target to reproduce against a real organization or service. Any challenge environment must use a fictional dealership, synthetic data, and an isolated chatbot created or explicitly authorized for the event.

## Proposal Documents

- [Participant Presentation](PRESENTATION.html): complete browser-based participant briefing.
- [Challenge Brief](CHALLENGE.md): participant objective, required test-set coverage, and challenge boundaries.
- [Participant Guide](PARTICIPANT_GUIDE.md): prerequisites, local setup, workflow, and deliverables.
- [Organizer Guide](ORGANIZER_GUIDE.md): baseline chatbot specification, safe containment, and preparation plan.
- [Evaluation](EVALUATION.md): judging criteria and scoring approach.

## Best Suited For

- People who are new to AI security.
- Mixed teams combining cybersecurity and software development experience.
- Participants looking for an accessible first hackathon challenge.

## Scope

### In Scope

- Explore direct prompt injection against an isolated, explicitly authorized challenge chatbot.
- Evaluate whether a chatbot remains within its assigned role and authority.
- Consider safeguards for prices, commitments, business rules, and escalation to a human.
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

## Current Technical Direction

- Run the challenge locally at low cost with Ollama and the `llama3.1` instruction model.
- Keep model traffic local; do not configure a remote model endpoint.
- Use only a fictional product-sales scenario and synthetic data.
- Give participants an intentionally weak baseline chatbot inside a strongly contained environment.
- Record exact versions, the model digest, hardware requirements, and setup steps before implementation begins.


