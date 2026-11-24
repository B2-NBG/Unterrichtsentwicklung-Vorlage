# Fächer: welche Fachregel gilt

Nach dem Auswahldialog steht das Fach fest. Steht es in der Tabelle, die genannte Datei lesen (zusätzlich zu
`seite.md`), sonst gibt es keine Fachregel. Nur die eine Datei zum Fach lesen, nie alle.

| Fach (Kürzel aus `faecher.txt`) | lies zuerst |
|---|---|
| (noch keine: Beispiel) Lernfelder, sobald technisch gezeichnet wird | `faecher/<kürzel klein>.md` mit Fachquellen, Festlegungen, Hilfsmitteln und der Schrift fürs Zeichnen (`<meta name="schrift" content="zeichnen">`, Ordner im Schulprofil) |

Neue Fachregel: Datei `faecher/<kürzel klein>.md` anlegen und hier eine Zeile eintragen. Was für alle Fächer gilt,
gehört nicht hierher, sondern in `seite.md` oder eine eigene Regel.
