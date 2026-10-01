"""Release clinically reviewed draft pages in one step.

    python3 _tools/release.py --list                                  # what's draft, what's live
    python3 _tools/release.py hip-pain leaking-urine-when-sneezing    # release these, reviewed today
    python3 _tools/release.py --date 2026-10-05 hip-pain ...          # with a specific review date
    python3 _tools/release.py --sync                                  # redo the cross-links only
    python3 _tools/release.py --batch 3 --date 2026-10-05             # release every draft question tagged 'batch': 3

For each slug (a condition page in _tools/conditions/ or a question in _tools/questions/) it:
  1. sets the page's 'reviewed' date in its content file (the page becomes indexable and gets
     Deepa's "Clinically reviewed by" line),
  2. rebuilds the page(s) and the ask-ari.html index,
  3. adds the page to sitemap.xml and llms.txt, and condition pages to the conditions.html schema,
  4. links the matching checklist phrases on service pages (each content file's 'links_from'),
  5. once any question is live: adds "Patient Questions" to every page's footer, and a
     "Common questions" list (live questions only) to the matching condition pages,
  6. Spanish pages ('lang': 'es'): go into the sitemap and the llms.txt "En español" section instead of the English
     conditions list; releasing the first one also puts the Spanish homepage, hub and form live. Once any is live,
     every English page gets an "Español" link in the top bar (to its own Spanish version when there is one), the
     footer gets "En español", and paired pages get hreflang links to each other,
  7. refreshes the site search index.
It never commits or pushes. Review `git diff`, then commit, push, and request indexing in Search Console.
Only release pages Deepa has actually reviewed.
"""
import argparse, datetime, glob, html, importlib.util, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, '_tools'))
import spanish
SITE = 'https://ariphysicaltherapy.com/'
TOOLS = os.path.join(ROOT, '_tools')
REL_START, REL_END = '<!-- ask-ari:related -->', '<!-- /ask-ari:related -->'
FOOT_LINK = '<a href="ask-ari.html">Patient Questions</a><a href="'   # footer: directly followed by another link (the breadcrumb on question pages is followed by a slash)


def p(*parts):
    return os.path.join(ROOT, *parts)


def load(path):
    spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def conditions():
    out = {}
    for f in sorted(glob.glob(p('_tools', 'conditions', '*.py'))):
        if not os.path.basename(f).startswith('_'):
            out[os.path.basename(f)[:-3]] = (f, load(f).PAGE)
    return out


def questions():
    out = {}
    for f in sorted(glob.glob(p('_tools', 'questions', '*.py'))):
        if not os.path.basename(f).startswith('_'):
            for q in load(f).PAGES:
                out[q['slug']] = (f, q)
    return out


def plain(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s))


def set_reviewed(path, slug, date, is_question):
    s = open(path, encoding='utf-8').read()
    if is_question:
        # slug, group and reviewed sit on the same line in the question files
        pat = re.compile(r"^(.*'slug': '" + re.escape(slug) + r"'.*'reviewed': )(None|'[\d-]+')", re.M)
    else:
        pat = re.compile(r"^(\s*'reviewed': )(None|'[\d-]+')", re.M)
    s2, n = pat.subn(lambda m: m.group(1) + repr(date), s, count=1)
    if n != 1:
        sys.exit(f"Couldn't find the 'reviewed' field for {slug} in {path}")
    open(path, 'w', encoding='utf-8').write(s2)


def sitemap_add(urls, date):
    path = p('sitemap.xml')
    s = open(path, encoding='utf-8').read()
    for u in urls:
        loc = f'<loc>{SITE}{u}</loc>'
        if loc in s:
            s = re.sub(re.escape(loc) + r'<lastmod>[^<]*</lastmod>', f'{loc}<lastmod>{date}</lastmod>', s)
        else:
            s = s.replace('</urlset>', f'  <url>{loc}<lastmod>{date}</lastmod></url>\n</urlset>')
    open(path, 'w', encoding='utf-8').write(s)


