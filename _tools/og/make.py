"""Share-preview images (og:image, 1200x630) rendered from HTML with headless Chrome.
    python3 _tools/og/make.py            # writes _tools/og/out/<name>.png
Keep text inside the middle ~1000x500: some apps crop the edges."""
import os, shutil, subprocess, tempfile, time
D = os.path.dirname(os.path.abspath(__file__)); A = os.path.abspath(os.path.join(D, '..', '..', 'assets'))
OUT = os.path.join(D, 'out'); os.makedirs(OUT, exist_ok=True)
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
PROF = tempfile.mkdtemp(prefix='ari-og-chrome-')   # throwaway browser profile, kept OUT of the repo
BASE = f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="file://{A}/ari.css">
<style>html,body{{margin:0;width:1200px;height:630px;overflow:hidden}}
.c{{position:relative;width:1200px;height:630px;overflow:hidden;background:#2B2B2B;font-family:Inter,sans-serif;color:#fff}}
.ring{{position:absolute;border-radius:50%;background:#E8630A;opacity:.13}}
.eb{{display:flex;align-items:center;gap:12px;font:700 17px Montserrat,sans-serif;letter-spacing:4px;text-transform:uppercase;color:#FF8C42}}
.eb i{{display:block;width:34px;height:3px;background:#E8630A}}
h1{{font:800 58px/1.08 Montserrat,sans-serif;letter-spacing:-1.2px;margin:0;color:#fff}}
.sub{{font-size:24px;line-height:1.45;color:rgba(255,255,255,.85)}}
.foot{{font:600 21px Inter,sans-serif;color:#fff}}.foot b{{color:#FF8C42}}
</style></head><body>'''
OPTS = {
 'A-brand': f'''<div class="c" style="border-right:14px solid #E8630A">
  <div class="ring" style="width:520px;height:520px;top:-210px;right:-150px"></div><div class="ring" style="width:300px;height:300px;bottom:-150px;right:260px"></div>
  <div style="position:absolute;left:96px;top:78px;right:120px;display:flex;flex-direction:column;gap:26px">
    <img src="file://{A}/logo-white.png" style="width:250px">
    <div class="eb"><i></i>Bakersfield, California</div>
    <h1>One-on-one physical therapy, every visit</h1>
    <div class="sub">With a licensed physical therapist. Orthopedics, pelvic health, pediatrics, pregnancy &amp; postpartum.</div>
  </div>
  <div class="foot" style="position:absolute;left:96px;bottom:62px">ariphysicaltherapy.com &nbsp;<b>&middot;</b>&nbsp; (661) 282-8584</div></div>''',
 'B-clinic-photo': f'''<div class="c">
  <img src="file://{A}/IMG_8165.jpg" style="position:absolute;left:0;top:0;width:560px;height:630px;object-fit:cover;object-position:50% 60%">
  <div style="position:absolute;left:560px;top:0;width:640px;height:630px;background:#2B2B2B;border-left:10px solid #E8630A;overflow:hidden">
    <div class="ring" style="width:380px;height:380px;top:-170px;right:-120px"></div>
    <div style="position:absolute;left:62px;top:70px;right:56px;display:flex;flex-direction:column;gap:24px">
      <img src="file://{A}/logo-white.png" style="width:220px">
      <h1 style="font-size:50px">One-on-one physical therapy in Bakersfield</h1>
      <div class="sub" style="font-size:22px">Every visit with a licensed physical therapist.</div>
    </div>
    <div class="foot" style="position:absolute;left:62px;bottom:58px;font-size:19px">ariphysicaltherapy.com &nbsp;<b>&middot;</b>&nbsp; (661) 282-8584</div></div></div>''',
 'C-deepa': f'''<div class="c" style="border-right:14px solid #E8630A">
  <div class="ring" style="width:420px;height:420px;top:-120px;right:-90px"></div>
  <div style="position:absolute;right:86px;top:95px;width:340px;height:440px;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 0 0 8px rgba(232,99,10,.9)">
    <img src="file://{A}/deepa-konnur.jpg" style="width:100%;height:100%;object-fit:cover;object-position:50% 12%"></div>
  <div style="position:absolute;left:90px;top:74px;width:590px;display:flex;flex-direction:column;gap:24px">
    <img src="file://{A}/logo-white.png" style="width:230px">
    <div class="eb"><i></i>Specialist-led care</div>
    <h1 style="font-size:50px">One-on-one physical therapy in Bakersfield</h1>
    <div class="sub" style="font-size:22px">Led by Deepa Konnur, PT, MPT, OCS, board-certified Orthopedic Certified Specialist</div>
  </div>
  <div class="foot" style="position:absolute;left:90px;bottom:58px;font-size:19px">ariphysicaltherapy.com &nbsp;<b>&middot;</b>&nbsp; (661) 282-8584</div></div>''',
}
for name, html in OPTS.items():
    src = os.path.join(OUT, name + '.html'); open(src, 'w').write(BASE + html + '</body></html>')
    png = os.path.join(OUT, name + '.png')
    if os.path.exists(png): os.remove(png)
    p = subprocess.Popen([CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--allow-file-access-from-files', f'--user-data-dir={PROF}',
                          '--window-size=1200,630', '--virtual-time-budget=3000', f'--screenshot={png}', 'file://' + src], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(40):
        if os.path.exists(png) and os.path.getsize(png) > 0: time.sleep(1); break
        time.sleep(0.5)
    p.kill(); print(png)
shutil.rmtree(PROF, ignore_errors=True)
