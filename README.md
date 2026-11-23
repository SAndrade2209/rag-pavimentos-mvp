# rag-pavimentos-mvp

## Objective

MVP of a pavement data platform. Users ask natural-language questions about tabular pavement data, answered with retrieval-augmented generation (RAG), and view the data in project and section views. The data include the fields:

- Section
- Coordinates
- PCI (Pavement Condition Index)
- Year

## Scope

### In the MVP

- Question answering over the tabular pavement data (section, coordinates, PCI, year). Answers are text and tables, without charts.
- Project display as in the demo: project list and project workspace.
- Project data overview: current PCI by section.
- Section view: PCI by survey year, with years without a survey marked as gaps, and the survey timeline.
- PCI data belong to the airport or road network, not to the project. A project is how data arrive and where they are shown. Every survey year is kept for future analysis, evidence and later surveys.
- Other dashboards: not confirmed.
- Sign-in, access by project, and access management. Loading, correcting, deleting and granting access depend on the user's permissions on each project.
- Corrections and deletions keep the old values, with who, when and why.

### Out of the MVP

- PDF documents and PDF extraction.
- Public pavement data sources.
- Network map. Sections are reached from a project, not from the map.
- Specifications.
- Workbench (mix design, material characterization, pavement life prediction and construction acceptance tools).

PDFs and other file types come later. Loading PCI data must allow adding them without rework.

## Repository structure

| Folder | Contents |
|---|---|
| `docs/use-cases/` | The main use cases of the MVP, business-oriented. |
| `docs/architecture/` | Architecture documentation. `quality-attributes.md` holds the prioritized quality attributes. |
| `docs/architecture/c4/` | C4 model diagrams as code (PlantUML with the C4-PlantUML library): C1 context, C2 containers and C3 components. |
| `docs/architecture/adr/` | Architecture decision records (ADRs). `0000-template.md` is the template; each ADR is named `YYYY-MM-DD-short-title.md`. |
| `docs/estimates/` | MVP estimates (effort, schedule and cost). |
| `demo/` | Code and material for the MVP demonstration. |
