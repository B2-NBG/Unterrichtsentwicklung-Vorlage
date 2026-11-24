"""
sync-vorlage.py - überträgt die Vorlagenblöcke (Stil, Knopfleiste, Dialoge, Script) aus templates/Fachunterricht.html
in templates/Allgemeinbildung.html, in die Layout-Vorlagen der Teams (Vorlagen/<team>/<Name>.html) und in alle Seiten
in Unterricht/. So funktionieren Bewertung, Abgabe, SCORM, PDF-Export, Leerdruck, Hell/Dunkel und Lösungssperre
überall gleich.

Aufruf (im Projektordner, am Mac python3 statt python):
  python .agents/gemeinsam/scripts/sync-vorlage.py               Probelauf: zeigt, was sich ändern würde
  python .agents/gemeinsam/scripts/sync-vorlage.py --schreiben   Seiten in Unterricht/ aktualisieren
  ... --datei Unterricht/.../index.html [--datei ...]                              nur diese Seiten (auch eine neue Seite)
  ... --diff                                                                   Unterschiede je Block zeigen
  ... --pruefen                                                                Exitcode 1, wenn eine Seite abweicht
  ... --vorlagen                                                               Fachunterricht.html -> Allgemeinbildung.html
                                                                               und Layout-Vorlagen der Teams, dazu die
                                                                               Kern-Dateien (siehe unten)
Nach JEDER Änderung an Fachunterricht.html: erst --vorlagen, dann --schreiben (und die SCORM-Pakete neu bauen).
Nach dem Kopieren einer Vorlage für eine neue Seite: --datei <neue Seite> --schreiben (setzt u. a. die Schriften ein).

Blöcke:
  Fachunterricht.html:head|tools|modals|scripts   aus Fachunterricht.html (in jeder Seite)
  Allgemeinbildung.html:stil|script               aus Allgemeinbildung.html (nur Seiten im Layout "Lernschritte")
  <team>/<Name>.html:stil|script                  aus Vorlagen/<team>/<Name>.html (Layout-Vorlage eines Teams): nur
                                                  Seiten, die diese Markierung tragen (also aus der Vorlage kopiert sind)
Team-Vorlagen (layouts): Eine Layout-Vorlage enthält die vier Blöcke aus Fachunterricht.html (markiert) und höchstens
je einen eigenen, markierten Block stil und script. Freie Vorlagen (<meta name="vorlage-art" content="frei">)
und Seiten daraus werden hier übersprungen. Prüfen: vorlage-pruefen.py.
Seiten ohne Markierungen bekommen sie beim ersten Lauf (Blöcke über feste Ankertexte gefunden, sonst Abbruch für diese Seite).
Alles außerhalb der Blöcke bleibt Byte für Byte erhalten.

Kern (kern/): --vorlagen schreibt zusätzlich Stil und Script der Vorlagen als Dateien: .agents/gemeinsam/templates/kern/
(Fachunterricht.head.css, Fachunterricht.scripts-1.js, Fachunterricht.scripts-2.js, Allgemeinbildung.stil.css,
Allgemeinbildung.script.js) und Vorlagen/<team>/kern/<Name>.stil.css|.script.js. Inhalt ist genau der Text zwischen den
Tags, Zeilenende \n (bauen.py passt es beim Bauen an die Seite an). --pruefen (ohne --datei) meldet, wenn eine
Kern-Datei nicht zur Vorlage passt. bauen.py setzt Seiten mit verlinktem Kern wieder zusammen.

Schrift fürs Zeichnen (Fachunterricht Technisches Zeichnen): Seiten mit <meta name="schrift" content="zeichnen"> bekommen im
Platzhalter <style id="zeichen-schriften"></style> die Schriften aus dem Ordner im Schulprofil (schule.txt,
Schrift-Zeichnen, base64) und die Schriftzuweisung. --vorlagen schreibt sie einmal nach kern/schrift-zeichnen.css, eine
Seite mit ausgelagertem Kern verweist darauf (bauen.py setzt sie beim Bauen wieder als <style id="zeichen-schriften"> ein).
Ist Schrift-Zeichnen leer, gibt es keine Datei, und die Seiten nehmen die Systemschrift. In allen anderen Seiten und in
den Vorlagen bleibt der Platzhalter leer.

Erscheinungsbild: --vorlagen setzt in Allgemeinbildung.html die Hausfarben aus dem Schulprofil (Zeile :root { --haus-… }
zwischen /* Erscheinungsbild: … */ und /* /Erscheinungsbild */ am Anfang des Stils, profil.haus_css()) und das Logo im
Kopf (<img class="logo" … alt="Logo der Schule">, profil.logo_data()). Der Stil nutzt nur var(--haus-…), keine festen
Hausfarben. Seiten behalten ihr eigenes Logo (bilder/), die Farben bekommen sie über kern/Allgemeinbildung.stil.css.
Nur Python-Standardbibliothek (Windows und Mac).
"""
import argparse
import base64
import difflib
import glob
import importlib.util
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HIER)
ROOT = os.path.dirname(os.path.dirname(SKILL))
TPL = os.path.join(SKILL, 'templates')
FACH = os.path.join(TPL, 'Fachunterricht.html')
ALLG = os.path.join(TPL, 'Allgemeinbildung.html')
sys.path.insert(0, HIER)   # profil.py liegt daneben
import profil  # noqa: E402
_SCHRIFT = profil.wert('Schrift-Zeichnen', '')   # Ordner mit den WOFF-Teilmengen, leer = Systemschrift
SCHRIFTEN = os.path.join(ROOT, *_SCHRIFT.replace('\\', '/').split('/')) if _SCHRIFT else ''
VORLAGEN = os.path.join(ROOT, 'Vorlagen')   # Vorlagen der Teams: Vorlagen/<team>/<Name>.html
ALLG_NAME = 'Allgemeinbildung.html'
FREI = re.compile(r'<meta\s+name="vorlage-art"\s+content="frei"\s*/?>', re.I)

