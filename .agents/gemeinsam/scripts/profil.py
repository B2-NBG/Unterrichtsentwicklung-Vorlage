"""
profil.py - liest das Schulprofil .agents/gemeinsam/data/schule.txt (Schule, Schulart, Erscheinungsbild, Niveaus,
Lernplattform, Lehrplan, Zusammenarbeit, Zustellung). Die eine Stelle, an der Skripte Werte der Schule finden.

  import profil                      (Skripte in .agents/gemeinsam/scripts/; andere laden es über den Pfad)
  profil.wert('Schule')              'Staatliche Berufsschule Musterstadt'   (erster Wert der ersten Zeile)
  profil.felder('Jahrgänge')         ['10', '13']                        (alle Werte der ersten Zeile)
  profil.liste('Niveau')             [['Einsteigerniveau', 'blau', '40'], …] (alle Zeilen mit diesem Schlüssel)
  profil.zahl('Bestehensgrenze')     70
  profil.muster('Klassenmuster')     regulärer Ausdruck aus allen Zeilen (je Zeile eine Alternative, denn | trennt Werte)
  profil.utf8_ausgabe()              Ausgabe auf UTF-8 (Windows-Konsole), am Anfang von main()
  profil.haus_css()                  ':root { --haus-haupt:#2F4858; … }' (Hausfarben als CSS-Variablen)
  profil.logo_data('Logo')           Logo als data:-Adresse

Ein anderes Profil (Tests, Beispielprofile): Umgebungsvariable SCHULPROFIL=<Pfad>.
Fehlt ein Schlüssel ohne Standardwert, gibt es einen ProfilFehler mit dem Namen des Schlüssels.
Aufruf im Projektordner (am Mac python3 statt python):
  python .agents/gemeinsam/scripts/profil.py            alle Angaben zeigen und die Pflichtangaben prüfen
  python .agents/gemeinsam/scripts/profil.py --wert Schutz   nur den Wert ausgeben (für den Workflow), leer wenn er fehlt
Nur Python-Standardbibliothek (Windows und Mac, ab Python 3.9).
"""
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HIER)))
# Umgebung SCHULPROFIL: anderes Profil (Tests, Beispielprofile im öffentlichen Spiegel), sonst schule.txt im Repo
DATEI = os.environ.get('SCHULPROFIL') or os.path.join(ROOT, '.agents', 'gemeinsam', 'data', 'schule.txt')
PFLICHT = ('Schule', 'Kurzname', 'Klassenmuster', 'Jahrgänge', 'Jahr-Versatz', 'Jahr-Bezeichnung', 'Sammelname',
           'Abschnitt', 'Niveau', 'Bestehensgrenze', 'Plattform', 'Plattform-Art', 'Schutz', 'Zustellung')
WAHL = {'Schutz': ('teams', 'aus'), 'Zustellung': ('power-automate', 'download')}
PFLICHT_FLOW = ('Teamordner', 'Teamordner-Link', 'Schulkonto', 'Flow-Kopf')   # nur bei Zustellung "power-automate"
PFLICHT_TEAMS = ('Team-Werkzeug',)                                       # nur bei Schutz "teams"
_FEHLT = object()


class ProfilFehler(Exception):
    pass


def utf8_ausgabe():
    """Ausgabe und Fehlerausgabe auf UTF-8 stellen (sonst Fragezeichen statt Umlauten in der Windows-Konsole)."""
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):   # umgeleitete Ausgabe (StringIO) oder schon geschlossen
            pass


def laden(pfad=None):
    """[(Schlüssel, [Werte], Zeilennummer)] in der Reihenfolge der Datei. Ohne Zwischenspeicher: Die Datei ist klein, und
    eine Änderung gilt sofort (auch zwei Änderungen kurz hintereinander mit gleicher Änderungszeit)."""
    pfad = pfad or DATEI
    try:
        with open(pfad, 'rb') as f:
            text = f.read().decode('utf-8-sig')
    except OSError:
        raise ProfilFehler('Das Schulprofil fehlt: %s' % os.path.relpath(pfad, ROOT))
    return zerlegen(text)


