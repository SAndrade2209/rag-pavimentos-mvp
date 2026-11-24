"""Build the estimation workbook (.xlsx) from the estimation inputs Markdown.

Usage: .venv/bin/python build_worklist.py INPUT.md OUTPUT.xlsx
Refuses to overwrite OUTPUT, so a workbook with estimates in it is never replaced.
Every row and every proposed value comes from a table in the Markdown, so the two files stay consistent.
Method (section 10 of the Markdown): Use Case Points, Wideband Delphi with PERT, COCOMO II schedule, cost by role.
"""
import math
import os
import re
import sys
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

MD_PATH, OUT_PATH = sys.argv[1], sys.argv[2]
if os.path.exists(OUT_PATH):
    sys.exit(f'{OUT_PATH} exists; choose a new file name')
md = open(MD_PATH, encoding='utf-8').read()
MD_NAME = os.path.basename(MD_PATH)

# ---------- Markdown parsing ----------

def clean(s):
    s = re.sub(r'`([^`]*)`', r'\1', s)
    return s.replace('**', '').strip()


def block(heading):
    """Text from a heading line to the next heading of the same or higher level."""
    lines = md.split('\n')
    level = len(heading) - len(heading.lstrip('#'))
    start = next(i for i, l in enumerate(lines) if l.startswith(heading))
    out = []
    for l in lines[start + 1:]:
        m = re.match(r'^(#+) ', l)
        if m and len(m.group(1)) <= level:
            break
        out.append(l)
    return '\n'.join(out)


def table(text):
    """First Markdown table in text: list of rows, header first."""
    rows = []
    for l in text.split('\n'):
        if l.startswith('|'):
            cells = [c for c in l.strip().strip('|').split('|')]
            if all(re.fullmatch(r'\s*-+\s*', c) for c in cells):
                continue
            rows.append([c.strip() for c in cells])
        elif rows:
            break
    return rows


def rows_of(heading):
    return [[clean(c) for c in r] for r in table(block(heading))[1:]]


def grouped(rows):
    """Yield (group, cleaned row) for data rows; group rows have an empty first cell."""
    group = None
    for r in rows[1:]:
        if r[0] == '' and r[1].startswith('**'):
            group = clean(r[1])
            continue
        yield group, [clean(c) for c in r]


def bullets(text):
    return [clean(l[2:]) for l in text.split('\n') if l.startswith('- ')]


ID_RE = re.compile(r'\b(FR|TR|IF|C|F|R|U|A)-(\d{2})(?: to (?:\1-)?(\d{2}))?')


def expand(text, prefix):
    ids = []
    for m in ID_RE.finditer(text):
        if m.group(1) != prefix:
            continue
        a, b = int(m.group(2)), m.group(3)
        ids += [f'{prefix}-{n:02d}' for n in range(a, (int(b) if b else a) + 1)]
    return ids


meta_date = re.search(r'^- Date: (.+)$', md, re.M).group(1)
meta_upd = re.search(r'^- Updated: (.+)$', md, re.M)
meta_basis = clean(re.search(r'^- Basis: (.+)$', md, re.M).group(1))

prefixes = rows_of('## Purpose')
fr_rows = []
for h in ['### 2.1', '### 2.2', '### 2.3', '### 2.4', '### 2.5', '### 2.6']:
    head = next(l for l in md.split('\n') if l.startswith(h))
    area = re.sub(r'^### \d\.\d ', '', head)
    fr_rows += [['Functional', area] + r for r in rows_of(h)]
tr_rows = [['Technical', 'Drives effort'] + r for r in rows_of('## 3.')]
f_rows = [[g] + r for g, r in grouped(table(block('## 4.')))]
if_ext = rows_of('### 5.1')
if_int = rows_of('### 5.2')
formats = bullets(block('### 5.3'))
c_rows = [[g] + r for g, r in grouped(table(block('### 6.1')))]
r_rows = rows_of('### 6.2')
reuse_in = rows_of('### 6.3')
a_rows = rows_of('### 6.4')
scales = block('### 7.1')
ratings = {r[0]: r for r in rows_of('### 7.2')}
u_rows = rows_of('## 8.')
t_rows = rows_of('## 9.')
actors = rows_of('### 10.1')
uc_tx = rows_of('### 10.2')
tcf_rows = rows_of('### 10.3')
ecf_rows = rows_of('### 10.4')
role_rows = rows_of('### 10.5')
sf_rows = rows_of('### 10.6')
const_rows = {r[0]: r for r in rows_of('### 10.7')}
references = bullets(block('### 10.8'))

assert len(c_rows) == 31 and len(ratings) == 31 and len(a_rows) == 11, (len(c_rows), len(ratings), len(a_rows))
assert len(fr_rows) == 43 and len(tr_rows) == 12 and len(f_rows) == 25 and len(u_rows) == 22
assert len(if_ext) + len(if_int) == 14 and len(r_rows) == 9 and len(t_rows) == 10
assert len(actors) == 11 and len(uc_tx) == 9 and len(tcf_rows) == 13 and len(ecf_rows) == 8 and len(sf_rows) == 5

role_of, ROLES, TEAM = {}, [], {}
PHASES = ['Design', 'Build', 'Final']
for role, engagement, alloc, phases, ids, why in role_rows:
    ROLES.append(role)
    TEAM[role] = {
        'engagement': engagement,
        'alloc': None if alloc.lower().startswith('to set') else float(alloc.rstrip('%')) / 100,
        'phases': None if phases.lower().startswith('to set') else [p_.strip() for p_ in phases.split(',')],
        'work': why,
    }
    assert TEAM[role]['phases'] is None or set(TEAM[role]['phases']) <= set(PHASES), phases
    for i in expand(ids, 'C') + expand(ids, 'A'):
        assert i not in role_of, f'{i} has two roles'
        role_of[i] = role
all_ids = [r[1] for r in c_rows] + [r[0] for r in a_rows]
assert sorted(role_of) == sorted(all_ids), set(all_ids) ^ set(role_of)

uc_name = {r[0].split(' ', 1)[0]: r[0] for r in t_rows if r[0].startswith('UC-')}
LEVELS = ['VL', 'L', 'N', 'H', 'VH', 'XH']
sf_values = {}
for f, *_ in sf_rows:
    vals = const_rows[f'{f} values VL to XH'][1]
    sf_values[f] = [float(x) for x in vals.split(',')]
    assert len(sf_values[f]) == 6

comp_for = defaultdict(list)
for g, cid, name, where, resp, reqs, deps in c_rows:
    for rid in expand(reqs, 'FR') + expand(reqs, 'TR'):
        comp_for[rid].append(cid)

# ---------- styles and helpers ----------

ARIAL = 'Arial'
F_BASE = Font(name=ARIAL, size=10)
F_BOLD = Font(name=ARIAL, size=10, bold=True)
F_TITLE = Font(name=ARIAL, size=14, bold=True, color='0F172A')
F_SUB = Font(name=ARIAL, size=10, color='475569')
F_HEAD = Font(name=ARIAL, size=10, bold=True, color='FFFFFF')
F_INPUT = Font(name=ARIAL, size=10, color='0000FF')
F_LINK = Font(name=ARIAL, size=10, color='008000')
F_LINK_B = Font(name=ARIAL, size=10, bold=True, color='008000')
F_RESULT = Font(name=ARIAL, size=10, bold=True)
FILL_HEAD = PatternFill('solid', fgColor='1E40AF')
FILL_INPUT = PatternFill('solid', fgColor='FFF2CC')
FILL_TOTAL = PatternFill('solid', fgColor='F1F5F9')
FILL_SECTION = PatternFill('solid', fgColor='DBEAFE')
FILL_RESULT = PatternFill('solid', fgColor='DCFCE7')
THIN = Side(style='thin', color='CBD5E1')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical='top')
CENTER = Alignment(horizontal='center', vertical='top', wrap_text=True)
LEVEL_FILLS = {'High': 'FDE2E1', 'Medium': 'FEF3C7', 'Low': 'DCFCE7'}
H = '#,##0'          # hours
H1 = '#,##0.0'
MONEY = '#,##0'

wb = Workbook()
wb.calculation.fullCalcOnLoad = True


def put(ws, row, col, value, font=F_BASE, fill=None, align=WRAP, border=True, fmt=None):
    c = ws.cell(row=row, column=col, value=value)
    c.font = font
    c.alignment = align
    if fill:
        c.fill = fill
    if border:
        c.border = BORDER
    if fmt:
        c.number_format = fmt
    return c


def header(ws, row, names, start=1):
    for i, n in enumerate(names, start):
        if n is not None:
            put(ws, row, i, n, font=F_HEAD, fill=FILL_HEAD, align=CENTER)


