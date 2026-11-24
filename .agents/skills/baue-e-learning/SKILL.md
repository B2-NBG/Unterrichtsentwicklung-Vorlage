---
name: baue-e-learning
description: Baut aus PDFs (Aufgabenblatt, Musterlösung) ein E-Learning nach Fachunterricht.html oder Allgemeinbildung.html, baut eine bestehende HTML-Datei auf die Vorlage um oder arbeitet ein neueres Skript ein; Lösungen bleiben gesperrt. Verwenden bei E-Learning aus PDFs oder HTML, Umbau, neuem Skript.
---

# PDF oder HTML in ein E-Learning nach Vorlage umwandeln

Du baust aus Unterrichtsmaterial ein E-Learning, das genauso aussieht und funktioniert wie jedes andere Dokument aus der gewählten Vorlage (Aufgaben mit Eingabefeldern, PDF-Export, Hell/Dunkel, Lösungssperre). Das fertige Ergebnis kann danach mit dem Skill **baue-lernpaket** zu einem SCORM-Paket werden.

**Das Grundgerüst (Stil und Script der Vorlage) bleibt unverändert.** Du kopierst die gewählte Vorlage (`.agents/gemeinsam/templates/Fachunterricht.html` oder `Allgemeinbildung.html`) und füllst Kopf und `<main>`. Interaktive Module aus dem Original (3D-Ansicht, Simulationen, Spiele) werden **übernommen, nicht weggelassen** (Schritt 4a). Bei **neuen E-Learnings aus PDFs** darfst du zusätzliches CSS und eigenes JavaScript schreiben, um Aufgaben interaktiv zu machen (Schritt 4b). Die Bausteine stehen im Kommentar am Anfang der Vorlage.

## Zwei Arbeitsweisen
- **A. Aus PDFs:** ein Aufgabenblatt (Schülerversion, zum Ausfüllen) und eine Musterlösung. Beide werden gelesen und zusammengeführt.
- **B. Aus bestehender HTML-Datei:** Inhalt übernehmen, in die Struktur der Vorlage umbauen.

## Zwei Vorlagen (Layout)
- **Fachunterricht** (`Fachunterricht.html`): technisches Schriftfeld, eine lange Seite mit Kapiteln und Niveaus. Für Arbeitsblätter, Lernskripte, Übungen für eine Stunde.
- **Allgemeinbildung** (`Allgemeinbildung.html`): dunkles Kopfband, Schritt-Leiste, eine Bildschirmseite je Schritt, Phasen mit Timer, Ergebnis-Seite (Beispiel: `Unterricht/ALLE10/Eth/BW1/Die-ethische-Brille/index.html`). Für Unterrichtsfolgen über mehrere Stunden.

Beide haben dieselben Funktionen (gleiche Style- und Script-Blöcke). Alles hier gilt für beide, die Unterschiede stehen in Schritt 4c und Schritt 5.

**Vorlagen der Teams** (`Vorlagen/<Teamname>/<Name>.html`, Auswahl im Dialog, Regeln in `seite.md`): Eine Layout-Vorlage wird genauso kopiert und gefüllt wie die beiden oben, ihre Bausteine stehen im Kommentar am Anfang der Vorlage. Eine freie Vorlage hat keine Bewertung, keinen Leerdruck und keinen PDF-Export: Das vor dem Bau sagen und im Bericht nennen.

**Vorlage geändert?** Ablauf in `seite.md` (Abschnitt Vorlage). Markierte Bereiche nie von Hand ändern.

Annahme bei "Schülerlösung": gemeint ist das **Aufgabenblatt für die Schülerinnen und Schüler** (ohne Lösungen). Ist stattdessen eine **ausgefüllte Schülerarbeit** gemeint, frage nach, wofür sie gebraucht wird. Ausgefüllte Arbeiten werden nie als Vorgabewerte in das E-Learning übernommen.

