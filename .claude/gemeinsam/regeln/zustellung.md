# Pakete, Kurse und Tests: `BYCS-SYNC/`, Zustellung und Links

Wo Gebautes liegt, was in Git ist, wie es in den Teamordner kommt. Lesen, wenn es um `BYCS-SYNC/`, den Teamordner,
Download-Links oder die Zustellung geht. Einrichtung und roter Lauf: `einrichtung.md`.

- **Regel: Pakete und Kurse entstehen nur über GitHub.** Nach dem Push baut GitHub sie und legt sie über Power Automate
  in den Teamordner (SharePoint `B2-BS-Kollegium - Dokumente/BYCS-SYNC`). Im Projektordner gibt es keinen Ordner
  `BYCS-SYNC/`: `build-scorm.py` und `build-mbz.py` legen am Rechner nur im Temp-Ordner ab (`unterrichtsmaterial.gebaut()`,
  `<Temp>/B2-ByCS-gebaut/BYCS-SYNC/…`), zum Prüfen und Ansehen. Nie ein ZIP oder eine `.mbz` von Hand in den Teamordner
  oder ins Repo kopieren. Liegt doch ein `BYCS-SYNC/` im Projektordner (alter Rest), stoppt `pruefen.py`: Ordner löschen.
  Die Pfade `BYCS-SYNC/…` in Kursplänen und Regeln meinen den Ort im Teamordner.

- **SCORM-Pakete** liegen immer in `BYCS-SYNC/Pakete/<Klasse>/<Fach>/`, nie in `Unterricht/`:
  `<Klasse>_<Fach>_<Abschnitt>_<Thema>_scorm.zip`. Der volle Name bleibt auch im Unterordner (ein heruntergeladenes
  Paket ist allein erkennbar). Ein Paket gleichen Namens wird ersetzt.
- **Kurssicherungen:** `BYCS-SYNC/Kurse/<Klasse>[/<Fach>]/<Name des Kursplans>.mbz` (z. B. `Kurse/ALLE10/PuG/Kurs-ALLE10-PuG.mbz`),
  ohne Datum, im selben Unterordner wie der Kursplan unter `Unterricht/` (Schema wie bei Paketen und Tests). Quelle ist
  der Kursplan (in Git); die `.mbz` liegt nicht in Git (`BYCS-SYNC/` steht ganz in
  `.gitignore`). GitHub baut einen Kurs neu, wenn sich sein Kursplan oder eine Datei ändert, die er ohne Link nennt
  (Banner, Test-`.mbz`, Dateien, mitgelieferte Lernpakete). Lernpakete mit Link holt Moodle selbst. Lokal gebaut nur zum
  Ansehen (im Temp-Ordner). Tests im Kurs behalten das Kennwort aus ihrer `.mbz` (Platzhalter "Bitte_neu_vergeben").
- **Lernpakete liegen nicht in Git** (`BYCS-SYNC/Pakete/` steht in `.gitignore`). Ein Lernpaket ist jeder Themenordner,
  dessen `index.html` eine Version trägt (einmal mit dem Skill Baue-Lernpaket gebaut). Nach jedem Push auf `main` baut
  GitHub die Pakete neu, deren Themenordner sich geändert hat, und stellt sie über Power Automate in denselben
  Unterordner im Teamordner `B2-BS-Kollegium - Dokumente/BYCS-SYNC` zu (Workflow "Bauen und zustellen",
  `.github/workflows/paket-zustellen.yml`). Das lokal gebaute ZIP (Temp-Ordner) ist nur zum Ansehen da.
  Prüfen, ob alles angekommen ist: `python .claude/gemeinsam/scripts/kette-pruefen.py --zugestellt`.
- **Test-Ordner und das Handbuch** stellt derselbe Workflow nach dem Push zu, wenn sie sich geändert haben (sie liegen
  in Git und werden unverändert geschickt). Kein Rechner kopiert selbst in den Teamordner, Git-Hooks gibt es nicht mehr.
  Der Flow nimmt nur `.html`, `.mbz`, `.xml` und `_scorm.zip` an: Andere Dateien in einem Test-Ordner (z. B. Bilder)
  kommen nicht in den Teamordner.
- **Download-Links gibt es nur für Lernpakete.** Jedes Paket im Teamordner bekommt von selbst einen geteilten Link
  (Power Automate), der bei jeder neuen Fassung gleich bleibt. Alle Links stehen auf der Linkseite "ByCS-Links"
  (Verknüpfung `# ByCS-Links` im Teamordner). Claude holt sie mit `python .claude/gemeinsam/scripts/linkseite.py`,
  nie abtippen, nie im Repo speichern (die Adresse der Linkseite enthält einen Schlüssel).
- **Kurse und Tests haben keinen Link:** Die Lehrkraft lädt die `.mbz` direkt aus dem Teamordner in die ByCS hoch
  (Wiederherstellen).
- **Tests** bleiben in `Unterricht/…/Test-<Thema>/`. GitHub stellt geänderte Test-Ordner nach dem Push zur Archivierung nach
  `BYCS-SYNC/Tests/<gleicher Pfad wie unter Unterricht/>` zu. In die ByCS kommen sie nur durch die Wiederherstellung
  (Test-`.mbz` aus dem Teamordner) der Lehrkraft. Die `Vorschau.html` erzeugt `quiz-vorschau.py`; aktuell hält sie `pruefen.py --erneuern` (vor dem Commit und auf GitHub).