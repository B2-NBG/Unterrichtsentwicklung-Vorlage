"""
profil.test.py - prüft das Lesen des Schulprofils (profil.py) und das echte Profil .agents/gemeinsam/data/schule.txt.
Aufruf im Projektordner (am Mac python3 statt python):  python .agents/gemeinsam/scripts/profil.test.py
Arbeitet mit Testdateien in einem temporären Ordner, im Projekt wird nichts geändert. Rückgabe: 0 = alles bestanden.
"""
import contextlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile

HIER = os.path.dirname(os.path.abspath(__file__))
FEHLER = []


def modul():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('profil', os.path.join(HIER, 'profil.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pruefe(ok, text):
    print(('  ok      ' if ok else '  FEHLER  ') + text)
    if not ok:
        FEHLER.append(text)


def wirft(f, *a, **kw):
    try:
        f(*a, **kw)
    except Exception as e:
        return type(e).__name__ == 'ProfilFehler'
    return False


GUT = """# Kommentar
Schule | Beispielschule
Kurzname | BS
Klassenmuster | [5-9][a-e]
Klassenmuster | 1[0-3][a-e]
Klassenmuster | Q1[12]
Jahrgänge | 5 | 13
Jahr-Versatz | 0
Jahr-Bezeichnung | Jahrgangsstufe
Sammelname | ALLE
Abschnitt | LS | Lernsituation | Nummer
Abschnitt | R | Themenreihe | Name
  Niveau  |  Basis | blau | 50
Niveau | Erweitert | rot | 50
Bestehensgrenze | 60
Plattform | Moodle der Schule
Plattform-Art | Moodle
Schutz | aus
Zustellung | download
Farbe-Haupt | #204060
Farbe-Akzent | #E07020
Farbe-Zweit | #208060
Farbe-Dritt | #806040
Farbe-Papier | #FFFFFF
Farbe-Band-Text | #DDDDDD
Logo | .agents/gemeinsam/data/erscheinungsbild/logo.png
Logo-Kursbanner | .agents/gemeinsam/data/erscheinungsbild/kursbanner-logo.png
Leer |
"""


def schreibe(tmp, name, text):
    p = os.path.join(tmp, name)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    return p


def main():
    m = modul()
    m.utf8_ausgabe()
    tmp = tempfile.mkdtemp(prefix='profil-test-')
    try:
        print('Lesen')
        p = schreibe(tmp, 'gut.txt', GUT)
        pruefe(m.wert('Schule', pfad=p) == 'Beispielschule', 'wert: erster Wert')
        pruefe(m.felder('Jahrgänge', pfad=p) == ['5', '13'], 'felder: alle Werte der Zeile')
        pruefe(m.liste('Abschnitt', pfad=p) == [['LS', 'Lernsituation', 'Nummer'], ['R', 'Themenreihe', 'Name']],
               'liste: alle Zeilen in Reihenfolge')
        pruefe(m.liste('Niveau', pfad=p)[0] == ['Basis', 'blau', '50'], 'Leerzeichen um | und am Anfang zählen nicht')
        pruefe(m.zahl('Bestehensgrenze', pfad=p) == 60, 'zahl')
        km = m.muster('Klassenmuster', pfad=p)
        pruefe(all(km.fullmatch(k) for k in ('7b', '10c', 'Q12')) and not any(km.fullmatch(k) for k in ('4a', '7', 'Q13', '7bb')),
               'muster: Alternativen auf eigenen Zeilen (7b, 10c, Q12 ja; 4a, 7, Q13 nein)')
        pruefe(m.wert('Leer', pfad=p) == '', 'leerer Wert bleibt leer')
        pruefe(m.liste('Gibt-es-nicht', pfad=p) == [], 'fehlender Schlüssel: leere Liste')
        pruefe(m.wert('Gibt-es-nicht', 'x', pfad=p) == 'x' and m.felder('Gibt-es-nicht', [], pfad=p) == [],
               'fehlender Schlüssel mit Standardwert')
        pruefe(wirft(m.wert, 'Gibt-es-nicht', pfad=p), 'fehlender Schlüssel ohne Standard: ProfilFehler')
        pruefe(wirft(m.zahl, 'Schule', pfad=p), 'keine Zahl: ProfilFehler')
        pruefe(wirft(m.muster, 'Klassenmuster', pfad=schreibe(tmp, 'oder.txt', GUT.replace('Klassenmuster | [5-9][a-e]', 'Klassenmuster | ([5-9]|1[0-3])[a-e]'))),
               'muster mit | in einer Zeile: ProfilFehler statt Absturz')
        pruefe(m.pruefen(p) == [], 'vollständiges Profil einer anderen Schulart besteht die Prüfung')
        css = m.haus_css(pfad=p)
        pruefe(css.startswith(':root { --haus-haupt:#204060;') and '--haus-akzent-16:rgba(224,112,32,.16);' in css
               and '--haus-akzent-20:rgba(224,112,32,.2);' in css, 'haus_css: Hausfarben und Akzent durchscheinend')
        pruefe(m.logo_data(pfad=p).startswith('data:image/png;base64,iVBOR'), 'logo_data: PNG als data:-Adresse')
        falsch = schreibe(tmp, 'farbe.txt', GUT.replace('Farbe-Haupt | #204060', 'Farbe-Haupt | blau').replace(
            'kursbanner-logo.png', 'gibt-es-nicht.png'))
        f = m.pruefen(falsch)
        pruefe(any('Farbe-Haupt' in t for t in f) and any('Logo-Kursbanner' in t for t in f),
               'Prüfung meldet falsche Farbe und fehlendes Logo')
        pruefe(wirft(m.laden, os.path.join(tmp, 'fehlt.txt')), 'fehlende Datei: ProfilFehler')
        pruefe(wirft(m.laden, schreibe(tmp, 'kaputt.txt', 'Schule Beispiel ohne Strich\n')), 'Zeile ohne |: ProfilFehler')

        print('Prüfen')
        def fehler_bei(alt, neu):
            return m.pruefen(schreibe(tmp, 'f.txt', GUT.replace(alt, neu)))
        pruefe(any('"Plattform"' in f for f in fehler_bei('Plattform | Moodle der Schule\n', '')), 'Pflichtangabe fehlt')
        pruefe(any('Schutz' in f for f in fehler_bei('Schutz | aus', 'Schutz | vielleicht')), 'falscher Auswahlwert')
        pruefe(any('100' in f for f in fehler_bei('Erweitert | rot | 50', 'Erweitert | rot | 40')), 'Niveaus nicht 100 %')
        pruefe(any('regulärer' in f for f in fehler_bei('Klassenmuster | [5-9][a-e]', 'Klassenmuster | [5-9')), 'kaputtes Klassenmuster')
        pruefe(any('eigene Zeile' in f for f in fehler_bei('Klassenmuster | Q1[12]', 'Klassenmuster | Q11|Q12')),
               'Klassenmuster mit | in einer Zeile wird gemeldet')
        pruefe(any('ganze Zahl' in f for f in fehler_bei('Bestehensgrenze | 60', 'Bestehensgrenze | sechzig')), 'Bestehensgrenze keine Zahl')
        flow = fehler_bei('Zustellung | download', 'Zustellung | power-automate')
        pruefe(all(any('"%s"' % k in f for f in flow) for k in ('Teamordner', 'Teamordner-Link', 'Schulkonto', 'Flow-Kopf')),
               'power-automate ohne Teamordner, Link, Schulkonto, Flow-Kopf: gemeldet')
        pruefe(any('"Team-Werkzeug"' in f for f in fehler_bei('Schutz | aus', 'Schutz | teams')), 'teams ohne Team-Werkzeug: gemeldet')
        pruefe(any('drei Werte' in f for f in fehler_bei('Leer |', 'Teamordner | Nur-Team')), 'Teamordner mit einem Wert: gemeldet')

        print('Änderung gilt sofort')
        p2 = schreibe(tmp, 'neu.txt', GUT)
        pruefe(m.wert('Schule', pfad=p2) == 'Beispielschule', 'erster Stand')
        st = os.stat(p2)
        schreibe(tmp, 'neu.txt', GUT.replace('Beispielschule', 'Andere Schule'))
        os.utime(p2, ns=(st.st_atime_ns, st.st_mtime_ns))   # gleiche Änderungszeit wie vorher
        pruefe(m.wert('Schule', pfad=p2) == 'Andere Schule', 'geänderte Datei wird neu gelesen, auch bei gleicher Änderungszeit')

        print('Ausgabe')
        with contextlib.redirect_stdout(io.StringIO()):
            m.utf8_ausgabe()
        pruefe(True, 'utf8_ausgabe bei umgeleiteter Ausgabe ohne Absturz')

        print('Das Profil der Schule')
        pruefe(m.pruefen() == [], 'schule.txt besteht die Prüfung: %s' % ('; '.join(m.pruefen()) or 'ok'))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('Ergebnis: %s' % ('alles bestanden' if not FEHLER else '%d Fehler' % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == '__main__':
    sys.exit(main())