## Teile dieses Skills
| Datei | Inhalt |
|---|---|
| `dialog.md` | Schritt 1: Auswahldialog für alle Skills (Vorlage, Klasse, Beruf, Fach · Abschnitt, Hilfsmittel, Niveaus, Sprachhilfen: `dialog-niveaus.md`), Listen, Ablageort |
| `bausteine.md` | Schritt 4: Bausteine der Vorlage, Regeln für Lösungsvorschläge, Bewertung, Punkte, Schlüssel; 4c Allgemeinbildung |
| `module-grafiken.md` | 4a Module übernehmen, 4b eigene Interaktivität, 4d Grafiken neu zeichnen und putzen |
| `druckfassung.md` | Leeres Arbeitsblatt: was die Vorlage automatisch macht, Papierfassungen (`.print-alt`, `.screen-only`), Katalog Bildschirm → Papier |
| `skript-uebernahme.md` | einen neueren Quelltext (z. B. ein Skript) in bestehende Abschnitte übernehmen, Zuordnung SuS/Lös, Rückmeldung an den Ersteller |

Regeln für alle Skills in `.agents/gemeinsam/regeln/`: `ablage.md`, `seite.md`, `sprache.md`, `abschluss.md` (vor dem Bauen lesen).

Werkzeuge in `.agents/gemeinsam/scripts/`: `sync-vorlage.py` (Vorlagenblöcke und Schrift fürs Zeichnen einsetzen), `bauen.py` (Kern und Bilder auslagern, einzelne Datei bauen), `seite-pruefen.py` (Prüfung plus Browser-Test), `medien-einsetzen.py` (eingebettete Bilder auflisten, ablegen, einsetzen), `pw-hash.py` (nur die Lehrkraft führt es aus).

Helfer (`werkzeuge.md`): `skript-abgleicher` (je Seite einen Quelltext einarbeiten, parallel einsetzbar) und `seiten-pruefer` (fertige Seite prüfen, nur lesend).

**Fachregeln** (z. B. Technisches Zeichnen mit Schrift und Festlegungen): `faecher.md`.

## Schritt 1 – Angaben klären (nur was fehlt)
Ablauf, Fragen, Listen und Ablageort: **`dialog.md`** (vorher lesen). Fehlende Pfade (PDFs, HTML-Datei, Skript) im Chat fragen. Nach dem Einlesen nach Niveaus und Sprachhilfen fragen (Fall B).

## Schritt 2 – Einlesen
**PDFs:** mit dem Lesewerkzeug der KI seitenweise lesen (höchstens 20 Seiten pro Aufruf, `werkzeuge.md`).
- Meldet Read, dass `pdftoppm` fehlt: Poppler (enthält `pdftoppm`) muss auf diesem Rechner installiert sein. Sag das der Lehrkraft und biete als Ausweg an, den Text des PDFs hier einzufügen.
- Liefert eine Seite keinen Text (Scan, Foto): Das kann ich nicht zuverlässig lesen. Sag es und bitte um die Textfassung.
- Namen oder andere personenbezogene Daten im PDF: nicht übernehmen, durch "Schülerin oder Schüler A" ersetzen und die Lehrkraft erinnern (Datenschutz laut AGENTS.md).

**HTML (Arbeitsweise B):** Datei lesen (große Dateien in Teilen, Bilder als `data:`-Adressen nicht ausgeben; zum Ansehen auspacken, siehe Schritt 4d). Das Original wird nie verändert.

## Schritt 3 – Zusammenführen (Arbeitsweise A)
1. Aus dem Aufgabenblatt eine Liste bauen: Aufgabennummer, Titel, Aufgabentext, Punkte/Hinweise, Abbildungen, Antwortart.
2. Aus der Musterlösung zu jeder Aufgabe die Lösung, den Lösungsweg und die Bewertungshinweise.
3. Über die Aufgabennummer zuordnen. Melde der Lehrkraft am Ende: Aufgaben ohne Lösung, Lösungen ohne Aufgabe, abweichende Nummerierung. Nichts erfinden: Fehlt eine Lösung, gilt die Regel **Lösungsvorschläge** in Schritt 4 (nur Aussagen mit Quelle, bei Meinungsaufgaben nur Vergleichskriterien; für eine Fundstelle darfst du ohne Rückfrage im Web suchen). Lässt sich keine Quelle finden, keinen Vorschlag schreiben und darauf hinweisen.

