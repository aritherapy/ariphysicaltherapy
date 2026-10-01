"""Build a condition page from a content file in _tools/conditions/.

    python3 _tools/build_condition.py hip-pain ankle-sprain-achilles-pain     # build some
    python3 _tools/build_condition.py --all                                  # build every content file
    python3 _tools/build_search_index.py                                     # then refresh site search

The page shell (head, nav, footer, scripts) is copied from SHELL, a live condition page, so
header/footer changes made across the site carry over. Each content file defines PAGE (a dict).

  PAGE['reviewed'] = None           -> DRAFT: robots noindex, no "Clinically reviewed by" line.
  PAGE['reviewed'] = '2026-10-02'   -> LIVE: indexable, reviewedBy/lastReviewed in schema.
  PAGE['clinical_review'] = False   -> live without the "Clinically reviewed by" line (owner-approved, non-clinical pages).
  PAGE['lang'] = 'es', PAGE['en'] = '<english-slug>'  -> a Spanish page (spanish.py), linked to its English version.
  PAGE['callout'] = False           -> no "No referral needed" box (e.g. workers' comp); optional PAGE['callout_html'].
Clinical content goes live only after Deepa has reviewed it. After going live, also add the page
to sitemap.xml and llms.txt.
"""
import html, importlib.util, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spanish   # Spanish phrases and shell; a content file with PAGE['lang'] = 'es' builds a Spanish page

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

EN = {
    'lang': 'en', 'in_language': 'en-US',
    'hub': 'conditions.html', 'hub_name': 'Conditions We Treat', 'form': 'appointment.html',
    'request': 'Request an Evaluation',
    'signs_h': 'Does this sound like you?',
    'steps_h': 'What treatment at ARI looks like',
    'red_h': 'When to see a doctor first',
    'red_intro': 'See a doctor promptly if you have:',
    'disclaimer': 'This page is general information, not a diagnosis. If you have symptoms, a licensed clinician should evaluate you.',
    'side_h': 'Start with an evaluation',
    'side_tail': 'Request an evaluation and we will help you take the first step, usually within one business day.',
    'or_call': 'or call',
    'related_h': 'Related',
    'all_conditions': 'All conditions we treat',
    'reviewed': lambda reviewer, y, m: (f'<p class="reviewed-by">Clinically reviewed by <a href="about.html">{reviewer}</a>, board-certified '
                                        f'Orthopedic Certified Specialist &middot; Reviewed {MONTHS[int(m) - 1]} {y}</p>'),
    'clinic_line': CLINIC_LINE, 'direct_access': DIRECT_ACCESS, 'referral_faq': REFERRAL_FAQ, 'page_cta': PAGE_CTA,
}


def strings(p):
    return spanish.ES if p.get('lang') == 'es' else EN


def load(slug):
    spec = importlib.util.spec_from_file_location(slug, os.path.join(CONTENT, slug + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PAGE


def jsonld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, indent=2, ensure_ascii=False) + '\n    </script>'


def body(p):
    L = strings(p)
    checks = ''.join(f'<div class="check"><span class="check-tick">&#10003;</span><span>{c}</span></div>' for c in p['signs'])
    steps = ''.join(f'<div class="step"><span class="step-num">{i}</span><div><b>{t}</b><p>{d}</p></div></div>'
                    for i, (t, d) in enumerate(p['steps'], 1))
    flags = ''.join(f'<li>{f}</li>' for f in p['red_flags'])
    faqs = p['faqs'] + ([L['referral_faq']] if p.get('referral_faq', True) else [])
    acc = ''.join(
        f'<div class="acc-item"><button class="acc-q" aria-expanded="{"true" if i == 0 else "false"}">{html.escape(q)}'
        f'<span class="acc-t">{"&minus;" if i == 0 else "+"}</span></button><div class="acc-a">{html.escape(a)}</div></div>'
        for i, (q, a) in enumerate(faqs))
    related = ''.join(f'<a href="{u}">{t} <span>&rarr;</span></a>' for t, u in p['related'])
    reviewed = ''
    if p.get('reviewed') and p.get('clinical_review', True):
        y, m, _ = p['reviewed'].split('-')
        reviewed = L['reviewed'](REVIEWER, y, m)
    sections = ''.join(f'<h2>{h}</h2>{c}' for h, c in p['why'])
    return f'''</nav>
<section class="page-hero"><div class="page-hero-inner">
  <p class="breadcrumb"><a href="{L['hub']}">{L['hub_name']}</a> &nbsp;/&nbsp; {p['crumb']}</p>
  <p class="eyebrow">{p['eyebrow']}</p><h1>{p['h1']} <span style="color:var(--orange)">Bakersfield</span></h1><p class="lead">{p['lead']}</p>
  <div style="margin-top:30px"><a href="{L['form']}" class="btn btn-primary">{L['request']}</a></div>
</div></section>
<section class="section"><div class="section-inner detail">
  <div class="prose">
    <p class="svc-lead" style="font-size:17px;line-height:1.75;margin-bottom:8px">{p['answer']}</p>
<h2>{L['signs_h']}</h2><div class="checks">{checks}</div>
{sections}
<h2>{L['steps_h']}</h2><div class="steps">{steps}</div>
{L['direct_access'] if p.get('callout', True) else p.get('callout_html', '')}
<h2>{L['red_h']}</h2>
<p>{p.get('red_flags_intro', L['red_intro'])}</p>
<ul class="plain-list">{flags}</ul>
{L['clinic_line']}
<h2>{p['faq_title']}</h2><div class="acc">{acc}</div>{L['page_cta']}<p class="med-disclaimer">{L['disclaimer']}</p>{reviewed}
  </div>
  <aside class="detail-side">
    <div class="side-card"><h3>{L['side_h']}</h3><p>{p['side']} {L['side_tail']}</p>
      <a href="{L['form']}" class="btn btn-primary">{L['request']}</a>
      <span class="or">{L['or_call']} <a href="tel:6612828584">(661) 282-8584</a></span></div>
    <div class="side-list"><h4>{L['related_h']}</h4>{related}<a href="{L['hub']}">{L['all_conditions']} <span>&rarr;</span></a></div>
  </aside>
</div></section>
'''


def build(slug):
    p = load(slug)
    L = strings(p)
    url = SITE + slug + '.html'
    s = open(os.path.join(ROOT, SHELL), encoding='utf-8').read()
    if L is spanish.ES:
        s = spanish.es_shell(s, url, SITE + p['en'] + '.html' if p.get('en') else None)
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
        'name': re.sub(r'<[^>]+>', '', p['h1']) + ' Bakersfield', 'description': p['description'], 'inLanguage': L['in_language'],
        'isPartOf': {'@type': 'WebSite', 'name': 'ARI Physical Therapy', 'url': SITE},
        'publisher': {'@id': SITE + '#clinic'},
        'audience': {'@type': 'MedicalAudience', 'audienceType': 'Patient'},
        'about': {'@type': 'MedicalCondition', 'name': p['condition'], 'alternateName': p['alt_names'],
                  'possibleTreatment': {'@type': 'MedicalTherapy', 'name': p['therapy']}},
        'breadcrumb': {'@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': L['hub_name'], 'item': SITE + L['hub']},
            {'@type': 'ListItem', 'position': 2, 'name': html.unescape(p['crumb']), 'item': url}]},
    }
    if p.get('reviewed') and p.get('clinical_review', True):
        page['lastReviewed'] = p['reviewed']
        page['reviewedBy'] = {'@id': SITE + 'about.html#deepa'}
    faqs = p['faqs'] + ([L['referral_faq']] if p.get('referral_faq', True) else [])
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
