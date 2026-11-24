"""
anbindung.py - erzeugt die Anbindung für KI-Werkzeuge, die die Skills nicht in .agents/skills/ suchen.

Die Skills liegen als Quelle in .agents/skills/<name>/SKILL.md (offener Standard). Manche Werkzeuge suchen in .claude/skills/.
Dort liegt je Skill eine erzeugte Verweisdatei: gleicher Kopf (name, description), Text "Lies die Quelle ganz und arbeite danach".
Zusätzlich gehört .gemini/settings.json dazu (nur context.fileName: AGENTS.md).
In AGENTS.md und in jeder .md-Datei unter .agents/ (Regeln, Helfer, Skills) sind die Blöcke zwischen
<!-- AUTO:<name> … --> und <!-- /AUTO:<name> --> erzeugt, aus dem Schulprofil (.agents/gemeinsam/data/schule.txt):
  ich, bewertung          AGENTS.md: Schule, Lehrplan, Auswahldialog, Lernplattform; Niveaus, Punkte, Bestehensgrenze
  sprache                 "Pflicht in BVJ, BIK und BFS, sonst Richtschnur" (Sprache-Pflicht)
  sprache-klassen         "`BVJ`, `BIK` oder `BFS`" (Sprache-Pflicht, "keiner Klasse" ohne Angabe)
  land, lehrplan, ferien  Land; Lehrplan mit Adresse; Quelle der Ferien und Feiertage
  schutz, zustellung      Betriebsart: "teams" oder "aus"; "power-automate" oder "download"
  teamordner              "`<Team> - <Bibliothek>/<Ordner>`" (nur bei power-automate, sonst ein Hinweis)
So bleibt der Text für die eigene Schule konkret, und ein anderes Profil (Spiegel) bekommt seine eigenen Werte. Den Rest
der Dateien schreiben Werkzeug-Verantwortliche von Hand; ein unbekannter Name bleibt unverändert.

Nicht von Hand ändern: pruefen.py --erneuern schreibt die Dateien neu, pruefen.py ohne --erneuern und auf GitHub meldet
Abweichungen (fehlt, weicht ab, überzählig) als Fehler.
"""
import glob
import importlib.util
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
QUELLE = '.agents/skills'
ZIEL = '.claude/skills'
GEMINI = '.gemini/settings.json'
GEMINI_TEXT = '{\n  "context": {\n    "fileName": ["AGENTS.md"]\n  }\n}\n'
HINWEIS = '<!-- Erzeugt aus %s, nicht von Hand ändern (python .agents/gemeinsam/scripts/pruefen.py --erneuern). -->'
KOPF = re.compile(r'\A---\n.*?\n---\n', re.S)
AGENTS = 'AGENTS.md'
TEXTE = (AGENTS, '.agents/**/*.md')   # Dateien mit erzeugten Blöcken
BLOCK = re.compile(r'(<!-- AUTO:([\w-]+)(?![\w-])[^>]*-->)(.*?)(<!-- /AUTO:\2 -->)', re.S)
ZAHLWORT = {1: 'ein', 2: 'zwei', 3: 'drei', 4: 'vier', 5: 'fünf'}


def _lesen(pfad):
    with open(pfad, 'rb') as f:
        return f.read().decode('utf-8').replace('\r\n', '\n')


