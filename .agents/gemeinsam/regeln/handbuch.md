# Handbuch für Kolleg/innen und Mitdokumentieren

`#Handbuch.html` (ganz oben im Repo) ist die Startseite für das Kollegium. Der Einstieg fragt "Was willst du tun?"
und zeigt nur den gewählten Weg: Lernpaket nutzen, Fehler korrigieren oder selbst erstellen. GitHub stellt es nach jedem Push, der es ändert, mit den Paketen zu (ganz oben, neben den Ordnern). Es hat ein
eigenes Layout mit eigenem CSS und JavaScript in der Datei (nicht `Fachunterricht.html`), ist kein E-Learning und
wird nicht als Paket gebaut. Bausteine: Kommentar am Anfang der Datei.

## Mitdokumentieren ist Pflicht
- Wer Skills, Vorlagen, Skripte, Helfer, Regeln, Einstellungen, den Workflow oder `AGENTS.md` ändert, trägt im selben
  Commit oben in `.agents/handbuch/neuigkeiten.txt` eine Zeile ein:
  `TT.MM.JJJJ | ein Satz ohne Technik, aus Sicht der Kolleg/innen`.
- Ändert sich die Bedienung, auch den passenden Abschnitt im Handbuch anpassen.
- `pruefen.py` (vor dem Commit) meldet einen Fehler, wenn das fehlt, und sagt, was zu tun ist. Nur bei rein internen
  Änderungen ohne Bedeutung fürs Kollegium: `pruefen.py --intern` und "[intern]" in der Commit-Nachricht. Auf GitHub
  ist es nur eine Warnung im Lauf (Commits einer KI, erkennbar an der Zeile "Co-Authored-By", `werkzeuge.md`).
- Neue Skills in `.agents/handbuch/skills.txt` eintragen (`Skill | Wofür | Beispiel`). Die `description` im Kopf der
  `SKILL.md` kurz halten (etwa 300 Zeichen, sie steht in jeder Sitzung im Kontext) und **ohne Doppelpunkt mit
  Leerzeichen** schreiben: Sonst wird der Kopf nicht gelesen und der Skill erscheint ohne Beschreibung.
- **"Nimm diese Frage ins Handbuch auf" (Fragen und Fehler von Kolleg/innen):** Den Text des Handbuchs ändern nur
  Werkzeug-Verantwortliche, `.agents/handbuch/fragen.txt` dürfen alle ändern. Darum:
  1. Die Frage sofort im Chat beantworten (aus Handbuch und Regeln).
  2. Beantwortet das Handbuch sie schon: Zeile in `fragen.txt` (`Frage | id des Abschnitts`).
  3. Sonst (und bei einem Fehler im Handbuch) mit dem Skill notizen einen Eintrag in `ToDo/Alle-NOTIZEN.md`:
     Kurztitel beginnt mit `Handbuch-Frage:` bzw. `Handbuch-Fehler:`, Text ist die Frage wörtlich, darunter ein
     Unterpunkt mit der id des passenden Abschnitts und einem kurzen Antwortvorschlag.
  4. Mit "Werkzeug-Verantwortliche: ja" stattdessen gleich den Abschnitt ergänzen und die Zeile in `fragen.txt`
     schreiben; offene Einträge `Handbuch-Frage:`/`Handbuch-Fehler:` so erledigen und abhaken.

## Automatisch, nie von Hand ändern
"Was ist neu" und die Zahl der Lernpakete (aus den Themenordnern in `Unterricht/`, deren `index.html` eine Version trägt), Skill-Liste (ohne Helfer), Häufige Fragen, Seitenleiste,
Kennzahlen und Stand. Das macht `python .agents/handbuch/handbuch.py` (auch über `pruefen.py --erneuern` vor dem Commit
und auf GitHub nach jedem Push, das dann selbst committet). Es prüft Fragen, Links und Pakete und liest die Seiten im
Arbeitsstand (in Git oder neu, nicht ignoriert).

