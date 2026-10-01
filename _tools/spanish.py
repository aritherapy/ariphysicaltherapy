"""Spanish-language support for the page builders (build_condition.py, build_es_core.py).

Spanish pages use the same layout as the English site. This module supplies:
  - ES: every built-in phrase the condition-page template prints (the English set lives in build_condition.py),
  - es_shell(): turns an English page shell into a Spanish one (lang, menu, top bar, footer, hreflang),
  - the Spanish core page slugs.
Spanish copy is neutral Latin American Spanish, formal "usted". A Spanish-speaking staff member reviews
every Spanish page before release (in addition to Deepa's clinical review of the English original).
"""
import re

SITE = 'https://ariphysicaltherapy.com/'
ES_HOME = 'terapia-fisica-bakersfield.html'
ES_HUB = 'afecciones.html'
ES_FORM = 'solicitar-cita.html'
MONTHS_ES = 'enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre'.split()

ES = {
    'lang': 'es', 'in_language': 'es-US',
    'hub': ES_HUB, 'hub_name': 'Afecciones que tratamos', 'form': ES_FORM,
    'request': 'Solicitar una evaluación',
    'signs_h': '¿Le suena familiar?',
    'steps_h': 'Cómo es el tratamiento en ARI',
    'red_h': 'Cuándo ver primero a un médico',
    'red_intro': 'Vea a un médico pronto si tiene:',
    'disclaimer': 'Esta página es información general, no un diagnóstico. Si tiene síntomas, un profesional de salud con licencia debe evaluarle.',
    'side_h': 'Empiece con una evaluación',
    'side_tail': 'Solicite una evaluación y le ayudaremos a dar el primer paso, normalmente en un día hábil.',
    'or_call': 'o llame al',
    'related_h': 'Relacionado',
    'all_conditions': 'Todas las afecciones que tratamos',
    'reviewed': lambda reviewer, y, m: (f'<p class="reviewed-by">Revisado clínicamente por <a href="about.html">{reviewer}</a>, '
                                        f'especialista certificada en ortopedia (Orthopedic Certified Specialist) &middot; '
                                        f'Revisado en {MONTHS_ES[int(m) - 1]} de {y}</p>'),
    'clinic_line': ('<h2>Por qué los pacientes eligen ARI</h2><p>En ARI, la atención siempre es <strong>individual y en persona</strong> '
                    'con un fisioterapeuta con licencia en nuestra clínica de Bakersfield: 8200 Stockdale Hwy, Suite B2, en el centro '
                    'comercial Town &amp; Country Village, junto a Trader Joe\'s. Nuestra directora clínica, Deepa Konnur, PT, MPT, OCS, '
                    'es especialista certificada en ortopedia (Orthopedic Certified Specialist). Aceptamos la mayoría de los seguros '
                    'médicos privados y Medicare, y <strong>hablamos español</strong>, inglés e hindi.</p>'),
    'direct_access': ('<div class="callout"><strong>No necesita una referencia médica para empezar.</strong> En California, puede ver '
                      'a un fisioterapeuta directamente hasta por 12 visitas o 45 días, lo que ocurra primero. Algunos seguros todavía '
                      'piden una referencia para cubrir el tratamiento; llámenos al <a href="tel:6612828584">(661) 282-8584</a> y le '
                      'ayudamos a verificarlo.</div>'),
    'referral_faq': ('¿Necesito una referencia del médico para ir a fisioterapia en California?',
                     'No. En California puede ver a un fisioterapeuta directamente hasta por 12 visitas o 45 días, lo que ocurra '
                     'primero. Algunos seguros todavía piden una referencia para cubrir el tratamiento; llámenos al (661) 282-8584 y le '
                     'ayudamos a verificarlo.'),
    'page_cta': ('<div class="page-cta"><p class="page-cta-h">¿Listo para sentirse mejor?</p><p>Hable con un fisioterapeuta con '
                 'licencia en ARI, de forma individual. Solicite una evaluación y le responderemos, normalmente en un día hábil. '
                 '<strong>Hablamos español.</strong></p><div class="page-cta-btns"><a href="' + ES_FORM + '" class="btn btn-primary">'
                 'Solicitar una evaluación</a><a href="tel:6612828584" class="btn btn-on-dark">Llamar al (661) 282-8584</a></div></div>'),
}