F_BLOECKE = ('head', 'tools', 'modals', 'scripts')
A_BLOECKE = ('stil', 'script')
PLATZHALTER = '<style id="zeichen-schriften"></style>'

# Schnitte: Datei, Familie, Gewicht, Stil
SCHNITTE = (
    ('Zeichenschrift-400-normal.woff', 'Zeichenschrift', 400, 'normal'),
    ('Zeichenschrift-700-normal.woff', 'Zeichenschrift', 700, 'normal'),
    ('Zeichenschrift-400-italic.woff', 'Zeichenschrift', 400, 'italic'),
    ('ZeichenschriftCondensed-400-normal.woff', 'Zeichenschrift Condensed', 400, 'normal'),
    ('ZeichenschriftCondensed-700-normal.woff', 'Zeichenschrift Condensed', 700, 'normal'),
    ('ZeichenschriftNorm-400-normal.woff', 'Zeichenschrift Norm', 400, 'normal'),
)
ZUWEISUNG = (
    'body{font-family:"Zeichenschrift",Arial,sans-serif}',
    'h1,h2,h3,table,.tb{font-family:"Zeichenschrift Condensed","Zeichenschrift",Arial,sans-serif}',
    '.chnum,.phnum,.score{font-family:"Zeichenschrift Condensed","Zeichenschrift",sans-serif}',
    'main svg text{font-family:"Zeichenschrift Norm","Zeichenschrift",sans-serif}',
    'main svg.text-normal text{font-family:inherit}',
    '@page{@bottom-right{font-family:"Zeichenschrift",Arial,sans-serif}}',
)


class Fehler(Exception):
    pass


def lesen(path):
    with open(path, 'rb') as f:
        raw = f.read()
    bom = raw.startswith(b'\xef\xbb\xbf')
    return raw.decode('utf-8-sig'), bom


def eol_von(s):
    return '\r\n' if '\r\n' in s else '\n'


def norm(s, eol):
    return re.sub(r'\r?\n', eol, s)


def finde(s, what, start=0, name='', vor=False):
    i = s.find(what, start)
    if i < 0:
        raise Fehler('Ankertext für "%s" nicht gefunden: %s' % (name, what[:50]))
    return i


def genau_einmal(s, what, name):
    n = s.count(what)
    if n != 1:
        raise Fehler('Ankertext für "%s" steht %d-mal statt einmal: %s' % (name, n, what[:50]))
    return s.find(what)


def div_ende(s, start):
    """Ende (Index nach '</div>') des <div>, das bei start beginnt (verschachtelte divs mitgezählt)."""
    tief = 0
    for m in re.compile(r'<div\b|</div>').finditer(s, start):
        tief += 1 if m.group(0) != '</div>' else -1
        if tief == 0:
            return m.end()
    raise Fehler('Schließendes </div> nicht gefunden')


