# Einrichtung: neuer Rechner, Teamordner, Passwort, im Browser arbeiten

Nur lesen, wenn etwas fehlt oder ein Rechner neu eingerichtet wird (auch bei Kolleg/innen). Workflow, Secrets, Flow und
Rulesets: `einrichtung-admin.md` (nur auf Nachfrage).

## Teamordner (nur bei Zustellung `power-automate`)
Zustellweg laut Schulprofil: **<!-- AUTO:zustellung -->download<!-- /AUTO:zustellung -->** (bei `download` entfallen dieser Abschnitt und
"Linkseite", die Pakete kommen als Download des Laufs, `zustellung.md`).
In den Teamordner <!-- AUTO:teamordner -->(im Schulprofil keiner, Zustellung "download")<!-- /AUTO:teamordner --> (OneDrive/SharePoint) stellt nur GitHub zu, nach jedem Push:
Lernpakete (`Pakete/<Klasse>/<Fach>/`), Kurse (`Kurse/<Klasse>[/<Fach>]/`), Tests (`Tests/…`) und das Handbuch. Dafür braucht ein
Rechner den Teamordner nicht. Am Rechner wird er nur gelesen: Download-Links für den Kursbau (`linkseite.py`), die
Prüfung `kette-pruefen.py --zugestellt` und das Hochladen von Kursen und Tests in die Lernplattform.

**Prüfen und einrichten:** `python .agents/gemeinsam/scripts/linkseite.py --teamordner` (am Mac `python3`) zeigt, wo
der Teamordner liegt, oder gibt die Anleitung aus (Link zum Ordner im Web, "…" → "Synchronisieren", am Mac
Festplattenvollzugriff für VS Code, sonst "Operation not permitted"; die KI kann das Fenster öffnen:
`open "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"`). Die Anleitung der Lehrkraft ganz
weitergeben, nach ihrem "fertig" erneut prüfen. Liegt der Ordner an einer ungewöhnlichen Stelle:
`git config bycs.ziel "<Pfad zum Ordner BYCS-SYNC>"`. Nachzuholen ist nichts: GitHub stellt auch ohne Teamordner zu.

Im Teamordner wird nie gelöscht: Umbenannte oder entfernte Pakete, Kurse und Tests bleiben dort liegen, bis die
Lehrkraft sie löscht.

## Roter Lauf (GitHub schickt eine Mail)
Im Protokoll des Workflows "Bauen und zustellen" stehen die Fehler (`::error::` bzw. `FEHLER:`). Meist stimmt der
Steckbrief oder die Version nicht (am Rechner beheben, pushen), ein Kurs wartet noch auf den Download-Link eines
neuen Pakets (Lauf nach 10 Minuten mit "Re-run jobs" wiederholen) oder der Flow antwortet nicht (nur
`power-automate`: Ausführungsverlauf in Power Automate ansehen, dann "Re-run jobs"). Ist die Prüfung rot, wird nichts zugestellt (Ausnahme: `schutz-admin.md`,
"Zurückhalten").

## Linkseite (nur bei `power-automate`)
Die Download-Links der Lernpakete holt `python .agents/gemeinsam/scripts/linkseite.py`. Die Adresse liest es aus der
Umgebung `BYCS_LINKSEITE`, aus `git config bycs.linkseite` oder aus der Verknüpfung `# ByCS-Links` im Teamordner (sie
enthält einen Schlüssel: nie ins Repo, nie in den Chat). Die Linkseite verlangt ein Passwort: Auf GitHub steht es in
der Adresse im Secret (`…&pw=…`). Am Rechner fragt `linkseite.py` beim ersten Mal in einem kleinen Fenster danach und
merkt es in `.git/config` (`git config bycs.linkpasswort`), auch wenn die KI das Skript startet. Nie im Chat nach dem
Passwort fragen und es nie ausgeben. Meldet es "ohne Link", liegt das Paket noch nicht im Teamordner oder OneDrive ist
noch nicht fertig.

## Lehrkraft-Passwort
- Der Hash steht in `.agents/gemeinsam/data/solution-password.txt` (Zeile `hash=`). Die Datei liegt im Repo, damit alle
  Rechner und GitHub denselben Hash nutzen; das Passwort selbst steht nirgends.
- Fehlt die Datei oder ist `hash=` leer: die Lehrkraft bitten, `python .agents/gemeinsam/scripts/pw-hash.py` (am Mac
  `python3`) selbst auszuführen, ohne Argument (das Passwort wird verdeckt abgefragt; als Argument lehnt das Skript es
  ab), und die Datei zu committen. Das Passwort wird nie im Chat eingegeben und steht nie im Handbuch. Bis dahin bleibt
  die Meta-Angabe leer, die Lösungen bleiben gesperrt.

## Im Browser arbeiten (Cloud-Sitzung)
- **Dev Container / Codespaces:** gibt es in diesem Repo nicht und sind nie Voraussetzung. Keinen `.devcontainer/` anlegen.
- **Cloud-Sitzung der KI** (Web-Oberfläche des Anbieters): Terminal und Python sind da, die Passwortdatei kommt mit dem Repo.
  Fehlt sie doch, bekommen Lösungen keinen Hash: vor dem Fertigmelden sagen. Lässt die Sitzung den Push auf `main` nicht zu: AGENTS.md, Abschnitt Git.
  Der Push kommt bei GitHub unter dem eigenen Konto an, Rulesets und Teams gelten wie am Rechner. Die Prüfung vor dem
  Commit kennt dort aber weder Login noch Teams (keine gespeicherte Git-Anmeldung oder ein Zugang, der keine Teams lesen
  darf, Git-Name der Cloud-Sitzung): Werkzeug und neue Notizen gehen aus einer Cloud-Sitzung nicht. Unterricht geht:
  Die Prüfung meldet "Teams unbekannt" und warnt höchstens, verbindlich prüft GitHub nach dem Push.
- **Grenzen im Browser:** Seiten öffnet man über die Vorschau statt per Doppelklick; der Teamordner fehlt (Kurse und
  Tests zum Wiederherstellen im Browser herunterladen: aus SharePoint bzw. aus dem Lauf auf GitHub); ohne installierten Browser läuft nur die statische Prüfung.
- **vscode.dev / github.dev** (Taste `.` im Repo): nur zum Lesen. Korrekturen laufen immer über die KI (am Rechner
  oder in einer Cloud-Sitzung), nie von Hand im Browser: Dort gibt es kein Terminal, keine Prüfung vor dem Commit und keinen Bau durch die KI.

## Skripte
Python 3, nur Standardbibliothek (am Mac `python3`), oder `sh`. Kein PowerShell. Für den Browser-Test braucht
`seite-pruefen.py` einen installierten Browser (Edge, Chrome oder Chromium); das Lesen von PDFs braucht, wenn die KI kein eigenes Lesewerkzeug hat, Poppler (`pdftotext`, `pdftoppm`; `werkzeuge.md`).
