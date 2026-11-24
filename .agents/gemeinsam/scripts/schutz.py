"""
schutz.py - Werkzeug-, Abteilungs- und Notizschutz: wer was ändern darf (am Rechner vor dem Commit, auf GitHub vor
dem Zustellen). Aufgerufen wird er über pruefen.py (geschuetzt, --rechte, --von-hand); schutz-github.py nutzt die
Regeln für die Rulesets. pruefen.py stellt alle Namen von hier weiter unter pruefen.<Name> bereit.
Aus pruefen.py herausgelöst (24.11.2026), ohne das Verhalten zu ändern; die Tests stehen in handbuch.test.py.

5.-7. Werkzeug-, Abteilungs- und Notizschutz (geschuetzt). Was erlaubt ist, wie man freigibt und wo die Grenzen
   liegen, steht in .agents/gemeinsam/regeln/schutz.md und schutz-admin.md. Hier nur, wo
   es im Code steckt:
   - Vor dem Push sperrt GitHub selbst (Rulesets aus schutz.txt, schutz-github.py). Werkzeug- und Abteilungsschutz
     hier sind dafür die zweite Sicherung, Notizschutz und Handbuch (von Hand) kann nur diese Prüfung.
   - Regeln: SCHUTZ (schutz.txt) über Regeln und schutzregeln; auf GitHub aus dem letzten grünen Lauf.
   - Am Rechner (_am_rechner): wer man ist, fragt rechte (meine_teams: GitHub mit der gespeicherten Git-Anmeldung,
     sonst git config bycs.werkzeug); ohne GitHub Hinweis aus teams_aus_geschichte.
   - Auf GitHub (_auf_github): pushes_im_lauf (BYCS_PUSHES), freigeber (Re-run), mitglieder_von (TEAM_TOKEN der
     GitHub-App), --zurueckhalten (zurueck_pfad), --von-hand (von_hand).
   - Notizbücher in ToDo/ (notizbuch): Ein Team-Notizbuch ToDo/<Teamname>-NOTIZEN.md gehört dem Team (Regeln.team,
     geprüft wie der Unterricht eines Teams). Notizschutz gilt für das gemeinsame Notizbuch ALLE: todo_fehler und
     notizen_fehler prüfen den Inhalt; wem ein Eintrag gehört, sagen ersteller (Name, @login) und Ich (Login zählt,
     ältere Einträge ohne Login: der Name; mein_login am Rechner). Alles andere in ToDo/ ist ein Fehler.
   - Vorlagen der Teams (vorlagen_team): Vorlagen/<team>/ gehört dem Team (Regeln.team), Dateien direkt in
     Vorlagen/ sind Werkzeug.
     Geänderte Vorlagen prüft vorlage-pruefen.py (Schritt 1).
   - Tests: handbuch.test.py ersetzt GitHub durch eine Teams-Datei (BYCS_TEAMS_TEST, am Rechner dazu BYCS_ICH).
Nur Python-Standardbibliothek (Windows, Mac, GitHub).
"""
import fnmatch
import importlib.util
import json
import os
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
AUF_GITHUB = os.environ.get('GITHUB_ACTIONS') == 'true'
# Werkzeug- und Abteilungsschutz: die eine Liste der Regeln (Werkzeug, Arbeitsordner, Frei, Klasse, Fach): Regeln
SCHUTZ = '.agents/gemeinsam/data/schutz.txt'
# Nur wenn SCHUTZ fehlt oder kein Werkzeug nennt: Dann ist wenigstens das Werkzeug geschützt. Maßgeblich ist SCHUTZ.
NOTFALL_WERKZEUG = ('AGENTS.md', 'CLAUDE.md', '.gitignore', '.agents/', '.claude/', '.gemini/', '.github/', '#Handbuch.html')

