---
name: kurs-umgestalten
description: Gestaltet einen gewachsenen Reiterkurs der Lernplattform aus seiner Sicherung neu (Blockplan je Klasse, Farbschema-Baukasten, Kursbild, passender Kursbeginn) mit farbiger Anleitung zum Wiederherstellen. Verwenden bei "Kurs umgestalten", "Blockplan in den Kurs", "Farbschema für den Kurs".
---

# Kurs umgestalten (Sicherung → neue Fassung)

Für Kurse, die in der Lernplattform gewachsen sind (Format Onetopic mit Reitern, Unterreitern, Unterabschnitten, eigenen
Aktivitäten). Inhalte bleiben, wie sie sind. Geändert werden nur Freigaben (Blockplan), Icons, Kopfbänder, Reiterfarben,
Abschnittsflächen, Kursbild, Kursbeginn und Name. Neue Kurse aus `Unterricht/` baut der Skill **baue-kurs**.

Skripte in `.agents/skills/kurs-umgestalten/scripts/` (nur Standardbibliothek, am Mac `python3`). Kursbild und
Baukasten brauchen Chrome oder Edge.

**Ablage:** Sicherungen, Baukasten und Anleitungen nur lokal in `Ressourcen/Kurssicherungen-ByCS/` (`.gitignore`, sie
enthalten Fragen und Lösungen). In Git: der Kursplan `Ressourcen/Kursumbau/Kursumbau-<Kurs>.json` und der Blockplan
`Ressourcen/Blockplaene/Blockplan-<Klasse>-<Schuljahr>.json` (Vorbild für beide: MGF10).

## Schritt 1 – Sicherung und Überblick
1. Die Lehrkraft sichert den Kurs in der Lernplattform **ohne Nutzerdaten** und legt die `.mbz` nach `Ressourcen/Kurssicherungen-ByCS/`.
2. `uebersicht.py --sicherung <mbz> [--plan <Kursplan>]` zeigt Kursbeginn, Reiter, Unterabschnitte, Inhalte und was im
   Kursplan oder Blockplan fehlt.

## Schritt 2 – Kursplan (nur was fehlt)
- Gibt es keinen: `uebersicht.py --sicherung <mbz> --entwurf Ressourcen/Kursumbau/Kursumbau-<Kurs>.json`, dann ergänzen:
  je Reiter `icon`, bei Hauptreitern `bereich` (A Allgemein, F/B/I die drei farbigen Bereiche, T Tests; Unterreiter erben,
  Test-Unterreiter dürfen F/B/I tragen), `satz` (ein Satz „Darum geht's“ für das Kopfband, Lernende lesen ihn: `sprache.md`),
  optional `titel`. Dazu `bereiche` (Icon + Name), `unterabschnitte` (Name → Icon), `kurs.kopfzeile`, `kursbild`.
  Den Entwurf als kurze Liste zeigen und bestätigen lassen.
- Reiter werden **ohne Icon** verglichen. Heißt ein Reiter in der Lernplattform inzwischen anders: Eintrag umbenennen, nie raten.
- **Blockplan** (falls Reiter je Klasse aufgehen sollen): PDFs der Schule nach `Ressourcen/Blockplaene/`, die Montage je
  Block übertragen (`bloecke`, `gruppenname` wie die Klassengruppen im Kurs, `abschnitte`: Reiter → Nummer der Schulwoche;
  die Zuordnung fragen). Pfad im Kursplan unter `blockplan`. Ohne Blockplan: `"blockplan": null`.

## Schritt 3 – Farbschema
`baukasten.py --plan <Kursplan> --sicherung <mbz>` und die Datei öffnen. Der Baukasten zeigt den echten Kurs. Die
Lehrkraft wählt Farben und Stil und gibt den **Gestaltungscode**. Ihn unter `gestaltungscode` eintragen. Bei
Kursbild „Foto-Banner“ (`bf`) braucht `kursbild.banner` Titel, Stufe, Untertitel und ein Foto aus `Ressourcen/Bilder/`.

## Schritt 4 – Kursbeginn erfragen (Pflicht, nie raten)
Lehrkräfte können den Kursbeginn in der Lernplattform meist **nicht ändern** (Schloss-Symbol, so in der ByCS). Moodle verschiebt beim Wiederherstellen
alle Termine um den Abstand zwischen dem Kursbeginn der Sicherung und dem des Zielkurses. Darum fragen: „Welcher
Kursbeginn steht im Zielkurs unter Einstellungen?“ Bei einem neuen Kurs: erst anlegen lassen, dann ablesen.

## Schritt 5 – Bauen und prüfen
```
python .agents/skills/kurs-umgestalten/scripts/umgestalten.py --plan <Kursplan> --sicherung <mbz> --kursbeginn TT.MM.JJJJ
```
Setzt Blockplan, Kursbild, Gestaltung, Kursbeginn und die nächste freie Fassung `V<n>` (Datei-, Kurz- und Vollname; die
Lernplattform lehnt vergebene Namen ab) und prüft mit `build-mbz.py --pruefen`. Meldungen, die schon die Sicherung aus der Lernplattform hat
(z. B. Fragenkategorien), zählen nicht. Exitcode 0 = keine neuen Fehler. Dann die **Anleitung**
`Anleitung-<Kurzname>-V<n>.html` öffnen und der Lehrkraft nennen: Sie enthält Kursbeginn und die Soll-Termine zum
Nachsehen. `--kursbild-behalten` lässt das Kursbild der Sicherung stehen.

## Schritt 6 – Abschluss
- Pfade von `.mbz` und Anleitung nennen. Kursplan und Blockplan nach `abschluss.md` committen und pushen, nie eine `.mbz`.
- Wiederherstellen macht die Lehrkraft nach der Anleitung. Danach nachfragen, ob die Termine stimmen.

## Grenzen und Hilfe
- Nur Format Onetopic. Icons aus (`jn`) ist nicht umgesetzt. Abschnitt 0 lässt sich nicht sperren.
- Termine verschoben → Kursbeginn passte nicht: neue Fassung mit dem richtigen `--kursbeginn`.
- Fehlermeldung beim Wiederherstellen: Wortlaut anfordern, dann `.agents/skills/baue-kurs/umfang.md`.
- Nur ein Teil gewünscht: `blockplan-einsetzen.py` (nur Freigaben), `kursbild.py` (nur Bild).
