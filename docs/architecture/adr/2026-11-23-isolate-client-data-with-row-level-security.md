# Isolate client data in shared tables with row-level security

- Date: 2026-11-23
- Status: Accepted

## Context

- CLAUDE.md: the platform supports multiple clients with isolated data. Clients are agencies and airports with government data.
- Isolation has two levels:
  - Between clients: one client never sees another client's data. This ADR covers this level.
  - Between projects of the same client: access is granted per project (UC-07, UC-08). The API application checks these permissions; that is not decided here.
- Client data in the platform database: PCI records per network section and survey year, projects, users, permissions and change history (UC-05, UC-09).
- Constraint (CLAUDE.md): data and backups stay in the US.
- Expected clients: 1 to 3 in the first year or two. A client requiring its own database is possible but not likely. Continuum may want to analyze data across clients later, with permission.
- Quality attributes involved (quality-attributes.md): security (high), deployability and simplicity (high), recoverability (high), performance (medium).

Options considered:

1. **Shared tables with a client identifier; the API application filters every query.** Simplest. A single query that forgets the filter exposes another client's data.
2. **Shared tables with a client identifier, plus row-level security in the database.** The database itself returns only the rows of the client making the request, even if the code forgets the filter.
3. **One schema per client** in a single database. Stronger separation. Every change to the data model has to be applied to each client's schema.
4. **One database per client.** The strongest separation, and one client's data can be restored or removed on its own. Every client adds a database to deploy, update, back up and monitor.

## Decision

Option 2.

With 1 to 3 clients, option 4 would be manageable. It still multiplies data model updates and backups, sends each request to a different database, and turns any later cross-client analysis into a data-copying project. Because a client needing its own database is possible but not likely, option 2 with a path to move that client out costs less.

- Every table that holds client data has a client identifier.
- The database enforces row-level security on those tables: each request sees only the rows of its client. The API application also filters by client, so there are two layers.
- Per-project permissions (UC-08) are checked by the API application, inside the client's data.
- Automated tests check that a user of one client cannot read or change another client's data.
- The database technology chosen for C2 must support row-level security. Both candidates (PostgreSQL, Microsoft SQL Server) do.
- A client that requires its own database, for example by contract, is moved to one through a new ADR. The client identifier makes its data straightforward to extract.

## Attributes gained

- **Security (high):** a missing filter in the code does not expose another client's data, because the database enforces the separation as well.
- **Deployability and simplicity (high):** one database to deploy, update and monitor, whatever the number of clients.
- **Recoverability (high):** one backup process covers all clients.

## Attributes sacrificed

- **Recoverability (high), partly:** restoring one client's data on its own is harder than with a database per client. It requires restoring a copy and extracting that client's rows. UC-09 reduces the need, since data mistakes are corrected without a restore.
- **Deployability and simplicity, slightly:** row-level security policies have to be written and tested for each client table, compared with option 1.
- **Performance (medium), slightly:** the database applies the policy on every query. The cost is expected to be small with the client identifier indexed.

## Consequences

- C2: the platform database description changes from "client data isolated" to "shared tables with row-level security".
- The database technology ADR must keep row-level security support as a requirement.
- All clients share one database in the US. A client that needs its data elsewhere needs a separate database (new ADR).
- Cross-client isolation tests belong to the minimum automated test set (maintainability).
- Row-level security blocks cross-client queries by default. If Continuum adds cross-client analysis later, it is a separate, explicitly permitted function, decided in a new ADR.
- Open item: whether any client's contract requires a separate database.
