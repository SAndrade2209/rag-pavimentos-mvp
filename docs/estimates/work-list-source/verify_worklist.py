"""Check a freshly built estimation workbook with pycel.

Usage: .venv/bin/python verify_worklist.py WORKBOOK.xlsx SCRATCH_COPY.xlsx
1. Every formula evaluates without an error value, with the input cells as built.
2. On a copy, test inputs are filled in (team factors, scale factors, Delphi hours, rates) and the
   results are compared with the same arithmetic done in Python.
Cells are found through the defined names and the column headers that build_worklist.py writes.
"""
import math
import shutil
import sys

from openpyxl import load_workbook
from pycel import ExcelCompiler

SRC, TST = sys.argv[1], sys.argv[2]
problems = []


def check(label, got, exp, tol=1e-6):
    ok = (got == exp) if not isinstance(exp, float) else (isinstance(got, (int, float)) and abs(got - exp) <= tol * max(1, abs(exp)))
    print(f'{"ok " if ok else "BAD"} {label}: {got!r} (expected {exp!r})')
    if not ok:
        problems.append(label)


def addr(wb, nm):
    sheet, cell = wb.defined_names[nm].attr_text.rsplit('!', 1)
    return sheet.strip("'"), cell.replace('$', '')


def ev(xl, sheet, cell):
    return xl.evaluate(f'{sheet}!{cell}')


def evn(xl, wb, nm):
    return ev(xl, *addr(wb, nm))


# 1. all formulas, as built
wb = load_workbook(SRC)
xl = ExcelCompiler(filename=SRC)
n, errors = 0, []
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith('='):
                n += 1
                v = ev(xl, ws.title, c.coordinate)
                if isinstance(v, str) and v.startswith('#'):
                    errors.append((ws.title, c.coordinate, v))
print(f'formulas evaluated: {n}; error values: {errors}')
if errors:
    problems.append('error values')
check('UCP hours blank until the team factors are rated', evn(xl, wb, 'UCP_HOURS'), '')

# 2. test inputs on a copy
shutil.copy(SRC, TST)
w = load_workbook(TST)
up, wl, sc, rc, de = w['Use case points'], w['Work list'], w['Schedule'], w['Roles and cost'], w['Delphi']


def rows_where(ws, col, pred, start=1):
    return [r for r in range(start, ws.max_row + 1) if pred(ws.cell(row=r, column=col).value)]


ecf_rows = rows_where(up, 1, lambda v: isinstance(v, str) and v[:2] in {f'E{i}' for i in range(1, 9)} and v[2] == ' ')
tcf_rows = rows_where(up, 1, lambda v: isinstance(v, str) and v.split(' ')[0] in {f'T{i}' for i in range(1, 14)})
assert len(ecf_rows) == 8 and len(tcf_rows) == 13
for r in ecf_rows:
    if up.cell(row=r, column=3).value is None:
        up.cell(row=r, column=3).value = 3
sf_rows = rows_where(sc, 1, lambda v: v in {'PREC', 'FLEX', 'RESL', 'TEAM', 'PMAT'})[:5]
for r in sf_rows:
    sc.cell(row=r, column=3).value = 'N'
wl_rows = rows_where(wl, 1, lambda v: isinstance(v, str) and v[:2] in ('C-', 'A-') and len(v) == 4)
base = [r for r in wl_rows if wl.cell(row=r, column=13).value == 'Base']
for r in base:
    wl.cell(row=r, column=15).value, wl.cell(row=r, column=16).value, wl.cell(row=r, column=17).value = 10, 20, 40
team = rows_where(rc, 2, lambda v: v in ('Hire', 'Continuum staff'))
cost_rows = rows_where(rc, 1, lambda v: isinstance(v, str) and v.startswith('=A'))
assert len(team) == len(cost_rows) == 7, (team, cost_rows)
for r in cost_rows:
    rc.cell(row=r, column=2).value = 100
months = {'Design': 2, 'Build': 8, 'Final': 2}
for i, m in enumerate(months.values()):
    rc.cell(row=6 + i, column=2).value = m
for r in team:
    if rc.cell(row=r, column=3).value is None:
        rc.cell(row=r, column=3).value = 0.2
    for col in (4, 5, 6):
        if rc.cell(row=r, column=col).value is None:
            rc.cell(row=r, column=col).value = 'Yes'
de_row = rows_where(de, 1, lambda v: v == 'C-01')[0]
de.cell(row=de_row, column=4).value, de.cell(row=de_row, column=5).value, de.cell(row=de_row, column=6).value = 10, 12, 30
w.save(TST)
x = ExcelCompiler(filename=TST)

