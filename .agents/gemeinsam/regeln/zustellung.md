# Pakete, Kurse und Tests: Zustellung und Links

Wie Gebautes zu den Lehrkräften kommt, mit Namen und Orten. Einrichtung und roter Lauf: `einrichtung.md`.
Zustellweg laut Schulprofil (`schule.txt`, `Zustellung`): **<!-- AUTO:zustellung -->download<!-- /AUTO:zustellung -->**.

- **Nur über GitHub.** Nach jedem Push auf `main` baut der Workflow "Bauen und zustellen" jedes Lernpaket, dessen
  Themenordner sich geändert hat, und jeden Kurs, dessen Kursplan oder eine darin ohne Link genannte Datei sich
  geändert hat (Banner, Test-`.mbz`, Dateien, mitgelieferte Lernpakete). Geänderte Test-Ordner (zur Archivierung nach
  `Tests/<gleicher Pfad wie unter Unterricht/>`) und das Handbuch schickt er unverändert mit. Kein Rechner kopiert selbst.
  - `power-automate`: Ein Flow legt alles in den Teamordner (<!-- AUTO:teamordner -->(im Schulprofil keiner, Zustellung "download")<!-- /AUTO:teamordner -->,
    OneDrive/SharePoint), in denselben Unterordner wie die Quelle.
  - `download`: Der Lauf bietet alles als Download an (Actions → Lauf → Artifacts, "Pakete-<Nummer>", Unterordner wie
    unten, GitHub löscht ihn nach 90 Tagen). Nach einem Push nur das Geänderte, alles auf einmal mit "Run workflow" und
    "alle".
- **In Git liegen nur die Quellen.** Ein Lernpaket ist jeder Themenordner, dessen `index.html` eine Version trägt
  (einmal mit dem Skill baue-lernpaket gebaut). ZIP und `.mbz` kommen nie ins Repo und nie von Hand in den Teamordner.
  Im Projektordner gibt es kein `BYCS-SYNC/` (liegt doch einer da, stoppt `pruefen.py`: Ordner löschen). Die Pfade
  `BYCS-SYNC/…` in Kursplänen und Regeln meinen den Ort im Teamordner bzw. im Download.
- **Lokal gebaut ist nur zum Ansehen:** `build-scorm.py` und `build-mbz.py` legen im Temp-Ordner ab
  (`unterrichtsmaterial.gebaut()`, `<Temp>/Unterricht-gebaut/BYCS-SYNC/…`).
- **Gleicher Name wird ersetzt,** der Download-Link bleibt. Der volle Paketname bleibt auch im Unterordner (ein
  heruntergeladenes Paket ist allein erkennbar).
- **Kurse und Tests haben keinen Link:** Die Lehrkraft lädt die `.mbz` aus dem Teamordner bzw. dem Download in die
  Lernplattform hoch (Wiederherstellen). Tests im Kurs behalten das Kennwort aus ihrer `.mbz` (Platzhalter
  "Bitte_neu_vergeben").
- **Vorschau der Tests:** `Vorschau.html` erzeugt `quiz-vorschau.py`; aktuell hält sie `pruefen.py --erneuern` (vor
  dem Commit und auf GitHub).

## Nur bei `power-automate`: Flow und Download-Links
- **Der Flow nimmt nur** `.html`, `.mbz`, `.xml` und `_scorm.zip` an: Andere Dateien in einem Test-Ordner (z. B.
  Bilder) kommen nicht in den Teamordner.
- **Download-Links gibt es nur für Lernpakete.** Jedes Paket im Teamordner bekommt von selbst einen geteilten Link, der
  bei jeder neuen Fassung gleich bleibt. Alle Links stehen auf der Linkseite "ByCS-Links" (Verknüpfung `# ByCS-Links`
  im Teamordner). Die KI holt sie mit `python .agents/gemeinsam/scripts/linkseite.py`, nie abtippen, nie im Repo
  speichern (die Adresse der Linkseite enthält einen Schlüssel). Lernpakete mit Link holt Moodle selbst.
- **Angekommen?** `python .agents/gemeinsam/scripts/kette-pruefen.py --zugestellt`.
- Bei `download` gibt es keine Links und keine Linkseite: Ein Kurs bringt seine Lernpakete mit (Skill baue-kurs), ein
  einzelnes Lernpaket lädt die Lehrkraft als ZIP in die Lernplattform hoch.

## Namen und Orte unter `BYCS-SYNC/` (nur über GitHub, nie im Projektordner, nie in `Unterricht/`)
- Lernpaket: `BYCS-SYNC/Pakete/<Klasse>/<Fach>/<Klasse>_<Fach>_<Abschnitt>_<Thema>_scorm.zip`.
- Kurssicherung: `BYCS-SYNC/Kurse/<Klasse>[/<Fach>]/<Name des Kursplans>.mbz` (ohne Datum, im selben Unterordner wie der
  Kursplan). Tests bleiben in `Unterricht/…/Test-<Thema>/` (in Git).
- `tmp/` im Projektordner ist der lokale Arbeitsordner (Entwürfe, Auszüge), in Git ausgenommen (nur `tmp/.gitkeep`).
  Lokal Gebautes landet im Temp-Ordner und ist nur zum Ansehen.
- **Paketnamen ändern:** nur die Groß-/Kleinschreibung ohne Rückfrage (die Datei im Teamordner wird an Ort und Stelle
  ersetzt, der Link bleibt). Jede andere Änderung am Namen oder Ort legt im Teamordner eine neue Datei mit neuem Link
  an: vorher fragen.
- **Themenordner umbenennen:** erst bauen und committen, dann umbenennen. Sonst findet `version.py` den Commit zu
  "Commit folgt" nicht und zählt die Version nicht hoch.
