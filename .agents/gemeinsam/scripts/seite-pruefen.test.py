"""
seite-pruefen.test.py - prüft, dass ein Absturz von sync-vorlage.py ein Fehler ist (nie nur ein Hinweis), und wie
seite-pruefen.py Anleitungen zu einem Test (Skill moodle-test) behandelt:
Sie bestehen ohne Leerdruck und PDF-Export, übrige {{…}}-Platzhalter sind ein Fehler, und die Ausnahme gilt nur für
index.html in einem Ordner Test-<…> neben Test-<…>.mbz.
Aufruf im Projektordner (am Mac python3 statt python):  python .agents/gemeinsam/scripts/seite-pruefen.test.py
Arbeitet nur in einem temporären Ordner (baut dort eine Anleitung mit build-test-mbz.py); im Projekt wird nichts geändert.
Ohne Edge/Chrome laufen nur die statischen Teile.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
PRUEFEN = os.path.join(HERE, 'seite-pruefen.py')
BAUEN_TEST = os.path.join(ROOT, '.agents', 'skills', 'moodle-test', 'scripts', 'build-test-mbz.py')
QUIZ = os.path.join(ROOT, 'Unterricht', 'ALLE', 'BerHan', 'M-3D-Druck', 'Test-Praxismodul-3D-Druck',
                    'Fragen-Praxismodul-3D-Druck.xml')
if not os.path.isfile(QUIZ):   # öffentliche Fassung: ohne diesen Test, dafür ein Beispieltest in Unterricht/
    import glob
    QUIZ = (sorted(glob.glob(os.path.join(ROOT, 'Unterricht', '**', 'Test-*', 'Fragen-*.xml'), recursive=True)) or [QUIZ])[0]
NAME = os.path.basename(QUIZ)[len('Fragen-'):-len('.xml')]   # Thema im Dateinamen, z. B. Praxismodul-3D-Druck
FEHLER = []


def modul():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('seite_pruefen', PRUEFEN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pruefe(ok, text):
    print(('  ok      ' if ok else '  FEHLER  ') + text)
    if not ok:
        FEHLER.append(text)


def anlegen(tmp, ordner, mbz=True, text=None):
    """<tmp>/<ordner>/index.html (Text der gebauten Anleitung), auf Wunsch mit <ordner>.mbz daneben."""
    o = os.path.join(tmp, ordner)
    os.makedirs(o, exist_ok=True)
    with open(os.path.join(o, 'index.html'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    if mbz:
        open(os.path.join(o, ordner + '.mbz'), 'wb').close()
    return os.path.join(o, 'index.html')


def lauf(seite, arb, browser):
    r = subprocess.run([sys.executable, PRUEFEN, seite, '--arbeitsordner', arb] + ([] if browser else ['--ohne-browser']),
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    return r.returncode, r.stdout + r.stderr


def main():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # profil.py liegt daneben, egal wer main() aufruft
    import profil
    profil.utf8_ausgabe()
    sp = modul()
    browser = bool(sp.browser())
    print('seite-pruefen.test.py (Browser: %s)' % ('ja' if browser else 'nein, nur statisch'))
    tmp = tempfile.mkdtemp(prefix='seite-pruefen-test-')
    try:
        # Eine echte Anleitung bauen, so wie der Skill moodle-test sie anlegt
        o = os.path.join(tmp, 'Test-' + NAME)
        os.makedirs(o)
        shutil.copy(QUIZ, o)
        r = subprocess.run([sys.executable, BAUEN_TEST, os.path.join(o, os.path.basename(QUIZ)),
                            '--thema', NAME.replace('-', ' '), '--zeit', '20'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        seite = os.path.join(o, 'index.html')
        pruefe(r.returncode == 0 and os.path.isfile(seite), 'build-test-mbz.py baut Anleitung und .mbz')
        if not os.path.isfile(seite):
            print(r.stdout + r.stderr)
            return 1
        with open(seite, encoding='utf-8') as f:
            text = f.read()
        arb = os.path.join(tmp, 'arbeit')

        # Erkennung: nur index.html im Ordner Test-<…> neben Test-<…>.mbz
        pruefe(sp.ist_test_anleitung(seite), 'Anleitung neben der .mbz wird erkannt')
        ohne_mbz = anlegen(tmp, 'Test-Ohne-mbz', mbz=False, text=text)
        pruefe(not sp.ist_test_anleitung(ohne_mbz), 'ohne .mbz keine Test-Anleitung')
        anders = anlegen(tmp, 'Anleitung', text=text)
        pruefe(not sp.ist_test_anleitung(anders), 'Ordner ohne "Test-" ist keine Test-Anleitung')
        andere_datei = os.path.join(o, 'andere.html')
        shutil.copy(seite, andere_datei)
        pruefe(not sp.ist_test_anleitung(andere_datei), 'andere Datei im Test-Ordner ist keine Test-Anleitung')

        # Die gebaute Anleitung besteht, ohne Leerdruck und PDF-Export
        rc, aus = lauf(seite, arb, browser)
        pruefe(rc == 0 and 'BESTANDEN' in aus, 'gebaute Anleitung besteht')
        pruefe('Anleitung zu einem Test' in aus and 'PDF speichern' not in aus and 'printBlank' not in aus,
               'Hinweis auf die Anleitung, kein PDF-Export und kein Leerdruck')
        if rc != 0:
            print(aus)

        # Übrige Platzhalter sind ein Fehler (Kommentar der Vorlage mit {{...}} zählt nicht)
        kaputt = anlegen(tmp, 'Test-Platzhalter', text=text.replace('</footer>', ' {{SUMME}}</footer>', 1))
        rc, aus = lauf(kaputt, arb, False)
        pruefe(rc == 1 and 'Platzhalter der Anleitung übrig: {{SUMME}}' in aus, 'übriger Platzhalter ist ein Fehler')
        pruefe('{{...}}' not in aus, 'Platzhalter im Kommentar zählt nicht')

        # Vorlagenblöcke (sync-vorlage.py im selben Prozess): Ein Absturz ist ein Fehler, nie nur ein Hinweis (fail-closed)
        echt = sp.sync()

        class Ersatz:   # wie sync-vorlage.py, nur main() ist ersetzt
            def __getattr__(self, name):
                return getattr(echt, name)

        class Kaputt(Ersatz):
            def main(self, argv):
                raise RuntimeError('Testabsturz')

        class Rueckgabe(Ersatz):
            def __init__(self, code, text=''):
                self.code, self.text = code, text

            def main(self, argv):
                print(self.text)
                return self.code
        try:
            for ersatz, code, erwartet, art, name in (
                    (Kaputt(), 3, 'sync-vorlage.py ist abgestürzt', 'fehler', 'Absturz ist ein Fehler'),
                    (Rueckgabe(7), 3, 'sync-vorlage.py ist abgestürzt', 'fehler', 'unbekannter Rückgabewert ist ein Fehler'),
                    (Rueckgabe(2, 'Blöcke\nFEHLER: Markierung fehlt'), 2, 'FEHLER: Markierung fehlt', 'fehler',
                     'Blöcke nicht gefunden: Fehler mit der FEHLER-Zeile'),
                    (Rueckgabe(1), 1, 'Vorlagenblöcke nicht aktuell', 'hinweise', 'Abweichung bleibt ein Hinweis'),
                    (Rueckgabe(0), 0, None, None, 'aktuelle Seite: nichts gemeldet')):
                sp._SYNC[:] = [ersatz]
                pruefe(sp.vorlage_pruefen(seite)[0] == code, 'vorlage_pruefen: %s (Code %d)' % (name, code))
                fehler, hinweise = sp.statisch(seite, text)
                meldungen = {'fehler': fehler, 'hinweise': hinweise}
                if erwartet:
                    pruefe(any(erwartet in t for t in meldungen[art]), 'statisch: ' + name)
                else:
                    pruefe(not [t for t in fehler + hinweise if 'sync-vorlage' in t or 'Vorlagenblöcke' in t],
                           'statisch: ' + name)
        finally:
            sp._SYNC[:] = [echt]
        pruefe(sp.vorlage_pruefen(seite)[0] in (0, 1, 2), 'echtes sync-vorlage.py läuft im selben Prozess')

        # Ohne .mbz gilt die volle Prüfung (dann fehlt der PDF-Knopf)
        if browser:
            rc, aus = lauf(ohne_mbz, arb, True)
            pruefe(rc == 1 and '"Als PDF speichern" hat kein PDF erzeugt' in aus, 'ohne .mbz: PDF-Export wird geprüft')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('Ergebnis: %s' % ('alles bestanden' if not FEHLER else '%d Fehler' % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == '__main__':
    sys.exit(main())
