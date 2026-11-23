# Ground answers through judged query plans and answer templates

- Date: 2026-11-23
- Status: Accepted

## Context

- This ADR replaces ADR 2026-11-23-ground-answers-with-validated-query-plans after a review of the architecture for unneeded complexity (2026-11-23). It keeps query plans built from blocks and changes three points:
  - the judge could reject a plan, but nothing said what happened next;
  - the number check accepted any number that "appears in, or is computed from" the results. "Computed from" had no defined limit, and a number that matches the results can still be attached to the wrong survey year or section;
  - the answer log kept every result with no end date, so it held client data under records retention rules that are not known yet.
- UC-01 to UC-04: answers come from the client's PCI data. Each answer gives the source rows and states the threshold, years and filters used. No charts.
- Answers must be grounded: every statement and every number in an answer traces back to PCI rows in the platform. Accuracy and security come first.
- Language models read questions and write text well, but they are unreliable at arithmetic over many rows. A model can state a wrong average or count with full confidence.
- The language model is reached only through the platform's interface and has no access to the database (ADR 2026-11-23-language-model-behind-replaceable-interface). Client data are isolated with row-level security (ADR 2026-11-23-isolate-client-data-with-row-level-security).
- Constraint (CLAUDE.md): language model processing stays in the US.
- Quality attributes involved (quality-attributes.md): data traceability (high), security (high), deployability and simplicity (high), usability (medium), maintainability (medium), performance (medium).

Options considered for turning a question into data (the same as in the replaced ADR):

1. **Fixed prepared queries,** one per question type in UC-01 to UC-04. Safe and exact, but any variation outside the fixed queries cannot be answered.
2. **Query plans built from blocks.** The model fills in a structured request (a query plan) by combining filters and operations; the API application validates it and turns it into a parameterized database query.
3. **The model writes the database query (SQL),** and the API application runs it read-only. Answers almost any question, but a wrong query is hard to detect and gives a confident wrong answer.
4. **Send all of a project's rows to the model** and let it answer. Unreliable numbers, more client data sent than needed, and slower and costlier as data grow.
5. **Vector search over rows** (classic retrieval for documents). A poor fit for filters, counts and averages; it is the tool for PDFs later.

Options considered for the answer text:

- **A. The model writes the text from the result rows,** and the API application checks the numbers (the replaced ADR). Readable, but the result rows go to the model, and the check cannot tell whether a correct number is attached to the right survey year or section.
- **B. The API application writes the text from templates,** one per operation. Exact, and no PCI data go to the model for the answer. The wording is fixed.
- **C. B, then the model rewords the template text.** The model receives the question and the template text, never the result rows. The API application accepts the reworded text only if it keeps the same numbers, survey years and section identifiers, in the same order.

Options considered when the judge rejects a plan:

- **Answer anyway, with a warning.** The user may get an answer that does not fit the question.
- **Stop at the first rejection.** Safe, but one wrong plan ends the question.
- **Build a new plan with the judge's reason,** up to a fixed number of plans, then stop.

## Decision

Option 2 for turning a question into data, option C for the answer text, and a new plan after each rejection, up to three plans in total.

**Building blocks (initial set, from UC-01 to UC-04):**

- Filters: survey year or range of years; PCI above, below or between values; specific sections; distance from a point (UC-04); project or whole network.
- Operations: list; latest value per section; change between surveys; count; average (by section count, UC-03); compare two years or two groups.

**How a question is answered:**

1. The model turns the question into a query plan made of these blocks, or states that the question cannot be answered with them.
2. The API application validates the plan: allowed operations and fields only, PCI between 0 and 100, years present in the data, valid section identifiers and coordinates.
3. A second model call (the judge) checks whether the plan answers the question asked. It receives the question and the plan, never PCI rows. It does not check numbers.
4. If the judge rejects the plan, the model builds a new plan using the judge's reason, and steps 2 and 3 run again. After the third rejected plan, the user is told that the question cannot be answered yet, and the question, every plan and every verdict are logged.
5. The API application adds the client, the project and the user's permissions itself. These never come from the model. Row-level security enforces them again in the database.
6. The database runs the parameterized query with read-only access and a row limit. The values in the plan (for example, 55 or 2024) travel as parameters, never as code, so code cannot be injected.
7. The API application writes the answer text with the template for the plan's operation. Every number, survey year, PCI threshold and section identifier in the text comes from the query results or the validated plan. The template also carries the statements UC-01 to UC-04 require, such as the threshold and years used and, for averages, that they are by section count (UC-03).
8. The model then rewords that text for readability. It receives the question and the template text, never the result rows. The API application accepts the reworded text only if it contains the same numbers, survey years and section identifiers as the template text, in the same order. Otherwise the user gets the template text, and the mismatch is logged.
9. The user receives the answer text, the plan stated in plain words (threshold, years, filters), and the source rows.
10. The question, every plan and judge verdict, the query, the results, the template text, the reworded text and the check result are logged with the user and time.

