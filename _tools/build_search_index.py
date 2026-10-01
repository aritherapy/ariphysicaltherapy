"""Build search-index.json for the site search (assets/ari.js).

Run from the repo root after any content change:  python3 _tools/build_search_index.py

Indexes, from the pages themselves (so the index can never say something the site doesn't):
  - every public page: H1, meta description, H2s, schema alternate names, and a slice of body text
  - every FAQ question/answer (from the FAQPage JSON-LD each page carries)
  - every condition write-up on conditions.html (by #anchor)
This folder starts with "_" so GitHub Pages (Jekyll) does not publish it.
"""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {'employees.html', 'review-display.html', 'sms-terms.html', 'privacy-policy.html'}
BODY_CHARS = 1400


def text(s):
    s = re.sub(r'<script.*?</script>|<style.*?</style>|<svg.*?</svg>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    return re.sub(r'\s+', ' ', html.unescape(s)).strip()


def main_html(s):
    """The page's own content: hero + main sections, minus nav/header/footer chrome."""
    a = s.find('</nav>')
    b = s.find('<footer')
    s = s[a + 6 if a != -1 else 0: b if b != -1 else len(s)]
    return re.sub(r'<section class="home-search".*?</section>', ' ', s, flags=re.S)   # the search box's own examples


entries = []
for f in sorted(os.listdir(ROOT)):
    if not f.endswith('.html') or f in SKIP or f.startswith('google'):
        continue
    s = open(os.path.join(ROOT, f), encoding='utf-8').read()
    if 'noindex' in (re.search(r'<meta name="robots" content="([^"]+)"', s) or [None, ''])[1]:
        continue
    body = main_html(s)
    h1 = text((re.search(r'<h1[^>]*>(.*?)</h1>', body, re.S) or [None, ''])[1])
    title = text((re.search(r'<title>(.*?)</title>', s, re.S) or [None, ''])[1])
    desc = html.unescape((re.search(r'<meta name="description" content="([^"]*)"', s) or [None, ''])[1])
    h2s = [text(h) for h in re.findall(r'<h2[^>]*>(.*?)</h2>', body, re.S)]
    keywords, faqs = [], []
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        try:
            d = json.loads(block)
        except ValueError:
            continue
        if d.get('@type') == 'FAQPage':
            faqs += [(q['name'], q['acceptedAnswer']['text']) for q in d.get('mainEntity', [])]
        about = d.get('about')
        if isinstance(about, dict):
            keywords += [about.get('name', '')] + list(about.get('alternateName', []) or [])
    page = 'home' if f == 'index.html' else f
    url = '/' if f == 'index.html' else f
    lang = {'l': 'es'} if '<html lang="es">' in s else {}   # Spanish pages; the search ranks the page's own language first
    entries.append({
        't': 'page', 'u': url, 'title': h1 or title.split('|')[0].strip(),
        'd': desc, 'k': ' '.join(k for k in keywords if k), 'h': ' · '.join(h for h in h2s if h)[:500],
        'x': text(body)[:BODY_CHARS], **lang,
    })
    for q, a in faqs:
        entries.append({'t': 'faq', 'u': url, 'title': q, 'd': a, 'k': '', 'h': '', 'x': '', **lang})

# condition write-ups on the Conditions page, one entry per #anchor
hub = open(os.path.join(ROOT, 'conditions.html'), encoding='utf-8').read()
for cid, name, summary, rest in re.findall(
        r'<div class="cond-item" id="([^"]+)"><h3>(.*?)</h3><p>(.*?)</p><div class="cond-actions">(.*?)</div></div>', hub, re.S):
    full = re.search(r'<a class="cond-link" href="([^"]+\.html)"', rest)
    target = full.group(1) if full and 'appointment' not in full.group(1) else 'conditions.html#' + cid
    entries.append({'t': 'condition', 'u': target, 'title': text(name), 'd': text(summary), 'k': '', 'h': '', 'x': ''})

# de-duplicate FAQ answers that appear on several pages: keep the FAQ page's copy, else the first
seen, out = {}, []
for e in entries:
    if e['t'] == 'faq':
        q, ans = e['title'].lower(), e['d'].lower()
        hit = seen.get(q, seen.get(ans))
        if hit is not None:
            if e['u'] == 'faq.html':
                out[hit] = e
            continue
        seen[q] = seen[ans] = len(out)
    out.append(e)

path = os.path.join(ROOT, 'search-index.json')
json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f'{len(out)} entries, {os.path.getsize(path) // 1024} KB -> search-index.json')
