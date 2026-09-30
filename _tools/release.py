"""Release clinically reviewed draft pages in one step.

    python3 _tools/release.py --list                                  # what's draft, what's live
    python3 _tools/release.py hip-pain leaking-urine-when-sneezing    # release these, reviewed today
    python3 _tools/release.py --date 2026-10-05 hip-pain ...          # with a specific review date
    python3 _tools/release.py --sync                                  # redo the cross-links only

For each slug (a condition page in _tools/conditions/ or a question in _tools/questions/) it:
  1. sets the page's 'reviewed' date in its content file (the page becomes indexable and gets
     Deepa's "Clinically reviewed by" line),
  2. rebuilds the page(s) and the ask-ari.html index,
  3. adds the page to sitemap.xml and llms.txt, and condition pages to the conditions.html schema,
  4. once any question is live: adds "Patient Questions" to every page's footer, and a
     "Common questions" list (live questions only) to the matching condition pages,
  5. refreshes the site search index.
It never commits or pushes. Review `git diff`, then commit, push, and request indexing in Search Console.
Only release pages Deepa has actually reviewed.
"""
import argparse, datetime, glob, html, importlib.util, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://ariphysicaltherapy.com/'
TOOLS = os.path.join(ROOT, '_tools')
REL_START, REL_END = '<!-- ask-ari:related -->', '<!-- /ask-ari:related -->'
FOOT_LINK = '<a href="ask-ari.html">Patient Questions</a><a href="appointment.html">'   # (question pages also say "Patient Questions" in their breadcrumb)


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
    a = ap.parse_args()
    cs, qs = conditions(), questions()

    if a.list:
        for label, items in (('Condition pages', cs), ('Question pages', qs)):
            print(f'{label}:')
            for slug, (_, pg) in items.items():
                print(f"  {'LIVE ' + pg['reviewed'] if pg.get('reviewed') else 'draft':16s} {slug}")
        return
    if not a.slugs and not a.sync:
        sys.exit(__doc__)
    unknown = [s for s in a.slugs if s not in cs and s not in qs]
    if unknown:
        sys.exit('Unknown page(s): ' + ', '.join(unknown) + '  (see --list)')

    rel_c = [s for s in a.slugs if s in cs]
    rel_q = [s for s in a.slugs if s in qs]
    for s in rel_c:
        set_reviewed(cs[s][0], s, a.date, False)
    for s in rel_q:
        set_reviewed(qs[s][0], s, a.date, True)
    cs, qs = conditions(), questions()   # reload with the new dates

    if rel_c:
        print(run('_tools/build_condition.py', *rel_c))
    print(run('_tools/build_questions.py').splitlines()[-1])

    urls = [s + '.html' for s in rel_c + rel_q]
    if rel_c:
        urls.append('conditions.html')
    if rel_q:
        urls.append('ask-ari.html')
    if urls:
        sitemap_add(urls, a.date)
        llms_add([(s, plain(cs[s][1]['crumb'])) for s in rel_c],
                 [(s, plain(q['q'])) for s, (_, q) in qs.items() if q.get('reviewed')])
    if rel_c:
        hub_schema_add([(s, plain(cs[s][1]['crumb']), cs[s][1]['condition']) for s in rel_c])
    footer, pages = sync_links(qs)
    print(run('_tools/build_search_index.py'))

    if rel_c or rel_q:
        print(f'\nReleased {len(rel_c)} condition page(s) and {len(rel_q)} question page(s), reviewed {a.date}.')
    if footer:
        print(f'Added the "Patient Questions" footer link to {footer} pages.')
    if pages:
        print(f'Updated "Common questions" lists on {pages} condition pages.')
    print('Next: check `git diff`, commit, push, then request indexing for the new URLs in Search Console.')


if __name__ == '__main__':
    main()
