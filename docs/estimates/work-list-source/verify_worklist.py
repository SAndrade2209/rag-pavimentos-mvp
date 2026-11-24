"""Check every formula of a freshly built work list with pycel, blank and with test inputs.
Usage: .venv/bin/python verify_worklist.py WORKBOOK.xlsx SCRATCH_COPY.xlsx
Row numbers in the checks assume the layout build_worklist.py writes today.
"""
import shutil, sys
from collections import Counter
from openpyxl import load_workbook
from pycel import ExcelCompiler

SRC = sys.argv[1]
wb = load_workbook(SRC)
wl = wb['Work list']
rows = [[wl.cell(row=r, column=c).value for c in range(1, 20)] for r in range(5, 45)]

def ev(xl, sheet, cell):
    return xl.evaluate(f'{sheet}!{cell}')

# every formula cell in the workbook evaluates without an error
xl = ExcelCompiler(filename=SRC)
errors, n = [], 0
for ws in wb.worksheets:
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith('='):
                n += 1
                v = ev(xl, ws.title, c.coordinate)
                if isinstance(v, str) and v.startswith('#'):
                    errors.append((ws.title, c.coordinate, v))
print(f'formulas evaluated: {n}; errors: {errors}')

# blank inputs: expected empty, totals 0, missing = base rows
print('Q5 blank ->', repr(ev(xl, 'Work list', 'Q5')))
print('totals base/chosen ->', [ev(xl, 'Work list', f'{c}47') for c in 'NOPQ'], [ev(xl, 'Work list', f'{c}48') for c in 'NOPQ'])
base_rows = sum(1 for r in rows if r[12] == 'Base')
print('missing ->', ev(xl, 'Work list', 'Q49'), '| python base rows:', base_rows)
print('unit line ->', ev(xl, 'Work list', 'C50'))
print('Read me example expected ->', ev(xl, 'Read me', 'E18'), '(python', (2 + 4 * 3 + 7) / 6, ')')

# Summary matrix vs python counts
cnt = Counter((r[8], r[10]) for r in rows if r[1] == 'Component' and r[12] == 'Base')
sm = wb['Summary']
ok = True
for rr in range(6, 9):
    lvl = sm[f'A{rr}'].value
    for col, unc in zip('BCD', ['Low', 'Medium', 'High']):
        got = ev(xl, 'Summary', f'{col}{rr}')
        exp = cnt[(lvl, unc)]
        if got != exp:
            ok = False; print('MISMATCH', lvl, unc, got, exp)
print('summary matrix matches python counts:', ok, '| total', ev(xl, 'Summary', 'E9'), '| python', sum(cnt.values()))
areas = Counter((r[3], r[12]) for r in rows)
for rr in range(sm.max_row + 1):
    a = sm[f'A{rr}'].value if rr else None
    if a in {k[0] for k in areas}:
        got = (ev(xl, 'Summary', f'B{rr}'), ev(xl, 'Summary', f'C{rr}'))
        exp = (areas[(a, 'Base')], areas[(a, 'Only if chosen')])
        print(f'  area {a!r}: {got} expected {exp}', '' if got == exp else '  <-- MISMATCH')

# with test inputs on a copy
tst = sys.argv[2]
shutil.copy(SRC, tst)
wb2 = load_workbook(tst)
w = wb2['Work list']
test = {5: (1, 2, 4), 6: (2, 3, 7), 34: (10, 12, 20), 35: (5, 6, 9), 36: (1, 1, None)}  # row 34 C-30, 35 C-31 conditional; 36 incomplete
for r, vals in test.items():
    for col, v in zip('NOP', vals):
        w[f'{col}{r}'] = v
wb2['Unknowns']['E5'] = 'Hosted, US region'
wb2['Read me']['B14'] = 'person-days'
wb2.save(tst)
x2 = ExcelCompiler(filename=tst)
pert = lambda l, m, h: (l + 4 * m + h) / 6
print('Q5 ->', ev(x2, 'Work list', 'Q5'), 'python', pert(1, 2, 4))
print('Q36 incomplete ->', repr(ev(x2, 'Work list', 'Q36')))
scopes = {r: w[f'M{r}'].value for r in test}
print('scopes of test rows:', scopes, '| IDs', {r: w[f'A{r}'].value for r in test})
exp_base = sum(pert(*v) for r, v in test.items() if None not in v and scopes[r] == 'Base')
exp_ch = sum(pert(*v) for r, v in test.items() if None not in v and scopes[r] == 'Only if chosen')
print('Q47 base expected ->', ev(x2, 'Work list', 'Q47'), 'python', exp_base)
print('N47 base low ->', ev(x2, 'Work list', 'N47'), 'python', sum(v[0] for r, v in test.items() if scopes[r] == 'Base'))
print('Q48 chosen expected ->', ev(x2, 'Work list', 'Q48'), 'python', exp_ch)
print('missing ->', ev(x2, 'Work list', 'Q49'), 'python', base_rows - sum(1 for r, v in test.items() if None not in v and scopes[r] == 'Base'))
print('Summary links ->', [ev(x2, 'Summary', f'{c}{r}') for r in (25, 26) for c in 'BCDE'])
print('Summary unit, unknowns answered ->', ev(x2, 'Summary', 'B27'), ev(x2, 'Summary', 'B31'))
print('unit line ->', ev(x2, 'Work list', 'C50'))