def llms_add(cond_items, live_questions):
    """Append new condition pages; rebuild the Patient questions section from every live question."""
    path = p('llms.txt')
    s = open(path, encoding='utf-8').read()
    lines = [f'- [{name}]({SITE}{slug}.html)' for slug, name in cond_items if f'{SITE}{slug}.html' not in s]
    if lines:
        i = s.index('## Conditions we treat')
        j = s.find('\n\n## ', i + 1)   # end of that section
        s = s[:j] + '\n' + '\n'.join(lines) + s[j:]
    if live_questions:
        head = '## Patient questions'
        section = (f'{head}\n\nPlain-English answers to common patient questions, clinically reviewed by Deepa Konnur, '
                   f'PT, MPT, OCS. Index: {SITE}ask-ari.html\n\n'
                   + '\n'.join(f'- [{name}]({SITE}{slug}.html)' for slug, name in live_questions))
        if head in s:
            i = s.index(head)
            j = s.find('\n\n## ', i + 1)
            s = s[:i] + section + (s[j:] if j != -1 else '\n')
        else:
            s = s.replace('\n\n## More', '\n\n' + section + '\n\n## More', 1)
    open(path, 'w', encoding='utf-8').write(s)


FOOT_ES = f'<a href="{spanish.ES_HOME}" lang="es" hreflang="es">En español</a>'
ES_CORE = {'index.html': spanish.ES_HOME, 'conditions.html': spanish.ES_HUB, 'appointment.html': spanish.ES_FORM}


def llms_spanish(cs):
    """Rebuild the "En español" section of llms.txt from the live Spanish pages."""
    live = [(slug, plain(pg['crumb'])) for slug, (_, pg) in cs.items() if pg.get('lang') == 'es' and pg.get('reviewed')]
    if not live:
        return
    path = p('llms.txt')
    s = open(path, encoding='utf-8').read()
    head = '## En español'
    section = (f'{head}\n\nSpanish-language pages for Spanish-speaking patients (ARI has Spanish-speaking staff).\n\n'
               f'- [Terapia física en Bakersfield (inicio)]({SITE}{spanish.ES_HOME})\n'
               f'- [Afecciones que tratamos]({SITE}{spanish.ES_HUB})\n'
               f'- [Solicitar una cita]({SITE}{spanish.ES_FORM})\n'
               + '\n'.join(f'- [{name}]({SITE}{slug}.html)' for slug, name in live))
    if head in s:
        i = s.index(head)
        j = s.find('\n\n## ', i + 1)
        s = s[:i] + section + (s[j:] if j != -1 else '\n')
    else:
        s = s.replace('\n\n## More', '\n\n' + section + '\n\n## More', 1)
    open(path, 'w', encoding='utf-8').write(s)


def sync_spanish(cs):
    """Language switch + hreflang on English pages, once any Spanish page is live. Idempotent."""
    pairs = {pg['en'] + '.html': slug + '.html' for slug, (_, pg) in cs.items()
             if pg.get('lang') == 'es' and pg.get('reviewed') and pg.get('en')}
    if not pairs:
        return 0
    pairs.update(ES_CORE)
    n = 0
    for f in glob.glob(p('*.html')):
        name = os.path.basename(f)
        s = open(f, encoding='utf-8').read()
        if '<html lang="en">' not in s or 'class="top-bar-left"' not in s:
            continue
        s2 = spanish.add_lang_link(s, pairs.get(name, spanish.ES_HOME), 'es')
        if name in pairs:
            canon = re.search(r'<link rel="canonical" href="([^"]*)">', s2).group(1)
            s2 = spanish.en_alternate(s2, canon, SITE + pairs[name])
        if 'class="foot-links"' in s2 and FOOT_ES not in s2:
            s2 = s2.replace('<a href="appointment.html">Book an Appointment</a>\n    </div></div>',
                            FOOT_ES + '<a href="appointment.html">Book an Appointment</a>\n    </div></div>', 1)
        if s2 != s:
            open(f, 'w', encoding='utf-8').write(s2)
            n += 1
    return n


