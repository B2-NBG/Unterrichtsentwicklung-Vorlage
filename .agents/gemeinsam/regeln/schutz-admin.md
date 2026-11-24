# Schutz für Admins: Rulesets, Lauf auf GitHub, Einrichten, Grenzen

Nachschlagewerk für Werkzeug-Verantwortliche und Admins (Teil von `schutz.md`). Nur lesen, wenn danach gefragt wird.

## Auf GitHub: vor dem Push gesperrt (Rulesets)
- **Was gesperrt ist:** `schutz-github.py` macht aus `schutz.txt` die Rulesets des Repos (Settings → Rules →
  Rulesets), alle heißen „Schutz: …“:
  - „Schutz: Werkzeug“: die Werkzeug-Muster und alles außerhalb der Arbeitsordner (`*`, `**/*`), ausgenommen die
    Arbeitsordner und die Frei-Muster. Vorbei darf `werkzeug-verantwortliche`.
    `#Handbuch.html` ist nicht gesperrt (automatische Teile, Commit von GitHub), das von Hand Geschriebene prüft
    `pruefen.py` nach dem Push.
  - „Schutz: <team>“ je Team: seine Klassen (`Unterricht/<Klasse>/`), Fächer (`Unterricht/*/<Fach>/`), sein
    Notizbuch (`ToDo/<team>-NOTIZEN.md`) und seine Vorlagen (`Vorlagen/<team>/`), ausgenommen die Frei-Muster und in den eigenen Klassen die Fächer anderer Teams. Vorbei dürfen das Team und
    `werkzeug-verantwortliche`.
  - „Schutz: main“: kein Force-Push, kein Löschen von `main`, für alle.
- **Wie es wirkt:** auf allen Branches, auch für Commits über die GitHub-Webseite und für
  den Commit von GitHub selbst (der ändert nur Handbuch und Vorschau, beides ist frei). Groß- und Kleinschreibung
  der Pfade spielt keine Rolle. Ein Push wird **als Ganzes** abgewiesen, auch das Erlaubte darin
  („GH013: Repository rule violations“, „File path is restricted“, darunter die Dateien): `abschluss.md`.
  Ein Merge-Commit nach `git pull` ohne Rebase, der fremde Werkzeugänderungen von `main` mitbringt, geht durch.
- **Owner der Organisation** kommen an den Push-Rulesets vorbei, Admins des Repos können Rulesets ändern.
- **Prüfen:** `python .agents/gemeinsam/scripts/schutz-github.py --pruefen` vergleicht GitHub mit `schutz.txt`.
  Der Workflow macht das in jedem Lauf (Schritt „Rulesets passen zu schutz.txt?“, liest mit dem `GITHUB_TOKEN`):
  Fehlt ein Ruleset, ist eines abgeschaltet oder weicht es ab, wird nichts zugestellt. Wer vorbei darf, zeigt
  GitHub nur Admins: Das vergleicht nur `--pruefen` am Rechner eines Admins.
- **Notfall:** Sperrt ein Ruleset alle oder GitHub selbst aus, stellt ein Admin es unter Settings → Rules →
  Rulesets auf „Disabled“. Der nächste Lauf ist dann rot (gewollt), bis `--anwenden` wieder gelaufen ist.

## Auf GitHub (nach dem Push)
- **Zweite Sicherung:** Werkzeug- und Abteilungsschutz greifen hier nur noch, wenn ein Ruleset fehlt oder jemand
  daran vorbei durfte. Notizschutz und das von Hand Geschriebene im Handbuch prüft weiter nur diese Stufe. Sie ist
  jetzt verlässlich, weil Workflow und `pruefen.py` selbst gesperrt sind.
- **Jeder Push zählt für sich:** GitHub prüft alles seit dem letzten grünen Lauf, aber jeden Push einzeln: Was er
  geändert hat, muss die Person dürfen, die ihn gepusht hat. Der Workflow liefert dafür Commit und Person jedes Laufs
  seit dem letzten grünen (`BYCS_PUSHES`). Liefert GitHub diese Liste nicht vollständig (Fehler der API, kein grüner
  Lauf unter den 100 neuesten), wird der Lauf rot, statt alles dem letzten Push zuzuordnen. Es zählt nur, was sich wirklich geändert hat: Wurde eine Änderung
  zurückgenommen, ist sie erledigt. Ein späterer Push gibt nichts frei, auch nicht von Werkzeug-Verantwortlichen.
- **Was dann angehalten wird:** Werkzeug ohne Werkzeugrecht, unlesbare Teams und alle übrigen Fehler (Steckbrief,
  Version, Test-XML) halten **alles** an, auch das Unterrichtsmaterial aus demselben Lauf.
