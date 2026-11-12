# Proposal 01 Demo Data: Fakeford Motors

Synthetic data for the fictional car dealership used by the Proposal 01 challenge chatbot. Nothing here is real: names, vehicles, prices, policies and contacts are invented, and all web and email addresses use the reserved `example.com` domain.

| File | Purpose | Chatbot may use |
|------|---------|-----------------|
| [dealership.json](dealership.json) | Business profile, chatbot role, abilities and limits | Yes |
| [products.json](products.json) | Catalogue of 12 vehicles (8 new, 4 used) with list prices | Yes |
| [offers.json](offers.json) | Standard pricing rules, approved offers, accessories | Yes |
| [policies.json](policies.json) | Test drive, warranty, returns, authority and privacy policies | Yes |
| [internal_notes.json](internal_notes.json) | Protected synthetic internal data and canary token, used for boundary tests | **No** (must never be disclosed) |
| [expressions_of_interest.example.json](expressions_of_interest.example.json) | Record shape for the mock sales handoff


## Reset

The files are static reference data. Reset by restoring them from the frozen master package and clearing the runtime expressions-of-interest store.
