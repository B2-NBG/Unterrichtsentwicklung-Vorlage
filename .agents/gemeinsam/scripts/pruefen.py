"""
pruefen.py - prüft geänderte Dateien, bevor sie zu den Kolleg/innen und den Schülerinnen und Schülern kommen.
Ersetzt den früheren Git-Hook pre-commit. Läuft an zwei Stellen mit denselben Regeln:
  python .agents/gemeinsam/scripts/pruefen.py [--erneuern] [--intern]
      Die KI vor dem Commit: Arbeitsstand gegen den letzten Commit (geänderte und neue Dateien).
  python .agents/gemeinsam/scripts/pruefen.py --seit <Commit> [--erneuern] [--zurueckhalten <Datei>]
      GitHub vor dem Zustellen (Workflow "Bauen und zustellen"): alles, was sich seit <Commit> bis HEAD geändert hat.
      --zurueckhalten: Fehler im Abteilungs- und Notizschutz halten nur den betroffenen Bereich an. Die Ordner
      (Themen- bzw. Test-Ordner, mit / am Ende) und Dateien stehen dann zeilenweise in <Datei>, paket-zustellen.py
      lässt sie aus (--ohne), der Workflow macht den Lauf danach rot. Alle anderen Fehler halten weiter alles an.
  python .agents/gemeinsam/scripts/pruefen.py --rechte
      Nur Auskunft am Rechner: Werkzeug-Verantwortliche ja/nein, eigene Teams, eigener Name (für die KI und Skills,
      statt git config selbst zu lesen). Prüft nichts.
  python .agents/gemeinsam/scripts/pruefen.py --von-hand
      GitHub, Lauf von Hand (Run workflow): Fehler, wenn ihn nicht Werkzeug-Verantwortliche gestartet haben.
  --erneuern  Handbuch (automatische Teile) und die Vorschau.html geänderter Test-XML neu schreiben. Committet nichts:
              Vor dem Commit nimmt die KI die Dateien mit, auf GitHub committet der Workflow sie.
  --intern    rein interne Änderung ohne Bedeutung fürs Kollegium: Mitdokumentieren wird nicht verlangt
              (auf GitHub: "[intern]" in der Commit-Nachricht).
Geprüft wird:
  1. Ablage, Steckbrief, Kursplan; ein geändertes Lernpaket hat eine neue Version; in Git liegen keine Lernpakete und
     keine Kurssicherungen (kette-pruefen.py, pruefe_dateien).
  2. Jede geänderte Test-XML ist lesbares Moodle-XML (sonst scheitert auch der Import in die ByCS).
  3. Das Handbuch: Fragen, Links, ids, Format der Neuigkeiten, Kurztext je Skill (handbuch.py).
  4. Mitdokumentieren: Ändern sich Regeln oder Werkzeuge (Muster PFLICHT in handbuch.py), muss auch die Dokumentation
     dabei sein (neuigkeiten.txt, Handbuch, fragen.txt, skills.txt). Vor dem Commit ist das ein Fehler, auf GitHub nur eine
     Warnung (und nur für Commits einer KI, erkennbar an der Zeile "Co-Authored-By", KI_COMMIT).
  5.-7. Werkzeug-, Abteilungs- und Notizschutz: schutz.py (geschuetzt, rechte, von_hand). Was erlaubt ist, steht in
     .agents/gemeinsam/regeln/schutz.md und schutz-admin.md.
  7b. Größe (dateigroessen): neue oder geänderte Datei über 5 MB, .h5p, .zip und .mbz außerhalb von Test-Ordnern und der
     Test-Vorlage (Skill moodle-test) sind Fehler.
  8. Selbsttest des Werkzeugs (selbsttest), nur wenn sich AGENTS.md, CLAUDE.md oder etwas in .agents/, .claude/ oder .gemini/ geändert hat: Kopf jedes
     Skills und Helfers (name, description), Verweise auf Dateien in .agents/ und auf Regeldateien, Vorlagen
     unverändert (VORLAGEN_HASH; gewollte Änderung bestätigt --vorlage-bestaetigen).
Rückgabe 1 bei einem Fehler. Die letzte Zeile sagt, ob ein Lernpaket betroffen ist: Dann fragt die KI vor dem Push
(nach dem Push ist die Änderung sofort bei den Schülerinnen und Schülern).
Nur Python-Standardbibliothek (Windows, Mac, GitHub).
"""
import argparse
import glob
import hashlib
import importlib.util
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
QUIZ = os.path.join(ROOT, '.agents', 'skills', 'moodle-fragenersteller', 'scripts', 'quiz-vorschau.py')
HANDBUCH = os.path.join(ROOT, '.agents', 'handbuch', 'handbuch.py')
AUF_GITHUB = os.environ.get('GITHUB_ACTIONS') == 'true'
# Selbsttest: Hash der <style>- und <script>-Blöcke je Vorlage ("Datei | Hash")
VORLAGEN_HASH = '.agents/gemeinsam/data/vorlagen-hash.txt'
VORLAGEN = '.agents/gemeinsam/templates/*.html'
BUDGET_ANWEISUNG, BUDGET_REGELDATEI, BUDGET_BESCHREIBUNG = 55, 80, 300   # Zeilen AGENTS.md, Zeilen je Regeldatei, Zeichen je Skill-Beschreibung
SEITENREGELN = ('ablage.md', 'dialog.md', 'seite.md', 'sprache.md', 'abschluss.md')   # die Regeln für eine Seite: zusammen höchstens
BUDGET_SEITENREGELN = 260
KI_COMMIT = re.compile(r'(?im)^Co-Authored-By:.*\b(ki|claude|copilot|codex|gemini)\b')   # Commit mit Beteiligung einer KI
VERWEIS = re.compile(r'`(?:python3? )?(\.(?:agents|claude|gemini)/[^`\s<>*…{}$]+|[a-z][a-z-]*\.md)[`\s]')


