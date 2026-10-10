"""Build one printable review packet (HTML, then PDF via headless Chrome) from built draft pages, for Deepa's clinical review.

    python3 _tools/review_packet.py --title "Round 5" --out ~/Desktop/packet.pdf slug1 slug2 ...
    python3 _tools/review_packet.py --batch 5 --conditions slugA slugB ... --out packet.pdf

Pages must already be built (build_condition.py / build_questions.py). The packet holds only the page's own
content (no header, footer or navigation), each page starting on a new sheet with an approve/changes box.
Nothing is published; the output file is meant for the reviewer only.
"""
import argparse, html, importlib.util, glob, os, re, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
CSS = '''@page{size:Letter;margin:0.55in}
body{font-family:-apple-system,"Helvetica Neue",Arial,sans-serif;color:#2B2B2B;font-size:10.5pt;line-height:1.45}
.cover h1{font-size:20pt;margin:0 0 6px}.cover p{margin:4px 0}
.page{page-break-before:always}
.ph{border-bottom:3px solid #E8630A;padding-bottom:6px;margin-bottom:10px}
.ph .n{color:#B84D09;font-weight:700;font-size:9pt;text-transform:uppercase;letter-spacing:.6px}
.ph h1{font-size:15pt;margin:2px 0}.ph .url{color:#6F6962;font-size:8.5pt}
.box{border:1.5px solid #2B2B2B;border-radius:6px;padding:8px 10px;margin:10px 0 14px;font-size:10pt}
.box .line{border-bottom:1px solid #999;height:20px;margin-top:4px}
h2{font-size:12pt;margin:14px 0 5px}h3{font-size:11pt;margin:10px 0 4px}
.check{margin:2px 0}.check-tick{color:#E8630A;margin-right:6px}
.acc-q{font-weight:700;margin-top:8px;display:block;border:0;background:none;padding:0;font:inherit;text-align:left}
.acc-t{display:none}.acc-a{margin:2px 0 6px}
.step{display:flex;gap:8px;margin:4px 0}.step-num{font-weight:700;color:#B84D09}
.callout,.page-cta,.side-card,.btn,.page-cta-btns,.med-disclaimer,.reviewed-by,.breadcrumb{display:none}
a{color:#2B2B2B;text-decoration:none}ul{margin:4px 0 4px 18px;padding:0}
table.toc{border-collapse:collapse;width:100%;font-size:9.5pt;margin-top:10px}table.toc td{border-bottom:1px solid #E0D9CE;padding:4px}
'''


def page_body(slug):
    s = open(os.path.join(ROOT, slug + '.html'), encoding='utf-8').read()
    title = html.unescape(re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S).group(1))
    title = re.sub(r'<[^>]+>', '', title)
    a, z = s.index('</nav>'), s.index('<footer')
    body = s[a + 6:z]
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S)
    body = re.sub(r'<aside.*?</aside>', '', body, flags=re.S)
    body = re.sub(r'<h1[^>]*>.*?</h1>', '', body, count=1, flags=re.S)
    return title, body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='*')
    ap.add_argument('--batch', type=int, help='add every question page tagged with this batch')
    ap.add_argument('--title', default='Pages for clinical review')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    slugs = list(a.slugs)
    if a.batch is not None:
        for f in sorted(glob.glob(os.path.join(ROOT, '_tools', 'questions', '*.py'))):
            spec = importlib.util.spec_from_file_location('m', f); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
            slugs += [p['slug'] for p in m.PAGES if p.get('batch') == a.batch]
    parts, toc = [], []
    for i, slug in enumerate(slugs, 1):
        title, body = page_body(slug)
        toc.append(f'<tr><td>{i}</td><td>{html.escape(title)}</td><td>☐ Approved &nbsp; ☐ Changes</td></tr>')
        parts.append(f'<section class="page"><div class="ph"><div class="n">Page {i} of {len(slugs)}</div><h1>{html.escape(title)}</h1>'
                     f'<div class="url">ariphysicaltherapy.com/{slug}.html</div></div>'
                     f'<div class="box">☐ Approved as written &nbsp;&nbsp; ☐ Approved with the changes marked/written here:<div class="line"></div><div class="line"></div></div>'
                     f'{body}</section>')
    cover = (f'<div class="cover"><h1>{html.escape(a.title)}</h1><p>{len(slugs)} draft pages for ariphysicaltherapy.com. '
             'They are hidden from Google until approved.</p><p>For each page, please check clinical accuracy, the warning signs, and '
             'anything that promises a result or a timeline. Tick a box, or mark changes directly on the page.</p>'
             f'<table class="toc">{"".join(toc)}</table></div>')
    doc = f'<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(a.title)}</title><style>{CSS}</style></head><body>{cover}{"".join(parts)}</body></html>'
    tmp = tempfile.mkdtemp()
    src = os.path.join(tmp, 'packet.html')
    open(src, 'w', encoding='utf-8').write(doc)
    out = os.path.abspath(os.path.expanduser(a.out))
    if os.path.exists(out):
        os.remove(out)
    prof = os.path.join(tmp, 'chrome')
    p = subprocess.Popen([CHROME, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', f'--user-data-dir={prof}',
                          f'--print-to-pdf={out}', 'file://' + src], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(90):   # headless Chrome sometimes writes the PDF and then doesn't exit
        if os.path.exists(out) and os.path.getsize(out) > 0:
            time.sleep(2)
            break
        time.sleep(1)
    p.kill()
    print(f'{out}  ({len(slugs)} pages)')


if __name__ == '__main__':
    main()
