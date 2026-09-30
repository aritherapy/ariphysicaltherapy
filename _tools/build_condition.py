"""Build a condition page from a content file in _tools/conditions/.

    python3 _tools/build_condition.py hip-pain ankle-sprain-achilles-pain     # build some
    python3 _tools/build_condition.py --all                                  # build every content file
    python3 _tools/build_search_index.py                                     # then refresh site search

The page shell (head, nav, footer, scripts) is copied from SHELL, a live condition page, so
header/footer changes made across the site carry over. Each content file defines PAGE (a dict).

  PAGE['reviewed'] = None           -> DRAFT: robots noindex, no "Clinically reviewed by" line.
  PAGE['reviewed'] = '2026-10-02'   -> LIVE: indexable, reviewedBy/lastReviewed in schema.
Clinical content goes live only after Deepa has reviewed it. After going live, also add the page
to sitemap.xml and llms.txt.
"""
import html, importlib.util, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, '_tools', 'conditions')
SHELL = 'knee-pain-arthritis.html'
SITE = 'https://ariphysicaltherapy.com/'
REVIEWER = 'Deepa Konnur, PT, MPT, OCS'
PAGE_CTA = open(os.path.join(ROOT, '_tools', 'page_cta.html'), encoding='utf-8').read().strip()   # shared end-of-page next step
MONTHS = 'January February March April May June July August September October November December'.split()

CLINIC_LINE = ('<h2>Why patients choose ARI</h2><p>Care at ARI is always <strong>one-on-one and in person</strong> with a '
               'licensed physical therapist at our Bakersfield clinic: 8200 Stockdale Hwy, Suite B2, in the Town &amp; Country '
               'Village center next to Trader Joe\'s. Our clinic director, Deepa Konnur, PT, MPT, OCS, is a board-certified '
               'Orthopedic Certified Specialist. We accept most private insurance plans and Medicare, and our team speaks '
               'English, Spanish, and Hindi.</p>')
DIRECT_ACCESS = ('<div class="callout"><strong>No referral needed to start.</strong> In California, you can see a physical '
                 'therapist directly for up to 12 visits or 45 days, whichever comes first. Some insurance plans still require a '
                 'referral for coverage; call us at <a href="tel:6612828584">(661) 282-8584</a> and we\'ll help you check.</div>')
REFERRAL_FAQ = ("Do I need a doctor's referral for physical therapy in California?",
                "No. In California you can see a physical therapist directly for up to 12 visits or 45 days, whichever comes "
                "first. Some insurance plans still require a referral for coverage, so call us at (661) 282-8584 and we'll help you check.")


