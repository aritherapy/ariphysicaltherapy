"""Give assets/ari.css and assets/ari.js a new ?v= on every page, so browsers fetch the new files at once.

    python3 _tools/bump_assets.py            # version = current date-time

Run it after ANY change to ari.css or ari.js. Without it, visitors' browsers can keep the old file for up to
10 minutes (GitHub Pages cache) while already showing new page HTML, so new parts of a page can look broken.
Builders copy their head from existing pages, so newly built pages carry the current version too.
"""
import glob, os, re, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
v = sys.argv[1] if len(sys.argv) > 1 else time.strftime('%Y%m%d%H%M')
n = 0
for f in glob.glob(os.path.join(ROOT, '*.html')):
    s = open(f, encoding='utf-8').read()
    t = re.sub(r'(href|src)="assets/ari\.(css|js)(\?v=[^"]*)?"', lambda m: f'{m.group(1)}="assets/ari.{m.group(2)}?v={v}"', s)
    if t != s:
        open(f, 'w', encoding='utf-8').write(t); n += 1
print(f'ari.css / ari.js -> ?v={v} on {n} pages')