def section(ws, row, text, ncols):
    put(ws, row, 1, text, font=F_BOLD, fill=FILL_SECTION)
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)


def note(ws, row, text, ncols, font=F_SUB):
    put(ws, row, 1, text, font=font, border=False)
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=ncols)
    total = sum(ws.column_dimensions[get_column_letter(i)].width or 9 for i in range(1, ncols + 1))
    ws.row_dimensions[row].height = 13 * max(1, math.ceil(len(text) / (total * 1.1))) + 3


def widths(ws, ws_widths):
    for i, w in enumerate(ws_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def fit_rows(ws, first, last, ws_widths, line_pt=12.75, min_lines=1):
    """Set row heights from the longest wrapped cell (Excel does not autofit on open)."""
    for r in range(first, last + 1):
        lines = min_lines
        for i, w in enumerate(ws_widths, 1):
            v = ws.cell(row=r, column=i).value
            if v is None or (isinstance(v, str) and v.startswith('=')):
                continue
            chars = max(1, int(w * 1.15))
            n = sum(max(1, math.ceil(len(part) / chars)) for part in str(v).split('\n'))
            lines = max(lines, n)
        ws.row_dimensions[r].height = line_pt * lines + 4


def title(ws, text, sub):
    put(ws, 1, 1, text, font=F_TITLE, align=Alignment(vertical='top'), border=False)
    put(ws, 2, 1, sub, font=F_SUB, align=Alignment(vertical='top', wrap_text=True), border=False)
    ws.row_dimensions[1].height = 22
    ncols = max(1, len([k for k in ws.column_dimensions if ws.column_dimensions[k].width]))
    total = sum(ws.column_dimensions[get_column_letter(i)].width or 9 for i in range(1, ncols + 1))
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncols)
    ws.row_dimensions[2].height = 13 * max(1, math.ceil(len(sub) / (total * 1.15))) + 3


def level_rules(ws, rng):
    for level, color in LEVEL_FILLS.items():
        ws.conditional_formatting.add(
            rng, CellIsRule(operator='equal', formula=[f'"{level}"'], fill=PatternFill('solid', fgColor=color)))


def ref(ws, row, col, absolute=True):
    L = get_column_letter(col)
    a = f'${L}${row}' if absolute else f'{L}{row}'
    return f"'{ws.title}'!{a}"


def name(nm, ws, row, col):
    wb.defined_names[nm] = DefinedName(nm, attr_text=ref(ws, row, col))


def blank_if_zero(x):
    return f'IF({x}="","",IF({x}=0,"",{x}))'


SRC = f'Built from docs/estimates/{MD_NAME} ({meta_basis}).'

# ---------- Read me ----------

rm = wb.active
rm.title = 'Read me'
widths(rm, [30, 22, 16, 16, 16, 22])
upd = f' Updated: {meta_upd.group(1)}.' if meta_upd else ''
title(rm, 'Estimation workbook: pavement data platform MVP', f'Date: {meta_date}.{upd} ' + SRC)
r = 4
section(rm, r, 'Purpose', 6)
r += 1
note(rm, r, 'Estimates effort, schedule, team and cost for the MVP with published methods: Use Case Points (top-down), '
     'Wideband Delphi with PERT (bottom-up), the COCOMO II schedule equation, and cost by role. Effort is in hours '
     "everywhere. 'Method' gives the steps and the sources.", 6, font=F_BASE)
r += 2
section(rm, r, 'Order of work', 6)
steps = [
    "1. 'Use case points': check the blue counts and ratings (each has its reason), and rate E1 to E8 for your team.",
    "2. 'Delphi': each estimator enters hours for every row without seeing the others. Discuss the rows marked Discuss, "
    "estimate again in round 2, then type the agreed low, most likely and high hours in 'Work list'.",
    "3. 'Work list': check the proposed complexity, uncertainty and primary role of each row.",
    "4. 'Schedule': rate the five COCOMO II scale factors (nominal when unsure).",
    "5. 'Roles and cost': enter the months of each phase (design, build, final), check each role's allocation and phases, "
    "and enter an hourly rate per role.",
    "6. 'Summary': effort, months, average team size and cost from both methods, and the inputs still missing. "
    "Record answers to open questions in 'Unknowns'.",
]
for s in steps:
    r += 1
    note(rm, r, s, 6, font=F_BASE)
r += 2
section(rm, r, "Example of a 'Work list' row (format only, not an estimate)", 6)
r += 1
for i, h in enumerate(['Item', 'Low (h)', 'Most likely (h)', 'High (h)', 'Expected (h)', 'Estimated by'], 1):
    put(rm, r, i, h, font=F_HEAD, fill=FILL_HEAD, align=CENTER)
r += 1
put(rm, r, 1, 'Example item')
for col, v in [(2, 8), (3, 12), (4, 20)]:
    put(rm, r, col, v, font=F_INPUT, fill=FILL_INPUT, fmt=H)
put(rm, r, 5, f'=IF(COUNT(B{r}:D{r})=3,(B{r}+4*C{r}+D{r})/6,"")', fmt=H1)
put(rm, r, 6, 'Delphi team', font=F_INPUT, fill=FILL_INPUT)
r += 2
section(rm, r, 'Legend', 6)
for nm_, meaning, fill, font in [
    ('Yellow cell, blue text', 'A cell for you to fill in.', FILL_INPUT, F_INPUT),
    ('Blue text', 'A proposed value from the inputs document, with its reason. Edit if you disagree.', None, F_INPUT),
    ('Black text', 'Text or a published constant from the inputs document, or a formula.', None, F_BASE),
    ('Green text', 'A link to a cell on another sheet.', None, F_LINK),
    ('Green fill', 'A result.', FILL_RESULT, F_RESULT),
]:
    r += 1
    put(rm, r, 1, nm_, font=font, fill=fill)
    put(rm, r, 2, meaning); rm.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
r += 2
section(rm, r, 'Complexity and uncertainty scales (section 7.1 of the inputs document)', 6)
comp_txt, unc_txt = scales.split('Uncertainty', 1)
for kind, txt in [('Complexity', comp_txt), ('Uncertainty', unc_txt)]:
    for b in bullets(txt):
        level, desc = b.split(':', 1)
        desc = desc.strip()
        r += 1
        put(rm, r, 1, f'{kind}: {level}', font=F_BOLD)
        put(rm, r, 2, desc[:1].upper() + desc[1:]); rm.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        rm.row_dimensions[r].height = 13 * max(1, math.ceil(len(desc) / 105)) + 3
r += 2
section(rm, r, 'ID prefixes', 6)
sheet_of = {'FR': 'Requirements', 'TR': 'Requirements', 'F': 'Functionalities', 'IF': 'Interfaces',
            'C': 'Work list', 'R': 'Reuse', 'A': 'Work list', 'U': 'Unknowns'}
for p, meaning, _ in prefixes:
    r += 1
    put(rm, r, 1, p, font=F_BOLD)
    put(rm, r, 2, meaning); rm.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    put(rm, r, 5, f'Sheet: {sheet_of[p]}'); rm.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6)

# ---------- Method ----------

me = wb.create_sheet('Method')
widths(me, [6, 30, 92])
title(me, 'Method', 'How the estimate is made, and its limits (section 10 of the inputs document).')
r = 4
section(me, r, 'Steps', 3)
method = [
    ('1', 'Size and effort, top-down', "Use Case Points (Karner 1993). Count actors and the transactions of each use case, rate 13 "
     "technical and 8 environmental factors. Hours per point (20 or 28) follow the rule of Schneider and Winters (2001). "
     "Sheet: 'Use case points'."),
    ('2', 'Effort, bottom-up', "Wideband Delphi (Boehm 1981). Two or three estimators give hours for each row independently, "
     "discuss the rows where they differ most, and estimate again. The agreed low, most likely and high hours go in "
     "'Work list', where PERT gives the expected value and the spread (Malcolm et al. 1959). Sheets: 'Delphi', 'Work list'."),
    ('3', 'Schedule and team size', "COCOMO II schedule equation (Boehm et al. 2000), applied to the effort of steps 1 and 2. "
     "Gives calendar months and an average team size. Sheet: 'Schedule'."),
    ('4', 'Who is needed, capacity and cost', "Each row has a primary role from the team plan (section 10.5). Hours per role "
     "come from the Delphi estimates; the Use Case Points hours are split with the same shares. Each role's capacity is its "
     "allocation times the months of its phases times 152 hours; a role above 100% of its capacity needs more time or help. "
     "Cost is shown two ways: estimated hours times the rate, and the planned allocation times the rate (what the hires "
     "cost for the time they are booked). Sheet: 'Roles and cost'."),
    ('5', 'Compare', "'Summary' puts both methods side by side. A large gap between them means a count, a rating or an "
     "estimate needs another look before the figures are used."),
]
r += 1
header(me, r, ['Step', 'What', 'How'])
for n_, what, how in method:
    r += 1
    put(me, r, 1, n_, font=F_BOLD, align=CENTER); put(me, r, 2, what, font=F_BOLD); put(me, r, 3, how)
    me.row_dimensions[r].height = 13 * max(1, math.ceil(len(how) / 100)) + 4
