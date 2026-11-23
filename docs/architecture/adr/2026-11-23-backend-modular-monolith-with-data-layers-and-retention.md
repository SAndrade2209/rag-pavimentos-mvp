# Structure the backend as a modular monolith with data layers and retention periods

- Date: 2026-11-23
- Status: Accepted

## Context

- This ADR replaces ADR 2026-11-23-backend-modular-monolith-with-data-layers after a review of the architecture for unneeded complexity (2026-11-23). The modules and the bronze, silver and gold data layers stay. The changes:
  - gold is rebuilt in the same database transaction as each load or correction;
  - original files are kept for a retention period, and a scheduled job deletes them and expired answer log entries;
  - the audit log records denied requests, not every allowed request;
  - option F, the chosen option, is scored with the other options;
  - the question answering module follows ADR 2026-11-23-ground-answers-with-judged-plans-and-answer-templates.
- C2 has one API application, a modular monolith (CLAUDE.md). This ADR decides its internal structure (C3).
- Already fixed by accepted ADRs:
  - sign-in tokens come from the identity service (ADR 2026-11-23-delegate-sign-in-to-an-identity-service);
  - client data are isolated with row-level security (ADR 2026-11-23-isolate-client-data-with-row-level-security);
  - the language model is reached only through an interface (ADR 2026-11-23-language-model-behind-replaceable-interface);
  - PCI data arrive by CSV and Excel upload, plus an automatic connection for the funding agency, through one validation path (ADR 2026-11-23-load-pci-data-by-upload-and-connection);
  - answers are grounded through judged query plans and answer templates (ADR 2026-11-23-ground-answers-with-judged-plans-and-answer-templates).
- Needs from the use cases:
  - loads that can be run again safely, with a summary of rows added, conflicts and rejected rows (UC-05);
  - corrections that keep old values (UC-09);
  - PCI by survey year for the views and the answers (UC-02, UC-03, UC-06);
  - access per project (UC-07, UC-08).
- Loads and use:
  - the largest load is expected to be the initial load of each client's PCI history; its size is not known. Later loads add survey years, yearly or less often per client (load ADR);
  - few users work at the same time;
  - original uploaded files are kept for a period as evidence of each load;
  - PDFs come later (CLAUDE.md), and file storage will hold them.
- Reproducing what the platform showed on a past date ("time travel") is not required.
- Quality attributes involved (quality-attributes.md): security, data traceability, deployability and simplicity, and recoverability (all high); maintainability, extensibility and performance (medium).

Options considered: one per high-priority attribute, in the order of quality-attributes.md, a balanced option, and a combination.

- **A. Security first.** A monolith split into two parts, with a security core: a request guard that denies by default, a database role per module, a separate answer service with read-only rights, a secrets store, and a log of every access decision. Needs a second deployable.
- **B. Data traceability first.** An event-sourced core: no value is ever overwritten; every change is stored as a permanent event, and current values and views are computed from the events. Includes time travel.
- **C. Deployability and simplicity first.** A plain layered monolith (endpoints, services, data access) with only the adapters the ADRs require. Everything runs inside the request.
- **D. Recoverability first.** A stateless API, a durable job queue with a separate worker, a load ledger that allows rebuilding data by replay, export and restore of one client at a time, and scheduled test restores. Needs a second deployable, and original files must be kept.
- **E. Balanced.** A modular monolith by business area, with one central access guard, versioned PCI history, a load ledger, and background jobs in the same process.
- **F. E combined with selected parts of A, B and D.** E's structure; bronze, silver and gold data layers in place of B's events; retryable loads with a conflict summary from D; read-only answering with values sent as parameters by the API, from A and the grounding ADR.

Comparison against quality-attributes.md (1 weakest, 5 strongest of the six; relative judgments, not measurements):

| Attribute (priority) | A | B | C | D | E | F |
|---|---|---|---|---|---|---|
| Security (high) | 5 | 3 | 3 | 3 | 4 | 4 |
| Data traceability (high) | 3 | 5 | 2 | 4 | 4 | 4 |
| Deployability and simplicity (high) | 2 | 1 | 5 | 2 | 4 | 3 |
| Recoverability (high) | 3 | 4 | 2 | 5 | 3 | 4 |
| Maintainability (medium) | 3 | 2 | 3 | 3 | 4 | 4 |
| Extensibility (medium) | 3 | 4 | 3 | 4 | 4 | 4 |
| Performance (medium) | 3 | 3 | 3 | 4 | 3 | 3 |

Relative operating cost: A medium to high; B medium; C low; D medium to high; E low to medium; F low to medium. Model calls and the identity service subscription cost the same in all options. Compared with E, F keeps the raw rows in bronze and the original files for a period. Recoverability gains one step; traceability gains less than one step on this scale. The cost is more tables, a refresh step, file storage and a retention job.

## Decision

Option F.

**Structure.** One deployable API application, split into modules by business area. Each module owns its tables, and other modules use it only through its interface.

- **Access module:**
  - access guard: on every request, checks the sign-in token, resolves the user and client, loads project permissions, and sets the client for row-level security; denies by default (UC-07);
  - access management: grants and removes project access and permissions (UC-08).