def load(slug):
    spec = importlib.util.spec_from_file_location(slug, os.path.join(CONTENT, slug + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PAGE


def jsonld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, indent=2, ensure_ascii=False) + '\n    </script>'


def body(p):
    checks = ''.join(f'<div class="check"><span class="check-tick">&#10003;</span><span>{c}</span></div>' for c in p['signs'])
    steps = ''.join(f'<div class="step"><span class="step-num">{i}</span><div><b>{t}</b><p>{d}</p></div></div>'
                    for i, (t, d) in enumerate(p['steps'], 1))
    flags = ''.join(f'<li>{f}</li>' for f in p['red_flags'])
    faqs = p['faqs'] + ([REFERRAL_FAQ] if p.get('referral_faq', True) else [])
    acc = ''.join(
        f'<div class="acc-item"><button class="acc-q" aria-expanded="{"true" if i == 0 else "false"}">{html.escape(q)}'
        f'<span class="acc-t">{"&minus;" if i == 0 else "+"}</span></button><div class="acc-a">{html.escape(a)}</div></div>'
        for i, (q, a) in enumerate(faqs))
    related = ''.join(f'<a href="{u}">{t} <span>&rarr;</span></a>' for t, u in p['related'])
    reviewed = ''
    if p.get('reviewed'):
        y, m, _ = p['reviewed'].split('-')
        reviewed = (f'<p class="reviewed-by">Clinically reviewed by <a href="about.html">{REVIEWER}</a>, board-certified '
                    f'Orthopedic Certified Specialist &middot; Reviewed {MONTHS[int(m) - 1]} {y}</p>')
    sections = ''.join(f'<h2>{h}</h2>{c}' for h, c in p['why'])
    return f'''</nav>
<section class="page-hero"><div class="page-hero-inner">
  <p class="breadcrumb"><a href="conditions.html">Conditions We Treat</a> &nbsp;/&nbsp; {p['crumb']}</p>
  <p class="eyebrow">{p['eyebrow']}</p><h1>{p['h1']} <span style="color:var(--orange)">Bakersfield</span></h1><p class="lead">{p['lead']}</p>
  <div style="margin-top:30px"><a href="appointment.html" class="btn btn-primary">Request an Evaluation</a></div>
</div></section>
<section class="section"><div class="section-inner detail">
  <div class="prose">
    <p class="svc-lead" style="font-size:17px;line-height:1.75;margin-bottom:8px">{p['answer']}</p>
<h2>Does this sound like you?</h2><div class="checks">{checks}</div>
{sections}
<h2>What treatment at ARI looks like</h2><div class="steps">{steps}</div>
{DIRECT_ACCESS}
<h2>When to see a doctor first</h2>
<p>{p.get('red_flags_intro', 'See a doctor promptly if you have:')}</p>
<ul class="plain-list">{flags}</ul>
{CLINIC_LINE}
<h2>{p['faq_title']}</h2><div class="acc">{acc}</div>{PAGE_CTA}<p class="med-disclaimer">This page is general information, not a diagnosis. If you have symptoms, a licensed clinician should evaluate you.</p>{reviewed}
  </div>
  <aside class="detail-side">
    <div class="side-card"><h3>Start with an evaluation</h3><p>{p['side']} Request an evaluation and we will help you take the first step, usually within one business day.</p>
      <a href="appointment.html" class="btn btn-primary">Request an Evaluation</a>
      <span class="or">or call <a href="tel:6612828584">(661) 282-8584</a></span></div>
    <div class="side-list"><h4>Related</h4>{related}<a href="conditions.html">All conditions we treat <span>&rarr;</span></a></div>
  </aside>
</div></section>
'''


def build(slug):
    p = load(slug)
    url = SITE + slug + '.html'
    s = open(os.path.join(ROOT, SHELL), encoding='utf-8').read()
    title, desc = html.escape(p['title']), html.escape(p['description'])
    assert len(p['description']) <= 160, f'{slug}: description is {len(p["description"])} chars (max 160)'
    s = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', s)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', s)
    s = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', s)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{title}">', s)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{desc}">', s)
    s = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{desc}">', s)
    robots = 'index, follow' if p.get('reviewed') else 'noindex, follow'
    s = re.sub(r'<meta name="robots" content="[^"]*">', f'<meta name="robots" content="{robots}">', s)

    page = {
        '@context': 'https://schema.org', '@type': 'MedicalWebPage', '@id': url + '#page', 'url': url,
        'name': re.sub(r'<[^>]+>', '', p['h1']) + ' Bakersfield', 'description': p['description'], 'inLanguage': 'en-US',
        'isPartOf': {'@type': 'WebSite', 'name': 'ARI Physical Therapy', 'url': SITE},
        'publisher': {'@id': SITE + '#clinic'},
        'audience': {'@type': 'MedicalAudience', 'audienceType': 'Patient'},
        'about': {'@type': 'MedicalCondition', 'name': p['condition'], 'alternateName': p['alt_names'],
                  'possibleTreatment': {'@type': 'MedicalTherapy', 'name': p['therapy']}},
        'breadcrumb': {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Conditions We Treat', 'item': SITE + 'conditions.html'},
            {'@type': 'ListItem', 'position': 2, 'name': html.unescape(p['crumb']), 'item': url}]},
    }
    if p.get('reviewed'):
        page['lastReviewed'] = p['reviewed']
        page['reviewedBy'] = {'@id': SITE + 'about.html#deepa'}
    faqs = p['faqs'] + ([REFERRAL_FAQ] if p.get('referral_faq', True) else [])
    faq = {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]}
    blocks = re.findall(r'<script type="application/ld\+json">.*?</script>', s, re.S)
    for b in blocks:
        if '"MedicalWebPage"' in b:
            s = s.replace(b, jsonld(page))
        elif '"FAQPage"' in b:
            s = s.replace(b, jsonld(faq))

    a, z = s.index('</nav>\n'), s.index('<footer')
    s = s[:a] + body(p) + s[z:]
    open(os.path.join(ROOT, slug + '.html'), 'w', encoding='utf-8').write(s)
    print(f"{slug}.html  {'LIVE' if p.get('reviewed') else 'DRAFT (noindex)'}  title {len(p['title'])} / desc {len(p['description'])} chars")


if __name__ == '__main__':
    args = sys.argv[1:]
    if args == ['--all']:
        args = sorted(f[:-3] for f in os.listdir(CONTENT) if f.endswith('.py') and not f.startswith('_'))
    if not args:
        sys.exit(__doc__)
    for slug in args:
        build(slug)