r += 2
section(me, r, 'Limits', 3)
limits = [
    'Use Case Points count only work an actor triggers. Background work (validation, gold refresh, retention, audit) is '
    'covered only through factors T4 and T11, which is why the Delphi cross-check matters.',
    'COCOMO II defines its schedule equation for effort estimated with COCOMO II. Applying it to Use Case Points or Delphi '
    'effort is a common shortcut [assumption].',
    'P80 and P90 assume the rows are independent and their total is roughly normal. Shared risks (for example the agency '
    'connection) make the real spread wider.',
    "Rows marked 'Only if chosen' (self-hosted model, self-hosted identity server) are left out of the totals.",
    'The published constants are taken from the cited books; their page numbers have not been checked [unverified].',
    'Average team size is an average over the schedule. Real staffing ramps up and down.',
]
for s in limits:
    r += 1
    put(me, r, 2, '- ' + s, border=False); me.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
    me.row_dimensions[r].height = 13 * max(1, math.ceil(len(s) / 115)) + 3
r += 2
section(me, r, 'References', 3)
for s in references:
    r += 1
    put(me, r, 2, s, border=False); me.merge_cells(start_row=r, start_column=2, end_row=r, end_column=3)
    me.row_dimensions[r].height = 13 * max(1, math.ceil(len(s) / 115)) + 3

# ---------- Use case points ----------

up = wb.create_sheet('Use case points')
UP_W = [36, 54, 11, 11, 11, 64]
widths(up, UP_W)
title(up, 'Use Case Points (Karner 1993)', 'Blue values are proposed from section 10 of the inputs document, each with its reason. '
      'Yellow cells are for you. The effort at the bottom fills in when every factor is rated.')
K = {}
r = 4
section(up, r, 'Constants (section 10.7)', 6)
consts = [
    ('aw_s', 'Actor weight: simple', 1), ('aw_a', 'Actor weight: average', 2), ('aw_c', 'Actor weight: complex', 3),
    ('uw_s', 'Use case weight: simple', 5), ('uw_a', 'Use case weight: average', 10), ('uw_c', 'Use case weight: complex', 15),
    ('lim_s', 'Simple use case: transactions up to', 3), ('lim_a', 'Average use case: transactions up to', 7),
    ('tcf_c', 'TCF constant', 0.6), ('tcf_m', 'TCF multiplier', 0.01),
    ('ecf_c', 'ECF constant', 1.4), ('ecf_m', 'ECF multiplier (subtracted)', 0.03),
    ('pf1', 'Hours per point when the risk count is low', 20), ('pf2', 'Hours per point when the risk count is medium', 28),
    ('pf3', 'Hours per point when the risk count is high [assumption]', 36),
    ('rk1', 'Risk count limit for the low value', 2), ('rk2', 'Risk count limit for the medium value', 4),
    ('hpm', 'Hours per person-month', 152),
]
src_of = {'pf1': 'Schneider and Winters 2001', 'pf2': 'Schneider and Winters 2001', 'pf3': 'This document',
          'rk1': 'Schneider and Winters 2001', 'rk2': 'Schneider and Winters 2001', 'hpm': 'Boehm et al. 2000'}
for key, label, val in consts:
    r += 1
    put(up, r, 1, label)
    put(up, r, 3, val, align=CENTER)
    put(up, r, 6, f"Source: {src_of.get(key, 'Karner 1993')}", font=F_SUB)
    K[key] = f'$C${r}'
HPM = f"'Use case points'!{K['hpm']}"

r += 2
section(up, r, '1. Actors (section 10.1)', 6)
r += 1
header(up, r, ['Actor', 'How it interacts', 'Class', None, 'Weight', 'Reason'])
dv_class = DataValidation(type='list', formula1='"Simple,Average,Complex"', allow_blank=True)
up.add_data_validation(dv_class)
a1 = r + 1
for actor, how, cls, why in actors:
    r += 1
    put(up, r, 1, actor); put(up, r, 2, how)
    put(up, r, 3, cls, font=F_INPUT, align=CENTER); dv_class.add(f'C{r}')
    put(up, r, 4, None)
    put(up, r, 5, f'=IF(C{r}="Simple",{K["aw_s"]},IF(C{r}="Average",{K["aw_a"]},IF(C{r}="Complex",{K["aw_c"]},"")))', align=CENTER)
    put(up, r, 6, why)
a2 = r
fit_rows(up, a1, a2, UP_W)
r += 1
put(up, r, 1, 'Unadjusted actor weight (UAW)', font=F_BOLD, fill=FILL_TOTAL)
put(up, r, 5, f'=SUM(E{a1}:E{a2})', font=F_BOLD, fill=FILL_TOTAL, align=CENTER)
UAW = f'E{r}'

r += 2
section(up, r, '2. Use cases (section 10.2)', 6)
r += 1
header(up, r, ['Use case', 'Transactions counted', 'Count', 'Class', 'Weight', 'Reason'])
dv_count = DataValidation(type='whole', operator='between', formula1='0', formula2='50', allow_blank=True)
up.add_data_validation(dv_count)
u1 = r + 1
for uc, tx, cnt, why in uc_tx:
    r += 1
    put(up, r, 1, uc_name.get(uc, uc)); put(up, r, 2, tx)
    put(up, r, 3, int(cnt), font=F_INPUT, align=CENTER); dv_count.add(f'C{r}')
    put(up, r, 4, f'=IF(C{r}="","",IF(C{r}<={K["lim_s"]},"Simple",IF(C{r}<={K["lim_a"]},"Average","Complex")))', align=CENTER)
    put(up, r, 5, f'=IF(D{r}="","",IF(D{r}="Simple",{K["uw_s"]},IF(D{r}="Average",{K["uw_a"]},{K["uw_c"]})))', align=CENTER)
    put(up, r, 6, why)
u2 = r
fit_rows(up, u1, u2, UP_W)
r += 1
put(up, r, 1, 'Unadjusted use case weight (UUCW)', font=F_BOLD, fill=FILL_TOTAL)
put(up, r, 5, f'=SUM(E{u1}:E{u2})', font=F_BOLD, fill=FILL_TOTAL, align=CENTER)
UUCW = f'E{r}'

dv_rate = DataValidation(type='whole', operator='between', formula1='0', formula2='5', allow_blank=True)
up.add_data_validation(dv_rate)


def factor_block(r, label, rows_):
    section(up, r, label, 6)
    r += 1
    header(up, r, ['Factor', 'Reason', 'Rating', 'Weight', 'Weighted', None])
    f1 = r + 1
    for fid, fname, w, rating, why in rows_:
        r += 1
        put(up, r, 1, f'{fid} {fname}')
        put(up, r, 2, why)
        if rating.lower().startswith('to rate'):
            put(up, r, 3, None, font=F_INPUT, fill=FILL_INPUT, align=CENTER)
        else:
            put(up, r, 3, float(rating) if '.' in rating else int(rating), font=F_INPUT, align=CENTER)
        dv_rate.add(f'C{r}')
        put(up, r, 4, float(w) if '.' in w else int(w), align=CENTER)
        put(up, r, 5, f'=IF(C{r}="","",C{r}*D{r})', align=CENTER, fmt='0.0')
    fit_rows(up, f1, r, UP_W)
    return r, f1, r


r += 2
r, t1, t2 = factor_block(r, '3. Technical factors (section 10.3): 0 irrelevant, 3 average, 5 essential', tcf_rows)
r += 1
put(up, r, 1, 'Technical factor (TFactor) and TCF', font=F_BOLD, fill=FILL_TOTAL)
put(up, r, 3, f'=SUM(E{t1}:E{t2})', font=F_BOLD, fill=FILL_TOTAL, align=CENTER, fmt='0.0')
put(up, r, 5, f'=IF(COUNT(C{t1}:C{t2})=13,{K["tcf_c"]}+{K["tcf_m"]}*C{r},"")', font=F_BOLD, fill=FILL_TOTAL, align=CENTER, fmt='0.000')
put(up, r, 6, 'TCF = 0.6 + 0.01 x TFactor, once all 13 factors are rated', font=F_SUB)
TCF = f'E{r}'