## Schritt 4 – Umbau in Bausteine der Vorlage
- Bausteine, Lösungsvorschläge, Bewertung (`data-ok`, `data-keys`, `data-score`), Punkte (`data-gewicht`), Speicherschlüssel (`data-k`), Abbildungen, Formeln: **`bausteine.md`**.
- Allgemeinbildung-Vorlage (Schritte, Phasen, Karten): **`bausteine.md`, Schritt 4c**.
- Interaktive Module übernehmen (4a), eigene Interaktivität bei neuen E-Learnings (4b), alte Grafiken neu zeichnen oder putzen (4d): **`module-grafiken.md`**.
- **Jede Aufgabe muss sich auf Papier lösen lassen** (leeres Arbeitsblatt): Interaktive Teile bekommen `screen-only` und eine Papierfassung `div.print-alt` nach dem Katalog in **`druckfassung.md`**, Textfelder genug Schreiblinien (`data-zeilen`).
- Neuerer Quelltext für vorhandene Abschnitte (z. B. ein Skript für mehrere Kapitel): **`skript-uebernahme.md`**.

## Schritt 5 – Bauen
Vorgehen nach `seite.md`:
1. Vorlage kopieren, `sync-vorlage.py --datei <Seite> --schreiben` und `bauen.py --auslagern <Seite> --schreiben` ausführen, genau nach `seite.md` (Abschnitt Vorlage).
2. `<title>`, Schriftfeld (Titel, Untertitel, Beruf, Ausbildungsjahr, Lernfeld · Blockwoche, Hilfsmittel) füllen. Der `<title>` ergibt auch den Namen der PDF-Datei ("Als PDF speichern"): Bei Kapiteln `<Kapitel> – <Thema> – <Titel im Schriftfeld>`, z. B. `Werkstück 4 – Formelemente, Bemaßung und Oberflächen – Technisches Zeichnen 1`; der Titel aus dem Schriftfeld am Ende entfällt im Dateinamen. Name-Zelle und `<span class="ver">` bleiben, wie sie sind (`seite.md`). Bei `Allgemeinbildung.html` zusätzlich die Zeile über dem Titel füllen (z. B. `Ethik · 10. Klasse · <Kurzname der Schule>`, `schule.txt`); das Logo bleibt.
3. Lösungssperre: `<meta name="loesung-hash">` nach `seite.md` füllen (ein Hash für alles, nie ein Passwort im Klartext oder im Chat). Übernommene Module mit eigener Passwortabfrage prüfen ebenfalls gegen diesen Hash.
4. `<main>` mit den Bausteinen aus Schritt 4 füllen.
5. Speichern als **`Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/index.html`** (z. B. `Unterricht/MGF10/LF1/BW4/Pythagoras-1-Grundlagen/index.html`, siehe Schritt 1). Der Ordner ist direkt als Quelle für baue-lernpaket geeignet. Bilder stehen als `data:`-Adressen in der Seite; `bauen.py --bilder <Seite> --schreiben` legt sie als Dateien in `bilder/` ab (`seite.md`). Nur große Medien (Video, 3D-Modell) liegen als Datei im selben Ordner.

