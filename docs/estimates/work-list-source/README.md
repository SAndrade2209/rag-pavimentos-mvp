# Estimation work list source

Builds `docs/estimates/2026-11-23-estimation-work-list.xlsx` from the tables in `docs/estimates/2026-11-23-estimation-inputs.md`. Every row of the workbook comes from a table in the Markdown, so the two files keep the same IDs and wording.

## Contents

| Path | Contents |
|---|---|
| `build_worklist.py` | Reads the Markdown tables and writes the workbook: Read me, Summary, Work list, Requirements, Functionalities, Interfaces, Reuse, Unknowns, Traceability. |
| `inject_cached.py` | Optional. Writes the result of each formula into the file, so previews (for example, Finder) show real counts. Excel recalculates when it opens the file either way. |
| `verify_worklist.py` | Optional. Evaluates every formula with pycel, blank and with test inputs on a copy, and compares the results with Python. |
| `requirements.txt` | Python packages. |

## Rebuild

Rebuild only before effort figures are entered. The build makes a new workbook from the Markdown; estimates typed into an existing workbook are not carried over. Both scripts refuse to overwrite an existing file.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build_worklist.py ../YYYY-MM-DD-estimation-inputs.md /path/to/scratch/work-list.xlsx
.venv/bin/python verify_worklist.py /path/to/scratch/work-list.xlsx /path/to/scratch/work-list-test.xlsx
.venv/bin/python inject_cached.py /path/to/scratch/work-list.xlsx ../YYYY-MM-DD-estimation-work-list.xlsx
```

`verify_worklist.py` checks fixed rows (Work list rows 5 to 44, totals in rows 47 to 49). If the Markdown gains or loses components or activities, update those row numbers before relying on it.

## What the build expects in the Markdown

- Section headings numbered as they are now (2.1 to 2.6, 3, 4, 5.1 to 5.3, 6.1 to 6.4, 7.1, 7.2, 8, 9).
- The counts checked at the start of the build: 43 FR, 12 TR, 25 F, 14 IF, 31 C, 9 R, 9 A, 22 U, 10 traceability rows. If the inputs change these counts, update the assertions in `build_worklist.py`.
- Group rows in tables 4 and 6.1 written as an empty first cell and a bold label, for example `| | **Web application** | |`.
