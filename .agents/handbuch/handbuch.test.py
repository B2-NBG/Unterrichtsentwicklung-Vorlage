"""
handbuch.test.py - prüft das automatische Mitdokumentieren und die Prüfung vor dem Commit und auf GitHub
(handbuch.py, .agents/gemeinsam/scripts/pruefen.py). Git-Hooks gibt es nicht mehr.
Aufruf im Projektordner (am Mac python3 statt python):
  python .agents/handbuch/handbuch.test.py
Ablauf: ein Wegwerf-Klon des Repos mit dem aktuellen Arbeitsstand (auch noch nicht committete Änderungen).
Das Repo und der Teamordner werden nicht berührt. Rückgabe: 0 = alles bestanden.
"""
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HIER))
DATEI = '#Handbuch.html'
NEU = '.agents/handbuch/neuigkeiten.txt'
FRAGEN = '.agents/handbuch/fragen.txt'
PRUEFEN = '.agents/gemeinsam/scripts/pruefen.py'
SCHUTZ_GITHUB = '.agents/gemeinsam/scripts/schutz-github.py'
CLAUDE = '\n\nCo-Authored-By: Claude Test <noreply@anthropic.com>'
ergebnisse = []


def pruefe(ok, text, mehr=''):
    ergebnisse.append(bool(ok))
    print('   %s %s%s' % ('ok   ' if ok else 'FEHLT', text, '' if ok else '  -> ' + str(mehr)[-500:]))


def arbeitsstand(ziel):
    """Überträgt geänderte, neue und gelöschte Dateien des Arbeitsstands in den Klon."""
    r = subprocess.run(['git', '-c', 'core.quotePath=false', 'status', '--porcelain', '-z', '--untracked-files=all'],
                       cwd=ROOT, stdout=subprocess.PIPE)
    eintraege = r.stdout.decode('utf-8').split('\0')
    i = 0
    while i < len(eintraege):
        e = eintraege[i]
        i += 1
        if len(e) < 4:
            continue
        art, pfad = e[:2], e[3:]
        if 'R' in art:   # umbenannt: der alte Name folgt als eigener Eintrag
            alt = eintraege[i]
            i += 1
            if os.path.exists(os.path.join(ziel, alt)):
                if pfad.endswith('solution-password.txt'):   # nicht kopieren, aber mit umziehen (Fassung des Klons)
                    os.makedirs(os.path.dirname(os.path.join(ziel, pfad)), exist_ok=True)
                    os.replace(os.path.join(ziel, alt), os.path.join(ziel, pfad))
                    continue
                os.remove(os.path.join(ziel, alt))
                try:   # leere alte Ordner entfernen (Windows: sonst bleibt ihre alte Schreibweise stehen)
                    os.removedirs(os.path.dirname(os.path.join(ziel, alt)))
                except OSError:
                    pass
        q, z = os.path.join(ROOT, pfad), os.path.join(ziel, pfad)
        if 'D' in art or not os.path.exists(q):
            if os.path.isfile(z):
                os.remove(z)
            continue
        if pfad.endswith('solution-password.txt') or '__pycache__' in pfad or os.path.isdir(q):
            continue
        os.makedirs(os.path.dirname(z), exist_ok=True)
        shutil.copy2(q, z)


