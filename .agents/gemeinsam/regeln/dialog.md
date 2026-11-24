# Auswahldialog: Angaben klären (nur was fehlt)

Ein Ablauf für alle Skills. Jeder Skill fragt nur, was er braucht: die Vorlage nur baue-e-learning, Beruf und Hilfsmittel
nur, wo das Schriftfeld sie führt (nicht bei einheit-planen, raster-feedback, moodle-fragenersteller, moodle-test).

## Ablauf
**Auswahldialog:** Fehlen die Pfade zu Aufgaben-PDF und Musterlösungs-PDF (oder zur HTML-Datei), erst im Chat danach fragen. Vorlage, Klasse, Beruf, Fach und Abschnitt per **Auswahldialog** abfragen (`werkzeuge.md`) (EIN Aufruf, Auswahl per
Klick, unter "Other" tippt die Lehrkraft frei). Was die Lehrkraft schon genannt hat, wird nicht gefragt. Nie raten. Ein
Aufruf hat höchstens vier Fragen: Wären es fünf, kommt "Hilfsmittel" in den zweiten Dialog (mit der Niveau-Bestätigung).
**Allgemeinbildende Fächer** (Ethik, Politik und Gesellschaft, Deutsch, Englisch, Religion, Sport): Beruf und
Hilfsmittel nicht fragen, Kurzkopf (`seite.md`); Klasse, Fach und Abschnitt schon (`Unterricht/ALLE10/Eth/BW1/`).

**Nach dem Dialog:** Steht das Fach fest, `faecher.md` lesen. Steht die Klasse fest, gilt `sprache.md` (<!-- AUTO:sprache -->Pflicht in BVJ, BIK und BFS, sonst Richtschnur<!-- /AUTO:sprache -->). Vor dem Dialog lesen: `dialog-niveaus.md`, `.agents/gemeinsam/data/berufe.txt` und die Ausgabe von
`python .agents/gemeinsam/scripts/unterrichtsmaterial.py --liste` (Fächer mit Kürzel aus `faecher.txt` nach Abteilung,
Klasse, Kürzel; bekannte Klassen; vorhandene Abschnitte je Klasse und Fach).

Fragen im Dialog:
1. **Vorlage** (Header "Vorlage"): nur baue-e-learning und nur, wenn nicht genannt. Dann `dialog-vorlage.md` lesen.
2. **Klasse** (Header "Klasse"): Klassenkürzel in Großbuchstaben (`MGF10`, `BFS11`) oder Sammelname für Material mehrerer
   Klassen (`ALLE10` = alle 10. Klassen, `ALLE11`, `ALLE` = alle Jahrgänge, z. B. Schulleitbild). Optionen: höchstens vier,
   die bekannten Klassen aus `--liste`, die zum Material passen, dazu der Sammelname; Nennt das Material eine Klasse,
   steht sie als erste mit "(empfohlen)". Das **Ausbildungsjahr wird nicht gefragt**, es folgt aus der Klasse (`unterrichtsmaterial.py`).
3. **Beruf** (Header "Beruf"): bis zu vier Einträge aus `berufe.txt`, die zum Material passen (sonst die ersten vier).
4. **Fach · Abschnitt** (Header "Fach"): je Fach aus `faecher.txt` (nur die zur Klasse passenden, in Listenreihenfolge)
   der **nächste freie Abschnitt** (höchste `BW<n>` + 1) und der **letzte vorhandene** (für weitere Kapitel derselben
   Woche), höchstens vier Optionen (Label `<Fach voller Name> · Blockwoche 3`, Beschreibung `MGF10, neue Blockwoche (BW1 und
   BW2 vorhanden)`). Die erste Option bekommt
   "(empfohlen)". Arten von Abschnitt (`BW<n>` Blockunterricht, `LS<n>` Tagesunterricht, `M-<Name>`, `R-<Name>`): `ablage.md`. Sagt das Material nicht, welche Art es ist, und gibt es noch keinen
   Abschnitt, fragen.
5. **Hilfsmittel** (Header "Hilfsmittel"), nur wenn das Material keine nennt: die Hilfsmittel aus der Fachregel des Fachs
   (`faecher.md`), sonst `Taschenrechner`, `Formelsammlung`, `Keine`.

Nach der Antwort:
- **Vorlage** für Schritt 4 und 5 merken, im Bericht nennen. **Listen fortschreiben:** Einen neuen Beruf in `berufe.txt`, ein neues Fach in `faecher.txt` eintragen und die Liste
  sortieren (Regeln im Kopf der Dateien, Zahlen natürlich: LF1, LF3, LF10). Kürzel eines neuen Fachs: Lernfelder `LF<Nummer>` mit der Klasse dahinter
  (dieselbe Nummer bedeutet in jedem Beruf etwas anderes), sonst kurz wie `Eth`, `PuG`, `D`, `E`. Im Bericht nennen.
- **Schriftfeld:** Zelle "Lernfeld · Blockwoche" mit dem vollen Namen des Fachs: `<voller Name> · Blockwoche <n>` (bei
  `LS<n>`: `· Lernsituation <n>`, bei `M-`/`R-`: `· <Name>`). **Ablageort:** nach `ablage.md` (`<Fach>` ist das Kürzel).
- Bricht die Lehrkraft ab oder bleibt eine Angabe offen: alles andere fertig bauen, in der Zelle "offen" eintragen,
  unter `Unterricht/Offen/<Thema>/` speichern und die offenen Angaben als Erstes im Bericht nennen.
- **Titel und Untertitel** aus dem Material übernehmen (nur wenn keiner erkennbar ist, fragen).

## Niveaus und Sprachhilfen
Bei neuem Material und beim Umbau per Auswahldialog fragen (Header "Niveaus" und "Sprachhilfen"): `dialog-niveaus.md` lesen.
