"""
version.test.py - prüft version.py (Versionsnummer, Anzeige im Benennungsfeld, Änderungsliste, Commit nachtragen).
Aufruf im Projektordner (am Mac python3 statt python):
  python .agents/skills/baue-lernpaket/tests/version.test.py
Ablauf: legt in einem Temp-Ordner ein Test-Repo mit einer Seite aus Fachunterricht.html an und spielt den Lebenslauf einer Version durch
(bauen, erneut bauen, committen, ändern, Bewertung ändern, --major, alte Seite ohne Anzeige). Exit-Code 0 = alles bestanden.
"""
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.dont_write_bytecode = True   # kein __pycache__ im Skill-Ordner
spec = importlib.util.spec_from_file_location('version', os.path.join(ROOT, '.agents', 'skills', 'baue-lernpaket', 'scripts', 'version.py'))
version = importlib.util.module_from_spec(spec)
spec.loader.exec_module(version)
TPL = os.path.join(ROOT, '.agents', 'gemeinsam', 'templates', 'Fachunterricht.html')

for s in (sys.stdout, sys.stderr):
    try:
        s.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

repo = tempfile.mkdtemp(prefix='vertest_')
d = os.path.join(repo, 'Unterricht', '10', 'Test', 'BW1', 'Thema')
os.makedirs(d)
page = os.path.join(d, 'index.html')
ok = bad = 0
UE = 'ü'
DASH = '–'


def check(what, cond):
    global ok, bad
    if cond:
        ok += 1
        print('   ok    ' + what)
    else:
        bad += 1
        print('   FEHLER ' + what)


class GitFehler(Exception):
    pass


def run_git(*args):
    """Git im Test-Repo; bricht mit GitFehler ab, statt still weiterzulaufen (sonst kippen alle Folgeprüfungen)."""
    r = subprocess.run(['git', '-C', repo] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if r.returncode != 0:
        raise GitFehler('git %s fehlgeschlagen (Code %d): %s'
                        % (' '.join(args), r.returncode, r.stderr.decode('utf-8', 'replace').strip()))
    return r.stdout.decode('utf-8', 'replace').strip()


def commit(msg):
    run_git('add', '-A')
    # Signatur-Vorgaben und Hooks der Umgebung gelten nicht für das Wegwerf-Repo
    run_git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
            'commit', '-q', '--no-verify', '-m', msg)
    h = run_git('log', '-1', '--format=%h')
    if not h:
        raise GitFehler('git log -1 lieferte keinen Commit nach "%s"' % msg)
    return h


def html():
    with open(page, 'rb') as f:
        return f.read().decode('utf-8')


def write(text):
    with open(page, 'wb') as f:
        f.write(text.encode('utf-8'))


def put(old, new):
    write(html().replace(old, new))


def ver(aenderung='', major=False):
    return version.pflegen(page, aenderung, major)


def ver_fehler(aenderung=''):
    try:
        ver(aenderung)
    except version.VersionFehler as e:
        return str(e)
    return ''


