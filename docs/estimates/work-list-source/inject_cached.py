"""Write cached values (computed by pycel) into formula cells, so previews show results.
Usage: .venv/bin/python inject_cached.py IN.xlsx OUT.xlsx (OUT must not exist). Formulas are kept; Excel still recalculates on open."""
import re, sys, zipfile
from xml.sax.saxutils import escape
from pycel import ExcelCompiler
from openpyxl import load_workbook

src, out = sys.argv[1], sys.argv[2]
import os
if os.path.exists(out):
    sys.exit(f'{out} exists; choose a new file name')
wb = load_workbook(src)
names = wb.sheetnames
xl = ExcelCompiler(filename=src)
values = {}
for i, ws in enumerate(wb.worksheets, 1):
    for row in ws.iter_rows():
        for c in row:
            if isinstance(c.value, str) and c.value.startswith('='):
                values[(i, c.coordinate)] = xl.evaluate(f'{ws.title}!{c.coordinate}')

def cell_xml(i, m):
    ref, attrs, formula = m.group(1), m.group(2), m.group(3)
    v = values[(i, ref)]
    if isinstance(v, bool):
        return f'<c r="{ref}"{attrs} t="b"><f>{formula}</f><v>{int(v)}</v></c>'
    if isinstance(v, (int, float)):
        num = repr(int(v)) if float(v).is_integer() else repr(float(v))
        return f'<c r="{ref}"{attrs}><f>{formula}</f><v>{num}</v></c>'
    if v is None:
        v = ''
    if isinstance(v, str) and v.startswith('#'):
        raise SystemExit(f'error value in sheet {i} {ref}: {v}')
    return f'<c r="{ref}"{attrs} t="str"><f>{formula}</f><v>{escape(str(v))}</v></c>'

pat = re.compile(r'<c r="([A-Z]+\d+)"((?: s="\d+")?)><f>(.*?)</f><v ?/></c>')
done = 0
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
    for info in zin.infolist():
        data = zin.read(info.filename)
        m = re.fullmatch(r'xl/worksheets/sheet(\d+)\.xml', info.filename)
        if m:
            i = int(m.group(1))
            text, n = pat.subn(lambda mm: cell_xml(i, mm), data.decode('utf-8'))
            done += n
            data = text.encode('utf-8')
        zout.writestr(info, data)
print(f'formula cells: {len(values)}, cached values written: {done}')
assert done == len(values)
