# Structure the backend as a modular monolith with bronze, silver and gold data layers

- Date: 2026-11-23
- Status: Accepted

## Context

- C2 has one API application, a modular monolith (CLAUDE.md). This ADR decides its internal structure (C3).
- Already fixed by accepted ADRs:
  - sign-in tokens come from the identity service (ADR 2026-11-23-delegate-sign-in-to-an-identity-service);
  - client data are isolated with row-level security (ADR 2026-11-23-isolate-client-data-with-row-level-security);
  - the language model is reached only through an interface (ADR 2026-11-23-language-model-behind-replaceable-interface);
  - PCI data arrive by CSV and Excel upload, plus an automatic connection for the funding agency, through one validation path (ADR 2026-11-23-load-pci-data-by-upload-and-connection);
  - answers are grounded through validated query plans (ADR 2026-11-23-ground-answers-with-validated-query-plans).
- Needs from the use cases:
  - loads that can be run again safely, with a summary of rows added, conflicts and rejected rows (UC-05);
  - corrections that keep old values (UC-09);
  - PCI by survey year for the views and the answers (UC-02, UC-03, UC-06);
  - access per project (UC-07, UC-08).
- Reproducing what the platform showed on a past date ("time travel") is not required.
- Quality attributes involved (quality-attributes.md): security, data traceability, deployability and simplicity, and recoverability (all high); maintainability, extensibility and performance (medium).

Options considered: one per high-priority attribute, in the order of quality-attributes.md, plus a balanced option.

- **A. Security first.** A monolith split into two parts, with a security core: a request guard that denies by default, a database role per module, a separate answer service with read-only rights, a secrets store, and a log of every access decision. Needs a second deployable.
- **B. Data traceability first.** An event-sourced core: no value is ever overwritten; every change is stored as a permanent event, and current values and views are computed from the events. Includes time travel.
- **C. Deployability and simplicity first.** A plain layered monolith (endpoints, services, data access) with only the adapters the ADRs require. Everything runs inside the request.
- **D. Recoverability first.** A stateless API, a durable job queue with a separate worker, a load ledger that allows rebuilding data by replay, export and restore of one client at a time, and scheduled test restores. Needs a second deployable, and original files must be kept.
- **E. Balanced.** A modular monolith by business area, with one central access guard, versioned PCI history, a load ledger, and background jobs in the same process.
- **F. E combined with selected parts of A, B and D.** E's structure; bronze, silver and gold data layers in place of B's events; retryable loads with a conflict summary from D; read-only answering with values sent as parameters by the API, from A and the grounding ADR.

Comparison of A to E against quality-attributes.md (1 weakest, 5 strongest of the five; relative judgments, not measurements):

| Attribute (priority) | A | B | C | D | E |
|---|---|---|---|---|---|
| Security (high) | 5 | 3 | 3 | 3 | 4 |
| Data traceability (high) | 3 | 5 | 2 | 4 | 4 |
| Deployability and simplicity (high) | 2 | 1 | 5 | 2 | 4 |
| Recoverability (high) | 3 | 4 | 2 | 5 | 3 |
| Maintainability (medium) | 3 | 2 | 3 | 3 | 4 |
| Extensibility (medium) | 3 | 4 | 3 | 4 | 4 |
| Performance (medium) | 3 | 3 | 3 | 4 | 3 |

Relative operating cost: A medium to high; B medium; C low; D medium to high; E low to medium. Model calls and the identity service subscription cost the same in all options. Compared with E, F adds traceability and recoverability through the data layers, at the cost of more tables and a refresh step.

## Decision

Option F.

**Structure.** One deployable API application, split into modules by business area. Each module owns its tables, and other modules use it only through its interface.

- **Access module:**
  - access guard: on every request, checks the sign-in token, resolves the user and client, loads project permissions, and sets the client for row-level security; denies by default (UC-07);
  - access management: grants and removes project access and permissions (UC-08).
