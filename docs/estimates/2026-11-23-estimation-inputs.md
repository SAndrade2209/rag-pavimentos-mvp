# Estimation inputs: requirements, functionalities, interfaces and components

- Date: 2026-11-23
- Status: Draft for review
- Basis: use cases UC-01 to UC-09, `docs/architecture/quality-attributes.md`, the C4 diagrams (C1 to C3) and the 7 accepted ADRs, at commit 19204b0
- Work list for the estimate: `2026-11-23-estimation-work-list.xlsx`, built from the tables in this document

## Purpose

This document distills the use cases, quality attributes, C4 diagrams and accepted ADRs into the inputs a later effort estimate needs: what the platform must do, what has to be built, what is reused, which interfaces and integrations are involved, and how complex each component is. It gives no effort, cost or schedule figures.

Complexity ratings are judgments made for this document, with the reasons stated (Section 7). Items the sources do not state are marked [assumption], like the assumptions carried over from the sources.

| Prefix | Meaning | Section |
|---|---|---|
| FR | Functional requirement | 2 |
| TR | Technical requirement that drives effort | 3 |
| F | Functionality (user-visible feature or platform service) | 4 |
| IF | Interface or integration | 5 |
| C | Component to develop | 6 |
| R | Reused component | 6 |
| A | Activity that is not a component | 6 |
| U | Unknown that changes the estimate | 8 |

ADR numbers follow the reading order of the architecture report:

| ADR | File in `docs/architecture/adr/` |
|---|---|
| ADR 1 | `2026-11-20-use-c4-model.md` |
| ADR 2 | `2026-11-23-delegate-sign-in-to-an-identity-service.md` |
| ADR 3 | `2026-11-23-isolate-client-data-with-row-level-security.md` |
| ADR 4 | `2026-11-23-load-pci-data-by-upload-and-connection.md` |
| ADR 5 | `2026-11-23-language-model-behind-replaceable-interface.md` |
| ADR 6 | `2026-11-23-ground-answers-with-judged-plans-and-answer-templates.md` |
| ADR 7 | `2026-11-23-backend-modular-monolith-with-data-layers-and-retention.md` |

## 1. Scope baseline

### 1.1 In and out of the MVP

In the MVP (README, CLAUDE.md):

- Question answering over tabular PCI data (section, coordinates, PCI, year). Answers are text and tables, without charts.
- Project list and project workspace, as in the demo.
- Project data overview (current PCI by section) and section view (PCI by survey year with gaps, survey timeline).
- Sign-in, access by project and access management.
- Loading PCI data by CSV and Excel upload, plus an automatic connection for the funding agency.
- Corrections and deletions that keep the old values, with who, when and why.

Out of the MVP: PDF documents and PDF extraction, public pavement data sources, network map and network view, specifications, and the workbench (mix design, material characterization, pavement life prediction, construction acceptance).

### 1.2 Size indicators

| Indicator | Value | Source |
|---|---|---|
| Use cases | 9: six main (UC-01 to UC-06), three supporting (UC-07 to UC-09) | `docs/use-cases/README.md` |
| User roles | 8: five use PCI data, three manage project access | C1 |
| Permissions per project | 4: View, Load, Correct and delete, Manage access [assumption] | `docs/use-cases/README.md` |
| Containers | 5: web application, API application, language model, platform database, file storage | C2 |
| External systems | 4: identity service, client identity provider, Continuum Google Workspace, client pavement management system | C1 |
| API modules | 7: access, projects, views, loading, PCI data, question answering, audit | ADR 7 |
| API components | 16 | C3 |
| Database layers | 3 schemas (bronze, silver, gold) plus platform tables | ADR 7 |
| Input adapters now | 3: CSV, Excel, funding agency connection | ADR 4 |
| Query plan blocks | 5 filters and 6 operations | ADR 6 |
| Answer templates | 6, one per operation | ADR 6 |
| Language model operations | 3: build a query plan, judge a plan, reword a template text | ADR 6 |
| Model calls per answered question | 3 to 7 | ADR 6 |
| Expected clients | 1 to 3 in the first year or two | ADR 3 |
| Load frequency | Yearly or less often per client; the largest load is each client's initial history, size not known | ADR 4; ADR 7 |
| Concurrent users | Few | ADR 7 |

## 2. Functional requirements

### 2.1 Sign-in and access (UC-07, UC-08)

| ID | Requirement | Source |
|---|---|---|
| FR-01 | Users sign in through the identity service with MFA, using a platform account, their organization's own account (single sign-on, for clients that require it) or, for Continuum staff, Google Workspace. | UC-07; ADR 2 |
| FR-02 | The API accepts only signed sign-in tokens (OpenID Connect) and stores no passwords. | ADR 2 |
| FR-03 | A user without access to any project cannot sign in. | UC-07; ADR 2 |
| FR-04 | The project list shows only the projects granted to the user. Opening a project that was not granted is refused. | UC-07 |
| FR-05 | Inside a project, the available actions match the user's permissions on that project: View, Load, Correct and delete, Manage access [assumption]. | UC-07; use cases README |
| FR-06 | Every request passes an access guard that checks the token, resolves the user and client, loads project permissions, sets the client for row-level security and denies by default. Denied requests are logged. | ADR 7 |
| FR-07 | Managers grant and remove a person's access to a project and set the permissions. [assumption] A client manager covers all projects of their client, a project lead their own project, and a Continuum administrator any project. | UC-08 |
| FR-08 | A Continuum administrator sets up each client and its first client manager. | UC-08; C1 |
| FR-09 | [assumption] Each grant or removal records who made it and when. | UC-08; ADR 7 |
| FR-10 | [assumption] The PCI data a person loaded stay in the platform after their access is removed. | UC-08 |

