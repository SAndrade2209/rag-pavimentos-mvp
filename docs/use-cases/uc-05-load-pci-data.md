# UC-05 Load PCI data

## Actor
- Primary: pavement management engineer; airport pavement management staff; client data administrator (a separate client role; the role name is a placeholder).
- Secondary: Continuum consultant, loading data on the client's behalf.
- Each of these users needs the Load permission on the project (see the permissions table in README.md). Continuum consultants get project access like any other user (UC-08).

## Goal
Load a client's PCI data so that UC-01 to UC-04 can answer from it and UC-06 can show it, and add new survey years as they become available.

## Example request
- "Load the 2025 PCI survey for this airport from this CSV file."
- "Load the latest PCI records from our pavement management database."

This use case is a load, not a question, so it gives example requests. The year (2025) is an example.

## Data required
- Section
- Coordinates
- PCI
- Year
- The client the data belong to (CLAUDE.md requires data isolated by client).

## Sources
- CSV and Excel (.xlsx) files, uploaded through the web application.
- For the funding agency only: an automatic connection to its existing pavement management system. The connection method is not decided yet (ADR 2026-11-23-load-pci-data-by-upload-and-connection).
- Other formats: not known yet.

## Expected result
- New survey years are added. Existing survey years are kept.
- A section and year that already exist in the MVP are reported to the loader and not overwritten.
- A load summary: rows added, duplicates by section and year, and rejected rows with the reason for each.
- [assumption] A row is rejected if section, PCI or year is missing, or if PCI is outside the 0 to 100 scale.
- Data loaded for one client are visible only to that client's users.
- Each load comes in through a project. The PCI records are stored for the airport or road network and kept for every survey year. Nothing is deleted when the project ends.
- Corrections and deletions of loaded data go through UC-09.

## Open items
- Formats beyond CSV and Excel, and the structure of each client's files.
- How the automatic connection for the funding agency works: the platform reads its database, reads through its system's API, or receives scheduled exports. To be decided in an ADR.
- How column names in each client's files map to section, coordinates, PCI and year.
- How a repeated section and year is resolved after it is reported.
- PDFs and other file types are out of phase 1. CLAUDE.md requires that loading can be extended to them later.
- How a section loaded through different projects is matched to the same network section. Example from the demo: the same airfield sections carry PCI from the airport's pavement management program and from a later consultant survey.
