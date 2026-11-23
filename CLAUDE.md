# RAG application MVP for pavement data

## Context
- Proposal for a government agency that may fund development.
- MVP goal: a pavement data platform. Answer natural-language questions
  about tabular pavement data (section, coordinates, PCI, year) and show
  the data in project and section views.
- Out of MVP scope: PDFs, map, specifications, network view, public data
  sources, workbench. PDFs and other file types come later, so ingestion
  must be extensible.
- The project display from the demo (project list and project workspace)
  stays in the MVP.
- PCI data belong to the network and are kept for every survey year. A
  project is how data arrive and where they are shown.
- Answers to questions have no charts. Charts appear only in the section
  view.
- Access is granted per project. Loading, correcting, deleting and granting
  access depend on the user's permissions. Corrected or deleted PCI data are
  kept with who, when and why.

## Design constraints
- Priority: an MVP that deploys fast. Prefer a modular monolith over
  microservices unless explicitly justified.
- Do not size for millions of users or multi-zone high availability.
  Response times must be reasonable.
- Must be portable across cloud providers and support multiple clients
  with isolated data.
- Quality attributes: see docs/architecture/quality-attributes.md.
  Do not optimize attributes outside that list.

## Documentation
- C4 model (levels C1 to C3) in PlantUML, in docs/architecture/c4/.
- Each architecture decision goes in an ADR in docs/architecture/adr/,
  named YYYY-MM-DD-title.md, stating which attribute it gains and which
  it sacrifices.

## Working rules
- Write in English. Plain, short, direct prose. Do not use em dashes.
- Use pavement engineering terminology, not plain-language or ML-only labels.
- Do not invent figures, costs, or vendors. Mark assumptions as [assumption].
- If information is missing, ask me before deciding.
- Before multi-file changes, propose a plan and wait for confirmation.