**Further rules:**

- If no plan fits (step 1), the answer says the question cannot be answered yet, and the question is logged. The logs show which blocks to add next.
- [assumption] A plan that fails validation in step 2 counts as a rejected plan, with the validation error as the reason.
- The judge runs on every answer.
- Each operation has one template. A new operation needs a new template, covered by the test set.
- Answer log entries are kept for a retention period, then deleted by the retention job (ADR 2026-11-23-backend-modular-monolith-with-data-layers-and-retention). The period is set with each client.
- Model-written queries (option 3) are not in the first release. They are reconsidered in a new ADR only if the logs show questions the blocks cannot express. If allowed then, they need read-only access, approved tables only, row limits and judge review.

## Attributes gained

- **Data traceability (high):** every number in an answer comes from the query results or the validated plan through a template, and a reworded text that changes a number, year or section is not shown. Every answer links to its plans, judge verdicts, query and rows in the log.
- **Security (high):** the model never writes code and never reaches the database. Parameters rule out code injection. Client, project and permissions come from the API application and are enforced again by row-level security. The model never receives result rows; it receives the question, the plans and the template text.
- **Usability (medium):** combinable blocks cover filters, thresholds and comparisons in many forms, and users see how their question was interpreted, so they can check it. The reworded text reads naturally when it passes the check. A plan the judge keeps rejecting ends in "cannot answer yet", not in a doubtful answer.
- **Maintainability (medium):** a new kind of question means a new block and a new template, found through the logs and covered by the test set. Rejected plans in the log show where the planner needs work.

## Attributes sacrificed

- **Performance (medium):** an answered question takes at least three model calls (plan, judge, reword) and up to seven when the judge rejects plans (three plans, three verdicts, one reword).
- **Deployability and simplicity (high), partly:** the plan format, validation, the judge with new plans, the templates and the reword check are more to build than fixed queries.
- **Security (high), partly:** the template text sent for rewording contains the answer's figures and section identifiers. Only the full result rows stay in the platform.
- **Usability (medium), partly:** questions the blocks cannot express, and questions whose plans are rejected three times, get "cannot answer yet" until a block is added or the planner improves. When a reword fails the check, the user reads the fixed template wording.
- **Data traceability (high), partly:** answer log entries are deleted after the retention period, so an older answer cannot be shown again exactly. Loads and corrections keep their full history (backend ADR).

## Consequences

- C2: the language model description and the API application to language model relationship state the plan, judge and reword steps, and that the model receives no result rows and has no access to the database.
- C3 (view 3): the question answering module contains the query planner (up to three plans), the judge, the query builder, the answer writer (templates and reword check) and the language model interface. The answer log goes to the audit module.
- The language model interface (ADR 2026-11-23-language-model-behind-replaceable-interface) has three operations: build a query plan, judge a plan, and reword a template text. That ADR's example of drafting answers from retrieved PCI rows no longer applies.
- The test set from the language model ADR is extended: each test question has its expected plan, its expected numbers and its expected template text. Each test run also reports how often the judge rejects a correct plan and how often a reword fails the check.
- The logs hold client data (questions, results and template text). They are stored in the platform database under row-level security, in the US, and deleted after the retention period.
- An answered question costs three to seven model calls, instead of two or three in the replaced ADR. The price depends on the model chosen.
- Open items: the row limit and query time limit; the retention period for answer logs, set with each client; whether UC-01 to UC-04 default to the project or the whole network (open item in the use cases).