r += 2
r, e1, e2 = factor_block(r, '4. Environmental factors (section 10.4): 0 none, 3 average, 5 expert or strong. Rate for your team.', ecf_rows)
r += 1
put(up, r, 1, 'Environmental factor (EFactor) and ECF', font=F_BOLD, fill=FILL_TOTAL)
put(up, r, 3, f'=SUM(E{e1}:E{e2})', font=F_BOLD, fill=FILL_TOTAL, align=CENTER, fmt='0.0')
put(up, r, 5, f'=IF(COUNT(C{e1}:C{e2})=8,{K["ecf_c"]}-{K["ecf_m"]}*C{r},"")', font=F_BOLD, fill=FILL_TOTAL, align=CENTER, fmt='0.000')
put(up, r, 6, 'ECF = 1.4 - 0.03 x EFactor, once all 8 factors are rated', font=F_SUB)
ECF = f'E{r}'

r += 2
section(up, r, '5. Result', 6)
results = [
    ('Unadjusted use case points (UUCP = UAW + UUCW)', f'={UAW}+{UUCW}', '0'),
    ('Use case points (UCP = UUCP x TCF x ECF)', None, '0.0'),
    ('Risk count: E1 to E6 rated below 3, plus E7 and E8 rated above 3', None, '0'),
    ('Hours per use case point', None, '0'),
    ('Rule applied', None, None),
    ('Effort (hours)', None, H),
    ('Effort (person-months)', None, H1),
]
RES = {}
for i, (label, f, fmt) in enumerate(results):
    r += 1
    put(up, r, 1, label, font=F_BOLD)
    RES[i] = r
    put(up, r, 5, f, font=F_RESULT, fill=FILL_RESULT, align=CENTER, fmt=fmt)
    up.merge_cells(start_row=r, start_column=1, end_row=r, end_column=4)
up[f'E{RES[1]}'] = f'=IF(OR({TCF}="",{ECF}=""),"",E{RES[0]}*{TCF}*{ECF})'
up[f'E{RES[2]}'] = (f'=IF({ECF}="","",COUNTIF(C{e1}:C{e1 + 5},"<3")+COUNTIF(C{e1 + 6}:C{e2},">3"))')
up[f'E{RES[3]}'] = (f'=IF(E{RES[2]}="","",IF(E{RES[2]}<={K["rk1"]},{K["pf1"]},IF(E{RES[2]}<={K["rk2"]},{K["pf2"]},{K["pf3"]})))')
up[f'E{RES[4]}'] = (f'=IF(E{RES[2]}="","Rate E1 to E8 first",IF(E{RES[2]}>{K["rk2"]},'
                    f'"High risk: Schneider and Winters advise changing the project before estimating","Schneider and Winters rule"))')
up[f'E{RES[5]}'] = f'=IF(OR(E{RES[1]}="",E{RES[3]}=""),"",E{RES[1]}*E{RES[3]})'
up[f'E{RES[6]}'] = f'=IF(E{RES[5]}="","",E{RES[5]}/{K["hpm"]})'
up.merge_cells(start_row=RES[4], start_column=5, end_row=RES[4], end_column=6)
UCP_HOURS = f"'Use case points'!$E${RES[5]}"
name('UCP_POINTS', up, RES[1], 5)
name('UCP_HOURS', up, RES[5], 5)
name('UCP_PF', up, RES[3], 5)
ECF_RANGE = f"'Use case points'!$C${e1}:$C${e2}"
up.freeze_panes = 'A4'

# ---------- Work list ----------

wl = wb.create_sheet('Work list')
WL_COLS = ['ID', 'Type', 'Item', 'Area', 'Where', 'Description', 'Requirements', 'Depends on',
           'Complexity', 'Complexity drivers', 'Uncertainty', 'Unknowns', 'Scope', 'Primary role',
           'Low (h)', 'Most likely (h)', 'High (h)', 'Expected (h)', 'Std dev (h)', 'Estimated by', 'Notes', 'Variance (helper)']
WL_W = [7, 11, 28, 17, 17, 44, 20, 18, 11, 40, 11, 15, 12, 18, 9, 9, 9, 10, 9, 13, 26, 10]
widths(wl, WL_W)
title(wl, 'Work list', "One row per component (C) and activity (A). Type the hours agreed in 'Delphi' in the yellow cells. "
      'Expected = (low + 4 x most likely + high) / 6; std dev = (high - low) / 6 (PERT).')
HR = 4
header(wl, HR, WL_COLS)
row = HR + 1
first = row
RC_FIRST = 13                      # first role row on 'Roles and cost' (fixed layout below)
RC_LAST = RC_FIRST + len(ROLES) - 1
dv_role = DataValidation(type='list', formula1=f"='Roles and cost'!$A${RC_FIRST}:$A${RC_LAST}", allow_blank=True)
for g, cid, name_, where, resp, reqs, deps in c_rows:
    rt = ratings[cid]
    scope = 'Only if chosen' if g == 'Only if chosen' else 'Base'
    area = 'Operations' if g == 'Only if chosen' else g
    vals = [cid, 'Component', name_, area, where, resp, reqs, deps, rt[2], rt[3], rt[4], rt[5], scope, role_of[cid]]
    for i, v in enumerate(vals, 1):
        font = F_INPUT if i in (9, 11, 14) else (F_BOLD if i == 1 else F_BASE)
        put(wl, row, i, v, font=font, align=CENTER if i in (1, 2, 9, 11, 13) else WRAP)
    row += 1
for aid, act, unk, src in a_rows:
    vals = [aid, 'Activity', act, 'Activity', '', f'Source: {src}', '', '', None, '', None, unk, 'Base', role_of[aid]]
    for i, v in enumerate(vals, 1):
        font = F_INPUT if i in (9, 11, 14) else (F_BOLD if i == 1 else F_BASE)
        put(wl, row, i, v, font=font, align=CENTER if i in (1, 2, 9, 11, 13) else WRAP)
    row += 1
last = row - 1
for rr in range(first, last + 1):
    for col in (15, 16, 17, 20, 21):
        put(wl, rr, col, None, font=F_INPUT, fill=FILL_INPUT, fmt=H if col < 18 else None,
            align=CENTER if col < 18 else WRAP)
    put(wl, rr, 18, f'=IF(COUNT(O{rr}:Q{rr})=3,(O{rr}+4*P{rr}+Q{rr})/6,"")', fmt=H1, align=CENTER)
    put(wl, rr, 19, f'=IF(R{rr}="","",(Q{rr}-O{rr})/6)', fmt=H1, align=CENTER)
    put(wl, rr, 22, f'=IF(R{rr}="","",S{rr}^2)', fmt=H1, align=CENTER, font=F_SUB)
fit_rows(wl, first, last, WL_W)
dv_level = DataValidation(type='list', formula1='"Low,Medium,High"', allow_blank=True)
dv_scope = DataValidation(type='list', formula1='"Base,Only if chosen"', allow_blank=False)
dv_hours = DataValidation(type='decimal', operator='greaterThanOrEqual', formula1='0', allow_blank=True)
for dv in (dv_level, dv_scope, dv_role, dv_hours):
    wl.add_data_validation(dv)
dv_level.add(f'I{first}:I{last}'); dv_level.add(f'K{first}:K{last}')
dv_scope.add(f'M{first}:M{last}'); dv_role.add(f'N{first}:N{last}'); dv_hours.add(f'O{first}:Q{last}')
level_rules(wl, f'I{first}:I{last}'); level_rules(wl, f'K{first}:K{last}')
wl.auto_filter.ref = f'A{HR}:V{last}'
wl.freeze_panes = f'D{HR + 1}'

WLR = lambda col: f"'Work list'!${col}${first}:${col}${last}"
t = last + 2
put(wl, t, 3, 'Totals (hours)', font=F_BOLD, fill=FILL_TOTAL)
for col, h in zip(range(15, 20), ['Low', 'Most likely', 'High', 'Expected', 'Std dev']):
    put(wl, t, col, h, font=F_BOLD, fill=FILL_TOTAL, align=CENTER)
TOT = {}
for k, (label, crit) in enumerate([('Base scope', 'Base'), ('Only if chosen', 'Only if chosen')], 1):
    rr = t + k
    put(wl, rr, 3, label, font=F_BOLD)
    for col in range(15, 19):
        L = get_column_letter(col)
        put(wl, rr, col, f'=SUMIFS({L}${first}:{L}${last},$M${first}:$M${last},"{crit}")', fmt=H, align=CENTER)
    put(wl, rr, 19, f'=SQRT(SUMIFS($V${first}:$V${last},$M${first}:$M${last},"{crit}"))', fmt=H1, align=CENTER)
    TOT[crit] = rr