NAV_ES = (f'<div class="nav-links"><a href="{ES_HOME}">Inicio</a><a href="{ES_HUB}">Afecciones</a>'
          f'<a href="{ES_FORM}">Solicitar cita</a><a href="{ES_HOME}#contacto">Contacto</a>'
          f'<a href="index.html" lang="en" hreflang="en">English</a><div class="nav-contact">')

FOOTER_ES = f'''<footer>
  <div class="foot-inner">
    <div>
      <img src="assets/logo-white-400.webp" alt="ARI Physical Therapy" width="1262" height="562">
      <p class="foot-desc">Fisioterapia individual y personalizada en Bakersfield, California. Le ayudamos a moverse mejor, sentirse mejor y vivir mejor.</p>
      <p class="foot-tag">Hablamos español</p>
    </div>
    <div><div class="foot-h">Enlaces</div><div class="foot-links">
      <a href="{ES_HOME}">Inicio</a><a href="{ES_HUB}">Afecciones que tratamos</a>
      <a href="{ES_FORM}">Solicitar una cita</a><a href="{ES_HOME}#contacto">Contacto</a>
      <a href="index.html" lang="en" hreflang="en">English website</a><a href="privacy-policy.html">Política de privacidad (en inglés)</a>
    </div></div>
    <div><div class="foot-h">Contacto</div><div class="foot-c">
      <a href="tel:6612828584">(661) 282-8584</a><br><a href="mailto:contactus@ariptcare.com">contactus@ariptcare.com</a><br>Fax: (661) 727-0005<br>
      8200 Stockdale Hwy, Suite B2<br>Bakersfield, CA 93311<br>Lunes a viernes &middot; 8:00 AM &ndash; 6:00 PM
    </div></div>
  </div>
  <div class="foot-bot"><span>&copy; 2026 ARI Physical Therapy. Todos los derechos reservados.</span>
  <span><a href="privacy-policy.html">Privacidad</a> &middot; <a href="sms-terms.html">Términos de SMS</a> &middot; 8200 Stockdale Hwy Suite B2, Bakersfield, CA 93311</span></div>
</footer>'''


def es_shell(s, url, en_url=None):
    """Turn an English page shell into a Spanish one. url = this page's absolute URL; en_url = English counterpart."""
    s = s.replace('<html lang="en">', '<html lang="es">', 1)
    alt = f'\n    <link rel="alternate" hreflang="es" href="{url}">'
    if en_url:
        alt += f'\n    <link rel="alternate" hreflang="en" href="{en_url}">\n    <link rel="alternate" hreflang="x-default" href="{en_url}">'
    s = re.sub(r'(<link rel="canonical" href="[^"]*">)', lambda m: m.group(1) + alt, s, count=1)
    s = re.sub(r'(<meta property="og:site_name" content="[^"]*">)', lambda m: m.group(1) + '\n    <meta property="og:locale" content="es_US">', s, count=1)
    s = s.replace('<a href="appointment.html" class="btn-book-topbar">Book an Appointment</a>',
                  f'<a href="{ES_FORM}" class="btn-book-topbar">Solicitar una cita</a>', 1)
    s = re.sub(r'<div class="nav-links">.*?<div class="nav-contact">', lambda m: NAV_ES, s, count=1, flags=re.S)
    s = s.replace('<a href="appointment.html" class="btn btn-primary">Book an Appointment</a>',
                  f'<a href="{ES_FORM}" class="btn btn-primary">Solicitar una cita</a>', 1)
    s = s.replace('<a href="index.html" class="nav-logo">', f'<a href="{ES_HOME}" class="nav-logo">', 1)
    s = s.replace('aria-label="Search the site"', 'aria-label="Buscar en el sitio"').replace('aria-label="Open menu"', 'aria-label="Abrir menú"')
    s = re.sub(r'<footer>.*?</footer>', lambda m: FOOTER_ES, s, count=1, flags=re.S)
    return s


def en_alternate(s, en_url, es_url):
    """Add hreflang links to an ENGLISH page pointing at its Spanish version (idempotent)."""
    if f'hreflang="es" href="{es_url}"' in s:
        return s
    alt = (f'\n    <link rel="alternate" hreflang="en" href="{en_url}">\n    <link rel="alternate" hreflang="es" href="{es_url}">'
           f'\n    <link rel="alternate" hreflang="x-default" href="{en_url}">')
    return re.sub(r'(<link rel="canonical" href="[^"]*">)', lambda m: m.group(1) + alt, s, count=1)