## Stil: so wenig wie möglich
Geschrieben für Kolleg/innen ohne Technikkenntnis, nach Aufgaben gegliedert, kurze Schritte. Das Lehrkraft-Passwort
steht nie im Handbuch.
- **Sichtbar stehen nur Schritte** und das, was alle brauchen. Hintergründe, Sonderfälle und Formeln kommen in einen
  Kasten `<details class="mehr">` ("Zusatzinfos", Aufbau im Kommentar am Anfang der Datei).
- **Nicht ins Handbuch gehört, was die KI selbst weiß oder tut:** Ablageschema, Dateinamen, Helfer, Git-Abläufe,
  Aufbau von `.agents/`. Wer es braucht, fragt die KI.
- Jedes Kapitel trägt `data-weg` (`nutzen`, `korrigieren`, `erstellen` oder `immer`). Neues zuerst einem Weg zuordnen,
  kein neues Kapitel für alle anlegen.
- **Im Handbuch heißt es "die KI", nie ein Produktname** (auch in `neuigkeiten.txt` und `fragen.txt`, `handbuch.py` prüft
  den Produktnamen ohne Ausnahme). Der Hinweis, dass ein bezahltes Abo des Anbieters (Pro oder Plus) unbedingt nötig ist, bleibt
  im Schritt zur Einrichtung stehen. Dateinamen gehören nicht ins Handbuch.
- **Keine Paketliste im Handbuch.** Die Kolleg/innen brauchen die Linkseite: Die Links mit `data-linkseite` führen
  direkt dorthin. Die Adresse enthält einen Schlüssel und steht nur im Handbuch (Entscheidung der Lehrkraft vom
  12.11.2026, das Repo ist privat), sonst nirgends im Repo, nie im Chat und nie in einer Ausgabe. Wird das Repo
  öffentlich, muss sie vorher raus.
- Das Kapitel "Warum wir so arbeiten" (eine Fassung für alle, keine parallelen Versionen) und der Kasten "Warum mit
  Link" unter "Paket per Link einbinden" bleiben sichtbar, nicht in einen Aufklappkasten verschieben.
- Die Häufigen Fragen stehen unsichtbar in der Seite und sind nur über die Suche zu finden. "Was ist neu" zeigt
  nur die neuesten Lernpaket-Änderungen, die Zeilen aus `neuigkeiten.txt` stehen eingeklappt darunter.

## Prüfen
`python .agents/handbuch/handbuch.test.py`, danach die HTML-Prüfung von Hand und einmal im Headless-Browser (gilt auch für Seiten
ohne die Vorlagen, z. B. Übungs-Apps): erste Zeile `<!doctype html>`, Ende `</html>`; `<section`, `<div`, `<table`, `<ol`, `<ul` so oft
wie ihr schließendes Tag (Grep im Zählmodus); keine Platzhalter (`[Titel]`, `[Thema]`, `TODO`), keine Markdown-Zeichen
(`**`, `##`); kein `http://` oder `https://` in `src=` oder `<link`; kein roter Fehlerkasten.

## Selbsttest des Werkzeugs
Ändert sich `AGENTS.md` oder etwas in `.agents/`, `.claude/` oder `.gemini/`, prüft `pruefen.py` zusätzlich: Kopf jedes Skills und Helfers (`name` wie
Ordner bzw. Datei, `description` ohne Doppelpunkt mit Leerzeichen), Verweise auf Dateien in `.agents/` und auf Regeldateien,
Vorlagen unverändert. Eine gewollte Änderung an `<style>` oder `<script>` einer Vorlage bestätigt
`python .agents/gemeinsam/scripts/pruefen.py --vorlage-bestaetigen` (schreibt `.agents/gemeinsam/data/vorlagen-hash.txt`,
mit committen). Rückfall bei einem missglückten Umbau: Git-Tag `werkzeug-stabil` (letzter geprüfter Stand des Werkzeugs).
Nach jedem Push laufen alle Tests auf GitHub ("Werkzeug testen", `einrichtung-admin.md`). Ein Umbau, der an Lernpaketen
und Kursen nichts ändern soll: vorher und nachher `python .agents/gemeinsam/scripts/referenz.py` (baut alles mit
Arbeitsstand und HEAD, muss "alles gleich" melden; einige Minuten).