# ---------- Blöcke über Markierungen ----------

def markierung(datei, name):
    return '<!-- %s:%s -->' % (datei, name), '<!-- /%s:%s -->' % (datei, name)


def bereich_markiert(s, datei, name):
    """(Anfang, Ende) des Inhalts zwischen den Markierungen oder None."""
    op, cl = markierung(datei, name)
    i = s.find(op)
    if i < 0:
        return None
    j = s.find(cl, i)
    if j < 0 or s.find(op, i + 1) >= 0 or s.find(cl, j + 1) >= 0:
        raise Fehler('Markierung %s fehlt oder steht doppelt' % op)
    a = i + len(op)
    a += 2 if s.startswith('\r\n', a) else (1 if s.startswith('\n', a) else 0)
    e = j
    if s.endswith('\r\n', 0, e):
        e -= 2
    elif s.endswith('\n', 0, e):
        e -= 1
    return a, e


# ---------- Blöcke über Ankertexte (Seiten ohne Markierungen) ----------

def bereich_anker(s, name):
    if name == 'head':
        k = genau_einmal(s, "window.addEventListener('error'", 'head')
        a = s.rfind('<script>', 0, k)
        r = finde(s, ':root { --paper:', k, 'head')
        e = finde(s, '</style>', r, 'head') + len('</style>')
        if s.find('<style id="zeichen-schriften">', a, e + 200) >= 0:   # Platzhalter direkt danach gehört dazu
            p = s.find('<style id="zeichen-schriften">', a)
            e = finde(s, '</style>', p, 'head') + len('</style>')
        blk = s[a:e]
        if '@page' not in blk or 'Lösungssperre' not in blk and 'loesung' not in blk.lower():
            raise Fehler('Kopfblock sieht nicht wie die Vorlage aus')
        return a, e
    if name == 'tools':
        a = genau_einmal(s, '<div class="tools">', 'tools')
        e = finde(s, '</div>', a, 'tools') + len('</div>')
        if 'id="pdfBtn"' not in s[a:e]:
            raise Fehler('Knopfleiste ohne "Als PDF speichern"')
        return a, e
    if name == 'modals':
        m = genau_einmal(s, '<div class="modal" id="pwModal"', 'modals')
        a = s.rfind('<!--', 0, m)
        if a < 0 or s[a:m].count('-->') != 1 or len(s[a:m].strip()) > 200:
            a = m
        sm = genau_einmal(s, '<div class="modal" id="subModal"', 'modals')
        e = div_ende(s, sm)
        if 'subCancel' not in s[a:e] and 'subOk' not in s[a:e] and 'subModal' not in s[a:e]:
            raise Fehler('Dialoge unvollständig')
        return a, e
    if name == 'scripts':
        k = genau_einmal(s, '/* Minimaler PDF-Writer', 'scripts')
        a = s.rfind('<script>', 0, k)
        e1 = finde(s, '</script>', k, 'scripts') + len('</script>')
        m = re.compile(r'\s*<script>').match(s, e1)
        if not m:
            raise Fehler('Hauptscript folgt nicht direkt auf den PDF-Writer')
        e = finde(s, '</script>', m.end(), 'scripts') + len('</script>')
        blk = s[a:e]
        if 'function printBlank' not in blk or 'function makePdf' not in blk:
            raise Fehler('Hauptscript ohne printBlank/makePdf')
        return a, e
    if name == 'stil':
        k = genau_einmal(s, '/* Layout "Lernschritte": überschreibt', 'stil')
        a = s.rfind('<style>', 0, k)
        return a, finde(s, '</style>', k, 'stil') + len('</style>')
    if name == 'script':
        k = genau_einmal(s, '/* Layout "Lernschritte": Schritt-Leiste', 'script')
        a = s.rfind('<script>', 0, k)
        return a, finde(s, '</script>', k, 'script') + len('</script>')
    raise Fehler('Unbekannter Block ' + name)


def bloecke_aus(s, datei, namen):
    """Inhalt der Blöcke einer Vorlage (über Markierungen, sonst Ankertexte)."""
    out = {}
    for n in namen:
        b = bereich_markiert(s, datei, n)
        if b is None:
            b = bereich_anker(s, n)
        out[n] = s[b[0]:b[1]]
    return out


