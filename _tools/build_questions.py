"""Build the "Patient Questions" library: one page per question, plus the ask-ari.html index.

    python3 _tools/build_questions.py        # builds every question page and ask-ari.html
    python3 _tools/build_search_index.py     # then refresh site search

Content lives in _tools/questions/*.py; each file defines GROUP (key, label) and PAGES (a list of dicts).
Question pages sit outside the main menu. Visitors reach them through site search, the ask-ari.html
index, and "Related questions" links. Google and AI assistants reach them through sitemap.xml and llms.txt.

  page['reviewed'] = None           -> DRAFT: noindex, no "Clinically reviewed by" line.
  page['reviewed'] = '2026-10-05'   -> LIVE. After release, add it to sitemap.xml and llms.txt.
While no page is reviewed, ask-ari.html is itself a noindex draft listing every question (Deepa's review
index). Once any page is live, it becomes indexable and lists only the live pages.
Release a few reviewed pages a week rather than all at once.
"""
import html, importlib.util, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, '_tools', 'questions')
SHELL = 'knee-pain-arthritis.html'
SITE = 'https://ariphysicaltherapy.com/'
INDEX = 'ask-ari.html'
REVIEWER = 'Deepa Konnur, PT, MPT, OCS'
PAGE_CTA = open(os.path.join(ROOT, '_tools', 'page_cta.html'), encoding='utf-8').read().strip()   # shared end-of-page next step
MONTHS = 'January February March April May June July August September October November December'.split()
ORDER = ['back', 'neck', 'shoulder-hand', 'knee', 'hip', 'foot-ankle', 'pelvic', 'balance', 'bone-surgery', 'starting']

ARI_LINE = ('At ARI Physical Therapy in Bakersfield, every visit is one-on-one and in person with a licensed physical '
            'therapist, and our clinic director, Deepa Konnur, PT, MPT, OCS, is a board-certified Orthopedic Certified '
            'Specialist. We accept most private insurance plans and Medicare, and our team speaks English, Spanish, and Hindi.')
DIRECT_ACCESS = ('<div class="callout"><strong>No referral needed to start.</strong> In California, you can see a physical '
                 'therapist directly for up to 12 visits or 45 days, whichever comes first. Some insurance plans still require a '
                 'referral for coverage; call us at <a href="tel:6612828584">(661) 282-8584</a> and we\'ll help you check.</div>')


def load_all():
    groups = {}
    for f in sorted(os.listdir(CONTENT)):
        if not f.endswith('.py') or f.startswith('_'):
            continue
        spec = importlib.util.spec_from_file_location(f[:-3], os.path.join(CONTENT, f))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for key, label in mod.GROUPS:
            groups.setdefault(key, {'label': label, 'pages': []})
        for p in mod.PAGES:
            groups[p['group']]['pages'].append(p)
    return [(k, groups[k]) for k in ORDER if k in groups]


def plain(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s))


def jsonld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, indent=2, ensure_ascii=False) + '\n    </script>'


def shell_with(url, title, desc, robots, blocks, body):
    s = open(os.path.join(ROOT, SHELL), encoding='utf-8').read()
    t, d = html.escape(title), html.escape(desc)
    s = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', s)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', s)
    s = re.sub(r'<title>.*?</title>', f'<title>{t}</title>', s)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{t}">', s)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{d}">', s)
    s = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{d}">', s)
    s = re.sub(r'<meta name="robots" content="[^"]*">', f'<meta name="robots" content="{robots}">', s)
    old = [b for b in re.findall(r'\s*<script type="application/ld\+json">.*?</script>', s, re.S)
           if '"MedicalWebPage"' in b or '"FAQPage"' in b]
    s = s.replace(old[0], '\n    ' + '\n    '.join(jsonld(b) for b in blocks))
    for b in old[1:]:
        s = s.replace(b, '')
    a, z = s.index('</nav>\n'), s.index('<footer')
    return s[:a] + body + s[z:]


def side(links):
    items = ''.join(f'<a href="{u}">{t} <span>&rarr;</span></a>' for t, u in links)
    return f'''  <aside class="detail-side">
    <div class="side-card"><h3>Talk to a physical therapist</h3><p>Care at ARI is one-on-one with a licensed physical therapist. Request an evaluation and we will help you take the first step, usually within one business day.</p>
      <a href="appointment.html" class="btn btn-primary">Request an Evaluation</a>
      <span class="or">or call <a href="tel:6612828584">(661) 282-8584</a></span></div>
    <div class="side-list"><h4>Related</h4>{items}</div>
  </aside>'''


