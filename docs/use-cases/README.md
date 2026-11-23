# Use cases

This folder holds the main use cases of the MVP, business-oriented: what the user needs to resolve with the pavement data and what result they obtain, without implementation details.

Phase 1 data: PCI information only (section, coordinates, PCI, year), from airport or road networks. PCI data belong to the network and are kept for every survey year. A project is how data arrive and where they are shown.

| ID | Use case | Decision supported |
|---|---|---|
| [UC-01](uc-01-mr-candidates.md) | Identify M&R candidate sections | Select M&R candidates |
| [UC-02](uc-02-pci-over-time.md) | Track PCI over time | Time M&R; condition reporting |
| [UC-03](uc-03-network-condition-summary.md) | Summarize network condition | Budget and reporting |
| [UC-04](uc-04-sections-by-location.md) | Find sections by location | Plan inspections |
| [UC-05](uc-05-load-pci-data.md) | Load PCI data | Keeps PCI data current for UC-01 to UC-04 and UC-06 |
| [UC-06](uc-06-view-pci-in-project.md) | View PCI data in a project | Review current PCI and section history |

## Supporting use cases

These do not answer a pavement question, but the use cases above depend on them.

| ID | Use case | Purpose |
|---|---|---|
| [UC-07](uc-07-sign-in-and-open-projects.md) | Sign in and open accessible projects | Users see only the projects granted to them |
| [UC-08](uc-08-manage-project-access.md) | Manage project access | Grant and remove access and permissions per project |
| [UC-09](uc-09-correct-or-delete-pci-data.md) | Correct or delete PCI data | Fix data while keeping the old values |

## Permissions (per project)

Access is granted per project (UC-08). [assumption] Permission levels:

| Permission | Allows |
|---|---|
| View | Ask questions (UC-01 to UC-04); view project and section PCI (UC-06) |
| Load | Load PCI data (UC-05) |
| Correct and delete | Correct or delete PCI data (UC-09) |
| Manage access | Grant and remove access (UC-08) |

## Answer format (UC-01 to UC-04)
- Short text answer plus the source rows.
- Downloadable table.
- Stated assumptions: threshold, years and filters used.
- No charts. Charts appear only in the UC-06 section view.

## Open items
- PCI threshold source: per-client setting, stated by the user, or both.
- Fields beyond section, coordinates, PCI and year (network or district ID, branch use or functional class, area or length).
- Coordinate format (point or line geometry) and coordinate reference system.
- Data formats beyond CSV and Excel, and the structure of each client's files (UC-05).
- Whether UC-01 to UC-04 answer within the selected project or across all projects the user can access.
- Which hosted identity service is used for sign-in (UC-07).
- How a section loaded through different projects is matched to the same network section (UC-05).
- Dashboards beyond the UC-06 project overview and section view: not confirmed.
