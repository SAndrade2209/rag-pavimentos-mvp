# Estimation workbook source

Builds the estimation workbook from the tables in `docs/estimates/2026-11-23-estimation-inputs.md`. Every row and every proposed value in the workbook comes from a table in the Markdown, so the two files keep the same IDs, wording and reasons.

| Workbook | Built with |
|---|---|
| `2026-11-24-estimation-workbook.xlsx` | The scripts in this folder: requirements and components, plus the estimation method of section 10 (Use Case Points, Wideband Delphi with PERT, COCOMO II schedule, cost by role). Effort in hours. |
| `2026-11-23-estimation-work-list.xlsx` | An earlier version of `build_worklist.py`, without the method sheets. Kept as it was. |

## Contents

| Path | Contents |
|---|---|
| `build_worklist.py` | Reads the Markdown and writes the workbook: Read me, Summary, Method, Use case points, Delphi, Work list, Schedule, Roles and cost, Requirements, Functionalities, Interfaces, Reuse, Unknowns, Traceability. |
| `inject_cached.py` | Writes the result of each formula into the file, so previews (for example, Finder) show values. Excel recalculates when it opens the file either way. |
| `verify_worklist.py` | Evaluates every formula with pycel, then fills test inputs on a copy and compares Use Case Points, PERT totals, schedule and cost with the same arithmetic in Python. |
| `requirements.txt` | Python packages. |

## Rebuild

Rebuild only before inputs are entered. The build makes a new workbook from the Markdown; ratings, hours and rates typed into an existing workbook are not carried over. Both writing scripts refuse to overwrite an existing file.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build_worklist.py ../2026-11-23-estimation-inputs.md /path/to/scratch/workbook.xlsx
.venv/bin/python verify_worklist.py /path/to/scratch/workbook.xlsx /path/to/scratch/workbook-test.xlsx
.venv/bin/python inject_cached.py /path/to/scratch/workbook.xlsx ../YYYY-MM-DD-estimation-workbook.xlsx
```

`verify_worklist.py` exits with status 1 if any check fails.

## What the build expects in the Markdown

- Section headings numbered as they are now (2.1 to 2.6, 3, 4, 5.1 to 5.3, 6.1 to 6.4, 7.1, 7.2, 8, 9, 10.1 to 10.8).
- The counts checked at the start of the build: 43 FR, 12 TR, 25 F, 14 IF, 31 C, 9 R, 10 A, 22 U, 10 traceability rows, 11 actors, 9 use cases, 13 technical factors, 8 environmental factors, 5 scale factors. If the inputs change these counts, update the assertions in `build_worklist.py`.
- Every component and activity has exactly one role in section 10.5.
- Group rows in tables 4 and 6.1 written as an empty first cell and a bold label, for example `| | **Web application** | |`.
- Scale factor values in 10.7 written as `PREC values VL to XH` with six comma-separated numbers.
