"""Build the estimation work list (.xlsx) from the estimation inputs Markdown.

Usage: .venv/bin/python build_worklist.py INPUT.md OUTPUT.xlsx
Refuses to overwrite OUTPUT, so a workbook with estimates in it is never replaced.
Every row comes from a table in the Markdown, so the two files stay consistent.
"""
import math
import re
import sys
from collections import defaultdict

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

MD_PATH, OUT_PATH = sys.argv[1], sys.argv[2]
import os
if os.path.exists(OUT_PATH):
    sys.exit(f'{OUT_PATH} exists; choose a new file name')
md = open(MD_PATH, encoding='utf-8').read()

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
    """First Markdown table in text: list of rows (cells cleaned), header first."""
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
meta_basis = clean(re.search(r'^- Basis: (.+)$', md, re.M).group(1))

prefixes = [[clean(c) for c in r] for r in table(block('## Purpose'))[1:]]

fr_rows = []
for h in ['### 2.1', '### 2.2', '### 2.3', '### 2.4', '### 2.5', '### 2.6']:
    head = next(l for l in md.split('\n') if l.startswith(h))
    area = re.sub(r'^### \d\.\d ', '', head)
    for r in table(block(h))[1:]:
        r = [clean(c) for c in r]
        fr_rows.append(['Functional', area] + r)
tr_rows = [['Technical', 'Drives effort'] + [clean(c) for c in r] for r in table(block('## 3.'))[1:]]

f_rows = [[g] + r for g, r in grouped(table(block('## 4.')))]
if_ext = [[clean(c) for c in r] for r in table(block('### 5.1'))[1:]]
if_int = [[clean(c) for c in r] for r in table(block('### 5.2'))[1:]]
formats = bullets(block('### 5.3'))
c_rows = [[g] + r for g, r in grouped(table(block('### 6.1')))]
r_rows = [[clean(c) for c in r] for r in table(block('### 6.2'))[1:]]
reuse_in = [[clean(c) for c in r] for r in table(block('### 6.3'))[1:]]
a_rows = [[clean(c) for c in r] for r in table(block('### 6.4'))[1:]]
scales = block('### 7.1')
ratings = {clean(r[0]): [clean(c) for c in r] for r in table(block('### 7.2'))[1:]}
u_rows = [[clean(c) for c in r] for r in table(block('## 8.'))[1:]]
t_rows = [[clean(c) for c in r] for r in table(block('## 9.'))[1:]]

assert len(c_rows) == 31 and len(ratings) == 31 and len(a_rows) == 9, (len(c_rows), len(ratings), len(a_rows))
assert len(fr_rows) == 43 and len(tr_rows) == 12 and len(f_rows) == 25 and len(u_rows) == 22
assert len(if_ext) + len(if_int) == 14 and len(r_rows) == 9 and len(t_rows) == 10

# components per requirement (inverse of the Requirements column in section 6.1)
comp_for = defaultdict(list)
for g, cid, name, where, resp, reqs, deps in c_rows:
    for rid in expand(reqs, 'FR') + expand(reqs, 'TR'):
        comp_for[rid].append(cid)

# ---------- styles ----------

ARIAL = 'Arial'
F_BASE = Font(name=ARIAL, size=10)
F_BOLD = Font(name=ARIAL, size=10, bold=True)
F_TITLE = Font(name=ARIAL, size=14, bold=True, color='0F172A')
F_SUB = Font(name=ARIAL, size=10, color='475569')
F_HEAD = Font(name=ARIAL, size=10, bold=True, color='FFFFFF')
F_INPUT = Font(name=ARIAL, size=10, color='0000FF')
F_LINK = Font(name=ARIAL, size=10, color='008000')
F_LINK_B = Font(name=ARIAL, size=10, bold=True, color='008000')
FILL_HEAD = PatternFill('solid', fgColor='1E40AF')
FILL_INPUT = PatternFill('solid', fgColor='FFF2CC')
FILL_TOTAL = PatternFill('solid', fgColor='F1F5F9')
FILL_SECTION = PatternFill('solid', fgColor='DBEAFE')
THIN = Side(style='thin', color='CBD5E1')
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical='top')
CENTER = Alignment(horizontal='center', vertical='top', wrap_text=True)
LEVEL_FILLS = {'High': 'FDE2E1', 'Medium': 'FEF3C7', 'Low': 'DCFCE7'}

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


