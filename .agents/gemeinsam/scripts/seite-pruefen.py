"""
seite-pruefen.py - HTML-Prüfung aus AGENTS.md für eine Seite, plus Test im Headless-Browser.

Aufruf (im Projektordner, am Mac python3 statt python):
  python .agents/gemeinsam/scripts/seite-pruefen.py Unterricht/.../index.html [weitere Seiten]
      [--arbeitsordner <Ordner>]   wohin Screenshot, Leerdruck-PDF und PDF-Export kommen (Standard: Temp-Ordner)
      [--ohne-browser]             nur die statischen Prüfungen

Geprüft wird die GEBAUTE Fassung (bauen.py: Kern aus kern/ und Bilder aus bilder/ eingebettet, das ist die Seite, die ins
Lernpaket kommt). Eine Seite in alter Form (alles eingebettet) ist ihre eigene gebaute Fassung. Dazu die Quelle selbst:
<link> und <script src> zeigen nur auf Dateien in kern/ (oder bilder/), die es gibt, und die Quelle lädt im Browser
ohne Fehlerkasten.
Statisch: Anfang <!doctype html>, Ende </html>, Tag-Paare, Platzhalter/TODO/TEMPLATE-Kommentar/Markdown-Zeichen,
keine externen src/link, doppelte data-k, Bilder ohne alt-Text (Fehler), Sprünge in der Überschriftenfolge (Hinweis),
Felder in .print-alt, Ergebnis einer interaktiven Aufgabe (data-score) ohne Papierfassung,
Schriften fürs Zeichnen gefüllt und alle Zeichen der Seite in den Schriften vorhanden, Vorlagenblöcke aktuell (sync-vorlage.py).
Seiten aus einer Vorlage eines Teams (<meta name="vorlage" content="<team>/<Name>.html">): Die Vorlage gibt es.
Seiten aus einer freien Vorlage (<meta name="vorlage-art" content="frei">): Lösungen stehen hinter dem Hash; Vorlagenblöcke, Leerdruck und PDF-Export werden nicht geprüft (keine Bewertung).
Anleitungen zu einem Test (Skill moodle-test, index.html in Test-<…>/ neben Test-<…>.mbz): keine {{…}}-Platzhalter
übrig; Leerdruck und PDF-Export werden nicht geprüft (nur für Lehrkräfte, kein PDF-Knopf, gedruckt wird mit "Drucken").
Browser (Edge oder Chrome, headless, auf KOPIEN im Arbeitsordner, die Seite selbst bleibt unverändert):
  1. Seite laden: kein roter Fehlerkasten (auch keine unbehandelte Promise-Ablehnung), Screenshot <name>-ansicht.png
  2. Leeres Arbeitsblatt (Lehrkraft-Modus, Knopf "Leeres Arbeitsblatt drucken") als <name>-leerdruck.pdf
  3. "Als PDF speichern": das erzeugte PDF als <name>-export.pdf, mit Angabe der eingebetteten Schrift
Die PDFs und das Bild danach mit dem Lesewerkzeug der KI ansehen (`werkzeuge.md`).
Exitcode 0 = alles bestanden, 1 = Fehler gefunden. Nur Python-Standardbibliothek.
"""
import argparse
import base64
import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HIER)))
BROWSER = (
    r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
)
BLANK_ALT = 'try { window.print(); } finally { endBlank(); }'
_SYNC = []
_BAUEN = []


