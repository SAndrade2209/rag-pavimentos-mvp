# Architecture report source

Source of `docs/architecture/2026-11-23-architecture-report.pdf`: use cases, quality attributes, C4 diagrams (C1 to C3) and ADRs, in reading order, for presenting the architecture.

## Contents

| Path | Contents |
|---|---|
| `parts/` | One HTML file per section. The build joins them in file name order, which is the page order. |
| `style.css` | Page layout (US Letter, landscape pages for diagrams), footer text, colors that match `../c4/styled/style.puml`. |
| `build.py` | Builds the PDF with Chrome headless. |
| `contact_sheets.py` | Optional. Renders several pages per PNG to check the layout. |
| `requirements.txt` | Python packages. |

The diagrams are not copied here. The parts load the committed renders in `../c4/styled/*.svg`. If a styled `.puml` file changes, render it again with PlantUML before building.

## Requirements

- Google Chrome. Set `CHROME` to its executable if it is not in `/Applications`.
- Python 3.9 or later.

## Build

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build.py ../YYYY-MM-DD-architecture-report.pdf
```

The build runs Chrome twice. The first pass finds the page of each heading from the PDF bookmarks, and the second fills those page numbers into the contents page. It stops if a heading is missing from the bookmarks, or if page numbers move between the passes.

It does not overwrite an existing PDF. Save each new edition as a new dated copy; `--force` replaces a file only when that is intended.

## Editing notes

- Headings with `data-toc="1"` or `data-toc="2"` appear on the contents page. `data-part` on a heading starts a part label there.
- For a new edition, update the date on the cover (`parts/00-cover.html`) and in the footer (`style.css`).
- Keep headings on one line. Chrome drops the space at a line break in a heading when it writes the bookmark.
- Keep the line height of `h1` and `h2` at 1.3 or more. With a tighter line height, Chrome writes doubled bookmark text for headings at the top of a page.
- ADR numbers 1 to 7 exist only in the report: they follow the reading order in `parts/08-adr-overview.html`. The repository identifies ADRs by file name.
- The report leaves out open questions and review material. Pending decisions still appear as "pending" or "candidates", so the report does not present them as decided.
