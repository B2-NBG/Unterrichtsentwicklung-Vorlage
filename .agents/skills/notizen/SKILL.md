---
name: notizen
description: Pflegt die Notizbücher in ToDo/ (je Team eines, eines für alle), mit Eintragen, Offenes zeigen, Thema nachschlagen, Abhaken, nur so, wie es der Schutz erlaubt. Verwenden bei "notier", "merk dir", "Notizzettel", "Notizbuch", "was ist noch offen", "ToDo" oder einem Thema aus den Notizen.
---

# Notizbücher pflegen

## Die Notizbücher
Alle liegen direkt in `ToDo/`, sonst liegt dort nichts (keine Ordner, kein Material: das gehört nach `Ressourcen/`).
- `ToDo/<Teamname>-NOTIZEN.md`: Notizbuch eines Teams (Teamname wie auf GitHub, z. B. `ToDo/pug-NOTIZEN.md`).
  Schreiben dürfen nur Mitglieder dieses Teams und Werkzeug-Verantwortliche.
- `ToDo/werkzeug-verantwortliche-NOTIZEN.md`: Notizbuch der Werkzeug-Verantwortlichen.
- `ToDo/Alle-NOTIZEN.md`: gemeinsames Notizbuch für alle.
- Lesen dürfen alle alles.

## Zuerst
- `git pull --rebase`. Dann `python .agents/gemeinsam/scripts/pruefen.py --rechte`: Die Zeile „Teams“ nennt die
  eigenen Teams (nur in deren Notizbücher schreiben), die Zeile „Werkzeug-Verantwortliche“ sagt, ob alles erlaubt
  ist, die Zeile „Ersteller in Notizen“ steht so in jedem neuen Eintrag (eigener Name und GitHub-Login). Meldet sie
  „Login: unbekannt“ (GitHub nicht erreichbar), keinen neuen Eintrag schreiben, sondern sagen, dass es geht, sobald
  GitHub erreichbar ist. `git config unterricht.werkzeug` nie selbst lesen oder setzen.
- Der Schutz steckt nicht in diesem Skill, sondern in den Rulesets auf GitHub und in `pruefen.py` („Notizbücher“ und
  „Notizschutz“ in `schutz.md`). Dieser Skill schreibt nur so, dass die Prüfung besteht.
- Notizbücher und `ToDo/` nie löschen.
- Schutz laut Schulprofil: **<!-- AUTO:schutz -->aus<!-- /AUTO:schutz -->**. Bei `aus` (eine Lehrkraft allein, `schutz.md`)
  gibt es nur `ToDo/Alle-NOTIZEN.md`: ohne Auswahldialog dorthin schreiben, als Ersteller genügt der Name (kein Login
  nötig, kein Notizschutz). Was unten zu Teams und fremden Einträgen steht, entfällt dann.

## Welches Notizbuch
- **Lesen** („was ist offen“, ein Thema nachschlagen): die Notizbücher der eigenen Teams und `Alle-NOTIZEN.md`, im
  Bericht je Notizbuch getrennt. Die Notizbücher anderer Teams nur, wenn die Lehrkraft danach fragt.
- **Schreiben:** Nennt die Lehrkraft das Notizbuch („notier für PuG …“, „für alle“), dorthin. Sonst: Gibt es nur
  ein eigenes Team-Notizbuch, dorthin. Gibt es mehrere, im Auswahldialog fragen (Header „Notizbuch“, höchstens
  vier Optionen: die eigenen Team-Notizbücher, die zum Inhalt passen, und „Alle“). Nie raten.
  Fragen und Fehler zum Handbuch („Handbuch-Frage:“, „Handbuch-Fehler:“, Ablauf in `handbuch.md`) gehen immer nach
  `Alle-NOTIZEN.md`, ohne Auswahldialog.
- **Notizbuch fehlt:** Hat das eigene Team noch keines, anlegen: `ToDo/<Teamname>-NOTIZEN.md` mit der Überschrift
  `# Notizbuch <Teamname>`, der Zeile mit den Markierungen und den Abschnitten „## Eingang (unsortiert)“ und
  „## Erledigt“. Für ein fremdes Team nie eines anlegen.

## Form der Einträge (in jedem Notizbuch)
- Neuer Eintrag: eine neue Zeile unter „## Eingang (unsortiert)“, unter den vorhandenen Einträgen:
  `- [ ] **Kurztitel (JJJJ-MM-TT, Ersteller: <Name>, @<Login>):** Text.` Eingerückte Unterpunkte (`  - …`) sind
  erlaubt. Die Lehrkraft nicht mit Rückfragen bremsen, der Eingang darf unsortiert sein.
- Markierungen `[ ]` offen, `[>]` in Arbeit, `[x]` erledigt. Reihenfolge = Priorität. Abschnitte: „Eingang
  (unsortiert)“, Themenabschnitte, „Erledigt“ (unten, mit Datum, neueste oben).
- Abhaken heißt: `[x]`, Datum davor, den Eintrag nach „## Erledigt“ verschieben (oben unter die Überschrift).
  Einträge nicht löschen, sondern abhaken.

## Was erlaubt ist
- **Im Notizbuch des eigenen Teams:** alles (eintragen, ändern, sortieren, abhaken, auch Einträge anderer
  Teammitglieder). Sortieren nur auf Wunsch, den Wortlaut dabei nicht ändern.
- **In `Alle-NOTIZEN.md` (Notizschutz):** neue Einträge im Eingang; eigene Einträge (bei „Ersteller:“ steht der
  eigene Login, bei älteren ohne Login der eigene Name) ändern, auf `[>]` setzen, abhaken; den eigenen Login
  nachtragen. Fremde Einträge ändern, sortieren, Überschriften und Text außerhalb der Einträge ändern dürfen nur
  Werkzeug-Verantwortliche.
- **Im Notizbuch eines fremden Teams:** nichts schreiben. Den Wunsch als eigenen Eintrag in `Alle-NOTIZEN.md`
  notieren („Bitte an das Team <Teamname>: …“) oder als kurzen Text formulieren, den die Lehrkraft weitergibt.
- Mit „Werkzeug-Verantwortliche: ja“ ist in allen Notizbüchern alles erlaubt.

## Datenschutz
Keine Namen, Noten oder anderen personenbezogenen Daten von Schülerinnen und Schülern in die Notizen. Werden welche
eingefügt: durch „Schülerin oder Schüler A“ ersetzen und daran erinnern.

## Abschluss
`python .agents/gemeinsam/scripts/pruefen.py --erneuern` muss bestehen. Meldet sie „Notizschutz“ oder „Notizbuch des
Teams“, die Änderung so zurücknehmen, dass nur Erlaubtes übrig bleibt. Notizen sind kein Lernpaket: danach nach
`AGENTS.md` selbst committen und pushen und kurz sagen, was gepusht ist. Bei reinen Notiz-Einträgen entfällt die
Zeile in `neuigkeiten.txt`.