### 2.2 Projects and views (UC-06)

| ID | Requirement | Source |
|---|---|---|
| FR-11 | Project list and project workspace follow the demo's display. | README; UC-06 |
| FR-12 | Project data overview: a table of the project's sections with the latest PCI and the survey year of that PCI. | UC-06 |
| FR-13 | Section view: PCI by survey year as a chart, with years without a survey marked as gaps (not filled), and the survey timeline. | UC-06 |
| FR-14 | The section view shows every survey year stored for the section on the network, including surveys loaded through other projects. | UC-06 |
| FR-15 | Views require the View permission and read from the gold serving tables. | UC-06; ADR 7 |

### 2.3 Loading PCI data (UC-05)

| ID | Requirement | Source |
|---|---|---|
| FR-16 | Users with the Load permission upload CSV and Excel (.xlsx) files into a project through the web application. | UC-05; ADR 4 |
| FR-17 | Each client's column names are mapped once to section, coordinates, PCI and year; the mapping is saved and reused by later loads. | ADR 4 |
| FR-18 | Every source is converted to one internal format (client, project, section, coordinates, PCI, year) and passes the same validation. | ADR 4 |
| FR-19 | Rows are validated and rejected rows are listed with the reason. [assumption] A row is rejected if section, PCI or year is missing, or if PCI is outside the 0 to 100 scale. | UC-05 |
| FR-20 | New survey years are added and existing ones kept. A section and survey year that already exist are a conflict: the existing value stays, and the load summary shows both values. | UC-05; ADR 7 |
| FR-21 | The load summary lists rows added, conflicts, rejected rows with the reason, and column mapping problems. | UC-05 |
| FR-22 | Loads run as background jobs. A failed load can be run again without duplicating data. | UC-05; ADR 7 |
| FR-23 | Each load is recorded with who started it, when and from which source. Its raw rows are kept as received, and the original file is kept for a retention period. | ADR 4; ADR 7 |
| FR-24 | PCI records are stored for the network section and survey year, and nothing is deleted when the project ends. | UC-05 |
| FR-25 | For the funding agency only, an automatic connection to its pavement management system, started by a user with the Load permission (a schedule only if the agency requires one). Read-only, limited to PCI data. Method pending. | ADR 4 |
| FR-26 | Data loaded for one client are visible only to that client's users. | UC-05; ADR 3 |

### 2.4 Corrections and deletions (UC-09)

| ID | Requirement | Source |
|---|---|---|
| FR-27 | Users with the Correct and delete permission correct a PCI value or delete records, giving a reason. | UC-09 |
| FR-28 | The old value or the deleted record is hidden from views and answers but kept, with who made the change, when and why. | UC-09; ADR 7 |
| FR-29 | A conflicting loaded value can be accepted as a correction, with a reason. | UC-05; UC-09 |
| FR-30 | After a load or correction, views and answers use the new values: gold is rebuilt in the same database transaction. | UC-09; ADR 7 |
| FR-31 | [assumption] The change history of a section can be viewed. | UC-09 |

### 2.5 Question answering (UC-01 to UC-04)

| ID | Requirement | Source |
|---|---|---|
| FR-32 | Users with the View permission ask natural-language questions about their client's PCI data: M&R candidates below a threshold (UC-01), PCI over time and change between surveys (UC-02), network averages and counts by survey year (UC-03), and sections by distance from a point and last survey year (UC-04). | UC-01 to UC-04 |
| FR-33 | Each answer gives a short text, the interpretation in plain words (threshold, years, filters), the source rows and a downloadable table. No charts. | README; ADR 6 |
| FR-34 | If a question gives no threshold and none is configured, the platform asks the user for one before answering. [assumption] The same applies to counts below a threshold in UC-03, which follow "the same rule as UC-01". | UC-01; UC-03 |
| FR-35 | Answers state what each use case requires: the years compared and the years without a survey, not filled (UC-02); that averages are by section count, not weighted by area or length (UC-03); the search radius and coordinates used (UC-04). | UC-02 to UC-04 |
| FR-36 | Questions become query plans built from blocks. Filters: survey year or range of years; PCI above, below or between values; specific sections; distance from a point; project or whole network. Operations: list; latest value per section; change between surveys; count; average by section count; compare two years or two groups. | ADR 6 |
| FR-37 | Each plan is validated (allowed operations and fields, PCI 0 to 100, years present in the data, valid section identifiers and coordinates) and judged before the query runs. A rejected plan is rebuilt with the judge's reason, up to three plans; then the user is told the question cannot be answered yet. [assumption] A plan that fails validation counts as a rejected plan. | ADR 6 |
| FR-38 | The query is parameterized and read-only, on gold, with a row limit. Client, project and permissions come from the API, never from the model. | ADR 6 |
| FR-39 | The answer text comes from one template per operation. The model's reword is shown only if its numbers, survey years and section identifiers match the template text, in the same order; otherwise the template text is shown and the mismatch is logged. | ADR 6 |
| FR-40 | A question that no plan fits gets "cannot answer yet", and the question is logged. | ADR 6 |