# ---------- Schriften ----------

_schrift_css = None


def schrift_css():
    global _schrift_css
    if _schrift_css is None:
        zeilen = ['<style id="zeichen-schriften">',
                  '/* Schriften fürs Zeichnen, eingesetzt von sync-vorlage.py aus '
                  '%s (Lizenzen der Schriften: in diesem Ordner). ' % _SCHRIFT.replace('\\', '/') +
                  '*/']
        for datei, fam, w, st in SCHNITTE:
            p = os.path.join(SCHRIFTEN, datei)
            if not os.path.exists(p):
                raise Fehler('Schriftdatei fehlt: ' + p)
            with open(p, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('ascii')
            zeilen.append('@font-face{font-family:"%s";font-weight:%d;font-style:%s;font-display:swap;'
                          'src:url(data:font/woff;base64,%s) format("woff")}' % (fam, w, st, b64))
        zeilen.extend(ZUWEISUNG)
        zeilen.append('</style>')
        _schrift_css = '\n'.join(zeilen)
    return _schrift_css


def will_nils(s):
    kopf = s[:s.find('</head>')] if '</head>' in s else s
    return re.search(r'<meta\s+name="schrift"\s+content="zeichnen"\s*/?>', re.sub(r'(?s)<!--.*?-->', '', kopf)) is not None


# ---------- Erscheinungsbild (Hausfarben und Logo aus dem Schulprofil) ----------

HAUS = re.compile(r'(/\* Erscheinungsbild: Hausfarben[^\n]*\*/\r?\n)([^\n]*?)(\r?\n[ \t]*/\* /Erscheinungsbild \*/)')
LOGO = re.compile(r'(<img class="logo" src=")(data:image/[a-z]+;base64,[A-Za-z0-9+/=]*)(" alt="Logo der Schule">)')


def erscheinungsbild_einsetzen(s):
    """Allgemeinbildung.html mit Hausfarben und Logo aus dem Schulprofil (neuer Text)."""
    if len(HAUS.findall(s)) != 1:
        raise Fehler('Allgemeinbildung.html: Abschnitt /* Erscheinungsbild: … */ fehlt oder steht mehrmals im Stil')
    if len(LOGO.findall(s)) != 1:
        raise Fehler('Allgemeinbildung.html: <img class="logo" src="data:…" alt="Logo der Schule"> fehlt oder steht mehrmals')
    try:
        css, logo = profil.haus_css(), profil.logo_data()
    except profil.ProfilFehler as e:
        raise Fehler(str(e))
    s = HAUS.sub(lambda m: m.group(1) + '  ' + css + m.group(3), s)
    return LOGO.sub(lambda m: m.group(1) + logo + m.group(3), s)


# ---------- Vorlagen der Teams ----------

def ohne_kommentare(s):
    return re.sub(r'(?s)<!--.*?-->', '', s)


def ist_frei(s):
    """Freie Vorlage oder Seite daraus: <meta name="vorlage-art" content="frei"> im Kopf."""
    kopf = s[:s.find('</head>')] if '</head>' in s else s
    return FREI.search(ohne_kommentare(kopf)) is not None


def vorlage_von(s):
    """Inhalt von <meta name="vorlage" content="<team>/<Name>.html"> im Kopf oder ''."""
    kopf = s[:s.find('</head>')] if '</head>' in s else s
    m = re.search(r'<meta\s+name="vorlage"\s+content="([^"]*)"\s*/?>', ohne_kommentare(kopf), re.I)
    return m.group(1).strip() if m else ''


def kennung(pfad):
    """Vorlagen/<team>/<Name>.html -> "<team>/<Name>.html" (so heißen die Markierungen der eigenen Blöcke)."""
    return '%s/%s' % (os.path.basename(os.path.dirname(pfad)), os.path.basename(pfad))


def team_vorlagen():
    """[(Kennung, Pfad, Text, BOM, frei?)] aller Vorlagen der Teams."""
    liste = []
    for p in sorted(glob.glob(os.path.join(VORLAGEN, '*', '*.html'))):
        s, bom = lesen(p)
        liste.append((kennung(p), p, s, bom, ist_frei(s)))
    return liste


def eigene_bloecke(s, datei):
    """Die markierten eigenen Blöcke einer Layout-Vorlage: {'stil': Text, 'script': Text} (nur die vorhandenen)."""
    out = {}
    for n in A_BLOECKE:
        b = bereich_markiert(s, datei, n)
        if b is not None:
            out[n] = s[b[0]:b[1]]
    return out


def layouts(allg_s):
    """{Kennung: {Block: Text}} für Allgemeinbildung.html und die Layout-Vorlagen der Teams (ohne die freien)."""
    lay = {ALLG_NAME: bloecke_aus(allg_s, ALLG_NAME, A_BLOECKE)}
    for k, _, s, _, frei in team_vorlagen():
        if not frei:
            lay[k] = eigene_bloecke(s, k)
    return lay


# ---------- Seite aktualisieren ----------

def ist_lernschritte(s):
    return ('Allgemeinbildung.html:stil' in s or '/* Layout "Lernschritte": überschreibt' in s)


def layout_von(s, lay):
    """Kennungen der Layouts, deren Blöcke die Seite trägt (Lernschritte auch ohne Markierung)."""
    return [k for k in sorted(lay) if (ist_lernschritte(s) if k == ALLG_NAME
                                        else any(markierung(k, n)[0] in s for n in lay[k]))]


def sollbloecke(fach, lay, seite):
    """({(Datei, Block): Text}, [(Datei, Block)]) für eine Seite: die vier Blöcke aus Fachunterricht.html und die
    eigenen Blöcke ihres Layouts."""
    soll = {('Fachunterricht.html', n): fach[n] for n in F_BLOECKE}
    if will_nils(seite) and SCHRIFTEN:
        if PLATZHALTER not in fach['head']:
            raise Fehler('Platzhalter für die Schriften fürs Zeichnen fehlt in Fachunterricht.html')
        soll[('Fachunterricht.html', 'head')] = fach['head'].replace(PLATZHALTER, schrift_css())
    for k in layout_von(seite, lay):
        for n in A_BLOECKE:
            if n in lay[k] and (k == ALLG_NAME or markierung(k, n)[0] in seite):
                soll[(k, n)] = lay[k][n]
    return soll, list(soll)


def ist_ausgelagert(block):
    """True, wenn der Block statt Stil und Script Verweise auf Dateien in kern/ trägt (bauen.py --auslagern)."""
    return re.search(r'<link rel="stylesheet" href="[^"]*kern/|<script src="[^"]*kern/', block) is not None


def aktualisiere(s, fach, lay, ordner=None):
    """Neuer Text und Bericht je Block. lay: layouts(). ordner: Ordner der Seite. Ausgelagerte Blöcke (Verweise auf kern/)
    bleiben ausgelagert: Stil und Script stehen dann in den Kern-Dateien, der Block wird mit den Verweisen verglichen
    (richtige Datei, richtige Tiefe), nur tools, modals, das Fehler-Script und die Schriften fürs Zeichnen werden gleichgehalten."""
    s = s.replace('<!-- Seite.html:', '<!-- Fachunterricht.html:').replace('<!-- /Seite.html:', '<!-- /Fachunterricht.html:')
    eol = eol_von(s)
    soll, namen = sollbloecke(fach, lay, s)
    stellen = []
    for datei, n in namen:
        b = bereich_markiert(s, datei, n)
        neu_markiert = b is None
        if b is None:
            b = bereich_anker(s, n)
        stellen.append((b[0], b[1], datei, n, neu_markiert))
    stellen.sort()
    for x, y in zip(stellen, stellen[1:]):
        if x[1] > y[0]:
            raise Fehler('Blöcke %s und %s überlappen' % (x[3], y[3]))
    out, pos, bericht = [], 0, []
    for a, e, datei, n, neu_markiert in stellen:
        alt = s[a:e]
        neu = norm(soll[(datei, n)], eol)
        if ordner and not neu_markiert and ist_ausgelagert(alt):
            b = _bauen()
            try:
                neu = b.auslagern_block(neu, datei, n, ordner)[0]
            except b.BauFehler as e:
                raise Fehler(str(e))
        out.append(s[pos:a])
        if neu_markiert:
            op, cl = markierung(datei, n)
            out.append(op + eol + neu + eol + cl)
        else:
            out.append(neu)
        pos = e
        if alt == neu:
            st = 'gleich' + (', Markierung ergänzt' if neu_markiert else '')
        else:
            al, nl = alt.splitlines(), neu.splitlines()
            plus = sum(1 for l in difflib.ndiff(al, nl) if l.startswith('+ '))
            minus = sum(1 for l in difflib.ndiff(al, nl) if l.startswith('- ')) if len(al) + len(nl) < 6000 else 0
            st = 'aktualisiert (+%d/-%d Zeilen)' % (plus, minus) + (', Markierung ergänzt' if neu_markiert else '')
        bericht.append((n, st, alt, neu))
    out.append(s[pos:])
    return ''.join(out), bericht


def pruefe_ergebnis(alt, neu, nils):
    if not neu.lstrip('﻿').lower().startswith('<!doctype html>'):
        raise Fehler('Erste Zeile ist nicht <!doctype html>')
    if not neu.rstrip().endswith('</html>'):
        raise Fehler('Datei endet nicht mit </html>')
    for tag in ('<script', '<style'):
        d = neu.count(tag) - alt.count(tag)
        erlaubt = (0, 1) if tag == '<style' else (0,)
        if d not in erlaubt:
            raise Fehler('Anzahl %s ändert sich um %d' % (tag, d))
    for t in ('function printBlank', 'id="pwModal"', 'id="pdfBtn"'):
        if neu.count(t) != 1:
            raise Fehler('%s steht %d-mal in der Seite' % (t, neu.count(t)))
    if nils and SCHRIFTEN and '@font-face{font-family:"Zeichenschrift"' not in neu:
        raise Fehler('Schriften fürs Zeichnen wurden nicht eingesetzt')


def schreiben(path, text, bom):
    data = (b'\xef\xbb\xbf' if bom else b'') + text.encode('utf-8')
    tmp = path + '.__sync__'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, path)


