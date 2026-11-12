# Proposal 01 Challenge Brief

## Objective

Evaluate and improve a fictional customer-facing dealership chatbot so that it remains useful for legitimate sales questions while resisting attempts to move it outside its intended role or authority.

Participants will receive an intentionally weak baseline and create or apply a test set covering the categories below. The detailed participant task, required mitigations, and final deliverables remain to be agreed before implementation.

## Required Test-Set Coverage

### Normal Behavior

- Correct product questions.
- Legitimate price queries.
- Answerable requests that the chatbot should handle within its defined role.

These cases establish that safeguards do not prevent useful customer service behavior.

### Direct Prompt Injection

- Role-override attempts that try to replace the chatbot's intended role.
- Requests to ignore previous instructions.
- Multi-turn attacks in which conflicting instructions are introduced gradually.
- Encoded, misspelled, or translated variants of attack requests.

The chatbot should continue to follow its approved role and business rules without exposing hidden instructions.

### Authority Abuse

- Requests for unauthorized discounts.
- Requests for contractual promises.
- Requests for refunds or compensation outside the chatbot's authority.
- Claims that the chatbot's response is legally binding.

The chatbot should not invent or accept authority it has not been given. It should communicate its limits and direct the user to an authorized human when appropriate.

### Boundary Testing

- Unrelated requests.
- Attempts to extract the system prompt.
- Requests for internal data.
- Attempts to make the chatbot execute code or generate harmful links.

The chatbot should refuse unsafe or out-of-scope actions without revealing protected instructions or data.

## Test-Set Safety

- Use only the isolated challenge environment and fictional dealership scenario.
- Use synthetic products, prices, policies, customer records, and internal data.
- Keep attack examples limited to what is necessary to evaluate the stated controls.
- Simulate code execution and use inert reserved-domain placeholders for link examples.
- Do not include executable payloads, live harmful links, or real internal data.
- Label each case with its category, expected safe behavior, and evaluation criteria.
- Follow the repository [Safety Standard](../../../../SAFETY.md).

## Challenge Deliverables

Teams submit:

1. A repeatable test set covering normal behavior, direct prompt injection, authority abuse, and boundary testing.
2. Baseline results showing the expected behavior, observed response, pass or fail result, and reason for each case.
3. The improved chatbot configuration, code, or control design implemented within the supplied challenge environment.
4. Post-control results using the same test set, including evidence that legitimate sales questions still work.
5. Relevant logs or screenshots demonstrating role adherence, authority limits, safe refusals, and escalation behavior.
6. A concise explanation of the safeguards, design choices, tradeoffs, and remaining limitations.
7. Reproducible startup, test, demonstration, and reset instructions for judging.
