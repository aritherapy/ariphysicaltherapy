"""Builds the two "trust" pages for the health library from the privacy-policy.html shell (same head, nav, footer).

    python3 _tools/build_trust.py            # writes deepa-konnur.html + editorial-policy.html

DRAFT = True  -> robots noindex, not in sitemap/llms.txt, nothing links to them yet.
On release (owner + Deepa approval): set DRAFT = False, rebuild, then
  - point every "Clinically reviewed by" link at deepa-konnur.html (build_condition.py, build_questions.py, rebuild),
  - footer link "How we create our content" -> editorial-policy.html on all pages,
  - add "publishingPrinciples" to the MedicalClinic schema, add both pages to sitemap.xml + llms.txt,
  - re-run build_search_index.py.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://ariphysicaltherapy.com/'
DRAFT = True
UPDATED = 'October 2026'
DEEPA = SITE + 'about.html#deepa'

TICK = '<span class="check-tick">&#10003;</span>'


def cred(b, s, last=False):
    st = ' style="border-bottom:none"' if last else ''
    return f'<div class="cred"{st}>{TICK}<div><b>{b}</b><span>{s}</span></div></div>'


REVIEWER_BODY = f'''<section class="section"><div class="section-inner">
  <div class="director">
    <div class="director-photo">
      <div class="frame"><img src="assets/deepa-konnur.jpg" alt="Deepa Konnur, PT, MPT, OCS, clinical reviewer for ARI Physical Therapy's health library" decoding="async" width="900" height="1200"></div>
      <div class="director-facts"><div><strong>OCS</strong><span>Board-certified Orthopedic Certified Specialist</span></div><div><strong>Residency-Trained</strong><span>Orthopedic physical therapy</span></div><div><strong>Spine Specialist PT</strong><span>Formerly Kaiser Permanente</span></div><div><strong>Pelvic Health Trained</strong><span>Herman &amp; Wallace Institute</span></div><div><strong>15+ Years</strong><span>Outpatient physical therapy</span></div></div></div>
    <div class="director-bio"><p class="director-name">Deepa Konnur</p><div class="director-creds">PT, MPT, OCS</div><div class="director-role">Founder &amp; Clinic Director &middot; Clinical Reviewer</div>
      <p>Deepa Konnur clinically reviews every condition guide and patient question on this website before it is published. She is an <strong>Orthopedic Certified Specialist (OCS)</strong>, board certified by the American Board of Physical Therapy Specialties, with more than 15 years of experience in outpatient physical therapy.</p>
      <p>She earned her <strong>Master of Physical Therapy at Loma Linda University</strong> and completed an <strong>Orthopedic Physical Therapy Residency</strong> through Movement for Life in partnership with the University of Southern California, a hybrid program that combined clinical work with coursework at USC. Before opening ARI, she was a <strong>Spine Clinical Specialist PT at Kaiser Permanente</strong>, focused on complex spine conditions and conservative alternatives for patients heading toward surgery. She has completed postgraduate pelvic rehabilitation training through the <strong>Herman &amp; Wallace Pelvic Rehabilitation Institute</strong>, and she has treated children, from babies to teens, throughout her career.</p>
      <div class="cred-h">Credentials &amp; training</div>
      {cred('Orthopedic Certified Specialist (OCS)', 'Board certified by the American Board of Physical Therapy Specialties')}
      {cred('Orthopedic Physical Therapy Residency', 'Movement for Life in partnership with USC')}
      {cred('Spine Clinical Specialist PT', 'Kaiser Permanente, complex spine conditions')}
      {cred('Pelvic rehabilitation training', 'Herman &amp; Wallace Pelvic Rehabilitation Institute')}
      {cred('Master of Physical Therapy (MPT)', 'Loma Linda University')}
      {cred('15+ years in outpatient physical therapy', 'Orthopedic, spine, pelvic, pediatric and post-surgical care', last=True)}
      <p class="license">California Physical Therapist License #PT292525 &middot; NPI #1245655307</p>
      <p style="font-size:14px">You can confirm any California physical therapist&rsquo;s license with the <a href="https://search.dca.ca.gov/" rel="noopener" target="_blank">California Department of Consumer Affairs license search</a>, and any provider&rsquo;s NPI in the <a href="https://npiregistry.cms.hhs.gov/provider-view/1245655307" rel="noopener" target="_blank">national NPI registry</a>.</p>
    </div>
  </div></div></section>
<section class="section cream"><div class="section-inner">
  <div class="section-head"><p class="eyebrow">Health Library</p><h2>What Deepa reviews</h2></div>
  <div class="grid-3">
    <div class="card"><h3>Condition guides</h3><p>In-depth pages on the conditions we treat, from back pain and knee arthritis to pelvic floor problems and torticollis in babies.</p><p><a href="conditions.html" class="link-arrow">Browse all conditions &rarr;</a></p></div>
    <div class="card"><h3>Patient questions</h3><p>Short, plain-language answers to the questions our patients ask most, like whether to use heat or ice, or when toe walking is normal.</p><p><a href="ask-ari.html" class="link-arrow">Browse patient questions &rarr;</a></p></div>
    <div class="card"><h3>Her areas of focus</h3><p>Orthopedics and sports injuries, spine care, pelvic health for women, prenatal and postpartum care, and children&rsquo;s physical therapy.</p><p><a href="about.html" class="link-arrow">More about ARI &rarr;</a></p></div>
  </div></div></section>
<section class="section"><div class="section-inner" style="max-width:860px">
  <div class="section-head"><h2>How she reviews a page</h2></div>
  <p>Before a page goes live, Deepa reads it as a clinician and checks that:</p>
  <div class="checks" style="grid-template-columns:1fr;margin:14px 0 18px">
    <div class="check">{TICK}<span>The information is accurate and matches current physical therapy practice.</span></div>
    <div class="check">{TICK}<span>It clearly lists the warning signs that mean you should see a doctor first.</span></div>
    <div class="check">{TICK}<span>It is honest about what physical therapy can and can&rsquo;t do, without promising results.</span></div>
    <div class="check">{TICK}<span>It only describes care we actually provide at ARI.</span></div>
    <div class="check">{TICK}<span>It is written in plain language a patient can use.</span></div>
  </div>
  <p>Each reviewed page shows &ldquo;Clinically reviewed by Deepa Konnur&rdquo; with the month it was reviewed. Read more about <a href="editorial-policy.html">how we create our health content</a>.</p>
</div></section>'''

EP_SECTIONS = [
    ('goal', 'Our goal', '''<p>Our health library answers the questions patients in Bakersfield ask us every day about pain, injuries, recovery after surgery, pelvic health and children&rsquo;s development. We want you to understand what may be going on, what usually helps, and when you should see a doctor, in plain language you can use.</p>'''),
    ('who', 'Who writes and reviews our content', f'''<p>Our pages are written by the ARI team. We use writing tools, including AI, to help draft and edit, and a person on our team checks every draft.</p>
        <p><strong>Nothing medical is published until a licensed physical therapist has reviewed it.</strong> Every condition guide and patient question is clinically reviewed by <a href="deepa-konnur.html">Deepa Konnur, PT, MPT, OCS</a>, our founder and a board-certified Orthopedic Certified Specialist. Reviewed pages show her name and the month of the review near the top.</p>'''),
    ('based', 'What our content is based on', '''<p>We base our content on current clinical practice guidelines, such as those published by the American Physical Therapy Association (APTA) and its specialty academies, on trusted public health sources such as MedlinePlus from the National Institutes of Health and the Centers for Disease Control and Prevention, and on the clinical experience of our physical therapists.</p>'''),
    ('standards', 'Our review standards', f'''<p>Every page we publish must:</p>
        <div class="checks" style="grid-template-columns:1fr;margin:14px 0 18px">
          <div class="check">{TICK}<span>Be accurate and match current physical therapy practice.</span></div>
          <div class="check">{TICK}<span>Include the warning signs that mean you should see a doctor first.</span></div>
          <div class="check">{TICK}<span>Be honest about what physical therapy can and can&rsquo;t do. We don&rsquo;t promise cures or guarantee results.</span></div>
          <div class="check">{TICK}<span>Describe only care we actually provide at ARI.</span></div>
          <div class="check">{TICK}<span>Use plain language and explain any medical terms.</span></div>
        </div>'''),
    ('updates', 'Keeping content up to date', '''<p>Each reviewed page shows when it was last reviewed. We re-review our pages at least once a year, and sooner when clinical guidance changes or a reader points out something we should fix.</p>'''),
    ('not', 'What our content is not', '''<p>Our pages are general information, not a diagnosis or a treatment plan for you. Everyone&rsquo;s situation is different, so please see a licensed clinician about your symptoms. <strong>If you think you have a medical emergency, call 911.</strong></p>'''),
    ('independence', 'Independence and transparency', '''<p>This website belongs to ARI Physical Therapy, an outpatient physical therapy clinic, and our pages invite you to contact us if you would like help. We are upfront about that. We do not run ads, publish sponsored content, or get paid to recommend products. Our articles do not include information that could identify any patient.</p>'''),
    ('feedback', 'Corrections and feedback', '''<p>If you think something on our site is wrong or out of date, please tell us. Email <a href="mailto:contactus@ariptcare.com">contactus@ariptcare.com</a> or call <a href="tel:6612828584">(661) 282-8584</a>. We review every report, and we correct the page when it needs it.</p>'''),
]


def editorial_body():
    toc = ''.join(f'<a href="#{i}">{h}</a>' for i, h, _ in EP_SECTIONS)
    secs = '\n        '.join(f'<h2 id="{i}">{h}</h2>\n        {b}' for i, h, b in EP_SECTIONS)
    return f'''<section class="section"><div class="section-inner legal-grid">
  <aside class="legal-toc"><h4>On this page</h4>{toc}</aside>
  <div class="legal"><p class="legal-date">Last updated: {UPDATED}</p>
        {secs}
  </div>
</div></section>'''


PAGES = [
    dict(slug='deepa-konnur', title='Deepa Konnur, PT, MPT, OCS | Clinical Reviewer | ARI Physical Therapy',
         desc='Deepa Konnur, PT, MPT, OCS, a board-certified Orthopedic Certified Specialist, clinically reviews every condition guide and patient question on the ARI Physical Therapy website.',
         eyebrow='Clinical Reviewer', h1='Deepa Konnur, PT, MPT, OCS',
         lead='Founder and Clinic Director of ARI Physical Therapy, and the licensed physical therapist who reviews every health page on this site.',
         body=REVIEWER_BODY,
         schema={'@context': 'https://schema.org', '@type': 'ProfilePage', 'name': 'Deepa Konnur, PT, MPT, OCS: Clinical Reviewer',
                 'url': SITE + 'deepa-konnur.html', 'mainEntity': {'@id': DEEPA}}),
    dict(slug='editorial-policy', title='How We Create Our Health Content | ARI Physical Therapy',
         desc='How ARI Physical Therapy writes, reviews and updates the condition guides and patient questions on its website, and what our content is and is not.',
         eyebrow='Health Library', h1='How We Create Our Health Content',
         lead='Who writes our pages, who reviews them, what they are based on, and how we keep them accurate.',
         body=editorial_body(),
         schema={'@context': 'https://schema.org', '@type': 'WebPage', 'name': 'How We Create Our Health Content',
                 'url': SITE + 'editorial-policy.html', 'about': {'@id': SITE + '#clinic'}, 'reviewedBy': {'@id': DEEPA},
                 'publisher': {'@id': SITE + '#clinic'}}),
]


def build(p):
    s = open(os.path.join(ROOT, 'privacy-policy.html'), encoding='utf-8').read()
    url = SITE + p['slug'] + '.html'
    s = s.replace('https://ariphysicaltherapy.com/privacy-policy.html', url)
    s = re.sub(r'<title>.*?</title>', f'<title>{p["title"]}</title>', s, count=1)
    s = re.sub(r'(<meta property="og:title" content=")[^"]*', r'\g<1>' + p['title'], s, count=1)
    for pat in (r'(<meta name="description" content=")[^"]*', r'(<meta property="og:description" content=")[^"]*'):
        s = re.sub(pat, lambda m: m.group(1) + p['desc'], s, count=1)
    s = s.replace('<meta name="robots" content="index, follow">',
                  '<meta name="robots" content="noindex, follow">' if DRAFT else '<meta name="robots" content="index, follow">')
    ld = '<script type="application/ld+json">\n' + json.dumps(p['schema'], indent=2, ensure_ascii=False) + '\n    </script>\n'
    s = s.replace('<link rel="preload"', ld + '<link rel="preload"', 1)
    a = s.index('<section class="page-hero">'); z = s.index('<footer>')
    hero = (f'<section class="page-hero"><div class="page-hero-inner">\n  <p class="eyebrow">{p["eyebrow"]}</p><h1>{p["h1"]}</h1>'
            f'<p class="lead">{p["lead"]}</p>\n</div></section>')
    s = s[:a] + hero + p['body'] + '\n' + s[z:]
    s = s.replace('class="active"', '')  # no nav item is active on these pages
    open(os.path.join(ROOT, p['slug'] + '.html'), 'w', encoding='utf-8').write(s)
    print(p['slug'] + '.html', 'DRAFT (noindex)' if DRAFT else 'LIVE')


if __name__ == '__main__':
    for p in PAGES: build(p)