- **Zurückhalten:** Ein Fehler im Abteilungs- oder Notizschutz (auch: fremdes Team-Notizbuch geändert) hält nur das
  Betroffene an: den Themen- oder Test-Ordner (er wird als Ganzes gebaut), dazu jeden Kurs, der etwas daraus
  mitliefert (`ToDo/` wird ohnehin nie zugestellt). Alles andere wird zugestellt, der Lauf endet trotzdem rot ("Zurückgehalten, nicht zugestellt: …").
  Bis zur Freigabe stellt jeder neue Lauf das Übrige noch einmal zu (der Download-Link bleibt gleich). Technik:
  `pruefen.py --zurueckhalten <Datei>` schreibt die Pfade, `paket-zustellen.py --ohne <Datei>` lässt sie aus.
- **Freigeben:** nur, wer den Lauf wiederholt (Actions → Lauf → Re-run jobs; zählt ab dem zweiten Versuch), nachdem
  er sich die Änderung angesehen hat: ein Mitglied des genannten Teams für den Bereich dieses Teams,
  Werkzeug-Verantwortliche für alles. Oder die Änderung wird zurückgenommen (`git revert`) und gepusht. Wiederholt
  jemand ohne Recht den Lauf (z. B. weil ein Kurs auf einen Download-Link wartet), schadet das nicht, gibt aber auch
  nichts frei.
- **Lauf von Hand:** nur Werkzeug-Verantwortliche (`pruefen.py --von-hand`, `einrichtung-admin.md`, "GitHub: prüfen, bauen, zustellen").
- **Zugang zu den Teams:** Die Mitglieder liest `pruefen.py` im Lauf über eine GitHub-App der Organisation (nur
  Leserecht „Members“, Secrets `TEAM_APP_ID` und `TEAM_APP_KEY`), einmal je Team, Unterteams eingeschlossen. Fehlt der
  Zugang oder ein Team, ist der Lauf rot („konnte die Mitglieder des Teams … nicht lesen“) und nichts wird zugestellt.
  Neu einrichten: Organisation → Settings → Developer settings → GitHub Apps → New GitHub App (Webhook aus,
  Organization permissions → Members: Read-only, nur für diese Organisation), „Generate a private key“, „Install App“
  für die Organisation, dann App-ID und Inhalt der `.pem`-Datei als Secrets eintragen (`gh secret set TEAM_APP_KEY --env zustellung < Datei.pem`).
  Der Schlüssel kommt nie ins Repo und nie in den Chat.

## Einrichten
- **Neue Kolleg/innen:** auf GitHub in das Team ihrer Abteilung und ihrer Fachbereiche aufnehmen, mehr nicht.
- **Neues Team:** als Unterteam von `material-autor-innen` anlegen (sichtbar, nicht geheim) und in `schutz.txt`
  zuordnen. Neue Klasse oder neues Fach: Werkzeug-Verantwortliche tragen die Zeile in `schutz.txt` ein.
- **Nach jeder Änderung an `schutz.txt`:** committen, dann `python .agents/gemeinsam/scripts/schutz-github.py
  --anwenden`, dann pushen (so ist der Lauf gleich grün). `--anwenden` braucht Admin-Recht am Repo und zeigt, was es
  anlegt, ersetzt oder löscht; andere Rulesets fasst es nicht an. `--zeigen` gibt die Rulesets nur aus.
- **Neue Werkzeug-Verantwortliche:** ins Team `werkzeug-verantwortliche` aufnehmen. Jeden ihrer Rechner richten sie
  einmal selbst ein (`git config bycs.werkzeug ja`), damit sie auch ohne Verbindung zu GitHub arbeiten können.

## Grenzen
- Rulesets sperren Pfade, keinen Inhalt: Notizschutz und das von Hand Geschriebene im Handbuch bleiben eine
  Nachkontrolle (erkennen und zurückhalten, die Änderung liegt trotzdem auf `main`).
- Rulesets ändern (`--anwenden`, Notfall) kann nur, wer Admin am Repo ist. Das sind zwei Personen, beide
  auch Owner der Organisation (Vertretung).
- Wer vorbei darf, bestimmen die Teams: Team-Maintainer können Mitglieder aufnehmen.
- Ein neuer Branch auf einem **alten Commit** bringt keine geänderte Datei mit und wird nicht abgewiesen. Von dort
  ließe sich ein älterer Stand des Workflows von Hand starten. Er bekommt aber keine Secrets und kann nichts
  zustellen: Sie liegen im Environment `zustellung`, das nur `main` nutzen darf.
- Kein `CODEOWNERS`: Ohne Pull Requests zeigt es nur an, wer zuständig ist. Das steht in `schutz.txt`.
- Bei älteren Notizen ohne Login zählt der Name (`user.name`), den jede und jeder frei einstellen kann. Wer
  gepusht hat, steht aber immer im Lauf; mit dem Login nachgetragen ist auch das sicher.
