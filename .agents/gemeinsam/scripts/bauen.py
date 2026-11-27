"""
bauen.py - setzt aus einer Quellseite (kleine index.html mit verlinktem Kern) die eine eigenständige Seite zusammen.

Die Quelle liegt in Git und lässt sich per Doppelklick im Projektordner öffnen: Stil und Script der Vorlage stehen
einmal in einem Ordner kern/ (.agents/gemeinsam/templates/kern/ und Vorlagen/<Teamname>/kern/) und werden mit
relativen Adressen geladen. Nur die gebaute Fassung (Kern eingebettet, Bilder aus bilder/ als data:-Adresse) geht ins
Lernpaket und zu den Schülerinnen und Schülern. Eine Seite ohne solche Verweise kommt unverändert zurück.
Die Schrift fürs Technische Zeichnen liegt ebenso einmal in kern/schrift-zeichnen.css (sync-vorlage.py schreibt sie aus
dem Schulprofil): Die Quelle trägt <link rel="stylesheet" href="…/kern/schrift-zeichnen.css" id="zeichen-schriften">, die
gebaute Seite wieder <style id="zeichen-schriften">…</style> (das Script der Vorlage liest die Schrift daraus fürs PDF).

Aufruf (im Projektordner, am Mac python3 statt python):
  python .agents/gemeinsam/scripts/bauen.py <Seite> [--nach <Ordner>]   gebaute Seite in den Temp-Ordner (oder --nach)
  python .agents/gemeinsam/scripts/bauen.py --auslagern [<Seite> ...]   Probelauf: Kern auslagern (ohne Seite: alle in Unterricht/)
  ... --auslagern ... --schreiben                                       wirklich schreiben, nur wenn gebaut(neu) == alt
  python .agents/gemeinsam/scripts/bauen.py --bilder [<Seite> ...]      Probelauf: Bilder nach bilder/ auslagern (mit --schreiben wirklich)

Als Modul: bauen.gebaut(pfad) liefert den Text der eigenständigen Seite (Text ohne BOM), bauen.gebaut_bytes(pfad) die
Bytes. Fehler (fehlende Datei, Verweis aus dem Projektordner hinaus): BauFehler.
Nur Python-Standardbibliothek (Windows und Mac).
"""
import argparse
import base64
import glob
import os
import re
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HIER)
ROOT = os.path.dirname(os.path.dirname(SKILL))
TPL = os.path.join(SKILL, 'templates')
KERN_TPL = os.path.join(TPL, 'kern')
VORLAGEN = os.path.join(ROOT, 'Vorlagen')
ALLG_NAME = 'Allgemeinbildung.html'
FACH_NAME = 'Fachunterricht.html'

# <!-- <Vorlage>:<Block> --> ... <!-- /<Vorlage>:<Block> -->
REGION = re.compile(r'<!-- ([^\s>]+):(head|tools|modals|scripts|stil|script) -->(.*?)<!-- /\1:\2 -->', re.S)
STYLE = re.compile(r'<style>(.*?)</style>', re.S)
SCRIPT = re.compile(r'<script>(.*?)</script>', re.S)
LINK = re.compile(r'<link rel="stylesheet" href="([^"]+)">')
LINK_ID = re.compile(r'<link rel="stylesheet" href="([^"]+)" id="([\w-]+)">')   # wird zu <style id="…">
SCHRIFT_ID, SCHRIFT_DATEI = 'zeichen-schriften', 'schrift-zeichnen.css'
SCHRIFT_STIL = re.compile(r'<style id="%s">(.+?)</style>' % SCHRIFT_ID, re.S)   # leerer Platzhalter: nichts auszulagern
SCRIPT_SRC = re.compile(r'<script src="([^"]+)"></script>')
BILD = re.compile(r'\b(src|href)="(bilder/[^"]+)"')
MIME = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif',
        '.svg': 'image/svg+xml', '.webp': 'image/webp'}


class BauFehler(Exception):
    pass


def eol_von(s):
    return '\r\n' if '\r\n' in s else '\n'


def norm(s, eol):
    return re.sub(r'\r?\n', eol, s)