def header(ws, row, names):
    for i, n in enumerate(names, 1):
        put(ws, row, i, n, font=F_HEAD, fill=FILL_HEAD, align=CENTER)


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


SRC = f'Built from docs/estimates/2026-11-23-estimation-inputs.md ({meta_basis}).'

# ---------- Read me ----------

rm = wb.active
rm.title = 'Read me'
widths(rm, [30, 22, 16, 16, 16, 22])
title(rm, 'Estimation work list: pavement data platform MVP', f'Date: {meta_date}. ' + SRC)
r = 4
put(rm, r, 1, 'Purpose', font=F_BOLD, fill=FILL_SECTION); rm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
r += 1
put(rm, r, 1, 'One row per component to develop and per activity, ready for an effort estimate. No effort figures are filled in. '
    'Requirements, functionalities, interfaces, reused components, unknowns and traceability are on their own sheets.', border=False)
rm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6); rm.row_dimensions[r].height = 30
r += 2
put(rm, r, 1, 'How to fill it in', font=F_BOLD, fill=FILL_SECTION); rm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
steps = [
    '1. Set the effort unit in the yellow cell below, for example person-days.',
    "2. In 'Work list', fill the yellow cells: effort low, most likely and high, estimated by, notes. "
    'Effort expected is calculated as (low + 4 x most likely + high) / 6, once all three are filled. '
    "Totals are at the end of the list and on 'Summary'.",
    '3. Complexity and uncertainty are proposed ratings (blue text). Change them from the drop-down list if you disagree. '
    'Activities have no rating yet.',
    "4. Scope: 'Base' rows are in the MVP; 'Only if chosen' rows exist only if that option is chosen. Totals keep them apart.",
    "5. In 'Unknowns', record answers and decisions as they arrive, and their effect on the estimate.",
]
for s in steps:
    r += 1
    put(rm, r, 1, s, border=False); rm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    rm.row_dimensions[r].height = 13 * max(1, math.ceil(len(s) / 150)) + 3
r += 2
put(rm, r, 1, 'Effort unit', font=F_BOLD)
unit_cell = put(rm, r, 2, None, font=F_INPUT, fill=FILL_INPUT)
UNIT_REF = f"'Read me'!$B${r}"
put(rm, r, 3, 'Type the unit used in all effort columns.', font=F_SUB, border=False)
rm.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)

r += 2
put(rm, r, 1, 'Example row (format only, not an estimate)', font=F_BOLD, fill=FILL_SECTION)
rm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
r += 1
for i, h in enumerate(['Item', 'Effort low', 'Effort most likely', 'Effort high', 'Effort expected', 'Estimated by'], 1):
    put(rm, r, i, h, font=F_HEAD, fill=FILL_HEAD, align=CENTER)
r += 1
put(rm, r, 1, 'Example item')
for col, v in [(2, 2), (3, 3), (4, 7)]:
    put(rm, r, col, v, font=F_INPUT, fill=FILL_INPUT, fmt='0.0')
put(rm, r, 5, f'=IF(COUNT(B{r}:D{r})=3,(B{r}+4*C{r}+D{r})/6,"")', fmt='0.0')
put(rm, r, 6, 'Initials', font=F_INPUT, fill=FILL_INPUT)
EXAMPLE_ROW = r

r += 2
put(rm, r, 1, 'Legend', font=F_BOLD, fill=FILL_SECTION); rm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
legend = [
    ('Yellow cell, blue text', 'A cell to fill in.', FILL_INPUT, F_INPUT),
    ('Blue text', 'A value typed by hand, such as a proposed rating. Edit if needed.', None, F_INPUT),
    ('Black text', 'Text from the inputs document, or a formula.', None, F_BASE),
    ('Green text', 'A link to a cell on another sheet.', None, F_LINK),
]
for name, meaning, fill, font in legend:
    r += 1
    put(rm, r, 1, name, font=font, fill=fill)
    put(rm, r, 2, meaning); rm.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)

