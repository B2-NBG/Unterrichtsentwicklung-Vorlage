"""
unterrichtsmaterial.py - Steckbrief und Namensregel für alles Unterrichtsmaterial. Die eine Stelle, an der steht, wie Ordner, Pakete und
Kurse heißen. Alle Skripte (Paketbau, Handbuch, Kursbau, Testbau, Prüfskript) lesen von hier, niemand tippt Namen ab.

Ablage:   Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/
Paket:    BYCS-SYNC/Pakete/<Klasse>/<Fach>/<Klasse>_<Fach>_<Abschnitt>_<Thema>_scorm.zip (nicht in Git: GitHub baut es nach dem Push
          aus dem Themenordner und stellt es in den Teamordner zu; am Rechner nur im Temp-Ordner, gebaut(); ein Lernpaket ist jeder Themenordner, dessen index.html eine Version trägt)
Kurs:     Unterricht/<Klasse>[/<Fach>]/Kurs-<Klasse>[-<Fach>][-<Zusatz>].json  ->  BYCS-SYNC/Kurse/<Klasse>[/<Fach>]/<gleicher Name>.mbz

  Klasse     Klassenkürzel oder Sammelname in Großbuchstaben: MGF10, BFS11, ALLE10, ALLE
  Fach       Kürzel aus .agents/gemeinsam/data/faecher.txt: LF1, Eth, PuG
  Abschnitt  BW<n> Blockwoche, LS<n> Lernsituation, M-<Name> Modul, R-<Name> Themenreihe
  Thema      sprechend und ungekürzt, Wörter mit - verbunden; die Art steht im Namen (-Arbeitsblatt, -Uebung,
             -Unterrichtsplan, -Testvorbereitung, -Feedback, Test-<Thema>), ohne Zusatz ist es ein E-Learning
  "_" trennt nur die vier Felder und kommt in keinem Feld vor.

Steckbrief in der Seite (index.html): <meta name="klasse|fach|abschnitt|thema" content="...">, der Titel ist <title>.
Der Steckbrief wird aus dem Ablageort geschrieben, nie von Hand.

Aufruf im Projektordner (am Mac python3 statt python):
  python .agents/gemeinsam/scripts/unterrichtsmaterial.py <Themenordner>               Steckbrief, Paketname und Fehler zeigen
  python .agents/gemeinsam/scripts/unterrichtsmaterial.py <Themenordner> --schreiben   Steckbrief in die index.html schreiben
  python .agents/gemeinsam/scripts/unterrichtsmaterial.py --liste                      Klassen, Fächer und vorhandene Abschnitte
                                                                            (für den Auswahldialog)
Nur Python-Standardbibliothek (Windows und Mac, ab Python 3.9).
"""
import html as _html
import glob
import os
import importlib.util
import re
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _profil():
    """profil.py (liegt daneben) über den Pfad laden: Dieses Modul laden auch Skripte aus anderen Ordnern."""
    spec = importlib.util.spec_from_file_location('profil', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'profil.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PROFIL = _profil()
FAECHER = '.agents/gemeinsam/data/faecher.txt'
FELDER = ('klasse', 'fach', 'abschnitt', 'thema')
ORDNER = 'Unterricht'                              # Ordner für alles Unterrichtsmaterial, ganz oben im Projekt (die eine Stelle für den Namen)
SONDERORDNER = ('Offen',)                         # in Unterricht/, keine Klassen
ARTEN = (('-Arbeitsblatt', 'Arbeitsblatt'), ('-Uebung', 'Übungs-App'), ('-Unterrichtsplan', 'Unterrichtsplan'),
         ('-Testvorbereitung', 'Testvorbereitung'), ('-Feedback', 'Feedback'))
# Aus dem Schulprofil (schule.txt): Klassen, Jahrgänge, Sammelname (Material mehrerer Klassen), Abschnitte
SAMMEL = PROFIL.wert('Sammelname')                                          # ALLE
JAHRGAENGE = tuple(int(j) for j in PROFIL.felder('Jahrgänge')[:2])           # (10, 13)
VERSATZ, JAHR = PROFIL.zahl('Jahr-Versatz'), PROFIL.wert('Jahr-Bezeichnung')  # 10. Klasse = 1. Jahr
BEISPIELE = PROFIL.felder('Beispielklassen', ['MGF10', 'BFS11'])
ABSCHNITTE = [(a[0], a[1], a[2] if len(a) > 2 else 'Nummer') for a in PROFIL.liste('Abschnitt')]   # (Kürzel, Name, Nummer|Name)
SAMMELNAMEN = ['%s%d' % (SAMMEL, j) for j in range(JAHRGAENGE[0], JAHRGAENGE[1] + 1)] + [SAMMEL]
RX_KLASSE = re.compile(r'(?:%s|%s(?:%s)?)$' % (PROFIL.muster('Klassenmuster').pattern, re.escape(SAMMEL),
                                               '|'.join(str(j) for j in range(JAHRGAENGE[0], JAHRGAENGE[1] + 1))))
RX_FACH = re.compile(r'[A-Za-z][A-Za-z0-9]{0,7}$')
RX_ABSCHNITT = re.compile(r'(%s)$' % '|'.join(re.escape(k) + (r'[1-9]\d*' if art == 'Nummer' else r'-[A-Z0-9][A-Za-z0-9]*(-[A-Za-z0-9]+)*')
                                              for k, _, art in ABSCHNITTE))
RX_THEMA = re.compile(r'[A-Z0-9][A-Za-z0-9]*(-[A-Za-z0-9]+)*$')
RX_PAKET = re.compile(r'([^_/\\]+)_([^_]+)_([^_]+)_(.+)_scorm\.zip$')
UML = (('ä', 'ae'), ('ö', 'oe'), ('ü', 'ue'), ('Ä', 'Ae'), ('Ö', 'Oe'), ('Ü', 'Ue'), ('ß', 'ss'))


class UnterrichtsmaterialFehler(Exception):
    pass


def lesen(pfad):
    with open(pfad, 'rb') as f:
        return f.read().decode('utf-8-sig')


def schreiben(pfad, text):
    with open(pfad, 'wb') as f:
        f.write(text.encode('utf-8'))


def namensteil(text):
    """Text als Teil eines Ordner- oder Dateinamens: Umlaute als ae/oe/ue/ss, Wörter mit -, erstes Zeichen groß, nichts gekürzt."""
    for a, b in UML:
        text = text.replace(a, b)
    text = re.sub(r'[^A-Za-z0-9]+', '-', text).strip('-')
    return text[:1].upper() + text[1:]


# ---------------------------------------------------------------------------
# Fächer und Klassen

def faecher():
    """Liste aus faecher.txt: {'kuerzel', 'name', 'klassen'} in der Reihenfolge der Datei (Abteilung, Klasse, Kürzel)."""
    liste = []
    for z in lesen(os.path.join(ROOT, FAECHER)).splitlines():
        if not z.strip() or z.lstrip().startswith('#'):
            continue
        t = [x.strip() for x in z.split('|')]
        if len(t) >= 2 and t[0] and t[1]:
            liste.append({'kuerzel': t[0], 'name': t[1], 'klassen': [k.strip() for k in t[2].split(',') if k.strip()] if len(t) > 2 else []})
    return liste


def fachname(fach, klasse=''):
    """Voller Name zum Kürzel. Gibt es das Kürzel mehrfach (LF1 in mehreren Berufen), entscheidet die Klasse. '' = unbekannt."""
    treffer = [f for f in faecher() if f['kuerzel'] == fach]
    for f in treffer:
        if klasse and klasse in f['klassen']:
            return f['name']
    for f in treffer:
        if not f['klassen']:
            return f['name']
    return treffer[0]['name'] if len(treffer) == 1 else ''


def jahrgang(klasse):
    """Jahrgang aus dem Klassenkürzel: die Zahl am Ende (MGF10 -> 10, 7b -> 7, Q12 -> 12), 0 außerhalb der Jahrgänge."""
    m = re.search(r'(\d{1,2})[A-Za-z]?$', klasse)
    j = int(m.group(1)) if m else 0
    return j if JAHRGAENGE[0] <= j <= JAHRGAENGE[1] else 0


def ausbildungsjahr(klasse):
    """Text fürs Schriftfeld: MGF10 -> '1. Jahr' (Versatz 9), 7b -> '7. Jahrgangsstufe' (Versatz 0), ALLE -> 'alle Jahrgänge'."""
    j = jahrgang(klasse)
    return '%d. %s' % (j - VERSATZ, JAHR) if j else 'alle Jahrgänge'


def klassenname(klasse):
    """Text fürs Handbuch: MGF10 -> 'Klasse MGF10', ALLE10 -> 'Alle 10. Klassen', ALLE -> 'Alle Klassen'."""
    if klasse.upper() == SAMMEL.upper():
        return 'Alle Klassen'
    if klasse.startswith(SAMMEL):
        return 'Alle %d. Klassen' % jahrgang(klasse)
    return 'Klasse ' + klasse


def abschnitt_arten():
    """Text für Meldungen: 'BW<n> (Blockwoche), LS<n> (Lernsituation), M-<Name> (Modul) oder R-<Name> (Themenreihe)'."""
    t = ['%s%s (%s)' % (k, '<n>' if art == 'Nummer' else '-<Name>', name) for k, name, art in ABSCHNITTE]
    return ', '.join(t[:-1]) + ' oder ' + t[-1] if len(t) > 1 else ''.join(t)


def art(thema):
    """Art des Unterrichtsmaterials aus dem Namen des Themenordners."""
    if thema.startswith('Test-'):
        return 'Test'
    for ende, name in ARTEN:
        if thema.endswith(ende):
            return name
    return 'E-Learning'


# ---------------------------------------------------------------------------
# Steckbrief aus dem Ablageort

def _teile(pfad):
    p = os.path.abspath(pfad)
    out = os.path.join(ROOT, ORDNER)
    try:
        rel = os.path.relpath(p, out)
    except ValueError:   # anderes Laufwerk
        return None
    if rel == '.' or rel.startswith('..'):
        return None
    return rel.replace(os.sep, '/').split('/')


def aus_pfad(pfad):
    """Steckbrief aus dem Ablageort (Themenordner oder eine Datei darin). Fehler, wenn der Pfad nicht im Schema liegt."""
    t = _teile(pfad)
    if not t:
        raise UnterrichtsmaterialFehler('%s liegt nicht unter Unterricht/.' % pfad)
    if len(t) < 4 or t[0] in SONDERORDNER:
        raise UnterrichtsmaterialFehler('Unterricht/%s ist kein Themenordner. Schema: Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/' % '/'.join(t))
    sb = dict(zip(FELDER, t[:4]))
    sb['ordner'] = 'Unterricht/' + '/'.join(t[:4])
    return sb


def pruefen(sb):
    """Fehler in den vier Feldern (Liste von Sätzen, leer = alles in Ordnung)."""
    f = []
    for feld in FELDER:
        if '_' in sb[feld]:
            f.append('%s "%s": "_" trennt nur die vier Felder im Paketnamen und darf im Namen nicht vorkommen (Wörter mit - verbinden).' % (feld.capitalize(), sb[feld]))
    if not RX_KLASSE.match(sb['klasse']):
        f.append('Klasse "%s": erwartet ist ein Klassenkürzel in Großbuchstaben (%s) oder %s, %s.'
                 % (sb['klasse'], ', '.join(BEISPIELE), SAMMELNAMEN[0], SAMMEL))
    if not RX_FACH.match(sb['fach']):
        f.append('Fach "%s": erwartet ist ein Kürzel aus %s (LF1, Eth, PuG).' % (sb['fach'], FAECHER))
    elif not fachname(sb['fach'], sb['klasse']):
        f.append('Fach "%s" steht nicht in %s (Zeile "Kürzel | voller Name | Klassen" ergänzen; gibt es das Kürzel für mehrere Klassen, fehlt dort %s).'
                 % (sb['fach'], FAECHER, sb['klasse']))
    if '_' in sb['abschnitt'] + sb['thema']:
        return f
    if not RX_ABSCHNITT.match(sb['abschnitt']):
        f.append('Abschnitt "%s": erwartet ist %s.' % (sb['abschnitt'], abschnitt_arten()))
    if not RX_THEMA.match(sb['thema']):
        f.append('Thema "%s": nur Buchstaben, Ziffern und -, erstes Zeichen groß, Umlaute als ae/oe/ue/ss.' % sb['thema'])
    return f


# ---------------------------------------------------------------------------
# Steckbrief in der Seite

def _ohne_kommentare(s):   # Kommentare durch gleich lange Leerstellen ersetzen: Fundstellen behalten ihre Position
    return re.sub(r'<!--.*?-->', lambda m: ' ' * len(m.group(0)), s, flags=re.S)


def titel(seite):
    """Inhalt von <title> (ohne Kommentare der Vorlage), '' wenn keiner da ist."""
    m = re.search(r'<title>(.*?)</title>', _ohne_kommentare(seite), re.S | re.I)
    return _html.unescape(re.sub(r'\s+', ' ', m.group(1))).strip() if m else ''


def _rx_meta(feld):
    return re.compile(r'<meta\s+name="%s"\s+content="([^"]*)"\s*/?>' % feld, re.I)


def aus_seite(seite):
    """Steckbrief, wie er in der Seite steht: nur die vorhandenen Felder."""
    kopf = _ohne_kommentare(seite)
    sb = {}
    for feld in FELDER:
        m = _rx_meta(feld).search(kopf)
        if m:
            sb[feld] = _html.unescape(m.group(1))
    return sb


def in_seite(seite, sb):
    """Seite mit dem Steckbrief sb: vier <meta>-Zeilen direkt vor <title>, vorhandene werden ersetzt."""
    nl = '\r\n' if '\r\n' in seite else '\n'
    kopf = _ohne_kommentare(seite)
    for feld in FELDER:   # vorhandene Zeilen entfernen (von hinten, damit die Positionen stimmen)
        for m in reversed(list(_rx_meta(feld).finditer(kopf))):
            ende = m.end()
            if seite[ende:ende + 2] == '\r\n':
                ende += 2
            elif seite[ende:ende + 1] == '\n':
                ende += 1
            seite = seite[:m.start()] + seite[ende:]
            kopf = kopf[:m.start()] + kopf[ende:]
    m = re.search(r'<title>', kopf, re.I)
    if not m:
        raise UnterrichtsmaterialFehler('Die Seite hat kein <title>: Der Steckbrief kann nicht eingetragen werden.')
    zeilen = ''.join('<meta name="%s" content="%s">%s' % (feld, _html.escape(sb[feld]), nl) for feld in FELDER)
    return seite[:m.start()] + zeilen + seite[m.start():]


def schreibe_steckbrief(ordner, start='index.html'):
    """Schreibt den Steckbrief aus dem Ablageort in die Startseite. Rückgabe: (Steckbrief, geändert)."""
    sb = aus_pfad(ordner)
    fehler = pruefen(sb)
    if fehler:
        raise UnterrichtsmaterialFehler(' '.join(fehler))
    pfad = os.path.join(ROOT, sb['ordner'], *start.split('/'))
    if not os.path.isfile(pfad):
        raise UnterrichtsmaterialFehler('%s/%s nicht gefunden.' % (sb['ordner'], start))
    alt = lesen(pfad)
    neu = in_seite(alt, sb)
    if neu != alt:
        schreiben(pfad, neu)
    return sb, neu != alt


# ---------------------------------------------------------------------------
# Namen von Paketen und Kursen

def paketname(sb):
    return '%s_%s_%s_%s_scorm.zip' % tuple(sb[f] for f in FELDER)


def paketpfad(sb):
    """Ort des Pakets ab Projektordner: im Unterordner je Klasse und Fach, der volle Name bleibt (ein heruntergeladenes Paket ist allein erkennbar)."""
    return 'BYCS-SYNC/Pakete/%s/%s/%s' % (sb['klasse'], sb['fach'], paketname(sb))


def aus_paketname(name):
    """Steckbrief aus dem Dateinamen eines Pakets , None wenn er nicht passt."""
    m = RX_PAKET.match(os.path.basename(name))
    if not m:
        return None
    return dict(zip(FELDER, m.groups()))


RX_VERSIONEN = re.compile(r'<!-- VERSIONEN:[^\r\n]*\r?\n(.*?)-->', re.S)
RX_VERSION = re.compile(r'V\d+\.\d+ \| \d{2}\.\d{2}\.\d{4} \| Commit \S+ \| ')


def stand(seite):
    """Neueste Zeile der Änderungsliste (Kommentar VERSIONEN) einer Seite, '' wenn sie noch nie als Lernpaket gebaut wurde."""
    m = RX_VERSIONEN.search(seite)
    for z in re.split(r'\r?\n', m.group(1) if m else ''):
        if RX_VERSION.match(z.strip()):
            return z.strip()
    return ''


def gebaut(rel):
    """Ort für Gebautes (Lernpaket, Kurssicherung) zu einem Pfad wie BYCS-SYNC/Pakete/…: Nur auf GitHub im Projektordner.
    Auf jedem anderen Rechner im Temp-Ordner, nie im Repo: Pakete und Kurse entstehen nur über GitHub."""
    basis = ROOT if os.environ.get('GITHUB_ACTIONS') == 'true' else os.path.join(tempfile.gettempdir(), 'Unterricht-gebaut')
    return os.path.join(basis, *rel.replace('\\', '/').split('/'))


def paket_quelle(pfad):
    """Themenordner (ab Projektordner) zu einem Paket (Dateiname oder Pfad), None wenn der Name nicht passt."""
    sb = aus_paketname(pfad)
    return '%s/%s' % (ORDNER, '/'.join(sb[f] for f in FELDER)) if sb else None


def lernpakete():
    """Alle Themenordner (ab Projektordner), aus denen ein Lernpaket entsteht: Die index.html trägt eine Version."""
    liste = []
    for seite in glob.glob(os.path.join(glob.escape(os.path.join(ROOT, ORDNER)), '*', '*', '*', '*', 'index.html')):
        rel = os.path.relpath(os.path.dirname(seite), ROOT).replace(os.sep, '/')
        if rel.split('/')[1] not in SONDERORDNER and stand(lesen(seite)):
            liste.append(rel)
    return sorted(liste)


RX_KURS_JAHR = re.compile(r'(?<!\d)(20\d\d|\d\d-\d\d)(?!\d)')


def ist_kursplan(rel):
    """Kursplan: Unterricht/<Klasse>/Kurs-….json (mehrere Fächer) oder Unterricht/<Klasse>/<Fach>/Kurs-….json (ein Fach)."""
    t = rel.replace('\\', '/').split('/')
    return len(t) in (3, 4) and t[0] == ORDNER and t[-1].startswith('Kurs-') and t[-1].endswith('.json')


def kursplaene():
    """Alle Kurspläne ab Projektordner."""
    basis = glob.escape(os.path.join(ROOT, ORDNER))
    return sorted(os.path.relpath(p, ROOT).replace(os.sep, '/')
                  for tiefe in (('*',), ('*', '*')) for p in glob.glob(os.path.join(basis, *tiefe, 'Kurs-*.json')))


def kursname(plan):
    """Name des Kurses = Dateiname des Kursplans ohne .json, z. B. Kurs-ALLE10-PuG."""
    return os.path.basename(plan.replace('\\', '/'))[:-len('.json')]


def kursplan_fehler(rel):
    """Namensregel: Kurs-<Klasse>[-<Fach>][-<Zusatz>].json, Klasse und Fach wie der Ordner, keine Jahreszahl. Rückgabe: Fehler."""
    t, name = rel.split('/'), kursname(rel)
    soll = 'Kurs-' + '-'.join(t[1:-1])
    if name != soll and not name.startswith(soll + '-'):
        return ['%s: Der Kursplan heißt nach seinem Ort %s.json oder %s-<Zusatz>.json.' % (rel, soll, soll)]
    zusatz = name[len(soll):]
    if not re.match(r'(-[A-Za-z0-9]+)*$', zusatz):
        return ['%s: Im Namen sind nur Buchstaben, Ziffern und Bindestriche erlaubt.' % rel]
    if RX_KURS_JAHR.search(zusatz):
        return ['%s: Keine Jahreszahl im Dateinamen. Das Schuljahr steht im Kursplan (vollname, kurzname).' % rel]
    return []


def kursdatei(plan):
    """Kurssicherung ab Projektordner: heißt wie der Kursplan, ohne Datum, ein neuer Bau ersetzt die alte Datei.
    Sie liegt im selben Unterordner wie der Kursplan unter Unterricht/ (Klasse, bei einem Fach auch Fach), wie Pakete
    und Tests. Ein Kursplan an einem anderen Ort (nur zum Ausprobieren) landet direkt in Kurse/."""
    rel = plan.replace('\\', '/')
    ordner = rel.split('/')[1:-1] if ist_kursplan(rel) else []
    return '/'.join(['BYCS-SYNC', 'Kurse'] + ordner + [kursname(rel) + '.mbz'])


# ---------------------------------------------------------------------------
# Aufruf

def _liste():
    out = os.path.join(ROOT, ORDNER)
    baum = {}
    for klasse in sorted(os.listdir(out)) if os.path.isdir(out) else []:
        if klasse in SONDERORDNER or not os.path.isdir(os.path.join(out, klasse)):
            continue
        for fach in sorted(os.listdir(os.path.join(out, klasse))):
            p = os.path.join(out, klasse, fach)
            if os.path.isdir(p):
                baum.setdefault(klasse, {})[fach] = sorted(a for a in os.listdir(p) if os.path.isdir(os.path.join(p, a)))
    print('Fächer (%s, nach Abteilung, Klasse, Kürzel):' % FAECHER)
    for f in faecher():
        print('  %-6s %s%s' % (f['kuerzel'], f['name'], '  [%s]' % ', '.join(f['klassen']) if f['klassen'] else ''))
    bekannt = sorted({k for f in faecher() for k in f['klassen']} | set(baum))
    print('Klassen: %s (Sammelnamen: %s)' % (', '.join(bekannt) or 'noch keine', ', '.join(SAMMELNAMEN)))
    print('Vorhandene Abschnitte:')
    for klasse in sorted(baum):
        for fach, abschnitte in sorted(baum[klasse].items()):
            print('  %s/%s/%s: %s' % (ORDNER, klasse, fach, ', '.join(abschnitte) or 'leer'))
    return 0


def main(argv=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # profil.py liegt daneben, egal wer main() aufruft
    import profil
    profil.utf8_ausgabe()
    argv = list(sys.argv[1:] if argv is None else argv)
    if '--liste' in argv:
        return _liste()
    schreibe = '--schreiben' in argv
    ordner = [a for a in argv if not a.startswith('--')]
    if not ordner:
        print(__doc__)
        return 2
    code = 0
    for o in ordner:
        try:
            if schreibe:
                sb, geaendert = schreibe_steckbrief(o)
                print('%s: Steckbrief %s.' % (sb['ordner'], 'geschrieben' if geaendert else 'stimmt schon'))
            else:
                sb = aus_pfad(o)
                fehler = pruefen(sb)
                print(sb['ordner'])
                print('  Klasse %s (%s) · Fach %s (%s) · Abschnitt %s · Thema %s (%s)' % (
                    sb['klasse'], ausbildungsjahr(sb['klasse']), sb['fach'], fachname(sb['fach'], sb['klasse']) or 'unbekannt',
                    sb['abschnitt'], sb['thema'], art(sb['thema'])))
                print('  Paket: ' + paketpfad(sb))
                for t in fehler:
                    print('  FEHLER: ' + t)
                code = code or (1 if fehler else 0)
        except UnterrichtsmaterialFehler as e:
            print('FEHLER: %s' % e)
            code = 1
    return code


if __name__ == '__main__':
    sys.exit(main())