def kurz(zeile):
    if 'base64,' in zeile and len(zeile) > 200:
        return re.sub(r'base64,[A-Za-z0-9+/=]{40,}', 'base64,[…]', zeile)[:200]
    return zeile[:200]


_BAUEN = []


def _bauen():
    """bauen.py als Modul, einmal geladen (sein Zwischenspeicher für die Kern-Dateien bleibt erhalten)."""
    if not _BAUEN:
        spec = importlib.util.spec_from_file_location('bauen', os.path.join(HIER, 'bauen.py'))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _BAUEN.append(mod)
    return _BAUEN[0]


def kern_sollen(fach_s, allg_s):
    """{Pfad: Text} aller Kern-Dateien, die sich aus den Vorlagen ergeben (Zeilenende LF)."""
    b = _bauen()
    soll = {}

    def aufnehmen(kennung, bloecke):
        for name, text in bloecke.items():
            for _, _, _, datei, inhalt in b.stuecke(text, kennung, name):
                soll[os.path.join(b.kern_ordner(kennung), datei)] = b.kern_text(inhalt)
    aufnehmen('Fachunterricht.html', bloecke_aus(fach_s, 'Fachunterricht.html', F_BLOECKE))
    if SCHRIFTEN:   # Schrift fürs Zeichnen: der Inhalt von <style id="zeichen-schriften">, einmal für alle Seiten
        css = schrift_css()
        soll[os.path.join(b.KERN_TPL, b.SCHRIFT_DATEI)] = b.kern_text(css[css.index('>') + 1:css.rindex('</style>')])
    aufnehmen(ALLG_NAME, bloecke_aus(allg_s, ALLG_NAME, A_BLOECKE))
    for k, _, s, _, frei in team_vorlagen():
        if not frei:
            aufnehmen(k, eigene_bloecke(s, k))
    return soll


