# Quality attributes

Status: priorities confirmed on 2026-11-23.

Terms follow the architecture characteristics in the course material based on Richards and Ford (2025). That method keeps the list short and picks the few that matter most.

- **High:** drives architecture decisions. Every ADR states how it affects these. At most 4.
- **Medium:** met through simple, standard choices, without dedicated design effort.
- **Nice to have:** only if it costs almost nothing, or a client requires it.

## Constraints

Pass or fail. Not ranked and not traded against other attributes.

- Data, backups and language model processing stay in the US (MVP). Other regions are out of the MVP.
- The platform runs on any major cloud provider (CLAUDE.md: "must be portable across cloud providers").

## Ranked attributes

| Attribute | Priority (high/medium/nice to have) | Rationale |
|---|---|---|
| Security (authentication, authorization, client data isolation) | High | UC-07: users see only the projects granted to them, and a user without access cannot sign in. UC-08: permissions are set per project. UC-09: only users with the Correct and delete permission change data. Several clients with government data share the platform, so one client must never see another's data. Cost: every query and screen checks permissions, and there is more to test. |
| Data traceability (archivability and audit trail) | High | UC-05: new survey years are added, and an existing section and year is reported, not overwritten. UC-06: the section view shows every survey year on the network, including years loaded through other projects. UC-09: corrected and deleted values are kept with who, when and why. UC-02 and UC-03 depend on that full history. Cost: more storage and a more involved data model than overwriting values. |
| Deployability and simplicity | High | CLAUDE.md: "an MVP that deploys fast". Not tied to one use case: it decides how quickly UC-01 to UC-09 reach users. Favors few containers (modular monolith) and well-known technologies. Cost: some parts may need rework if the platform grows well beyond the MVP. |
| Recoverability | High | The network history built through UC-05 and UC-09 exists only in the platform: clients cannot rebuild the corrections, their reasons, or the history merged across projects from their own files. UC-02, UC-03 and UC-06 depend on it. Minimum: automatic daily backups of the database and files, kept in a separate US location, with a restore tested. Cost: low at this level; stricter targets (see open questions) cost more. |
| Maintainability | Medium | The use cases will change after the first users: UC-01 to UC-04 still have open items (PCI threshold source, project or network scope). Met by clear modules and automated tests on the rules that matter most: permissions (UC-07, UC-08) and PCI history and corrections (UC-05, UC-09). Cost: time spent writing tests. |
| Extensibility (data loading and language model) | Medium | UC-05: CSV now, client database exports, PDFs later. UC-01 to UC-04: the language model must be switchable between hosted and self-hosted. A replaceable interface is built only at these two points, where a second option is already planned. Cost: a little more design in two modules. |
| Performance (response time) | Medium | UC-01 to UC-04 return answers that include a language model call; UC-06 opens the project overview and section view. CLAUDE.md: "response times must be reasonable". Target not defined yet. Cost of a strict target: caching and query tuning. |
| Usability | Medium | UC-06: project overview and section view, following the demo's display. UC-01 to UC-04: answers state the threshold, years and filters used, so engineers can check them. Users are pavement engineers and airport staff. Cost: interface design and testing with users. |
| Interoperability | Medium | UC-05: PCI data come from CSV files and from client pavement management systems (export file or direct connection). UC-01 to UC-04: tables are downloadable. Cost: mapping each client's column names to section, coordinates, PCI and year (open item in UC-05). |
| Localization (units) | Nice to have | UC-04 uses a search radius, so distance units matter; the demo has a units switch (US). International clients are out of the MVP. Cost: unit conversion in the location search and displays. |
| Accessibility | Nice to have | No use case requires it. Public agencies may require it in their solicitations; if a client does, it moves up. Cost: interface work and checks. |

## Not optimized

Decisions do not spend effort on these.

- Scalability to millions of users (CLAUDE.md).
- Multi-zone high availability (CLAUDE.md).
- On-demand elasticity.
- Privacy beyond standard security, such as hiding data even from administrators.

## Open questions

- Recovery targets: how much recently loaded data can be lost (for example, everything since the last daily backup), and how long the platform can be down.
- Client-specific legal requirements: for example, FedRAMP authorization for federal clients, and records retention rules.
- Response time target for answers (UC-01 to UC-04) and for the project and section views (UC-06).
- Whether a client's solicitation requires accessibility.
- Distance units for UC-04: US customary, metric, or both.
