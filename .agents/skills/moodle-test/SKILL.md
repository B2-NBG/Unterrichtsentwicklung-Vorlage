---
name: moodle-test
description: Baut aus geprüften Testfragen (Moodle-XML aus moodle-fragenersteller) eine fertige Test-Aktivität (.mbz) samt Anleitung; Arbeitszeit, Punkte, Noten und Safe Exam Browser sind eingestellt. Verwenden bei "Test für die Lernplattform", "fertiger Test", "Test zum Wiederherstellen", "mbz für den Test".
---

# moodle-test: fertige Test-Aktivität zum Wiederherstellen

Ziel: eine `.mbz` (Aktivitätssicherung), die in der Lernplattform als fertiger Test "Test - <Thema>" wiederhergestellt wird, mit allen Fragen in seiner eigenen Fragensammlung. Kein Fragenimport und kein Einrichten von Hand mehr. Dazu die Anleitung `index.html`.

**Ausnahmen beim Dateiformat:** Die `.mbz` ist zum Hochladen da, nicht zum Lesen. Die Anleitung `index.html` beginnt nicht mit `Fachunterricht.html`, sondern wird aus `templates/test-anleitung.html` erzeugt (Look der Moodle-Testseite, kein Namensfeld, kein Lehrkraft-Modus, nur für die Lehrkraft).

## Woher die Einstellungen kommen
`templates/Test-Vorlage.mbz` ist eine Sicherung eines fertig eingerichteten Tests aus der Lernplattform (Moodle 5.2.4). Alles kommt unverändert daraus:
1 Versuch, Verhalten "Spätere Auswertung", Überprüfung nur mit Punkten, 6 Fragen pro Seite, freie Navigation, Antworten mischen, Kennwort "Bitte_neu_vergeben", Safe Exam Browser Pflicht, Notenstufen als Gesamtfeedback "Note 1" bis "Note 6" (ab 92/81/67/50/30 % der Höchstpunktzahl, wie die Notenskala im Kurs).
Je Test neu gesetzt werden nur:
- Name "Test - <Thema>",
- **Arbeitszeit** (wird jedes Mal abgefragt),
- die Fragen in der Reihenfolge der XML, Punkte je Frage aus `<defaultgrade>` (Lückentext: Summe der Lückengewichte),
- **Höchstpunktzahl = Summe der Fragenpunkte**, automatisch, und die Grenzen der Notenstufen mit denselben Prozentsätzen dazu.

Andere Einstellungen gewünscht (z. B. ohne Safe Exam Browser, andere Notenstufen)? Die Lehrkraft richtet einen Test in der Lernplattform so ein, sichert ihn (Test öffnen → "Mehr" → "Sicherung", ohne Nutzerdaten) und gibt der KI die `.mbz`. Sie ersetzt `templates/Test-Vorlage.mbz`, der Code bleibt gleich, die Anleitung liest die Einstellungen ebenfalls aus der Vorlage. Danach `build-test-mbz.test.py` laufen lassen (vergleicht mit dem Beispieltest 3D-Druck; mit einer anderen Vorlage zeigt er die geänderten Einstellungen als Abweichung, das ist dann gewollt).

## Schritt 1 – Prüfen (Fragen)
- Die Fragen kommen aus dem Skill **moodle-fragenersteller** (Moodle-XML, "Ohne Niveaus") und haben das **Review** hinter sich: Die Lehrkraft hat die `Vorschau.html` durchgesehen, die Fragen ausgewählt und freigegeben. Fehlt das, zuerst moodle-fragenersteller bzw. die Vorschau öffnen und auf das Okay warten.
- In der XML stehen genau die Fragen des Tests. Fragen, die nicht in den Test sollen, vorher aus der XML entfernen (danach `quiz-vorschau.py` erneut).
- Unterstützte Fragetypen: multichoice, truefalse, shortanswer, matching, numerical, multianswer (Lückentext), gapselect, ddwtos. Freitext (`essay`, `aitext`) und Bilder gehen nicht.

