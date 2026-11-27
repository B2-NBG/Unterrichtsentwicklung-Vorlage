# Abschluss: prüfen, öffnen, berichten, Paket, Commit

Die Reihenfolge gilt für jede Seite, egal aus welchem Skill: erst prüfen, dann der Lehrkraft zeigen, dann committen
(bei Lernpaketen erst nach ihrem Ja). So kommt nichts Ungeprüftes zu den Schülerinnen und Schülern.

## 1. Prüfen (vor "Seite ist fertig", immer)
`python .agents/gemeinsam/scripts/seite-pruefen.py <Seite> --arbeitsordner <absoluter Pfad>/pruefen` prüft die Quelle und
die gebaute Fassung in einem Lauf (statisch und im Headless-Browser, die Meldung nennt jede Prüfung) und legt
Screenshot, Leerdruck und PDF-Export als Datei ab: ansehen.
- **Seiten ohne die Vorlagen** (Übungs-App, Handbuch): von Hand prüfen, Liste in `handbuch.md`, "Prüfen".
- Besteht eine Prüfung nicht: korrigieren, wiederholen, dann in einer Zeile sagen, was bestanden ist.
- **Mehrere Seiten auf einmal:** je Seite einen Helfer `seiten-pruefer` parallel (`werkzeuge.md`; er berichtet nur, behoben wird danach).
- Meldet die Lehrkraft eine leere Seite oder einen roten Fehlerkasten: um die kopierte rote Meldung bitten, Ursache
  beheben, erneut prüfen.

## 2. Zur Kontrolle öffnen (nach inhaltlichen Änderungen)
Das E-Learning nach bestandener Prüfung im integrierten Browser öffnen: `code -r "Unterricht/<…>/index.html"` (Quelltext: Rechtsklick → "Öffnen mit…" → "Text-Editor"). Bei mehreren vorher fragen (Auswahldialog, `werkzeuge.md`): **Alle öffnen**, **Eine exemplarisch** (typische wählen, sagen welche), **Keine öffnen**.

## 3. Berichten
Standardsatz (ein Skill kann einen kürzeren vorgeben): "Doppelklick auf `Unterricht/<…>/index.html` zum Öffnen. Mit dem
Button 'Als PDF speichern' lädst du ein PDF herunter. Im Lehrkraft-Modus druckt 'Leeres Arbeitsblatt drucken' eine
unausgefüllte Fassung für Papier (auch als PDF speicherbar)." Dazu offene Punkte und Annahmen nennen.

## 4. Paket, Prüfung vor dem Commit, Commit
- Ein Lernpaket baut der Skill baue-lernpaket (`build-scorm.py --source <Themenordner> --aenderung "…"`). Der Text bei
  `--aenderung` erscheint im Handbuch: verständlich fürs Kollegium formulieren. Eine Hauptversion warnt das Skript, weitersagen.
- Vor jedem Commit: `git pull --rebase`, dann `python .agents/gemeinsam/scripts/pruefen.py --erneuern` (prüft alles, erneuert
  Handbuch und Test-Vorschau). Fehler beheben, erneuerte Dateien mit committen. Rein interne Änderung ohne Bedeutung
  fürs Kollegium: `--intern` und "[intern]" in der Commit-Nachricht. Änderungen am Werkzeug brauchen im selben Commit
  eine Zeile in `.agents/handbuch/neuigkeiten.txt` (`handbuch.md`). Die Commit-Nachricht endet mit der Zeile `Co-Authored-By:` (`werkzeuge.md`).
- Die letzte Zeile von `pruefen.py` entscheidet:
  - **"Lernpaket betroffen: ja"**: fragen: "Committen und pushen? Nach dem Push ist die Änderung sofort bei den
    Schülerinnen und Schülern (über den Download-Link im Kurs)." Erst nach dem Ja committen und pushen.
  - **"nein"**: selbst committen und pushen, danach in einem Satz sagen, was gepusht ist. Kurse und Tests erreichen die
    Schülerinnen und Schüler erst, wenn die Lehrkraft sie in der Lernplattform wiederherstellt.
- Nach dem Push prüft GitHub dasselbe noch einmal, baut Lernpakete und Kurse und stellt sie zu (Teamordner oder Download, etwa
  eine Minute, `zustellung.md`). Lernpakete und Kurssicherungen werden nie committet. Der Lehrkraft sagen: Schlägt der
  Lauf fehl, kommt eine Mail von GitHub, und es wird nichts zugestellt. Kontrolle bei Bedarf:
  `python .agents/gemeinsam/scripts/kette-pruefen.py --zugestellt`.
- **GitHub weist den Push ab** („GH013: Repository rule violations“), als Ganzes (`schutz.md`): „File path is restricted“ heißt Werkzeug
  oder Unterricht eines fremden Teams, „File size limit exceeded“ oder „File extension is restricted“ eine Datei über 5 MB bzw. `.h5p`/`.zip`
  (aus den Commits nehmen, verkleinern oder weglassen). Nie erzwingen, nie einen anderen Branch oder Weg suchen, keine Rulesets ändern (meist: die gesperrte Änderung aus den Commits nehmen, Wunsch weitergeben). Anhalten, `git log origin/main..HEAD --stat` zeigen, die gesperrten Dateien nennen und fragen.