def main():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass
    tmp = tempfile.mkdtemp(prefix='handbuch-test-')
    repo = os.path.join(tmp, 'repo')
    # Sauber wie am Rechner, auch im Workflow "Werkzeug testen": keine Angaben des echten Laufs (GITHUB_ACTOR,
    # GITHUB_REPOSITORY_OWNER, Zugänge …), die Tests setzen selbst, was sie brauchen.
    env = {k: v for k, v in os.environ.items()
           if k not in ('CLAUDECODE', 'CI', 'TEAM_TOKEN', 'SCHUTZ_TOKEN')
           and not k.startswith(('GIT_', 'GITHUB_', 'RUNNER_', 'ACTIONS_'))}
    env['UNTERRICHT_ICH'] = '-'   # nie die echte Git-Anmeldung fragen (meine_teams in pruefen.py): "GitHub nicht erreichbar"

    def git(*args):
        r = subprocess.run(['git', '-c', 'core.safecrlf=false'] + list(args), cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return r.returncode, r.stdout.decode('utf-8', 'replace')

    def lies(rel):
        with open(os.path.join(repo, rel), encoding='utf-8', newline='') as f:
            return f.read()

    def schreibe(rel, text, anhaengen=False):
        p = os.path.join(repo, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'a' if anhaengen else 'w', encoding='utf-8', newline='') as f:
            f.write(text)

    def commit(text):
        git('add', '-A')
        return git('commit', '-q', '-m', text)

    def pruefen(*args):
        r = subprocess.run([sys.executable, PRUEFEN] + list(args), cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return r.returncode, r.stdout.decode('utf-8', 'replace')

    def kopf():
        return git('rev-parse', 'HEAD')[1].strip()

    def aendere_skill(n):
        schreibe('.agents/skills/baue-arbeitsblatt/SKILL.md', '\n<!-- Test %d -->\n' % n, True)

    try:
        subprocess.run(['git', 'clone', '-q', '--no-hardlinks', ROOT, repo], env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        git('config', 'user.name', 'Test')
        git('config', 'user.email', 'test@example.org')
        git('config', 'unterricht.werkzeug', 'ja')   # der Test ändert Werkzeug: wie am Rechner von Werkzeug-Verantwortlichen
        arbeitsstand(repo)
        # Ausgangslage unabhängig von der Schule: Schutz mit Teams und Testteams in schutz.txt (die öffentliche Fassung
        # kommt für eine Lehrkraft allein, ohne Teams). In einem Repo, das das schon hat, ändert sich nichts.
        p_profil, p_schutz = '.agents/gemeinsam/data/schule.txt', '.agents/gemeinsam/data/schutz.txt'
        t = re.sub(r'(?m)^Schutz \|[^\r\n]*', 'Schutz | teams', lies(p_profil))
        if not re.search(r'(?m)^Team-Werkzeug \|', t):
            t += 'Team-Werkzeug | werkzeug-verantwortliche\n'
        if t != lies(p_profil):
            schreibe(p_profil, t)
            subprocess.run([sys.executable, '-c', 'import sys; sys.dont_write_bytecode = True; '
                            'sys.path.insert(0, ".agents/gemeinsam/scripts"); import anbindung; anbindung.schreiben()'],
                           cwd=repo, env=env, check=True)
        if not re.search(r'(?m)^(Klasse|Fach) \|', lies(p_schutz)):
            schreibe(p_schutz, lies(p_schutz) + '\nKlasse | MGF10 | grundstufe\nFach | Eth | ethik\nFach | PuG | pug\n')
        code, aus = commit('Arbeitsstand [intern]')
        pruefe(code == 0 or 'nothing to commit' in aus, 'Ausgangsstand committet', aus)
        code, aus = pruefen('--erneuern', '--intern')
        commit('Handbuch erneuert [intern]')
        pruefe(code == 0, 'Ausgangsstand besteht die Prüfung', aus)

        print('Rulesets auf GitHub aus schutz.txt (schutz-github.py)')
        import importlib.util
        import json
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('schutz_github', os.path.join(repo, SCHUTZ_GITHUB))
        sg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(sg)

        def wirft(m):
            try:
                sg.muster(m)
            except sg.Fehler:
                return True
            return False

        pruefe(sg.muster('.claude/') == '.claude/**/*' and sg.muster('.agents/') == '.agents/**/*' and sg.muster('AGENTS.md') == 'AGENTS.md'
               and sg.muster('Unterricht/*/Vorschau.html') == 'Unterricht/**/Vorschau.html' and sg.muster('a/*') == 'a/**/*',
               'Muster: Ordner, Pfad, * als Ordnername')
        pruefe(wirft('a/b*.txt') and wirft('a/[x]') and wirft('a/' + 'x' * 200),
               'Muster, das sich nicht sicher umsetzen lässt oder zu lang ist: Abbruch')
        regeln = sg.p.Regeln('Werkzeug | AGENTS.md\nWerkzeug | CLAUDE.md\nWerkzeug | .agents/\nWerkzeug | .claude/\nWerkzeug | .gemini/\nWerkzeug | #Handbuch.html\n'
                             'Frei | .agents/handbuch/fragen.txt\nFrei | Unterricht/Offen/\nFrei | Unterricht/*/Vorschau.html\n'
                             'Klasse | MGF10 | grundstufe\nKlasse | BFS10 | grundstufe\nFach | Eth | ethik\nFach | PuG | pug\n'
                             'Fach | Werken | grundstufe\n')
        soll = sg.soll_rulesets(regeln)
        nach = {r['name']: r for r in soll}
        pruefe(sorted(nach) == ['Schutz: Dateigröße', 'Schutz: Werkzeug', 'Schutz: Werkzeug in Arbeitsordnern', 'Schutz: ethik',
                                'Schutz: grundstufe', 'Schutz: main', 'Schutz: pug'],
               'ein Ruleset für das Werkzeug (und eines für Werkzeug in Arbeitsordnern), eines je Team, eines für main, eines für die Dateigröße', sorted(nach))
        d = sg.fuer_github(nach['Schutz: Dateigröße'], {})
        pruefe(d['rules'] == [{'type': 'file_extension_restriction', 'parameters': {'restricted_file_extensions': ['*.h5p', '*.zip']}},
                              {'type': 'max_file_size', 'parameters': {'max_file_size': 5}}]
               and d['bypass_actors'] == [{'actor_id': 1, 'actor_type': 'OrganizationAdmin', 'bypass_mode': 'always'}],
               'Dateigröße: über 5 MB und .h5p/.zip abgewiesen, vorbei nur Owner der Organisation', d)
        pruefe('ToDo/grundstufe-NOTIZEN.md' in nach['Schutz: grundstufe']['gesperrt']
               and 'Vorlagen/grundstufe/**/*' in nach['Schutz: grundstufe']['gesperrt']
               and nach['Schutz: Werkzeug in Arbeitsordnern']['gesperrt'] == [
                   'ToDo/werkzeug-verantwortliche-NOTIZEN.md', 'Vorlagen/*', 'Vorlagen/werkzeug-verantwortliche/**/*'],
               'Notizbuch und Vorlagen je Team gesperrt, die der Werkzeug-Verantwortlichen als Werkzeug',
               nach['Schutz: Werkzeug in Arbeitsordnern']['gesperrt'])
        pruefe(all({'.agents/handbuch/fragen.txt', 'Unterricht/Offen/**/*', 'Unterricht/**/Vorschau.html'} <= set(r['ausnahmen'])
                   for r in soll if 'file_path_restriction' in r['regeln']), 'Frei-Muster sind in jedem Pfad-Ruleset ausgenommen')
        pruefe('#Handbuch.html' not in nach['Schutz: Werkzeug']['gesperrt'] and {'.agents/**/*', '.claude/**/*', '.gemini/**/*'} <= set(nach['Schutz: Werkzeug']['gesperrt']),
               'Werkzeug gesperrt, das Handbuch nicht (automatische Teile, Bot)')
        g = nach['Schutz: grundstufe']
        pruefe({'Unterricht/MGF10/Eth/**/*', 'Unterricht/BFS10/PuG/**/*'} <= set(g['ausnahmen'])
               and not any('Werken' in m for m in g['ausnahmen']) and 'Unterricht/*/Werken/**/*' in g['gesperrt'],
               'Fachbereich vor Abteilung: fremde Fächer in den eigenen Klassen ausgenommen, eigene nicht', g)
        pruefe(g['vorbei'] == ['OrganizationAdmin', 'grundstufe', 'werkzeug-verantwortliche'] and nach['Schutz: main']['vorbei'] == []
               and nach['Schutz: main']['regeln'] == ['deletion', 'non_fast_forward'],
               'vorbei dürfen das Team und die Werkzeug-Verantwortlichen, bei main niemand', g['vorbei'])

        def trifft(pfad, muster_liste):   # wie GitHub: ohne Groß/Klein, * bleibt im Ordner, **/ = beliebig viele Ordner
            for m in muster_liste:
                teile = m.split('/')
                rx = ''.join('(?:[^/]+/)*' if t == '**' else re.escape(t).replace(r'\*', '[^/]*') + ('' if i == len(teile) - 1 else '/')
                             for i, t in enumerate(teile))
                if re.fullmatch(rx, pfad, re.I):
                    return True
            return False

        def gesperrt_fuer(pfad, liste):
            # 'Werkzeug in Arbeitsordnern' (z. B. die Platzhalter .gitkeep) zählt wie 'Werkzeug'
            return sorted({'Werkzeug' if r['name'].startswith('Schutz: Werkzeug') else r['name'][len('Schutz: '):]
                           for r in liste if r['target'] == 'push'
                           and trifft(pfad, r['gesperrt']) and not trifft(pfad, r['ausnahmen'])})

        echt = sg.p.schutzregeln('HEAD')
        for name, rg in (('Testregeln', regeln), ('schutz.txt', echt)):
            liste, falsch = sg.soll_rulesets(rg), []
            for pfad in ('AGENTS.md', 'agents.md', 'CLAUDE.md', '.agents/skills/x/SKILL.md', '.claude/skills/x/SKILL.md', '.claude/a/.b/c', '.gemini/settings.json', '.agents/handbuch/fragen.txt',
                         '.agents/handbuch/neuigkeiten.txt', '.github/workflows/a.yml', '.gitignore', 'README.md',
                         'Neu-ganz-oben.txt', 'Neuer-Ordner/a/b.txt', '.vscode/settings.json', 'Ressourcen/a/b.pdf', 'ressourcen/x.pdf',
                         'ToDo/Alle-NOTIZEN.md', 'ToDo/grundstufe-NOTIZEN.md', 'todo/PuG-notizen.md', 'ToDo/Ordner/x.md',
                         'ToDo/werkzeug-verantwortliche-NOTIZEN.md', 'ToDo/grundstufe-NOTIZEN.md.txt', 'Unterricht/x.txt',
                         'Vorlagen/LIESMICH.md', 'Vorlagen/grundstufe/Probe.html', 'vorlagen/PuG/bilder/a.png',
                         'Vorlagen/werkzeug-verantwortliche/x.html', 'Unterricht/MGF10/LF1/t/index.html', 'Unterricht/MGF10/Kurs.md',
                         'Unterricht/MGF10/Eth/t/index.html', 'Unterricht/MGF10/Eth', 'Unterricht/mgf10/eth/t/x.html',
                         'Unterricht/ALLE10/PuG/t/index.html', 'Unterricht/ALLE10/LF/t/index.html', 'Unterricht/ALLE10/Eth/x',
                         'Unterricht/Offen/x/y.html', 'Unterricht/MGF10/LF1/t/Vorschau.html', 'Unterricht/BFS10/BerHan/a/b.html',
                         'Unterricht/BFS10/Werken/a/b.html', 'Unterricht/BFS11/LF2/a.html', 'Unterricht/MGF10/.gitkeep',
                         'Unterricht/MGF10/LF2/.gitkeep', 'Unterricht/MGF10/LF1/BW1/Thema/.gitkeep',
                         '.agents/gemeinsam/templates/kern/Fachunterricht.head.css', 'Vorlagen/grundstufe/kern/Name.stil.css',
                         'Unterricht/MGF10/LF1/BW1/Thema/bilder/bild-01.png', 'Unterricht/ALLE10/PuG/BW1/Thema/bilder/b.jpg'):
                wie = pfad if pfad != 'agents.md' else 'AGENTS.md'   # Regeln.ist_werkzeug unterscheidet Groß/Klein, GitHub nicht
                erwartet = (['Werkzeug'] if rg.ist_werkzeug(wie) else []) + ([rg.team(pfad)] if rg.team(pfad) else [])
                if gesperrt_fuer(pfad, liste) != sorted(erwartet):
                    falsch.append('%s: Rulesets %s, pruefen.py %s' % (pfad, gesperrt_fuer(pfad, liste), erwartet))
            pruefe(not falsch, '%s: Die Rulesets sperren dieselben Pfade für dieselben Teams wie pruefen.py' % name, falsch)

        # Kern und Bilder: Der Kern der Vorlagen ist Werkzeug, der Kern einer Team-Vorlage gehört dem Team, bilder/ dem Themenordner
        kern_falsch = []
        for pfad, werkzeug, team in (('.agents/gemeinsam/templates/kern/Fachunterricht.head.css', True, None),
                                     ('Vorlagen/grundstufe/kern/Name.stil.css', False, 'grundstufe'),
                                     ('Unterricht/MGF10/LF1/BW1/Thema/bilder/bild-01.png', False, 'grundstufe'),
                                     ('Unterricht/ALLE10/PuG/BW1/Thema/bilder/b.jpg', False, 'pug')):
            if echt.ist_werkzeug(pfad) != werkzeug or (echt.team(pfad) or None) != team:
                kern_falsch.append('%s: Werkzeug %s, Team %s' % (pfad, echt.ist_werkzeug(pfad), echt.team(pfad)))
        pruefe(not kern_falsch, 'schutz.txt: kern/ der Vorlagen ist Werkzeug, kern/ und bilder/ der Teams gehören den Teams', kern_falsch)

        nr = {t: 100 + i for i, t in enumerate(sorted({t for r in sg.soll_rulesets(echt) for t in r['vorbei'] if t != sg.ADMIN}))}
        gut = [dict(sg.fuer_github(r, nr), id=i) for i, r in enumerate(sg.soll_rulesets(echt))]
        antwort = os.path.join(tmp, 'rulesets.json')

        def schutz(rulesets, *args):
            if rulesets is None:
                if os.path.exists(antwort):
                    os.remove(antwort)
            else:
                with open(antwort, 'w', encoding='utf-8') as f:
                    json.dump({'rulesets': rulesets, 'teams': nr}, f)
            r = subprocess.run([sys.executable, SCHUTZ_GITHUB] + list(args or ['--pruefen', '--repo', 'test/test']), cwd=repo,
                               env=dict(env, UNTERRICHT_RULESETS_TEST=antwort), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            return r.returncode, r.stdout.decode('utf-8', 'replace')

        def kopie():
            return json.loads(json.dumps(gut))

        code, aus = schutz(gut)
        pruefe(code == 0 and 'passen zu schutz.txt' in aus and 'nicht geprüft' not in aus, '--pruefen: GitHub wie schutz.txt: besteht', aus)
        ohne = [{k: v for k, v in r.items() if k != 'bypass_actors'} for r in kopie()]
        code, aus = schutz(ohne)
        pruefe(code == 0 and 'nicht geprüft' in aus, '--pruefen ohne Admin-Recht (GitHub zeigt nicht, wer vorbei darf): besteht mit Hinweis', aus)
        anders = kopie()
        anders[0]['rules'][0]['parameters']['restricted_file_paths'].remove('.claude/**/*')
        code, aus = schutz(anders)
        pruefe(code == 1 and 'Schutz: Werkzeug' in aus and '.claude/**/*' in aus, '--pruefen: gesperrter Pfad fehlt: Fehler', aus)
        anders = kopie()
        groesse = next(r for r in anders if r['name'] == 'Schutz: Dateigröße')
        groesse['rules'] = [{'type': 'file_extension_restriction', 'parameters': {'restricted_file_extensions': ['*.zip']}},
                            {'type': 'max_file_size', 'parameters': {'max_file_size': 50}}]
        code, aus = schutz(anders)
        pruefe(code == 1 and 'Dateigröße' in aus and '50 MB' in aus and '.h5p' in aus,
               '--pruefen: andere Größe oder fehlende Endung bei Dateigröße: Fehler', aus)
        anders = kopie()
        anders[1]['bypass_actors'].append({'actor_id': 5, 'actor_type': 'RepositoryRole', 'bypass_mode': 'always'})
        code, aus = schutz(anders)
        pruefe(code == 1 and 'vorbei dürfen' in aus, '--pruefen: jemand darf zusätzlich vorbei: Fehler', aus)
        anders = kopie()
        for a in next(r for r in anders if r['name'] == 'Schutz: Dateigröße')['bypass_actors']:
            a['bypass_mode'] = 'pull_request'
        code, aus = schutz(anders)
        pruefe(code == 1 and 'Dateigröße' in aus and 'pull_request' in aus,
               '--pruefen: Owner nur noch bei Pull Requests vorbei: Fehler', aus)
        anders = kopie()
        anders[0]['enforcement'] = 'disabled'
        code, aus = schutz(anders)
        pruefe(code == 1 and 'nicht aktiv' in aus, '--pruefen: Ruleset abgeschaltet: Fehler', aus)
        code, aus = schutz(kopie()[1:])
        pruefe(code == 1 and 'fehlt auf GitHub' in aus, '--pruefen: Ruleset fehlt: Fehler', aus)
        code, aus = schutz(kopie() + [dict(kopie()[1], name='Schutz: gibt-es-nicht-mehr', id=99)])
        pruefe(code == 1 and 'gibt-es-nicht-mehr' in aus, '--pruefen: Ruleset zu viel: Fehler', aus)
        code, aus = schutz(kopie() + [dict(kopie()[1], name='Anderes Ruleset', id=98)])
        pruefe(code == 0, '--pruefen: Rulesets mit anderem Namen stören nicht', aus)
        code, aus = schutz(None)
        pruefe(code == 1 and 'nicht lesen' in aus, '--pruefen: GitHub lässt nicht lesen: Fehler', aus)
        code, aus = schutz(gut, '--zeigen')
        pruefe(code == 0 and '"Schutz: Werkzeug"' in aus, '--zeigen gibt die Rulesets aus', aus)

        print('Vor dem Commit: Regeln oder Werkzeuge geändert')
        aendere_skill(1)
        code, aus = pruefen('--erneuern')
        pruefe(code == 1 and 'nicht dokumentiert' in aus and 'arbeitsblatt/SKILL.md' in aus, 'ohne Dokumentation: Fehler, Datei genannt', aus)
        code, aus = pruefen('--intern')
        pruefe(code == 0, '--intern: rein interne Änderung besteht', aus)
        schreibe(NEU, '31.12.2099 | Testneuigkeit für das Kollegium.\n', True)
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and 'Testneuigkeit' in lies(DATEI), 'mit Zeile in neuigkeiten.txt: besteht, Neuigkeit steht im Handbuch', aus)
        pruefe('Lernpaket betroffen: nein' in aus, 'meldet: kein Lernpaket betroffen', aus)
        commit('Skill mit Doku' + CLAUDE)

        print('Auf GitHub (--seit): Mitdokumentieren nur als Warnung, nur für Commits von Claude')
        basis = kopf()
        aendere_skill(2)
        commit('Skill ohne Doku' + CLAUDE)
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0 and 'WARNUNG' in aus and 'nicht dokumentiert' in aus, 'Commit von Claude ohne Doku: Warnung, kein Fehler', aus)
        basis = kopf()
        aendere_skill(3)
        commit('von Hand')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0 and 'nicht dokumentiert' not in aus, 'Commit von Hand: keine Warnung', aus)
        basis = kopf()
        aendere_skill(4)
        commit('intern [intern]' + CLAUDE)
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0 and 'nicht dokumentiert' not in aus, '"[intern]" in der Nachricht: keine Warnung', aus)
        code, aus = pruefen('--seit', 'gibtesnicht')
        pruefe(code == 1 and 'kennt Git hier nicht' in aus, 'unbekannter Commit: Fehler', aus)

        print('Werkzeugschutz: Werkzeug ändern nur Werkzeug-Verantwortliche')
        # Eine Teams-Datei statt GitHub (UNTERRICHT_TEAMS_TEST in pruefen.py), für den Lauf und mit UNTERRICHT_ICH für den Rechner
        teams = os.path.join(tmp, 'teams.txt')
        with open(teams, 'w', encoding='utf-8') as f:
            f.write('werkzeug-verantwortliche: chefin\nethik: ethikerin\npug: politiker, chefin, beides\n'
                    'grundstufe: metaller, beides\n')
        env['UNTERRICHT_TEAMS_TEST'] = teams
        zurueck = os.path.join(tmp, 'zurueck.txt')   # pruefen.py --zurueckhalten schreibt hier hinein

        def zurueckgehalten():
            with open(zurueck, encoding='utf-8') as f:
                return f.read().split()

        env['GITHUB_RUN_ATTEMPT'] = '2'   # GITHUB_TRIGGERING_ACTOR steht ab hier für "hat den Lauf wiederholt"
        git('config', '--unset', 'unterricht.werkzeug')

        print('Lauf von Hand (Run workflow): nur Werkzeug-Verantwortliche')
        env['GITHUB_TRIGGERING_ACTOR'] = 'Autorin'
        code, aus = pruefen('--von-hand')
        pruefe(code == 1 and 'nur Werkzeug-Verantwortliche' in aus and 'autorin' in aus, 'von Unberechtigten gestartet: Fehler', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'chefin'
        code, aus = pruefen('--von-hand')
        pruefe(code == 0 and 'chefin' in aus, 'von Werkzeug-Verantwortlichen gestartet: besteht', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        code, aus = pruefen('--von-hand')
        pruefe(code == 1 and 'nur auf GitHub' in aus, 'ohne GitHub: Fehler', aus)

        aendere_skill(5)
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'ändern nur Werkzeug-Verantwortliche' in aus and 'arbeitsblatt/SKILL.md' in aus, 'Rechner nicht eingerichtet: geänderter Skill ist ein Fehler', aus)
        git('checkout', '--', '.agents/skills/baue-arbeitsblatt/SKILL.md')
        schreibe('.agents/gemeinsam/data/berufe.txt', 'Testberuf\n', True)
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'fortgeschriebene Listen (berufe.txt) bleiben erlaubt', aus)
        schreibe('ToDo/Notiz-Test/Material.md', 'x')
        schreibe('ToDo/Notiz-Test.txt', 'x')
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'Notizschutz' in aus and 'liegen nur Notizbücher' in aus and 'Notiz-Test/Material.md' in aus
               and 'Notiz-Test.txt' in aus, 'andere Datei oder Ordner in ToDo/ ohne Werkzeugrecht: Fehler', aus)
        shutil.rmtree(os.path.join(repo, 'ToDo', 'Notiz-Test'))
        os.remove(os.path.join(repo, 'ToDo', 'Notiz-Test.txt'))
        git('checkout', '--', '.agents/gemeinsam/data/berufe.txt')
        schreibe('Neu-ganz-oben.txt', 'x')
        schreibe('Neuer-Ordner/x.txt', 'x')
        schreibe('Ressourcen/Neu-Test/x.txt', 'x')
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'ändern nur Werkzeug-Verantwortliche' in aus and 'Neu-ganz-oben.txt' in aus
               and 'Neuer-Ordner/x.txt' in aus and 'Ressourcen/Neu-Test' not in aus,
               'Neue Datei und neuer Ordner ganz oben im Repo ohne Werkzeugrecht: Fehler, in Ressourcen/ erlaubt', aus)
        os.remove(os.path.join(repo, 'Neu-ganz-oben.txt'))
        shutil.rmtree(os.path.join(repo, 'Neuer-Ordner'))
        shutil.rmtree(os.path.join(repo, 'Ressourcen', 'Neu-Test'))
        schreibe(NEU, '31.12.2099 | Neuigkeit von Autor/innen.\n', True)
        schreibe(FRAGEN, 'Frage von Autor/innen? | einbinden\n', True)
        code, aus = pruefen('--erneuern', '--intern')
        pruefe(code == 0 and 'Neuigkeit von Autor/innen' in lies(DATEI) and 'Frage von Autor/innen?' in lies(DATEI),
               'Handbuch: Neuigkeiten, Fragen und die automatischen Teile dürfen sich bei allen ändern', aus)
        s = lies(DATEI)
        schreibe(DATEI, s.replace('</main>', '<p>Von Hand ergänzt.</p></main>'))
        code, aus = pruefen('--erneuern', '--intern')
        pruefe(code == 1 and 'ändern nur Werkzeug-Verantwortliche' in aus and DATEI in aus, 'Handbuch von Hand geändert: Fehler', aus)
        git('checkout', '--', DATEI, NEU, FRAGEN)
        basis = kopf()
        aendere_skill(6)
        commit('Skill von Unberechtigten [intern]')
        env['GITHUB_ACTOR'] = 'Autorin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'nichts zugestellt' in aus and 'autorin' in aus, 'auf GitHub: Push von Unberechtigten ist ein Fehler', aus)
        code, aus = pruefen('--seit', basis, '--zurueckhalten', zurueck)
        pruefe(code == 1 and 'nichts zugestellt' in aus and zurueckgehalten() == [],
               'Werkzeug mit --zurueckhalten: hält weiter alles an', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'Chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Werkzeug-Verantwortliche wiederholen den Lauf: besteht', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        git('revert', '--no-edit', 'HEAD')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Änderung zurückgenommen: besteht', aus)
        env['GITHUB_ACTOR'] = 'chefin'
        aendere_skill(7)
        commit('Skill von Berechtigten [intern]')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Push von Werkzeug-Verantwortlichen: besteht', aus)

        print('Schutzregeln (schutz.txt): auf GitHub in der Fassung des letzten grünen Laufs')
        basis = kopf()
        schutz = '.agents/gemeinsam/data/schutz.txt'
        schreibe(schutz, re.sub(r'Werkzeug \| \.agents/\r?\n', '', lies(schutz)))
        aendere_skill(10)
        commit('Regel gestrichen und Skill geändert [intern]')
        env['GITHUB_ACTOR'] = 'Autorin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'schutz.txt' in aus and 'arbeitsblatt/SKILL.md' in aus,
               'Werkzeug-Regel gestrichen: wirkt noch nicht, Skill und schutz.txt sind Fehler', aus)
        git('reset', '-q', '--hard', basis)
        env['GITHUB_ACTOR'] = 'chefin'

        print('Abteilungsschutz: Unterricht ändern nur das zuständige Team oder Werkzeug-Verantwortliche')
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n<quiz></quiz>\n'
        basis = kopf()
        schreibe('Unterricht/ALLE10/Eth/BW7/Test-Schutz/Fragen-Schutz.xml', xml)
        commit('Ethik von Fremden [intern]')
        env['GITHUB_ACTOR'] = 'Metaller'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'Teams "ethik"' in aus and 'nichts zugestellt' in aus and 'metaller' in aus, 'fremder Fachbereich: Fehler, Team genannt', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'Ethikerin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Mitglied des Teams wiederholt den Lauf: besteht', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Werkzeug-Verantwortliche wiederholen den Lauf: besteht', aus)
        env['GITHUB_RUN_ATTEMPT'] = '1'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'Teams "ethik"' in aus, 'erster Versuch: wer den Lauf auslöst, gibt nichts frei', aus)
        env['GITHUB_RUN_ATTEMPT'] = '2'
        del env['GITHUB_TRIGGERING_ACTOR']

        print('Jeder Push zählt für sich (UNTERRICHT_PUSHES)')
        ethik_push = kopf()
        schreibe('Ressourcen/Test-Schutz.txt', 'x')
        commit('Später etwas anderes [intern]')
        env['UNTERRICHT_PUSHES'] = '%s:metaller' % ethik_push
        env['GITHUB_ACTOR'] = 'chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'metaller (Unterricht/ALLE10/Eth' in aus and 'chefin' not in aus,
               'späterer Push von Werkzeug-Verantwortlichen gibt die fremde Änderung nicht frei', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Werkzeug-Verantwortliche wiederholen den Lauf: besteht', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        env['UNTERRICHT_PUSHES'] = '%s:ethikerin' % ethik_push
        env['GITHUB_ACTOR'] = 'metaller'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Ethik gepusht von ethikerin, danach anderes von metaller: besteht', aus)
        aendere_skill(9)
        commit('Skill von Werkzeug-Verantwortlichen [intern]')
        env['UNTERRICHT_PUSHES'] = '%s:metaller %s:chefin' % (ethik_push, kopf())
        schreibe('Ressourcen/Test-Schutz.txt', 'y')
        commit('Noch etwas anderes [intern]')
        env['GITHUB_ACTOR'] = 'politiker'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'Teams "ethik"' in aus and 'Werkzeug geändert' not in aus and 'Ressourcen' not in aus,
               'drei Pushes: nur der fremde Ethik-Push ist ein Fehler, der Skill von Werkzeug-Verantwortlichen nicht', aus)
        code, aus = pruefen('--seit', basis, '--zurueckhalten', zurueck)
        pruefe(code == 0 and zurueckgehalten() == ['Unterricht/ALLE10/Eth/BW7/Test-Schutz/'] and 'alles andere wird zugestellt' in aus
               and 'zurückgehalten: Unterricht/ALLE10/Eth/BW7/Test-Schutz/' in aus,
               'mit --zurueckhalten: nur der Ethik-Test-Ordner wird angehalten, der Rest darf zugestellt werden', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'ethikerin'
        code, aus = pruefen('--seit', basis, '--zurueckhalten', zurueck)
        pruefe(code == 0 and zurueckgehalten() == [], 'Mitglied des Teams wiederholt den Lauf: nichts mehr zurückgehalten', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        del env['UNTERRICHT_PUSHES']
        env['GITHUB_ACTOR'] = 'metaller'
        git('reset', '-q', '--hard', basis)
        schreibe('Unterricht/MGF10/LF1/BW1/Test-Schutz/Fragen-Schutz.xml', xml)
        commit('Lernfeld der eigenen Abteilung [intern]')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Lernfeld in der Klasse der eigenen Abteilung: besteht', aus)
        schreibe('Unterricht/MGF10/PuG/BW1/Test-Schutz/Fragen-Schutz.xml', xml)
        commit('PuG in der eigenen Klasse [intern]')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'Teams "pug"' in aus and 'Teams "grundstufe"' not in aus, 'Fach mit Fachbereich in der eigenen Klasse: Fachbereich gewinnt, Fehler', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('Unterricht/ALLE10/Eth/BW7/Test-Schutz/Vorschau.html', '<html></html>')
        schreibe('ToDo/grundstufe-NOTIZEN.md', '# Notizbuch grundstufe\n\n## Eingang (unsortiert)\n- [ ] Ohne Form.\n')
        commit('Vorschau und Notiz [intern]')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Vorschau (schreibt GitHub) und neues Notizbuch des eigenen Teams: besteht', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('Unterricht/ALLE10/Eth/BW7/Test-Schutz/Fragen-Schutz.xml', xml)
        commit('Ethik vom Team [intern]')
        env['GITHUB_ACTOR'] = 'ethikerin'
        del env['UNTERRICHT_TEAMS_TEST']
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'nicht lesen' in aus and 'TEAM_APP_KEY' in aus, 'GitHub kann die Teams nicht lesen: Fehler, es wird nichts zugestellt', aus)
        git('reset', '-q', '--hard', basis)

        print('Abteilungsschutz am Rechner: GitHub fragen, sonst die Git-Geschichte')
        env['UNTERRICHT_TEAMS_TEST'] = teams
        ethik = 'Unterricht/ALLE10/Eth/BW7/Test-Schutz/Fragen-Schutz.xml'
        schreibe(ethik, xml)
        env['UNTERRICHT_ICH'] = 'ethikerin'
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'laut GitHub' not in aus, 'im zuständigen Team: besteht', aus)
        env['UNTERRICHT_ICH'] = 'beides'
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'Teams "ethik"' in aus and 'laut GitHub' in aus, 'fremdes Team: Fehler, Team genannt', aus)
        env['UNTERRICHT_ICH'] = 'chefin'
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'laut GitHub' not in aus, 'Werkzeug-Verantwortliche laut GitHub: besteht', aus)
        env['UNTERRICHT_ICH'] = '-'
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'nicht erreichbar' in aus and 'Teams "ethik"' in aus,
               'GitHub nicht erreichbar, noch nichts im Bereich: nur Warnung', aus)
        env['UNTERRICHT_ICH'] = 'niemand'   # Zugang ohne read:org (Cloud-Sitzung): GitHub liefert keine Teams
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'nicht erreichbar' in aus and 'Teams "ethik"' in aus and 'laut GitHub' not in aus,
               'GitHub liefert keine Teams (Zugang ohne read:org): wie nicht erreichbar, nur Warnung', aus)
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Teams: unbekannt' in aus and 'Teams: keine' not in aus,
               'GitHub liefert keine Teams: --rechte meldet Teams unbekannt', aus)
        env['UNTERRICHT_ICH'] = '-'
        commit('Ethik früher [intern]')
        schreibe(ethik, xml.replace('<quiz>', '<quiz><!-- später -->'))
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'nicht erreichbar' not in aus, 'GitHub nicht erreichbar, früher schon im Bereich: keine Warnung', aus)
        git('reset', '-q', '--hard', basis)
        schreibe(ethik, xml)
        git('config', 'unterricht.werkzeug', 'ja')
        code, aus = pruefen('--intern')
        pruefe(code == 0 and 'laut GitHub' not in aus and 'nicht erreichbar' not in aus,
               'GitHub nicht erreichbar, unterricht.werkzeug ja: keine Prüfung', aus)
        env['UNTERRICHT_ICH'] = 'metaller'
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'Teams "ethik"' in aus and 'unterricht.werkzeug "ja"' in aus,
               'unterricht.werkzeug ja, laut GitHub aber nicht Werkzeug-Verantwortliche: GitHub geht vor, Fehler', aus)
        git('config', '--unset', 'unterricht.werkzeug')
        env['UNTERRICHT_ICH'] = '-'
        os.remove(os.path.join(repo, ethik))

        print('Werkzeug-Verantwortliche am Rechner: GitHub geht vor, sonst unterricht.werkzeug')
        aendere_skill(8)
        env['UNTERRICHT_ICH'] = 'chefin'
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'laut GitHub Werkzeug-Verantwortliche, ohne unterricht.werkzeug: Skill ändern besteht', aus)
        env['UNTERRICHT_ICH'] = 'ethikerin'
        git('config', 'unterricht.werkzeug', 'ja')
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'ändern nur Werkzeug-Verantwortliche' in aus and 'unterricht.werkzeug "ja"' in aus,
               'unterricht.werkzeug ja, laut GitHub nicht im Team: Skill ändern ist ein Fehler', aus)
        git('config', '--unset', 'unterricht.werkzeug')
        env['UNTERRICHT_ICH'] = '-'
        git('checkout', '--', '.agents/skills/baue-arbeitsblatt/SKILL.md')

        print('Auskunft --rechte: dieselbe Entscheidung wie die Prüfung')
        env['UNTERRICHT_ICH'] = 'chefin'
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Werkzeug-Verantwortliche: ja (laut GitHub)' in aus and 'pug' in aus and 'Name: Test' in aus
               and 'Login: @chefin' in aus and '"Ersteller: Test, @chefin"' in aus,
               'laut GitHub im Team: ja, Teams und Name', aus)
        env['UNTERRICHT_ICH'] = 'ethikerin'
        git('config', 'unterricht.werkzeug', 'ja')
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Werkzeug-Verantwortliche: nein (laut GitHub)' in aus and 'WARNUNG' in aus,
               'unterricht.werkzeug ja, laut GitHub nicht im Team: nein, mit Warnung', aus)
        env['UNTERRICHT_ICH'] = '-'
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Werkzeug-Verantwortliche: ja (GitHub nicht erreichbar' in aus and 'Teams: unbekannt' in aus,
               'GitHub nicht erreichbar: unterricht.werkzeug entscheidet', aus)
        git('config', '--unset', 'unterricht.werkzeug')
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Werkzeug-Verantwortliche: nein' in aus, 'ohne GitHub und ohne unterricht.werkzeug: nein', aus)

        print('Notizschutz: Im gemeinsamen Notizbuch prüft die Prüfung, was sich geändert hat')
        env['UNTERRICHT_TEAMS_TEST'] = teams
        notizen = 'ToDo/Alle-NOTIZEN.md'
        fremd = '- [ ] **Fremd (2026-11-01, Ersteller: Autor B):** Text.\n  - Unterpunkt.\n'
        eigen = '- [ ] **Eigen (2026-11-14, Ersteller: Autorin A, @autorin):** Text.\n'
        erledigt = '## Erledigt\n- [x] 2026-11-01 Alt.\n'

        def zettel(eingang, thema='- [ ] **Fremd im Thema (2026-11-01, Ersteller: Autor B):** Text.\n', fertig=''):
            schreibe(notizen, '# Notizzettel\n\nKopf.\n\n## Eingang (unsortiert)\n%s\nText im Eingang.\n\n## Thema\n\n%s\n%s%s'
                     % (eingang, thema, erledigt, fertig))

        zettel(fremd)
        commit('Testzettel [intern]')
        git('config', 'user.name', 'Autorin A')
        basis = kopf()

        def lauf(text, als='Autorin'):
            commit(text + ' [intern]')
            env['GITHUB_ACTOR'] = als
            return pruefen('--seit', basis)

        zettel(fremd + eigen)
        code, aus = lauf('Eintrag im Eingang')
        pruefe(code == 0, 'neuer Eintrag im Eingang mit eigenem Namen: besteht', aus)
        basis = kopf()   # später: eigener Eintrag liegt schon auf main
        zettel(fremd, fertig='- [x] 2026-11-15 **Eigen (2026-11-14, Ersteller: Autorin A, @autorin):** Text.\n')
        code, aus = lauf('Eigenen abhaken')
        pruefe(code == 0, 'eigenen Eintrag abhaken und nach "Erledigt": besteht', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd)
        code, aus = lauf('Eigenen löschen')
        pruefe(code == 1 and 'Eigener Eintrag gelöscht' in aus, 'eigenen Eintrag löschen: Fehler (abhaken statt löschen)', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen.replace('Autorin A, @autorin', 'Autor B, @autorb') + eigen)
        code, aus = lauf('Fremder Ersteller')
        pruefe(code == 1 and 'fremdem Ersteller' in aus, 'neuer Eintrag mit fremdem Namen und Login: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen + '- [ ] **Fremder Login (2026-11-14, Ersteller: Autorin A, @chefin):** Text.\n')
        code, aus = lauf('Fremder Login')
        pruefe(code == 1 and 'fremdem Ersteller' in aus, 'eigener Name, aber fremder Login: Fehler (der Login zählt)', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen + '- [ ] **Ohne Login (2026-11-14, Ersteller: Autorin A):** Text.\n')
        code, aus = lauf('Ohne Login')
        pruefe(code == 1 and 'ohne GitHub-Login' in aus, 'neuer Eintrag nur mit Namen: auf GitHub ein Fehler', aus)
        git('reset', '-q', '--hard', basis)
        git('config', 'user.name', 'Autor B')
        zettel(fremd.replace('Text.', 'Text ergänzt.') + eigen)
        code, aus = lauf('Alter eigener Eintrag', als='autorb')
        pruefe(code == 0, 'älterer Eintrag nur mit Namen: der Ersteller darf ihn weiter ändern (Übergang)', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd.replace('Autor B)', 'Autor B, @autorb)') + eigen)
        code, aus = lauf('Login nachgetragen', als='autorb')
        pruefe(code == 0, 'eigenen älteren Eintrag um den Login ergänzen: besteht', aus)
        git('config', 'user.name', 'Autorin A')
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen + '- [ ] **Ohne Angaben:** Text.\n')
        code, aus = lauf('Ohne Ersteller')
        pruefe(code == 1 and 'ohne Datum oder Ersteller' in aus, 'neuer Eintrag ohne Ersteller: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        zettel(eigen)
        code, aus = lauf('Fremden löschen')
        pruefe(code == 1 and 'Fremde Einträge' in aus and 'nichts zugestellt' in aus and 'autorin' in aus,
               'fremden Eintrag löschen: Fehler, es wird nichts zugestellt', aus)
        code, aus = pruefen('--seit', basis, '--zurueckhalten', zurueck)
        pruefe(code == 0 and zurueckgehalten() == ['ToDo/Alle-NOTIZEN.md'] and 'Fremde Einträge' in aus,
               'mit --zurueckhalten: Notizschutz hält nur ToDo/ an (Lauf wird trotzdem rot)', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd.replace('- [ ]', '- [x]') + eigen)
        code, aus = lauf('Fremden abhaken')
        pruefe(code == 1 and 'Fremde Einträge' in aus, 'fremden Eintrag abhaken: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        zettel(fremd + eigen, thema='- [ ] **Neu im Thema (2026-11-14, Ersteller: Autorin A):** Text.\n'
               '- [ ] **Fremd im Thema (2026-11-01, Ersteller: Autor B):** Text.\n')
        code, aus = lauf('Neu im Thema')
        pruefe(code == 1 and 'Neue Einträge kommen unter' in aus, 'neuer Eintrag in einem Themenabschnitt: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        schreibe(notizen, lies(notizen).replace('Kopf.', 'Kopf geändert.'))
        code, aus = lauf('Kopf geändert')
        pruefe(code == 1 and 'außerhalb der Einträge' in aus, 'Text außerhalb der Einträge ändern: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('ToDo/Test-Thema/Uebergabe.md', '# Übergabe\n\nErsteller: Autorin A, @autorin\n')
        code, aus = lauf('Themenordner')
        pruefe(code == 1 and 'liegen nur Notizbücher' in aus and 'ToDo/Test-Thema/Uebergabe.md' in aus,
               'Themenordner in ToDo/: Fehler (gibt es nicht mehr)', aus)
        git('reset', '-q', '--hard', basis)

        print('Notizbücher der Teams: schreiben nur das Team und Werkzeug-Verantwortliche')
        buch = '# Notizbuch pug\n\n## Eingang (unsortiert)\n- [ ] **Neu (2026-11-16, Ersteller: Politiker P, @politiker):** Text.\n\n## Erledigt\n'
        schreibe('ToDo/pug-NOTIZEN.md', buch)
        code, aus = lauf('Notizbuch vom Team', als='politiker')
        pruefe(code == 0, 'Notizbuch des eigenen Teams anlegen: besteht', aus)
        basis = kopf()
        schreibe('ToDo/pug-NOTIZEN.md', '# Notizbuch pug\n\nUmsortiert.\n\n## Thema\n- [x] Alles anders.\n')
        code, aus = lauf('Notizbuch vom Team frei geändert', als='beides')
        pruefe(code == 0, 'im Notizbuch des eigenen Teams ist alles erlaubt (auch fremde Einträge, Sortieren)', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('ToDo/pug-NOTIZEN.md', buch + '- [ ] Fremd.\n')
        code, aus = lauf('Fremdes Notizbuch', als='Metaller')
        pruefe(code == 1 and 'Notizbuch des Teams "pug"' in aus and 'metaller' in aus and 'nichts zugestellt' in aus,
               'Notizbuch eines fremden Teams ändern: Fehler, Team genannt', aus)
        code, aus = pruefen('--seit', basis, '--zurueckhalten', zurueck)
        pruefe(code == 0 and zurueckgehalten() == ['ToDo/pug-NOTIZEN.md'], 'mit --zurueckhalten: nur das Notizbuch wird angehalten', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'politiker'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Mitglied des Teams wiederholt den Lauf: besteht', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        git('reset', '-q', '--hard', basis)

        print('Vorlagen der Teams: Vorlagen/<team>/ ändert nur das Team')
        schreibe('Vorlagen/pug/Bild.txt', 'x')
        code, aus = lauf('Vorlagen vom Team', als='politiker')
        pruefe(code == 0, 'Datei im Vorlagen-Ordner des eigenen Teams: besteht', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('Vorlagen/pug/Bild.txt', 'x')
        code, aus = lauf('Fremde Vorlagen', als='Metaller')
        pruefe(code == 1 and 'Vorlagen des Teams "pug"' in aus and 'metaller' in aus, 'Vorlagen eines fremden Teams ändern: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('Vorlagen/Neu.md', 'x')
        code, aus = lauf('Datei direkt in Vorlagen', als='politiker')
        pruefe(code == 1 and 'Werkzeug geändert' in aus and 'Vorlagen/Neu.md' in aus, 'Datei direkt in Vorlagen/: Werkzeug, Fehler', aus)
        git('reset', '-q', '--hard', basis)
        frei = ('<!doctype html>\n<html lang="de">\n<head>\n<meta charset="utf-8">\n<meta name="vorlage-art" content="frei">\n'
                '<meta name="vorlage" content="pug/Frei.html">\n<meta name="loesung-hash" content="">\n<title>Frei</title>\n'
                '</head>\n<body>\n<p>Text</p>\n</body>\n</html>\n')
        schreibe('Vorlagen/pug/Frei.html', frei)
        code, aus = lauf('Freie Vorlage', als='politiker')
        pruefe(code == 0, 'freie Vorlage vom eigenen Team, ohne Freigabe: besteht', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('Vorlagen/pug/Frei.html', frei.replace('pug/Frei.html', 'pug/Andere.html'))
        code, aus = lauf('Freie Vorlage mit falschem Namen', als='politiker')
        pruefe(code == 1 and 'nennt eine andere Datei' in aus, 'freie Vorlage, die sich anders nennt: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        kern = lies('.agents/gemeinsam/templates/Fachunterricht.html')
        schreibe('Vorlagen/pug/Layout.html', kern)
        code, aus = lauf('Layout-Vorlage', als='politiker')
        pruefe(code == 0, 'Layout-Vorlage mit den Blöcken aus Fachunterricht.html: besteht', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('Vorlagen/pug/Layout.html', kern.replace('function printBlank', 'function printBlank2'))
        code, aus = lauf('Layout-Vorlage mit geändertem Kern', als='politiker')
        pruefe(code == 1 and 'nicht aktuell' in aus, 'Layout-Vorlage mit verändertem Kern: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        schreibe('Vorlagen/pug/Layout.html', kern.replace('</body>', '<script>var x = 1;</script>\n</body>'))
        code, aus = lauf('Layout-Vorlage mit Script außerhalb', als='politiker')
        pruefe(code == 1 and 'außerhalb der markierten Blöcke' in aus, 'eigenes Script ohne Markierung: Fehler', aus)
        git('reset', '-q', '--hard', basis)

        schreibe('ToDo/gibtsnicht-NOTIZEN.md', buch)
        code, aus = lauf('Notizbuch ohne Team', als='Metaller')
        pruefe(code == 1 and 'nicht lesen' in aus and 'gibtsnicht' in aus, 'Notizbuch für ein Team, das es nicht gibt: Fehler', aus)
        git('reset', '-q', '--hard', basis)
        git('config', 'user.name', 'Test')
        schreibe('ToDo/werkzeug-verantwortliche-NOTIZEN.md', buch)
        code, aus = lauf('Notizbuch der Werkzeug-Verantwortlichen', als='Andere')
        pruefe(code == 1 and 'Werkzeug geändert' in aus and 'werkzeug-verantwortliche-NOTIZEN.md' in aus,
               'Notizbuch der Werkzeug-Verantwortlichen ändern: Fehler (Werkzeug)', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'chefin'
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'Werkzeug-Verantwortliche wiederholen den Lauf: besteht', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        git('reset', '-q', '--hard', basis)
        del env['GITHUB_ACTOR']
        git('config', '--unset', 'unterricht.werkzeug')
        zettel(fremd.replace('Text.', 'Anderer Text.'))
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'Notizschutz' in aus and 'Fremde Einträge' in aus, 'am Rechner ohne Werkzeugrecht: fremden Eintrag ändern ist ein Fehler', aus)
        env['UNTERRICHT_ICH'] = 'politiker'   # am Rechner mit Verbindung: der eigene Login kommt von GitHub
        git('config', 'user.name', 'Politiker P')
        zettel(fremd + eigen + '- [ ] **Am Rechner (2026-11-14, Ersteller: Politiker P, @politiker):** Text.\n')
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'am Rechner: neuer Eintrag mit eigenem Login besteht', aus)
        zettel(fremd + eigen + '- [ ] **Am Rechner (2026-11-14, Ersteller: Politiker P, @chefin):** Text.\n')
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'fremdem Ersteller' in aus, 'am Rechner: fremder Login ist ein Fehler', aus)
        zettel(fremd + eigen + '- [ ] **Am Rechner (2026-11-14, Ersteller: Politiker P):** Text.\n')
        code, aus = pruefen('--intern')
        pruefe(code == 1 and 'ohne GitHub-Login' in aus, 'am Rechner mit Verbindung: Login fehlt ist ein Fehler', aus)
        env['UNTERRICHT_ICH'] = '-'
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'am Rechner ohne Verbindung: Name genügt vorerst (GitHub prüft den Login)', aus)
        git('config', 'user.name', 'Test')
        zettel(fremd.replace('Text.', 'Anderer Text.'))
        git('config', 'unterricht.werkzeug', 'ja')
        code, aus = pruefen('--intern')
        pruefe(code == 0, 'am Rechner von Werkzeug-Verantwortlichen: besteht', aus)
        git('reset', '-q', '--hard', basis)
        git('config', 'unterricht.werkzeug', 'ja')

        print('Neues Lernpaket')
        zahl = int(re.search(r'<b>(\d+)</b> Lernpakete', lies(DATEI)).group(1))
        seite = ('<html><head>\n<meta name="klasse" content="ALLE10">\n<meta name="fach" content="Eth">\n<meta name="abschnitt" content="BW7">\n'
                 '<meta name="thema" content="Testpaket">\n<title>Testpaket Zwei</title>\n'
                 '<!-- VERSIONEN: neueste oben\nV1.2 | 31.12.2099 | Commit folgt | Tippfehler in Aufgabe 3 korrigiert\n-->\n</head></html>\n')
        schreibe('Unterricht/ALLE10/Eth/BW7/Testpaket/index.html', seite)   # Lernpaket = Themenordner, dessen index.html eine Version trägt
        code, aus = pruefen('--erneuern')
        s = lies(DATEI)
        pruefe(code == 0, 'neues Lernpaket besteht', aus)
        pruefe('Lernpaket betroffen: ja (Testpaket)' in aus, 'meldet: Lernpaket betroffen (dann fragt Claude vor dem Push)', aus)
        pruefe('<b>%d</b> Lernpakete' % (zahl + 1) in s and 'Testpaket Zwei' in s, 'auch noch nicht committet: Paket unter "Alle Lernpakete", Zahl erhöht')
        pruefe('Testpaket Zwei V1.2:</b> Tippfehler in Aufgabe 3 korrigiert' in s, 'Änderungstext unter "Was ist neu"')
        commit('Paket' + CLAUDE)
        z = os.path.join(repo, 'FREIGABE-SYNC', 'Pakete', 'ALLE10', 'Eth', 'ALLE10_Eth_BW7_Testpaket_scorm.zip')
        os.makedirs(os.path.dirname(z), exist_ok=True)
        with zipfile.ZipFile(z, 'w') as a:
            a.writestr('index.html', seite)
        git('add', '-f', '--', os.path.relpath(z, repo))
        code, aus = pruefen()
        pruefe(code == 1 and 'gehört nicht in Git' in aus, 'Paket trotzdem in Git: Fehler', aus)
        git('rm', '-q', '--cached', '--', os.path.relpath(z, repo))
        schreibe('FREIGABE-SYNC/Kurse/Kurs-Probe.mbz', 'x')
        git('add', '-f', '--', 'FREIGABE-SYNC/Kurse/Kurs-Probe.mbz')
        code, aus = pruefen()
        pruefe(code == 1 and 'Kurs-Probe.mbz' in aus, 'Kurssicherung in Git: Fehler', aus)
        git('rm', '-q', '--cached', '--', 'FREIGABE-SYNC/Kurse/Kurs-Probe.mbz')
        code, aus = pruefen()
        pruefe(code == 1 and 'liegt im Projektordner' in aus, 'Ordner FREIGABE-SYNC/ im Projektordner: Fehler (Pakete nur über GitHub)', aus)
        shutil.rmtree(os.path.join(repo, 'FREIGABE-SYNC'))

        basis = kopf()
        schreibe('Unterricht/ALLE10/Eth/BW7/Testpaket/index.html', seite.replace('</html>', '<p>neu</p></html>'))
        code, aus = pruefen()
        pruefe(code == 1 and 'nicht neu gebaut' in aus, 'Lernpaket geändert, Version nicht hochgezählt: Fehler vor dem Commit', aus)
        commit('Paket geändert, nicht gebaut (von Hand)')
        code, aus = pruefen('--seit', basis)
        pruefe(code == 1 and 'nicht neu gebaut' in aus, 'dasselbe auf GitHub: Fehler, es wird nichts zugestellt', aus)
        schreibe('Unterricht/ALLE10/Eth/BW7/Testpaket/index.html', seite.replace('</html>', '<p>neu</p></html>').replace(
            'V1.2 | 31.12.2099 | Commit folgt | Tippfehler', 'V1.3 | 31.12.2099 | Commit folgt | Absatz ergänzt\nV1.2 | 31.12.2099 | Commit abc1234 | Tippfehler'))
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and 'Testpaket Zwei V1.3:</b> Absatz ergänzt' in lies(DATEI), 'mit neuer Version: besteht, Änderung unter "Was ist neu"', aus)
        commit('Paket gebaut' + CLAUDE)
        code, aus = pruefen('--seit', basis)
        pruefe(code == 0, 'auf GitHub nach dem Nachbau: besteht (der rote Lauf wird nachgeholt)', aus)

        print('Kursplan')
        schreibe('Unterricht/ALLE10/Kurs-ALLE10.json', '{"kurs": {"vollname": "Probe", "kurzname": "Probe-Kurs", "startdatum": "2099-01-01"},'
                 ' "abschnitte": [{"dateien": [{"typ": "test", "datei": "gibt/es/nicht.mbz", "passwort": "geheim"}]}]}')
        code, aus = pruefen()
        pruefe(code == 1 and 'nicht.mbz' in aus and 'Kennwort' in aus, 'Kursplan mit fehlender Datei und Kennwort: Fehler', aus)
        os.remove(os.path.join(repo, 'Unterricht', 'ALLE10', 'Kurs-ALLE10.json'))

        print('Test-XML')
        ordner = 'Unterricht/ALLE10/Eth/BW7/Test-Probe'
        schreibe(ordner + '/Fragen-Probe.xml', '<quiz><question type="truefalse">')
        code, aus = pruefen()
        pruefe(code == 1 and 'XML fehlerhaft' in aus, 'kaputte Test-XML: Fehler', aus)
        schreibe(ordner + '/Fragen-Probe.xml', '<?xml version="1.0" encoding="UTF-8"?>\n<quiz></quiz>\n')
        code, aus = pruefen('--erneuern', '--intern')
        pruefe(code == 0 and os.path.isfile(os.path.join(repo, ordner, 'Vorschau.html')), 'gültige Test-XML: Vorschau.html entsteht', aus)
        shutil.rmtree(os.path.join(repo, *ordner.split('/')))

        print('Neuer Skill und Fragen')
        schreibe('.agents/skills/Test-Skill/SKILL.md', '---\nname: Test-Skill\ndescription: Macht etwas Neues. Use when the teacher says "Mach etwas Neues".\n---\n')
        schreibe(NEU, '31.12.2099 | Neuer Skill.\n', True)
        code, aus = pruefen('--erneuern')
        pruefe(code == 1 and 'Test-Skill' in aus, 'neuer Skill ohne Kurztext: Fehler', aus)
        schreibe('.agents/handbuch/skills.txt', 'Test-Skill | Macht etwas Neues | Mach etwas Neues\n', True)
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and '/Test-Skill' in lies(DATEI), 'mit Kurztext: Skill steht im Handbuch', aus)
        schreibe(FRAGEN, 'Frage ohne Antwort? | gibt-es-nicht\n', True)
        code, aus = pruefen('--erneuern')
        pruefe(code == 1 and 'gibt-es-nicht' in aus, 'Frage ohne Abschnitt: Fehler', aus)
        schreibe(FRAGEN, lies(FRAGEN).replace('Frage ohne Antwort? | gibt-es-nicht\n', 'Testfrage? | einbinden\n'))
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and 'Testfrage?' in lies(DATEI), 'neue Frage steht automatisch im Handbuch', aus)
        s = lies(DATEI)
        schreibe(DATEI, s.replace('</main>', '<section><h2 id="neu-test">Neues Kapitel</h2></section></main>'))
        code, aus = pruefen('--erneuern')
        pruefe(code == 0 and 'href="#neu-test"' in lies(DATEI), 'neue Überschrift erscheint in der Seitenleiste', aus)
        commit('Skill, Frage, Kapitel' + CLAUDE)

        print('Eine Lehrkraft allein (schule.txt: "Schutz | aus")')
        profil_datei = '.agents/gemeinsam/data/schule.txt'
        env.pop('GITHUB_TRIGGERING_ACTOR', None)
        env['GITHUB_RUN_ATTEMPT'] = '1'
        vorher = kopf()
        def schutz_setzen(w):   # Zeile "Schutz | …" ersetzen, egal ob der Klon CRLF oder LF auscheckt
            schreibe(profil_datei, re.sub(r'(?m)^Schutz \|[^\r\n]*', 'Schutz | ' + w, lies(profil_datei)))
            # wie am Rechner (pruefen.py --erneuern): die erzeugten Blöcke in Regeln und Skills mit dem Profil erneuern
            subprocess.run([sys.executable, '-c', 'import sys; sys.dont_write_bytecode = True; '
                            'sys.path.insert(0, ".agents/gemeinsam/scripts"); import anbindung; anbindung.schreiben()'],
                           cwd=repo, env=env, check=True)
            return re.search(r'(?m)^Schutz \| %s\r?$' % w, lies(profil_datei)) is not None
        pruefe(schutz_setzen('aus'), 'Testprofil: Schutz aus gesetzt')
        aendere_skill(8)
        commit('Schutz aus von Unberechtigten [intern]')
        env['GITHUB_ACTOR'] = 'Autorin'
        code, aus = pruefen('--seit', vorher)
        pruefe(code == 1 and 'nichts zugestellt' in aus and 'autorin' in aus,
               'Push, der selbst "Schutz | aus" setzt: gilt erst nach dem grünen Lauf, also Fehler', aus)
        env['GITHUB_ACTOR'] = 'chefin'
        code, aus = pruefen('--seit', vorher)
        pruefe(code == 0, 'derselbe Push von Werkzeug-Verantwortlichen: besteht', aus)
        aus_basis = kopf()
        aendere_skill(9)
        commit('Skill nach Schutz aus [intern]')
        env['GITHUB_ACTOR'] = 'Autorin'
        code, aus = pruefen('--seit', aus_basis)
        pruefe(code == 0, 'nach dem grünen Lauf mit "Schutz | aus": Werkzeug ändern darf jede Person', aus)
        env['GITHUB_TRIGGERING_ACTOR'] = 'Autorin'
        code, aus = pruefen('--von-hand')
        pruefe(code == 0 and 'Schutz aus' in aus, 'Schutz aus: Lauf von Hand darf jede Person starten', aus)
        del env['GITHUB_TRIGGERING_ACTOR']
        code, aus = pruefen('--rechte')
        pruefe(code == 0 and 'Werkzeug-Verantwortliche: ja (Schutz aus laut schule.txt)' in aus, 'Schutz aus: --rechte meldet ja', aus)
        r = subprocess.run([sys.executable, SCHUTZ_GITHUB, '--pruefen'], cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pruefe(r.returncode == 0 and 'nicht nötig' in r.stdout.decode('utf-8', 'replace'), 'Schutz aus: schutz-github.py --pruefen fragt GitHub nicht',
               r.stdout.decode('utf-8', 'replace'))
        pruefe(schutz_setzen('vielleicht'), 'Testprofil: Schutz vielleicht gesetzt')
        commit('Schutz unklar [intern]')
        unklar = kopf()
        aendere_skill(10)
        commit('Skill bei unklarem Schutz [intern]')
        code, aus = pruefen('--seit', unklar)
        pruefe(code == 1 and 'nichts zugestellt' in aus, 'unklarer Wert ("vielleicht"): der Schutz gilt', aus)
        git('reset', '-q', '--hard', vorher)
        env['GITHUB_ACTOR'] = 'chefin'

        print('Nur prüfen')
        pruefe(git('status', '--short')[1].strip() == '', 'Arbeitsordner sauber', git('status', '--short')[1])
        schreibe(NEU, '31.12.2099 | Noch eine.\n', True)
        r = subprocess.run([sys.executable, '.agents/handbuch/handbuch.py', '--pruefen'], cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pruefe(r.returncode == 1, 'handbuch.py --pruefen meldet veraltete Teile (neue Neuigkeit noch nicht eingetragen)', r.stdout)
        subprocess.run([sys.executable, '.agents/handbuch/handbuch.py'], cwd=repo, env=env, stdout=subprocess.DEVNULL)
        r = subprocess.run([sys.executable, '.agents/handbuch/handbuch.py', '--pruefen'], cwd=repo, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        pruefe(r.returncode == 0, 'danach: alle Prüfungen bestanden', r.stdout)
    finally:
        def frei(f, p, _):
            os.chmod(p, stat.S_IWRITE)
            f(p)
        shutil.rmtree(tmp, onerror=frei)
    bad = ergebnisse.count(False)
    print('\n%d von %d Prüfungen bestanden.' % (len(ergebnisse) - bad, len(ergebnisse)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