## Schritt 2 – Angaben klären (Namen und Arbeitszeit)
- Thema und **Arbeitszeit in Minuten** per Auswahldialog (`werkzeuge.md`), nur was fehlt. Ablageort wie im Skill moodle-fragenersteller (Klasse, Fach, Abschnitt).
- Namensmuster (Schreibweise der Dateien nach `ablage.md`):
  - Aktivität in der Lernplattform: `Test - <Thema>` (z. B. "Test - Praxismodul 3D-Druck"),
  - Ordner `Unterricht/<Klasse>/<Fach>/<Abschnitt>/Test-<Thema>/` (Zustellung und Vorschau erkennen Ordner, die mit `Test-` beginnen; dorthin kommen nur `.html`, `.mbz` und `.xml`),
  - Fragen `Fragen-<Thema>.xml`, Test `Test-<Thema>.mbz`, Anleitung `index.html`, Vorschau `Vorschau.html`,
  - Kategorie in der XML `$course$/top/Standard für Test - <Thema>`. Im Test landen alle Fragen in dieser Standardkategorie, eine eigene Unterkategorie gibt es nicht.
  Heißen Ordner, Datei oder Kategorie noch anders, mit `git mv` umbenennen und die Kategorie anpassen.

## Schritt 3 – Bauen
```
python .agents/skills/moodle-test/scripts/build-test-mbz.py <Ordner>/Fragen-<Thema>.xml --thema "<Thema>" --zeit <Minuten> [--abschnitt <n>]
```
. Legt `Test-<Thema>.mbz` und `index.html` in den Ordner, zeigt Fragen, Punkte und Zeit und prüft die Sicherung (Verweise, Lückentexte, Punkte gleich Höchstpunktzahl, Notenstufen lückenlos, Archivindex). `--abschnitt` ist die Nummer des Kursabschnitts, in den der Test beim Wiederherstellen kommt (z. B. Termin 4 = 4); ohne Angabe wie in der Vorlage. Gibt es den Abschnitt nicht, legt Moodle den Test in den ersten Abschnitt, die Lehrkraft verschiebt ihn dann.
`--thema` ist der Titel mit Umlauten und Leerzeichen, der Ordner heißt dazu `Test-<Thema als Ordnername>` (das Skript prüft das und nennt den richtigen Namen). Beim erneuten Bau kann `--thema` entfallen, es steht in der Anleitung `index.html`.
Meldet das Skript einen Fehler, nennt es die Frage: diese in der XML korrigieren, dann neu bauen. Eine fertige Datei nachprüfen: `--pruefen <datei.mbz>`.
Nach Änderungen am Skript oder an der Vorlage: `python .agents/skills/moodle-test/scripts/build-test-mbz.test.py` (Rundlauf gegen die Vorlage, muss "alles gleich" melden).

## Schritt 4 – Prüfen (Pflicht)
Die `index.html` entsteht automatisch: Infobox wie beim Teststart, Schritte zum Wiederherstellen und Ergänzen (Kennwort, Zeitraum, Safe Exam Browser), Einstellungen als Formularabschnitte, Fragenliste mit Seiten und Punkten wie auf der Moodle-Seite "Fragen", Notenstufen mit Punktgrenzen. Nie von Hand ändern: Texte und Aussehen in `templates/test-anleitung.html` bzw. im Skript (`schreibe_anleitung`) ändern und neu bauen.
Prüfen: `python .agents/gemeinsam/scripts/seite-pruefen.py <Ordner>/index.html`. Die Prüfung erkennt die Anleitung (Test-Ordner neben der `.mbz`) und lässt Leerdruck und PDF-Export weg (die Seite hat keinen PDF-Knopf, gedruckt wird mit "Drucken"). Sie muss bestehen. Den Screenshot ansehen, dann `code -r "<Ordner>/index.html"` zur Kontrolle.

## Schritt 5 – Abschluss
Der Lehrkraft nennen: `Test-<Thema>.mbz` zum Wiederherstellen in der Lernplattform, `index.html` (Anleitung) und `Vorschau.html` (Fragen ohne Upload ansehen) per Doppelklick. Dann nach `abschluss.md` prüfen und selbst committen und pushen (ein Test erreicht die Schülerinnen und Schüler erst nach der Wiederherstellung, keine Rückfrage nötig). Etwa eine Minute nach dem Push archiviert GitHub den ganzen Ordner unter `FREIGABE-SYNC/Tests/` (Teamordner oder Download).

## Grenzen (offen sagen)
- Die Sicherung folgt genau der Vorlage aus der Lernplattform, der Rundlauf-Test ergibt für den Beispieltest dieselben Fragen und Einstellungen. Ob jede neue Sicherung fehlerfrei einspielt, zeigt erst die Wiederherstellung im Testkurs.
- Die Test-`.mbz` kann einzeln wiederhergestellt werden oder mit dem Skill baue-kurs gleich in eine Kurssicherung kommen (`"typ": "test"`).
