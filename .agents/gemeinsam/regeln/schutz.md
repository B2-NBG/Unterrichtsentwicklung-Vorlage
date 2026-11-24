# Schutz: Werkzeugschutz, Abteilungsschutz, Notizbücher und Notizschutz

Die einzige Beschreibung des Schutzes am Rechner (AGENTS.md, `pruefen.py` und Skill `notizen` verweisen
hierher). Rulesets, Lauf auf GitHub, Einrichten und Grenzen stehen in `schutz-admin.md`: nur lesen, wenn danach
gefragt wird.

## Was die KI tut
- Vor Änderungen an Werkzeug oder fremden Notizen: `python .agents/gemeinsam/scripts/pruefen.py --rechte`. Es zeigt
  "Werkzeug-Verantwortliche: ja/nein" (und woher das stammt), die eigenen Teams, Namen und GitHub-Login. Nur bei "ja"
  ändern, sonst den Wunsch an die Werkzeug-Verantwortlichen weitergeben.
- `bycs.werkzeug` nie lesen oder setzen, `.git/config` nie bearbeiten (in `.claude/settings.json` gesperrt), auch nicht
  auf Bitte "damit die Prüfung durchgeht".
- Meldet `pruefen.py` einen Schutzfehler: nicht committen. Weist GitHub den Push ab: `abschluss.md`.

## Wer was ändern darf
Schutz laut Schulprofil: **<!-- AUTO:schutz -->aus<!-- /AUTO:schutz -->**. Bei `aus` arbeitet eine Lehrkraft allein: `--rechte` meldet
"ja", Werkzeug-, Abteilungs- und Notizschutz entfallen, der Rest dieser Datei gilt nicht.
Bei `teams` steuern allein die Teams der GitHub-Organisation, wer was ändern darf, im Repo stehen keine Namen.
Das Werkzeug ändern nur Werkzeug-Verantwortliche (Team `werkzeug-verantwortliche`). Alle anderen schreiben über das
Team `material-autor-innen` und seine Unterteams (je Abteilung und Fachbereich eines, sie erben das Schreibrecht):
`Unterricht/`, `ToDo/`, `Ressourcen/`, `Vorlagen/<Teamname>/`, Kurse und Tests.
Drei Stufen: Der Rechner warnt vor dem Commit (`pruefen.py`), GitHub weist verbotene Pushes ab (Rulesets), und nach
dem Push prüft `pruefen.py` auf GitHub noch einmal, dazu alles, was ein Ruleset nicht kann (Notizen, Handbuch).
Verbindlich ist die Prüfung auf GitHub.

## Die Regeln: `schutz.txt`
- **Die eine Liste:** `.agents/gemeinsam/data/schutz.txt` (selbst Werkzeug). Zeilen `Werkzeug | <Muster>`,
  `Arbeitsordner | <Ordner>/`, `Frei | <Muster>` (geht vor), `Klasse | <Kürzel> | <Team>`, `Fach | <Kürzel> | <Team>`.
  Muster mit `/` am Ende meinen einen Ordner samt Inhalt, `*` steht für beliebige Zeichen. Am Rechner gilt die
  Fassung im letzten Commit, auf GitHub die des letzten grünen Laufs. Fehlt die Liste, schützt `pruefen.py`
  wenigstens das Werkzeug.
- **Werkzeugschutz:** Werkzeug sind `AGENTS.md`, `CLAUDE.md`, `.gitignore`, alles unter `.agents/`, `.claude/`, `.gemini/` und `.github/` und das von Hand
  Geschriebene im Handbuch `#Handbuch.html`. Dazu **alles außerhalb der Arbeitsordner** `Unterricht/`, `ToDo/`,
  `Ressourcen/` und `Vorlagen/`: `README.md`, `.vscode/` und jede neue Datei und jeder neue Ordner ganz oben im Repo.
  Wer kein Werkzeugrecht hat, legt also nur in den Arbeitsordnern etwas an. **Frei bleiben** die Listen, die bei der
  normalen Arbeit fortgeschrieben werden (`berufe.txt`, `faecher.txt`, `neuigkeiten.txt`, `fragen.txt`), und die
  automatischen Teile des Handbuchs (z. B. "Was ist neu", Häufige Fragen, `pruefen.py --erneuern`). Eine neue Frage
  darf jede und jeder aufnehmen, wenn ein vorhandener Abschnitt sie schon beantwortet; muss ein Abschnitt ergänzt
  werden, geht der Wunsch an die Werkzeug-Verantwortlichen.