### 2.6 Audit and retention

| ID | Requirement | Source |
|---|---|---|
| FR-41 | The audit log records PCI data changes, project access grants and removals, denied requests, load summaries and the answer log. Allowed requests are not logged one by one. | ADR 7 |
| FR-42 | The answer log keeps the question, every plan and judge verdict, the query, the results, the template text, the reworded text and the check result, with the user and time. | ADR 6 |
| FR-43 | A scheduled retention job deletes original files and answer log entries when their retention periods end. Periods are set per client. The PCI history in bronze and silver is kept. | ADR 7 |

## 3. Technical requirements that drive effort

| ID | Requirement | Source |
|---|---|---|
| TR-01 | US data: the database, backups, language model processing, identity service user data and agency connection traffic stay in the US. | CLAUDE.md; quality attributes; ADR 2; ADR 4; ADR 5 |
| TR-02 | Portable across major cloud providers: all container candidates run on any provider or on premises; the code reads settings and never calls the provider's secret manager directly; sign-in through OpenID Connect, with cloud providers' own identity services excluded. | CLAUDE.md; C2; ADR 2; ADR 7 |
| TR-03 | Client isolation: a client identifier on every client table, row-level security on every schema, filtering in the API, and cross-client isolation tests. | ADR 3; ADR 7 |
| TR-04 | One deployable API application (modular monolith). Each module owns its tables; module boundaries are checked in code review and by automated tests. | CLAUDE.md; ADR 7 |
| TR-05 | Question answering has read-only database access to gold only, with a row limit and a query time limit. | ADR 6; ADR 7 |
| TR-06 | Keys for the language model, the identity service and the agency connection come from the cloud provider's secret manager, injected as settings at start. | ADR 7 |
| TR-07 | Automatic daily backups of the database and files, kept in a separate US location, with a restore tested. | Quality attributes |
| TR-08 | Automated tests on permissions (UC-07, UC-08), PCI history and corrections (UC-05, UC-09), cross-client isolation and module boundaries. | Quality attributes; ADR 3; ADR 7 |
| TR-09 | A fixed question test set from the UC-01 to UC-04 examples, with expected plans, numbers and template texts checked by a pavement engineer, run before and after any model change. Each run reports how often the judge rejects a correct plan and how often a reword fails the check. | ADR 5; ADR 6 |
| TR-10 | Extension points: a new source is a new input adapter (PDFs later); a new model option is a new adapter; a new question type is a new block and template; a new dashboard is a new gold table. | ADR 4 to ADR 7 |
| TR-11 | Reasonable response times. No target is defined. | CLAUDE.md; quality attributes |
| TR-12 | Not required: scaling to millions of users, multi-zone high availability, on-demand elasticity, privacy beyond standard security. | CLAUDE.md; quality attributes |

## 4. Functionalities

| ID | Functionality | Who | Requirements | Components |
|---|---|---|---|---|
| | **Access and administration** | | | |
| F-01 | Sign in and out (platform account with MFA, single sign-on, Google Workspace); refused when the user has no project | All roles | FR-01 to FR-03 | C-01, C-08, C-09, R-01 |
| F-02 | Project list, granted projects only | All roles | FR-04 | C-02, C-10 |
| F-03 | Actions inside a project shown and allowed per permission | All roles | FR-05, FR-06 | C-01, C-08 |
| F-04 | Manage project access: grant, change permissions, remove | Client manager, project lead, Continuum administrator | FR-07, FR-09, FR-10 | C-07, C-09, C-24 |
| F-05 | Set up a client and its first client manager | Continuum administrator | FR-08 | C-07, C-09 |
| | **Project and section views** | | | |
| F-06 | Project workspace, as in the demo | Users with View | FR-11 | C-02, C-10 |
| F-07 | Project data overview: latest PCI and its survey year by section | Users with View | FR-12, FR-15 | C-03, C-11, C-18 |
| F-08 | Section view: PCI chart by survey year with gaps, survey timeline, network history across projects | Users with View | FR-13 to FR-15 | C-03, C-11, C-18 |
| | **Loading** | | | |
| F-09 | Upload a CSV or Excel file into a project | Users with Load | FR-16, FR-24 | C-05, C-12, C-13 |
| F-10 | Map columns on a client's first load; reuse the saved mapping | Users with Load | FR-17 | C-05, C-13 |
| F-11 | Follow a load and read its summary: rows added, conflicts with both values, rejected rows with reasons, mapping problems | Users with Load | FR-19 to FR-21 | C-05, C-15 |
| F-12 | Run a failed load again without duplicates | Users with Load | FR-22 | C-05, C-12 |
| F-13 | Start the funding agency connection and read its load summary | Users with Load (funding agency) | FR-25 | C-05, C-12, C-14 |
| | **Corrections** | | | |
| F-14 | Correct a PCI value, with a reason | Users with Correct and delete | FR-27, FR-28, FR-30 | C-06, C-17, C-18 |
| F-15 | Delete records, including the rows of a load, with a reason | Users with Correct and delete | FR-27, FR-28, FR-30 | C-06, C-17, C-18 |
| F-16 | Accept a conflicting loaded value as a correction, with a reason | Users with Correct and delete | FR-29 | C-05, C-06, C-17 |
| F-17 | [assumption] View the change history of a section | Not decided (U-18) | FR-31 | C-06, C-17 |
| | **Question answering** | | | |
| F-18 | Ask a question in a project | Users with View | FR-32, FR-36 to FR-38 | C-04, C-19 to C-21 |
| F-19 | Read the answer: text, interpretation in plain words, source rows | Users with View | FR-33, FR-35, FR-39 | C-04, C-22 |
| F-20 | Download the answer table | Users with View | FR-33 | C-04 |
| F-21 | Give a PCI threshold when asked | Users with View | FR-34 | C-04, C-19 |
| F-22 | Receive "cannot answer yet" when no plan fits or three plans are rejected | Users with View | FR-37, FR-40 | C-04, C-19, C-20 |
| | **Platform services (no screen)** | | | |
| F-23 | Audit records: changes, access grants and removals, denied requests, load summaries, answers | System | FR-41, FR-42 | C-24 |
| F-24 | Retention: scheduled deletion of expired original files and answer log entries | System | FR-43 | C-16, C-24 |
| F-25 | Daily backups and a tested restore | Operations | TR-07 | C-28 |

