# Content guide: condition pages and Patient Questions (ariphysicaltherapy.com)

This is for anyone, human or Claude, writing new pages. The `_tools/` folder isn't published.
Every new page starts as a hidden draft (`'reviewed': None` makes it noindex). Deepa Konnur, PT, MPT, OCS reviews it clinically, then `release.py` publishes it.

## Who it's for and how it should sound
- Patients in Bakersfield, CA searching for a symptom. Plain English at a 6th–8th grade reading level, warm and calm, using "you". Keep sentences short.
- Be honest and evidence-based. Use "often", "most people", "can" and avoid promises. Mention a guideline body only when you're sure it says so (e.g. the American College of Physicians for low back pain, ACR/AAOS for knee and hip arthritis). Never invent numbers, studies or percentages.
- Reassure without dismissing. Always include clear warning signs that need a doctor or emergency care.
- Never say or imply that doctors don't know things.

## Clinic facts. Use only these and never invent others.
- ARI Physical Therapy, 8200 Stockdale Hwy, Suite B2, Bakersfield, CA 93311 (Town & Country Village, next to Trader Joe's). Phone (661) 282-8584, fax (661) 727-0005.
- Every visit is one-on-one and in person with a licensed physical therapist. First visit about 45–60 minutes, follow-ups about 30–45.
- Never say visits happen "in a private room" (or "cuarto privado" / "en privado"). Not every visit is in one; some are exercise in the open gym area (owner, 2026-10-10).
- Clinic director: Deepa Konnur, PT, MPT, OCS, a board-certified Orthopedic Certified Specialist. She has pelvic rehab training from Herman & Wallace.
- Pediatrics (owner + Deepa, 2026-10-11): ARI treats babies, kids and teens. Most pediatric patients are BABIES with torticollis or gross-motor/developmental delays (rolling, sitting, crawling, walking), plus kids about 10–15 with sports injuries (incl. ACL). Parents are involved in visits, families get a home program, and we coordinate with the child's pediatrician. Deepa has treated children throughout her career. Don't claim helmets/orthotics fitting, early-intervention (Regional Center) services, neuro conditions (cerebral palsy etc.) or autism therapy.
- Insurance: "most private insurance plans and Medicare". Never mention Medi-Cal.
- California direct access: patients can see a PT without a referral for up to 12 visits or 45 days. Some plans still require a referral.
- Languages: say "we have staff who speak Spanish and Hindi". NEVER say "our team speaks…".
- The template adds the clinic paragraph, the referral FAQ, the end-of-page call to action, the disclaimer and the reviewed line, so don't repeat them in content.

## Never claim
Online booking ("request an appointment" only). Telehealth. Free consultations. Neuro rehab (stroke, Parkinson's, MS). Aquatic therapy. Dry needling (not legal for CA PTs). FCE or pre-employment testing. Concussion care. Scoliosis treatment (owner 2026-10-11). Auto-injury liens or med-pay arrangements (not decided). Custom splints or "certified hand therapist". Midwives (say "your OB"). Pelvic floor therapy for men (it's for women only). Any equipment or technique not already on the site. Guaranteed results or timelines.

## Condition pages: `_tools/conditions/<slug>.py`, built by `build_condition.py`
Copy the structure of an existing page, e.g. `hip-pain.py` or `hand-wrist-therapy.py`. Required keys:
`reviewed` (None), `title` (≤62 chars, ends " | ARI PT", include Bakersfield if it fits), `description` (120–158 chars), `crumb`, `eyebrow`, `h1` (ENDS WITH " in"; the template appends "Bakersfield"), `lead`, `answer` (opening paragraph starting with `<strong>…</strong>`), `signs` (5–6 checklist items), `why` (2–3 `(heading, html)` sections), `steps` (3 `(title, text)`: evaluation → treatment → lasting progress), `red_flags` (4–6, optional `red_flags_intro`), `faq_title`, `faqs` (4–5 `(q, a)` plain text, NO referral FAQ), `side` (one sentence), `related` (2–4 `(label, file.html)` that EXIST), `condition`, `alt_names` (include common search phrases), `therapy`. Optional: `links_from`.
Length: about 700–1,000 words of body copy. Link to related existing pages inside the HTML where it's natural.

## Patient Questions: `_tools/questions/<file>.py` with `GROUPS` and `PAGES`, built by `build_questions.py`
Copy an existing entry, e.g. in `batch4_spine_upper.py`. Keys:
`slug` (the question in URL form), `group` (one of: back, neck, shoulder-hand, knee, hip, foot-ankle, pelvic, balance, bone-surgery, kids, starting), `reviewed` (None), `batch` (N), `about` (condition name), `q`, `crumb`, `title` (≤62 chars incl. " | ARI PT"), `description` (≤158), `short` (2–3 sentence direct answer, written to be quotable by Google and AI answers), `sections` (2–3 `(heading, html)`), `red_intro`, `red_flags` (3–6), `pt` (one paragraph on how PT helps, no clinic facts beyond the list above), `guide` (`(label, 'existing-condition-page.html')`).
Length: about 300–450 words. A question must not duplicate an existing page; check `release.py --list`.

## Check before handing over
`python3 -c` import the file. Then check: title ≤62, description ≤158, condition h1 ends " in", every linked .html exists in the repo root, and no banned claims (search for: book online, telehealth, Medi-Cal, midwife, neuro, aquatic, dry needling, FCE, concussion, "our team speaks").
