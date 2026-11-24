---
name: einheit-planen
description: Plant eine Unterrichtseinheit mit einem Team von Helfern (Lehrplanprüfung, Stundenplan, Termine unter Beachtung des Schulkalenders, Kalenderdatei, Qualitätsprüfung). Verwenden, wenn die Lehrkraft eine Einheit, Unterrichtsreihe oder Stundenfolge ab einem Startdatum planen möchte.
---

# Eine Einheit mit dem Helferteam planen

Du bist der **Orchestrator**. Du erledigst die Detailarbeit nicht selbst.
Du gibst jeden Schritt an einen Fachhelfer (`werkzeuge.md`: ohne Unterhelfer führst du ihn selbst aus), reichst die Ergebnisse weiter und fügst alles zusammen.

## Schritt 0 – Angaben klären (nur was fehlt)
**Klasse, Fach und Abschnitt** (für den Ablageort) per Auswahldialog nach `dialog.md`. Der Unterrichtsplan ist ein Dokument nur für die Lehrkraft: kurzer Kopf, nach Beruf und Hilfsmittel nicht fragen (`seite.md`). Abschnitt = die Blockwoche oder Lernsituation, in der die Einheit beginnt.

**Niveaus** im selben Auswahldialog (`dialog-niveaus.md`, Fall A).

Der Rest in EINER Nachricht im Chat:
- Thema
- Startdatum
- Unterrichtstage und -zeiten (z. B. "Mo 08:00 und Do 09:45, 45 Minuten")
- Anzahl der Stunden (Standard: 8)

Ablageort: `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>-Unterrichtsplan/` (`ablage.md`).

Gib den Auftrag in 3 Zeilen wieder, dann starte.

## Schritt 1 – Lehrplan → `lehrplan-agent`
Bitte ihn um die passenden LehrplanPLUS-Kompetenzen und 3–5 Lernziele zu diesem Thema und dieser Jahrgangsstufe.

## Schritt 2 – Stunden → `unterrichts-planer`
Gib ihm den Auftrag (mit der Wahl bei den Niveaus) und das Lehrplanergebnis. Er liefert den Stundenplan mit Aufbau.

## Schritt 3 – Termine → `kalender-agent`
Gib ihm das Startdatum, die Unterrichtstage/-zeiten, die Anzahl der Stunden, die Stundentitel aus Schritt 2 und den Pfad für die `.ics`-Datei: `<Ablageort>/<Thema>-Stunden.ics`.
Er überspringt Ferien, schreibt die `.ics`-Datei und liefert die Terminliste. Erst nach Schritt 2 starten: Er braucht die Stundentitel.

## Schritt 4 – Bauen (zusammenfügen)
`<Ablageort>/index.html` als EINE Webseite schreiben: `.agents/gemeinsam/templates/Fachunterricht.html` kopieren, `sync-vorlage.py --datei <Seite> --schreiben` und `bauen.py --auslagern <Seite> --schreiben` ausführen, kurzen Kopf setzen (`<div class="tb kurz">`, `seite.md`) und `<main>` füllen:
```html
<h1>Einheit: [Thema]</h1>
<p class="lead">[Fach], [Jahrgangsstufe] · [erstes Datum] bis [letztes Datum] · [n] Stunden</p>
<h2>Lehrplanbezüge und Lernziele</h2> ... (alles Ungeprüfte in einer .box kennzeichnen)
<h2>Übersicht</h2> <table> Nr. | Datum | Stundentitel | Ziel | Hauptaktivität </table>
<h2>Stunden</h2> je Stunde ein <h3>, mit dem Plan des Helfers unterrichts-planer und dem echten Datum
<h2>Übersprungene Termine</h2> Ferien und Grund
```

Dann den Plan mit `python .agents/gemeinsam/scripts/seite-pruefen.py <Seite>` prüfen (`abschluss.md`).

## Schritt 5 – Prüfen (Pflicht) → `qualitaets-pruefer`
Gib ihm den Pfad des Unterrichtsplans und der `.ics`-Datei und die Wahl bei den Niveaus. Behebe jeden Punkt unter **Muss korrigiert werden**.
Nenne der Lehrkraft die **Wünschenswert**-Vorschläge, setze sie aber nicht ungefragt um.

## Schritt 6 – Abschluss
Sage der Lehrkraft in höchstens 8 Zeilen: die beiden Dateinamen ("Doppelklick auf die .html-Datei öffnet den Plan; die .ics-Datei öffnen, um die Stunden in den Kalender zu übernehmen"), das erste und letzte Stundendatum,
welche Ferien übersprungen wurden, und einen Vorschlag
(z. B. "Das Arbeitsblatt für Stunde 3 mit /baue-arbeitsblatt erstellen").
