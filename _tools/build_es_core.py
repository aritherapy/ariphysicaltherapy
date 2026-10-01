"""Build the Spanish core pages: homepage, conditions hub and appointment-request form.

    python3 _tools/build_es_core.py
    python3 _tools/build_search_index.py

Spanish condition pages are content files in _tools/conditions/ with PAGE['lang'] = 'es' (built by
build_condition.py). The hub lists the released ones (all of them while none is released). The three core
pages stay noindex until the first Spanish condition page is released; release.py rebuilds them.
"""
import html, importlib.util, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import spanish
from spanish import ES_HOME, ES_HUB, ES_FORM, SITE

LIVE = None   # set by __main__: live once any Spanish condition page has been released (release.py does that)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = 'https://www.google.com/maps/search/?api=1&amp;query=ARI+Physical+Therapy+8200+Stockdale+Hwy+Suite+B2+Bakersfield+CA+93311'


def es_pages():
    out = []
    for f in sorted(os.listdir(os.path.join(ROOT, '_tools', 'conditions'))):
        if f.endswith('.py') and not f.startswith('_'):
            spec = importlib.util.spec_from_file_location(f[:-3], os.path.join(ROOT, '_tools', 'conditions', f))
            m = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(m)
            if m.PAGE.get('lang') == 'es':
                out.append((f[:-3], m.PAGE))
    return out


def jsonld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, indent=2, ensure_ascii=False) + '\n    </script>'


def page(shell_file, slug, en_slug, title, desc, blocks, body, robots=None):
    url = SITE + slug
    s = open(os.path.join(ROOT, shell_file), encoding='utf-8').read()
    en_url = SITE if en_slug == 'index.html' else SITE + en_slug if en_slug else None   # the homepage's canonical is the bare domain
    s = spanish.es_shell(s, url, en_url)
    t, d = html.escape(title), html.escape(desc)
    s = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', s)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', s)
    s = re.sub(r'<title>.*?</title>', f'<title>{t}</title>', s, flags=re.S)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{t}">', s)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{d}">', s)
    s = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{d}">', s)
    rb = robots or ('index, follow' if LIVE else 'noindex, follow')
    if re.search(r'<meta name="robots" content="[^"]*">', s):
        s = re.sub(r'<meta name="robots" content="[^"]*">', f'<meta name="robots" content="{rb}">', s)
    else:
        s = s.replace('</title>', f'</title>\n    <meta name="robots" content="{rb}">', 1)
    # keep the shell's MedicalClinic block; replace page-level blocks with ours
    for b in re.findall(r'\s*<script type="application/ld\+json">.*?</script>', s, re.S):
        if '"MedicalClinic"' not in b:
            s = s.replace(b, '')
    s = s.replace('</head>', '    ' + '\n    '.join(jsonld(b) for b in blocks) + '\n</head>', 1)
    a, z = s.index('</nav>\n'), s.index('<footer')
    s = s[:a] + body + s[z:]
    open(os.path.join(ROOT, slug), 'w', encoding='utf-8').write(s)
    print(f"{slug}  {'draft (noindex)' if 'noindex' in rb else 'LIVE'}")


SIDE = f'''  <aside class="detail-side">
    <div class="side-card"><h3>Se habla español</h3><p>Llámenos o solicite una cita en línea. Le responderemos, normalmente en un día hábil.</p>
      <a href="{ES_FORM}" class="btn btn-primary">Solicitar una cita</a>
      <span class="or">o llame al <a href="tel:6612828584">(661) 282-8584</a></span></div>
    <div class="side-list"><h4>Más información</h4><a href="{ES_HUB}">Afecciones que tratamos <span>&rarr;</span></a><a href="{ES_HOME}#contacto">Dirección y horario <span>&rarr;</span></a><a href="index.html" lang="en">English website <span>&rarr;</span></a></div>
  </aside>'''