def hub_schema_add(cond_items):
    path = p('conditions.html')
    s = open(path, encoding='utf-8').read()
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        d = json.loads(block)
        if d.get('@type') != 'CollectionPage':
            continue
        urls = {x.get('url') for x in d.get('hasPart', [])}
        for slug, name, condition in cond_items:
            if SITE + slug + '.html' not in urls:
                d.setdefault('hasPart', []).append({'@type': 'MedicalWebPage', 'name': name, 'url': SITE + slug + '.html'})
                if isinstance(d.get('about'), list):
                    d['about'].append({'@type': 'MedicalCondition', 'name': condition})
        s = s.replace(block, '\n' + json.dumps(d, indent=2, ensure_ascii=False) + '\n    ')
        break
    open(path, 'w', encoding='utf-8').write(s)


def sync_links(qs):
    live = [(slug, q) for slug, (_, q) in qs.items() if q.get('reviewed')]
    if not live:
        return 0, 0
    # footer link on every page
    footer = 0
    for f in glob.glob(p('*.html')):
        s = open(f, encoding='utf-8').read()
        if 'class="foot-links"' in s and FOOT_LINK not in s:
            s = s.replace('<a href="appointment.html">Book an Appointment</a>\n    </div></div>',
                          '<a href="ask-ari.html">Patient Questions</a><a href="appointment.html">Book an Appointment</a>\n    </div></div>', 1)
            if FOOT_LINK in s:
                open(f, 'w', encoding='utf-8').write(s)
                footer += 1
    # "Common questions" on the condition page each live question points to
    by_page = {}
    for slug, q in live:
        if q.get('guide'):
            by_page.setdefault(q['guide'][1], []).append(q)
    pages = 0
    for f in glob.glob(p('*.html')):
        name = os.path.basename(f)
        s = open(f, encoding='utf-8').read()
        s = re.sub(re.escape(REL_START) + '.*?' + re.escape(REL_END), '', s, flags=re.S)
        # condition pages: just above the end-of-page next step; service pages: above "Related services"
        anchor = next((a for a in ('<div class="page-cta">', '<h2>Related services</h2>') if a in s), None)
        if name in by_page and anchor:
            items = ''.join(f'<li><a href="{q["slug"]}.html">{q["q"]}</a></li>' for q in by_page[name][:6])
            block = f'{REL_START}<h2>Common questions</h2><ul class="plain-list">{items}</ul>{REL_END}'
            s = s.replace(anchor, block + anchor, 1)
            pages += 1
        if s != open(f, encoding='utf-8').read():
            open(f, 'w', encoding='utf-8').write(s)
    return footer, pages


CHECK_ITEM = re.compile(r'(<div class="check"><span class="check-tick">&#10003;</span><span>)(.*?)(</span></div>)', re.S)


def link_phrase(inner, slug, phrase):
    """Wrap the first unlinked occurrence of phrase in a checklist line's HTML; existing links are left alone."""
    parts = re.split(r'(<a\b.*?</a>)', inner, flags=re.S)
    for i, part in enumerate(parts):
        if not part.startswith('<a') and phrase in part:
            parts[i] = part.replace(phrase, f'<a href="{slug}.html">{phrase}</a>', 1)
            return ''.join(parts)
    return inner


def link_mentions(cs):
    """Link checklist phrases on service pages to live condition pages (each content file's 'links_from').
    A line is matched on its visible text (links stripped), so it still matches after other words are linked."""
    todo = {}
    for slug, (_, pg) in cs.items():
        if pg.get('reviewed'):
            for page, ctx, phrase in pg.get('links_from', []):
                todo.setdefault(page, []).append((slug, ctx, phrase))
    n = 0
    for page, rows in todo.items():
        path = p(page)
        s = open(path, encoding='utf-8').read()
        def fix(m):
            nonlocal n
            inner = m.group(2)
            visible = re.sub(r'<[^>]+>', '', inner)
            for slug, ctx, phrase in rows:
                if ctx in visible and f'href="{slug}.html"' not in inner:
                    new_inner = link_phrase(inner, slug, phrase)
                    if new_inner != inner:
                        inner = new_inner
                        n += 1
            return m.group(1) + inner + m.group(3)
        s2 = CHECK_ITEM.sub(fix, s)
        if s2 != s:
            open(path, 'w', encoding='utf-8').write(s2)
    return n