def sync():
    """sync-vorlage.py als Modul (Vorlagen der Teams: ist_frei, vorlage_von)."""
    if not _SYNC:
        import importlib.util
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('sync_vorlage', os.path.join(HIER, 'sync-vorlage.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _SYNC.append(mod)
    return _SYNC[0]


def bauen():
    """bauen.py als Modul (gebaut: die Seite mit eingebettetem Kern und Bildern)."""
    if not _BAUEN:
        import importlib.util
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('bauen', os.path.join(HIER, 'bauen.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _BAUEN.append(mod)
    return _BAUEN[0]


def ZEICHNEN(s):
    kopf = s[:s.find('</head>')] if '</head>' in s else s
    return re.search(r'<meta\s+name="schrift"\s+content="zeichnen"', re.sub(r'(?s)<!--.*?-->', '', kopf)) is not None


def ist_test_anleitung(p):
    """Anleitung zu einem Test (Skill moodle-test): index.html in einem Ordner Test-<…> neben Test-<…>.mbz
    (Test-Ordner wie MBZ_ERLAUBT in pruefen.py). Nur für Lehrkräfte, ohne Lehrkraft-Modus und PDF-Knopf."""
    ordner = os.path.dirname(os.path.abspath(p))
    name = os.path.basename(ordner)
    return (os.path.basename(p) == 'index.html' and name.startswith('Test-')
            and os.path.isfile(os.path.join(ordner, name + '.mbz')))


def ist_uebungs_app(s):
    """Übungs-App (Skill uebungs-app): eigene kleine Seite mit den Einträgen als JSON, ohne Leerdruck und PDF-Export."""
    return '<script id="app-data" type="application/json">' in s


def lesen(p):
    with open(p, 'rb') as f:
        return f.read().decode('utf-8-sig')


# ---------- WOFF: Zeichen in der Schrift (cmap) ----------

def woff_tabellen(data):
    if data[:4] != b'wOFF':
        raise ValueError('keine WOFF-Datei')
    num = struct.unpack('>H', data[12:14])[0]
    tabs = {}
    for i in range(num):
        tag, off, clen, olen, _ = struct.unpack('>4sIIII', data[44 + 20 * i:64 + 20 * i])
        raw = data[off:off + clen]
        tabs[tag.decode('latin-1')] = zlib.decompress(raw) if clen < olen else raw
    return tabs


def cmap_zeichen(cmap):
    n = struct.unpack('>H', cmap[2:4])[0]
    zeichen = set()
    for i in range(n):
        pid, eid, off = struct.unpack('>HHI', cmap[4 + 8 * i:12 + 8 * i])
        fmt = struct.unpack('>H', cmap[off:off + 2])[0]
        if fmt == 4:
            segx2 = struct.unpack('>H', cmap[off + 6:off + 8])[0]
            ends = struct.unpack('>%dH' % (segx2 // 2), cmap[off + 14:off + 14 + segx2])
            starts = struct.unpack('>%dH' % (segx2 // 2), cmap[off + 16 + segx2:off + 16 + 2 * segx2])
            for a, e in zip(starts, ends):
                if a != 0xFFFF:
                    zeichen.update(range(a, e + 1))
        elif fmt == 12:
            ngr = struct.unpack('>I', cmap[off + 12:off + 16])[0]
            for g in range(ngr):
                a, e, _ = struct.unpack('>III', cmap[off + 16 + 12 * g:off + 28 + 12 * g])
                zeichen.update(range(a, e + 1))
    return zeichen


def schrift_zeichen(s):
    """Zeichen je Familie aus dem eingebetteten <style id="zeichen-schriften">."""
    fam = {}
    for m in re.finditer(r'@font-face\{font-family:"([^"]+)";[^}]*?base64,([A-Za-z0-9+/=]+)', s):
        try:
            z = cmap_zeichen(woff_tabellen(base64.b64decode(m.group(2)))['cmap'])
        except Exception:
            continue
        fam.setdefault(m.group(1), set()).update(z)
    return fam


def sichtbarer_text(s):
    t = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', s)
    t = re.sub(r'(?s)<!--.*?-->', ' ', t)
    svg = ' '.join(re.findall(r'(?is)<text\b[^>]*>(.*?)</text>', t))
    t = re.sub(r'<[^>]+>', ' ', t)
    return html.unescape(t), html.unescape(re.sub(r'<[^>]+>', ' ', svg))


# ---------- statische Prüfungen ----------

def statisch(p, s, quelle=None):
    """s: gebaute Fassung, quelle: Text der Seite im Projektordner (None: wie s)."""
    fehler, hinweise = [], []
    if quelle is not None and quelle != s:
        fehler += ['Quelle: ' + t for t in bauen().quelle_fehler(quelle, os.path.dirname(os.path.abspath(p)))]
    if not s.lstrip().lower().startswith('<!doctype html>'):
        fehler.append('1. Zeile ist nicht <!doctype html>')
    if not s.rstrip().endswith('</html>'):
        fehler.append('Datei endet nicht mit </html> (abgeschnitten?)')
    ohne = re.sub(r'(?is)<script\b.*?</script>', '', s)
    ohne = re.sub(r'(?s)<!--.*?-->', '', ohne)
    for tag in ('section', 'div', 'table', 'ol', 'ul'):
        a = len(re.findall(r'<%s\b' % tag, ohne))
        b = len(re.findall(r'</%s>' % tag, ohne))
        if a != b:
            fehler.append('<%s> %d-mal geöffnet, %d-mal geschlossen' % (tag, a, b))
    sichtbar = re.sub(r'(?is)<(script|style)\b.*?</\1>', '', s)
    sichtbar = re.sub(r'(?s)<!--.*?-->', '', sichtbar)
    for ph in ('[Titel]', '[Untertitel', '[Beruf]', '[Thema]', '[1. Jahr]', '[LF · B]', '[Hilfsmittel]', 'TODO'):
        if ph in sichtbar:
            fehler.append('Platzhalter übrig: ' + ph)
    if re.search(r'<!--\s*\n\s*TEMPLATE', s):
        fehler.append('TEMPLATE-Kommentar der Vorlage nicht entfernt')
    txt = re.sub(r'<[^>]+>', ' ', sichtbar)
    if re.search(r'\*\*\S|^\s*##', txt, re.M):
        fehler.append('Markdown-Zeichen (** oder ##) im Text')
    for m in re.finditer(r'<(?:img|script|iframe|source|video|audio)\b[^>]*\ssrc\s*=\s*["\']?(https?:)', s):
        fehler.append('externe Quelle in src= (nicht offline): ' + s[m.start():m.start() + 80])
    for m in re.finditer(r'<link\b[^>]*href\s*=\s*["\']?https?:', s):
        fehler.append('externes <link>: ' + s[m.start():m.start() + 80])
    keys = re.findall(r'<(?:input|select|textarea)\b[^>]*?\sdata-k="([^"$]+)"', ohne)
    dup = sorted(set(k for k in keys if keys.count(k) > 1))
    if dup:
        fehler.append('doppelte data-k: ' + ', '.join(dup[:10]))
    for m in re.finditer(r'<img\b[^>]*>', ohne):   # Bildbeschreibung für Vorlesehilfen; alt="" nur für reinen Schmuck
        if not re.search(r'\salt\s*=', m.group(0)):
            fehler.append('Bild ohne alt-Text (Bildbeschreibung): ' + m.group(0)[:90])
    stufe = 0
    for m in re.finditer(r'<h([1-6])\b[^>]*>(.*?)</h\1>', ohne, re.S):   # Gliederung für Vorlesehilfen
        neu = int(m.group(1))
        if stufe and neu > stufe + 1:
            hinweise.append('Überschrift springt von h%d auf h%d: %s' % (stufe, neu, re.sub(r'<[^>]+>|\s+', ' ', m.group(2)).strip()[:60]))
        stufe = neu
    for m in re.finditer(r'<(\w+)[^>]*class="[^"]*\bprint-alt\b[^"]*"', s):
        tag = m.group(1)
        e = s.find('</%s>' % tag, m.end())
        if re.search(r'<(input|select|textarea)\b', s[m.end():e if e > 0 else m.end() + 4000]):
            fehler.append('Eingabefeld in .print-alt (zählt nicht, verschiebt Schlüssel): ' + s[m.start():m.start() + 70])
    for m in re.finditer(r'<div class="task\b', s):
        e = s.find('<div class="task', m.end())
        teil = s[m.start():e if e > 0 else len(s)]
        if 'data-score' in teil and 'print-alt' not in teil:
            tt = re.search(r'class="tt">([^<]*)', teil)
            hinweise.append('Ergebnis einer interaktiven Aufgabe ohne Papierfassung (.print-alt) für den Leerdruck: ' + (tt.group(1) if tt else '?'))
    vorlage, frei = sync().vorlage_von(s), sync().ist_frei(s)
    if vorlage and not os.path.isfile(os.path.join(ROOT, 'Vorlagen', *vorlage.split('/'))):
        fehler.append('Vorlage Vorlagen/%s (aus <meta name="vorlage">) gibt es nicht' % vorlage)
    if frei:
        if not vorlage:
            fehler.append('Seite aus einer freien Vorlage ohne <meta name="vorlage" content="<team>/<Name>.html">')
        if re.search(r'class="[^"]*\b(?:sol|answers)\b', s) and not re.search(
                r'<meta\s+name="loesung-hash"\s+content="[0-9a-f]{64}"', s):
            fehler.append('Lösungen ohne Lösungssperre: <meta name="loesung-hash"> ist leer (seite.md)')
        hinweise.append('Seite aus einer freien Vorlage: ohne Bewertung, Vorlagenblöcke, Leerdruck und PDF-Export nicht geprüft')
    if ist_test_anleitung(p):
        for ph in sorted(set(re.findall(r'\{\{[A-Z_]+\}\}', re.sub(r'(?s)<!--.*?-->', '', s)))):
            fehler.append('Platzhalter der Anleitung übrig: %s (build-test-mbz.py neu ausführen)' % ph)
        hinweise.append('Anleitung zu einem Test (Skill moodle-test): Leerdruck und PDF-Export nicht geprüft')
    if ist_uebungs_app(s):
        m = re.search(r'<script id="app-data" type="application/json">(.*?)</script>', s, re.S)
        try:
            if not m:
                raise ValueError('der Block endet nicht mit </script> (Datei abgeschnitten?)')
            json.loads(m.group(1))
        except ValueError as e:
            fehler.append('Übungs-App: Die Einträge (JSON in app-data) sind kaputt: %s' % e)
        hinweise.append('Übungs-App (Skill uebungs-app): Leerdruck und PDF-Export gibt es dort nicht, nicht geprüft')
    if ZEICHNEN(s):
        if '@font-face{font-family:"Zeichenschrift"' not in s:
            fehler.append('Schriften fürs Zeichnen fehlen: sync-vorlage.py --datei <Seite> --schreiben ausführen')
        else:
            fam = schrift_zeichen(s)
            text, svgtext = sichtbarer_text(s)
            for name, quelle in (('Zeichenschrift', text), ('Zeichenschrift Norm', svgtext)):
                vorhanden = fam.get(name, set())
                fehlt = sorted(set(c for c in quelle if ord(c) > 32 and ord(c) not in vorhanden and not c.isspace()
                                   and not 0x1F000 <= ord(c) <= 0x1FFFF))
                if fehlt:
                    hinweise.append('%s: Zeichen fehlen in der Schrift (Ersatzschrift): %s' % (name, ' '.join(fehlt[:40])))
    code, ausgabe = vorlage_pruefen(p)
    if code == 1:
        hinweise.append('Vorlagenblöcke nicht aktuell: sync-vorlage.py --datei <Seite> --schreiben')
    elif code == 2:
        zeilen = [z for z in ausgabe.splitlines() if 'FEHLER' in z] or ausgabe.strip().splitlines() or ['(keine Ausgabe)']
        fehler.append('sync-vorlage.py findet die Vorlagenblöcke nicht: ' + zeilen[0][:200])
    elif code != 0:   # fail-closed: Ob die Seite zur Vorlage passt, ist dann nicht geprüft
        fehler.append('sync-vorlage.py ist abgestürzt, die Vorlagenblöcke sind nicht geprüft: ' + ausgabe[:300])
    return fehler, hinweise


def vorlage_pruefen(p):
    """sync-vorlage.py --datei <p> --pruefen im selben Prozess (das Modul ist schon geladen, kein neuer Python-Start).
    Rückgabe (Code, Ausgabe): 0 aktuell, 1 weicht ab, 2 Blöcke nicht gefunden, 3 abgestürzt (Ausgabe = Fehlermeldung)."""
    import contextlib
    import io
    puffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(puffer):
            code = sync().main(['--datei', p, '--pruefen'])
    except SystemExit as e:   # argparse oder sys.exit im Modul
        code = e.code if isinstance(e.code, int) else 3
    except Exception as e:   # absichtlich breit: jeder Absturz wird zum Fehler der Prüfung, nie zum Hinweis
        return 3, '%s: %s' % (type(e).__name__, e)
    return (code if code in (0, 1, 2) else 3), puffer.getvalue()


# ---------- Browser ----------

INJEKT_FEHLER = """<script>
window.addEventListener('unhandledrejection', function (e) {
  var b = document.getElementById('page-error');
  if (b) { b.style.display = 'block'; b.textContent = 'Etwas ist schiefgelaufen (Promise): ' + (e.reason && e.reason.message || e.reason); }
});
</script>"""

INJEKT_PDF = """<script>
(function () {
  var out = document.createElement('pre'); out.id = '__pdf__'; out.hidden = true; document.body.appendChild(out);
  URL.createObjectURL = function (b) {
    b.arrayBuffer().then(function (buf) {
      var u = new Uint8Array(buf), s = '', i;
      for (i = 0; i < u.length; i += 8192) s += String.fromCharCode.apply(null, u.subarray(i, i + 8192));
      out.textContent = 'PDF:' + btoa(s);
    });
    return 'about:blank';
  };
  HTMLAnchorElement.prototype.click = function () { out.setAttribute('data-name', this.download || ''); };
  window.addEventListener('load', function () { setTimeout(function () { document.getElementById('pdfBtn').click(); }, 800); });
})();
</script>"""

INJEKT_LEER = """<script>
window.print = function () {};
window.addEventListener('load', function () { setTimeout(function () {
  document.body.classList.add('solOpen'); document.getElementById('blankBtn').click();
  window.dispatchEvent(new Event('beforeprint'));
}, 800); });
</script>"""


def _liefert(b):
    """Kurztest: Der Browser muss eine winzige Seite wirklich ausgeben (Edge liefert nach manchen Updates nichts)."""
    try:
        prof = tempfile.mkdtemp(prefix='bt-')
        r = subprocess.run([b, '--headless=new', '--disable-gpu', '--no-first-run', '--user-data-dir=' + prof,
                            '--dump-dom', 'data:text/html,<p>ok</p>'], capture_output=True, timeout=30)
        shutil.rmtree(prof, ignore_errors=True)
        return b'ok' in r.stdout
    except Exception:
        return False


def browser():
    kandidaten = [b for b in BROWSER if os.path.exists(b)]
    kandidaten += [w for w in (shutil.which('msedge'), shutil.which('google-chrome'), shutil.which('chromium')) if w]
    for b in kandidaten:
        if _liefert(b):
            return b
    return kandidaten[0] if kandidaten else None


def kopie(src_text, ziel, injekt, ersetze=None):
    t = src_text
    if ersetze:
        t = t.replace(*ersetze)
    i = t.rfind('</body>')
    t = t[:i] + injekt + '\n' + t[i:] if i >= 0 else t + injekt
    with open(ziel, 'wb') as f:
        f.write(t.encode('utf-8'))


def lauf(b, prof, args, url, timeout=120):
    cmd = [b, '--headless=new', '--disable-gpu', '--enable-unsafe-swiftshader', '--use-angle=swiftshader',
           '--no-first-run', '--no-default-browser-check', '--allow-file-access-from-files',
           '--user-data-dir=' + prof] + args + [url]
    r = subprocess.run(cmd, capture_output=True, timeout=timeout)
    return r.stdout.decode('utf-8', 'replace')


def url_von(p):
    return 'file:///' + os.path.abspath(p).replace('\\', '/').lstrip('/')


def im_browser(p, s, ordner, name, quelle=None):
    """s: gebaute Fassung (Kopien im Arbeitsordner), quelle: Text der Seite im Projektordner (None: wie s)."""
    fehler, hinweise, dateien = [], [], []
    b = browser()
    if not b:
        hinweise.append('Kein Edge/Chrome gefunden: Browser-Test übersprungen')
        return fehler, hinweise, dateien
    if quelle is not None and quelle != s:   # die Quelle selbst, am Ort, damit kern/ und bilder/ gefunden werden
        dom = lauf(b, os.path.join(ordner, 'browser-profil'), ['--virtual-time-budget=6000', '--dump-dom'], url_von(p))
        m = re.search(r'<div id="page-error"([^>]*)>(.*?)</div>', dom, re.S)
        if not dom.strip():
            fehler.append('Quelle: Browser lieferte keine Seite (Absturz?)')
        elif m and ('display: block' in m.group(1) or m.group(2).strip()):
            fehler.append('Quelle: Roter Fehlerkasten beim Laden aus dem Projektordner: '
                          + html.unescape(re.sub(r'<[^>]+>', '', m.group(2)))[:300])
    seite_dir = os.path.dirname(os.path.abspath(p))
    prof = os.path.join(ordner, 'browser-profil')
    # Kopien neben die Seite legen wäre nötig für Medien-Dateien; Kopien kommen in den Arbeitsordner,
    # große Medien (Video, 3D-Datei) werden dort nicht gefunden - das ist für diese Prüfung in Ordnung.
    k1 = os.path.join(ordner, name + '-ansicht.html')
    kopie(s, k1, INJEKT_FEHLER)
    dom = lauf(b, prof, ['--virtual-time-budget=6000', '--dump-dom'], url_von(k1))
    m = re.search(r'<div id="page-error"([^>]*)>(.*?)</div>', dom, re.S)
    if not dom.strip():
        fehler.append('Browser lieferte keine Seite (Absturz?)')
    elif m and ('display: block' in m.group(1) or m.group(2).strip()):
        fehler.append('Roter Fehlerkasten: ' + html.unescape(re.sub(r'<[^>]+>', '', m.group(2)))[:300])
    png = os.path.join(ordner, name + '-ansicht.png')
    lauf(b, prof, ['--virtual-time-budget=6000', '--hide-scrollbars', '--window-size=1200,1800', '--screenshot=' + png], url_von(k1))
    if os.path.exists(png):
        dateien.append(png)
    if sync().ist_frei(s) or ist_test_anleitung(p) or ist_uebungs_app(s):   # freie Vorlage, Test-Anleitung oder
        return fehler, hinweise, dateien   # Übungs-App: kein gemeinsamer Kern, also kein Leerdruck und kein PDF-Export
    # Leerdruck
    if BLANK_ALT in s:
        k2 = os.path.join(ordner, name + '-leerdruck.html')
        kopie(s, k2, INJEKT_LEER, (BLANK_ALT, 'window.print();'))
        pdf = os.path.join(ordner, name + '-leerdruck.pdf')
        lauf(b, prof, ['--virtual-time-budget=6000', '--no-pdf-header-footer', '--print-to-pdf=' + pdf], url_von(k2))
        if os.path.exists(pdf):
            dateien.append(pdf)
        else:
            fehler.append('Leerdruck-PDF wurde nicht erzeugt')
    else:
        hinweise.append('Leerdruck nicht getestet (Vorlagenzeile mit printBlank nicht gefunden)')
    # PDF-Export
    k3 = os.path.join(ordner, name + '-export.html')
    kopie(s, k3, INJEKT_PDF)
    dom = lauf(b, prof, ['--virtual-time-budget=15000', '--dump-dom'], url_von(k3))
    m = re.search(r'<pre id="__pdf__"[^>]*>PDF:([A-Za-z0-9+/=]+)</pre>', dom)
    if not m:
        fehler.append('"Als PDF speichern" hat kein PDF erzeugt')
    else:
        data = base64.b64decode(m.group(1))
        pdf = os.path.join(ordner, name + '-export.pdf')
        with open(pdf, 'wb') as f:
            f.write(data)
        dateien.append(pdf)
        fonts = sorted(set(re.findall(rb'/BaseFont\s*/([A-Za-z0-9+_-]+)', data)))
        hinweise.append('PDF-Export: %d KB, Schriften: %s' % (len(data) // 1024, ', '.join(f.decode() for f in fonts)))
        if ZEICHNEN(s) and not any(b'Zeichenschrift' in f for f in fonts):
            fehler.append('PDF-Export ohne Schrift fürs Zeichnen (Seite fürs Technische Zeichnen)')
        if b'/FontFile2' not in data and b'(?' in data:
            hinweise.append('PDF-Export enthält "?" (Zeichen ohne Ersatz in Helvetica?)')
    return fehler, hinweise, dateien


def main(argv=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # profil.py liegt daneben, egal wer main() aufruft
    import profil
    profil.utf8_ausgabe()
    ap = argparse.ArgumentParser(description='HTML-Prüfung (AGENTS.md) und Browser-Test für Seiten.')
    ap.add_argument('seiten', nargs='+')
    ap.add_argument('--arbeitsordner', default=os.path.join(tempfile.gettempdir(), 'seite-pruefen'))
    ap.add_argument('--ohne-browser', action='store_true')
    a = ap.parse_args(argv)
    os.makedirs(a.arbeitsordner, exist_ok=True)
    gesamt = 0
    for p in a.seiten:
        quelle = lesen(p)
        rel = os.path.relpath(os.path.abspath(p), ROOT)
        name = re.sub(r'[^A-Za-z0-9-]+', '-', os.path.basename(os.path.dirname(os.path.abspath(p))) or 'seite')[:60]
        try:
            s = bauen().gebaut(p)
        except bauen().BauFehler as e:
            print('%s: FEHLER (1)\n  FEHLER  Seite lässt sich nicht bauen: %s' % (rel, e))
            gesamt += 1
            continue
        fehler, hinweise = statisch(p, s, quelle)
        dateien = []
        if not a.ohne_browser:
            f2, h2, dateien = im_browser(p, s, a.arbeitsordner, name, quelle)
            fehler += f2
            hinweise += h2
        print('%s: %s' % (rel, 'BESTANDEN' if not fehler else 'FEHLER (%d)' % len(fehler)))
        for f in fehler:
            print('  FEHLER  ' + f)
        for h in hinweise:
            print('  Hinweis ' + h)
        for d in dateien:
            print('  Datei   ' + d)
        gesamt += len(fehler)
    return 1 if gesamt else 0


if __name__ == '__main__':
    sys.exit(main())