## 5. Interfaces and integrations

### 5.1 External integrations

| ID | System | Direction and use | Protocol or method | Use cases | Source | Work involved |
|---|---|---|---|---|---|---|
| IF-01 | Identity service (hosted; service not chosen) | The web application sends users to sign in and receives a signed token; the API checks tokens | OpenID Connect | UC-07 | ADR 2; C2 | Configure the service (platform accounts with MFA, Google Workspace sign-in); token checks in the access guard |
| IF-02 | Client identity providers | Through the identity service, for each client that requires single sign-on | Single sign-on standards, through the identity service | UC-07 | ADR 2 | Setup with each client's IT; MFA is enforced by the client's provider, confirmed per client |
| IF-03 | Continuum Google Workspace | Through the identity service, for Continuum staff | Through the identity service | UC-07 | ADR 2 | Two-step verification required for staff who use the platform |
| IF-04 | Language model (hosted model API or self-hosted open-weight model; pending) | The API calls it only through the language model interface | HTTPS | UC-01 to UC-04 | ADR 5; ADR 6; C2 | One adapter; endpoint that processes data in the US; 3 to 7 calls per answered question |
| IF-05 | Funding agency pavement management system | Read by the API through an input adapter | Pending: read the agency's database, read through its system's API, or receive scheduled exports | UC-05 | ADR 4 | Read-only access limited to PCI data; credentials outside the code; traffic and processing in the US; coordination with the agency's IT |
| IF-06 | Cloud secret manager (provider not chosen) | Keys injected as settings when the application starts | Provider's own mechanism | None | ADR 7 | Deployment setup only; the code reads settings |
| IF-07 | File storage (S3-compatible object storage or network file volume) | The API stores, reads and deletes original files | Not specified | UC-05, UC-09 | C2; ADR 7 | Store per load; delete at the end of the retention period |
| IF-08 | Platform database (PostgreSQL with PostGIS, or Microsoft SQL Server) | The API reads and writes | SQL | UC-01 to UC-09 | C2; ADR 3 | Row-level security required; read-only role for answering |

### 5.2 Internal interfaces

| ID | Interface | Operations | Source |
|---|---|---|---|
| IF-09 | Web application to API application | JSON over HTTPS. [assumption] Operation groups derived from the use cases: project list and workspace; project overview, section series and timeline; loads (upload, column mapping, status, summary, rerun, agency run); corrections (correct, delete, accept a conflicting value, history); questions (ask, answer, download); access (grants, permissions, client setup). | C2; UC-01 to UC-09 |
| IF-10 | Module interfaces inside the API | Each module is used only through its interface. The access guard passes checked requests, with client, project and permissions, to the other modules; every module writes to the audit log; loading and corrections trigger the gold refresh; the retention job asks the audit module to delete expired answer log entries. | ADR 7; C3 |
| IF-11 | Language model interface | Build a query plan; judge a plan; reword a template text. One adapter per model option, chosen in configuration. | ADR 5; ADR 6 |
| IF-12 | Input adapter interface | From a source to rows in one internal format (client, project, section, coordinates, PCI, year), using the saved column mapping. CSV, Excel and the agency connection now; PDFs later. | ADR 4; ADR 7 |
| IF-13 | Query plan format | A structured request of filters and operations (FR-36), validated by the API and turned into a parameterized query. | ADR 6 |
| IF-14 | Answer templates | One per operation, filled from the query results and the validated plan, carrying the statements UC-01 to UC-04 require. | ADR 6 |