def _modul(name, pfad):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod



# Schutz (schutz.py): Alle Namen bleiben auch hier erreichbar (pruefen.geschuetzt, pruefen.Regeln, pruefen.git …),
# für main() und für Skripte und Tests, die pruefen.py laden.
schutz = _modul('schutz', os.path.join(HERE, 'schutz.py'))
globals().update({k: v for k, v in vars(schutz).items() if not k.startswith('__') and k not in globals()
                  and not isinstance(v, type(sys))})
git, geaenderte_dateien, geschuetzt = schutz.git, schutz.geaenderte_dateien, schutz.geschuetzt   # die hier gebrauchten
rechte_zeigen, von_hand, vorlagen_team = schutz.rechte_zeigen, schutz.von_hand, schutz.vorlagen_team


def doku_fehlt(hb, dateien, seit=None, intern=False):
    """Geänderte Regel- oder Werkzeugdateien ohne Dokumentation. Rückgabe: Liste der Dateien (leer = in Ordnung)."""
    if intern:
        return []
    if not seit:
        pflicht = [p for p in dateien if hb.PFLICHT.match(p)]
        return pflicht if pflicht and not any(p in hb.DOKU for p in dateien) else []
    # GitHub: nur Commits einer KI zählen (Co-Authored-By), "[intern]" in der Nachricht nimmt einen Commit aus
    code, log = git('log', '--format=%H%x00%B%x01', '%s..HEAD' % seit)
    if code != 0:
        return []
    pflicht = []
    for eintrag in log.split('\x01'):
        if '\x00' not in eintrag:
            continue
        h, text = eintrag.strip().split('\x00', 1)
        if not KI_COMMIT.search(text) or '[intern]' in text:
            continue
        _, d = git('diff-tree', '--no-commit-id', '--name-only', '-r', '-z', h)
        pflicht += [p for p in d if hb.PFLICHT.match(p)]
    return sorted(set(pflicht)) if pflicht and not any(p in hb.DOKU for p in dateien) else []


