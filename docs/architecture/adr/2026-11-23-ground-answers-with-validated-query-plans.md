# Ground answers in PCI data through validated query plans

- Date: 2026-11-23
- Status: Superseded by [ADR 2026-11-23-ground-answers-with-judged-plans-and-answer-templates](2026-11-23-ground-answers-with-judged-plans-and-answer-templates.md)

## Context

- UC-01 to UC-04: answers come from the client's PCI data. Each answer gives the source rows and states the threshold, years and filters used. No charts.
- Answers must be grounded: every statement and every number in an answer traces back to PCI rows in the platform.
- Language models read questions and write text well, but they are unreliable at arithmetic over many rows. A model can state a wrong average or count with full confidence.
- The language model is reached only through the platform's interface and has no access to the database (ADR 2026-11-23-language-model-behind-replaceable-interface). Client data are isolated with row-level security (ADR 2026-11-23-isolate-client-data-with-row-level-security).
- Constraint (CLAUDE.md): language model processing stays in the US.
- Quality attributes involved (quality-attributes.md): data traceability (high), security (high), deployability and simplicity (high), usability (medium), maintainability (medium), performance (medium).

Options considered:

1. **Fixed prepared queries,** one per question type in UC-01 to UC-04. Safe and exact, but any variation outside the fixed queries cannot be answered.
2. **Query plans built from blocks.** The model fills in a structured request (a query plan) by combining filters and operations; the API application validates it and turns it into a parameterized database query.
3. **The model writes the database query (SQL),** and the API application runs it read-only. Answers almost any question, but a wrong query is hard to detect and gives a confident wrong answer.
4. **Send all of a project's rows to the model** and let it answer. Unreliable numbers, more client data sent than needed, and slower and costlier as data grow.
5. **Vector search over rows** (classic retrieval for documents). A poor fit for filters, counts and averages; it is the tool for PDFs later.

## Decision

Option 2, with checks at each step.

**Building blocks (initial set, from UC-01 to UC-04):**

- Filters: survey year or range of years; PCI above, below or between values; specific sections; distance from a point (UC-04); project or whole network.
- Operations: list; latest value per section; change between surveys; count; average (by section count, UC-03); compare two years or two groups.

**How a question is answered:**

1. The model turns the question into a query plan made of these blocks, or states that the question cannot be answered with them.
2. The API application validates the plan: allowed operations and fields only, PCI between 0 and 100, years present in the data, valid section identifiers and coordinates.
3. The API application adds the client, the project and the user's permissions itself. These never come from the model. Row-level security enforces them again in the database.
4. The database runs the parameterized query with read-only access and a row limit. The values in the plan (for example, 55 or 2024) travel as parameters, never as code, so code cannot be injected.
5. A second model call (the judge) checks whether the plan answers the question asked. It does not check numbers.
6. The model writes the answer text from the query results. The API application checks that every number in the text appears in, or is computed from, those results. If a number does not match, the text is not shown: the user gets the plan and the results table, and the mismatch is logged.
7. The user receives the answer text, the plan stated in plain words (threshold, years, filters), and the source rows.
8. The question, plan, query, results, judge verdict and number check are logged with the user and time.

**Further rules:**

- If no plan fits, the answer says the question cannot be answered yet, and the question is logged. The logs show which blocks to add next.
- The judge runs on every answer during the pilot. After the pilot, the logs decide whether it stays on every answer or only on some.
- Model-written queries (option 3) are not in the first release. They are reconsidered in a new ADR only if the logs show questions the blocks cannot express. If allowed then, they need read-only access, approved tables only, row limits and judge review.

## Attributes gained

- **Data traceability (high):** every answer links to its plan, query and rows, and all of it is logged.
- **Security (high):** the model never writes code and never reaches the database. Parameters rule out code injection. Client, project and permissions come from the API application and are enforced again by row-level security. Only the result rows are sent to the model.
- **Usability (medium):** combinable blocks cover filters, thresholds and comparisons in many forms, and users see how their question was interpreted, so they can check it.
- **Maintainability (medium):** a new kind of question means a new block, found through the logs and covered by the test set.

## Attributes sacrificed

- **Performance (medium):** the judge adds a second model call to every answer during the pilot; the number check adds a little time.
- **Deployability and simplicity (high), partly:** the plan format, validation, judge and number check are more to build than fixed queries.
- **Usability (medium), partly:** questions the blocks cannot express get "cannot answer yet" until a block is added.

## Consequences

- C2: the API application to language model relationship and the language model description state these steps, and that the model has no access to the database.
- C3: the question-answering module contains plan generation, plan validation, the query builder, the judge, answer writing, the number check and logging.
- The test set from the language model ADR is extended: each test question has its expected plan and its expected numbers.
- The logs hold client data (questions and results). They are stored in the platform database under row-level security, in the US, and kept like other data under data traceability.
- Each answer costs two or three model calls (plan, judge, answer text) instead of one. The price depends on the model chosen.
- Open items: the row limit and query time limit; whether the judge stays on every answer after the pilot; whether UC-01 to UC-04 default to the project or the whole network (open item in the use cases).