def build_page(p, label, siblings):
    slug, url = p['slug'], SITE + p['slug'] + '.html'
    assert len(p['description']) <= 160, f"{slug}: description {len(p['description'])} chars"
    sections = ''.join(f'<h2>{h}</h2>{c}' for h, c in p['sections'])
    flags = ''
    if p.get('red_flags'):
        items = ''.join(f'<li>{f}</li>' for f in p['red_flags'])
        flags = f'<h2>When to see a doctor</h2><p>{p.get("red_intro", "See a doctor promptly if you have:")}</p><ul class="plain-list">{items}</ul>'
    guide = ''
    if p.get('guide'):
        guide = f'<p><strong><a href="{p["guide"][1]}">Read our full guide: {p["guide"][0]} &rarr;</a></strong></p>'
    related = ''.join(f'<li><a href="{q["slug"]}.html">{q["q"]}</a></li>' for q in siblings)
    related = f'<h2>Related questions</h2><ul class="plain-list">{related}<li><a href="{INDEX}">All patient questions</a></li></ul>'
    reviewed = ''
    if p.get('reviewed'):
        y, m, _ = p['reviewed'].split('-')
        reviewed = (f'<p class="reviewed-by">Clinically reviewed by <a href="about.html">{REVIEWER}</a>, board-certified '
                    f'Orthopedic Certified Specialist &middot; Reviewed {MONTHS[int(m) - 1]} {y}</p>')
    callout = DIRECT_ACCESS if p.get('callout', True) else ''
    body = f'''</nav>
<section class="page-hero"><div class="page-hero-inner">
  <p class="breadcrumb"><a href="{INDEX}">Patient Questions</a> &nbsp;/&nbsp; {p['crumb']}</p>
  <p class="eyebrow">{label}</p><h1>{p['q']}</h1><p class="lead">{p['short']}</p>
  <div style="margin-top:30px"><a href="appointment.html" class="btn btn-primary">Request an Evaluation</a></div>
</div></section>
<section class="section"><div class="section-inner detail">
  <div class="prose">
{sections}
{flags}
<h2>How physical therapy at ARI can help</h2>{p['pt']}<p>{ARI_LINE}</p>{guide}
{callout}
{related}
{PAGE_CTA}<p class="med-disclaimer">This page is general information, not a diagnosis. If you have symptoms, a licensed clinician should evaluate you.</p>{reviewed}
  </div>
{side(([p['guide']] if p.get('guide') else []) + [('All patient questions', INDEX), ('Conditions we treat', 'conditions.html')])}
</div></section>
'''
    page = {
        '@context': 'https://schema.org', '@type': 'MedicalWebPage', '@id': url + '#page', 'url': url,
        'name': plain(p['q']), 'description': p['description'], 'inLanguage': 'en-US',
        'isPartOf': {'@type': 'WebSite', 'name': 'ARI Physical Therapy', 'url': SITE},
        'publisher': {'@id': SITE + '#clinic'},
        'audience': {'@type': 'MedicalAudience', 'audienceType': 'Patient'},
        'breadcrumb': {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Patient Questions', 'item': SITE + INDEX},
            {'@type': 'ListItem', 'position': 2, 'name': plain(p['crumb']), 'item': url}]},
    }
    if p.get('about'):
        page['about'] = {'@type': 'MedicalCondition', 'name': p['about']}
    if p.get('reviewed'):
        page['lastReviewed'] = p['reviewed']
        page['reviewedBy'] = {'@id': SITE + 'about.html#deepa'}
    faq = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': plain(p['q']), 'acceptedAnswer': {'@type': 'Answer', 'text': plain(p['short'])}}]}
    robots = 'index, follow' if p.get('reviewed') else 'noindex, follow'
    out = shell_with(url, p['title'], p['description'], robots, [page, faq], body)
    open(os.path.join(ROOT, slug + '.html'), 'w', encoding='utf-8').write(out)
    return f"{slug}.html  {'LIVE' if p.get('reviewed') else 'draft'}  title {len(p['title'])}"


def build_index(groups):
    live = any(p.get('reviewed') for _, g in groups for p in g['pages'])
    url = SITE + INDEX
    blocks, parts = '', []
    for key, g in groups:
        pages = [p for p in g['pages'] if p.get('reviewed') or not live]
        if not pages:
            continue
        items = ''.join(f'<div class="cond-item" id="{p["slug"]}-q"><h3><a href="{p["slug"]}.html">{p["q"]}</a></h3><p>{p["short"]}</p></div>'
                        for p in pages)
        blocks += f'<h2 id="{key}">{g["label"]}</h2>{items}'
        parts += [{'@type': 'MedicalWebPage', 'name': plain(p['q']), 'url': SITE + p['slug'] + '.html'} for p in pages]
    body = f'''</nav>
<section class="page-hero"><div class="page-hero-inner">
  <p class="eyebrow">Patient Questions</p><h1>Your Questions About Pain, Answered</h1><p class="lead">Plain-English answers to the questions our patients ask most, from back pain and dizziness to bladder leaks and getting started with physical therapy.</p>
  <div style="margin-top:30px"><a href="appointment.html" class="btn btn-primary">Request an Evaluation</a></div>
</div></section>
<section class="section"><div class="section-inner detail">
  <div class="prose">
{blocks}
<p class="med-disclaimer">These pages are general information, not a diagnosis. If you have symptoms, a licensed clinician should evaluate you.</p>
  </div>
{side([('Conditions we treat', 'conditions.html'), ('Frequently asked questions', 'faq.html'), ('Our services', 'services.html')])}
</div></section>
'''
    page = {'@context': 'https://schema.org', '@type': 'CollectionPage', '@id': url + '#page', 'url': url,
            'name': 'Patient Questions About Pain and Physical Therapy', 'inLanguage': 'en-US',
            'isPartOf': {'@type': 'WebSite', 'name': 'ARI Physical Therapy', 'url': SITE},
            'publisher': {'@id': SITE + '#clinic'}, 'hasPart': parts}
    out = shell_with(url, 'Patient Questions About Pain & Physical Therapy | ARI PT',
                     'Plain-English answers to common questions about back, neck, joint and pelvic pain, dizziness, and starting physical therapy, from ARI in Bakersfield.',
                     'index, follow' if live else 'noindex, follow', [page], body)
    open(os.path.join(ROOT, INDEX), 'w', encoding='utf-8').write(out)
    return f"{INDEX}  {'LIVE' if live else 'draft (review index)'}  {len(parts)} questions"


if __name__ == '__main__':
    groups = load_all()
    for key, g in groups:
        for p in g['pages']:
            sib = [q for q in g['pages'] if q is not p and (q.get('reviewed') or not p.get('reviewed'))][:4]   # live pages link only to live pages
            print(build_page(p, g['label'], sib))
    print(build_index(groups))