# Python arithmetic from the same inputs
aw = {'Simple': 1, 'Average': 2, 'Complex': 3}
actor_rows = rows_where(up, 3, lambda v: v in aw)
uaw = sum(aw[up.cell(row=r, column=3).value] for r in actor_rows)
uc_rows = rows_where(up, 1, lambda v: isinstance(v, str) and v.startswith('UC-'))
uucw = sum(5 if c <= 3 else 10 if c <= 7 else 15 for c in (up.cell(row=r, column=3).value for r in uc_rows))
tf = sum(up.cell(row=r, column=3).value * up.cell(row=r, column=4).value for r in tcf_rows)
efr = [up.cell(row=r, column=3).value for r in ecf_rows]
ef = sum(v * up.cell(row=r, column=4).value for v, r in zip(efr, ecf_rows))
ucp = (uaw + uucw) * (0.6 + 0.01 * tf) * (1.4 - 0.03 * ef)
risk = sum(1 for v in efr[:6] if v < 3) + sum(1 for v in efr[6:] if v > 3)
pf = 20 if risk <= 2 else 28 if risk <= 4 else 36
hours = ucp * pf
print(f'python: UAW {uaw}, UUCW {uucw}, TFactor {tf}, EFactor {ef}, risk {risk}, PF {pf}')
check('use case points', evn(x, w, 'UCP_POINTS'), ucp)
check('hours per point', evn(x, w, 'UCP_PF'), pf)
check('UCP hours', evn(x, w, 'UCP_HOURS'), hours)
F = 0.28 + 0.2 * 0.01 * (3.72 + 3.04 + 4.24 + 3.29 + 4.68)
check('schedule exponent F (all nominal)', evn(x, w, 'SCHED_F'), F)
pm = hours / 152
check('UCP months', evn(x, w, 'TDEV_UCP'), 3.67 * pm ** F)
nb = len(base)
exp_total = nb * (10 + 4 * 20 + 40) / 6
sd = math.sqrt(nb * ((40 - 10) / 6) ** 2)
check('Delphi expected total', evn(x, w, 'BU_EXPECTED'), exp_total)
check('Delphi std dev', evn(x, w, 'BU_SD'), sd)
check('Delphi P80', evn(x, w, 'BU_P80'), exp_total + 0.84 * sd)
check('Delphi months', evn(x, w, 'TDEV_BU'), 3.67 * (exp_total / 152) ** F)
check('cost, Delphi', evn(x, w, 'COST_BU'), exp_total * 100)
check('cost, UCP', evn(x, w, 'COST_UCP'), hours * 100)
row_hours = (10 + 4 * 20 + 40) / 6
cap_total, over, plan_cost = 0.0, 0, 0.0
for r in team:
    role = rc.cell(row=r, column=1).value
    alloc = rc.cell(row=r, column=3).value
    ph_months = sum(m for col, m in zip((4, 5, 6), months.values()) if rc.cell(row=r, column=col).value == 'Yes')
    cap = alloc * ph_months * 152
    hrs = row_hours * sum(1 for rr in base if wl.cell(row=rr, column=14).value == role)
    cap_total += cap
    plan_cost += cap * 100
    over += 1 if hrs / cap > 1 else 0
    check(f'capacity, {role}', ev(x, 'Roles and cost', f'L{r}'), cap)
    check(f'months needed, {role}', ev(x, 'Roles and cost', f'N{r}'), hrs / (alloc * 152) if hrs else '')
check('total capacity hours', evn(x, w, 'CAPACITY_HOURS'), cap_total)
check('cost of planned allocation', evn(x, w, 'COST_PLAN'), plan_cost)
check('plan months', evn(x, w, 'PLAN_MONTHS'), float(sum(months.values())))
check('roles above capacity', ev(x, 'Roles and cost', f'M{team[-1] + 1}'), over)
r1 = ev(x, 'Delphi', f'I{de_row}'), ev(x, 'Delphi', f'J{de_row}')
check('Delphi ratio and flag for 10, 12, 30 hours', r1, (3.0, 'Discuss'))
print('summary rows:')
sm = w['Summary']
for r in range(5, 14):
    print('  ', [sm.cell(row=r, column=1).value] + [ev(x, 'Summary', f'{c}{r}') for c in 'BCDEF'])
print('RESULT:', 'all checks passed' if not problems else f'problems: {problems}')
sys.exit(1 if problems else 0)
