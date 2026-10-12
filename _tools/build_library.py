"""Builds health-library.html: one place to browse every condition guide and patient question by topic, or A-Z.

    python3 _tools/build_library.py

Condition guides come from the "Conditions we treat" section of llms.txt (only live pages are listed there) and are
placed in a topic by TOPIC_OF below; a new guide that isn't in TOPIC_OF stops the build so it can't go missing.
Patient questions come from _tools/questions/*.py (only pages with a 'reviewed' date). Re-run after any release.
DRAFT = True -> noindex and not linked from the nav; see the release notes at the bottom of this file.
"""
import html, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_trust, build_questions

ROOT = build_trust.ROOT
SITE = build_trust.SITE
DRAFT = False

TOPICS = [  # (key, label, blurb); keys match the question groups in _tools/questions where they exist
    ('back', 'Back &amp; Spine', 'Low back pain, sciatica, discs, stenosis and tailbone pain'),
    ('neck', 'Neck, Jaw &amp; Headaches', 'Neck pain, pinched nerves, whiplash, TMJ and headaches'),
    ('shoulder-hand', 'Shoulder, Elbow &amp; Hand', 'Rotator cuff, frozen shoulder, tennis elbow and carpal tunnel'),
    ('knee', 'Knee', 'Arthritis, ligament injuries, meniscus tears and knee pain'),
    ('hip', 'Hip', 'Hip pain, stiffness and arthritis'),
    ('foot-ankle', 'Foot &amp; Ankle', 'Heel pain, sprains and Achilles problems'),
    ('pelvic', 'Women&rsquo;s Pelvic Health &amp; Pregnancy', 'Bladder leaks, prolapse, pelvic pain, pregnancy and postpartum'),
    ('kids', 'Babies &amp; Kids', 'Torticollis, flat head, milestones, toe walking and young athletes'),
    ('balance', 'Dizziness &amp; Balance', 'Vertigo, unsteadiness and preventing falls'),
    ('bone-surgery', 'Arthritis, Bones &amp; Surgery Recovery', 'Osteoporosis, arthritis, joint replacement and rehab after surgery'),
    ('pain', 'Muscles, Tendons &amp; Chronic Pain', 'Strains, tendonitis, running injuries and fibromyalgia'),
    ('starting', 'Starting Physical Therapy', 'What to expect, cost, referrals and your first visit'),
]

TOPIC_OF = {
    'back': ['sciatica-back-pain', 'herniated-disc-bulging-disc', 'spinal-stenosis', 'si-joint-pain', 'upper-back-pain-posture', 'tailbone-pain-coccyx'],
    'neck': ['neck-pain-headaches', 'pinched-nerve-neck', 'car-accident-whiplash', 'tmj-jaw-pain', 'headaches-migraines'],
    'shoulder-hand': ['frozen-shoulder-rotator-cuff', 'shoulder-impingement-bursitis', 'tennis-elbow-golfers-elbow', 'carpal-tunnel-hand-numbness', 'hand-wrist-therapy'],
    'knee': ['knee-pain-arthritis', 'acl-mcl-knee-ligament-injuries', 'meniscus-tear'],
    'hip': ['hip-pain'],
    'foot-ankle': ['plantar-fasciitis-heel-pain', 'ankle-sprain-achilles-pain'],
    'pelvic': ['bladder-leaks-incontinence', 'pelvic-organ-prolapse', 'pelvic-pain-painful-sex', 'diastasis-recti', 'pregnancy-back-pelvic-pain',
               'c-section-recovery', 'bowel-leakage', 'interstitial-cystitis-bladder-pain'],
    'kids': ['torticollis-in-babies', 'flat-head-plagiocephaly', 'gross-motor-delays', 'coordination-problems-in-kids', 'toe-walking-in-kids', 'youth-sports-injuries'],
    'balance': ['vertigo-dizziness-bppv', 'balance-fall-prevention'],
    'bone-surgery': ['osteoporosis-bone-health', 'osteoarthritis-joint-pain', 'prehab-before-surgery', 'knee-hip-replacement-rehab', 'shoulder-surgery-rehab',
                     'spine-surgery-rehab', 'foot-ankle-surgery-rehab', 'fracture-recovery'],
    'pain': ['muscle-strains', 'tendonitis-overuse-injuries', 'running-injuries-running-assessment', 'fibromyalgia'],
}
SKIP = {'workers-comp-physical-therapy'}   # a service page, not a condition guide


