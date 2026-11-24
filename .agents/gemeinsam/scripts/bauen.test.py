"""
bauen.test.py - prüft bauen.py (verlinkter Kern, Bilder, Auslagern) und dass die Kern-Dateien zu den Vorlagen passen.
Aufruf im Projektordner (am Mac python3 statt python):  python .agents/gemeinsam/scripts/bauen.test.py
Arbeitet nur in einem temporären Ordner und liest das Projekt; im Projekt wird nichts geändert.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FEHLER = []
KERN = '../../../../.agents/gemeinsam/templates/kern/'
DATA = 'src="data:image/png;base64,iVBORw0KGgp4eXo="'


def modul(name):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), os.path.join(HERE, name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pruefe(ok, text):
    print(('  ok      ' if ok else '  FEHLER  ') + text)
    if not ok:
        FEHLER.append(text)


def wirft(f, *a):
    try:
        f(*a)
    except Exception as e:
        return type(e).__name__ == 'BauFehler'
    return False


def schreibe(pfad, text, eol='\n'):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, 'wb') as f:
        f.write(text.replace('\n', eol).encode('utf-8'))


def lies(pfad):
    with open(pfad, 'rb') as f:
        return f.read()


def main():
    b = modul('bauen')
    tmp = tempfile.mkdtemp(prefix='bauen-test-')
    try:
        b.ROOT = tmp
        b.KERN_TPL = os.path.join(tmp, '.agents', 'gemeinsam', 'templates', 'kern')
        b.VORLAGEN = os.path.join(tmp, 'Vorlagen')
        css, js1, js2 = 'body { color: red; }\n.a { b: c }', 'var a = 1;\nvar x = "</b>";', 'function f() {\n  return 2;\n}'
        schreibe(os.path.join(b.KERN_TPL, 'Fachunterricht.head.css'), '\n' + css + '\n')
        schreibe(os.path.join(b.KERN_TPL, 'Fachunterricht.scripts-1.js'), '\n' + js1 + '\n')
        schreibe(os.path.join(b.KERN_TPL, 'Fachunterricht.scripts-2.js'), '\n' + js2 + '\n')
        schreibe(os.path.join(tmp, 'Vorlagen', 'team', 'kern', 'Name.stil.css'), '\n.t { u: v }\n')
        fehler_script = '<script>\n  window.addEventListener("error", function(){});\n</script>'
        quelle = ('<!doctype html>\n<html><head><title>T</title>\n<!-- Fachunterricht.html:head -->\n' + fehler_script +
                  '\n<style>\n' + css + '\n</style>\n<style id="zeichen-schriften"></style>\n<!-- /Fachunterricht.html:head -->\n'
                  '</head><body>\n<img ' + DATA + '>\n<!-- Fachunterricht.html:tools -->\n<div class="tools"></div>\n'
                  '<!-- /Fachunterricht.html:tools -->\n<!-- Fachunterricht.html:scripts -->\n<script>\n' + js1 +
                  '\n</script>\n<script>\n' + js2 + '\n</script>\n<!-- /Fachunterricht.html:scripts -->\n'
                  '<!-- team/Name.html:stil -->\n<style>\n.t { u: v }\n</style>\n<!-- /team/Name.html:stil -->\n'
                  '</body></html>\n')
        seitenordner = os.path.join(tmp, 'Unterricht', 'A', 'B', 'T')
        seite = os.path.join(seitenordner, 'index.html')
        png = b'\x89PNG\r\n\x1a\nxyz'

        print('Seite ohne Verweise kommt unverändert zurück')
        einfach = '<!doctype html>\n<html><body><p>Hallo</p></body></html>\n'
        schreibe(seite, einfach)
        pruefe(b.gebaut(seite) == einfach, 'unverändert')

        for eol, name in (('\n', 'LF'), ('\r\n', 'CRLF')):
            print('Auslagern und Rückbau (%s)' % name)
            schreibe(seite, quelle, eol)
            os.makedirs(os.path.join(seitenordner, 'bilder'), exist_ok=True)
            with open(os.path.join(seitenordner, 'bilder', 'b.png'), 'wb') as f:
                f.write(png)
            alt = lies(seite)
            status, _ = b.auslagern(seite, schreiben=False)
            pruefe(status == 'ausgelagert' and lies(seite) == alt, 'Probelauf ändert nichts')
            status, _ = b.auslagern(seite, schreiben=True)
            neu = lies(seite).decode('utf-8')
            pruefe(status == 'ausgelagert', 'Status ausgelagert: ' + status)
            pruefe('<link rel="stylesheet" href="%sFachunterricht.head.css">' % KERN in neu, 'Stil als relativer Verweis')
            pruefe('<script src="%sFachunterricht.scripts-2.js"></script>' % KERN in neu, 'Script als relativer Verweis')
            pruefe('href="../../../../Vorlagen/team/kern/Name.stil.css"' in neu, 'Kern der Team-Vorlage')
            pruefe('window.addEventListener' in neu and 'zeichen-schriften' in neu, 'Fehler-Script und Platzhalter der Schrift fürs Zeichnen bleiben')
            pruefe(b.auslagern(seite)[0] == 'schon ausgelagert', 'zweiter Lauf: schon ausgelagert')
            gebaut = b.gebaut(seite)
            pruefe(gebaut == alt.decode('utf-8'), 'gebaut gleicht der alten Seite Zeichen für Zeichen')
            pruefe(b.gebaut_bytes(seite) == alt, 'gebaut_bytes gleicht den alten Bytes')
            bild = neu.replace(DATA, 'src="bilder/b.png"')
            pruefe(b.gebaut_text(bild, seitenordner) == gebaut, 'Bild aus bilder/ wird zur data:-Adresse')

        for eol, name in (('\n', 'LF'), ('\r\n', 'CRLF')):
            print('Schrift fürs Zeichnen: einmal in kern/, gebaut wieder <style id="zeichen-schriften"> (%s)' % name)
            schrift = '\n/* Schrift */\n@font-face{font-family:"X";src:url(data:font/woff;base64,AAAA) format("woff")}\n'
            schreibe(os.path.join(b.KERN_TPL, b.SCHRIFT_DATEI), schrift)
            mit = quelle.replace('<style id="zeichen-schriften"></style>', '<style id="zeichen-schriften">' + schrift + '</style>')
            schreibe(seite, mit, eol)
            alt = lies(seite)
            status, _ = b.auslagern(seite, schreiben=True)
            neu = lies(seite).decode('utf-8')
            pruefe(status == 'ausgelagert' and '<link rel="stylesheet" href="%s%s" id="zeichen-schriften">' % (KERN, b.SCHRIFT_DATEI)
                   in neu and '@font-face' not in neu, 'Schrift als Verweis mit id, nicht mehr in der Quelle')
            pruefe(b.gebaut_bytes(seite) == alt, 'gebaut gleicht den alten Bytes (Schrift wieder eingebettet)')
            pruefe(os.path.join(b.KERN_TPL, b.SCHRIFT_DATEI) in b.kern_dateien(seite) and b.quelle_fehler(neu, seitenordner) == [],
                   'Verweis zählt als Kern-Datei und ist in der Quelle erlaubt')
        leer = b.stuecke('<style>\na\n</style>\n<style id="zeichen-schriften"></style>', b.FACH_NAME, 'head')
        pruefe([t[2] for t in leer] == ['style'], 'leerer Platzhalter wird nicht ausgelagert')

        print('Fehlerfälle')
        schreibe(seite, quelle)
        b.auslagern(seite, schreiben=True)
        gut = lies(seite).decode('utf-8')
        kopf = KERN + 'Fachunterricht.head.css'
        for was, ersatz in ((kopf, KERN + 'Gibtsnicht.css'), ('../../../../.agents', '../../../../../../..'),
                            (kopf, 'https://example.org/kern/x.css'), (kopf, 'bilder/b.png')):
            pruefe(wirft(b.gebaut_text, gut.replace(was, ersatz, 1), seitenordner), 'Fehler bei Verweis "%s"' % ersatz)
        alt_kern = gut.replace(KERN, KERN.replace('.agents', '.claude'))
        try:
            b.gebaut_text(alt_kern, seitenordner)
            meldung = ''
        except b.BauFehler as e:
            meldung = str(e)
        pruefe('sync-vorlage.py --datei' in meldung, 'Alter Kern-Pfad (.claude/): Bau nennt die Reparatur: ' + meldung[:60])
        pruefe(any('sync-vorlage.py --datei' in f for f in b.quelle_fehler(alt_kern, seitenordner)),
               'Alter Kern-Pfad (.claude/): Prüfung der Quelle nennt die Reparatur')
        pruefe(wirft(b.gebaut_text, gut.replace(DATA, 'src="bilder/fehlt.png"'), seitenordner), 'Fehler bei fehlendem Bild')
        pruefe(wirft(b.gebaut_text, gut.replace(DATA, 'src="bilder/../../x.png"'), seitenordner),
               'Fehler bei Bild außerhalb von bilder/')

        print('Veralteter Kern: nichts wird geschrieben')
        schreibe(seite, quelle.replace('var a = 1;', 'var a = 2;'))
        alt = lies(seite)
        status, text = b.auslagern(seite, schreiben=True)
        pruefe(status == 'Fehler' and lies(seite) == alt and 'Zeile' in text, 'Fehler mit Stelle: ' + text[:60])

        print('Seite ohne Markierungen')
        schreibe(seite, einfach)
        pruefe(b.auslagern(seite)[0] == 'ohne Kern', 'ohne Kern')

        print('Wer nutzt den Kern, was ist in der Quelle erlaubt')
        schreibe(seite, quelle)
        b.auslagern(seite, schreiben=True)
        pruefe(b.ist_kern_datei('.agents/gemeinsam/templates/kern/Fachunterricht.head.css')
               and b.ist_kern_datei('Vorlagen/team/kern/Name.stil.css')
               and not b.ist_kern_datei('.agents/gemeinsam/templates/Fachunterricht.html')
               and not b.ist_kern_datei('Unterricht/A/B/C/T/index.html'), 'ist_kern_datei')
        pruefe(len(b.kern_dateien(seite)) == 4, 'kern_dateien: vier Verweise (Stil, zwei Scripte, Team-Stil)')
        pruefe(b.themen_mit_kern(['.agents/gemeinsam/templates/kern/Fachunterricht.scripts-2.js']) == ['Unterricht/A/B/T'],
               'themen_mit_kern findet die Seite')
        pruefe(b.themen_mit_kern(['Vorlagen/team/kern/Name.stil.css']) == ['Unterricht/A/B/T'], 'themen_mit_kern: Kern der Team-Vorlage')
        pruefe(b.themen_mit_kern(['Vorlagen/team/kern/Andere.stil.css', 'Unterricht/A/B/T/index.html']) == [],
               'themen_mit_kern: andere Kern-Datei und Seite selbst zählen nicht')
        pruefe(b.quelle_fehler(lies(seite).decode('utf-8'), seitenordner) == [], 'Quelle mit Verweisen auf kern/ ist in Ordnung')
        gut = lies(seite).decode('utf-8')
        for was, ersatz, wort in ((KERN + 'Fachunterricht.head.css', KERN + 'Gibtsnicht.css', 'fehlt'),
                                  (KERN + 'Fachunterricht.head.css', 'stil.css', 'kern/'),
                                  (KERN + 'Fachunterricht.head.css', '/etc/x.css', 'relative'),
                                  (KERN + 'Fachunterricht.head.css', 'file:///x.css', 'relative')):
            f = b.quelle_fehler(gut.replace(was, ersatz, 1), seitenordner)
            pruefe(len(f) == 1 and wort in f[0], 'Quelle: Fehler bei "%s": %s' % (ersatz, f))
        pruefe(b.quelle_fehler(gut.replace(KERN + 'Fachunterricht.head.css', 'https://example.org/x.css', 1), seitenordner) == [],
               'Quelle: Externes meldet seite-pruefen.py an der gebauten Fassung, nicht hier')
        schreibe(os.path.join(seitenordner, 'bilder', 'b.svg'), '<svg/>')
        pruefe(b.quelle_fehler('<link rel="icon" href="bilder/b.svg">', seitenordner) == [], 'Quelle: Verweis auf bilder/ mit Datei')
        pruefe(len(b.quelle_fehler('<link rel="icon" href="bilder/fehlt.svg">', seitenordner)) == 1, 'Quelle: Verweis auf bilder/ ohne Datei')
        draussen = gut.replace('</body>', '<link rel="stylesheet" href="%sFachunterricht.head.css"></body>' % KERN)
        f = b.quelle_fehler(draussen, seitenordner)
        pruefe(len(f) == 1 and 'außerhalb der Vorlagenblöcke' in f[0], 'Quelle: Verweis auf kern/ außerhalb der Blöcke: %s' % f)
        for text in ('<img srcset="bilder/b.svg 2x">', "<img src='bilder/b.svg'>", '<div style="background:url(bilder/b.svg)">'):
            f = b.quelle_fehler(gut.replace('</body>', text + '</body>'), seitenordner)
            pruefe(len(f) == 1 and 'nicht eingebettet' in f[0], 'Quelle: %s wird nicht eingebettet: %s' % (text, f))
        pruefe(b.quelle_fehler(gut.replace('</body>', '<img src="bilder/b.svg"></body>'), seitenordner) == [],
               'Quelle: src="bilder/…" wird eingebettet')
        pruefe(b.quelle_fehler('<p>Ausbilder/in</p>', seitenordner) == [], 'Quelle: "Ausbilder/in" ist kein Verweis auf bilder/')
        pruefe(b.themen_mit_bauskript(['Unterricht/x.html'], 'HEAD') == [], 'themen_mit_bauskript: bauen.py nicht geändert')

        print('Bilder auslagern')
        import base64
        b1 = base64.b64encode(b'\x89PNG\r\n\x1a\nAAA').decode()
        b2 = base64.b64encode(b'\xff\xd8\xffBBB').decode()
        for eol, name in (('\n', 'LF'), ('\r\n', 'CRLF')):
            shutil.rmtree(os.path.join(seitenordner, 'bilder'), ignore_errors=True)
            bq = quelle.replace(DATA, 'src="data:image/png;base64,%s"' % b1).replace(
                '</body>', '<img src="data:image/png;base64,%s"><a href="data:image/jpeg;base64,%s">x</a>'
                '<img src="data:image/png;base64,%s==">'
                '<script>var i = new Image(); i.src="data:image/png;base64,%s";</script>'
                '<style>.k { background: url(data:image/png;base64,%s) }</style></body>' % (b1, b2, b1, b1, b1))
            schreibe(seite, bq, eol)
            alt = lies(seite)
            status, text = b.bilder_auslagern(seite, schreiben=False)
            pruefe(status == 'ausgelagert' and lies(seite) == alt and not os.path.isdir(os.path.join(seitenordner, 'bilder')),
                   'Probelauf (%s) ändert nichts: %s' % (name, text))
            status, text = b.bilder_auslagern(seite, schreiben=True)
            neu = lies(seite).decode('utf-8')
            pruefe(status == 'ausgelagert', 'Status ausgelagert: ' + status + ' ' + text)
            pruefe(sorted(os.listdir(os.path.join(seitenordner, 'bilder'))) == ['bild-01.png', 'bild-02.jpg'],
                   'gleiche Bilder nur einmal, Nummer in Reihenfolge')
            pruefe(neu.count('src="bilder/bild-01.png"') == 2 and 'href="bilder/bild-02.jpg"' in neu, 'relative Adressen gesetzt')
            pruefe('base64,%s==' % b1 in neu, 'unsauberes base64 bleibt eingebettet')
            pruefe('i.src="data:image/png' in neu and 'url(data:image/png' in neu, 'Script und CSS bleiben unberührt')
            pruefe(b.gebaut_bytes(seite) == alt, 'gebaut gleicht der alten Seite Byte für Byte')
            pruefe(b.bilder_auslagern(seite)[0] == 'keine Bilder', 'zweiter Lauf findet nichts Neues')
            schreibe(seite, bq, eol)
            alt = lies(seite)
            shutil.rmtree(os.path.join(seitenordner, 'bilder'), ignore_errors=True)
            b.auslagern(seite, schreiben=True)
            status, text = b.bilder_auslagern(seite, schreiben=True)
            pruefe(status == 'ausgelagert' and b.gebaut_bytes(seite) == alt, 'erst Kern, dann Bilder (%s): gebaut gleicht alt: %s' % (name, text))
        shutil.rmtree(os.path.join(seitenordner, 'bilder'), ignore_errors=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('Das Projekt selbst')
    b = modul('bauen')
    r = subprocess.run([sys.executable, '-B', os.path.join(HERE, 'sync-vorlage.py'), '--vorlagen', '--pruefen'],
                       capture_output=True)
    pruefe(r.returncode == 0, 'Kern-Dateien passen zu den Vorlagen (sync-vorlage.py --vorlagen --pruefen)')
    zahl = 0
    for p in b.alle_seiten():
        status, text = b.auslagern(p, schreiben=False)
        if status == 'ohne Kern':
            continue
        zahl += 1
        if status not in ('ausgelagert', 'schon ausgelagert'):
            pruefe(False, '%s: %s %s' % (os.path.relpath(p, b.ROOT), status, text[:80]))
    pruefe(zahl > 0, '%d Seiten im Projekt lassen sich verlustfrei auslagern' % zahl)
    print()
    print('%d Fehler.' % len(FEHLER) if FEHLER else 'Alles bestanden.')
    return 1 if FEHLER else 0


if __name__ == '__main__':
    sys.exit(main())
