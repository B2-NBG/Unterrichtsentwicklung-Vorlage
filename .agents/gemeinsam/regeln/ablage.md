# Ablage und Namen

Gilt für alles in `Unterricht/`, `FREIGABE-SYNC/` (Gebautes, `zustellung.md`), `ToDo/` und `Ressourcen/`. Die Regel steht als Code in
`.agents/gemeinsam/scripts/unterrichtsmaterial.py`, `pruefen.py` prüft sie vor jedem Commit und auf GitHub.

## Ordnerschema
`Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/index.html`, z. B. `Unterricht/MGF10/LF1/BW2/Toleranzen-1-Pruefen-Messen-Lehren/`.

| Ebene | Regel | Beispiele |
|---|---|---|
| Klasse | Klassenkürzel in Großbuchstaben oder Sammelname | `MGF10`, `BFS11`, `ALLE10`, `ALLE11`, `ALLE` |
| Fach | Kürzel aus `.agents/gemeinsam/data/faecher.txt`. Der volle Name steht nur im Schriftfeld und im Handbuch. | `LF1`, `Eth`, `PuG` |
| Abschnitt | `BW<n>` Blockwoche, `LS<n>` Lernsituation, `M-<Name>` Modul, `R-<Name>` Themenreihe | `BW2`, `LS3`, `M-3D-Druck` |
| Thema | sprechend, nie gekürzt, nie mit `_` | `Toleranzen-1-Pruefen-Messen-Lehren` |

- **Namen nie abtippen:** Paketname, Titel und Steckbrief der Seite (`<meta name="klasse|fach|abschnitt|thema">`)
  entstehen aus dem Ablageort und aus `<title>`. `python .agents/gemeinsam/scripts/unterrichtsmaterial.py "<Ordner>"`
  zeigt sie und sagt, ob der Ort zur Regel passt (Zeichen, `_` nur zwischen den vier Feldern, `BW<n>` statt `B<n>`).

## Art des Unterrichtsmaterials im Ordnernamen
| Unterrichtsmaterial | Ordner | Skill |
|---|---|---|
| E-Learning | `<Thema>/` | baue-e-learning |
| Arbeitsblatt | `<Thema>-Arbeitsblatt/` | baue-arbeitsblatt |
| Übungs-App | `<Thema>-Uebung/` | uebungs-app |
| Testvorbereitung | `<Thema>-Testvorbereitung/` | baue-testvorbereitung |
| Test | `Test-<Thema>/` mit `Fragen-<Thema>.xml`, `Test-<Thema>.mbz`, `index.html` (Anleitung), `Vorschau.html` | moodle-fragenersteller, moodle-test |
| Unterrichtsplan | `<Thema>-Unterrichtsplan/` (mit `.ics`) | einheit-planen |
| Feedback | `<JJJJ-MM-TT>-<Aufgabe>-Feedback/` (bleibt lokal, `.gitignore`) | raster-feedback |
| Kursplan | eine Datei, kein Ordner: `Unterricht/<Klasse>/<Fach>/Kurs-<Klasse>-<Fach>.json` oder `Unterricht/<Klasse>/Kurs-<Klasse>.json` (mehrere Fächer). Mehrere Kurse am selben Ort: Zusatz anhängen (`Kurs-ALLE-BerHan-3D-Druck.json`). Nie eine Jahreszahl im Dateinamen: Das Schuljahr steht im Plan (`vollname` "… SJ 2026/2027", `kurzname` "… 26/27") | baue-kurs |

**Keine Quizze, immer Tests:** Wünscht die Lehrkraft Fragen für die Lernplattform (auch "Quiz"), entsteht ein Test "Ohne
Niveaus". Kein `-Quiz`-Ordner, kein Lernpfad mit Niveaus. In der Lernplattform heißt der Test "Test - <Thema>".

## Gebautes
Lernpakete und Kurssicherungen (Namen, Umbenennen) entstehen nur über GitHub unter `FREIGABE-SYNC/`: `zustellung.md`. Tests bleiben in
`Unterricht/…/Test-<Thema>/`. `tmp/` ist der lokale Arbeitsordner (nicht in Git).

## Schreibweise von Ordner- und Dateinamen
Gilt auch für SCORM-Pakete und das PDF aus "Als PDF speichern". `unterrichtsmaterial.py` prüft Zeichen, erstes Zeichen
groß und Umlaute; von Hand gilt (vor dem Speichern prüfen):
- Deutsche Rechtschreibung: Nomen und Nominalisierungen groß, Verben, Adjektive, Artikel und Bindewörter klein
  (`Stueckliste-und-Zeichnungen-lesen`, `Unser-Leitbild-kennen-und-leben`), Abkürzungen wie
  üblich (`ISO`, `IHK`, `BW1`). Gibt es einen Seitentitel, dessen Schreibweise übernehmen. Umlaute als ae/oe/ue/ss.
- Technische Namen bleiben (`index.html`, `_scorm.zip`, `imsmanifest.xml`, `scorm-api.js`, Skripte, `.agents/`,
  `.github/`, übernommene Dateien aus fremden Paketen in `Ressourcen/`).
- Ist ein vorhandener Name falsch geschrieben, ihn korrigieren und die Verweise darauf anpassen (AGENTS.md, Regeln,
  Skills, Notizbücher). Unter Windows über einen Zwischennamen umbenennen (`git mv name name.__tmp__`, dann `git mv
  name.__tmp__ Name`), sonst erkennt Git die Änderung nicht.

## Ressourcen
`Ressourcen/` ist ein **Baukasten, kein Archiv**: Bausteine (Bauskripte, SVG, verkleinerte Fotos, kurze PDF-Auszüge,
Kursbanner) ohne Rückfrage nach Thema ablegen, **höchstens 1 MB je Datei**; **Originale der Lehrkraft** (Office-Dateien,
ganze Skripte, Archive) **nicht aufheben**, nur `tmp/`. Vorher den Kopf von `Ressourcen/Inhalt.md` lesen (Einzelheiten,
Eintrag jeder neuen Datei). Fachquellen und ihren Vorrang nennt die Fachregel (`faecher.md`).

## Dateiformate
Interne Arbeitsdateien (Notizen, Festlegungen, Wegweiser, Regeln) sind `.md`, nie `.txt` (Datendateien für Skripte wie `faecher.txt` bleiben). Jeder
Klassen- und Fachordner hat eine Platzhalterdatei `.gitkeep`: Werkzeug, nie löschen, ändern oder verschieben; neue legen
nur Werkzeug-Verantwortliche an.