- **Projects module:** project list and workspace, limited to the projects granted to the user (UC-06, UC-07).
- **Loading module:**
  - input adapters for CSV, Excel and the agency connection, using the column mapping saved per client; each uploaded file goes to file storage and its rows to bronze;
  - load jobs: uploads and agency connection runs are retryable background jobs in the same process, tracked in a job table; running a load again does not duplicate rows. Loads run in the background because the initial load of a client's history may take longer than a web request allows;
  - validation and load summary: moves rows from bronze to silver with the UC-05 checks, and lists rows added, conflicts and rejected rows with the reason (UC-05);
  - retention job: a scheduled job in the same process. Deletes original files when their retention period ends, and asks the audit module to delete expired answer log entries.
- **PCI data module:**
  - corrections: corrects or deletes PCI values as new versions with who, when and why, and resolves load conflicts (UC-09);
  - gold refresh: rebuilds the client's gold tables from silver in the same database transaction as each load or correction, so gold never shows a partial or outdated state.
- **Views module:** project overview and section view, read from gold (UC-06).
- **Question answering module:** query planner, judge, query builder, answer writer with templates and the reword check, and the language model interface, as in the grounding and language model ADRs. Read-only database access, to gold only (UC-01 to UC-04).
- **Audit module:** log of PCI data changes, project access grants and removals, denied requests, load summaries, and the answer log of the grounding ADR. Allowed requests are not logged one by one.

**Data layers.** Three schemas in the same platform database, all under row-level security:

- **Bronze:** every load exactly as received, with who loaded it, when, and the source file or connection run. Never changed.
- **Silver:** validated PCI per network section and survey year. Corrections and deletions are new versions with who, when and why. Conflicts are recorded here.
- **Gold:** serving tables: latest PCI per section, PCI by survey year, project overview and network summaries. Rebuilt from silver with each load or correction.

**Retention.**

- Original uploaded files stay in file storage for a retention period, then are deleted. Bronze keeps the rows of every load, so each load stays traceable after its file is deleted.
- Answer log entries stay for a retention period, then are deleted (grounding ADR).
- Retention applies only to these two. PCI records in bronze and silver, with their versions, are the network's PCI history and are kept (UC-05, UC-09).
- Each module deletes its own records: the loading module deletes files, and the audit module deletes answer log entries when the retention job asks.
- The retention periods are set with each client.

**Conflict rule.** When a load brings a section and survey year that already exist, the existing value stays, and the load summary shows both values. A user with the Correct and delete permission can accept the new value as a correction (UC-09), with a reason.

**Not built:** time travel.

**Secrets.** Keys for the language model, the identity service and the agency connection come from the cloud provider's secret manager and are injected as settings when the application starts. The code reads settings only and never calls the provider directly, so changing providers changes the deployment setup, not the code.

**Module boundaries** are checked in code review and by simple automated checks, for example a test that fails if one module reads another module's tables.

## Attributes gained

- **Security (high):** one guard on every request, denying by default, and denied requests are logged. Answering has read-only access to gold only; plan values travel as parameters, and the API adds client, project and permissions. Row-level security covers every layer. Secrets stay outside the code.
- **Data traceability (high):** bronze keeps exactly what each client sent, and file storage keeps the original file for its retention period; silver keeps every version with who, when and why; the answer log links each answer to its plans, verdicts, query and rows.
- **Deployability and simplicity (high):** one deployable; no event sourcing; load jobs and the retention job run in the same process, with no separate worker or queue.
- **Recoverability (high):** failed loads can be run again; gold can be rebuilt from silver; silver can be checked against bronze and, during the retention period, against the original files; one database backup covers all layers.
- **Maintainability (medium):** modules by business area, each owning its tables and deleting its own records for retention.
- **Extensibility (medium):** a new source is a new input adapter into bronze; a new dashboard is a new gold table; PDFs later use file storage and the same loading path.

## Attributes sacrificed

- **Deployability and simplicity (high), partly:** three data layers mean more tables than a plain layered design; each load or correction includes a gold refresh; file storage is one more container to run and back up; the retention job is one more scheduled task.
- **Performance (medium), slightly:** each load or correction waits for its gold refresh, and background jobs share the process with requests. Accepted because few users work at the same time and loads are infrequent.
- **Recoverability (high), partly:** one client cannot be restored alone (as noted in the isolation ADR), and there are no scheduled test restores beyond the minimum in quality-attributes.md.
- **Security (high), partly:** compared with option A, answering runs in the same process as the rest. It is limited by its read-only database role, not by a process boundary. Allowed requests are not logged one by one, so the audit log cannot list every read of a client's data.
- **Data traceability (high), partly:** no time travel; original files and answer log entries are deleted after their retention periods.

## Consequences

- C3: c3-components.puml shows these modules, their components, the three data layers, file storage and the retention job.
- C2: the platform database description names the three layers and the answer log retention. File storage is no longer an assumption.
- UC-05 keeps the conflict rule and rerunnable loads.
- The building blocks of the grounding ADR's query plans map to gold tables.
- Storage grows with every load, since bronze keeps every raw row. Original files stop taking space when their retention period ends.
- If a client later needs to be restored alone, or answering must run in its own process, options D or A are reconsidered in a new ADR.
- If a client's security requirements call for a log of every allowed request, the audit module adds it through a new ADR.
- Open items:
  - the retention periods for original files and for answer log entries, set with each client (records retention rules are an open question in quality-attributes.md);
  - the size of each client's initial load (sections and survey years in its history);
  - which cloud secret manager, and whether the funding agency requires hosting on its own infrastructure;
  - the list of gold tables, which grows with the views and the query plan blocks.