def lesen(path):
    """(Text, BOM?) mit unveränderten Zeilenenden."""
    with open(path, 'rb') as f:
        raw = f.read()
    return raw.decode('utf-8-sig'), raw.startswith(b'\xef\xbb\xbf')


# ---------- Kern: welcher Block liefert welche Dateien ----------

def kern_ordner(kennung):
    """Ordner kern/ zu einer Vorlage ("Fachunterricht.html" oder "<team>/<Name>.html")."""
    if kennung in (FACH_NAME, ALLG_NAME):
        return KERN_TPL
    team = kennung.split('/')[0]
    if '/' not in kennung or team in ('', '.', '..'):
        raise BauFehler('Unbekannte Vorlage in der Markierung: ' + kennung)
    return os.path.join(VORLAGEN, team, 'kern')


def stuecke(block, kennung, name):
    """Die auslagerbaren Elemente eines Blocks: [(Anfang, Ende, Tag, Dateiname, Inhalt)] (Stellen im Blocktext).
    Fachunterricht:head das <style> ohne Attribut und die gefüllte Schrift fürs Zeichnen (<style id="zeichen-schriften">,
    Tag 'style-id'), :scripts beide <script>, bei eigenen Blöcken (stil, script) das eine Element. Was nicht genau so
    aussieht, wird nicht ausgelagert (leere Liste)."""
    base = os.path.basename(kennung)[:-5] if kennung.endswith('.html') else os.path.basename(kennung)
    if name in ('head', 'stil'):
        treffer = list(STYLE.finditer(block))
        if len(treffer) != 1:
            return []
        suffix = 'head.css' if name == 'head' else 'stil.css'
        out = [(treffer[0].start(), treffer[0].end(), 'style', '%s.%s' % (base, suffix), treffer[0].group(1))]
        schrift = list(SCHRIFT_STIL.finditer(block)) if name == 'head' and kennung == FACH_NAME else []
        if len(schrift) == 1:
            out.append((schrift[0].start(), schrift[0].end(), 'style-id', SCHRIFT_DATEI, schrift[0].group(1)))
        return sorted(out)
    if name in ('scripts', 'script'):
        treffer = list(SCRIPT.finditer(block))
        if name == 'script' and len(treffer) != 1 or not treffer:
            return []
        out = []
        for i, m in enumerate(treffer, 1):
            datei = '%s.script.js' % base if name == 'script' else '%s.scripts-%d.js' % (base, i)
            out.append((m.start(), m.end(), 'script', datei, m.group(1)))
        return out
    return []


def kern_text(inhalt):
    """So liegt der Text in der Kern-Datei: Zeilenende \\n."""
    return norm(inhalt, '\n')


# ---------- gebaut ----------

_cache = {}


def _datei_text(abs_pfad):
    if abs_pfad not in _cache:
        with open(abs_pfad, 'rb') as f:
            _cache[abs_pfad] = f.read().decode('utf-8-sig')
    return _cache[abs_pfad]


def _im_projekt(abs_pfad):
    rel = os.path.relpath(abs_pfad, ROOT)
    return not (rel == '..' or rel.startswith('..' + os.sep) or os.path.isabs(rel))


# Übergang nach dem Umzug von .claude/ nach .agents/ (22.11.2026): Seiten, die noch auf den alten Kern-Pfad zeigen
ALT_KERN = '.claude/gemeinsam/templates/kern/'
ALT_KERN_HINWEIS = ('Verweis auf den alten Kern-Pfad (%s, das Werkzeug liegt jetzt in .agents/): '
                    'python .agents/gemeinsam/scripts/sync-vorlage.py --datei <Seite> --schreiben ausführen')


def _ziel(seitenordner, adresse, nur_kern):
    """Absoluter Pfad eines relativen Verweises. Fehler bei Adresse nach außen, fremdem Ordner oder fehlender Datei."""
    if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', adresse) or adresse.startswith('/') or '\\' in adresse:
        raise BauFehler('Verweis ist keine relative Adresse: ' + adresse)
    p = os.path.normpath(os.path.join(seitenordner, adresse.replace('/', os.sep)))
    if not _im_projekt(p):
        raise BauFehler('Verweis führt aus dem Projektordner hinaus: ' + adresse)
    if nur_kern and os.path.basename(os.path.dirname(p)) != 'kern':
        raise BauFehler('Verweis zeigt nicht in einen Ordner kern/: ' + adresse)
    if ALT_KERN in adresse:
        raise BauFehler(ALT_KERN_HINWEIS % adresse)
    if not os.path.isfile(p):
        raise BauFehler('Datei fehlt: %s (Verweis %s)' % (os.path.relpath(p, ROOT), adresse))
    return p


