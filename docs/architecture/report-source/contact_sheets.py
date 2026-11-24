"""Render PDF pages onto contact sheets (several pages per PNG) for a visual check of the layout.

Usage: .venv/bin/python contact_sheets.py report.pdf FIRST LAST COLS ROWS OUT_PREFIX [ZOOM]
Example: .venv/bin/python contact_sheets.py ../2026-11-23-architecture-report.pdf 1 49 4 2 /tmp/sheet 0.66
"""
import sys
import fitz

src = fitz.open(sys.argv[1])
first, last, cols, rows = (int(x) for x in sys.argv[2:6])
prefix = sys.argv[6]
zoom = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
cell_w, cell_h = 792, 792  # points; each page is fit into a square cell
per = cols * rows
pages = list(range(first - 1, min(last, len(src))))
for s in range(0, len(pages), per):
    out = fitz.open()
    sheet = out.new_page(width=cols * cell_w, height=rows * cell_h)
    sheet.draw_rect(sheet.rect, color=None, fill=(0.85, 0.87, 0.9))
    for i, pno in enumerate(pages[s:s + per]):
        r, c = divmod(i, cols)
        pr = src[pno].rect
        scale = min((cell_w - 24) / pr.width, (cell_h - 40) / pr.height)
        w, h = pr.width * scale, pr.height * scale
        x0 = c * cell_w + (cell_w - w) / 2
        y0 = r * cell_h + 30
        box = fitz.Rect(x0, y0, x0 + w, y0 + h)
        sheet.draw_rect(box, color=(0.6, 0.6, 0.6), fill=(1, 1, 1), width=0.5)
        sheet.show_pdf_page(box, src, pno)
        sheet.insert_text((c * cell_w + 12, r * cell_h + 20), f"p{pno + 1}", fontsize=16, color=(0.1, 0.2, 0.6))
    pix = sheet.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    name = f"{prefix}-{pages[s] + 1:02d}.png"
    pix.save(name)
    print(name, pix.width, pix.height)
