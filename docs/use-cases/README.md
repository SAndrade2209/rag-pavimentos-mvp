# Use cases

This folder holds the main use cases of the MVP, business-oriented: what the user needs to resolve with the pavement data and what result they obtain, without implementation details.

Phase 1 data: PCI information only (section, coordinates, PCI, year), from airport or road networks.

| ID | Use case | Decision supported |
|---|---|---|
| [UC-01](uc-01-mr-candidates.md) | Identify M&R candidate sections | Select M&R candidates |
| [UC-02](uc-02-pci-over-time.md) | Track PCI over time | Time M&R; condition reporting |
| [UC-03](uc-03-network-condition-summary.md) | Summarize network condition | Budget and reporting |
| [UC-04](uc-04-sections-by-location.md) | Find sections by location | Plan inspections |
| [UC-05](uc-05-load-pci-data.md) | Load PCI data | Keeps PCI data current for UC-01 to UC-04 |

## Answer format (UC-01 to UC-04)
- Short text answer plus the source rows.
- Downloadable table.
- Stated assumptions: threshold, years and filters used.

## Open items
- PCI threshold source: per-client setting, stated by the user, or both.
- Fields beyond section, coordinates, PCI and year (network or district ID, branch use or functional class, area or length).
- Coordinate format (point or line geometry) and coordinate reference system.
- Data formats beyond CSV, and the structure of each client's database exports (UC-05).