def kern_abweichungen(fach_s, allg_s):
    """[(Pfad, Zustand)] der Kern-Dateien, die fehlen, abweichen oder überzählig sind."""
    b = _bauen()
    soll = kern_sollen(fach_s, allg_s)
    out = []
    for p, text in sorted(soll.items()):
        if not os.path.isfile(p):
            out.append((p, 'fehlt'))
        elif open(p, 'rb').read().decode('utf-8').replace('\r\n', '\n') != text:
            out.append((p, 'weicht ab'))
    ordner = {b.KERN_TPL} | {os.path.join(VORLAGEN, d, 'kern') for d in os.listdir(VORLAGEN)
                             if os.path.isdir(os.path.join(VORLAGEN, d))}
    for o in sorted(ordner):
        for p in sorted(glob.glob(os.path.join(o, '*'))):
            if os.path.isfile(p) and p not in soll:
                out.append((p, 'überzählig'))
    return out


def kern_schreiben(fach_s, allg_s, schreibe=True):
    """Kern-Dateien schreiben (mit schreibe=False nur zählen). Rückgabe: Zahl der abweichenden Dateien."""
    soll = kern_sollen(fach_s, allg_s)
    abw = kern_abweichungen(fach_s, allg_s)
    for p, zustand in abw:
        rel = os.path.relpath(p, ROOT).replace(os.sep, '/')
        if schreibe:
            if zustand == 'überzählig':
                os.remove(p)
            else:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, 'wb') as f:
                    f.write(soll[p].encode('utf-8'))
        print('%s %s.' % (rel, {'fehlt': 'geschrieben', 'weicht ab': 'aktualisiert', 'überzählig': 'entfernt'}[zustand]
                          if schreibe else zustand + ' (sync-vorlage.py --vorlagen)'))
    if not abw:
        print('Kern-Dateien (%d) sind aktuell.' % len(soll))
    return len(abw)