rb = TOT['Base']
rr = t + 3
put(wl, rr, 3, 'Base scope P80: expected + 0.84 std dev', font=F_BOLD)
put(wl, rr, 18, f'=IF(R{rb}=0,"",R{rb}+0.84*S{rb})', fmt=H, align=CENTER, font=F_RESULT, fill=FILL_RESULT)
TOT['P80'] = rr
rr += 1
put(wl, rr, 3, 'Base scope P90: expected + 1.28 std dev', font=F_BOLD)
put(wl, rr, 18, f'=IF(R{rb}=0,"",R{rb}+1.28*S{rb})', fmt=H, align=CENTER, font=F_RESULT, fill=FILL_RESULT)
TOT['P90'] = rr
rr += 1
put(wl, rr, 3, 'Base-scope rows without a complete estimate', font=F_BOLD)
put(wl, rr, 18, f'=SUMPRODUCT(($M${first}:$M${last}="Base")*($R${first}:$R${last}=""))', fmt='0', align=CENTER)
TOT['missing'] = rr
note(wl, rr + 1, 'P80 and P90 use the normal approximation and assume rows are independent (see Method, Limits). '
     'Only-if-chosen rows are excluded from the base totals.', 12)
name('BU_EXPECTED', wl, rb, 18)
name('BU_SD', wl, rb, 19)
name('BU_P80', wl, TOT['P80'], 18)
wl.page_setup.orientation = 'landscape'
wl.page_setup.fitToWidth = 1
wl.page_setup.fitToHeight = 0
wl.sheet_properties.pageSetUpPr.fitToPage = True
wl.print_title_rows = f'{HR}:{HR}'
BU_EXP = f"'Work list'!$R${rb}"
BU_P80 = f"'Work list'!$R${TOT['P80']}"
BU_P90 = f"'Work list'!$R${TOT['P90']}"

# ---------- Delphi ----------

de = wb.create_sheet('Delphi')
DE_W = [7, 34, 13, 10, 10, 10, 8, 8, 8, 10, 10, 10, 10, 8, 8, 8, 10]
widths(de, DE_W)
title(de, 'Wideband Delphi (Boehm 1981)', 'Each estimator types most likely hours for every row without seeing the others (separate '
      "copies of this file work). Discuss the rows marked Discuss, estimate again in round 2, then type the agreed low, "
      "most likely and high hours in 'Work list'.")
put(de, 4, 1, 'Mark a row Discuss when highest / lowest is above', font=F_BOLD)
de.merge_cells('A4:C4')
put(de, 4, 4, 1.5, font=F_INPUT, align=CENTER, fmt='0.00')
put(de, 4, 5, '[assumption] A team rule, not part of the published method. Change it if you agree another.', font=F_SUB, border=False)
de.merge_cells('E4:Q4')
THR = '$D$4'
put(de, 5, 1, 'Estimator names', font=F_BOLD); de.merge_cells('A5:C5')
for col in (4, 5, 6):
    put(de, 5, col, None, font=F_INPUT, fill=FILL_INPUT, align=CENTER)
for col, src in zip((11, 12, 13), ('D', 'E', 'F')):
    put(de, 5, col, f'=IF({src}5="","",{src}5)', font=F_LINK, align=CENTER)
put(de, 6, 4, 'Round 1: most likely hours, independent', font=F_BOLD, fill=FILL_SECTION, align=CENTER); de.merge_cells('D6:J6')
put(de, 6, 11, 'Round 2: after discussion', font=F_BOLD, fill=FILL_SECTION, align=CENTER); de.merge_cells('K6:Q6')
header(de, 7, ['ID', 'Item', 'Scope', 'Estimator A', 'Estimator B', 'Estimator C', 'Lowest', 'Highest', 'Ratio', 'Round 1',
               'Estimator A', 'Estimator B', 'Estimator C', 'Lowest', 'Highest', 'Ratio', 'Round 2'])
d1 = 8
rr = d1
wl_rows = [(r_[1], r_[2], 'Only if chosen' if r_[0] == 'Only if chosen' else 'Base') for r_ in c_rows] + \
          [(a[0], a[1], 'Base') for a in a_rows]
for i, (rid, item, scope) in enumerate(wl_rows):
    put(de, rr, 1, rid, font=F_BOLD, align=CENTER)
    put(de, rr, 2, item)
    put(de, rr, 3, scope, align=CENTER)
    for c0 in (4, 11):
        a_, c_ = get_column_letter(c0), get_column_letter(c0 + 2)
        for col in range(c0, c0 + 3):
            put(de, rr, col, None, font=F_INPUT, fill=FILL_INPUT, fmt=H, align=CENTER)
        lo, hi, ra = get_column_letter(c0 + 3), get_column_letter(c0 + 4), get_column_letter(c0 + 5)
        put(de, rr, c0 + 3, f'=IF(COUNT({a_}{rr}:{c_}{rr})=0,"",MIN({a_}{rr}:{c_}{rr}))', fmt=H, align=CENTER)
        put(de, rr, c0 + 4, f'=IF(COUNT({a_}{rr}:{c_}{rr})=0,"",MAX({a_}{rr}:{c_}{rr}))', fmt=H, align=CENTER)
        put(de, rr, c0 + 5, f'=IF(COUNT({a_}{rr}:{c_}{rr})<2,"",IF({lo}{rr}=0,"",{hi}{rr}/{lo}{rr}))', fmt='0.00', align=CENTER)
        put(de, rr, c0 + 6, f'=IF({ra}{rr}="","",IF({ra}{rr}>{THR},"Discuss","Close"))', align=CENTER)
    rr += 1
d2 = rr - 1
assert [x[0] for x in wl_rows] == all_ids
for rng_ in (f'J{d1}:J{d2}', f'Q{d1}:Q{d2}'):
    de.conditional_formatting.add(rng_, CellIsRule(operator='equal', formula=['"Discuss"'], fill=PatternFill('solid', fgColor='FDE2E1')))
    de.conditional_formatting.add(rng_, CellIsRule(operator='equal', formula=['"Close"'], fill=PatternFill('solid', fgColor='DCFCE7')))
de_hours = DataValidation(type='decimal', operator='greaterThanOrEqual', formula1='0', allow_blank=True)
de.add_data_validation(de_hours); de_hours.add(f'D{d1}:F{d2}'); de_hours.add(f'K{d1}:M{d2}')
fit_rows(de, d1, d2, DE_W)
de.freeze_panes = f'D{d1}'
DISCUSS2 = f"Delphi!$Q${d1}:$Q${d2}"

# ---------- Schedule ----------

sc = wb.create_sheet('Schedule')
SC_W = [40, 46, 11, 11, 11, 11, 11, 11]
widths(sc, SC_W)
title(sc, 'Schedule and team size (COCOMO II, Boehm et al. 2000)', 'Rate the five scale factors; the schedule follows for '
      'each effort figure. Months = C x person-months ^ F.')
r = 4
section(sc, r, '1. Scale factors (section 10.6): rate VL, L, N, H, VH or XH; nominal (N) when unsure', 8)
r += 1
header(sc, r, ['Factor', 'Meaning', 'Rating', 'Value'])
dv_sf = DataValidation(type='list', formula1='"' + ','.join(LEVELS) + '"', allow_blank=True)
sc.add_data_validation(dv_sf)
s1 = r + 1
vt_first = s1 + len(sf_rows) + 4   # first row of the values table
for i, (f, meaning) in enumerate(sf_rows):
    r += 1
    put(sc, r, 1, f, font=F_BOLD); put(sc, r, 2, meaning)
    put(sc, r, 3, None, font=F_INPUT, fill=FILL_INPUT, align=CENTER); dv_sf.add(f'C{r}')
    vr = vt_first + i
    put(sc, r, 4, f'=IF(C{r}="","",INDEX($C${vr}:$H${vr},MATCH(C{r},$C${vt_first - 1}:$H${vt_first - 1},0)))',
        align=CENTER, fmt='0.00')
s2 = r
fit_rows(sc, s1, s2, SC_W)
r += 1
put(sc, r, 1, 'Sum of scale factors', font=F_BOLD, fill=FILL_TOTAL)
put(sc, r, 4, f'=IF(COUNT(D{s1}:D{s2})=5,SUM(D{s1}:D{s2}),"")', font=F_BOLD, fill=FILL_TOTAL, align=CENTER, fmt='0.00')
SFSUM = f'$D${r}'
r += 2
assert r + 1 == vt_first - 1, (r, vt_first)
put(sc, r, 1, 'Scale factor values (section 10.7, Boehm et al. 2000)', font=F_BOLD, fill=FILL_SECTION)
sc.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
r += 1
header(sc, r, ['Factor', None] + LEVELS)
for f, _ in sf_rows:
    r += 1
    put(sc, r, 1, f)
    for j, v in enumerate(sf_values[f]):
        put(sc, r, 3 + j, v, align=CENTER, fmt='0.00')
