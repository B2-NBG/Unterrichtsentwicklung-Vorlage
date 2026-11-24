"""
pruefen.test.py - prüft die Textregeln (Schülerinnen und Schüler, Passwort im Klartext) und das Zeilenbudget in pruefen.py.
Aufruf im Projektordner (am Mac python3 statt python):  python .agents/gemeinsam/scripts/pruefen.test.py
Arbeitet nur in einem temporären Ordner, im Projekt wird nichts geändert.
"""
import importlib.util
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FEHLER = []


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


def schreibe(root, rel, text):
    p = os.path.join(root, *rel.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def main():
    m = modul('pruefen')
    print('Schreibweise "Schülerinnen und Schüler"')
    for text, anzahl in (('Schülerinnen und Schüler', 0), ('Schülerinnen und Schülern', 0), ('Schüler sollen', 1),
                         ('die Schüler/innen', 1), ('„Schüler/innen“', 0), ('unseren Schüler*innen', 0),
                         ('Schülersicht', 0), ('Schülerin oder Schüler A', 0), ('Die Schüler lesen', 1), ('Schülers Heft', 1)):
        pruefe(len(m.RX_SCHUELER.findall(text)) == anzahl, '"%s": %d Fund(e)' % (text, anzahl))
    print('Passwort im Klartext')
    for text, anzahl in (('var passwort = "abc123";', 1), ('password: "geheim"', 1), ('const hash = "x"', 0),
                         ('Passwort eingeben', 0)):
        pruefe(len(m.RX_KLARTEXT.findall(text)) == anzahl, '"%s": %d Fund(e)' % (text, anzahl))

    print('Commit einer KI (Co-Authored-By)')
    for text, ok in (('Text\n\nCo-Authored-By: Claude Sonnet <noreply@anthropic.com>', True),
                     ('Text\n\nco-authored-by: KI (Codex) <noreply@invalid>', True),
                     ('Text\n\nCo-Authored-By: Copilot <noreply@github.com>', True),
                     ('Text\n\nCo-Authored-By: Gemini <noreply@google.com>', True),
                     ('Text\n\nCo-Authored-By: Kai Meier <kai@example.org>', False),
                     ('Text ohne Zeile, aber Claude erwähnt', False)):
        pruefe(bool(m.KI_COMMIT.search(text)) == ok, '%s: %s' % (text.split('\n')[-1][:45], 'KI' if ok else 'kein KI-Commit'))

    print('textregeln an Dateien')
    tmp = tempfile.mkdtemp(prefix='pruefen-test-')
    try:
        m.ROOT = tmp
        gut = '<html><meta name="loesung-hash" content="%s"><p>Schülerinnen und Schüler</p></html>' % ('a' * 64)
        schreibe(tmp, 'Unterricht/A/B/C/T/index.html', gut)
        pruefe(m.textregeln(['Unterricht/A/B/C/T/index.html']) == [], 'gute Seite besteht')
        schreibe(tmp, 'Unterricht/A/B/C/T/index.html', gut.replace('Schülerinnen und Schüler', 'Schüler'))
        pruefe(len(m.textregeln(['Unterricht/A/B/C/T/index.html'])) == 1, 'Schüler allein in einer Seite wird gemeldet')
        schreibe(tmp, 'Unterricht/A/B/C/T/index.html', gut.replace('a' * 64, 'geheim'))
        pruefe(len(m.textregeln(['Unterricht/A/B/C/T/index.html'])) == 1, 'Klartext statt Hash in loesung-hash wird gemeldet')
        schreibe(tmp, 'Unterricht/A/B/C/T/index.html', gut + '<script>var passwort = "abc123";</script>')
        pruefe(len(m.textregeln(['Unterricht/A/B/C/T/index.html'])) == 1, 'Klartext-Passwort im Script wird gemeldet')
        schreibe(tmp, 'Unterricht/A/B/C/T/index.html', gut + '<!-- passwort = "abc123" -->')
        pruefe(m.textregeln(['Unterricht/A/B/C/T/index.html']) == [], 'Kommentare zählen nicht')
        schreibe(tmp, '.agents/gemeinsam/regeln/x.md', 'Die Schüler/innen lesen.')
        pruefe(len(m.textregeln(['.agents/gemeinsam/regeln/x.md'])) == 1, 'Schüler/innen in einer Regel wird gemeldet')
        pruefe(m.textregeln(['gibt/es/nicht.html', 'Ressourcen/x.html']) == [], 'fehlende und fremde Dateien werden übergangen')

        print('Größe neuer Dateien')
        schreibe(tmp, 'Ressourcen/klein.jpg', 'x')
        pruefe(m.dateigroessen(['Ressourcen/klein.jpg']) == [], 'kleine Datei besteht')
        with open(os.path.join(tmp, 'Ressourcen/gross.jpg'), 'wb') as f:
            f.write(b'0' * (m.GROESSE_MAX + 1))
        pruefe(len(m.dateigroessen(['Ressourcen/gross.jpg'])) == 1, 'Datei über 5 MB wird gemeldet')
        for rel, anzahl in (('ToDo/x.h5p', 1), ('Ressourcen/x.zip', 1), ('Ressourcen/x.mbz', 1),
                            ('Unterricht/A/B/C/Test-X/Test-X.mbz', 0), ('.agents/skills/moodle-test/templates/V.mbz', 0)):
            schreibe(tmp, rel, 'x')
            pruefe(len(m.dateigroessen([rel])) == anzahl, '%s: %d Fehler' % (rel, anzahl))

        print('Anbindung im Selbsttest')
        schreibe(tmp, 'AGENTS.md', 'Regeln\n')
        schreibe(tmp, '.agents/skills/eins/SKILL.md', '---\nname: eins\ndescription: Macht eins\n---\n')
        fehler = [t for t in m.selbsttest() if 'Anbindung' in t]
        pruefe(any('.claude/skills/eins/SKILL.md fehlt' in t for t in fehler), 'fehlende Verweisdatei wird gemeldet')
        ang = modul('anbindung')
        ang.schreiben(tmp)
        pruefe(not [t for t in m.selbsttest() if 'Anbindung' in t and 'eins' in t], 'erzeugte Verweisdatei besteht')
        schreibe(tmp, '.claude/skills/eins/SKILL.md', 'alt\n')
        pruefe(any('weicht ab' in t for t in m.selbsttest() if 'Anbindung' in t), 'veraltete Verweisdatei wird gemeldet')
        ang.schreiben(tmp)

        print('Zeilenbudget im Selbsttest')
        for rel, text in (('AGENTS.md', 'x\n' * (m.BUDGET_ANWEISUNG + 1)),
                          ('.agents/gemeinsam/regeln/lang.md', 'x\n' * (m.BUDGET_REGELDATEI + 1)),
                          ('.agents/gemeinsam/regeln/lang-admin.md', 'x\n' * (m.BUDGET_REGELDATEI + 50)),
                          ('.agents/skills/S/SKILL.md', '---\nname: S\ndescription: %s\n---\n' % ('y' * (m.BUDGET_BESCHREIBUNG + 1)))):
            schreibe(tmp, rel, text)
        fehler = [t for t in m.selbsttest() if 'Zeilen' in t or 'Zeichen' in t]
        pruefe(any('AGENTS.md hat' in t for t in fehler), 'AGENTS.md über dem Budget wird gemeldet')
        pruefe(any('lang.md hat' in t for t in fehler), 'Regeldatei über dem Budget wird gemeldet')
        pruefe(not any('lang-admin.md' in t for t in fehler), 'Dateien *-admin.md sind ausgenommen')
        pruefe(any('description' in t for t in fehler), 'zu lange Skill-Beschreibung wird gemeldet')
        for n in m.SEITENREGELN:
            schreibe(tmp, '.agents/gemeinsam/regeln/' + n, 'x\n' * (m.BUDGET_SEITENREGELN // len(m.SEITENREGELN) + 1))
        fehler = [x for x in m.selbsttest() if 'zusammen' in x]
        pruefe(len(fehler) == 1, 'Seitenregeln zusammen über dem Budget werden gemeldet')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print()
    print('%d Fehler.' % len(FEHLER) if FEHLER else 'Alles bestanden.')
    return 1 if FEHLER else 0


if __name__ == '__main__':
    sys.exit(main())