def zerlegen(text):
    """Text eines Profils (z. B. aus git show) -> [(Schlüssel, [Werte], Zeilennummer)]."""
    zeilen = []
    for nr, z in enumerate(text.splitlines(), 1):
        z = z.strip()
        if not z or z.startswith('#'):
            continue
        teile = [t.strip() for t in z.split('|')]
        if len(teile) < 2 or not teile[0]:
            raise ProfilFehler('schule.txt, Zeile %d: erwartet ist "Schlüssel | Wert": %s' % (nr, z[:80]))
        zeilen.append((teile[0], teile[1:], nr))
    return zeilen


def liste(schluessel, pfad=None):
    """Alle Zeilen mit diesem Schlüssel, je Zeile die Liste der Werte (leer, wenn keine)."""
    return [w for k, w, _ in laden(pfad) if k == schluessel]


def felder(schluessel, standard=_FEHLT, pfad=None):
    """Alle Werte der ersten Zeile mit diesem Schlüssel."""
    z = liste(schluessel, pfad)
    if z:
        return z[0]
    if standard is _FEHLT:
        raise ProfilFehler('Im Schulprofil (schule.txt) fehlt die Angabe "%s".' % schluessel)
    return standard


def wert(schluessel, standard=_FEHLT, pfad=None):
    """Erster Wert der ersten Zeile mit diesem Schlüssel."""
    f = felder(schluessel, None if standard is not _FEHLT else _FEHLT, pfad)
    return f[0] if f else standard


def zahl(schluessel, standard=_FEHLT, pfad=None):
    w = wert(schluessel, standard, pfad)
    try:
        return int(w)
    except (TypeError, ValueError):
        raise ProfilFehler('Im Schulprofil (schule.txt) ist "%s" keine ganze Zahl: %s' % (schluessel, w))


def muster(schluessel, pfad=None):
    """Regulärer Ausdruck aus allen Zeilen mit diesem Schlüssel, je Zeile eine Alternative ("|" trennt in der Datei die
    Werte, deshalb stehen Alternativen auf eigenen Zeilen). Passt auf den ganzen Text (fullmatch)."""
    teile = [w[0] for w in liste(schluessel, pfad) if w and w[0]]
    if not teile:
        raise ProfilFehler('Im Schulprofil (schule.txt) fehlt die Angabe "%s".' % schluessel)
    try:
        return re.compile('(?:%s)' % ')|(?:'.join(teile))
    except re.error as e:
        raise ProfilFehler('schule.txt: "%s" ist kein gültiger regulärer Ausdruck (%s). "|" trennt in der Datei die Werte: '
                           'jede Alternative auf eine eigene Zeile schreiben.' % (schluessel, e))


# Hausfarben als CSS-Variablen (Vorlage Allgemeinbildung.html, Handbuch): Name -> Schlüssel im Profil
HAUSFARBEN = (('haupt', 'Farbe-Haupt'), ('akzent', 'Farbe-Akzent'), ('zweit', 'Farbe-Zweit'), ('dritt', 'Farbe-Dritt'),
              ('papier', 'Farbe-Papier'), ('band-text', 'Farbe-Band-Text'))
HAUS_ALPHA = (('akzent', 16), ('akzent', 20))   # Akzent durchscheinend (Hervorhebungen), als --haus-akzent-16 usw.
RX_FARBE = re.compile(r'#[0-9A-Fa-f]{6}')


def haus_css(pfad=None):
    """:root { --haus-haupt:#…; … } aus den Hausfarben (eine Zeile). Fehlt eine Farbe: ProfilFehler."""
    teile = []
    farben = {}
    for name, k in HAUSFARBEN:
        w = wert(k, pfad=pfad)
        if not RX_FARBE.fullmatch(w):
            raise ProfilFehler('schule.txt: "%s" ist keine Farbe wie #2F4858: %s' % (k, w))
        farben[name] = w
        teile.append('--haus-%s:%s;' % (name, w))
    for name, prozent in HAUS_ALPHA:
        w = farben[name]
        teile.append('--haus-%s-%d:rgba(%d,%d,%d,%s);' % (name, prozent, int(w[1:3], 16), int(w[3:5], 16), int(w[5:7], 16),
                                                        ('%.2f' % (prozent / 100)).rstrip('0').lstrip('0')))
    return ':root { %s }' % ' '.join(teile)


