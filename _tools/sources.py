"""Key sources shown at the bottom of condition guides ("Sources" list + schema.org citation).

    python3 _tools/sources.py                 # apply to every page listed in SOURCES (idempotent)
    python3 _tools/sources.py sciatica-back-pain knee-pain-arthritis

build_condition.py also applies these on every build, so a rebuilt page keeps its sources.
Only use pages that were opened and checked (title matches the topic). Prefer, in order: APTA/JOSPT clinical
practice guidelines, other specialty-society guidelines, then NIH (MedlinePlus, NIAMS, NIDDK, NIDCR, NIA), CDC,
AAOS OrthoInfo, ACOG and womenshealth.gov patient pages. 2-4 per page. Links checked 2026-10-11.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JOSPT = 'Journal of Orthopaedic &amp; Sports Physical Therapy (APTA clinical practice guideline)'
SOURCES = {
    'sciatica-back-pain': [
        ('Interventions for the Management of Acute and Chronic Low Back Pain: Revision 2021', JOSPT, '2021', 'https://www.jospt.org/doi/10.2519/jospt.2021.0304'),
        ('Sciatica', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/000686.htm'),
        ('Back Pain', 'National Institute of Arthritis and Musculoskeletal and Skin Diseases (NIH)', '', 'https://www.niams.nih.gov/health-topics/back-pain'),
    ],
    'knee-pain-arthritis': [
        ('2019 American College of Rheumatology/Arthritis Foundation Guideline for the Management of Osteoarthritis of the Hand, Hip, and Knee', 'Arthritis &amp; Rheumatology', '2020', 'https://doi.org/10.1002/art.41142'),
        ('Arthritis of the Knee', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/arthritis-of-the-knee/'),
        ('Osteoarthritis', 'Centers for Disease Control and Prevention', '', 'https://www.cdc.gov/arthritis/osteoarthritis/index.html'),
    ],
    'frozen-shoulder-rotator-cuff': [
        ('Shoulder Pain and Mobility Deficits: Adhesive Capsulitis', JOSPT, '2013', 'https://www.jospt.org/doi/10.2519/jospt.2013.0302'),
        ('Frozen Shoulder', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/frozen-shoulder/'),
        ('Rotator Cuff Tears', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/rotator-cuff-tears/'),
    ],
    'bladder-leaks-incontinence': [
        ('Urinary Incontinence', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/urinary-incontinence'),
        ('Bladder Control Problems (Urinary Incontinence)', 'National Institute of Diabetes and Digestive and Kidney Diseases (NIH)', '', 'https://www.niddk.nih.gov/health-information/urologic-diseases/bladder-control-problems'),
        ('Urinary Incontinence', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/urinaryincontinence.html'),
    ],
    'car-accident-whiplash': [
        ('Neck Pain: Revision 2017', JOSPT, '2017', 'https://www.jospt.org/doi/10.2519/jospt.2017.0302'),
        ('Neck Sprains and Strains', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/neck-sprain/'),
        ('Neck Injuries and Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/neckinjuriesanddisorders.html'),
    ],
    'tennis-elbow-golfers-elbow': [
        ('Lateral Elbow Pain and Muscle Function Impairments', JOSPT, '2022', 'https://www.jospt.org/doi/10.2519/jospt.2022.0302'),
        ('Tennis Elbow (Lateral Epicondylitis)', 'OrthoInfo, American Academy of Orthopaedic Surgeons', '', 'https://www.orthoinfo.org/diseases--conditions/tennis-elbow-lateral-epicondylitis/'),
        ('Tennis elbow', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/ency/article/000449.htm'),
    ],
    'tmj-jaw-pain': [
        ('TMD (Temporomandibular Disorders)', 'National Institute of Dental and Craniofacial Research (NIH)', '', 'https://www.nidcr.nih.gov/health-info/tmd'),
        ('Temporomandibular Disorders', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/temporomandibulardisorders.html'),
    ],
    'balance-fall-prevention': [
        ('Older Adult Fall Prevention', 'Centers for Disease Control and Prevention', '', 'https://www.cdc.gov/falls/about/index.html'),
        ('Falls and Fractures in Older Adults: Causes and Prevention', 'National Institute on Aging (NIH)', '', 'https://www.nia.nih.gov/health/falls-and-falls-prevention/falls-and-fractures-older-adults-causes-and-prevention'),
        ('Falls', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/falls.html'),
    ],
    'pelvic-organ-prolapse': [
        ('Pelvic Support Problems', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/pelvic-support-problems'),
        ('Pelvic Organ Prolapse', 'Office on Women&rsquo;s Health, U.S. Department of Health and Human Services', '', 'https://womenshealth.gov/a-z-topics/pelvic-organ-prolapse'),
        ('Pelvic Support Problems', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/pelvicfloordisorders.html'),
    ],
    'pelvic-pain-painful-sex': [
        ('Chronic Pelvic Pain', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/chronic-pelvic-pain'),
        ('When Sex Is Painful', 'American College of Obstetricians and Gynecologists', '', 'https://www.acog.org/womens-health/faqs/when-sex-is-painful'),
        ('Pelvic Pain', 'MedlinePlus, National Library of Medicine', '', 'https://medlineplus.gov/pelvicpain.html'),
    ],
}

START, END = '<!-- sources -->', '<!-- /sources -->'


def block(slug):
    items = ''.join(f'<li><a href="{u}" rel="noopener" target="_blank">{t}</a>. {p}{", " + y if y else ""}.</li>'
                    for t, p, y, u in SOURCES[slug])
    return f'{START}<div class="sources"><h2>Sources</h2><ol>{items}</ol></div>{END}'


def citations(slug):
    out = []
    for t, p, y, u in SOURCES[slug]:
        c = {'@type': 'CreativeWork', 'name': html.unescape(t), 'url': u, 'publisher': {'@type': 'Organization', 'name': html.unescape(p.split(' (APTA')[0])}}
        if y: c['datePublished'] = y
        out.append(c)
    return out


def apply(slug, s):
    """Return page HTML with the Sources block (before the disclaimer) and schema citations set."""
    if slug not in SOURCES:
        return s
    s = re.sub(re.escape(START) + '.*?' + re.escape(END), '', s, flags=re.S)
    assert s.count('<p class="med-disclaimer">') == 1, slug
    s = s.replace('<p class="med-disclaimer">', block(slug) + '<p class="med-disclaimer">', 1)
    for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        if '"MedicalWebPage"' in b:
            d = json.loads(b)
            d['citation'] = citations(slug)
            s = s.replace(b, '\n' + json.dumps(d, indent=2, ensure_ascii=False) + '\n    ', 1)
    return s


if __name__ == '__main__':
    for slug in sys.argv[1:] or sorted(SOURCES):
        f = os.path.join(ROOT, slug + '.html')
        s = open(f, encoding='utf-8').read()
        open(f, 'w', encoding='utf-8').write(apply(slug, s))
        print(slug, len(SOURCES[slug]), 'sources')