r += 2
put(rm, r, 1, 'Rating scales (section 7.1 of the inputs document)', font=F_BOLD, fill=FILL_SECTION)
rm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
comp_txt, unc_txt = scales.split('Uncertainty', 1)
for kind, txt in [('Complexity', comp_txt), ('Uncertainty', unc_txt)]:
    for b in bullets(txt):
        level, desc = b.split(':', 1)
        r += 1
        put(rm, r, 1, f'{kind}: {level}', font=F_BOLD)
        desc = desc.strip()
        put(rm, r, 2, desc[:1].upper() + desc[1:]); rm.merge_cells(start_row=r, start_column=2, end_row=r, end_column=6)
        rm.row_dimensions[r].height = 13 * max(1, math.ceil(len(desc) / 105)) + 3

r += 2
put(rm, r, 1, 'ID prefixes', font=F_BOLD, fill=FILL_SECTION); rm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
sheet_of = {'FR': 'Requirements', 'TR': 'Requirements', 'F': 'Functionalities', 'IF': 'Interfaces',
            'C': 'Work list', 'R': 'Reuse', 'A': 'Work list', 'U': 'Unknowns'}
for p, meaning, section in prefixes:
    r += 1
    put(rm, r, 1, p, font=F_BOLD)
    put(rm, r, 2, meaning); rm.merge_cells(start_row=r, start_column=2, end_row=r, end_column=4)
    put(rm, r, 5, f'Sheet: {sheet_of[p]}'); rm.merge_cells(start_row=r, start_column=5, end_row=r, end_column=6)

# ---------- Work list ----------

wl = wb.create_sheet('Work list')
WL_COLS = ['ID', 'Type', 'Item', 'Area', 'Where', 'Description', 'Requirements', 'Depends on',
           'Complexity', 'Complexity drivers', 'Uncertainty', 'Unknowns', 'Scope',
           'Effort low', 'Effort most likely', 'Effort high', 'Effort expected', 'Estimated by', 'Notes']
WL_W = [7, 11, 28, 17, 17, 46, 20, 18, 11, 42, 11, 15, 12, 10, 10, 10, 11, 13, 28]
widths(wl, WL_W)
title(wl, 'Work list', 'One row per component to develop (C) and activity (A). Fill the yellow cells; see Read me.')
HR = 4
header(wl, HR, WL_COLS)
row = HR + 1
first = row
for g, cid, name, where, resp, reqs, deps in c_rows:
    rt = ratings[cid]
    scope = 'Only if chosen' if g == 'Only if chosen' else 'Base'
    area = 'Operations' if g == 'Only if chosen' else g
    vals = [cid, 'Component', name, area, where, resp, reqs, deps, rt[2], rt[3], rt[4], rt[5], scope]
    for i, v in enumerate(vals, 1):
        font = F_INPUT if i in (9, 11) else (F_BOLD if i == 1 else F_BASE)
        put(wl, row, i, v, font=font, align=CENTER if i in (1, 2, 9, 11, 13) else WRAP)
    row += 1
for aid, act, unk, src in a_rows:
    vals = [aid, 'Activity', act, 'Activity', '', f'Source: {src}', '', '', None, '', None, unk, 'Base']
    for i, v in enumerate(vals, 1):
        font = F_INPUT if i in (9, 11) else (F_BOLD if i == 1 else F_BASE)
        put(wl, row, i, v, font=font, align=CENTER if i in (1, 2, 9, 11, 13) else WRAP)
    row += 1
last = row - 1
for rr in range(first, last + 1):
    for col in (14, 15, 16, 18, 19):
        put(wl, rr, col, None, font=F_INPUT, fill=FILL_INPUT, fmt='0.0' if col < 17 else None,
            align=CENTER if col < 17 else WRAP)
    put(wl, rr, 17, f'=IF(COUNT(N{rr}:P{rr})=3,(N{rr}+4*O{rr}+P{rr})/6,"")', fmt='0.0', align=CENTER)
fit_rows(wl, first, last, WL_W)

rng = lambda col: f'${col}${first}:${col}${last}'
dv_level = DataValidation(type='list', formula1='"Low,Medium,High"', allow_blank=True)
dv_scope = DataValidation(type='list', formula1='"Base,Only if chosen"', allow_blank=False)
wl.add_data_validation(dv_level); wl.add_data_validation(dv_scope)
dv_level.add(f'I{first}:I{last}'); dv_level.add(f'K{first}:K{last}'); dv_scope.add(f'M{first}:M{last}')
level_rules(wl, f'I{first}:I{last}'); level_rules(wl, f'K{first}:K{last}')
wl.auto_filter.ref = f'A{HR}:S{last}'
wl.freeze_panes = f'D{HR + 1}'