r += 2
section(sc, r, '2. Schedule constants (section 10.7)', 8)
SCK = {}
for key, label, val in [('C', 'C', 3.67), ('D', 'D', 0.28), ('B', 'B', 0.91)]:
    r += 1
    put(sc, r, 1, label); put(sc, r, 3, val, align=CENTER, fmt='0.00')
    put(sc, r, 4, 'Source: Boehm et al. 2000', font=F_SUB, border=False)
    SCK[key] = f'$C${r}'
r += 1
put(sc, r, 1, 'Hours per person-month'); put(sc, r, 3, f'={HPM}', font=F_LINK, align=CENTER)
SCK['hpm'] = f'$C${r}'
r += 1
put(sc, r, 1, 'E = B + 0.01 x sum of scale factors', font=F_BOLD)
put(sc, r, 3, f'=IF({SFSUM}="","",{SCK["B"]}+0.01*{SFSUM})', align=CENTER, fmt='0.0000')
SCE = f'$C${r}'
r += 1
put(sc, r, 1, 'F = D + 0.2 x (E - B)', font=F_BOLD)
put(sc, r, 3, f'=IF({SCE}="","",{SCK["D"]}+0.2*({SCE}-{SCK["B"]}))', align=CENTER, fmt='0.0000')
SCF = f'$C${r}'
name('SCHED_F', sc, r, 3)
r += 2
section(sc, r, '3. Result', 8)
r += 1
header(sc, r, ['Effort basis', 'Notes', 'Hours', 'Person-months', 'Months', 'Average team'])
SCR = {}
for key, label, src, why in [
    ('ucp', 'Use Case Points (top-down)', UCP_HOURS, "From 'Use case points'"),
    ('bu', 'Delphi, expected (bottom-up, base scope)', BU_EXP, "From 'Work list'"),
    ('p80', 'Delphi, P80 (bottom-up, base scope)', BU_P80, 'Expected + 0.84 std dev'),
    ('p90', 'Delphi, P90 (bottom-up, base scope)', BU_P90, 'Expected + 1.28 std dev'),
]:
    r += 1
    put(sc, r, 1, label, font=F_BOLD); put(sc, r, 2, why, font=F_SUB)
    put(sc, r, 3, f'={blank_if_zero(src)}', font=F_LINK, align=CENTER, fmt=H)
    put(sc, r, 4, f'=IF(C{r}="","",C{r}/{SCK["hpm"]})', align=CENTER, fmt=H1)
    put(sc, r, 5, f'=IF(OR(D{r}="",{SCF}=""),"",{SCK["C"]}*D{r}^{SCF})', align=CENTER, fmt=H1, font=F_RESULT, fill=FILL_RESULT)
    put(sc, r, 6, f'=IF(E{r}="","",D{r}/E{r})', align=CENTER, fmt=H1, font=F_RESULT, fill=FILL_RESULT)
    SCR[key] = r
name('TDEV_UCP', sc, SCR['ucp'], 5)
name('TDEV_BU', sc, SCR['bu'], 5)
r += 1
note(sc, r, '[assumption] COCOMO II defines this equation for effort estimated with COCOMO II; using it on Use Case Points or '
     'Delphi effort is a shortcut (see Method, Limits).', 8)
TDEV_BU = f"Schedule!$E${SCR['bu']}"

# ---------- Roles and cost ----------

rc = wb.create_sheet('Roles and cost')
RC_W = [36, 15, 11, 9, 9, 9, 8, 11, 9, 11, 12, 12, 12, 13]
widths(rc, RC_W)
title(rc, 'Roles and cost', 'Team plan of 2026-11-24 (section 10.5). Enter the months of each phase and an hourly rate per role. '
      'Hours per role come from the Delphi rows (base scope); capacity comes from allocation and phases.')
section(rc, 4, '1. Phases: months (enter)', 14)
header(rc, 5, ['Phase', 'Months', 'Meaning'])
rc.merge_cells('C5:N5')
meanings = {'Design': 'Interface design and approval of designs; the UX/UI designer works here',
            'Build': 'Building the platform; the frontend developer joins here',
            'Final': 'End-to-end and acceptance testing before release; the QA / tester works here'}
PH = {}
for i, ph in enumerate(PHASES):
    r = 6 + i
    put(rc, r, 1, ph, font=F_BOLD)
    put(rc, r, 2, None, font=F_INPUT, fill=FILL_INPUT, align=CENTER, fmt='0.0')
    put(rc, r, 3, meanings[ph]); rc.merge_cells(start_row=r, start_column=3, end_row=r, end_column=14)
    PH[ph] = f'$B${r}'
put(rc, 9, 1, 'Plan length (months)', font=F_BOLD, fill=FILL_TOTAL)
put(rc, 9, 2, '=IF(COUNT(B6:B8)=3,SUM(B6:B8),"")', font=F_BOLD, fill=FILL_TOTAL, align=CENTER, fmt='0.0')
PLAN_MONTHS = "'Roles and cost'!$B$9"
name('PLAN_MONTHS', rc, 9, 2)

section(rc, 11, '2. Team, hours and capacity', 14)
header(rc, 12, ['Role', 'Engagement', 'Allocation', 'Design', 'Build', 'Final', 'Rows', 'Delphi hours', 'Share',
                'UCP hours', 'Months in its phases', 'Capacity hours', 'Delphi hours / capacity', 'Months needed at allocation'])
dv_yes = DataValidation(type='list', formula1='"Yes,No"', allow_blank=True)
dv_pct = DataValidation(type='decimal', operator='between', formula1='0', formula2='1', allow_blank=True)
rc.add_data_validation(dv_yes); rc.add_data_validation(dv_pct)
q1 = RC_FIRST
for i, role in enumerate(ROLES):
    rr = q1 + i
    tm = TEAM[role]
    put(rc, rr, 1, role, font=F_BOLD)
    put(rc, rr, 2, tm['engagement'], align=CENTER)
    if tm['alloc'] is None:
        put(rc, rr, 3, None, font=F_INPUT, fill=FILL_INPUT, align=CENTER, fmt='0%')
    else:
        put(rc, rr, 3, tm['alloc'], font=F_INPUT, align=CENTER, fmt='0%')
    dv_pct.add(f'C{rr}')
    for j, ph in enumerate(PHASES):
        col = 4 + j
        if tm['phases'] is None:
            put(rc, rr, col, None, font=F_INPUT, fill=FILL_INPUT, align=CENTER)
        else:
            put(rc, rr, col, 'Yes' if ph in tm['phases'] else 'No', font=F_INPUT, align=CENTER)
        dv_yes.add(f'{get_column_letter(col)}{rr}')
    put(rc, rr, 7, f'=COUNTIFS({WLR("N")},A{rr},{WLR("M")},"Base")', align=CENTER, fmt='0')
    put(rc, rr, 8, f'=SUMIFS({WLR("R")},{WLR("N")},A{rr},{WLR("M")},"Base")', align=CENTER, fmt=H)
q2 = q1 + len(ROLES) - 1
assert q2 == RC_LAST
for rr in range(q1, q2 + 1):
    put(rc, rr, 9, f'=IF(SUM($H${q1}:$H${q2})=0,"",H{rr}/SUM($H${q1}:$H${q2}))', align=CENTER, fmt='0%')
    put(rc, rr, 10, f'=IF(OR(I{rr}="",{UCP_HOURS}=""),"",I{rr}*{UCP_HOURS})', align=CENTER, fmt=H)
    put(rc, rr, 11, f'=IF(COUNTIF(D{rr}:F{rr},"Yes")=0,"",IF(COUNT($B$6:$B$8)<3,"",'
                    f'IF(D{rr}="Yes",{PH["Design"]},0)+IF(E{rr}="Yes",{PH["Build"]},0)+IF(F{rr}="Yes",{PH["Final"]},0)))',
        align=CENTER, fmt='0.0')
    put(rc, rr, 12, f'=IF(OR(C{rr}="",K{rr}=""),"",C{rr}*K{rr}*{HPM})', align=CENTER, fmt=H)
    put(rc, rr, 13, f'=IF(OR(L{rr}="",H{rr}=0),"",IF(L{rr}=0,"",H{rr}/L{rr}))', align=CENTER, fmt='0%',
        font=F_RESULT, fill=FILL_RESULT)
    put(rc, rr, 14, f'=IF(OR(C{rr}="",H{rr}=0),"",IF(C{rr}=0,"",H{rr}/(C{rr}*{HPM})))', align=CENTER, fmt='0.0',
        font=F_RESULT, fill=FILL_RESULT)
