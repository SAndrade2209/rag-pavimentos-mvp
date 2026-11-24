"""Build the architecture report PDF with Chrome headless.

Usage (from this folder):
    .venv/bin/python build.py ../YYYY-MM-DD-architecture-report.pdf [--force]

Two passes: the first finds the page of every heading through the PDF bookmarks
that Chrome writes; the second fills the contents page with those page numbers.
The build stops if a heading is missing from the bookmarks or if page numbers
move between the passes. It does not overwrite an existing PDF unless --force.
"""
import html
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pypdf

ROOT = Path(__file__).resolve().parent
CHROME = os.environ.get('CHROME', '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
HEADING = re.compile(r'<h([12])\b([^>]*)>(.*?)</h\1>', re.S)
METADATA = {
    '/Title': 'Pavement data platform MVP: architecture report',
    '/Subject': 'Use cases, quality attributes, C4 diagrams C1 to C3 and architecture decision records',
    '/Author': 'Continuum Infrastructure Solutions',
}


def text_of(fragment):
    t = re.sub(r'<[^>]+>', '', fragment)
    return re.sub(r'\s+', ' ', html.unescape(t)).strip()


def attr(attrs, name):
    m = re.search(name + r'="([^"]*)"', attrs)
    return m.group(1) if m else None


def toc_entries(body):
    """Headings with data-toc="1" or "2" go on the contents page; data-part starts a part label."""
    out = []
    for _level, attrs, inner in HEADING.findall(body):
        toc = attr(attrs, 'data-toc')
        if not toc:
            continue
        out.append({
            'level': int(toc), 'id': attr(attrs, 'id'), 'part': attr(attrs, 'data-part'),
            'title': text_of(inner), 'short': attr(attrs, 'data-short') or text_of(inner),
        })
    return out


def toc_html(entries, pages):
    rows = ['<nav class="toc">']
    for e in entries:
        if e['part']:
            rows.append(f'<div class="part">{html.escape(e["part"])}</div>')
        pg = pages.get(e['title'], '00')
        rows.append(
            f'<a class="l{e["level"]}" href="#{e["id"]}"><span class="t">{html.escape(e["short"])}</span>'
            f'<span class="dots"></span><span class="pg">{pg}</span></a>')
    rows.append('</nav>')
    return '\n'.join(rows)


def assemble(pages):
    """Join parts/*.html in file name order into report.html (kept next to style.css)."""
    body = '\n'.join(p.read_text() for p in sorted((ROOT / 'parts').glob('*.html')))
    entries = toc_entries(body)
    for e in entries:
        assert e['id'], f'heading without id: {e["title"]}'
    body = body.replace('<!--TOC-->', toc_html(entries, pages))
    doc = (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<title>Pavement data platform MVP: architecture report</title>'
        '<link rel="stylesheet" href="style.css"></head><body>\n' + body + '\n</body></html>')
    (ROOT / 'report.html').write_text(doc)
    return entries


def print_pdf(out):
    subprocess.run([
        CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
        '--generate-pdf-document-outline', '--run-all-compositor-stages-before-draw',
        '--virtual-time-budget=8000', f'--print-to-pdf={out}', (ROOT / 'report.html').as_uri(),
    ], check=True, capture_output=True)


def outline_pages(pdf):
    reader = pypdf.PdfReader(str(pdf))
    pages = {}

    def walk(items):
        for it in items:
            if isinstance(it, list):
                walk(it)
            else:
                title = re.sub(r'\s+', ' ', it.title).strip()
                pages.setdefault(title, reader.get_destination_page_number(it) + 1)
    walk(reader.outline)
    return pages, len(reader.pages)


def main():
    args = [a for a in sys.argv[1:] if a != '--force']
    if len(args) != 1:
        sys.exit(__doc__)
    out = Path(args[0]).resolve()
    if out.exists() and '--force' not in sys.argv:
        sys.exit(f'{out} exists. Save a new dated copy, or pass --force to replace it.')
    with tempfile.TemporaryDirectory() as tmp:
        first, second = Path(tmp) / 'pass1.pdf', Path(tmp) / 'pass2.pdf'
        entries = assemble({})
        print_pdf(first)
        pages, n1 = outline_pages(first)
        missing = [e['title'] for e in entries if e['title'] not in pages]
        if missing:
            sys.exit('headings missing from the PDF bookmarks: ' + '; '.join(missing))
        toc_pages = {e['title']: pages[e['title']] for e in entries}
        assemble(toc_pages)
        print_pdf(second)
        pages2, n2 = outline_pages(second)
        moved = [t for t, p in toc_pages.items() if pages2.get(t) != p]
        if moved or n1 != n2:
            sys.exit(f'page numbers moved between passes: {moved} ({n1} vs {n2} pages)')
        writer = pypdf.PdfWriter(clone_from=str(second))
        writer.add_metadata(METADATA)
        with open(out, 'wb') as fh:
            writer.write(fh)
    print(f'{out}: {n2} pages')
    for e in entries:
        print(f'  p{toc_pages[e["title"]]:>3}  {"  " * (e["level"] - 1)}{e["title"]}')


if __name__ == '__main__':
    main()