- **Projects module:** project list and workspace, limited to the projects granted to the user (UC-06, UC-07).
- **Loading module:**
  - input adapters for CSV, Excel and the agency connection, using the column mapping saved per client;
  - load jobs: uploads and agency connection runs are retryable background jobs in the same process, tracked in a job table; running a load again does not duplicate rows;
  - validation and load summary: moves rows from bronze to silver with the UC-05 checks, and lists rows added, conflicts and rejected rows with the reason (UC-05).
- **PCI data module:**
  - corrections: corrects or deletes PCI values as new versions with who, when and why, and resolves load conflicts (UC-09);
  - gold refresh: rebuilds the gold tables from silver after each load or correction.
- **Views module:** project overview and section view, read from gold (UC-06).
- **Question answering module:** query planner, query builder, answer writer, answer checks (judge and number check), and the language model interface, as in the grounding and language model ADRs. Read-only database access, to gold only (UC-01 to UC-04).
- **Audit module:** log of changes, access decisions and every answer step.

**Data layers.** Three schemas in the same platform database, all under row-level security:

- **Bronze:** every load exactly as received, with who loaded it, when, and the source file or connection run. Never changed.
- **Silver:** validated PCI per network section and survey year. Corrections and deletions are new versions with who, when and why. Conflicts are recorded here.
- **Gold:** serving tables: latest PCI per section, PCI by survey year, project overview and network summaries. Rebuilt from silver.

**Conflict rule.** When a load brings a section and survey year that already exist, the existing value stays, and the load summary shows both values. A user with the Correct and delete permission can accept the new value as a correction (UC-09), with a reason.

**Not built:** time travel.

**Secrets.** Keys for the language model, the identity service and the agency connection come from the cloud provider's secret manager and are injected as settings when the application starts. The code reads settings only and never calls the provider directly, so changing providers changes the deployment setup, not the code.

**Module boundaries** are checked in code review and by simple automated checks, for example a test that fails if one module reads another module's tables.

## Attributes gained

- **Security (high):** one guard on every request, denying by default. Answering has read-only access to gold only; plan values travel as parameters, and the API adds client, project and permissions. Row-level security covers every layer. Secrets stay outside the code.
- **Data traceability (high):** bronze keeps exactly what each client sent; silver keeps every version with who, when and why; each answer logs its plan, query and rows.
- **Deployability and simplicity (high):** one deployable and no new container; no event sourcing; background jobs run in the same process.
- **Recoverability (high):** failed loads can be run again; gold can be rebuilt from silver, and silver can be checked against bronze; one backup covers all layers.
- **Maintainability (medium):** modules by business area, each owning its tables.
- **Extensibility (medium):** a new source is a new input adapter into bronze; a new dashboard is a new gold table; PDFs later follow the same path.

## Attributes sacrificed

- **Deployability and simplicity (high), partly:** three data layers mean more tables than a plain layered design, and a refresh step after each load or correction.
- **Performance (medium), slightly:** gold is refreshed after each load or correction, and background jobs share the process with requests.
- **Recoverability (high), partly:** one client cannot be restored alone (as noted in the isolation ADR), and there are no scheduled test restores beyond the minimum in quality-attributes.md.
- **Security (high), partly:** compared with option A, answering runs in the same process as the rest. It is limited by its read-only database role, not by a process boundary.
- **Data traceability (high), partly:** no time travel; what the platform showed on a past date is not reconstructed.

## Consequences

- C3: c3-components.puml shows these modules, their components and the three data layers.
- C2: the platform database description names the three layers. No new container.
- UC-05: the conflict rule and rerunnable loads are added, and the open item on repeated sections and years is closed.
- The building blocks of the grounding ADR's query plans map to gold tables.
- Storage grows with every load, since bronze keeps every raw row.
- If a client later needs to be restored alone, or answering must run in its own process, options D or A are reconsidered in a new ADR.
- Open items:
  - whether original files are also kept in file storage (bronze keeps the rows; the original keeps the exact file);
  - which cloud secret manager, and whether the funding agency requires hosting on its own infrastructure;
  - the list of gold tables, which grows with the views and the query plan blocks.