def kern_einsetzen(s, fach, name):
    """Die vier Blöcke aus Fachunterricht.html in eine Vorlage einsetzen (über die Markierungen). Neuer Text."""
    eol = eol_von(s)
    for n in F_BLOECKE:
        b = bereich_markiert(s, 'Fachunterricht.html', n)
        if b is None:
            raise Fehler('%s: Markierung Fachunterricht.html:%s fehlt' % (name, n))
        s = s[:b[0]] + norm(fach[n], eol) + s[b[1]:]
    return s


def vorlagen_sync(fach_s, schreibe=True):
    """Fachunterricht.html -> Allgemeinbildung.html und Layout-Vorlagen der Teams. Rückgabe: Zahl der Vorlagen, die
    abweichen (mit schreibe werden sie aktualisiert)."""
    fach = bloecke_aus(fach_s, 'Fachunterricht.html', F_BLOECKE)
    for n in F_BLOECKE:
        print('%-8s %7d Zeichen aus Fachunterricht.html' % (n, len(fach[n])))
    allg_s, bom = lesen(ALLG)
    eol = eol_von(allg_s)
    neu = allg_s.replace('<!-- Seite.html:', '<!-- Fachunterricht.html:').replace('<!-- /Seite.html:', '<!-- /Fachunterricht.html:')
    neu = erscheinungsbild_einsetzen(kern_einsetzen(neu, fach, ALLG_NAME))
    for n in A_BLOECKE:   # eigene Blöcke von Allgemeinbildung.html markieren (einmalig)
        if bereich_markiert(neu, ALLG_NAME, n) is None:
            a, e = bereich_anker(neu, n)
            op, cl = markierung(ALLG_NAME, n)
            neu = neu[:a] + op + eol + neu[a:e] + eol + cl + neu[e:]
            print('%-8s Markierung ergänzt' % n)
    liste = [(ALLG_NAME, ALLG, allg_s, neu, bom)]
    for k, p, s, b, frei in team_vorlagen():
        if frei:
            print('Vorlagen/%s: freie Vorlage (übersprungen)' % k)
            continue
        liste.append(('Vorlagen/' + k, p, s, kern_einsetzen(s, fach, 'Vorlagen/' + k), b))
    abweichend = 0
    for name, p, alt, neu, bom in liste:
        if neu == alt:
            print('%s ist aktuell.' % name)
            continue
        abweichend += 1
        if schreibe:
            schreiben(p, neu, bom)
        print('%s %s.' % (name, 'aktualisiert' if schreibe else 'weicht ab (sync-vorlage.py --vorlagen)'))
    abweichend += kern_schreiben(fach_s, liste[0][3], schreibe)   # Kern aus der erneuerten Allgemeinbildung.html
    return abweichend


