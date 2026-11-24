# Mein Unterrichtsprojekt

Die KI liest diese Datei in jeder Sitzung. Hier steht nur, was immer gilt. Alles Weitere steht genau einmal in
`.agents/gemeinsam/regeln/` und wird gelesen, bevor die Arbeit beginnt (Wegweiser).

## Über mich <!-- AUTO:ich (aus schule.txt, nicht von Hand ändern: pruefen.py --erneuern) -->
- Ich unterrichte an einer Berufsschule in Bayern (Lehrplan: Bayerischer LehrplanPLUS, https://www.lehrplanplus.bayern.de).
- Klasse, Beruf, Fach und Abschnitt (Blockwoche, Lernsituation, Modul, Themenreihe) wechseln: Sie kommen jedes Mal aus dem Auswahldialog, nie raten. Unsere Lernplattform: ByCS Lernplattform (BayernCloud Schule, läuft auf Moodle, früher mebis).<!-- /AUTO:ich -->

## Wegweiser: erst lesen, dann arbeiten
Alle Regeldateien liegen in `.agents/gemeinsam/regeln/` und werden überall nur mit ihrem Namen genannt (`seite.md`). Die Skills nennen, welche sie brauchen. Fragen zu Rulesets, Secrets, Flow, Workflow-Einrichtung oder Freigabe beantworten `schutz-admin.md` und `einrichtung-admin.md` (nur auf Nachfrage lesen). Ohne Skill gilt:

| Wenn du … | lies zuerst |
|---|---|
| Unterrichtsmaterial anlegst, ablegst, umbenennst oder etwas in `Ressourcen/` speicherst | `ablage.md` |
| Klasse, Beruf, Fach, Abschnitt, Vorlage oder Niveaus brauchst | `dialog.md` |
| eine Seite (`.html`) baust oder änderst oder eine Vorlage eines Teams (`Vorlagen/<Teamname>/`) anlegst oder änderst | `seite.md` |
| Unterrichtsmaterial für ein bestimmtes Fach baust (z. B. PuG, Lernfelder mit Technischem Zeichnen) | `faecher.md` (nennt die Fachregel, falls es eine gibt) |
| Text schreibst, den Schülerinnen und Schüler lesen (Aufgaben, Infotexte, Rückmeldungen, Testfragen) | `sprache.md` (<!-- AUTO:sprache -->Pflicht in BVJ, BIK und BFS, sonst Richtschnur<!-- /AUTO:sprache -->) |
| eine Seite fertig meldest, ein Paket baust oder committen willst | `abschluss.md` |
| Skills, Vorlagen, Skripte, Regeln, Einstellungen, diese Datei oder das Handbuch änderst | `handbuch.md` |
| wissen musst, wer was ändern darf (Werkzeug, Unterricht und Notizbücher anderer Teams, Notizen), oder GitHub einen Push abweist | `schutz.md` |
| Auswahldialog, Helfer, PDFs, Arbeitsordner oder einen Commit mit Co-Authored-By brauchst | `werkzeuge.md` |
| mit `BYCS-SYNC/`, Teamordner, Download-Links oder Zustellung zu tun hast | `zustellung.md` |
| "Teamordner … nicht gefunden" siehst, die Passwortdatei fehlt, ein Rechner neu ist oder du in einer Cloud-Sitzung im Browser arbeitest | `einrichtung.md` |

## Wie ich Unterrichtsmaterialien möchte
- Sprache der Schülermaterialien: Deutsch, kurze klare Anweisungen. **Immer "Schülerinnen und Schüler"** (richtig gebeugt), wo die lange Form stört "Lernende". Nie "Schüler" allein und nie "Schüler/innen", im ganzen Projekt und in deinen Antworten (`pruefen.py` prüft Seiten und Regeln). Zusammensetzungen wie "Schülersicht" bleiben, wörtliche Zitate aus Leitbild und Qualitätszielen der Schule ("Schüler*innen") auch.
- <!-- AUTO:bewertung (aus schule.txt, nicht von Hand ändern: pruefen.py --erneuern) -->Standard sind drei Niveaus: **Einsteigerniveau** blau, **Prüfungsniveau** rot, **Profiniveau** schwarz. Ohne Niveaus ist in jedem Fach erlaubt, aber nie von selbst: bei neuem Unterrichtsmaterial und beim Umbau im Auswahldialog fragen, außer ich habe es schon gesagt.
- Bewertete Pakete: Einsteigerniveau 40 %, Prüfungsniveau 40 %, Profiniveau 20 % der Punkte. Bestehensgrenze 70 %, auch ohne Niveaus. Einsteigerniveau + Prüfungsniveau (80 %) sind die Mindestanforderung.
- Am Ende eine Lösung für die Lehrkraft, deutlich abgetrennt. Fragen für die Lernplattform werden immer als Test gebaut, es gibt keine Quizze.<!-- /AUTO:bewertung -->

## Was immer gilt
- **Unterrichtsmaterial ist immer EINE Webseite (`.html`)** aus der Vorlage `Fachunterricht.html` oder `Allgemeinbildung.html` (`.agents/gemeinsam/templates/`) oder einer Vorlage eines Teams, die ich per Doppelklick öffne. Nie Markdown. Ausnahmen zum Importieren: `.xml`, `.ics`, `.zip`, `.mbz`. Interne Arbeitsdateien sind `.md`.
- **Ablage:** `Unterricht/<Klasse>/<Fach>/<Abschnitt>/<Thema>/index.html`, Namen nie abtippen (`python .agents/gemeinsam/scripts/unterrichtsmaterial.py "<Ordner>"`). In Git liegen nur die Quellen, die Seite ist klein: Stil und Script der Vorlage in `kern/`, Bilder in `<Thema>/bilder/` (`seite.md`). Lernpakete und Kurssicherungen baut **nur GitHub** nach dem Push (`zustellung.md`).
- **Blöcke und `kern/` nie anfassen:** Die markierten Blöcke und `<style>`/`<script>` der Vorlage bleiben unverändert. Beim bloßen Umbau nie von dir aus neuen interaktiven Code schreiben.
- **Keine externen Ressourcen:** Bilder, Skripte, Stylesheets und Schriften kommen nie von außen. Klickbare Links nach außen sind erlaubt.
- **Lösungen bleiben gesperrt:** nur in `<details class="sol">` oder `<section class="answers">`, mit dem einen Passwort-Hash aus `.agents/gemeinsam/data/solution-password.txt`. Nie ein Passwort im Klartext in eine Seite, nie im Chat, nie im Handbuch. **Der Schülername wird nie eingetippt:** Er kommt aus der Lernplattform, wenn die Seite im SCORM-Paket läuft.
- **Fertig heißt geprüft:** `python .agents/gemeinsam/scripts/seite-pruefen.py <Seite>` besteht, danach öffnen und berichten nach `abschluss.md`. Vor jedem Commit besteht `python .agents/gemeinsam/scripts/pruefen.py --erneuern` (dieselbe Prüfung macht GitHub nach dem Push).
- **Mitdokumentieren:** Änderungen am Werkzeug brauchen im selben Commit eine Zeile in `.agents/handbuch/neuigkeiten.txt` (nur intern: `--intern` und "[intern]" in der Commit-Nachricht).
- **Werkzeug ändern nur Werkzeug-Verantwortliche** (Skills, Vorlagen, Skripte, Regeln, Einstellungen, Workflow, diese Datei, alles außerhalb von `Unterricht/`, `ToDo/`, `Ressourcen/` und `Vorlagen/<Teamname>/`; Liste: `.agents/gemeinsam/data/schutz.txt`), und nur, wenn `python .agents/gemeinsam/scripts/pruefen.py --rechte` "Werkzeug-Verantwortliche: ja" meldet. Sonst den Wunsch weitergeben; eigene Skills im eigenen Skill-Ordner deines Werkzeugs, nie im Projekt. `bycs.werkzeug` setzt nie die KI. Einzelheiten: `schutz.md`.
- **Kein PowerShell** (in `.claude/settings.json` gesperrt): keine `.ps1`-Dateien, keine PowerShell-Befehle in Skills oder Anleitungen, Skripte sind Python 3 oder `sh`. Am Mac in jedem Befehl `python3` statt `python`.

## Git: direkt auf `main` arbeiten
- Wir arbeiten zu mehreren an diesem Repo. Änderungen direkt auf `main` committen und pushen, keinen eigenen Branch, keinen Pull Request (außer ich bitte darum).
- Vor der ersten Änderung einer Sitzung und vor jedem Commit `git pull --rebase` (nach jedem Push committet GitHub das erneuerte Handbuch). Bei einem Konflikt anhalten und fragen, nie raten und nie fremde Änderungen überschreiben.
- **Wann fragen, wann selbst committen** (Ablauf und Wortlaut: `abschluss.md`): Meldet `pruefen.py` "Lernpaket betroffen: ja", immer erst fragen und mein Ja abwarten (nach dem Push ist die Änderung sofort bei den Schülerinnen und Schülern). **Alles andere:** nach bestandener Prüfung selbst committen und pushen und kurz sagen, was gepusht ist.
- Weist GitHub einen Push ab ("repository rule violations"), nie erzwingen und keinen anderen Weg suchen: `abschluss.md`. Lässt die Cloud-Sitzung den Push auf `main` nicht zu, mir das sagen und den Branch der Sitzung nutzen; am Ende erinnern, dass er zusammengeführt oder gelöscht werden muss.

## Datenschutz (immer)
- Nie nach Namen, Noten oder anderen personenbezogenen Daten von Schülerinnen und Schülern fragen oder sie speichern. Eingefügte Schülerarbeiten sind anonymisiert; steht doch ein Name darin, ihn durch "Schülerin oder Schüler A" ersetzen und mich erinnern.
- Nichts auf externe Dienste hochladen. Ausnahmen: Websuchen, um die ich bitte, und Suchen nach Belegen für Lösungsvorschläge (nur Fachbegriffe, keine Schülerdaten); `git push` auf `main`; die Zustellung durch GitHub an den Teamordner (OneDrive/SharePoint) nach jedem Push (Workflow "Bauen und zustellen", Power Automate).

## Hilfreiche Kontextdateien
`Ressourcen/Inhalt.md` (was in `Ressourcen/` liegt), `#Handbuch.html` (Startseite für Kolleg/innen) und `ToDo/` (Notizbücher `ToDo/<Teamname>-NOTIZEN.md` und `ToDo/Alle-NOTIZEN.md`, sonst liegt dort nichts). Die Notizbücher lesen, wenn ich frage, was noch offen ist, oder ein Thema daraus nenne; schreiben nur mit dem Skill `notizen`.