### 5.3 Data formats in and out

- In: CSV and Excel (.xlsx) files; agency data in a format that depends on the connection method (U-02).
- Out: downloadable answer tables. The format is not stated in the sources [assumption: CSV or Excel].

## 6. Components

### 6.1 Components to develop

| ID | Component | Where | Responsibility | Requirements | Depends on |
|---|---|---|---|---|---|
| | **Web application** | | | | |
| C-01 | Web shell and sign-in | Web | Sign-in redirect and session (OpenID Connect), navigation, actions shown per permission | FR-01, FR-03, FR-05 | IF-01, IF-09 |
| C-02 | Project list and workspace | Web | Granted projects; workspace following the demo's display | FR-04, FR-11 | C-10 |
| C-03 | Project overview and section view | Web | Overview table; PCI chart by survey year with gaps; survey timeline | FR-12 to FR-14 | C-11, R-09 |
| C-04 | Question and answer screens | Web | Question box, threshold prompt, answer text, interpretation, source rows, download, "cannot answer yet" | FR-32 to FR-35, FR-40 | C-19 to C-22, R-09 |
| C-05 | Loading screens | Web | Upload, column mapping, progress, load summary, conflicts, rerun, agency connection run | FR-16, FR-17, FR-19 to FR-22, FR-25 | C-12 to C-15 |
| C-06 | Correction screens | Web | Correct, delete with a reason, accept a conflicting value, [assumption] change history | FR-27 to FR-31 | C-17 |
| C-07 | Access management and client setup screens | Web | Grants and permissions per project; client and first client manager setup | FR-07, FR-08 | C-09 |
| | **API application** | | | | |
| C-08 | Access guard | Access module | Token check, user and client resolution, project permissions, client set for row-level security, deny by default, denied requests to the audit log | FR-02, FR-03, FR-06, TR-03 | IF-01, C-24, C-25 |
| C-09 | Access management | Access module | Grants and removals, permissions, client setup, no-project sign-in rule | FR-03, FR-07 to FR-10 | C-24, C-25 |
| C-10 | Projects | Projects module | Project list and workspace data, granted projects only | FR-04, FR-11 | C-25 |
| C-11 | Project and section views | Views module | Overview, PCI series and survey timeline read from gold | FR-12 to FR-15 | C-25 |
| C-12 | Load jobs | Loading module | Retryable background jobs in the same process, tracked in a job table; reruns do not duplicate rows | FR-22, FR-23 | C-13 to C-15 |
| C-13 | File input adapters and column mapping | Loading module | CSV and Excel readers; saved column mapping per client; original file to file storage; raw rows to bronze | FR-16 to FR-18, FR-23 | IF-07, IF-12, C-25 |
| C-14 | Agency connection adapter | Loading module | Reads PCI records from the funding agency's system (method pending) into bronze | FR-25 | IF-05, IF-12, C-25 |
| C-15 | Validation and load summary | Loading module | UC-05 checks from bronze to silver, conflicts with both values, rejected rows with reasons, summary to the audit log | FR-19 to FR-21, FR-24 | C-18, C-24, C-25 |
| C-16 | Retention job | Loading module | Scheduled deletion of expired original files; asks the audit module to delete expired answer log entries | FR-43 | IF-07, C-24 |
| C-17 | Corrections | PCI data module | New versions in silver with who, when and why; deletions hidden but kept; conflict resolution | FR-27 to FR-29, FR-31 | C-18, C-24, C-25 |
| C-18 | Gold refresh | PCI data module | Rebuilds the client's gold tables from silver in the same transaction as each load or correction | FR-30 | C-25 |
| C-19 | Query planner | Question answering module | Plan from the model, validation, up to three plans with the judge's reasons, "cannot answer yet" | FR-32, FR-34, FR-36, FR-37, FR-40 | C-20, C-23, C-24 |
| C-20 | Judge | Question answering module | Model verdict on each validated plan, before the query runs | FR-37 | C-23 |
| C-21 | Query builder | Question answering module | Parameterized read-only query on gold for every filter and operation, including distance from a point; row and time limits | FR-36, FR-38, TR-05 | C-08, C-25 |
| C-22 | Answer writer | Question answering module | Six answer templates with the required statements; reword request; check of numbers, survey years and section identifiers in order | FR-33, FR-35, FR-39 | C-23, C-24 |
| C-23 | Language model interface and first adapter | Question answering module | Three operations; model and endpoint in configuration; US endpoint | IF-11, TR-01 | IF-04 |
| C-24 | Audit log | Audit module | Audit records, answer log, deletion of expired answer log entries on request | FR-09, FR-41 to FR-43 | C-25 |
| | **Platform database** | | | | |
| C-25 | Database schemas and row-level security | Platform database | Platform tables (users, clients, projects, permissions, load jobs, audit log, [assumption] column mappings); bronze; silver with versions and conflicts; gold serving tables (latest PCI per section, PCI by survey year, project overview, network summaries); client identifier and row-level security on every client table; read-only role for answering | FR-20, FR-24, FR-26, FR-28, TR-03, TR-05 | R-02 |
| | **Quality and operations** | | | | |
| C-26 | Automated test suites | All | Permissions, PCI history and corrections, cross-client isolation, module boundaries | TR-03, TR-04, TR-08 | All API components |
| C-27 | Question test set and runner | Question answering | Test questions with expected plans, numbers and template texts; judge and reword statistics per run | TR-09 | C-19 to C-23 |
| C-28 | Backups and tested restore | Operations | Daily backups of the database and files to a separate US location; one tested restore | TR-07 | R-02, R-03 |
| C-29 | Hosting and delivery [assumption] | Operations | Cloud setup in a US region, deployment pipeline, environments, logs and monitoring. Not described in the architecture documents, but needed to deploy. | TR-01, TR-02, TR-06 | R-04 |
| | **Only if chosen** | | | | |
| C-30 | Self-hosted model hosting | Operations | Running an open-weight model in the US. Needed only if a self-hosted model is chosen. | TR-01 | IF-04 |
| C-31 | Self-hosted identity server | Operations | Running an open-source identity server as a new container. Fallback only if no hosted service keeps user data in the US at a price that fits the budget. | FR-01, FR-02 | IF-01 |