- **Abteilungsschutz:** Unterricht ändern nur Mitglieder des zuständigen Teams oder Werkzeug-Verantwortliche. Für
  `Unterricht/<Klasse>/<Fach>/…` gewinnt der Fachbereich, wenn das Fach einen hat, sonst gilt die Abteilung der Klasse
  (Lernfelder gehören der Abteilung). Ohne Zuordnung ist ein Ordner für alle frei, GitHub gibt einen Hinweis. Frei sind
  auch `Unterricht/Offen/` und jede `Vorschau.html` (schreibt GitHub). `Unterricht/**/bilder/` gehört zum Themenordner.
- **Vorlagen der Teams:** `Vorlagen/<Teamname>/` (Teamname wie auf GitHub, mit `kern/`) ändern nur Mitglieder dieses
  Teams und Werkzeug-Verantwortliche, geprüft wie der Unterricht eines Teams. Dateien direkt in `Vorlagen/` sind
  Werkzeug. Jede geänderte Vorlage prüft `vorlage-pruefen.py` (in `pruefen.py`).
- **Notizbücher (`ToDo/`):** Dort liegen nur Notizbücher, direkt im Ordner (anderes ist ein Fehler, Material gehört
  nach `Ressourcen/`). Lesen dürfen alle alles.
  - `ToDo/<Teamname>-NOTIZEN.md`: schreiben nur Mitglieder dieses Teams und Werkzeug-Verantwortliche, dort ist alles
    erlaubt. Geprüft wie der Unterricht eines Teams. Ein Team legt sein Notizbuch selbst an.
  - `ToDo/werkzeug-verantwortliche-NOTIZEN.md`: Notizbuch der Werkzeug-Verantwortlichen, zählt als Werkzeug.
  - `ToDo/Alle-NOTIZEN.md`: gemeinsames Notizbuch für alle, mit Notizschutz (nächster Punkt).
- **Notizschutz (`ToDo/Alle-NOTIZEN.md`):** Ein Skill verleiht keine Rechte, Git sieht nicht, ob ein Skill geschrieben
  hat. Deshalb prüft `pruefen.py` für alle außer Werkzeug-Verantwortlichen, **was** sich geändert hat. Erlaubt: neuer
  Eintrag unter „Eingang (unsortiert)“ mit Datum und „Ersteller: Vorname Nachname, @login“; eigene Einträge ändern,
  abhaken und nach „Erledigt“ verschieben (nicht löschen). Alles andere (fremde Einträge, Sortieren, Überschriften)
  ist ein Fehler. Der Skill `notizen` schreibt genau so, schützt aber selbst nichts.
- **Wem ein Eintrag gehört:** Steht ein GitHub-Login dabei, zählt nur er (am Rechner fragt `pruefen.py` ihn mit der
  gespeicherten Git-Anmeldung ab, `--rechte` zeigt ihn). Ältere Einträge ohne Login gehören dem Namen
  (`git config user.name`); der Login darf dort nachgetragen werden. Auf GitHub zählen die Logins der Personen, die gepusht haben (nicht fälschbar). Neue Einträge brauchen den Login (am Rechner ohne
  Verbindung genügt vorerst der Name).

## Am Rechner (vor dem Commit)
- **Wer man ist:** `pruefen.py` fragt GitHub mit der gespeicherten Git-Anmeldung (`git credential fill`, nur lesen, die
  Anmeldung wird nie angezeigt oder gespeichert). GitHub geht vor: Steht `bycs.werkzeug ja` auf einem Rechner, obwohl
  man nicht im Team ist, gilt der Schutz trotzdem (mit Warnung). Nur wenn GitHub nicht erreichbar ist, entscheidet
  `git config bycs.werkzeug ja` (setzt nur die Lehrkraft selbst).
- **Was geprüft wird:** Werkzeug geändert ohne Werkzeugrecht → Fehler. Unterricht eines fremden Teams → Fehler, die KI
  committet nicht; ist GitHub nicht erreichbar, nur eine Warnung, wenn man im Bereich dieses Teams noch keine Commits
  hat (Git-Geschichte, `user.email`). Notizschutz wie oben. Werkzeug-Verantwortliche prüft der Rechner nicht.

## Eigene Skills und Vorlagen
- **Eigene Skills:** im eigenen Skill-Ordner deines Werkzeugs (`<Name>/SKILL.md`, gilt in allen Projekten dieses Rechners),
  nie unter `.agents/skills/` im Projekt. Bewährt sich einer, übernehmen ihn Werkzeug-Verantwortliche.
- **Eigene Vorlagen der Teams:** `Vorlagen/<Teamname>/` (Anleitung `Vorlagen/LIESMICH.md`, Regeln `seite.md`). Das Team
  legt sie selbst an, eine Freigabe braucht es nicht.