def _text(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as f:
        return f.read()


def _rel(muster):
    return sorted(os.path.relpath(p, ROOT).replace(os.sep, '/') for p in glob.glob(os.path.join(ROOT, muster), recursive=True))


def vorlagen_hash():
    """{Vorlage: Hash der <style>- und <script>-Blöcke} (Zeilenenden egal)."""
    return {p: hashlib.sha256('\n'.join(m.group(0) for m in re.finditer(
        r'(?s)<(style|script)\b.*?</\1>', _text(p))).encode('utf-8')).hexdigest() for p in _rel(VORLAGEN)}


def vorlagen_bestaetigen():
    with open(os.path.join(ROOT, VORLAGEN_HASH), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join('%s | %s\n' % z for z in sorted(vorlagen_hash().items())))
    print('Vorlagen bestätigt: %s (mit committen).' % VORLAGEN_HASH)
    return 0


RX_SCHUELER = re.compile(r'(?<!Schülerinnen und )(?<!Schülerin oder )(?<!Schülerinnen oder )(?<![\w"„»‚*])Schüler(?:/innen|n|s)?\b(?![a-zäöüß*-])')
RX_PRODUKT = re.compile(r'(?<![./\w])Claude\b')   # der Produktname, nicht der Dateiname CLAUDE.md oder der Ordner .claude/
RX_KLARTEXT = re.compile(r"""(?i)(?:passwor[dt]|kennwort)\w*["']?\s*[:=]\s*["'][^"'\s]{3,}["']""")
RX_LOESUNG_HASH = re.compile(r'<meta name="loesung-hash" content="([^"]*)"')


def textregeln(dateien):
    """Regeln, die ein Skript prüft (statt Prosa): in geänderten Seiten und Regeln immer "Schülerinnen und Schüler"
    (nie "Schüler" allein, nie "Schüler/innen"; "Schüler*innen" nur als Zitat aus dem Leitbild) und in Seiten kein
    Passwort im Klartext (nur der Hash in <meta name="loesung-hash">)."""
    fehler = []
    for p in sorted(dateien):
        seite = p.endswith('.html') and (p.startswith('Unterricht/') or p.startswith('Vorlagen/'))
        regel = p == 'AGENTS.md' or (p.startswith(('.agents/', '.claude/')) and p.endswith('.md'))
        if not (seite or regel) or not os.path.isfile(os.path.join(ROOT, p)):
            continue
        t = _text(p)
        if p == 'AGENTS.md' or (p.startswith('.agents/') and p.endswith('.md')):   # Rückfallschutz: Das Werkzeug ist KI-neutral
            for m in list(RX_PRODUKT.finditer(t))[:3]:
                fehler.append('%s: "%s" heißt hier "die KI" (die Regeln gelten für jede KI; Dateinamen wie CLAUDE.md oder .claude/ '
                              'sind erlaubt). Stelle: …%s…' % (p, m.group(0), t[max(0, m.start() - 25):m.end() + 15].replace('\n', ' ')))
        for m in list(RX_SCHUELER.finditer(t))[:3]:
            fehler.append('%s: "%s" – immer "Schülerinnen und Schüler" (richtig gebeugt), nie "Schüler" allein und nie '
                          '"Schüler/innen" (Stelle: …%s…).' % (p, m.group(0), t[max(0, m.start() - 25):m.end() + 15].replace('\n', ' ')))
        if seite:
            ohne = re.sub(r'(?s)<!--.*?-->', '', t)
            for h in RX_LOESUNG_HASH.findall(ohne):
                if h and not re.fullmatch(r'[0-9a-f]{64}', h):
                    fehler.append('%s: <meta name="loesung-hash"> enthält keinen SHA-256-Hash (nie ein Passwort im Klartext).' % p)
            if RX_KLARTEXT.search(ohne):
                fehler.append('%s: sieht nach einem Passwort im Klartext aus (nur der Hash aus solution-password.txt gehört in eine Seite).' % p)
    return fehler


GROESSE_MAX = 5 * 1024 * 1024   # größer gehört in den Teamordner, nicht in Git
MBZ_ERLAUBT = re.compile(r'^(\.agents/skills/moodle-test/templates/|Unterricht/.+/Test-[^/]+/)[^/]+\.mbz$')


def dateigroessen(dateien):
    """Repo klein halten: Eine neue oder geänderte Datei über 5 MB ist ein Fehler; .h5p und .zip gehören nie in Git,
    .mbz nur als Test-Aktivität (Test-Ordner) oder als Vorlage des Skills moodle-test."""
    fehler = []
    for p in sorted(dateien):
        voll = os.path.join(ROOT, p)
        if not os.path.isfile(voll):
            continue
        endung = os.path.splitext(p)[1].lower()
        if endung in ('.h5p', '.zip') or (endung == '.mbz' and not MBZ_ERLAUBT.match(p)):
            fehler.append('%s: %s-Dateien gehören nicht in Git (nur die Quelle, Lernpakete und Kurse baut GitHub; '
                          'Test-Sicherungen nur im Test-Ordner). Große Dateien in den Teamordner.' % (p, endung))
        elif os.path.getsize(voll) > GROESSE_MAX:
            fehler.append('%s: %.1f MB, über %d MB. Das Repo bleibt klein: Die Datei gehört in den Teamordner '
                          '(Fotos vorher verkleinern, lange Kante 2000 Pixel genügt).' % (p, os.path.getsize(voll) / 1048576, GROESSE_MAX // 1048576))
    return fehler


def selbsttest():
    """Fehler im Werkzeug selbst: Kopf der Skills und Helfer, tote Verweise, geänderte Vorlagen."""
    fehler = []
    skills, helfer = _rel('.agents/skills/*/SKILL.md'), _rel('.agents/helfer/*.md')
    for p in skills + helfer:
        k = re.match(r'---\n(.*?)\n---\n', _text(p), re.S)
        feld = dict(re.findall(r'(?m)^(name|description):[ \t]*(.*)$', k.group(1))) if k else {}
        soll = p.split('/')[-2] if p in skills else p.split('/')[-1][:-3]
        if feld.get('name') != soll:
            fehler.append('%s: Im Kopf muss "name: %s" stehen (wie der %s).' % (p, soll, 'Ordner' if p in skills else 'Dateiname'))
        if not feld.get('description') or ': ' in feld['description']:
            fehler.append('%s: Im Kopf fehlt "description:" oder sie enthält einen Doppelpunkt mit Leerzeichen '
                          '(dann wird der Kopf nicht gelesen).' % p)
    try:   # erzeugte Anbindung (Verweise in .claude/skills/, .gemini/settings.json) gleicht der Quelle
        for rel, zustand in _modul('anbindung', os.path.join(HERE, 'anbindung.py')).abweichungen(ROOT):
            fehler.append('Anbindung %s %s: python .agents/gemeinsam/scripts/pruefen.py --erneuern ausführen.' % (rel, zustand))
    except Exception as e:
        fehler.append('Anbindung nicht prüfbar: %s' % e)
    try:   # Schulprofil (schule.txt): Pflichtangaben, Auswahlwerte, Zahlen, Klassenmuster, Niveaus
        profil = _modul('profil', os.path.join(HERE, 'profil.py'))
        fehler += profil.pruefen()
        # Übergang bis zur Vorlagen-Hauptversion: Seite (kern/), scorm-api.js und Manifest rechnen noch fest mit
        # 40/40/20 und 70 %. Eine andere Bewertung im Profil gälte sonst nur im Kurs, nicht im Lernpaket.
        niveaus = [(n[0], n[2]) for n in profil.liste('Niveau') if len(n) > 2]
        if niveaus != [('Einsteigerniveau', '40'), ('Prüfungsniveau', '40'), ('Profiniveau', '20')] or profil.wert('Bestehensgrenze', '') != '70':
            fehler.append('schule.txt: Niveaus und Bestehensgrenze lassen sich noch nicht ändern (Vorlagen und Lernpakete '
                          'rechnen fest mit 40/40/20 und 70 %, das kommt mit der Vorlagen-Hauptversion). Bitte zurücksetzen.')
    except Exception as e:
        fehler.append('Schulprofil nicht prüfbar: %s' % e)
    namen = {q.rsplit('/', 1)[-1] for q in _rel('.agents/**/*.md')}   # Regeln liegen auch in den Skill-Ordnern
    for p in ['AGENTS.md'] + skills + helfer + _rel('.agents/gemeinsam/regeln/**/*.md'):
        for v in sorted(set(VERWEIS.findall(_text(p) + ' '))):
            ziel = v.rstrip('.,;:)')
            if not (os.path.exists(os.path.join(ROOT, ziel)) if '/' in v else v in namen):
                fehler.append('%s: Der Verweis `%s` führt ins Leere (die Datei gibt es nicht).' % (p, v))
    soll = {}
    if os.path.isfile(os.path.join(ROOT, VORLAGEN_HASH)):
        soll = dict(z.split(' | ') for z in _text(VORLAGEN_HASH).splitlines() if ' | ' in z)
    ist = vorlagen_hash()
    anders = sorted(p for p in set(ist) | set(soll) if ist.get(p) != soll.get(p))
    if anders:
        fehler.append('Vorlage geändert (<style> oder <script>): %s. War das gewollt, mit "python .agents/gemeinsam/scripts/'
                      'pruefen.py --vorlage-bestaetigen" bestätigen und %s mit committen, sonst die Änderung zurücknehmen.'
                      % (', '.join(anders), VORLAGEN_HASH))
    try:   # Die Kern-Dateien (kern/) stammen aus den Vorlagen: Weichen sie ab, laden die Seiten veralteten Stil oder Script
        sync = _modul('sync_vorlage', os.path.join(HERE, 'sync-vorlage.py'))
        allg = sync.lesen(sync.ALLG)[0]
        for p, zustand in sync.kern_abweichungen(sync.lesen(sync.FACH)[0], allg):
            fehler.append('Kern-Datei %s %s: python .agents/gemeinsam/scripts/sync-vorlage.py --vorlagen ausführen.'
                          % (os.path.relpath(p, ROOT).replace(os.sep, '/'), zustand))
        if sync.erscheinungsbild_einsetzen(allg) != allg:   # Hausfarben und Logo der Vorlage = Schulprofil
            fehler.append('Allgemeinbildung.html: Hausfarben oder Logo passen nicht zum Schulprofil (schule.txt): '
                          'python .agents/gemeinsam/scripts/sync-vorlage.py --vorlagen ausführen.')
    except Exception as e:
        fehler.append('Kern-Dateien nicht prüfbar: %s' % e)
    # Zeilenbudget: Was in jeder Sitzung im Kontext steht, bleibt klein (Regeln straffen, Plan Phase 4)
    def zeilen(rel):
        return len(_text(rel).splitlines())
    if zeilen('AGENTS.md') > BUDGET_ANWEISUNG:
        fehler.append('AGENTS.md hat %d Zeilen (höchstens %d): Was nicht in jeder Sitzung gelten muss, gehört in eine Regeldatei.'
                      % (zeilen('AGENTS.md'), BUDGET_ANWEISUNG))
    for p in _rel('.agents/gemeinsam/regeln/*.md'):
        if not p.endswith('-admin.md') and zeilen(p) > BUDGET_REGELDATEI:
            fehler.append('%s hat %d Zeilen (höchstens %d): kürzen oder Nachschlagewerk in eine Datei *-admin.md auslagern.'
                          % (p, zeilen(p), BUDGET_REGELDATEI))
    summe = sum(zeilen('.agents/gemeinsam/regeln/' + n) for n in SEITENREGELN if os.path.isfile(os.path.join(ROOT, '.agents/gemeinsam/regeln', n)))
    if summe > BUDGET_SEITENREGELN:
        fehler.append('Die Regeln für eine Seite (%s) haben zusammen %d Zeilen (höchstens %d): kürzen oder Nachschlagewerk auslagern.'
                      % (', '.join(SEITENREGELN), summe, BUDGET_SEITENREGELN))
    for p in skills:
        k = re.match(r'---\n(.*?)\n---\n', _text(p), re.S)
        d = re.search(r'(?m)^description:[ \t]*(.*)$', k.group(1)) if k else None
        if d and len(d.group(1)) > BUDGET_BESCHREIBUNG:
            fehler.append('%s: "description" hat %d Zeichen (höchstens %d, sie steht in jeder Sitzung im Kontext).'
                          % (p, len(d.group(1)), BUDGET_BESCHREIBUNG))
    return ['Selbsttest: ' + t for t in fehler]


def main(argv=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # profil.py liegt daneben, egal wer main() aufruft
    import profil
    profil.utf8_ausgabe()
    ap = argparse.ArgumentParser(description='Geänderte Dateien prüfen (vor dem Commit und auf GitHub).')
    ap.add_argument('--seit', help='alle Änderungen seit diesem Commit bis HEAD (GitHub)')
    ap.add_argument('--erneuern', action='store_true', help='Handbuch und Vorschau.html neu schreiben')
    ap.add_argument('--intern', action='store_true', help='Mitdokumentieren nicht verlangen')
    ap.add_argument('--rechte', action='store_true', help='nur zeigen: Werkzeug-Verantwortliche?, eigene Teams, Name')
    ap.add_argument('--von-hand', action='store_true', help='GitHub: Lauf von Hand nur für Werkzeug-Verantwortliche')
    ap.add_argument('--zurueckhalten', metavar='DATEI', help='GitHub: Abteilungs- und Notizschutz halten nur ihren Bereich '
                    'an, die Pfade kommen in DATEI (für paket-zustellen.py --ohne)')
    ap.add_argument('--vorlage-bestaetigen', action='store_true', help='gewollte Änderung an einer Vorlage bestätigen')
    a = ap.parse_args(argv)
    if a.vorlage_bestaetigen:
        return vorlagen_bestaetigen()
    if a.rechte:
        rechte_zeigen()
        return 0
    if a.von_hand:
        return von_hand()

    dateien = geaenderte_dateien(a.seit)
    if dateien is None:
        print('FEHLER: Den Commit %s kennt Git hier nicht.' % a.seit)
        return 1
    kette = _modul('kette_pruefen', os.path.join(HERE, 'kette-pruefen.py'))
    quiz = _modul('quiz_vorschau', QUIZ)
    hb = _modul('handbuch', HANDBUCH)
    fehler, warnungen = [], []

    # 1. Ablage, Steckbrief, Kursplan, Version, nichts Gebautes in Git
    f, pakete = kette.pruefe_dateien(dateien, alt=a.seit or 'HEAD', neu='HEAD' if a.seit else None)
    fehler += f
    vorlagen = [p for p in dateien if vorlagen_team(p) and p.lower().endswith('.html') and os.path.isfile(os.path.join(ROOT, p))]
    if vorlagen:   # Vorlagen der Teams: Kernblöcke aktuell, eigene Blöcke markiert, Grundregeln der freien Vorlagen
        vp = _modul('vorlage_pruefen', os.path.join(HERE, 'vorlage-pruefen.py'))
        for p in vorlagen:
            fehler += ['%s: %s' % (p, t) for t in vp.pruefe(os.path.join(ROOT, p))[0]]

    # 2. Test-XML lesbar, Vorschau erneuern
    xml = [p for p in dateien if quiz.ist_quiz(p) and os.path.isfile(os.path.join(ROOT, p))]
    if quiz.VORLAGE_REL in dateien:   # neue Vorlage: alle Vorschauen
        xml = sorted(set(xml) | {q.relative_to(quiz.REPO).as_posix() for q in quiz.alle_quizze()})
    neu_geschrieben = []
    for p in xml:
        try:
            if a.erneuern:
                ziel = quiz.schreiben(quiz.REPO / p)
                neu_geschrieben.append(ziel.relative_to(quiz.REPO).as_posix())
            else:
                quiz.bauen(quiz.REPO / p)
        except quiz.QuizFehler as e:
            fehler.append(str(e))

    if a.erneuern and not AUF_GITHUB:   # Anbindung (Verweise auf die Skills) nur am Rechner neu schreiben: Der Workflow
        # committet nur Handbuch und Vorschau, auf GitHub muss eine veraltete Anbindung deshalb ein Fehler bleiben (Selbsttest)
        neu_geschrieben += _modul('anbindung', os.path.join(HERE, 'anbindung.py')).schreiben()

    # 3. Handbuch
    s = hb.lesen(hb.DATEI)
    neu, fehlen = hb.erneuern(s)
    fehler += ['%s: %s' % (hb.DATEI, t) for t in hb.pruefen(neu)]
    fehler += ['Skill %s hat keinen Kurztext in %s.' % (n, hb.SKILLS) for n in fehlen]
    if neu != s:
        if a.erneuern:
            hb.schreiben(hb.DATEI, neu)
            neu_geschrieben.append(hb.DATEI)
        elif not a.seit:
            warnungen.append('%s: Automatische Teile sind veraltet (mit --erneuern neu schreiben).' % hb.DATEI)

    # 4. Mitdokumentieren
    ohne = doku_fehlt(hb, dateien, a.seit, a.intern)
    if ohne:
        text = ('Regeln oder Werkzeuge geändert, aber nicht dokumentiert: %s. In %s oben eine Zeile eintragen '
                '(TT.MM.JJJJ | was sich für Kolleg/innen ändert, ein Satz ohne Technik), bei geänderter Bedienung auch das Handbuch. '
                'Nur intern: --intern bzw. "[intern]" in der Commit-Nachricht.' % (', '.join(ohne), hb.NEU))
        (warnungen if a.seit else fehler).append(text)

    # 5. bis 7. Werkzeugschutz, Abteilungsschutz, Notizschutz
    f, w, zurueck = geschuetzt(hb, a.seit, bool(a.zurueckhalten and a.seit))
    fehler += f
    warnungen += w
    if a.zurueckhalten:   # immer schreiben (auch leer): Der Workflow liest die Datei nach dem Zustellen
        with open(a.zurueckhalten, 'w', encoding='utf-8', newline='\n') as datei:
            datei.write(''.join(p + '\n' for p in sorted(zurueck)))

    fehler += textregeln(dateien)
    fehler += dateigroessen(dateien)

    # 8. Selbsttest des Werkzeugs
    if any(p in ('AGENTS.md', 'CLAUDE.md') or p.startswith(('.agents/', '.claude/', '.gemini/')) for p in dateien):
        fehler += selbsttest()

    for t in warnungen:
        if t.startswith('ZURUECK:'):   # zurückgehalten: als Fehler zeigen, hält aber nur den Bereich an
            print(('::error::' if AUF_GITHUB else 'FEHLER: ') + t[len('ZURUECK:'):])
            continue
        print(('::warning::' if AUF_GITHUB else 'WARNUNG: ') + t)
    for t in fehler:
        print(('::error::' if AUF_GITHUB else 'FEHLER: ') + t)
    for p in neu_geschrieben:
        print('Erneuert: %s' % p)
    print('Prüfung: %s (%d geänderte Dateien).' % ('%d Fehler' % len(fehler) if fehler else 'bestanden' + (
        ', zurückgehalten: %s' % ', '.join(sorted(zurueck)) if zurueck else ''), len(dateien)))
    kern = any(kette.bauen.ist_kern_datei(p) for p in dateien)
    print('Lernpaket betroffen: %s' % (('ja (%s%s)' % (', '.join(p.rsplit('/', 1)[-1] for p in pakete),
                                                       '; alle Seiten mit diesem Kern' if kern else '')) if pakete else 'nein'))
    return 1 if fehler else 0


if __name__ == '__main__':
    sys.exit(main())