### 6.2 Reused from outside (configure or use, not build)

| ID | Component | Candidates named in the sources | Used by | Source |
|---|---|---|---|---|
| R-01 | Hosted identity service: OpenID Connect, MFA, single sign-on, Google sign-in | Not chosen; ADR 2 names Auth0 as an example | C-01, C-08 | ADR 2 |
| R-02 | Database engine with row-level security | PostgreSQL with PostGIS, or Microsoft SQL Server | C-25, C-21, C-28 | C2; ADR 3 |
| R-03 | File storage | S3-compatible object storage, or network file volume | C-13, C-16, C-28 | C2 |
| R-04 | Cloud secret manager | Not chosen | C-29 | ADR 7 |
| R-05 | Web framework | React or Vue (TypeScript) | C-01 to C-07 | C2 |
| R-06 | API framework | Python with FastAPI, or TypeScript with NestJS | C-08 to C-24 | C2 |
| R-07 | Language model | Hosted model API, or self-hosted open-weight model | C-23 | C2; ADR 5 |
| R-08 | [assumption] Standard libraries the sources do not name: OpenID Connect client and token checks, CSV and Excel parsing, database migrations, in-process job scheduling | Not chosen | C-01, C-08, C-12, C-13, C-16, C-25 | This document |
| R-09 | [assumption] Web chart and data table components (section view chart; tables with download) | Not chosen | C-03, C-04, C-05 | This document |

### 6.3 Built once, reused inside the platform

| Component | Reused by | Source |
|---|---|---|
| Access guard (C-08) | Every request and every module | C3 view 1 |
| Audit log interface (C-24) | Access management, loading, corrections, question answering, retention job | C3 |
| Gold refresh (C-18) | Every load and every correction | ADR 7 |
| Input adapter boundary and one validation path (C-13 to C-15) | CSV, Excel and the agency connection now; PDFs and other client systems later | ADR 4; ADR 7 |
| Background job runner (C-12) | Load jobs and the retention job, in the same process | ADR 7 |
| Language model interface (C-23) | Query planner, judge, answer writer; a second model is a new adapter | ADR 5; ADR 6 |
| Query plan blocks and answer templates (C-19, C-21, C-22) | All of UC-01 to UC-04; a new question type is a new block and template | ADR 6 |
| Row-level security pattern: client identifier plus policy (C-25) | Every client table in every schema | ADR 3 |
| [assumption] Data table with download (web) | Answers, project overview, load summary | This document |

### 6.4 Activities that are not components

Work the sources state that an estimate should include:

| ID | Activity | Unknowns | Source |
|---|---|---|---|
| A-01 | Choosing the identity service: US data location, MFA and single sign-on support, price | U-03 | ADR 2 |
| A-02 | Writing the pending ADRs: hosted or self-hosted model, database technology, agency connection method, cloud secret manager | U-01, U-02, U-04, U-06 | ADR 3; ADR 4; ADR 5; ADR 7 |
| A-03 | Single sign-on setup with the IT department of each client that requires it, and confirming per client that its identity provider enforces MFA | U-03 | ADR 2 |
| A-04 | Two-step verification in Continuum's Google Workspace for staff who use the platform | None | ADR 2 |
| A-05 | Coordination with the funding agency's IT for the connection | U-02 | ADR 4 |
| A-06 | Mapping each client's column names to section, coordinates, PCI and year | U-09 | Quality attributes (interoperability) |
| A-07 | Writing and checking the question test set with a pavement engineer | None | ADR 5; ADR 6 |
| A-08 | Interface design and testing with users | U-16 | Quality attributes (usability) |
| A-09 | The backup restore test | U-14 | Quality attributes (recoverability) |

## 7. Technical complexity

### 7.1 Rating scales

Complexity:

- **Low:** a standard pattern, or configuration of a reused component; few rules.
- **Medium:** several business rules or states, security-critical code on a known pattern, or one integration with a known interface. Needs targeted automated tests.
- **High:** correctness-critical logic with many combinations, a language model in the loop, or an integration whose interface is not known yet. Needs a dedicated test set.

