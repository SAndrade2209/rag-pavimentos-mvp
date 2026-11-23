# Load PCI data by file upload and by an automatic connection

- Date: 2026-11-23
- Status: Accepted

## Context

- UC-05: PCI data (section, coordinates, PCI, year) come from files and from the client's existing pavement management databases. Each load comes in through a project and is validated: new survey years are added, an existing section and year is reported, not overwritten, and rejected rows are listed with the reason.
- The funding agency expects the platform to connect automatically to its existing pavement management system. File upload alone would not meet that expectation.
- New PCI data are loaded yearly or less often per client.
- Continuum staff and client staff both load data.
- Clients keep PCI data in spreadsheets as well as in databases. Upload accepts CSV and Excel.
- Expected clients: 1 to 3 in the first year or two (ADR 2026-11-23-isolate-client-data-with-row-level-security).
- PDFs and other file types come later; loading must be extensible (CLAUDE.md).
- Not known yet: which system the funding agency uses, whether it offers an export or an API, the agency's IT rules for connections, and what "automatic" means to the agency.
- Quality attributes involved (quality-attributes.md): security (high), deployability and simplicity (high), data traceability (high), interoperability (medium), extensibility (medium), usability (medium).

Options considered:

1. **File upload only.** Simplest and safest, but it does not meet the funding agency's expectation.
2. **Automatic connection only.** Leaves out the clients and staff who work from files and spreadsheets.
3. **File upload for every client, plus an automatic connection for the funding agency's system.**
4. **Import API for clients.** Clients write their own software to send data. Requires development work at each client.

## Decision

Option 3.

- **Upload:** CSV and Excel (.xlsx) files, through the web application, by users with the Load permission on the project (UC-05, UC-08).
- **Automatic connection:** built for the funding agency's system only. Another client's system is added only when that client requires it.
- **One validation path:** the loading module converts every source into one internal format (client, project, section, coordinates, PCI, year) and applies the UC-05 validation to it. Each source is an input adapter: CSV, Excel and the agency's system now; PDFs later.
- **Column mapping:** each client's column names are mapped to section, coordinates, PCI and year once and saved, so later loads reuse the mapping.
- **When it runs:** because new data arrive yearly or less often, the connection runs when a user with the Load permission starts it. A schedule is added only if the agency requires one.
- **How it connects** (the platform reads the agency's database, reads through the system's API, or the agency's system sends scheduled exports to the platform) is decided in a separate ADR, once the agency's system and IT rules are known.
- **Minimum for any connection method:** read-only access limited to PCI data, credentials kept outside the code, and traffic and processing inside the US.

## Attributes gained

- **Interoperability (medium):** meets the funding agency's expectation of an automatic connection, and files cover every other client.
- **Data traceability (high):** every load, by file or by connection, is recorded with who started it, when, and from which source.
- **Extensibility (medium):** the input adapter boundary is where other client systems and PDFs plug in later.
- **Usability (medium):** Excel files are accepted without conversion, and the agency's data arrive without manual export.

## Attributes sacrificed

- **Deployability and simplicity (high):** one connector to build, test and maintain; coordination with the agency's IT; and it can break when the agency changes its system.
- **Security (high), partly:** the platform holds access to one client system, which has to be protected. Upload, by contrast, needs no access to client systems.

## Consequences

- C1 and C2: the client pavement management system stays in the diagrams. The dashed relationship is relabeled "automatic connection for the funding agency; method pending (ADR)". Its direction is set by the connection method ADR.
- UC-05: sources become CSV and Excel uploads, plus the automatic connection for the funding agency.
- C3: the loading module has an input adapter boundary and one shared validation step.
- [assumption] For connection loads, a copy of the records received is kept, as uploaded files are, so each load can be traced to what arrived.
- Open items: what "automatic" means to the funding agency (a scheduled export may be enough); which system it uses and whether it offers an export or an API; its IT rules for connections.