def guides():
    sec = open(os.path.join(ROOT, 'llms.txt'), encoding='utf-8').read().split('## Conditions we treat')[1].split('\n## ')[0]
    items = [(t, s) for t, s in re.findall(r'- \[([^\]]+)\]\(https://ariphysicaltherapy\.com/([a-z0-9-]+)\.html\)', sec) if s not in SKIP]
    where = {s: k for k, ss in TOPIC_OF.items() for s in ss}
    missing = [s for _, s in items if s not in where]
    assert not missing, f'add these guides to TOPIC_OF: {missing}'
    out = {k: [] for k, _, _ in TOPICS}
    for t, s in items:
        out[where[s]].append((html.escape(t, quote=False), s))
    return out


def questions():
    out = {k: [] for k, _, _ in TOPICS}
    for key, g in build_questions.load_all():
        for p in g['pages']:
            if p.get('reviewed'):
                out[key].append((p['q'], p['slug']))
    return out


def body(G, Q):
    tiles = ''.join(
        f'<a class="lib-tile" href="#{k}"><b>{label}</b><span>{blurb}</span>'
        f'</a>'
        for k, label, blurb in TOPICS)
    secs = []
    for k, label, _ in TOPICS:
        gl = ''.join(f'<a href="{s}.html">{t} <span>&rarr;</span></a>' for t, s in G[k])
        ql = ''.join(f'<li><a href="{s}.html">{q}</a></li>' for q, s in Q[k])
        cols = (f'<div class="side-list"><h4>Condition guides</h4>{gl}</div>' if gl else '') + \
               (f'<div><h4 class="lib-h4">Patient questions</h4><ul class="plain-list lib-q">{ql}</ul></div>' if ql else '')
        secs.append(f'<div class="lib-topic" id="{k}"><h2>{label}</h2><div class="lib-cols{" one" if not gl else ""}">{cols}</div>'
                    f'<p class="lib-top"><a href="#topics">Back to all topics &uarr;</a></p></div>')
    allitems = [(re.sub(r'<[^>]+>', '', html.unescape(t)), s, 'Guide') for k in G for t, s in G[k]] + \
               [(html.unescape(q), s, 'Question') for k in Q for q, s in Q[k]]
    allitems.sort(key=lambda x: re.sub(r'^(why|what|when|how|is|are|can|do|does|should|my|will|i)\b\s*', '', x[0].lower()))
    letters = {}
    for t, s, kind in allitems:
        key = re.sub(r'^(why|what|when|how|is|are|can|do|does|should|my|will|i)\b\s*', '', t.lower())
        L = key[:1].upper() if key[:1].isalpha() else '#'
        letters.setdefault(L, []).append((t, s, kind))
    aznav = ''.join(f'<a href="#az-{L}">{L}</a>' for L in letters)
    azsecs = ''.join(f'<div class="az-group" id="az-{L}"><h3>{L}</h3><ul class="plain-list">' +
                     ''.join(f'<li><a href="{s}.html">{html.escape(t, quote=False)}</a> <small>{kind}</small></li>' for t, s, kind in items) +
                     '</ul></div>' for L, items in letters.items())
    n_g, n_q = sum(map(len, G.values())), sum(map(len, Q.values()))
    return f'''<section class="section"><div class="section-inner">
  <div class="lib-trust">
    <div class="cond-search"><label class="cond-search-h" for="cond-q">Search the library</label><form class="site-search site-search-inline" role="search"><div class="ss-row"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><use href="#i-search"/></svg><input id="cond-q" class="site-search-input" type="search" placeholder="Try &ldquo;heel pain&rdquo;" aria-label="Search conditions and patient questions" autocomplete="off"></div><div class="site-search-results" hidden aria-live="polite"></div></form></div></div>
  <div class="section-head" id="topics"><p class="eyebrow">Browse by topic</p><h2>What can we help you with?</h2></div>
  <div class="lib-tiles">{tiles}</div>
</div></section>
<section class="section cream"><div class="section-inner">
  {''.join(secs)}
</div></section>
<section class="section" id="a-z"><div class="section-inner">
  <div class="section-head"><p class="eyebrow">A&ndash;Z</p><h2>Everything in the library, A to Z</h2></div>
  <nav class="az-nav" aria-label="Jump to letter">{aznav}</nav>
  <div class="az-cols">{azsecs}</div>
<script>
/* Phones: show the first 2 questions per topic, with a button for the rest (desktop shows all; no-JS shows all) */
(function(){{
  document.querySelectorAll('.lib-q').forEach(function(ul){{
    if(ul.children.length <= 2) return;
    ul.classList.add('collapsed');
    var b = document.createElement('button');
    b.type = 'button'; b.className = 'lib-more'; b.setAttribute('aria-expanded', 'false');
    b.textContent = 'Show all questions';
    b.addEventListener('click', function(){{
      var open = ul.classList.toggle('collapsed') === false;
      b.setAttribute('aria-expanded', String(open));
      b.textContent = open ? 'Show fewer' : 'Show all questions';
    }});
    ul.after(b);
  }});
}})();
</script>
  <p class="med-disclaimer" style="margin-top:40px">Our health library is general information, not a diagnosis. If you have symptoms, a licensed clinician should evaluate you. If you think you have a medical emergency, call 911.</p>
  <p class="reviewed-by">Our condition guides and patient questions are written for patients and clinically reviewed by <a href="deepa-konnur.html">Deepa Konnur, PT, MPT, OCS</a> &middot; <a href="editorial-policy.html">How we create our content</a></p>
</div></section>'''