def main(argv=None):
    profil.utf8_ausgabe()
    ap = argparse.ArgumentParser(description='Vorlagenblöcke in Allgemeinbildung.html, die Layout-Vorlagen der Teams '
                                 'und die Seiten in Unterricht/ übertragen.')
    ap.add_argument('--schreiben', action='store_true', help='Seiten wirklich ändern (sonst Probelauf)')
    ap.add_argument('--datei', action='append', default=[], help='nur diese Seite(n)')
    ap.add_argument('--diff', action='store_true', help='Unterschiede je Block zeigen')
    ap.add_argument('--pruefen', action='store_true', help='Exitcode 1, wenn eine Seite von der Vorlage abweicht')
    ap.add_argument('--vorlagen', action='store_true', help='nur Fachunterricht.html -> Allgemeinbildung.html und '
                    'Layout-Vorlagen der Teams (mit --pruefen: nichts schreiben, Exitcode 1 bei Abweichung)')
    a = ap.parse_args(argv)

    fach_s, _ = lesen(FACH)
    if a.vorlagen:
        try:
            abweichend = vorlagen_sync(fach_s, schreibe=not a.pruefen)
        except Fehler as e:
            print('FEHLER: ' + str(e))
            return 2
        return 1 if a.pruefen and abweichend else 0

    allg_s, _ = lesen(ALLG)
    try:
        fach = bloecke_aus(fach_s, 'Fachunterricht.html', F_BLOECKE)
        lay = layouts(allg_s)
    except Fehler as e:
        print('FEHLER: ' + str(e))
        return 2

    if a.datei:
        seiten = [os.path.abspath(p) for p in a.datei]
    else:
        seiten = sorted(glob.glob(os.path.join(ROOT, 'Unterricht', '**', '*.html'), recursive=True))
    abweichend, fehler, geaendert, ausgelagert = 0, 0, 0, False
    for p in seiten:
        rel = os.path.relpath(p, ROOT)
        s, bom = lesen(p)
        ausgelagert = ausgelagert or ist_ausgelagert(s)
        if ('/* Minimaler PDF-Writer' not in s and markierung('Fachunterricht.html', 'scripts')[0] not in s) or ist_frei(s):
            if a.datei:
                print('%s: %s (übersprungen)' % (rel, 'Seite aus einer freien Vorlage' if ist_frei(s)
                                                 else 'keine Seite aus der Vorlage'))
            continue
        try:
            ordner = os.path.dirname(p)
            neu, bericht = aktualisiere(s, fach, lay, ordner)
            b = _bauen()
            try:   # geprüft wird die gebaute Fassung (bei ausgelagertem Kern liegen Stil und Script in kern/)
                neu_gebaut = b.gebaut_text(neu, ordner)
            except b.BauFehler as e:
                raise Fehler(str(e))
            try:
                alt_gebaut = b.gebaut_text(s, ordner)
            except b.BauFehler:
                alt_gebaut = neu_gebaut   # alte Verweise kaputt (falsche Datei oder Tiefe): die neuen ersetzen sie
            pruefe_ergebnis(alt_gebaut, neu_gebaut, will_nils(s))
        except Fehler as e:
            fehler += 1
            print('FEHLER %s: %s (Seite nicht geändert)' % (rel, e))
            continue
        layout = ', '.join('Lernschritte' if k == ALLG_NAME else k for k in layout_von(s, lay)) or 'Schriftfeld'
        print('%s  [%s%s]' % (rel, layout, ', Schriften fürs Zeichnen' if will_nils(s) else ''))
        for n, st, alt, nn in bericht:
            print('    %-8s %s' % (n, st))
            if a.diff and alt != nn:
                for z in difflib.unified_diff(alt.splitlines(), nn.splitlines(), 'Seite', 'Vorlage', n=1, lineterm=''):
                    print('      ' + kurz(z))
        if neu != s:
            abweichend += 1
            if a.schreiben:
                schreiben(p, neu, bom)
                geaendert += 1
                print('    -> geschrieben (%d KB)' % (len(neu.encode('utf-8')) // 1024))
    print()
    kern_fehler = 0
    if a.pruefen and (not a.datei or ausgelagert):   # ausgelagerte Seite: Sie lädt Stil und Script aus kern/
        kern_fehler = kern_schreiben(fach_s, allg_s, schreibe=False)
    print('%d Seiten weichen ab, %d geschrieben, %d Fehler.%s' % (
        abweichend, geaendert, fehler, '' if a.schreiben or not abweichend else ' Probelauf: mit --schreiben übernehmen.'))
    if fehler:
        return 2
    if a.pruefen and (abweichend or kern_fehler):
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
