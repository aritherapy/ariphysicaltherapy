"""Tell Bing (and other IndexNow engines) which pages changed, right after a push to main.

    python3 _tools/indexnow.py                  # pages changed in the last commit
    python3 _tools/indexnow.py --since <sha>    # pages changed since a commit
    python3 _tools/indexnow.py --all            # every URL in sitemap.xml (one-time / after big changes)
    python3 _tools/indexnow.py page.html ...    # specific pages

Wait for the GitHub Pages build to finish first, so engines fetch the new version.
The key file (506b8095d9bbe02966077e7956d742c2.txt) must stay at the site root.
"""
import json, os, re, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://ariphysicaltherapy.com/'
KEY = '506b8095d9bbe02966077e7956d742c2'
SKIP = {'404.html', 'employees.html', 'review-display.html', 'privacy-policy.html', 'sms-terms.html'}


def url_for(f):
    return SITE if f == 'index.html' else SITE + f


def changed(since):
    out = subprocess.run(['git', '-C', ROOT, 'diff', '--name-status', since, 'HEAD'], capture_output=True, text=True, check=True).stdout
    files = []
    for line in out.splitlines():
        parts = line.split('\t')
        name = parts[-1]
        if '/' not in name and name.endswith('.html') and name not in SKIP:
            files.append(name)   # deleted pages are sent too, so engines drop them faster
    return files


def main(argv):
    if '--all' in argv:
        urls = re.findall(r'<loc>([^<]+)</loc>', open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8').read())
    elif '--since' in argv:
        urls = [url_for(f) for f in changed(argv[argv.index('--since') + 1])]
    elif argv:
        urls = [url_for(os.path.basename(f)) for f in argv]
    else:
        urls = [url_for(f) for f in changed('HEAD~1')]
    urls = sorted(set(urls))
    if not urls:
        print('IndexNow: nothing to send'); return
    body = json.dumps({'host': 'ariphysicaltherapy.com', 'key': KEY, 'keyLocation': SITE + KEY + '.txt', 'urlList': urls[:10000]}).encode()
    req = urllib.request.Request('https://api.indexnow.org/indexnow', data=body, headers={'Content-Type': 'application/json; charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f'IndexNow: sent {len(urls)} URL(s), HTTP {r.status}')
    except urllib.error.HTTPError as e:
        print(f'IndexNow: HTTP {e.code} {e.reason} (202/200 = accepted; 403 = key file not live yet; 422 = URL/host mismatch)')


if __name__ == '__main__':
    main(sys.argv[1:])