try:
    main = ('<main class="wrap"><section class="level foundation"><h2>Einsteigerniveau</h2>'
            '<div class="task"><span class="tt">Aufgabe 1 - Bauteil</span><p>Name: <input type="text" data-k="a1-1" data-ok="Passfeder"></p></div></section></main>')
    with open(TPL, 'rb') as f:
        h = f.read().decode('utf-8-sig')
    h = re.sub(r'<main class="wrap">.*?</main>', lambda _: main, h, count=1, flags=re.S)
    write(h)
    run_git('init', '-q')

    print('Erster Bau')
    r = ver('Erste Fassung')
    check('V1.0, Commit folgt, neu', r['Version'] == '1.0' and r['Commit'] == 'folgt' and r['Neu'] and not r['Haupt'])
    check('Anzeige V1.0 mit Datum im Benennungsfeld', re.search(r'<small>Benennung<span class="ver" data-datum="\d\d\.\d\d\.\d{4}">V1\.0</span></small>', html()))
    check('Änderungsliste nach <title>', re.search(r'</title>\r?\n<!-- VERSIONEN:[^\n]*\n(V1\.0 \| \d\d\.\d\d\.\d{4} \| Commit folgt \| Erste Fassung)\r?\n-->', html()))

    print('Erneut bauen vor dem Commit')
    r = ver('Tippfehler -- Aufgabe 1')
    check('bleibt V1.0, Text angehängt, -- ersetzt', r['Version'] == '1.0' and not r['Neu'] and r['Text'] == 'Erste Fassung; Tippfehler ' + DASH + ' Aufgabe 1')
    check('Kommentar ohne -- im Text', 'Tippfehler --' not in html())
    r = ver('Tippfehler -- Aufgabe 1')
    check('gleicher Text wird nicht doppelt angehängt', r['Text'] == 'Erste Fassung; Tippfehler ' + DASH + ' Aufgabe 1' and not r['Geschrieben'])

    print('Committen, dann bauen')
    c1 = commit('V1.0')
    r = ver()
    check('Commit nachgetragen (%s)' % c1, r['Commit'] == c1 and r['Version'] == '1.0' and not r['Neu'] and r['Geschrieben'])
    r = ver()
    check('nochmal bauen ohne Änderung: nichts geschrieben', not r['Geschrieben'] and r['Version'] == '1.0')
    commit('Commit eingetragen')

    print('Text ändern (Korrektur)')
    put('Name: <input', 'Bezeichnung (' + UE + 'bersicht): <input')
    check('ohne --aenderung: Fehler mit Hinweis', '--aenderung' in ver_fehler())
    r = ver('Aufgabentext gek' + UE + 'rzt')
    check('V1.1, Nebenversion', r['Version'] == '1.1' and r['Neu'] and not r['Haupt'] and r['Commit'] == 'folgt')
    check('Umlaut im Text erhalten', r['Text'] == 'Aufgabentext gek' + UE + 'rzt')
    check('alte Zeile mit Commit darunter', re.search(r'V1\.1 \| [\d.]+ \| Commit folgt \| [^\n]+\r?\nV1\.0 \| [\d.]+ \| Commit ' + c1 + r' \|', html()))
    check('Anzeige V1.1', '>V1.1</span>' in html())

    print('Bewertung ändern vor dem Commit')
    put('data-ok="Passfeder"', 'data-ok="Passfeder|Feder"')
    r = ver('Antwort Feder zugelassen')
    check('wird V2.0 (Hauptversion)', r['Version'] == '2.0' and r['Haupt'] and 'Feder zugelassen' in r['Text'])
    c2 = commit('V2.0')
    r = ver()
    check('Commit von V2.0 nachgetragen', r['Commit'] == c2 and r['Version'] == '2.0')
    commit('Commit eingetragen')

    print('Neue Aufgabe, --major, neues Bild')
    put('</section></main>', '<div class="task"><span class="tt">Aufgabe 2</span><textarea data-k="a2-1"></textarea></div></section></main>')
    r = ver('Aufgabe 2 neu')
    check('neue Aufgabe: V3.0', r['Version'] == '3.0' and r['Haupt'])
    commit('V3.0'); ver(); commit('Commit eingetragen')
    r = ver('Nur neu gebaut', major=True)
    check('--major ohne Inhaltsänderung: V4.0', r['Version'] == '4.0' and r['Haupt'])
    commit('V4.0'); ver(); commit('Commit eingetragen')
    with open(os.path.join(d, 'bild.png'), 'wb') as f:
        f.write(bytes([1, 2, 3]))
    check('neue Datei im Ordner zählt als Änderung', '--aenderung' in ver_fehler())
    r = ver('Bild ergänzt')
    check('V4.1', r['Version'] == '4.1' and not r['Haupt'])

    print('Alte Seite ohne Anzeige im Kopf')
    h = re.sub(r'<span class="ver"[^>]*>[^<]*</span>', '', html())
    h = re.sub(r'\r?\n<!-- VERSIONEN:.*?-->', '', h, count=1, flags=re.S)
    write(h)
    r = ver('Erste Fassung mit Versionsnummer')
    check('Anzeige eingefügt, V1.0', r['Version'] == '1.0' and re.search(r'<small>Benennung<span class="ver" data-datum="[\d.]+">V1\.0</span></small>', html()))
    check('beginnt weiter mit <!doctype html>, endet mit </html>', html().startswith('<!doctype html>') and html().rstrip().endswith('</html>'))

    print('Kern in kern/: Eine Änderung dort ist eine Änderung der Seite')
    d2 = os.path.join(repo, 'Unterricht', '10', 'Test', 'BW1', 'Thema2')   # eigener Ordner: eigene Geschichte der Seite
    os.makedirs(d2)
    page2 = os.path.join(d2, 'index.html')
    kern = os.path.join(repo, 'kern', 'x.js')
    os.makedirs(os.path.dirname(kern))

    def kern_schreiben(text):
        with open(kern, 'w', encoding='utf-8', newline='') as f:
            f.write(text)

    def seite2():
        with open(page2, 'rb') as f:
            return f.read().decode('utf-8')

    def ver2(aenderung=''):
        return version.pflegen(page2, aenderung)

    def ver2_fehler():
        try:
            ver2()
        except version.VersionFehler as e:
            return str(e)
        return ''
    h = re.sub(r'<span class="ver"[^>]*>[^<]*</span>', '', html())
    h = re.sub(r'\r?\n<!-- VERSIONEN:.*?-->', '', h, count=1, flags=re.S)
    kern_schreiben('var a = 1;\n')
    with open(page2, 'wb') as f:
        f.write(h.replace('</body>', '<!-- Fachunterricht.html:scripts -->\n<script src="../../../../../kern/x.js"></script>\n'
                          '<!-- /Fachunterricht.html:scripts -->\n</body>').encode('utf-8'))
    r = ver2('Erste Fassung')
    check('neue Seite mit Kern: V1.0', r['Version'] == '1.0' and r['Neu'])
    commit('Seite mit Kern'); ver2(); commit('Commit eingetragen')
    check('nichts geändert: keine neue Version', not ver2()['Neu'])
    kern_schreiben('var a = 2;\n')
    check('nur die Kern-Datei geändert: Version verlangt', '--aenderung' in ver2_fehler())
    r = ver2('Kern geändert')
    check('Kern geändert: V1.1, keine Hauptversion', r['Version'] == '1.1' and r['Neu'] and not r['Haupt'])
    commit('Kern geändert'); ver2(); commit('Commit eingetragen')
    check('Kern unverändert: keine neue Version', not ver2()['Neu'])
except GitFehler as e:
    bad += 1
    print('   FEHLER Test abgebrochen, Git im Test-Repo: %s' % e)
finally:
    def _rw(func, path, _):   # Git legt schreibgeschützte Dateien an (Windows)
        os.chmod(path, 0o700)
        func(path)
    if sys.version_info >= (3, 12):
        shutil.rmtree(repo, onexc=_rw)
    else:
        shutil.rmtree(repo, onerror=_rw)

print('')
print('%d von %d Prüfungen bestanden.' % (ok, ok + bad))
sys.exit(1 if bad else 0)