rc.conditional_formatting.add(f'M{q1}:M{q2}', CellIsRule(operator='greaterThan', formula=['1'],
                                                          fill=PatternFill('solid', fgColor='FDE2E1')))
fit_rows(rc, q1, q2, RC_W)
rr = q2 + 1
put(rc, rr, 1, 'Total', font=F_BOLD, fill=FILL_TOTAL)
for col, fmt in [(7, '0'), (8, H), (10, H), (12, H)]:
    L = get_column_letter(col)
    put(rc, rr, col, f'=SUM({L}{q1}:{L}{q2})', font=F_BOLD, fill=FILL_TOTAL, align=CENTER, fmt=fmt)
put(rc, rr, 13, f'=SUMPRODUCT(($M${q1}:$M${q2}<>"")*1)-COUNTIF($M${q1}:$M${q2},"<=1")', font=F_BOLD, fill=FILL_TOTAL,
    align=CENTER, fmt='0')
TT = rr
name('CAPACITY_HOURS', rc, TT, 12)
note(rc, TT + 1, 'Bottom right of the table: number of roles above 100% of their capacity. Months needed at allocation = '
     'Delphi hours / (allocation x 152). Rows marked Only if chosen (self-hosted model, self-hosted identity server) are not '
     'included.', 14)

c0 = TT + 4
section(rc, c0, '3. Cost (enter an hourly rate per role, in your currency)', 14)
header(rc, c0 + 1, ['Role', 'Rate per hour', 'Cost of Delphi hours', 'Cost of UCP hours', 'Cost of planned allocation'])
k1 = c0 + 2
for i, role in enumerate(ROLES):
    rr, tr_ = k1 + i, q1 + i
    put(rc, rr, 1, f'=A{tr_}', font=F_BOLD)
    put(rc, rr, 2, None, font=F_INPUT, fill=FILL_INPUT, align=CENTER, fmt='#,##0.00')
    put(rc, rr, 3, f'=IF(B{rr}="","",H{tr_}*B{rr})', align=CENTER, fmt=MONEY)
    put(rc, rr, 4, f'=IF(OR(B{rr}="",J{tr_}=""),"",J{tr_}*B{rr})', align=CENTER, fmt=MONEY)
    put(rc, rr, 5, f'=IF(OR(B{rr}="",L{tr_}=""),"",L{tr_}*B{rr})', align=CENTER, fmt=MONEY)
k2 = k1 + len(ROLES) - 1
rr = k2 + 1
put(rc, rr, 1, 'Total', font=F_BOLD, fill=FILL_TOTAL)
put(rc, rr, 2, None, fill=FILL_TOTAL)
for col in (3, 4, 5):
    L = get_column_letter(col)
    put(rc, rr, col, f'=SUM({L}{k1}:{L}{k2})', font=F_BOLD, fill=FILL_TOTAL, align=CENTER, fmt=MONEY)
QT = rr
name('COST_BU', rc, QT, 3)
name('COST_UCP', rc, QT, 4)
name('COST_PLAN', rc, QT, 5)
note(rc, QT + 1, 'Cost of planned allocation is what the team costs for the time it is booked (allocation x months of its '
     'phases x 152 hours x rate), whether or not the estimated hours fill it. Rates are not part of the inputs document.', 14)
RATES = f"'Roles and cost'!$B${k1}:$B${k2}"
COST = {'ucp': f"'Roles and cost'!$D${QT}", 'bu': f"'Roles and cost'!$C${QT}", 'plan': f"'Roles and cost'!$E${QT}"}

# ---------- Summary ----------

sm = wb.create_sheet('Summary')
widths(sm, [44, 13, 13, 13, 13, 15])
title(sm, 'Summary', 'Results update from the other sheets. Blank results wait for the inputs listed at the bottom.')
r = 4
section(sm, r, 'Estimate (base scope)', 6)
r += 1
header(sm, r, ['Method', 'Hours', 'Person-months', 'Months', 'Average team', 'Cost'])
for key, label, cost in [('ucp', 'Use Case Points (top-down)', COST['ucp']),
                         ('bu', 'Delphi, expected (bottom-up)', COST['bu']),
                         ('p80', 'Delphi, P80', None), ('p90', 'Delphi, P90', None)]:
    r += 1
    put(sm, r, 1, label, font=F_BOLD)
    for col, src_col, fmt in [(2, 'C', H), (3, 'D', H1), (4, 'E', H1), (5, 'F', H1)]:
        put(sm, r, col, f'=Schedule!{src_col}{SCR[key]}', font=F_LINK, align=CENTER, fmt=fmt)
    if cost:
        put(sm, r, 6, f'=IF(COUNT({RATES})<{len(ROLES)},"",IF({cost}=0,"",{cost}))', font=F_LINK, align=CENTER, fmt=MONEY)
    else:
        put(sm, r, 6, None)
r += 1
put(sm, r, 1, 'Delphi expected / Use Case Points hours', font=F_BOLD)
put(sm, r, 2, f'=IF(OR(B{r - 3}="",B{r - 4}=""),"",B{r - 3}/B{r - 4})', align=CENTER, fmt='0.00')
r += 1
put(sm, r, 1, 'Team plan (planned allocation)', font=F_BOLD)
put(sm, r, 2, f"={blank_if_zero(chr(39) + 'Roles and cost' + chr(39) + '!$L$' + str(TT))}", font=F_LINK, align=CENTER, fmt=H)
put(sm, r, 3, f'=IF(B{r}="","",B{r}/{HPM})', align=CENTER, fmt=H1)
put(sm, r, 4, f'=IF({PLAN_MONTHS}="","",{PLAN_MONTHS})', font=F_LINK, align=CENTER, fmt=H1)
put(sm, r, 5, f'=IF(OR(C{r}="",D{r}=""),"",IF(D{r}=0,"",C{r}/D{r}))', align=CENTER, fmt=H1)
put(sm, r, 6, f'=IF(COUNT({RATES})<{len(ROLES)},"",IF({COST["plan"]}=0,"",{COST["plan"]}))', font=F_LINK, align=CENTER, fmt=MONEY)
r += 1
put(sm, r, 1, 'Roles above 100% of their capacity', font=F_BOLD)
put(sm, r, 2, f"='Roles and cost'!$M${TT}", font=F_LINK, align=CENTER, fmt='0')
r += 1
note(sm, r, 'Cost is shown once every role has a rate; P80 and P90 cost are not computed. Months and team size of the '
     "methods are averages from the COCOMO II schedule equation; the team plan row uses your phases and allocations.", 6)

r += 2
section(sm, r, 'Inputs still missing', 6)
missing = [
    ('Environmental factors not rated (of 8)', f'=8-COUNT({ECF_RANGE})'),
    ('Scale factors not rated (of 5)', f'=5-SUMPRODUCT((Schedule!$C${s1}:$C${s2}<>"")*1)'),
    ('Base-scope rows without agreed Delphi hours', f"='Work list'!R{TOT['missing']}"),
    ('Rows still marked Discuss after round 2', f'=COUNTIF({DISCUSS2},"Discuss")'),
    (f'Roles without an hourly rate (of {len(ROLES)})', f'={len(ROLES)}-COUNT({RATES})'),
    ('Phases without months (of 3)', "=3-COUNT('Roles and cost'!$B$6:$B$8)"),
    ('Roles without an allocation', f"={len(ROLES)}-COUNT('Roles and cost'!$C${q1}:$C${q2})"),
    ('Unknowns with a recorded answer or decision (of 22)', '=SUMPRODUCT((Unknowns!$E$5:$E$26<>"")*1)'),
]
for label, f in missing:
    r += 1
    put(sm, r, 1, label); put(sm, r, 2, f, font=F_LINK, align=CENTER, fmt='0')

WL = "'Work list'!"
r += 2
section(sm, r, 'Components in base scope, by complexity and uncertainty', 6)
r += 1
for i, h in enumerate(['Complexity \\ Uncertainty', 'Low', 'Medium', 'High', 'Total'], 1):
    put(sm, r, i, h, font=F_HEAD, fill=FILL_HEAD, align=CENTER)
hdr = r
for lvl in ['High', 'Medium', 'Low']:
    r += 1
    put(sm, r, 1, lvl, font=F_BOLD)
    for col in range(2, 5):
        L = get_column_letter(col)
        put(sm, r, col, f'=COUNTIFS({WL}$I${first}:$I${last},$A{r},{WL}$K${first}:$K${last},{L}${hdr},'
                        f'{WL}$M${first}:$M${last},"Base",{WL}$B${first}:$B${last},"Component")', fmt='0', align=CENTER)
    put(sm, r, 5, f'=SUM(B{r}:D{r})', fmt='0', align=CENTER, font=F_BOLD)