Uncertainty, how much a pending decision or a missing input can change the work:

- **Low:** decided in the sources.
- **Medium:** a choice between named candidates, or an input not known yet that changes details.
- **High:** the method or interface is not known.

### 7.2 Ratings by component

| ID | Component | Complexity | Main drivers | Uncertainty | Unknowns |
|---|---|---|---|---|---|
| C-01 | Web shell and sign-in | Medium | OpenID Connect redirect and session; three sign-in paths handled by the identity service; actions per permission | Medium | U-03, U-05 |
| C-02 | Project list and workspace | Low | Follows the demo's display | Medium | U-05, U-17 |
| C-03 | Project overview and section view | Medium | Chart with gaps not filled; survey timeline; history across projects | Medium | U-08 |
| C-04 | Question and answer screens | Medium | Interpretation in plain words, source rows, download, threshold prompt, "cannot answer yet" states | Medium | U-10, U-11, U-20 |
| C-05 | Loading screens | Medium | Column mapping, background progress, summary with conflicts and rejected rows, rerun | Medium | U-02, U-09 |
| C-06 | Correction screens | Medium | Reason capture, deletion of a load's rows, conflict acceptance, history | Medium | U-18 |
| C-07 | Access management and client setup screens | Medium | Four permissions per project; three manager scopes; client setup | Medium | U-10, U-19 |
| C-08 | Access guard | Medium | Security-critical; token checks; deny by default; client set for row-level security; denials logged | Low | U-03 |
| C-09 | Access management | Medium | Scope rules per role; no-project sign-in rule; grants and removals audited | Medium | U-19 |
| C-10 | Projects | Low | List and workspace data | Low | None |
| C-11 | Project and section views | Low | Reads gold | Low | U-08 |
| C-12 | Load jobs | Medium | Background jobs in the same process; job table; retry without duplicates | Medium | U-12 |
| C-13 | File input adapters and column mapping | Medium | Varied client files; saved mapping per client; mapping problems reported | Medium | U-07, U-09 |
| C-14 | Agency connection adapter | High | Interface not known; read-only access, credentials and US traffic; depends on the agency's IT | High | U-02, U-06 |
| C-15 | Validation and load summary | Medium | UC-05 rules; conflicts per section and survey year; reruns without duplicates | Medium | U-08, U-09 |
| C-16 | Retention job | Low | Scheduled deletion; each module deletes its own records | Low | U-13 |
| C-17 | Corrections | Medium | Versions in silver with who, when and why; hidden but kept; conflict resolution | Low | U-18 |
| C-18 | Gold refresh | Medium | Rebuild per client inside the load or correction transaction | Medium | U-04, U-12 |
| C-19 | Query planner | High | Model builds plans; plan format; validation rules; up to three plans with judge feedback | Medium | U-01, U-11 |
| C-20 | Judge | Medium | One model call per plan with a structured verdict and reason | Medium | U-01 |
| C-21 | Query builder | High | Every filter and operation combination, change between surveys, comparison of groups, distance from a point; parameters, read-only, row and time limits | Medium | U-04, U-07, U-11, U-15 |
| C-22 | Answer writer | Medium | Six templates with the required statements; check of numbers, years and section identifiers in order | Medium | U-01, U-09 |
| C-23 | Language model interface and first adapter | Low | Three operations; configuration; US endpoint | Medium | U-01 |
| C-24 | Audit log | Medium | Several record types; answer log entries hold client data; deletion at the end of retention | Low | U-13 |
| C-25 | Database schemas and row-level security | High | Three layers plus platform tables; versions and conflicts; client identifier and row-level security on every client table; read-only role; spatial data | Medium | U-04, U-07, U-08, U-09 |
| C-26 | Automated test suites | Medium | Permissions, history and corrections, cross-client isolation, module boundaries | Low | None |
| C-27 | Question test set and runner | Medium | Expected plans, numbers and template texts per question, checked by a pavement engineer; judge and reword statistics | Low | U-01 |
| C-28 | Backups and tested restore | Low | Daily backups of the database and files to a separate US location; one restore test | Medium | U-06, U-14 |
| C-29 | Hosting and delivery [assumption] | Medium | US region; portability; environments; pipeline; monitoring | High | U-06, U-14, U-16 |
| C-30 | Self-hosted model hosting (only if chosen) | High | Running a model in the US for 3 to 7 calls per answered question | High | U-01 |
| C-31 | Self-hosted identity server (fallback only) | Medium | Running and securing an identity server with MFA and single sign-on | Medium | U-03 |

### 7.3 Where the complexity concentrates

- **Question answering** (C-19 to C-23, C-27): a language model in the loop, 3 to 7 calls per answered question, plan validation and a check of the reworded text. Answer quality depends on the test set and the model chosen.
- **Data model** (C-15, C-17, C-18, C-25): three layers, versions with who, when and why, conflicts per section and survey year, reruns without duplicates, and gold rebuilt in the same transaction. How a section loaded through different projects maps to one network section is not decided (U-08).
- **Client isolation** (C-08, C-25, C-26): row-level security on every client table, filtering in the API, and isolation tests. Security-critical, but a known pattern.
- **Agency connection** (C-14): the highest uncertainty, because the method, the agency's system and its IT rules are not known.
- **Location search for UC-04** (C-21, C-25): distance from a point depends on the coordinate format and reference system (U-07).
- **Work that exists only if chosen:** a self-hosted model (C-30) or a self-hosted identity server (C-31).