def logo_data(schluessel='Logo', pfad=None):
    """Das Logo (Pfad im Profil, ab Projektordner) als data:-Adresse (PNG oder JPG). Fehlt es: ProfilFehler."""
    import base64
    rel = wert(schluessel, pfad=pfad)
    datei = os.path.join(ROOT, *rel.replace('\\', '/').split('/'))
    art = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}.get(os.path.splitext(datei)[1].lower())
    if not art or not os.path.isfile(datei):
        raise ProfilFehler('schule.txt: "%s" zeigt nicht auf ein PNG oder JPG im Repo: %s' % (schluessel, rel))
    with open(datei, 'rb') as f:
        return 'data:%s;base64,%s' % (art, base64.b64encode(f.read()).decode('ascii'))


def pruefen(pfad=None):
    """Liste der Fehler im Profil (leer = in Ordnung): Pflichtangaben, Auswahlwerte, Zahlen, Muster, Niveaus."""
    fehler = []
    try:
        laden(pfad)
    except ProfilFehler as e:
        return [str(e)]
    for k in PFLICHT:
        if not liste(k, pfad):
            fehler.append('Im Schulprofil (schule.txt) fehlt die Angabe "%s".' % k)
    for k in (PFLICHT_FLOW if wert('Zustellung', '', pfad) == 'power-automate' else ()) +             (PFLICHT_TEAMS if wert('Schutz', '', pfad) == 'teams' else ()):
        if not liste(k, pfad):
            fehler.append('Im Schulprofil (schule.txt) fehlt die Angabe "%s" (nötig bei %s).'
                          % (k, 'Zustellung "power-automate"' if k in PFLICHT_FLOW else 'Schutz "teams"'))
    if len(felder('Teamordner', [], pfad)) not in (0, 3):
        fehler.append('schule.txt: Teamordner braucht drei Werte: Team | Bibliothek | Ordner.')
    for k, erlaubt in WAHL.items():
        w = wert(k, '', pfad)
        if w and w not in erlaubt:
            fehler.append('schule.txt: "%s" ist %s, erlaubt ist %s.' % (k, w, ' oder '.join(erlaubt)))
    for k in ('Bestehensgrenze', 'Jahr-Versatz'):
        try:
            zahl(k, 0, pfad)
        except ProfilFehler as e:
            fehler.append(str(e))
    for w in liste('Klassenmuster', pfad):
        try:
            re.compile(w[0])
        except re.error as e:
            fehler.append('schule.txt: Klassenmuster "%s" ist kein gültiger regulärer Ausdruck (%s).' % (w[0], e))
        if len(w) > 1:
            fehler.append('schule.txt: Klassenmuster "%s" enthält |: Jede Alternative auf eine eigene Zeile schreiben.'
                          % ' | '.join(w))
    for f in (haus_css, logo_data, lambda pfad: logo_data('Logo-Kursbanner', pfad)):
        try:
            f(pfad=pfad)
        except ProfilFehler as e:
            fehler.append(str(e))
    niveaus = liste('Niveau', pfad)
    if niveaus:
        try:
            summe = sum(int(n[2]) for n in niveaus)
            if summe != 100:
                fehler.append('schule.txt: Die Anteile der Niveaus ergeben %d %%, nicht 100 %%.' % summe)
        except (IndexError, ValueError):
            fehler.append('schule.txt: Niveau braucht Name, Farbe und Anteil in %% (z. B. "Niveau | Einsteigerniveau | blau | 40").')
    return fehler


def main(argv=None):
    utf8_ausgabe()
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['--wert'] and len(argv) == 2:
        try:
            print(wert(argv[1], ''))
        except ProfilFehler as e:
            print('FEHLER: %s' % e, file=sys.stderr)
            return 1
        return 0
    try:
        for k, w, nr in laden():
            print('%4d  %-18s %s' % (nr, k, ' | '.join(w)))
    except ProfilFehler as e:
        print('FEHLER: %s' % e)
        return 1
    fehler = pruefen()
    for f in fehler:
        print('FEHLER: %s' % f)
    print('Schulprofil: %s' % ('in Ordnung.' if not fehler else '%d Fehler.' % len(fehler)))
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main())