## Schritt 6 – Prüfen (Pflicht)
1. `python .agents/gemeinsam/scripts/seite-pruefen.py <Seite> --arbeitsordner <Arbeitsordner>/pruefen` (Prüfung aus `abschluss.md` plus Browser-Test). Screenshot und Leerdruck ansehen (PDF-Seiten im Arbeitsordner mit pypdfium2 in Bilder umwandeln). Hinweise beheben oder im Bericht nennen.
2. **Vollständigkeit:** Anzahl der Aufgaben im HTML = Anzahl im Original. Jede zugeordnete Lösung steht in einer Aufgabe oder in `section.answers`.
3. **Lösungen verborgen:** Mit Grep prüfen, dass in `<main>` keine Lösungstexte außerhalb von `details.sol`, `section.answers`, `.sol-only` stehen (Stichproben mit markanten Lösungswörtern).
4. **Eingabefelder:** Jede Aufgabe mit Antwort hat ein Feld, jedes `<select>` beginnt mit leerer Option, kein Feld hat einen Vorgabewert, jedes Feld hat einen eigenen `data-k` (kein Schlüssel doppelt).
5. **Niveaus:** Jede Aufgabe liegt in einem `level`-Block (außer die Lehrkraft hat "Ohne Niveaus" gewählt).
6. **Nur Allgemeinbildung.html:** Schrittnummern in den Überschriften lückenlos, letzter Schritt ist `section.step.result` mit `#stepResult`, jede `phasebar` hat ein gültiges `data-form`, kein `<h3>` in `.teacher`/`.sol-only`. Im Headless-Browser einmal durch alle Schritte klicken (Leiste und Weiter).
7. **Abbildungen:** Jede neue Fassung neben dem Original ansehen (Vergleich aus Schritt 4d). Jedes Maß, Symbol und jede Beschriftung des Originals einzeln abhaken. Nichts ist abgeschnitten oder überdeckt, keine Lösung steht im Bild oder im `alt`, kein Scan steht ungeputzt in der Seite.
8. **Leerdruck:** Jede Aufgabe ist auf Papier lösbar (`druckfassung.md`, Abschnitt 6).
Fehler beheben, erneut prüfen, dann in einer Zeile sagen, welche Prüfungen bestanden sind.

## Schritt 7 – Abschluss
Kurz und konkret:
- Öffnen, Standardsatz und Commit-Frage nach `abschluss.md`.
- Welche Vorlage (Fachunterricht oder Allgemeinbildung) und was übernommen wurde (Anzahl Aufgaben, Niveaus, Lösungen verknüpft; bei Allgemeinbildung Anzahl Schritte und Minuten je Stunde).
- **Lösungsvorschläge:** bei welchen Aufgaben ein Vorschlag mit Quelle steht, bei welchen nur Vergleichskriterien und welche keinen haben (Organisationsaufgaben, keine Quelle gefunden).
- **Abbildungen:** welche neu gezeichnet, welche nur geputzt (mit Grund), welche unverändert geblieben sind, und jede inhaltliche Korrektur (z. B. ergänztes Ø).
- **Offene Punkte:** fehlende Abbildungen, Aufgaben ohne Lösung, nicht übernommene Interaktivität, gemachte Annahmen (z. B. Niveau-Einteilung, "Schülerlösung" = Aufgabenblatt).
- Nächster Schritt anbieten: "Soll ich daraus mit baue-lernpaket ein SCORM-Paket für die Lernplattform bauen?"

## Grenzen (offen sagen)
- Abgabe, Punkte (40/40/20, bestanden ab 70 %), Bewertung und was Lernende nach der Abgabe sehen: `.agents/skills/baue-lernpaket/punkte.md`. Kurz: Nach der Abgabe sehen sie alle Lösungsvorschläge in `details.sol` (auch im PDF); was sie nie sehen sollen (Bewertungsraster, Hinweise für die Lehrkraft), gehört in `section.answers` oder `.sol-only`. Aufgaben ohne hinterlegte Lösung zählen als "bearbeitet = volle Punkte".
- Eigene interaktive Module (Schritt 4a/4b) werden nach der Abgabe nicht automatisch gesperrt; ihr Ergebnisfeld schon, und es wird nichts mehr gemeldet.
- Die Lösungssperre hält nur ab, wer nicht in den Quelltext schaut. Für Prüfungen sind die Lösungen in einer getrennten Datei besser aufgehoben.
- Neu zeichnen und putzen geht nur, wo das Original lesbar ist: Unlesbare Scans und sehr komplexe Zeichnungen lassen sich ohne bessere Vorlage nicht vollständig übernehmen.
- Beide Vorlagen speichern Eingaben nur in der Lernplattform (SCORM). Per Doppelklick geöffnet, gehen Eingaben beim Neuladen verloren; `Allgemeinbildung.html` merkt sich dort nur den zuletzt geöffneten Schritt.

## Datenschutz
Nach AGENTS.md. Felder für Gruppenmitglieder: Schritt 4.
