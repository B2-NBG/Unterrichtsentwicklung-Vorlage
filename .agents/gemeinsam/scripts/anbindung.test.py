"""
anbindung.test.py - prüft die erzeugte Anbindung (anbindung.py): fehlende, veraltete und überzählige Verweisdatei.
Aufruf im Projektordner (am Mac python3 statt python):  python .agents/gemeinsam/scripts/anbindung.test.py
Arbeitet nur in einem temporären Ordner, im Projekt wird nichts geändert.
"""
import importlib.util
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FEHLER = []


def pruefe(ok, text):
    print(('  ok      ' if ok else '  FEHLER  ') + text)
    if not ok:
        FEHLER.append(text)


def schreibe(pfad, text):
    os.makedirs(os.path.dirname(pfad), exist_ok=True)
    with open(pfad, 'w', encoding='utf-8', newline='') as f:
        f.write(text)


def main():
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location('anbindung', os.path.join(HERE, 'anbindung.py'))
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    tmp = tempfile.mkdtemp()
    try:
        schreibe(os.path.join(tmp, '.agents/skills/eins/SKILL.md'), '---\nname: eins\ndescription: Macht eins\n---\n\n# Eins\n')
        schreibe(os.path.join(tmp, '.agents/skills/zwei/SKILL.md'), '---\r\nname: zwei\r\ndescription: Macht zwei\r\n---\r\n\r\n# Zwei\r\n')
        print('Soll')
        s = a.soll(tmp)
        pruefe(set(s) == {a.GEMINI, '.claude/skills/eins/SKILL.md', '.claude/skills/zwei/SKILL.md'}, 'je Skill eine Verweisdatei, dazu Gemini')
        v = s['.claude/skills/eins/SKILL.md']
        pruefe(v.startswith('---\nname: eins\ndescription: Macht eins\n---\n'), 'Kopf 1:1 übernommen')
        pruefe('Lies `.agents/skills/eins/SKILL.md` ganz und arbeite danach.' in v and 'Erzeugt aus' in v, 'Verweis und Hinweis im Text')
        pruefe('\r' not in s['.claude/skills/zwei/SKILL.md'], 'Zeilenenden normalisiert')
        print('Abweichungen')
        pruefe(len(a.abweichungen(tmp)) == 3 and all(z == 'fehlt' for _, z in a.abweichungen(tmp)), 'alles fehlt am Anfang')
        a.schreiben(tmp)
        pruefe(a.abweichungen(tmp) == [], 'nach schreiben() aktuell')
        os.remove(os.path.join(tmp, '.claude/skills/eins/SKILL.md'))
        pruefe(a.abweichungen(tmp) == [('.claude/skills/eins/SKILL.md', 'fehlt')], 'fehlende Verweisdatei wird gemeldet')
        schreibe(os.path.join(tmp, '.claude/skills/zwei/SKILL.md'), 'von Hand geändert\n')
        pruefe(('.claude/skills/zwei/SKILL.md', 'weicht ab') in a.abweichungen(tmp), 'veraltete Verweisdatei wird gemeldet')
        schreibe(os.path.join(tmp, '.claude/skills/alt/SKILL.md'), 'Skill gibt es nicht mehr\n')
        pruefe(('.claude/skills/alt/SKILL.md', 'überzählig') in a.abweichungen(tmp), 'überzählige Verweisdatei wird gemeldet')
        pruefe(len(a.schreiben(tmp)) == 3 and a.abweichungen(tmp) == [], 'schreiben() heilt alle drei')
        pruefe(not os.path.exists(os.path.join(tmp, '.claude/skills/alt')), 'überzähliger Ordner ist entfernt')
        schreibe(os.path.join(tmp, a.GEMINI), '{}\n')
        pruefe(a.abweichungen(tmp) == [(a.GEMINI, 'weicht ab')], 'Gemini-Einstellung wird geprüft')
        a.schreiben(tmp)

        print('AGENTS.md: Blöcke aus dem Schulprofil')
        pruefe(a.AGENTS not in a.soll(tmp), 'AGENTS.md fehlt: nichts erzeugt')
        schreibe(os.path.join(tmp, a.AGENTS), '# Projekt\nVon Hand.\n')
        pruefe(a.AGENTS not in a.soll(tmp), 'AGENTS.md ohne Markierungen: bleibt von Hand')
        hand = ('# Projekt\n## Über mich <!-- AUTO:ich (aus schule.txt) -->\nalt<!-- /AUTO:ich -->\nVon Hand bleibt.\n'
                '- <!-- AUTO:bewertung -->alt<!-- /AUTO:bewertung -->\n<!-- AUTO:unbekannt -->bleibt<!-- /AUTO:unbekannt -->\n')
        schreibe(os.path.join(tmp, a.AGENTS), hand)
        pruefe((a.AGENTS, 'weicht ab') in a.abweichungen(tmp), 'veralteter Block wird gemeldet')
        a.schreiben(tmp)
        neu = open(os.path.join(tmp, a.AGENTS), encoding='utf-8').read()
        pruefe(a.abweichungen(tmp) == [] and 'Von Hand bleibt.' in neu and '>bleibt<' in neu and 'alt<' not in neu,
               'schreiben(): Blöcke erneuert, Text außerhalb und unbekannte Blöcke bleiben')
        pruefe('Ich unterrichte' in neu and 'Bestehensgrenze' in neu, 'Blöcke mit Inhalt aus dem Profil')

        print('Regeln, Helfer, Skills: Blöcke aus dem Schulprofil')
        regel = '.agents/gemeinsam/regeln/probe.md'
        schreibe(os.path.join(tmp, regel), 'Pflicht in <!-- AUTO:sprache-klassen -->x<!-- /AUTO:sprache-klassen -->, '
                 'Zustellung <!-- AUTO:zustellung -->x<!-- /AUTO:zustellung -->.\n')
        schreibe(os.path.join(tmp, '.agents/helfer/ohne.md'), 'Nur <!-- AUTO:unbekannt -->bleibt<!-- /AUTO:unbekannt -->.\n')
        pruefe((regel, 'weicht ab') in a.abweichungen(tmp) and '.agents/helfer/ohne.md' not in a.soll(tmp),
               'Regel mit bekanntem Block wird gemeldet, Datei nur mit unbekanntem Block nicht')
        pruefe('.agents/skills/eins/SKILL.md' not in a.soll(tmp), 'Datei ohne Blöcke bleibt von Hand')
        a.schreiben(tmp)
        neu = open(os.path.join(tmp, regel), encoding='utf-8').read()
        pruefe(a.abweichungen(tmp) == [] and '>x<' not in neu and 'AUTO:sprache-klassen -->`' in neu,
               'schreiben(): Block mit Bindestrich im Namen erneuert')

        class Profil:   # Profil einer anderen Schulart (Gymnasium), ohne Datei
            werte = {'Schulart': ['Gymnasium', 'an einem Gymnasium'], 'Land': ['Hessen'], 'Lehrplan': ['Kerncurriculum Hessen'],
                     'Plattform': ['Schulmoodle'], 'Bestehensgrenze': ['60'], 'Sprache-Pflicht': []}
            zeilen = {'Abschnitt': [['LS', 'Lernsituation', 'Nummer'], ['R', 'Themenreihe', 'Name']],
                      'Niveau': [['Basis', 'grün', '50'], ['Erweitert', 'lila', '50']]}

            def felder(self, k, standard=None):
                return self.werte.get(k) or standard

            def wert(self, k, standard=''):
                return (self.werte.get(k) or [standard])[0]

            def zahl(self, k):
                return int(self.wert(k))

            def liste(self, k):
                return self.zeilen.get(k, [])
        b = a.bloecke(Profil())
        pruefe('Ich unterrichte an einem Gymnasium in Hessen (Lehrplan: Kerncurriculum Hessen).' in b['ich'], 'ich: Schulart, Land, Lehrplan')
        pruefe('Klasse, Fach und Abschnitt (Lernsituation, Themenreihe) wechseln' in b['ich'] and 'Beruf' not in b['ich'],
               'ich: ohne Beruf, Abschnitte aus dem Profil')
        pruefe('Unsere Lernplattform: Schulmoodle.' in b['ich'], 'ich: Lernplattform ohne Beschreibung')
        pruefe('Standard sind zwei Niveaus: **Basis** grün, **Erweitert** lila.' in b['bewertung']
               and 'Basis 50 %, Erweitert 50 % der Punkte. Bestehensgrenze 60 %' in b['bewertung']
               and 'Basis (50 %) ist die Mindestanforderung.' in b['bewertung'] and 'Fragen für die Lernplattform' in b['bewertung'],
               'bewertung: zwei Niveaus, Grenze, Mindestanforderung, Plattform')
        pruefe(b['sprache'] == 'Richtschnur', 'sprache: ohne Pflicht-Klassen nur Richtschnur')
        pruefe(b['sprache-klassen'] == 'keiner Klasse' and b['land'] == 'Hessen' and b['lehrplan'] == 'Kerncurriculum Hessen'
               and 'Lehrkraft fragen' in b['ferien'], 'sprache-klassen, land, lehrplan, ferien ohne Angabe')
        Profil.werte.update({'Sprache-Pflicht': ['BVJ', 'BIK'], 'Zustellung': ['download'], 'Teamordner': ['T', 'B', 'O']})
        b = a.bloecke(Profil())
        pruefe(b['sprache-klassen'] == '`BVJ` oder `BIK`' and b['teamordner'] == '(im Schulprofil keiner, Zustellung "download")',
               'sprache-klassen mit zwei Klassen, Teamordner nur bei power-automate')
        Profil.werte['Zustellung'] = ['power-automate']
        pruefe(a.bloecke(Profil())['teamordner'] == '`T - B/O`', 'teamordner bei power-automate')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print('\n%s' % ('ALLE TESTS BESTANDEN' if not FEHLER else '%d FEHLER' % len(FEHLER)))
    return 1 if FEHLER else 0


if __name__ == '__main__':
    sys.exit(main())