t = last + 2
put(wl, t, 3, 'Totals', font=F_BOLD, fill=FILL_TOTAL)
for col, h in zip(range(14, 18), ['Effort low', 'Effort most likely', 'Effort high', 'Effort expected']):
    put(wl, t, col, h, font=F_BOLD, fill=FILL_TOTAL, align=CENTER)
TOTALS = {}
for k, (label, crit) in enumerate([('Base scope', 'Base'), ('Only if chosen', 'Only if chosen')], 1):
    rr = t + k
    put(wl, rr, 3, label, font=F_BOLD)
    for col in range(14, 18):
        L = get_column_letter(col)
        put(wl, rr, col, f'=SUMIFS({L}${first}:{L}${last},$M${first}:$M${last},"{crit}")', fmt='0.0', align=CENTER)
    TOTALS[crit] = rr
rr = t + 3
put(wl, rr, 3, 'Base-scope rows without a complete estimate', font=F_BOLD)
put(wl, rr, 17, f'=SUMPRODUCT(($M${first}:$M${last}="Base")*($Q${first}:$Q${last}=""))', fmt='0', align=CENTER)
TOTALS['missing'] = rr
put(wl, rr + 1, 3, '=IF(' + UNIT_REF + '="","Effort unit: not set (Read me)","Effort unit: "&' + UNIT_REF + ')',
    font=F_LINK, border=False)
wl.page_setup.orientation = 'landscape'
wl.page_setup.fitToWidth = 1
wl.page_setup.fitToHeight = 0
wl.sheet_properties.pageSetUpPr.fitToPage = True
wl.print_title_rows = f'{HR}:{HR}'

# ---------- Summary ----------

sm = wb.create_sheet('Summary', 1)
widths(sm, [36, 14, 14, 14, 14])
title(sm, 'Summary', 'Counts and totals update from the Work list.')
WL = "'Work list'!"
r = 4
put(sm, r, 1, 'Components in base scope, by complexity and uncertainty', font=F_BOLD, fill=FILL_SECTION)
sm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
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
put(sm, r, 1, 'Rows by area', font=F_BOLD, fill=FILL_SECTION)
sm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
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

r += 2
put(sm, r, 1, 'Effort totals (links to the Work list)', font=F_BOLD, fill=FILL_SECTION)
sm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
r += 1
for i, h in enumerate(['Scope', 'Effort low', 'Effort most likely', 'Effort high', 'Effort expected'], 1):
    put(sm, r, i, h, font=F_HEAD, fill=FILL_HEAD, align=CENTER)
for label, key in [('Base scope', 'Base'), ('Only if chosen', 'Only if chosen')]:
    r += 1
    put(sm, r, 1, label, font=F_BOLD)
    for col in range(2, 6):
        src_col = get_column_letter(col + 12)
        put(sm, r, col, f'={WL}{src_col}{TOTALS[key]}', font=F_LINK, fmt='0.0', align=CENTER)
r += 1
put(sm, r, 1, 'Effort unit', font=F_BOLD)
put(sm, r, 2, f'=IF({UNIT_REF}="","not set",{UNIT_REF})', font=F_LINK, align=CENTER)

r += 2
put(sm, r, 1, 'Progress', font=F_BOLD, fill=FILL_SECTION)
sm.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
r += 1
put(sm, r, 1, 'Base-scope rows')
put(sm, r, 2, f'=COUNTIF({WL}$M${first}:$M${last},"Base")', fmt='0', align=CENTER)
r += 1
put(sm, r, 1, 'Base-scope rows without a complete estimate')
put(sm, r, 2, f'={WL}Q{TOTALS["missing"]}', font=F_LINK, fmt='0', align=CENTER)
r += 1
put(sm, r, 1, 'Unknowns with a recorded answer or decision')
put(sm, r, 2, "=SUMPRODUCT((Unknowns!$E$5:$E$26<>\"\")*1)", font=F_LINK, fmt='0', align=CENTER)
put(sm, r, 3, f'of {len(u_rows)}', border=False)

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

for ws in wb.worksheets:
    ws.sheet_view.zoomScale = 100
wb.active = 0
wb.save(OUT_PATH)
print('saved', OUT_PATH)
print('work list rows', first, 'to', last, '| totals rows', TOTALS, '| example row', EXAMPLE_ROW, '| unit', UNIT_REF)