def _profil():   # Schulprofil (schule.txt) über den Pfad laden: pruefen.py laden auch andere Skripte
    spec = importlib.util.spec_from_file_location('profil', os.path.join(HERE, 'profil.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


TEAM_WERKZEUG = _profil().wert('Team-Werkzeug', 'werkzeug-verantwortliche')   # GitHub-Team: darf das Werkzeug und jeden Unterricht ändern
PROFIL_DATEI = '.agents/gemeinsam/data/schule.txt'
# Notizbücher in ToDo/: das gemeinsame für alle (Notizschutz am Inhalt) und je Team eines (schreibt nur das Team)
ALLE = 'ToDo/Alle-NOTIZEN.md'
NOTIZBUCH = re.compile(r'ToDo/([A-Za-z0-9][A-Za-z0-9-]*)-NOTIZEN\.md', re.I)   # ohne Groß/Klein, wie die Rulesets
EINGANG, ERLEDIGT = 'Eingang (unsortiert)', 'Erledigt'
ERSTELLER = re.compile(r'Ersteller:\s*([^)\n]*)')   # "Ersteller: Vorname Nachname, @login" (ältere: nur der Name)
LOGIN = re.compile(r'@([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)')
FORM = '- [ ] **Titel (JJJJ-MM-TT, Ersteller: Vorname Nachname, @login):** Text'
NICHT_LESBAR = ('GitHub konnte die Mitglieder des Teams "%s" nicht lesen, deshalb wird nichts zugestellt. '
                'Werkzeug-Verantwortliche: GitHub-App und Secrets TEAM_APP_ID, TEAM_APP_KEY prüfen, gibt es das Team? '
                '(.agents/gemeinsam/regeln/schutz-admin.md), dann den Lauf wiederholen.')
STOPP = ' Es wird nichts zugestellt.'
ZURUECK = (' Zurückgehalten wird nur das Betroffene (%s), alles andere wird zugestellt. Der Lauf bleibt rot, bis es '
           'freigegeben ist.')
LOESEN = (' %s: Änderung ansehen, dann den Lauf wiederholen (Re-run jobs), oder die Änderung zurücknehmen (git revert) '
          'und pushen.')
NOTIZ = ('Notizschutz: %s Ohne Werkzeugrecht in ToDo/ erlaubt: im gemeinsamen Notizbuch ' + ALLE + ' ein neuer '
         'Eintrag im Eingang und eigene Einträge abhaken, im Notizbuch des eigenen Teams (ToDo/<Teamname>-NOTIZEN.md) '
         'alles (Skill notizen). Sonst den Wunsch an die Werkzeug-Verantwortlichen weitergeben '
         '(.agents/gemeinsam/regeln/schutz.md, "Notizschutz").')


def git(*args):
    """(Rückgabecode, Liste der Einträge) für Befehle mit -z, sonst Text."""
    r = subprocess.run(['git', '-c', 'core.quotePath=false'] + list(args), cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    aus = r.stdout.decode('utf-8', 'replace')
    return r.returncode, ([z for z in aus.split('\0') if z] if '-z' in args else aus)


def geaenderte_dateien(seit=None, auch_geloeschte=False):
    """Geänderte und neue Dateien (ab Projektordner), mit auch_geloeschte auch gelöschte (Umbenennen = alter Name
    gelöscht, neuer Name neu). Ohne seit: Arbeitsstand gegen HEAD. None, wenn Git den Commit nicht kennt."""
    auswahl = '--no-renames' if auch_geloeschte else '--diff-filter=ACMR'
    if seit:
        code, d = git('diff', '--name-only', '-z', auswahl, seit, 'HEAD')
        return sorted(d) if code == 0 else None
    _, d = git('diff', '--name-only', '-z', auswahl, 'HEAD')
    _, neu = git('ls-files', '-z', '--others', '--exclude-standard')
    return sorted(set(d) | set(neu))


def kurz(dateien):
    """Die ersten sechs Dateien, dahinter "und n weitere"."""
    dateien = list(dateien)
    return ', '.join(dateien[:6]) + (' und %d weitere' % (len(dateien) - 6) if len(dateien) > 6 else '')


def notizbuch(pfad):
    """Team (klein), dem das Notizbuch ToDo/<Teamname>-NOTIZEN.md gehört. '' für alles andere, auch für ALLE."""
    m = NOTIZBUCH.fullmatch(pfad)
    return m.group(1).lower() if m and pfad.lower() != ALLE.lower() else ''


def vorlagen_team(pfad):
    """Team (klein), dem Vorlagen/<team>/… gehört. '' für alles andere, auch für Dateien direkt in Vorlagen/."""
    t = pfad.split('/')
    return t[1].lower() if len(t) > 2 and t[0].lower() == 'vorlagen' else ''


def bereich(dateien):
    """Wie der Bereich eines Teams in einer Meldung heißt: Notizbuch, Vorlagen oder Unterricht."""
    if all(notizbuch(p) for p in dateien):
        return 'Notizbuch'
    return 'Vorlagen' if all(vorlagen_team(p) for p in dateien) else 'Unterricht'


class Regeln:
    """Die Schutzregeln aus SCHUTZ: Muster für Werkzeug und Frei, Teams je Klasse und Fach (Kürzel klein).
    arbeit: die Arbeitsordner (mit / am Ende). Nennt SCHUTZ welche, ist alles außerhalb davon Werkzeug, auch neue
    Dateien und Ordner ganz oben im Repo.
    schreibweise: ('klasse' oder 'fach', Kürzel klein) -> Kürzel wie in SCHUTZ (für die Rulesets, schutz-github.py)."""

    def __init__(self, text):
        self.werkzeug, self.frei, self.klassen, self.faecher, self.schreibweise = [], [], {}, {}, {}
        self.arbeit = []
        for z in text.splitlines():
            t = [x.strip() for x in z.split('|')]
            art = t[0].lower()
            if z.lstrip().startswith('#'):
                continue
            if art in ('werkzeug', 'frei') and len(t) == 2 and t[1]:
                (self.werkzeug if art == 'werkzeug' else self.frei).append(t[1])
            elif art == 'arbeitsordner' and len(t) == 2 and t[1].endswith('/') and t[1].strip('/'):
                self.arbeit.append(t[1])
            elif art in ('klasse', 'fach') and len(t) == 3 and t[1] and t[2]:
                (self.klassen if art == 'klasse' else self.faecher)[t[1].lower()] = t[2].lower()
                self.schreibweise[(art, t[1].lower())] = t[1]
        if not self.werkzeug:
            self.werkzeug = list(NOTFALL_WERKZEUG)

    @staticmethod
    def _passt(pfad, muster):
        """Muster mit / am Ende: der Ordner samt allem darin; sonst der Pfad, * für beliebige Zeichen."""
        return pfad.startswith(muster) if muster.endswith('/') else fnmatch.fnmatchcase(pfad, muster)

    def ist_frei(self, pfad):
        return any(self._passt(pfad, m) for m in self.frei)

    def ist_werkzeug(self, pfad):
        if self.ist_frei(pfad):
            return False
        if notizbuch(pfad) == TEAM_WERKZEUG:   # Notizbuch der Werkzeug-Verantwortlichen
            return True
        if pfad.lower().startswith('vorlagen/'):   # Vorlagen/<team>/ gehört dem Team, der Rest ist Werkzeug
            return vorlagen_team(pfad) in ('', TEAM_WERKZEUG)
        if any(self._passt(pfad, m) for m in self.werkzeug):
            return True
        # Alles außerhalb der Arbeitsordner ist Werkzeug (ohne Groß/Klein, wie die Rulesets auf GitHub)
        return bool(self.arbeit) and not any(pfad.lower().startswith(a.lower()) for a in self.arbeit)

    def team(self, pfad):
        """Zuständiges Team: '' = frei (kein Unterricht oder "Frei"), None = Unterricht ohne Zuordnung.
        Ein Team-Notizbuch (notizbuch) gehört seinem Team, das der Werkzeug-Verantwortlichen ist Werkzeug."""
        eigen = notizbuch(pfad) or vorlagen_team(pfad)   # Notizbuch oder Vorlagen eines Teams
        if eigen:
            return '' if self.ist_frei(pfad) or self.ist_werkzeug(pfad) else eigen
        t = pfad.split('/')
        if t[0] != 'Unterricht' or len(t) < 3 or self.ist_frei(pfad):
            return ''
        fach = self.faecher.get(t[2].lower()) if len(t) > 3 else None   # Kursplan direkt in der Klasse: kein Fach
        return fach or self.klassen.get(t[1].lower())

    def bedarf(self, dateien):
        """({Team: [Dateien]}, {Ordner ohne Zuordnung}) für geänderte Pfade."""
        bedarf, ohne = {}, set()
        for p in sorted(dateien):
            team = self.team(p)
            if team is None:
                ohne.add('/'.join(p.split('/')[:3]))
            elif team:
                bedarf.setdefault(team, []).append(p)
        return bedarf, ohne


def schutzregeln(commit='HEAD'):
    """Regeln aus SCHUTZ in der Fassung von commit, nicht aus dem Arbeitsstand: Auf GitHub ist commit der letzte grüne
    Lauf, eine Änderung an den Regeln wirkt also erst nach der Freigabe (sonst könnte ein Push "Werkzeug | .agents/"
    streichen und wäre selbst frei). Fehlt SCHUTZ dort, gilt nur NOTFALL_WERKZEUG."""
    code, text = git('show', '%s:%s' % (commit, SCHUTZ))
    return Regeln(text if code == 0 else '')


def schutz_an(commit='HEAD'):
    """Gilt der Schutz (schule.txt: "Schutz | teams")? In der Fassung von commit, nicht aus dem Arbeitsstand: Auf GitHub
    ist commit der letzte grüne Lauf, sonst könnte ein Push "Schutz | aus" setzen und wäre selbst frei (wie bei
    schutzregeln). Nur ein klares "aus" schaltet ihn ab; fehlt das Profil oder ist es unlesbar: Schutz an."""
    code, text = git('show', '%s:%s' % (commit, PROFIL_DATEI))
    if code != 0:
        return True
    try:
        werte = [w for k, w, _ in _profil().zerlegen(text) if k == 'Schutz']
    except Exception:   # absichtlich breit: im Zweifel gilt der Schutz
        return True
    return not (werte and werte[0][:1] == ['aus'])


def _api(url, zugang, timeout=20):
    """GET bei der GitHub-API: (Status, Daten). Status 0 = keine Verbindung. Der Zugang wird nie ausgegeben."""
    anfrage = urllib.request.Request(url, headers={
        'Authorization': 'Bearer ' + zugang, 'Accept': 'application/vnd.github+json', 'User-Agent': 'pruefen.py'})
    try:
        with urllib.request.urlopen(anfrage, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return e.code, None
    except (OSError, ValueError):   # auch URLError
        return 0, None


def _github(pfad):
    """Antwort von GitHub als dict, False bei 404, None wenn GitHub nicht lesen lässt."""
    token, org = os.environ.get('TEAM_TOKEN', '').strip(), os.environ.get('GITHUB_REPOSITORY_OWNER', '').strip()
    if not token or not org:
        return None
    status, daten = _api('https://api.github.com/orgs/%s/%s' % (urllib.parse.quote(org), pfad), token)
    return daten if status == 200 else (False if status == 404 else None)


def _test_teams():
    """Nur für handbuch.test.py: {Team: {GitHub-Namen}} aus der Datei BYCS_TEAMS_TEST (Zeilen "team: name, name")
    statt GitHub, für den Lauf (mitglieder_von) wie für den Rechner (meine_teams mit BYCS_ICH). None ohne Test."""
    pfad = os.environ.get('BYCS_TEAMS_TEST')
    if not pfad:
        return None
    teams = {}
    with open(pfad, encoding='utf-8') as f:
        for z in f:
            if ':' in z:
                team, namen = z.split(':', 1)
                teams[team.strip().lower()] = {n.strip().lower() for n in namen.split(',')} - {''}
    return teams


_MITGLIEDER = {}   # Team -> GitHub-Namen der Mitglieder, einmal je Lauf von GitHub gelesen


def mitglieder_von(team, wer):
    """Wer aus der Menge wer (GitHub-Namen, klein) im Team ist, Unterteams eingeschlossen. Liest die Mitglieder einmal
    je Team (alle Seiten) und merkt sie. None, wenn GitHub das Team nicht lesen lässt (fehlt, Zugang reicht nicht)."""
    test = _test_teams()
    if test is not None:
        return wer & test[team] if team in test else None
    if team not in _MITGLIEDER:
        namen, seite = set(), 1
        while True:
            daten = _github('teams/%s/members?per_page=100&page=%d' % (urllib.parse.quote(team), seite))
            if not isinstance(daten, list):   # False (404: Team fehlt) oder None (nicht lesbar)
                return None
            namen |= {str(m.get('login', '')).lower() for m in daten if isinstance(m, dict)} - {''}
            if len(daten) < 100:
                break
            seite += 1
        _MITGLIEDER[team] = namen
    return wer & _MITGLIEDER[team]


def handbuch_von_hand(hb, alt_commit, neu_commit=None):
    """True, wenn sich am Handbuch mehr geändert hat als die automatischen Teile (alt_commit gegen neu_commit,
    ohne neu_commit gegen den Arbeitsstand)."""
    code, alt = git('show', '%s:%s' % (alt_commit, hb.DATEI))
    if neu_commit:
        c, neu = git('show', '%s:%s' % (neu_commit, hb.DATEI))
        if c != 0:
            return True   # gelöscht
    else:
        try:
            neu = hb.lesen(hb.DATEI)
        except OSError:
            return True   # gelöscht
    if code != 0:
        return True   # neu
    try:   # beide Fassungen mit denselben automatischen Teilen füllen: Was dann noch abweicht, ist von Hand
        return hb.ohne_stand(hb.erneuern(alt)[0]) != hb.ohne_stand(hb.erneuern(neu)[0])
    except SystemExit:
        return True   # eine AUTO-Markierung fehlt


def _name(text):
    """Name zum Vergleichen: klein, ohne doppelte Leerzeichen."""
    return ' '.join(text.split()).casefold()


def ersteller(text):
    """(Name, Login) aus "Ersteller: Vorname Nachname, @login" (erste Fundstelle, zum Vergleichen klein), ('', '')
    wenn keiner dasteht. Ältere Einträge haben nur den Namen, der Login ist dann ''."""
    m = ERSTELLER.search(text or '')
    if not m:
        return '', ''
    login = LOGIN.search(m.group(1))
    return _name(re.split(r'[,@]', m.group(1), maxsplit=1)[0]), (login.group(1).lower() if login else '')


class Ich:
    """Wer gerade ändert: Namen und GitHub-Logins (klein). Steht beim Ersteller ein Login, zählt nur der Login (den
    bestätigt GitHub beim Push); ältere Einträge ohne Login gehören dem Namen. logins None = Login unbekannt (am Rechner
    ohne Verbindung zu GitHub): Dann zählt vorerst der Name, verbindlich prüft GitHub."""

    def __init__(self, namen, logins):
        self.namen, self.logins = set(namen) - {''}, (None if logins is None else set(logins) - {''})

    def meins(self, wer):
        name, login = wer
        if login and self.logins is not None:
            return login in self.logins
        return bool(name) and name in self.namen

    def ohne_login(self, wer):
        """True, wenn bei einem neuen Eintrag oder Ordner der Login fehlt, obwohl er sich prüfen lässt."""
        return not wer[1] and self.logins is not None


def notizen_teile(text):
    """Notizzettel zerlegen: (Überschriften, {Abschnitt: fester Text}, [(Abschnitt, Eintrag, Ersteller)]).
    Ein Eintrag ist eine Zeile "- [ ] …" samt den eingerückten Folgezeilen, fester Text der Rest ohne Leerzeilen."""
    abschnitt, koepfe, fest, eintraege = '', [], {'': []}, []
    for z in text.splitlines():
        if z.startswith('## '):
            abschnitt = z[3:].strip()
            koepfe.append(abschnitt)
            fest.setdefault(abschnitt, [])
        elif re.match(r'- \[.\]', z):
            eintraege.append([abschnitt, z.rstrip()])
        elif z[:1] in (' ', '\t') and z.strip() and eintraege and eintraege[-1][0] == abschnitt:
            eintraege[-1][1] += '\n' + z.rstrip()
        elif z.strip():
            fest[abschnitt].append(z.rstrip())
    return koepfe, fest, [(a, t, ersteller(t.split('\n', 1)[0])) for a, t in eintraege]


def notizen_fehler(alt_commit, ich):
    """Was am gemeinsamen Notizbuch ALLE ohne Werkzeugrecht nicht erlaubt ist (Liste von Texten, leer = in Ordnung)."""
    code, alt = git('show', '%s:%s' % (alt_commit, ALLE))
    if code != 0:
        return ['%s ist neu. Das gemeinsame Notizbuch legen nur Werkzeug-Verantwortliche an.' % ALLE]
    try:
        with open(os.path.join(ROOT, ALLE), encoding='utf-8') as f:
            neu = f.read()
    except OSError:
        return ['%s ist gelöscht. Das gemeinsame Notizbuch löschen nur Werkzeug-Verantwortliche.' % ALLE]
    k_alt, f_alt, e_alt = notizen_teile(alt)
    k_neu, f_neu, e_neu = notizen_teile(neu)
    fehler = []
    if k_alt != k_neu:
        fehler.append('Überschriften geändert (nur Werkzeug-Verantwortliche).')
    elif f_alt != f_neu:
        fehler.append('Text außerhalb der Einträge geändert (Abschnitt "%s", nur Werkzeug-Verantwortliche).'
                      % next(a for a in k_neu + [''] if f_alt.get(a) != f_neu.get(a)))
    rest = list(e_neu)
    fremd, eigen = [], []   # alte Einträge, die sich geändert haben oder fehlen
    for a, t, e in e_alt:
        if (a, t, e) in rest:
            rest.remove((a, t, e))
        elif ich.meins(e):
            eigen.append((a, e))
        else:
            fremd.append(t.split('\n', 1)[0][:90])
    if fremd:
        fehler.append('Fremde Einträge geändert, verschoben oder gelöscht: %s. Ändern dürfen das nur die Person, die '
                      'unter "Ersteller" steht, oder Werkzeug-Verantwortliche.' % '; '.join(fremd[:3]))
    for a, e in eigen:   # eigene Einträge dürfen sich ändern, aber nicht verschwinden
        treffer = [x for x in rest if ich.meins(x[2])]   # auch mit nachgetragenem Login
        passt = [x for x in treffer if x[0] in (a, ERLEDIGT)]
        if passt:
            rest.remove(passt[0])
        elif treffer:
            rest.remove(treffer[0])
            fehler.append('Eigener Eintrag in einen anderen Abschnitt verschoben (erlaubt: bleibt in "%s" oder '
                          'kommt nach "%s"). Sortieren dürfen nur Werkzeug-Verantwortliche.' % (a, ERLEDIGT))
        else:
            fehler.append('Eigener Eintrag gelöscht (Abschnitt "%s"). Abhaken statt löschen: [x], Datum, nach "%s".'
                          % (a, ERLEDIGT))
    for a, t, e in rest:   # neue Einträge
        kopf = t.split('\n', 1)[0]
        if a != EINGANG:
            fehler.append('Neuer Eintrag im Abschnitt "%s": %s. Neue Einträge kommen unter "%s".' % (a, kopf[:90], EINGANG))
        elif not any(e) or not re.search(r'\d{4}-\d{2}-\d{2}', kopf):
            fehler.append('Neuer Eintrag ohne Datum oder Ersteller: %s. Form: %s' % (kopf[:90], FORM))
        elif ich.ohne_login(e):
            fehler.append('Neuer Eintrag ohne GitHub-Login beim Ersteller: %s. Form: %s (den eigenen Login zeigt '
                          'pruefen.py --rechte).' % (kopf[:90], FORM))
        elif not ich.meins(e):
            fehler.append('Neuer Eintrag mit fremdem Ersteller: %s. Als Ersteller stehen der eigene Name und Login '
                          '(pruefen.py --rechte).' % kopf[:90])
    return fehler


def notizschutz_pfade(regeln, dateien):
    """Geänderte Pfade in ToDo/, für die der Notizschutz gilt: alles außer den Team-Notizbüchern (die gehören ihrem
    Team, Regeln.team) und dem, was SCHUTZ als Werkzeug oder Frei nennt."""
    return sorted(p for p in dateien if p.lower().startswith('todo/') and not notizbuch(p)
                  and not regeln.ist_werkzeug(p) and not regeln.ist_frei(p))


def todo_fehler(pfade, alt_commit, ich):
    """Notizschutz für die geänderten Pfade aus notizschutz_pfade (Liste von Texten, leer = in Ordnung). ich: Ich."""
    fehler, fremd = [], []
    for p in pfade:
        if p.lower() == ALLE.lower():
            fehler += notizen_fehler(alt_commit, ich)
        else:
            fremd.append(p)
    if fremd:
        fehler.append('In ToDo/ liegen nur Notizbücher (%s und je Team ToDo/<Teamname>-NOTIZEN.md), keine anderen '
                      'Dateien und keine Ordner: %s. Material gehört nach Ressourcen/.' % (ALLE, kurz(fremd)))
    return fehler


def organisation():
    """GitHub-Organisation des Repos: auf GitHub aus der Umgebung, am Rechner aus der Adresse von origin."""
    org = os.environ.get('GITHUB_REPOSITORY_OWNER', '').strip()
    if org:
        return org
    m = re.search(r'github\.com[:/]+([^/]+)/', git('remote', 'get-url', 'origin')[1])
    return m.group(1) if m else ''


_ANMELDUNG = []   # gespeicherte Git-Anmeldung für github.com, einmal je Aufruf geholt, nur im Speicher


def _anmeldung():
    """Am Rechner: Zugang aus der gespeicherten Git-Anmeldung (dieselbe wie beim Push, git credential fill, ohne
    Rückfrage). '' wenn keine da ist. Wird nie ausgegeben oder gespeichert."""
    if not _ANMELDUNG:
        umgebung = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='never')
        try:
            r = subprocess.run(['git', 'credential', 'fill'], cwd=ROOT, input=b'protocol=https\nhost=github.com\n\n',
                               env=umgebung, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
            werte = dict(z.split('=', 1) for z in r.stdout.decode('utf-8', 'replace').splitlines() if '=' in z)
            _ANMELDUNG.append(werte.get('password', '') if r.returncode == 0 else '')
        except (OSError, subprocess.SubprocessError):
            _ANMELDUNG.append('')
    return _ANMELDUNG[0]


def mein_login():
    """Am Rechner: eigener GitHub-Login (klein, für "Ersteller: …, @login"). None, wenn GitHub nicht erreichbar ist."""
    ich = os.environ.get('BYCS_ICH')   # nur für handbuch.test.py, "-" = nicht erreichbar
    if ich is not None:
        return None if ich.strip() in ('', '-') else ich.strip().lower()
    zugang = _anmeldung()
    if not zugang:
        return None
    status, daten = _api('https://api.github.com/user', zugang, timeout=10)
    login = str(daten.get('login', '')).lower() if status == 200 and isinstance(daten, dict) else ''
    return login or None


def meine_teams():
    """Am Rechner: Teams der Organisation, in denen die angemeldete Person ist (Menge der Kürzel, klein).
    Fragt GitHub mit der gespeicherten Git-Anmeldung (git credential fill, ohne Rückfrage). Die Anmeldung bleibt nur
    im Speicher, sie wird nie ausgegeben oder gespeichert. None, wenn das nicht geht (offline, keine Anmeldung, die
    Anmeldung darf keine Teams lesen). Nie eine leere Menge: Ein Zugang ohne read:org (Cloud-Sitzung, App-Token)
    bekommt von GitHub oft 200 mit leerer Liste statt 403, darum heißt "kein Team der Organisation" auch None
    (Teams unbekannt, verbindlich prüft GitHub nach dem Push)."""
    ich = os.environ.get('BYCS_ICH')   # nur für handbuch.test.py: GitHub-Name aus BYCS_TEAMS_TEST, "-" = nicht erreichbar
    if ich is not None:
        test = _test_teams()
        if ich.strip() == '-' or test is None:
            return None
        return {team for team, namen in test.items() if ich.strip().lower() in namen} or None
    org, zugang = organisation(), _anmeldung()
    if not org or not zugang:
        return None
    status, daten = _api('https://api.github.com/user/teams?per_page=100', zugang, timeout=10)
    if status != 200 or not isinstance(daten, list):
        return None
    return {str(t.get('slug', '')).lower() for t in daten if isinstance(t, dict)
            and str((t.get('organization') or {}).get('login', '')).lower() == org.lower()} - {''} or None


def rechte():
    """Am Rechner: (Werkzeug-Verantwortliche?, woher das stammt, eigene Teams oder None, bycs.werkzeug "ja"?).
    GitHub geht vor (meine_teams). Nur wenn GitHub nicht erreichbar ist, entscheidet git config bycs.werkzeug."""
    eingerichtet = git('config', '--get', 'bycs.werkzeug')[1].strip().lower() == 'ja'
    if not schutz_an():   # eine Lehrkraft allein (schule.txt: "Schutz | aus"): Sie darf alles
        return True, 'Schutz aus laut schule.txt', set(), eingerichtet
    meine = meine_teams()
    if meine is not None:
        return TEAM_WERKZEUG in meine, 'laut GitHub', meine, eingerichtet
    return eingerichtet, 'GitHub nicht erreichbar, laut git config bycs.werkzeug', None, eingerichtet


def rechte_zeigen():
    """Ausgabe für --rechte."""
    werkzeug, quelle, meine, eingerichtet = rechte()
    print('Werkzeug-Verantwortliche: %s (%s)' % ('ja' if werkzeug else 'nein', quelle))
    print('Teams: %s' % (', '.join(sorted(meine)) or 'keine') if meine is not None else
          'Teams: unbekannt (GitHub nicht erreichbar oder Teams nicht lesbar, verbindlich prüft GitHub nach dem Push)')
    name, login = git('config', '--get', 'user.name')[1].strip(), mein_login()
    print('Name: %s (git config user.name)' % (name or 'fehlt'))
    print('Login: @%s (laut GitHub)' % login if login else
          'Login: unbekannt (GitHub nicht erreichbar; neue Notizen erst eintragen, wenn GitHub erreichbar ist)')
    if login:
        print('Ersteller in Notizen: "Ersteller: %s, @%s"' % (name or 'Vorname Nachname', login))
    if eingerichtet and not werkzeug:
        print('WARNUNG: bycs.werkzeug steht auf "ja", laut GitHub bist du aber nicht im Team "%s".' % TEAM_WERKZEUG)


def teams_aus_geschichte(regeln):
    """Am Rechner, wenn GitHub nicht erreichbar ist: Teams, in deren Unterricht user.email schon Commits hat."""
    email = git('config', '--get', 'user.email')[1].strip().lower()
    if not email:
        return set()
    _, log = git('log', '--format=%x01%ae', '--name-only', 'HEAD', '--', 'Unterricht/')
    teams, meins = set(), False
    for z in log.splitlines():
        if z.startswith('\x01'):
            meins = z[1:].strip().lower() == email
        elif meins and z.strip():
            team = regeln.team(z.strip())
            if team:
                teams.add(team)
    return teams


def _vorfahr(a, b):
    """True, wenn Commit a in der Geschichte von b liegt (auch a == b)."""
    return git('merge-base', '--is-ancestor', a, b)[0] == 0


def pushes_im_lauf(seit):
    """GitHub: [(von, bis, Person, {Dateien})] je Push seit dem letzten grünen Lauf, älteste zuerst.
    BYCS_PUSHES (Workflow): "<Commit>:<GitHub-Name> …" der früheren Läufe seit dem letzten grünen Lauf, älteste zuerst.
    Dazu kommt dieser Lauf (HEAD, GITHUB_ACTOR). Ein Push bekommt die Dateien zwischen dem vorigen Push und seinem
    Commit (auch Commits ohne eigenen Lauf, z. B. das Handbuch von GitHub). Leer, wenn nicht auf GitHub."""
    liste = [(c, n.strip().lower()) for c, _, n in (x.partition(':') for x in os.environ.get('BYCS_PUSHES', '').split())
             if c and n.strip()]
    kopf, ich = git('rev-parse', 'HEAD')[1].strip(), os.environ.get('GITHUB_ACTOR', '').strip().lower()
    if ich and (not liste or liste[-1][0] != kopf):
        liste.append((kopf, ich))
    pushes, vorher = [], seit
    for commit, person in liste:
        if not _vorfahr(commit, 'HEAD') or _vorfahr(commit, vorher):
            continue   # nicht mehr auf main (erzwungener Push) oder schon vor dem Vergleichsstand
        von = vorher if _vorfahr(vorher, commit) else seit
        _, d = git('diff', '--name-only', '-z', '--no-renames', von, commit)
        pushes.append((von, commit, person, set(d)))
        vorher = commit
    return pushes


def freigeber():
    """GitHub: Wer den Lauf wiederholt hat (Re-run jobs, ab dem zweiten Versuch). Sonst ''."""
    try:
        versuch = int(os.environ.get('GITHUB_RUN_ATTEMPT', '1'))
    except ValueError:
        versuch = 1
    return os.environ.get('GITHUB_TRIGGERING_ACTOR', '').strip().lower() if versuch > 1 else ''


def von_hand():
    """GitHub, Lauf von Hand (Run workflow): Nur Werkzeug-Verantwortliche dürfen ihn starten, denn er stellt zu, was auf
    main liegt, auch das, was ein roter Lauf angehalten hat. Rückgabe 1, wenn nicht."""
    wer = (os.environ.get('GITHUB_TRIGGERING_ACTOR') or os.environ.get('GITHUB_ACTOR') or '').strip().lower()
    fehler = '::error::' if AUF_GITHUB else 'FEHLER: '
    if not wer:
        print(fehler + '--von-hand gibt es nur auf GitHub (Lauf von Hand, Run workflow).')
        return 1
    if not schutz_an():
        print('Lauf von Hand, gestartet von %s (Schutz aus laut schule.txt): Zugestellt wird, was auf main liegt.' % wer)
        return 0
    drin = mitglieder_von(TEAM_WERKZEUG, {wer})
    if drin is None:
        print(fehler + NICHT_LESBAR % TEAM_WERKZEUG)
        return 1
    if not drin:
        print(fehler + 'Einen Lauf von Hand (Run workflow) starten nur Werkzeug-Verantwortliche (Team "%s"), gestartet hat '
              'ihn %s. Es wird nichts zugestellt. Lernpakete, Kurse und Tests stellt GitHub nach jedem Push von selbst zu. '
              'Soll etwas neu zugestellt werden, die Werkzeug-Verantwortlichen fragen.' % (TEAM_WERKZEUG, wer))
        return 1
    print('Lauf von Hand, gestartet von %s (Werkzeug-Verantwortliche): Zugestellt wird, was auf main liegt, auch '
          'Änderungen, die ein roter Lauf angehalten hat.' % wer)
    return 0


def zurueck_pfad(p):
    """Was für eine geänderte Datei zurückgehalten wird: ihr Themen- bzw. Test-Ordner (Unterricht/<Klasse>/<Fach>/
    <Abschnitt>/<Ordner>/, wird als Ganzes gebaut und zugestellt), sonst die Datei selbst (z. B. ein Kursplan)."""
    t = p.split('/')
    return '/'.join(t[:5]) + '/' if t[0] == 'Unterricht' and len(t) > 5 else p


def geschuetzt(hb, seit=None, zurueckhalten=False):
    """Werkzeug-, Abteilungs- und Notizschutz. Rückgabe: (Fehler, Warnungen, zurückgehaltene Pfade).
    Am Rechner: Arbeitsstand gegen HEAD, Regeln aus HEAD. Auf GitHub (seit): alles seit dem letzten grünen Lauf, Regeln
    in dessen Fassung. Mit zurueckhalten (nur GitHub) halten Fehler im Abteilungs- und Notizschutz nur ihren Bereich an."""
    if not schutz_an(seit or 'HEAD'):   # eine Lehrkraft allein: kein Werkzeug-, Abteilungs- und Notizschutz
        return [], [], set()
    regeln = schutzregeln(seit or 'HEAD')
    d = set(geaenderte_dateien(seit, auch_geloeschte=True) or [])
    werkzeug = sorted(p for p in d if regeln.ist_werkzeug(p)
                      and (p != hb.DATEI or handbuch_von_hand(hb, seit or 'HEAD')))   # Handbuch: nur von Hand
    if seit:
        return _auf_github(hb, regeln, d, werkzeug, seit, zurueckhalten)
    return _am_rechner(regeln, d, werkzeug) + (set(),)


def _am_rechner(regeln, d, werkzeug):
    """Vor dem Commit, für alle außer Werkzeug-Verantwortliche (rechte). Rückgabe: (Fehler, Warnungen).
    Die eigenen Teams kommen von GitHub (verbindlich: Fehler). Ist GitHub nicht erreichbar, gibt es für den
    Abteilungsschutz nur einen Hinweis aus der Git-Geschichte (teams_aus_geschichte). Verbindlich prüft GitHub."""
    bedarf, _ = regeln.bedarf(d)
    notizen = notizschutz_pfade(regeln, d)
    if not (werkzeug or bedarf or notizen):
        return [], []
    recht, _, meine, eingerichtet = rechte()   # meine None = GitHub nicht erreichbar
    if recht:
        return [], []
    warnungen = ['Auf diesem Rechner steht bycs.werkzeug "ja", laut GitHub bist du aber nicht im Team "%s". '
                 'Werkzeug-, Notiz- und Abteilungsschutz gelten deshalb wie für alle.' % TEAM_WERKZEUG] if eingerichtet else []
    fehler = ['Werkzeug geändert (%s). Das Werkzeug (Skills, Vorlagen, Skripte, Regeln, Einstellungen, Handbuch und '
              'alles außerhalb der Arbeitsordner Unterricht/, ToDo/, Ressourcen/ und Vorlagen/<Teamname>/, auch neue Dateien und Ordner ganz '
              'oben im Repo) ändern nur Werkzeug-Verantwortliche. Änderung zurücknehmen und den Wunsch an die Werkzeug-Verantwortlichen '
              'weitergeben. Eigene Skills gehören in den eigenen Skill-Ordner deines Werkzeugs, nicht ins Projekt. '
              'Werkzeug-Verantwortliche: .agents/gemeinsam/regeln/schutz.md, "Werkzeugschutz".' % kurz(werkzeug)] if werkzeug else []
    if notizen:
        login = mein_login()
        ich = Ich({_name(git('config', '--get', 'user.name')[1])}, {login} if login else None)
        fehler += [NOTIZ % t for t in todo_fehler(notizen, 'HEAD', ich)]
    if meine is not None:
        fehler += ['%s des Teams "%s" geändert (%s), du bist laut GitHub aber nicht in diesem Team. Nach dem Push '
                   'würde nichts zugestellt. Änderung zurücknehmen oder ein Mitglied des Teams "%s" bzw. die '
                   'Werkzeug-Verantwortlichen bitten (.agents/gemeinsam/regeln/schutz.md, "Abteilungsschutz").'
                   % (bereich(dateien), team, kurz(dateien), team) for team, dateien in sorted(bedarf.items())
                   if team not in meine]
    elif bedarf:
        bekannt = teams_aus_geschichte(regeln)
        warnungen += ['GitHub war nicht erreichbar, die Teams sind nicht geprüft. Im %s des Teams "%s" (%s) gibt es '
                      'noch keine Änderung von dir. Bist du nicht in diesem Team, hält GitHub nach dem Push die Zustellung an.'
                      % (bereich(dateien), team, kurz(dateien)) for team, dateien in sorted(bedarf.items())
                      if team not in bekannt]
    return fehler, warnungen


def _auf_github(hb, regeln, d, werkzeug, seit, zurueckhalten):
    """Nach dem Push: jeder Push für sich (pushes_im_lauf), Freigabe nur per Re-run (freigeber).
    Rückgabe: (Fehler, Warnungen, zurückgehaltene Pfade)."""
    pushes = pushes_im_lauf(seit)
    if not pushes:   # nicht auf GitHub
        return [], [], set()
    _, ohne = regeln.bedarf(d)   # Ordner ohne Zuordnung
    warnungen = ['Ohne Zuordnung zu einer Abteilung oder einem Fachbereich, deshalb für alle frei: %s. '
                 'Werkzeug-Verantwortliche tragen Klasse oder Fach in %s ein.' % (', '.join(sorted(ohne)), SCHUTZ)] if ohne else []
    # Je Push: welches Team braucht er für welche Dateien? Es zählt nur, was sich seit dem letzten grünen Lauf wirklich
    # geändert hat (Zurückgenommenes nicht), das Handbuch nur, wenn dieser Push es von Hand geändert hat.
    noetig = {}   # Team -> {Person: [Dateien]}
    for von, bis, person, dateien in pushes:
        dateien &= d
        for team, liste in regeln.bedarf(dateien)[0].items():
            noetig.setdefault(team, {}).setdefault(person, []).extend(liste)
        wz = sorted(p for p in dateien if p in werkzeug and (p != hb.DATEI or handbuch_von_hand(hb, von, bis)))
        if wz:
            noetig.setdefault(TEAM_WERKZEUG, {}).setdefault(person, []).extend(wz)
    notizen = notizschutz_pfade(regeln, d)
    todo = sorted({person for _, _, person, dateien in pushes if dateien & set(notizen)})
    if not noetig and not todo:
        return [], warnungen, set()
    frei = freigeber()
    alle = {person for _, _, person, _ in pushes} | ({frei} - {''})
    chefs = mitglieder_von(TEAM_WERKZEUG, alle)
    if chefs is None:
        return [NICHT_LESBAR % TEAM_WERKZEUG], warnungen, set()
    if frei in chefs:   # Werkzeug-Verantwortliche haben den Lauf wiederholt: alles freigegeben
        return [], warnungen, set()

    def von_wem(fremde):
        return '; '.join('%s (%s)' % (person, kurz(sorted(set(dateien)))) for person, dateien in sorted(fremde.items()))

    fehler, zurueck = [], set()

    def anhalten(text, pfade, wer):
        """Fehler im Abteilungs- oder Notizschutz: mit zurueckhalten nur den Bereich anhalten, sonst alles."""
        if zurueckhalten:
            bereich = sorted({zurueck_pfad(p) for p in pfade})
            zurueck.update(bereich)
            warnungen.append('ZURUECK:' + text + ZURUECK % kurz(bereich) + LOESEN % wer)
        else:
            fehler.append(text + STOPP + LOESEN % wer)

    if todo and not set(todo) <= chefs:   # Notizschutz: eigene Logins = wer in ToDo/ gepusht hat (bestätigt GitHub),
        _, autoren = git('log', '-z', '--format=%an', '%s..HEAD' % seit, '--', 'ToDo/')   # Namen nur für ältere Einträge
        for t in todo_fehler(notizen, seit, Ich({_name(a) for a in autoren}, todo)):
            anhalten((NOTIZ % t) + ' Gepusht von %s.' % ', '.join(p for p in todo if p not in chefs),
                     notizen, 'Werkzeug-Verantwortliche')
    for team, wer_was in sorted(noetig.items()):
        fremde = {person: dateien for person, dateien in wer_was.items() if person not in chefs}
        if not fremde:
            continue
        if team == TEAM_WERKZEUG:
            fehler.append(('Werkzeug geändert von %s, das dürfen aber nur Werkzeug-Verantwortliche (Team "%s").'
                           % (von_wem(fremde), TEAM_WERKZEUG)) + STOPP + LOESEN % 'Werkzeug-Verantwortliche')
            continue
        drin = mitglieder_von(team, alle)
        if drin is None:
            fehler.append(NICHT_LESBAR % team)
            continue
        if frei in drin:   # ein Mitglied des Teams hat den Lauf wiederholt: Bereich freigegeben
            continue
        fremde = {person: dateien for person, dateien in fremde.items() if person not in drin}
        if fremde:
            pfade = [p for dateien in fremde.values() for p in dateien]
            anhalten('%s des Teams "%s" geändert von %s, niemand davon ist in diesem Team.'
                     % (bereich(pfade), team, von_wem(fremde)), pfade,
                     'Mitglieder des Teams "%s" oder Werkzeug-Verantwortliche' % team)
    return fehler, warnungen, zurueck
