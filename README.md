# rag-pavimentos-mvp

## Objective

MVP of a RAG (retrieval-augmented generation) application that answers natural-language questions about tabular pavement data. The data include the fields:

- Section
- Coordinates
- PCI (Pavement Condition Index)
- Year

## Scope

### In the MVP

- Question answering over the tabular pavement data (section, coordinates, PCI, year).
- Project display as in the demo: project list and project workspace.
- [assumption] PCI data are kept per project.

### Out of the MVP

- PDF documents and PDF extraction.
- Public pavement data sources.
- Map and network view.
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