def _profil():
    spec = importlib.util.spec_from_file_location('profil', os.path.join(HERE, 'profil.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _aufzaehlung(teile):
    """['a', 'b', 'c'] -> 'a, b und c'."""
    return ', '.join(teile[:-1]) + ' und ' + teile[-1] if len(teile) > 1 else ''.join(teile)


def bloecke(profil=None):
    """{Name: Text} der erzeugten Blöcke in AGENTS.md, aus dem Schulprofil."""
    pr = profil or _profil()
    schulart = pr.felder('Schulart', ['Schule'])
    lehrplan = pr.felder('Lehrplan', [])
    abschnitte = [a[1] for a in pr.liste('Abschnitt') if len(a) > 1]
    angaben = ['Klasse'] + (['Beruf'] if pr.wert('Beruf', '') == 'ja' else []) + ['Fach', 'Abschnitt (%s)' % ', '.join(abschnitte)]
    plattform = pr.wert('Plattform')
    beschreibung = pr.wert('Plattform-Beschreibung', '')
    ich = ('\n- Ich unterrichte %s%s%s.\n- %s wechseln: Sie kommen jedes Mal aus dem Auswahldialog, nie raten. '
           'Unsere Lernplattform: %s%s.') % (
        schulart[1] if len(schulart) > 1 else 'an einer ' + schulart[0],
        ' in %s' % pr.wert('Land') if pr.wert('Land', '') else '',
        ' (Lehrplan: %s)' % ', '.join(lehrplan) if lehrplan else '',
        _aufzaehlung(angaben), plattform, ' (%s)' % beschreibung if beschreibung else '')
    niv = [n for n in pr.liste('Niveau') if len(n) > 2]
    mindest = niv[:-1] if len(niv) > 1 else []
    bewertung = ('Standard sind %s Niveaus: %s. Ohne Niveaus ist in jedem Fach erlaubt, aber nie von selbst: bei neuem '
                 'Unterrichtsmaterial und beim Umbau im Auswahldialog fragen, außer ich habe es schon gesagt.\n'
                 '- Bewertete Pakete: %s der Punkte. Bestehensgrenze %d %%, auch ohne Niveaus.%s\n'
                 '- Am Ende eine Lösung für die Lehrkraft, deutlich abgetrennt. Fragen für die Lernplattform werden immer '
                 'als Test gebaut, es gibt keine Quizze.') % (
        ZAHLWORT.get(len(niv), str(len(niv))), ', '.join('**%s** %s' % (n[0], n[1]) for n in niv),
        ', '.join('%s %s %%' % (n[0], n[2]) for n in niv), pr.zahl('Bestehensgrenze'),
        ' %s (%d %%) %s die Mindestanforderung.' % (' + '.join(n[0] for n in mindest), sum(int(n[2]) for n in mindest),
                                                    'sind' if len(mindest) > 1 else 'ist') if mindest else '')
    pflicht = pr.felder('Sprache-Pflicht', [])
    sprache = 'Pflicht in %s, sonst Richtschnur' % _aufzaehlung(pflicht) if pflicht else 'Richtschnur'
    klassen = ['`%s`' % k for k in pflicht]
    ordner = pr.felder('Teamordner', [])
    ohne = 'kein Hinweis im Schulprofil, die Lehrkraft fragen'
    return {'ich': ich, 'bewertung': bewertung, 'sprache': sprache,
            'sprache-klassen': ', '.join(klassen[:-1]) + ' oder ' + klassen[-1] if len(klassen) > 1 else ''.join(klassen) or 'keiner Klasse',
            'land': pr.wert('Land', '') or 'dem eigenen Land',
            'lehrplan': ', '.join(lehrplan) or ohne,
            'ferien': pr.wert('Ferien-Quelle', '') or ohne,
            'schutz': pr.wert('Schutz'), 'zustellung': pr.wert('Zustellung'),
            'teamordner': '`%s - %s/%s`' % tuple(ordner[:3]) if pr.wert('Zustellung') == 'power-automate' and len(ordner) > 2
            else '(im Schulprofil keiner, Zustellung "%s")' % pr.wert('Zustellung')}


def agents_soll(text, profil=None, b=None):
    """Text mit erneuerten Blöcken; der Text außerhalb der Blöcke und unbekannte Blöcke bleiben, wie sie sind."""
    b = b if b is not None else bloecke(profil)
    return BLOCK.sub(lambda m: m.group(1) + b[m.group(2)] + m.group(4) if m.group(2) in b else m.group(0), text)


def soll(root=ROOT):
    """{relativer Pfad: Text} aller erzeugten Dateien (AGENTS.md und .md unter .agents/ nur mit bekannten Blöcken)."""
    out = {GEMINI: GEMINI_TEXT}
    b = None
    for muster in TEXTE:
        for p in sorted(glob.glob(os.path.join(root, muster), recursive=True)):
            text = _lesen(p)
            if not BLOCK.search(text):
                continue
            b = b if b is not None else bloecke()
            if any(m.group(2) in b for m in BLOCK.finditer(text)):
                out[os.path.relpath(p, root).replace(os.sep, '/')] = agents_soll(text, b=b)
    for q in sorted(glob.glob(os.path.join(root, QUELLE, '*', 'SKILL.md'))):
        name = os.path.basename(os.path.dirname(q))
        k = KOPF.match(_lesen(q))
        if not k:
            continue   # kaputter Kopf: meldet der Selbsttest
        quelle = '%s/%s/SKILL.md' % (QUELLE, name)
        out['%s/%s/SKILL.md' % (ZIEL, name)] = '%s\n%s\n\nLies `%s` ganz und arbeite danach.\n' % (
            k.group(0).rstrip('\n'), HINWEIS % quelle, quelle)
    return out


def abweichungen(root=ROOT):
    """[(relativer Pfad, 'fehlt' | 'weicht ab' | 'überzählig')]."""
    s = soll(root)
    out = []
    for rel, text in sorted(s.items()):
        p = os.path.join(root, rel)
        if not os.path.isfile(p):
            out.append((rel, 'fehlt'))
        elif _lesen(p) != text:
            out.append((rel, 'weicht ab'))
    for p in sorted(glob.glob(os.path.join(root, ZIEL, '*', '*'))):
        rel = os.path.relpath(p, root).replace(os.sep, '/')
        if os.path.isfile(p) and rel not in s:
            out.append((rel, 'überzählig'))
    return out


def schreiben(root=ROOT):
    """Fehlende und abweichende Dateien schreiben, überzählige löschen. Rückgabe: Liste der Änderungen (Pfad)."""
    s = soll(root)
    geaendert = []
    for rel, zustand in abweichungen(root):
        p = os.path.join(root, rel)
        if zustand == 'überzählig':
            os.remove(p)
            try:
                os.rmdir(os.path.dirname(p))   # leeren Skill-Ordner entfernen
            except OSError:
                pass
        else:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'wb') as f:
                f.write(s[rel].encode('utf-8'))
        geaendert.append(rel)
    return geaendert
