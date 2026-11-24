# Einrichtung für Admins: Workflow, Secrets, Flow, Rulesets

Nachschlagewerk für Werkzeug-Verantwortliche und Admins (Teil von `einrichtung.md`). Nur lesen, wenn danach gefragt
wird. Rulesets, Zugang zu den Teams und Freigabe: `schutz-admin.md`.

## GitHub: prüfen, bauen, zustellen ("Bauen und zustellen")
- Workflow `.github/workflows/paket-zustellen.yml` nach jedem Push auf `main`:
  1. vergleicht mit dem letzten grünen Lauf (was ein roter Lauf nicht zugestellt hat, holt der nächste grüne nach; in
     einem ganz neuen Repo mit dem ersten Commit, alles von da an baut ein Lauf von Hand mit `alle`),
  2. prüft mit `pruefen.py --seit … --erneuern` (Ablage, Steckbrief, Version, Kursplan, Test-XML, Handbuch;
     Mitdokumentieren nur als Warnung) und erneuert Handbuch und Test-Vorschau,
  3. committet Erneuertes als `github-actions[bot]` ("Automatisch: Handbuch und Vorschau erneuert [intern]"),
  4. baut die geänderten Lernpakete und Kurse und stellt sie mit geänderten Test-Ordnern und dem Handbuch zu
     (`.agents/skills/baue-lernpaket/scripts/paket-zustellen.py`).
  Ist die Prüfung rot, wird nichts zugestellt. Ausnahme: Ein Fehler im Abteilungs- oder Notizschutz hält nur seinen
  Bereich an (`schutz-admin.md`, "Zurückhalten").
- Von Hand (nur Werkzeug-Verantwortliche): GitHub → Actions → "Bauen und zustellen" → Run workflow: Themenordner,
  Test-Ordner, Kurs (Name wie `Kurs-ALLE10-PuG`), `Kurse`, `Handbuch` oder `alle`, mit Haken "Probe" nach
  `<Bereich>/_Pilot/`. Ein Lauf von Hand prüft nicht und stellt zu, was auf `main` liegt, auch was ein roter Lauf
  angehalten hat. Deshalb prüft er zuerst, wer ihn gestartet hat (`pruefen.py --von-hand`): Wer nicht im Team
  `werkzeug-verantwortliche` ist, bekommt einen roten Lauf, und nichts wird zugestellt.
- Secrets (Settings → Environments → `zustellung`, nur `main` darf es nutzen; keine Repository-Secrets): `FLOW_URL`,
  `FLOW_SCHLUESSEL` (Flow), `BYCS_LINKSEITE` (Adresse der Linkseite für den Kursbau), `TEAM_APP_ID`, `TEAM_APP_KEY`
  (Teams lesen, `schutz-admin.md`). Nie ins Repo, nie in den Chat.
- Einstellung: Settings → Actions → General → Workflow permissions: **Read and write** (für den Commit des Handbuchs).
- Schulprofil (`schule.txt`): Der Schritt "Schulprofil" liest `Schutz` (in der Fassung des letzten grünen Laufs, im
  Zweifel an) und `Zustellung`. Bei `Schutz | aus` entfallen Zugang zu den Teams und Rulesets, bei
  `Zustellung | download` legt der Lauf die Pakete als Download ab (Actions → Lauf → Artifacts) statt an den Flow.
- Der Flow (Power Automate, eigenes Dienstkonto, Schreibrecht auf den ganzen Ordner `BYCS-SYNC`) nimmt in `Pakete/`,
  `Kurse/` und `Tests/` samt Unterordnern nur `.html`, `.mbz`, `.xml` und `_scorm.zip` an, ganz oben nur das Handbuch.
  Er ersetzt eine vorhandene Datei an Ort und Stelle (der Download-Link bleibt) und legt fehlende Unterordner an.

## Power Automate einrichten (nur bei `Zustellung | power-automate`)
Zwei Flows mit einem eigenen Dienstkonto, das nur auf den Teamordner (`schule.txt`, `Teamordner`) schreiben darf:
1. **Zustellung:** Auslöser "Wenn eine HTTP-Anforderung empfangen wird" (POST, JSON mit `pfad`, `datei`, `inhalt`;
   `paket-zustellen.py`, Funktion `schicken`). Zuerst den Kopf `Flow-Kopf` (aus `schule.txt`) mit dem geheimen Schlüssel
   vergleichen, sonst mit 403 antworten. Nur die Endungen oben annehmen, sonst 400. Dann im Teamordner unter `pfad`
   fehlende Ordner anlegen und die Datei `datei` mit `base64ToBinary(inhalt)` anlegen oder ersetzen (ersetzen, nicht neu
   anlegen: Der Freigabelink bleibt). Antwort 200. Die HTTP-Adresse kommt als Secret `FLOW_URL`, der Schlüssel als
   `FLOW_SCHLUESSEL` ins Environment `zustellung`.
2. **Linkseite** (für Lernpakete mit Download-Link im Kurs): Jedes `_scorm.zip` unter `Pakete/` bekommt einen
   Freigabelink "Jeder mit dem Link". Ein zweiter HTTP-Flow (GET, mit Passwort) liefert eine HTML-Tabelle, je Paket eine
   Zeile `<tr data-p="Pakete/…">` mit `<td>Dateiname</td>`, dem Link in `data-link="https://…"` und dem Datum der
   letzten Änderung (`linkseite.py`, `RX_ZEILE` usw.). Die Adresse mit `&pw=…` kommt als Secret `BYCS_LINKSEITE`
   ins Environment, am Rechner liest `linkseite.py` sie wie in `einrichtung.md` beschrieben.
Probe: GitHub → Actions → "Bauen und zustellen" → Run workflow mit Haken "Probe" (legt nach `<Bereich>/_Pilot/`).

## GitHub: Werkzeug testen ("Werkzeug testen")
- Workflow `.github/workflows/werkzeug-testen.yml` nach jedem Push auf `main`, der `.agents/`, `AGENTS.md`, `.github/`
  oder eine `index.html` in `Unterricht/` ändert: alle `*.test.py`, `suspend-data.test.js` (Chrome des Runners) und
  `seite-pruefen.py --ohne-browser` für jede geänderte Seite. Nur Leserechte, ohne Environment und Secrets. Er hält die
  Zustellung nicht an; ist er rot, mailt GitHub der Person, die gepusht hat. Von Hand: Run workflow (alle Seiten).
- Actions sind auf einen Commit gepinnt, die Version steht als Kommentar daneben (`actions/checkout`,
  `actions/create-github-app-token`). Zweimal im Jahr (Februar, September) neue Versionen prüfen: Commit des Tags mit
  `gh api repos/<action>/git/ref/tags/<tag>` lesen, in beiden Workflows eintragen, einen Lauf von Hand machen. Eine neue
  Hauptversion erst nach dem Lesen der Änderungen übernehmen.