r += 1
put(sm, r, 1, 'Total', font=F_BOLD, fill=FILL_TOTAL)
for col in range(2, 6):
    L = get_column_letter(col)
    put(sm, r, col, f'=SUM({L}{hdr + 1}:{L}{r - 1})', fmt='0', align=CENTER, font=F_BOLD, fill=FILL_TOTAL)
level_rules(sm, f'A{hdr + 1}:A{hdr + 3}')

r += 2
section(sm, r, 'Rows by area', 6)
r += 1
for i, h in enumerate(['Area', 'Base scope', 'Only if chosen'], 1):
    put(sm, r, i, h, font=F_HEAD, fill=FILL_HEAD, align=CENTER)
areas = []
for g, *_ in c_rows:
    a = 'Operations' if g == 'Only if chosen' else g
    if a not in areas:
        areas.append(a)
areas.append('Activity')
a_first = r + 1
for a in areas:
    r += 1
    put(sm, r, 1, a)
    for col, crit in [(2, 'Base'), (3, 'Only if chosen')]:
        put(sm, r, col, f'=COUNTIFS({WL}$D${first}:$D${last},$A{r},{WL}$M${first}:$M${last},"{crit}")', fmt='0', align=CENTER)
r += 1
put(sm, r, 1, 'Total', font=F_BOLD, fill=FILL_TOTAL)
for col in (2, 3):
    L = get_column_letter(col)
    put(sm, r, col, f'=SUM({L}{a_first}:{L}{r - 1})', fmt='0', align=CENTER, font=F_BOLD, fill=FILL_TOTAL)

# ---------- Requirements ----------

rq = wb.create_sheet('Requirements')
RQ_W = [8, 12, 30, 70, 26, 26]
widths(rq, RQ_W)
title(rq, 'Requirements', 'Functional requirements (FR) and technical requirements that drive effort (TR). '
      'Components are taken from the Requirements column of the Work list.')
header(rq, 4, ['ID', 'Kind', 'Area', 'Requirement', 'Source', 'Components'])
r = 4
for kind, area, rid, text, src in fr_rows + tr_rows:
    r += 1
    comps = ', '.join(comp_for.get(rid, [])) or 'None listed'
    for i, v in enumerate([rid, kind, area, text, src, comps], 1):
        put(rq, r, i, v, font=F_BOLD if i == 1 else F_BASE, align=CENTER if i in (1, 2) else WRAP)
fit_rows(rq, 5, r, RQ_W)
rq.auto_filter.ref = f'A4:F{r}'
rq.freeze_panes = 'B5'

# ---------- Functionalities ----------

fu = wb.create_sheet('Functionalities')
FU_W = [7, 26, 52, 26, 22, 26]
widths(fu, FU_W)
title(fu, 'Functionalities', 'User-visible features and platform services, with their requirements and components.')
header(fu, 4, ['ID', 'Group', 'Functionality', 'Who', 'Requirements', 'Components'])
r = 4
for g, fid, text, who, reqs, comps in f_rows:
    r += 1
    for i, v in enumerate([fid, g, text, who, reqs, comps], 1):
        put(fu, r, i, v, font=F_BOLD if i == 1 else F_BASE, align=CENTER if i == 1 else WRAP)
fit_rows(fu, 5, r, FU_W)
fu.auto_filter.ref = f'A4:F{r}'
fu.freeze_panes = 'B5'

# ---------- Interfaces ----------

itf = wb.create_sheet('Interfaces')
IT_W = [7, 10, 30, 46, 26, 14, 16, 44]
widths(itf, IT_W)
title(itf, 'Interfaces and integrations', 'External integrations and internal interfaces.')
header(itf, 4, ['ID', 'Type', 'System or interface', 'Use or operations', 'Protocol or method', 'Use cases', 'Source', 'Work involved'])
r = 4
for iid, system, use, proto, ucs, src, work in if_ext:
    r += 1
    for i, v in enumerate([iid, 'External', system, use, proto, ucs, src, work], 1):
        put(itf, r, i, v, font=F_BOLD if i == 1 else F_BASE, align=CENTER if i in (1, 2) else WRAP)
for iid, name, ops, src in if_int:
    r += 1
    for i, v in enumerate([iid, 'Internal', name, ops, '', '', src, ''], 1):
        put(itf, r, i, v, font=F_BOLD if i == 1 else F_BASE, align=CENTER if i in (1, 2) else WRAP)
fit_rows(itf, 5, r, IT_W)
itf.auto_filter.ref = f'A4:H{r}'
itf.freeze_panes = 'C5'
r += 2
put(itf, r, 1, 'Data formats in and out', font=F_BOLD, border=False)
for b in formats:
    r += 1
    put(itf, r, 1, b, border=False); itf.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)

# ---------- Reuse ----------

ru = wb.create_sheet('Reuse')
RU_W = [7, 48, 40, 30, 16]
widths(ru, RU_W)
title(ru, 'Reused components', 'From outside (configure or use, not build), and built once and reused inside the platform.')
put(ru, 4, 1, 'Reused from outside', font=F_BOLD, fill=FILL_SECTION)
ru.merge_cells(start_row=4, start_column=1, end_row=4, end_column=5)
header(ru, 5, ['ID', 'Component', 'Candidates named in the sources', 'Used by', 'Source'])
r = 5
for vals in r_rows:
    r += 1
    for i, v in enumerate(vals, 1):
        put(ru, r, i, v, font=F_BOLD if i == 1 else F_BASE, align=CENTER if i == 1 else WRAP)
fit_rows(ru, 6, r, RU_W)
r += 2
put(ru, r, 1, 'Built once, reused inside the platform', font=F_BOLD, fill=FILL_SECTION)
ru.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
r += 1
for i, h in enumerate(['', 'Component', 'Reused by', 'Source'], 1):
    put(ru, r, i, h, font=F_HEAD, fill=FILL_HEAD, align=CENTER)
start_in = r + 1
for comp, by, src in reuse_in:
    r += 1
    for i, v in enumerate(['', comp, by, src], 1):
        put(ru, r, i, v, align=WRAP)
fit_rows(ru, start_in, r, RU_W)

# ---------- Unknowns ----------

un = wb.create_sheet('Unknowns')
UN_W = [7, 56, 30, 24, 40, 12, 36]
widths(un, UN_W)
title(un, 'Unknowns that change the estimate', 'Record answers and decisions in the yellow cells as they arrive.')
header(un, 4, ['ID', 'Unknown', 'Affects', 'Source', 'Answer or decision', 'Date', 'Effect on the estimate'])
r = 4
for uid, text, affects, src in u_rows:
    r += 1
    for i, v in enumerate([uid, text, affects, src], 1):
        put(un, r, i, v, font=F_BOLD if i == 1 else F_BASE, align=CENTER if i == 1 else WRAP)
    for col in (5, 6, 7):
        put(un, r, col, None, font=F_INPUT, fill=FILL_INPUT, fmt='yyyy-mm-dd' if col == 6 else None)
assert r == 26, r
fit_rows(un, 5, r, UN_W)
un.auto_filter.ref = f'A4:G{r}'
un.freeze_panes = 'B5'

# ---------- Traceability ----------

tr = wb.create_sheet('Traceability')
TR_W = [40, 34, 26, 44]
widths(tr, TR_W)
title(tr, 'Traceability', 'From each use case to its requirements, functionalities and components.')
header(tr, 4, ['Use case', 'Requirements', 'Functionalities', 'Components'])
r = 4
for vals in t_rows:
    r += 1
    for i, v in enumerate(vals, 1):
        put(tr, r, i, v, font=F_BOLD if i == 1 else F_BASE)
fit_rows(tr, 5, r, TR_W)
tr.freeze_panes = 'B5'


ORDER = ['Read me', 'Summary', 'Method', 'Use case points', 'Delphi', 'Work list', 'Schedule', 'Roles and cost',
         'Requirements', 'Functionalities', 'Interfaces', 'Reuse', 'Unknowns', 'Traceability']
assert sorted(ORDER) == sorted(wb.sheetnames), wb.sheetnames
wb._sheets = [wb[n] for n in ORDER]
for ws in wb.worksheets:
    ws.sheet_view.zoomScale = 100
    ws.sheet_view.tabSelected = ws.title == 'Read me'
wb.active = 0
wb.save(OUT_PATH)
print('saved', OUT_PATH)
print('work list rows', first, 'to', last, '| totals', TOT, '| delphi rows', d1, 'to', d2, '| schedule rows', SCR, '| roles', q1, 'to', q2, '| cost rows', k1, 'to', k2)