def run(*cmd):
    r = subprocess.run([sys.executable, *cmd], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('slugs', nargs='*')
    ap.add_argument('--date', default=datetime.date.today().isoformat())
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--sync', action='store_true')
    ap.add_argument('--batch', type=int, help="release every still-draft question page whose content has 'batch': N")
    a = ap.parse_args()
    cs, qs = conditions(), questions()

    if a.list:
        for label, items in (('Condition pages', cs), ('Question pages', qs)):
            print(f'{label}:')
            for slug, (_, pg) in items.items():
                tag = f" (batch {pg['batch']})" if pg.get('batch') else ''
                tag += ' (es)' if pg.get('lang') == 'es' else ''
                print(f"  {'LIVE ' + pg['reviewed'] if pg.get('reviewed') else 'draft':16s} {slug}{tag}")
        return
    if a.batch is not None:
        picked = [slug for slug, (_, q) in qs.items() if q.get('batch') == a.batch and not q.get('reviewed')]
        if not picked:
            sys.exit(f'No draft question pages tagged batch {a.batch}.')
        a.slugs = list(a.slugs) + picked
    if not a.slugs and not a.sync:
        sys.exit(__doc__)
    unknown = [s for s in a.slugs if s not in cs and s not in qs]
    if unknown:
        sys.exit('Unknown page(s): ' + ', '.join(unknown) + '  (see --list)')

    rel_c = [s for s in a.slugs if s in cs]
    rel_es = [s for s in rel_c if cs[s][1].get('lang') == 'es']
    rel_en = [s for s in rel_c if s not in rel_es]
    rel_q = [s for s in a.slugs if s in qs]
    for s in rel_c:
        set_reviewed(cs[s][0], s, a.date, False)
    for s in rel_q:
        set_reviewed(qs[s][0], s, a.date, True)
    cs, qs = conditions(), questions()   # reload with the new dates

    if rel_c:
        print(run('_tools/build_condition.py', *rel_c))
    if rel_es:
        print(run('_tools/build_es_core.py'))
    print(run('_tools/build_questions.py').splitlines()[-1])

    urls = [s + '.html' for s in rel_c + rel_q]
    if rel_en:
        urls.append('conditions.html')
    if rel_es:
        urls += [spanish.ES_HOME, spanish.ES_HUB, spanish.ES_FORM]
    if rel_q:
        urls.append('ask-ari.html')
    if urls:
        sitemap_add(urls, a.date)
        llms_add([(s, plain(cs[s][1]['crumb'])) for s in rel_en],
                 [(s, plain(q['q'])) for s, (_, q) in qs.items() if q.get('reviewed')])
    if rel_en:
        hub_schema_add([(s, plain(cs[s][1]['crumb']), cs[s][1]['condition']) for s in rel_en])
    llms_spanish(cs)
    footer, pages = sync_links(qs)
    es_pages = sync_spanish(cs)
    mentions = link_mentions(cs)
    print(run('_tools/build_search_index.py'))

    if rel_c or rel_q:
        print(f'\nReleased {len(rel_c)} condition page(s) and {len(rel_q)} question page(s), reviewed {a.date}.')
    if footer:
        print(f'Added the "Patient Questions" footer link to {footer} pages.')
    if pages:
        print(f'Updated "Common questions" lists on {pages} condition pages.')
    if es_pages:
        print(f'Updated the Español link / hreflang on {es_pages} English pages.')
    if mentions:
        print(f'Linked {mentions} checklist mentions on service pages to live condition pages.')
    print('Next: check `git diff`, commit, push, then request indexing for the new URLs in Search Console.')


if __name__ == '__main__':
    main()