FAQS = [
    ('¿Necesito una referencia del médico?', 'No, en la mayoría de los casos. En California puede ver a un fisioterapeuta directamente hasta por 12 visitas o 45 días, lo que ocurra primero. Algunos seguros todavía piden una referencia; llámenos y le ayudamos a verificarlo. Para casos de compensación de trabajadores, el tratamiento lo receta su médico tratante.'),
    ('¿Aceptan mi seguro?', 'Aceptamos la mayoría de los seguros médicos privados y Medicare. Llámenos al (661) 282-8584 y verificamos sus beneficios antes de su primera visita.'),
    ('¿Hablan español?', 'Sí. Tenemos personal que habla español. Cuando pida su cita, díganos que prefiere español y haremos lo posible para atenderle en su idioma.'),
    ('¿Cuánto dura la primera visita?', 'La evaluación inicial dura de 45 a 60 minutos. Las visitas de seguimiento suelen durar de 30 a 45 minutos. Todas las visitas son individuales con un fisioterapeuta con licencia.'),
    ('¿Ofrecen terapia por video?', 'No. Toda nuestra atención es en persona en nuestra clínica de Bakersfield.'),
]


def acc(faqs):
    return ''.join(f'<div class="acc-item"><button class="acc-q" aria-expanded="{"true" if i == 0 else "false"}">{html.escape(q)}'
                   f'<span class="acc-t">{"&minus;" if i == 0 else "+"}</span></button><div class="acc-a">{html.escape(a)}</div></div>'
                   for i, (q, a) in enumerate(faqs))


def check(inner):
    return f'<div class="check"><span class="check-tick">&#10003;</span><span>{inner}</span></div>'