def _block_aufloesen(inner, seitenordner, eol):
    def stil(m):
        return '<style>' + norm(_datei_text(_ziel(seitenordner, m.group(1), True)), eol) + '</style>'

    def stil_id(m):
        return '<style id="%s">' % m.group(2) + norm(_datei_text(_ziel(seitenordner, m.group(1), True)), eol) + '</style>'

    def skript(m):
        return '<script>' + norm(_datei_text(_ziel(seitenordner, m.group(1), True)), eol) + '</script>'
    return SCRIPT_SRC.sub(skript, LINK_ID.sub(stil_id, LINK.sub(stil, inner)))


def _bilder_aufloesen(teil, seitenordner):
    def bild(m):
        p = _ziel(seitenordner, m.group(2), False)
        if not p.startswith(os.path.join(os.path.normpath(seitenordner), 'bilder') + os.sep):
            raise BauFehler('Bild liegt nicht in bilder/ des Themenordners: ' + m.group(2))
        mime = MIME.get(os.path.splitext(p)[1].lower())
        if not mime:
            raise BauFehler('Unbekannte Bildart: ' + m.group(2))
        with open(p, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('ascii')
        return '%s="data:%s;base64,%s"' % (m.group(1), mime, b64)
    return BILD.sub(bild, teil)


def gebaut_text(s, seitenordner):
    """Text der eigenständigen Seite aus dem Text der Quelle (seitenordner: Ordner, in dem die Quelle liegt)."""
    eol = eol_von(s)
    out, pos = [], 0
    for m in REGION.finditer(s):
        out.append(_bilder_aufloesen(s[pos:m.start(3)], seitenordner))
        out.append(_block_aufloesen(m.group(3), seitenordner, eol))
        pos = m.end(3)
    out.append(_bilder_aufloesen(s[pos:], seitenordner))
    return ''.join(out)


def gebaut(pfad):
    """Text der eigenständigen Seite (ohne BOM). Seiten ohne Verweise kommen unverändert zurück."""
    s, _ = lesen(pfad)
    return gebaut_text(s, os.path.dirname(os.path.abspath(pfad)))


def gebaut_bytes(pfad):
    s, bom = lesen(pfad)
    return (b'\xef\xbb\xbf' if bom else b'') + gebaut_text(s, os.path.dirname(os.path.abspath(pfad))).encode('utf-8')


# ---------- auslagern ----------

def auslagern_block(inner, kennung, name, seitenordner):
    """(neuer Blocktext, Zahl der ersetzten Elemente): ersetzt in einem Block Stil und Script durch Verweise.
    Wo keine Kern-Dateien dazu gehören (fremde Markierung, nichts Auslagerbares), kommt der Block unverändert zurück."""
    if kennung not in (FACH_NAME, ALLG_NAME) and '/' not in kennung:
        return inner, 0   # fremde Markierung (z. B. Testvorbereitung): nicht Sache des Kerns
    teile = stuecke(inner, kennung, name)
    if not teile:
        return inner, 0
    neu, p = [], 0
    for a, e, tag, datei, _ in teile:
        ziel = os.path.join(kern_ordner(kennung), datei)
        if not os.path.isfile(ziel):
            raise BauFehler('Kern-Datei fehlt: %s (sync-vorlage.py --vorlagen)' % os.path.relpath(ziel, ROOT))
        rel = os.path.relpath(ziel, seitenordner).replace(os.sep, '/')
        neu.append(inner[p:a])
        neu.append('<link rel="stylesheet" href="%s">' % rel if tag == 'style'
                   else '<link rel="stylesheet" href="%s" id="%s">' % (rel, SCHRIFT_ID) if tag == 'style-id'
                   else '<script src="%s"></script>' % rel)
        p = e
    neu.append(inner[p:])
    return ''.join(neu), len(teile)


def auslagern_text(s, seitenordner):
    """(neuer Text, Zahl der ersetzten Elemente). Ersetzt in den markierten Blöcken Stil und Script durch Verweise."""
    out, pos, n = [], 0, 0
    for m in REGION.finditer(s):
        neu, k = auslagern_block(m.group(3), m.group(1), m.group(2), seitenordner)
        out.append(s[pos:m.start(3)])
        out.append(neu)
        pos = m.end(3)
        n += k
    out.append(s[pos:])
    return ''.join(out), n


# ---------- Kern: wer nutzt welche Datei, was ist in der Quelle erlaubt ----------

def _norm(p):
    return os.path.normcase(os.path.normpath(p))


def ist_kern_datei(rel):
    """True für eine Datei in einem Ordner kern/ (.agents/gemeinsam/templates/kern/ oder Vorlagen/<Teamname>/kern/)."""
    t = rel.replace('\\', '/').split('/')
    return (t[:4] == ['.agents', 'gemeinsam', 'templates', 'kern'] and len(t) == 5) or (
        t[0] == 'Vorlagen' and len(t) == 4 and t[2] == 'kern')


def kern_verweise(s, seitenordner):
    """Absolute Pfade aller Kern-Dateien, auf die der Text einer Quellseite verweist (ohne zu prüfen, ob es sie gibt)."""
    out = []
    for m in REGION.finditer(s):
        for rx in (LINK, LINK_ID, SCRIPT_SRC):
            for v in rx.finditer(m.group(3)):
                a = v.group(1)
                if not (re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', a) or a.startswith('/') or '\\' in a):
                    out.append(os.path.normpath(os.path.join(seitenordner, a.replace('/', os.sep))))
    return out


def kern_dateien(pfad):
    """Wie kern_verweise, für eine Seite im Dateisystem."""
    s, _ = lesen(pfad)
    return kern_verweise(s, os.path.dirname(os.path.abspath(pfad)))


def themen_mit_kern(dateien):
    """Themenordner (ab Projektordner, mit /), deren Seite eine der geänderten Kern-Dateien (Pfade ab Projektordner) nutzt."""
    kern = {_norm(os.path.join(ROOT, *d.replace('\\', '/').split('/'))) for d in dateien if ist_kern_datei(d)}
    if not kern:
        return []
    out = []
    for seite in alle_seiten():
        try:
            if kern & {_norm(p) for p in kern_dateien(seite)}:
                out.append(os.path.relpath(os.path.dirname(seite), ROOT).replace(os.sep, '/'))
        except (OSError, UnicodeDecodeError):
            continue
    return out


BAUSKRIPT = '.agents/gemeinsam/scripts/bauen.py'


def themen_mit_bauskript(dateien, alt_ref):
    """Ist bauen.py selbst geändert: Themenordner (ab Projektordner), deren gebaute Seite mit bauen.py aus alt_ref
    (Commit) anders aussieht als mit dem jetzigen. Seiten, die sich mit einer Fassung nicht bauen lassen, zählen mit."""
    if BAUSKRIPT not in [d.replace('\\', '/') for d in dateien]:
        return []
    import subprocess
    import types
    r = subprocess.run(['git', 'show', '%s:%s' % (alt_ref, BAUSKRIPT)], cwd=ROOT, stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL)
    if r.returncode != 0:
        return []   # bauen.py ist neu: vorher gab es keine gebauten Seiten
    alt = types.ModuleType('bauen_alt')
    alt.__file__ = os.path.join(HIER, 'bauen.py')
    try:
        exec(compile(r.stdout.decode('utf-8-sig'), alt.__file__, 'exec'), alt.__dict__)
    except Exception:
        alt = None   # alte Fassung nicht lesbar: alle Seiten mit Verweisen zählen
    out = []
    for seite in alle_seiten():
        try:
            jetzt = gebaut_bytes(seite)
            with open(seite, 'rb') as f:
                quelle = f.read()
        except (BauFehler, OSError, UnicodeDecodeError):
            jetzt, quelle = None, b''
        try:
            vorher = alt.gebaut_bytes(seite) if alt else None
        except Exception:
            vorher = None
        if (jetzt != quelle) if alt is None else (jetzt != vorher):
            out.append(os.path.relpath(os.path.dirname(seite), ROOT).replace(os.sep, '/'))
    return out


RX_LADEN = re.compile(r'''<link\b[^>]*\shref\s*=\s*["']?([^"'\s>]+)|<script\b[^>]*\ssrc\s*=\s*["']?([^"'\s>]+)''', re.I)


def quelle_fehler(s, seitenordner):
    """Regel "nichts von außen" für eine Quellseite: <link> und <script src> zeigen nur auf relative Kern-Dateien,
    die es gibt (Bilder aus bilder/ prüft gebaut_text). Rückgabe: Liste von Fehlern. Externe Adressen und data: bleiben
    Sache der Prüfung der gebauten Seite (seite-pruefen.py)."""
    fehler = []
    # Verweise auf kern/ wirken nur in den markierten Blöcken (nur dort setzt gebaut den Kern ein)
    bloecke = [(m.start(3), m.end(3)) for m in REGION.finditer(s)]
    for rx in (LINK, LINK_ID, SCRIPT_SRC):
        for m in rx.finditer(s):
            if 'kern/' in m.group(1) and not any(a <= m.start() < e for a, e in bloecke):
                fehler.append('Verweis auf kern/ außerhalb der Vorlagenblöcke (wird nicht eingebettet): ' + m.group(1))
    # bilder/ kommt nicht ins Lernpaket: Jeder Verweis darauf muss so stehen, dass gebaut ihn einbettet
    rest = BILD.sub('', s)
    for m in re.finditer(r'(?<![\w-])bilder/', rest):
        fehler.append('Verweis auf bilder/, der nicht eingebettet wird (nur src="bilder/…" oder href="bilder/…"): '
                      + rest[max(0, m.start() - 40):m.end() + 30].replace('\n', ' '))
    ohne = re.sub(r'(?s)<!--.*?-->', '', s)
    for m in RX_LADEN.finditer(ohne):
        a = m.group(1) or m.group(2)
        if re.match(r'^(https?:)?//', a, re.I) or a.startswith('data:') or a.startswith('#'):
            continue   # extern oder eingebettet: Sache der Prüfung der gebauten Seite
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', a) or a.startswith('/') or '\\' in a:
            fehler.append('Verweis ist keine relative Adresse: ' + a)
            continue
        p = os.path.normpath(os.path.join(seitenordner, a.replace('/', os.sep)))
        if os.path.basename(a) == 'scorm-api.js':
            continue   # setzt der Bau ein
        if a.startswith('bilder/'):
            if not os.path.isfile(p):
                fehler.append('Bild fehlt: ' + a)
        elif ALT_KERN in a:
            fehler.append(ALT_KERN_HINWEIS % a)
        elif not ist_kern_datei(os.path.relpath(p, ROOT)):
            fehler.append('Verweis zeigt nicht auf eine Datei in kern/ oder bilder/: ' + a)
        elif not os.path.isfile(p):
            fehler.append('Kern-Datei fehlt: ' + a)
    return fehler


def erste_abweichung(a, b):
    """Beschreibung der ersten Stelle, an der zwei Texte abweichen."""
    i = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
    zeile = a.count('\n', 0, i) + 1
    return 'Zeile %d, Zeichen %d: Quelle "%s" gebaut "%s"' % (
        zeile, i, a[i:i + 40].replace('\n', '\\n'), b[i:i + 40].replace('\n', '\\n'))


def auslagern(pfad, schreiben=False):
    """(Status, Text). Status: 'ausgelagert', 'schon ausgelagert', 'ohne Kern', 'unverändert (Abweichung: ...)'."""
    s, bom = lesen(pfad)
    ordner = os.path.dirname(os.path.abspath(pfad))
    if not REGION.search(s):
        return 'ohne Kern', 'keine Vorlagenmarkierungen'
    neu, n = auslagern_text(s, ordner)
    if n == 0:
        if 'kern/' in s and (LINK.search(s) or LINK_ID.search(s) or SCRIPT_SRC.search(s)):
            return 'schon ausgelagert', ''
        return 'ohne Kern', 'nichts Auslagerbares'
    try:
        zurueck = gebaut_text(neu, ordner)
    except BauFehler as e:
        return 'Fehler', str(e)
    if zurueck != s:
        return 'Fehler', 'Rückbau weicht ab: ' + erste_abweichung(s, zurueck)
    if schreiben:
        data = (b'\xef\xbb\xbf' if bom else b'') + neu.encode('utf-8')
        tmp = pfad + '.__bauen__'
        with open(tmp, 'wb') as f:
            f.write(data)
        os.replace(tmp, pfad)
    return 'ausgelagert', '%d Elemente, %d KB -> %d KB' % (n, len(s.encode('utf-8')) // 1024, len(neu.encode('utf-8')) // 1024)


# ---------- Bilder auslagern ----------

DATA_BILD = re.compile(r'\b(src|href)="data:(image/[a-z+.-]+);base64,([A-Za-z0-9+/=]*)"')
ENDUNG = {'image/png': '.png', 'image/jpeg': '.jpg', 'image/gif': '.gif', 'image/svg+xml': '.svg', 'image/webp': '.webp'}


def _ausserhalb_von_script_und_stil(teil):
    """[(Anfang, Ende)] der Stellen eines Textes außerhalb von <script> und <style> (dort bleibt data: unangetastet)."""
    out, pos = [], 0
    for m in re.finditer(r'(?is)<(script|style)\b.*?</\1\s*>', teil):
        out.append((pos, m.start()))
        pos = m.end()
    out.append((pos, len(teil)))
    return out


def bilder_auslagern_text(s, seitenordner):
    """(neuer Text, [(Dateiname, Bytes)], Zahl der Bilder, Zahl der eingebettet gebliebenen).
    Jede data:-Adresse in src= und href= außerhalb der Vorlagenblöcke, von Script und Stil wird zu bilder/bild-NN.<Endung>
    (gleiche Bilder nur einmal). Bleibt eingebettet, wenn sie sich nicht Byte für Byte zurückbauen lässt."""
    dateien, nummern, geblieben = [], {}, [0]
    belegt = set(os.listdir(os.path.join(seitenordner, 'bilder'))) if os.path.isdir(os.path.join(seitenordner, 'bilder')) else set()

    def bild(m):
        mime, b64 = m.group(2), m.group(3)
        endung = ENDUNG.get(mime)
        try:
            roh = base64.b64decode(b64, validate=True)
        except ValueError:
            roh = None
        if (not endung or roh is None or not roh or MIME.get(endung) != mime
                or base64.b64encode(roh).decode('ascii') != b64):
            geblieben[0] += 1
            return m.group(0)
        schluessel = (mime, roh)
        if schluessel not in nummern:
            n = len(nummern) + 1
            while 'bild-%02d%s' % (n, endung) in belegt:
                n += 1
            name = 'bild-%02d%s' % (n, endung)
            belegt.add(name)
            nummern[schluessel] = name
            dateien.append((name, roh))
        return '%s="bilder/%s"' % (m.group(1), nummern[schluessel])

    def teil_bearbeiten(teil):
        out, pos = [], 0
        for a, e in _ausserhalb_von_script_und_stil(teil):
            out.append(teil[pos:a])
            out.append(DATA_BILD.sub(bild, teil[a:e]))
            pos = e
        out.append(teil[pos:])
        return ''.join(out)

    out, pos = [], 0
    for m in REGION.finditer(s):
        out.append(teil_bearbeiten(s[pos:m.start(3)]))
        out.append(m.group(3))
        pos = m.end(3)
    out.append(teil_bearbeiten(s[pos:]))
    return ''.join(out), dateien, sum(1 for _ in DATA_BILD.finditer(s)) - geblieben[0], geblieben[0]


def bilder_auslagern(pfad, schreiben=False):
    """(Status, Text). Status: 'ausgelagert', 'keine Bilder', 'Fehler'. Schreibt nur, wenn gebaut(neu) == alt Byte für Byte."""
    s, bom = lesen(pfad)
    ordner = os.path.dirname(os.path.abspath(pfad))
    neu, dateien, n, geblieben = bilder_auslagern_text(s, ordner)
    if not dateien:
        return 'keine Bilder', ('%d bleiben eingebettet' % geblieben) if geblieben else ''
    info = '%d Bilder in %d Dateien, %d KB -> %d KB' % (n, len(dateien), len(s.encode('utf-8')) // 1024, len(neu.encode('utf-8')) // 1024)
    if geblieben:
        info += ', %d bleiben eingebettet' % geblieben
    if not schreiben:
        return 'ausgelagert', info
    bilder = os.path.join(ordner, 'bilder')
    angelegt = []
    try:
        os.makedirs(bilder, exist_ok=True)
        for name, roh in dateien:
            ziel = os.path.join(bilder, name)
            with open(ziel, 'wb') as f:
                f.write(roh)
            angelegt.append(ziel)
        soll = gebaut_text(s, ordner)   # die Quelle selbst darf schon einen verlinkten Kern haben
        zurueck = gebaut_text(neu, ordner)
        if zurueck != soll:
            raise BauFehler('Rückbau weicht ab: ' + erste_abweichung(soll, zurueck))
        data = (b'\xef\xbb\xbf' if bom else b'') + neu.encode('utf-8')
        tmp = pfad + '.__bauen__'
        with open(tmp, 'wb') as f:
            f.write(data)
        os.replace(tmp, pfad)
    except (BauFehler, OSError) as e:
        for z in angelegt:
            try:
                os.remove(z)
            except OSError:
                pass
        try:
            os.rmdir(bilder)
        except OSError:
            pass
        return 'Fehler', str(e)
    return 'ausgelagert', info


def alle_seiten():
    return sorted(glob.glob(os.path.join(ROOT, 'Unterricht', '**', 'index.html'), recursive=True))


def main(argv=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # profil.py liegt daneben, egal wer main() aufruft
    import profil
    profil.utf8_ausgabe()
    ap = argparse.ArgumentParser(description='Quellseite zur eigenständigen Seite zusammensetzen; Kern auslagern.')
    ap.add_argument('seiten', nargs='*', help='Seite(n) (index.html)')
    ap.add_argument('--nach', help='Ordner für die gebaute Seite (Standard: Temp-Ordner)')
    ap.add_argument('--auslagern', action='store_true', help='Kern auslagern (ohne --schreiben nur Probelauf)')
    ap.add_argument('--bilder', action='store_true', help='Bilder (data:-Adressen) nach bilder/ auslagern (ohne --schreiben nur Probelauf)')
    ap.add_argument('--schreiben', action='store_true', help='mit --auslagern oder --bilder: Seite wirklich ändern')
    a = ap.parse_args(argv)

    if a.auslagern or a.bilder:
        seiten = [os.path.abspath(p) for p in a.seiten] or alle_seiten()
        zaehler = {}
        for p in seiten:
            status, text = auslagern(p, a.schreiben) if a.auslagern else bilder_auslagern(p, a.schreiben)
            zaehler[status] = zaehler.get(status, 0) + 1
            print('%-18s %s %s' % (status, os.path.relpath(p, ROOT), text))
        print()
        print(', '.join('%d %s' % (v, k) for k, v in sorted(zaehler.items())) +
              ('' if a.schreiben else ' (Probelauf, mit --schreiben übernehmen)'))
        return 1 if zaehler.get('Fehler') else 0

    if len(a.seiten) != 1:
        ap.error('genau eine Seite angeben (oder --auslagern, --bilder)')
    quelle = os.path.abspath(a.seiten[0])
    try:
        data = gebaut_bytes(quelle)
    except BauFehler as e:
        print('FEHLER: %s' % e)
        return 2
    ziel_ordner = a.nach or os.path.join(tempfile.gettempdir(), 'pakete-gebaut', os.path.basename(os.path.dirname(quelle)))
    os.makedirs(ziel_ordner, exist_ok=True)
    ziel = os.path.join(ziel_ordner, os.path.basename(quelle))
    with open(ziel, 'wb') as f:
        f.write(data)
    print('Gebaut: %s (%d KB)' % (ziel, len(data) // 1024))
    return 0


if __name__ == '__main__':
    sys.exit(main())