## 8. Unknowns that change the estimate

| ID | Unknown | Affects | Source |
|---|---|---|---|
| U-01 | Hosted or self-hosted language model, and which model | C-19, C-20, C-22, C-23, C-27, C-30; cost per answered question | ADR 5; C2 |
| U-02 | Agency connection method (database, API or scheduled exports), what "automatic" means to the agency, its system and IT rules | C-05, C-14 | ADR 4 |
| U-03 | Which identity service (US data location, MFA, single sign-on, price); how many clients need single sign-on | C-01, C-08, C-31; IF-02 setup | ADR 2 |
| U-04 | Database technology: PostgreSQL with PostGIS, or Microsoft SQL Server | C-18, C-21, C-25 | C2; ADR 3 |
| U-05 | Web and API technology: React or Vue; FastAPI or NestJS | C-01 to C-24 | C2 |
| U-06 | Cloud provider and secret manager; whether the funding agency requires hosting on its own infrastructure | C-14, C-28, C-29 | ADR 7 |
| U-07 | Coordinate format (one point per section or line geometry) and coordinate reference system | C-13, C-21, C-25 | UC-04; use cases README |
| U-08 | How a section loaded through different projects is matched to the same network section | C-03, C-11, C-15, C-25 | UC-05; UC-06 |
| U-09 | Structure of each client's files; formats beyond CSV and Excel; fields beyond the four (network or district ID, branch use or functional class, area or length); section identifier formats | C-05, C-13, C-15, C-22, C-25 | UC-05; use cases README |
| U-10 | PCI threshold source: per-client setting, stated by the user, or both | C-04, C-07, C-19 | UC-01; UC-03 |
| U-11 | Whether UC-01 to UC-04 answer within the selected project or across all projects the user can access | C-04, C-19, C-21 | Use cases README; ADR 6 |
| U-12 | Size of each client's initial load | C-12, C-18 | ADR 7 |
| U-13 | Retention periods for original files and answer logs; records retention rules | C-16, C-24 | ADR 6; ADR 7; quality attributes |
| U-14 | Recovery targets (data loss, downtime) and response time targets | C-28, C-29; performance work in C-18 and C-21 | Quality attributes |
| U-15 | Row limit and query time limit for answers | C-21 | ADR 6 |
| U-16 | Client legal requirements, for example FedRAMP authorization for federal clients, and accessibility required in a solicitation | C-29; all web components | Quality attributes |
| U-17 | Whether the demo's code can be reused; the `demo/` folder in this repository is empty | C-02, C-03 | README; repository |
| U-18 | Who can see the change history; whether a deleted record can be restored | C-06, C-17 | UC-09 |
| U-19 | Whether a project lead can grant the Manage access permission; whether access expires | C-07, C-09 | UC-08 |
| U-20 | Distance units for UC-04: US customary, metric or both | C-04, C-21 | Quality attributes |
| U-21 | Dashboards beyond the project overview and section view: not confirmed | Scope | README; use cases README |
| U-22 | PDF documents are out of the MVP (CLAUDE.md). If they enter the scope, they use file storage and a new input adapter. | Scope; C-13, R-03 | CLAUDE.md; ADR 7 |

## 9. Traceability

| Use case | Requirements | Functionalities | Components |
|---|---|---|---|
| UC-01 Identify M&R candidate sections | FR-32 to FR-34, FR-36 to FR-40 | F-18 to F-22 | C-04, C-19 to C-23, C-25 |
| UC-02 Track PCI over time | FR-32, FR-33, FR-35 to FR-40 | F-18 to F-20, F-22 | C-04, C-19 to C-23, C-25 |
| UC-03 Summarize network condition | FR-32 to FR-40 | F-18 to F-22 | C-04, C-19 to C-23, C-25 |
| UC-04 Find sections by location | FR-32, FR-33, FR-35 to FR-40 | F-18 to F-20, F-22 | C-04, C-19 to C-23, C-25 |
| UC-05 Load PCI data | FR-16 to FR-26, FR-29 | F-09 to F-13, F-16 | C-05, C-12 to C-16, C-18, C-24, C-25 |
| UC-06 View PCI data in a project | FR-11 to FR-15 | F-06 to F-08 | C-02, C-03, C-10, C-11, C-18, C-25 |
| UC-07 Sign in and open accessible projects | FR-01 to FR-06 | F-01 to F-03 | C-01, C-02, C-08, C-09, C-10 |
| UC-08 Manage project access | FR-07 to FR-10 | F-04, F-05 | C-07, C-09, C-24 |
| UC-09 Correct or delete PCI data | FR-27 to FR-31 | F-14 to F-17 | C-06, C-17, C-18, C-24 |
| Cross-cutting | FR-41 to FR-43, TR-01 to TR-12 | F-23 to F-25 | C-24 to C-31 |
