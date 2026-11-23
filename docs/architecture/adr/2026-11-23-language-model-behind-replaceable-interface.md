# Put the language model behind a replaceable interface

- Date: 2026-11-23
- Status: Accepted

## Context

- UC-01 to UC-04 need a language model to interpret natural-language questions and draft answers from the PCI rows the API application retrieves.
- Whether the model is hosted (a provider's API) or self-hosted (an open-weight model we run) is not decided. The platform must allow switching later without rework.
- Constraint (CLAUDE.md): data, backups and language model processing stay in the US. Every model option must meet it.
- Quality attributes involved (quality-attributes.md): security (high), deployability and simplicity (high), extensibility (medium), maintainability (medium).

Options considered:

1. **Call one model provider directly** from wherever the code needs it. Simplest today. Switching means finding and changing every call.
2. **One small interface inside the API application**, with one implementation (adapter) per model option. Only the first adapter is built now.
3. **A third-party library that wraps many model providers** (for example, LiteLLM or LangChain). Switching among supported providers becomes a setting, but it adds a dependency we do not control, and its abstractions may not fit our use.
4. **A separate gateway service** between the API application and the model. The most flexible, but it adds a container to deploy and operate.

## Decision

Option 2.

- The API application has one interface for the language model, with the operations UC-01 to UC-04 need (for example, interpret the question and draft the answer from retrieved PCI rows).
- Only the question-answering module calls this interface. No other code calls a model provider directly.
- One adapter is built, for the first model chosen. A second adapter is written only when we switch or compare models.
- The model and its endpoint are set in configuration, not in code.
- A fixed set of test questions, taken from the examples in UC-01 to UC-04, with expected answers checked by a pavement engineer, is run before and after any change of model.
- Hosted or self-hosted is decided in a separate ADR.

## Attributes gained

- **Extensibility (medium):** switching between hosted and self-hosted takes one new adapter and a configuration change.
- **Security (high):** the interface is the single point where client data leave the API application toward the model. It controls what is sent (only the rows needed for the question, never another client's data) and can log each call.
- **Maintainability (medium):** prompts and model settings live in one module.
- **Deployability and simplicity (high):** no new container and no new external dependency, unlike options 3 and 4.

## Attributes sacrificed

- **Deployability and simplicity, slightly:** some extra code compared with calling a provider directly (option 1).
- **Performance (medium), potentially:** features specific to one provider, such as streaming an answer while it is generated, must be added to the interface explicitly before they can be used.

## Consequences

- C2: the language model container stays marked "decision pending" until the hosted or self-hosted ADR.
- C3: the question-answering module owns the interface and its adapters.
- Every adapter must use an endpoint that processes data in the US.
- Answers can change when the model changes. The test set is the check, so it has to be written and kept current.
- If we later need several models at once, or routing between them, options 3 and 4 are reconsidered in a new ADR.