def build():
    G, Q = guides(), questions()
    n_g, n_q = sum(map(len, G.values())), sum(map(len, Q.values()))
    page = dict(slug='health-library', title='Health Library: Condition Guides &amp; Patient Questions | ARI Physical Therapy',
                desc='Browse condition guides and patient questions from ARI Physical Therapy, by topic or A to Z. Clinically reviewed by a licensed physical therapist.',
                eyebrow='Patient Education', h1='Health Library',
                lead='Clear answers about pain, injuries, pelvic health and children&rsquo;s development, from the physical therapists at ARI Physical Therapy in Bakersfield.',
                body=body(G, Q),
                schema={'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'ARI Physical Therapy Health Library',
                        'url': SITE + 'health-library.html', 'publisher': {'@id': SITE + '#clinic'}, 'reviewedBy': {'@id': SITE + 'about.html#deepa'},
                        'hasPart': [{'@type': 'MedicalWebPage', 'name': html.unescape(t), 'url': SITE + s + '.html'} for k in G for t, s in G[k]]})
    page['title'] = html.unescape(page['title'])
    build_trust.DRAFT = DRAFT
    build_trust.build(page)
    f = os.path.join(ROOT, 'health-library.html')   # this page is the nav's "Health Library" item: mark it active
    s = open(f, encoding='utf-8').read().replace('<a href="health-library.html">Health Library</a>', '<a href="health-library.html" class="active">Health Library</a>', 1)
    open(f, 'w', encoding='utf-8').write(s)
    print(f'{n_g} guides, {n_q} questions')


if __name__ == '__main__':
    build()

# RELEASE (after owner approval): DRAFT = False, rebuild; decide the nav (e.g. "Conditions" -> "Health Library"),
# add health-library.html to sitemap.xml + llms.txt ("More"), link it from conditions.html and ask-ari.html,
# re-run build_search_index.py. Re-run this builder after every content release so counts and lists stay current.