def build_home(pages):
    by_en = {p.get('en'): slug for slug, p in pages}
    link = lambda en, label: f'<a href="{by_en[en]}.html">{label}</a>' if en in by_en else label
    services = [
        'Rehabilitación ortopédica: espalda, cuello, hombro, rodilla y cadera',
        'Lesiones deportivas y regreso seguro al deporte',
        'Rehabilitación después de una cirugía',
        'Dolor crónico',
        'Terapia del piso pélvico para mujeres',
        'Fisioterapia pediátrica',
        link('pregnancy-back-pelvic-pain', 'Embarazo y posparto'),
        link('workers-comp-physical-therapy', 'Lesiones del trabajo y compensación de trabajadores'),
        link('car-accident-whiplash', 'Lesiones por accidentes de auto'),
        link('balance-fall-prevention', 'Equilibrio y prevención de caídas'),
    ]
    conds = ''.join(f'<li><a href="{slug}.html">{html.unescape(re.sub(r"<[^>]+>", "", p["crumb"]))}</a></li>' for slug, p in pages)
    body = f'''</nav>
<section class="page-hero"><div class="page-hero-inner">
  <p class="eyebrow">Se habla español</p><h1>Terapia física individual en <span style="color:var(--orange)">Bakersfield</span></h1>
  <p class="lead">Atención uno a uno con un fisioterapeuta con licencia para el dolor de espalda y cuello, lesiones, rehabilitación después de una cirugía, la salud pélvica de la mujer y mucho más.</p>
  <div style="margin-top:30px;display:flex;gap:12px;flex-wrap:wrap"><a href="{ES_FORM}" class="btn btn-primary">Solicitar una cita</a><a href="tel:6612828584" class="btn btn-on-dark">Llamar al (661) 282-8584</a></div>
</div></section>
<section class="section"><div class="section-inner detail">
  <div class="prose">
    <p class="svc-lead" style="font-size:17px;line-height:1.75;margin-bottom:8px"><strong>ARI Physical Therapy es una clínica independiente de terapia física en Bakersfield.</strong> Cada visita es individual y en persona con un fisioterapeuta con licencia. Nuestra directora clínica, Deepa Konnur, PT, MPT, OCS, es especialista certificada en ortopedia (Orthopedic Certified Specialist). Aceptamos la mayoría de los seguros médicos privados y Medicare, y contamos con personal que habla español.</p>
<h2>Cómo le podemos ayudar</h2><div class="checks">{''.join(check(x) for x in services)}</div>
<h2>Afecciones que tratamos</h2><p>Información en español sobre algunas de las afecciones más comunes que tratamos:</p><ul class="plain-list">{conds}</ul><p><a href="{ES_HUB}">Ver todas las afecciones &rarr;</a></p>
<h2>Por qué los pacientes eligen ARI</h2><ul class="plain-list"><li><strong>Atención individual:</strong> todo el tiempo de su visita con un fisioterapeuta con licencia.</li><li><strong>Experiencia especializada:</strong> nuestra directora clínica es especialista certificada en ortopedia.</li><li><strong>Personal que habla español</strong>, para que pueda explicar sus síntomas con comodidad.</li><li><strong>Seguros:</strong> aceptamos la mayoría de los seguros privados y Medicare.</li><li><strong>Estacionamiento gratis</strong> en Town &amp; Country Village, junto a Trader Joe's.</li></ul>
{spanish.ES['direct_access']}
<h2>Su primera visita</h2><div class="steps"><div class="step"><span class="step-num">1</span><div><b>Una evaluación individual</b><p>Su primera visita dura de 45 a 60 minutos. Hablamos de sus síntomas y sus metas, y revisamos cómo se mueve.</p></div></div><div class="step"><span class="step-num">2</span><div><b>Un plan hecho para usted</b><p>Tratamiento práctico y ejercicios que avanzan poco a poco, adaptados a su cuerpo y a su vida diaria.</p></div></div><div class="step"><span class="step-num">3</span><div><b>Progreso que dura</b><p>Medimos su avance y le enseñamos un programa en casa para mantener los resultados.</p></div></div></div>
<h2 id="contacto">Dirección y horario</h2><p><strong>ARI Physical Therapy</strong><br>8200 Stockdale Hwy, Suite B2<br>Bakersfield, CA 93311<br>En Town &amp; Country Village, junto a Trader Joe's<br><a href="{MAP}">Cómo llegar &rarr;</a></p><p><strong>Horario:</strong> lunes a viernes, 8:00 AM a 6:00 PM<br><strong>Teléfono:</strong> <a href="tel:6612828584">(661) 282-8584</a><br><strong>Fax (referencias):</strong> (661) 727-0005<br><strong>Correo:</strong> <a href="mailto:contactus@ariptcare.com">contactus@ariptcare.com</a></p>
<h2>Preguntas frecuentes</h2><div class="acc">{acc(FAQS)}</div>{spanish.ES['page_cta']}
  </div>
{SIDE}
</div></section>
'''
    web = {'@context': 'https://schema.org', '@type': 'WebPage', '@id': SITE + ES_HOME + '#page', 'url': SITE + ES_HOME,
           'name': 'Terapia física en Bakersfield | ARI Physical Therapy', 'inLanguage': 'es-US',
           'isPartOf': {'@type': 'WebSite', 'name': 'ARI Physical Therapy', 'url': SITE}, 'about': {'@id': SITE + '#clinic'}}
    faq = {'@context': 'https://schema.org', '@type': 'FAQPage', 'inLanguage': 'es-US', 'mainEntity': [
        {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQS]}
    page('knee-pain-arthritis.html', ES_HOME, 'index.html',
         'Terapia física en Bakersfield en español | ARI PT',
         'Terapia física individual en Bakersfield, CA. Se habla español. Dolor de espalda, lesiones, cirugía y salud pélvica de la mujer. Medicare aceptado.',
         [web, faq], body)


def build_hub(pages):
    live = [x for x in pages if x[1].get('reviewed')]
    shown = live if live else pages
    items = ''.join(f'<div class="cond-item"><h3><a href="{slug}.html">{html.unescape(re.sub(r"<[^>]+>", "", p["crumb"]))}</a></h3>'
                    f'<p>{p["lead"]}</p></div>' for slug, p in shown)
    body = f'''</nav>
<section class="page-hero"><div class="page-hero-inner">
  <p class="breadcrumb"><a href="{ES_HOME}">Inicio</a> &nbsp;/&nbsp; Afecciones que tratamos</p>
  <p class="eyebrow">Se habla español</p><h1>Afecciones que tratamos</h1>
  <p class="lead">Información clara, en español, sobre problemas comunes que la terapia física puede ayudar. Cada página explica las señales, el tratamiento y cuándo ver a un médico.</p>
</div></section>
<section class="section"><div class="section-inner detail">
  <div class="prose">
{items}
<p>Tratamos muchas otras afecciones. Vea la <a href="conditions.html" lang="en">lista completa en inglés</a> o llámenos al <a href="tel:6612828584">(661) 282-8584</a>; tenemos personal que habla español.</p>
{spanish.ES['page_cta']}<p class="med-disclaimer">{spanish.ES['disclaimer']}</p>
  </div>
{SIDE}
</div></section>
'''
    coll = {'@context': 'https://schema.org', '@type': 'CollectionPage', '@id': SITE + ES_HUB + '#page', 'url': SITE + ES_HUB,
            'name': 'Afecciones que tratamos', 'inLanguage': 'es-US', 'publisher': {'@id': SITE + '#clinic'},
            'hasPart': [{'@type': 'MedicalWebPage', 'name': html.unescape(re.sub(r'<[^>]+>', '', p['crumb'])), 'url': SITE + slug + '.html'}
                        for slug, p in shown]}
    page('knee-pain-arthritis.html', ES_HUB, 'conditions.html', 'Afecciones que tratamos en Bakersfield | ARI PT',
         'Terapia física en Bakersfield para dolor de espalda, rodilla, hombro, cuello, vértigo, embarazo y más. Información en español. Se habla español.',
         [coll], body)


FORM_TEXT = [
    ('<p class="eyebrow">Get Started</p><h1>Book Your Appointment</h1><p class="lead">Request an appointment online and we\'ll confirm within one business day. Prefer to talk? Call us directly.</p>',
     '<p class="eyebrow">Se habla español</p><h1>Solicite una cita</h1><p class="lead">Envíe su solicitud en línea y le confirmaremos, normalmente en un día hábil. ¿Prefiere hablar con alguien? Llámenos; tenemos personal que habla español.</p>'),
    ('<h3>Request an Appointment</h3><p>Fill out the form below and our team will confirm your appointment within one business day.</p>',
     '<h3>Solicitud de cita</h3><p>Llene este formulario y nuestro equipo le contactará para confirmar su cita, normalmente en un día hábil. Si prefiere español, se lo pasamos a nuestro personal que habla español.</p>'),
    ("I'm booking this for my child", 'Estoy pidiendo esta cita para mi hijo o hija'),
    ('>Patient information</div>', '>Información del paciente</div>'),
    ('>First Name *<', '>Nombre *<'), ('>Last Name *<', '>Apellido *<'), ('>Age<', '>Edad<'), ('>Sex<', '>Sexo<'),
    ('>Select age range<', '>Seleccione un rango de edad<'), ('>Under 5<', '>Menos de 5<'), ('>5 to 12<', '>De 5 a 12<'),
    ('>13 to 17<', '>De 13 a 17<'), ('>18 to 39<', '>De 18 a 39<'), ('>40 to 64<', '>De 40 a 64<'), ('>65 or older<', '>65 o más<'),
    ('>Prefer not to say<', '>Prefiero no decir<'), ('>Female<', '>Femenino<'), ('>Male<', '>Masculino<'),
    ('Age and sex help us match you with the right therapist, for example pediatric or pelvic health care. Both are optional.',
     'La edad y el sexo nos ayudan a asignarle el terapeuta adecuado, por ejemplo para atención pediátrica o de salud pélvica. Ambos son opcionales.'),
    ('>Parent or guardian<', '>Padre, madre o tutor<'), ('>Your Name<', '>Su nombre<'), ('>Relationship to Patient<', '>Relación con el paciente<'),
    ('>Select one<', '>Seleccione una opción<'), ('>Parent<', '>Padre o madre<'), ('>Legal guardian<', '>Tutor legal<'),
    ('>Grandparent<', '>Abuelo o abuela<'), ('>Other<', '>Otro<'),
    ('>How we reach you<', '>Cómo le contactamos<'), ('>Email Address *<', '>Correo electrónico *<'), ('>Phone Number *<', '>Teléfono *<'),
    ('>Visit details<', '>Detalles de la visita<'), ('>Service Needed<', '>Servicio que necesita<'),
    ('>Select a service (optional)<', '>Seleccione un servicio (opcional)<'),
    ('>Orthopedic Rehabilitation<', '>Rehabilitación ortopédica<'), ('>Sports Injury Recovery<', '>Lesiones deportivas<'),
    ('>Post-Operative Care<', '>Rehabilitación después de una cirugía<'), ('>Chronic Pain Rehab<', '>Dolor crónico<'),
    ('>Pelvic Pain<', '>Salud pélvica de la mujer<'), ('>Pediatric Rehabilitation<', '>Fisioterapia pediátrica<'),
    ('>Pre / Post Partum Rehab<', '>Embarazo y posparto<'), ('>Health Programs<', '>Programas de bienestar<'),
    ('>Not Sure / General Inquiry<', '>No estoy seguro / Pregunta general<'),
    ('>Insurance<', '>Seguro médico<'), ('>Select your plan (optional)<', '>Seleccione su plan (opcional)<'),
    ('>Workers Compensation<', '>Compensación de trabajadores<'), ('>Self-pay / Cash<', '>Pago propio / Efectivo<'), ('>Not sure<', '>No estoy seguro<'),
    ('Carrier name only. Please do not enter your member ID or policy number here; we will collect those securely at your first visit.',
     'Solo el nombre de la compañía. Por favor no escriba aquí su número de miembro ni de póliza; los pedimos de forma segura en su primera visita.'),
    ('>Preferred Date<', '>Fecha preferida<'), ('>Preferred Time<', '>Hora preferida<'), ('>Any time<', '>Cualquier hora<'),
    ('>Morning (8 AM to 12 PM)<', '>Mañana (8 AM a 12 PM)<'), ('>Afternoon (12 PM to 4 PM)<', '>Tarde (12 PM a 4 PM)<'),
    ('>Late Afternoon (4 PM to 6 PM)<', '>Tarde-noche (4 PM a 6 PM)<'),
    ('>Were you referred by a physician?<', '>¿Le refirió un médico?<'), ('>Yes, I have a referral<', '>Sí, tengo una referencia<'),
    (">No, I'm self-referring<", '>No, vengo por mi cuenta<'),
    ('>Tell us about your condition or concern<', '>Cuéntenos sobre su problema o preocupación<'),
    ('<span>Yes, text me about my care. I agree to receive SMS text messages from ARI Physical Therapy at the phone number provided: appointment reminders, confirmations, scheduling, and patient-care notifications.</span>',
     '<span>Sí, envíenme mensajes de texto sobre mi atención. Acepto recibir mensajes de texto (SMS) de ARI Physical Therapy al número de teléfono que di: recordatorios y confirmaciones de citas, programación y avisos sobre mi atención.</span>'),
    ('Consent is not a condition of any purchase or of receiving care. Message frequency varies. Message &amp; data rates may apply. Reply <strong>STOP</strong> to opt out at any time, or <strong>HELP</strong> for help. See our <a href="privacy-policy.html">Privacy Policy</a> and <a href="sms-terms.html">SMS Terms</a>.',
     'Dar su consentimiento no es requisito para ninguna compra ni para recibir atención. La frecuencia de los mensajes varía. Pueden aplicarse tarifas de mensajes y datos. Responda <strong>STOP</strong> para dejar de recibir mensajes en cualquier momento, o <strong>HELP</strong> para obtener ayuda. Vea nuestra <a href="privacy-policy.html">Política de privacidad</a> y los <a href="sms-terms.html">Términos de SMS</a> (en inglés).'),
    ('Request My Appointment &rarr;', 'Enviar mi solicitud &rarr;'),
    ("We'll confirm within one business day. No obligation.", 'Le confirmaremos, normalmente en un día hábil. Sin compromiso.'),
    ('<h3>Request Received!</h3><p>Thank you! Our team will review your request and reach out to confirm your appointment within one business day. If you need immediate assistance, please call us at (661) 282-8584.</p>',
     '<h3>¡Recibimos su solicitud!</h3><p>¡Gracias! Nuestro equipo revisará su solicitud y le contactará para confirmar su cita, normalmente en un día hábil. Si necesita ayuda de inmediato, llámenos al (661) 282-8584.</p>'),
    ('<h3>Prefer to Call?</h3><p>Our front desk team is ready to help you schedule and answer any questions.</p>',
     '<h3>¿Prefiere llamar?</h3><p>Nuestro equipo de recepción le ayuda a programar su cita y responde sus preguntas. Tenemos personal que habla español.</p>'),
    ('<h4>Clinic Information</h4>', '<h4>Información de la clínica</h4>'), ('</svg>Address</div>', '</svg>Dirección</div>'),
    ('</svg>Hours</div>', '</svg>Horario</div>'), ('Monday &ndash; Friday', 'Lunes a viernes'),
    ('</svg>Fax (Referrals)</div>', '</svg>Fax (referencias)</div>'), ('</svg>Email</div>', '</svg>Correo</div>'),
    ('<p class="eyebrow">What to Expect</p><h2>Four steps, start to finish</h2>', '<p class="eyebrow">Qué esperar</p><h2>Cuatro pasos, de principio a fin</h2>'),
    ('<h3>Submit your request</h3><p>Fill out the form or give us a call. Either works.</p>', '<h3>Envíe su solicitud</h3><p>Llene el formulario o llámenos. Cualquiera de las dos opciones funciona.</p>'),
    ('<h3>We confirm your appointment</h3><p>Our team will reach out within one business day to confirm your date and time.</p>',
     '<h3>Confirmamos su cita</h3><p>Nuestro equipo le contactará, normalmente en un día hábil, para confirmar la fecha y la hora.</p>'),
    ("<h3>Your first visit</h3><p>We'll do a full evaluation and build your personalized treatment plan together.</p>",
     '<h3>Su primera visita</h3><p>Hacemos una evaluación completa y juntos creamos su plan de tratamiento personalizado.</p>'),
    ("<h3>Start your recovery</h3><p>Begin your program with a team that's fully committed to your goals.</p>",
     '<h3>Empiece su recuperación</h3><p>Comience su programa con un equipo comprometido con sus metas.</p>'),
    ("lg.textContent=cb.checked?\"Your child's information\":'Patient information';", "lg.textContent=cb.checked?'Información de su hijo o hija':'Información del paciente';"),
]


def build_form():
    url = SITE + ES_FORM
    s = open(os.path.join(ROOT, 'appointment.html'), encoding='utf-8').read()
    for en, es in FORM_TEXT:
        assert en in s, 'missing on appointment.html: ' + en[:60]
        s = s.replace(en, es)
    # tell the front desk this request came from the Spanish form
    s = s.replace('<form id="appt-form" action="https://formspree.io/f/xaqaegkz" method="POST">',
                  '<form id="appt-form" action="https://formspree.io/f/xaqaegkz" method="POST">\n      <input type="hidden" name="language" value="Spanish (respond in Spanish)">', 1)
    s = spanish.es_shell(s, url, SITE + 'appointment.html')
    rb = 'index, follow' if LIVE else 'noindex, follow'
    s = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', s)
    s = re.sub(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{url}">', s)
    title = 'Solicite una cita de terapia física | ARI PT Bakersfield'
    desc = 'Solicite su cita de terapia física en Bakersfield en línea. Le confirmamos, normalmente en un día hábil. Se habla español. (661) 282-8584.'
    s = re.sub(r'<title>.*?</title>', f'<title>{html.escape(title)}</title>', s, flags=re.S)
    s = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{html.escape(title)}">', s)
    s = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{html.escape(desc)}">', s)
    s = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{html.escape(desc)}">', s)
    if re.search(r'<meta name="robots" content="[^"]*">', s):
        s = re.sub(r'<meta name="robots" content="[^"]*">', f'<meta name="robots" content="{rb}">', s)
    else:
        s = s.replace('</title>', f'</title>\n    <meta name="robots" content="{rb}">', 1)
    open(os.path.join(ROOT, ES_FORM), 'w', encoding='utf-8').write(s)
    print(f'{ES_FORM}  {"LIVE" if LIVE else "draft (noindex)"}')


if __name__ == '__main__':
    pages = es_pages()
    LIVE = any(p.get('reviewed') for _, p in pages)
    build_home([x for x in pages if x[1].get('reviewed')] or pages)
    build_hub(pages)
    build_form()
