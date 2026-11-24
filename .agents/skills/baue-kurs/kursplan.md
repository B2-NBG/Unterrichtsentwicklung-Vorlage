# Kursplan schreiben: Layout, Links, Gestaltung, Felder

Teil des Skills baue-kurs (Ablauf in `SKILL.md`). Lesen, wenn ein Kursplan neu entsteht oder geändert wird (nicht für einen bloßen Neubau).

## Layout aus dem Inhalt ableiten
Der Ordnerbaum bestimmt den Kursaufbau:
- Dateien für Allgemeines (Kursinfo, Ablauf) → Abschnitt 0. Sie liegen als normale Seite im Schema, z. B. `Unterricht/<Klasse>/<Fach>/<Abschnitt>/Kursinfo/index.html`, nie lose neben dem Kursplan.
- Jeder Abschnitts-Ordner (`BW1`, `BW2`, …, `LS<n>`; bei einem Modul `M-…` jeder Termin) → ein Abschnitt, in numerischer Reihenfolge (BW2 vor BW10). Der Abschnittsname enthält immer auch den Titel der Einheit, nie nur die Nummer: `BW1-Ethische Brille` (wie im Ethikkurs), bei Terminen `Termin 1 – 3D-Druck und CAD-Grundlagen`. Den Titel aus den Seiten auslesen (`<h1>` bzw. `<title>`) oder von der Lehrkraft nehmen.
- Jede Datei direkt im Abschnitts-Ordner (PDF, HTML, Bild, Office-Datei) → eine Ressource. Titel aus dem Dateinamen (Unterstriche zu Leerzeichen), oder den Titel nehmen, den die Lehrkraft nennt.
- Ein Unterordner mit `index.html` (ein E-Learning-Kapitel, z. B. `BW1/Werkstueck-1-Aufbau-und-Funktion/index.html`, ein Arbeitsblatt `…-Arbeitsblatt/` oder eine Übungs-App `…-Uebung/`) → eine Aktivität. Gibt es dazu ein **SCORM-ZIP**, wird das ZIP die Aktivität (Punkte und Abgabe in Moodle), sonst die `index.html` als Datei. SCORM-ZIPs liegen immer in `BYCS-SYNC/Pakete/<Klasse>/<Fach>/` (`<Klasse>_<Fach>_<Abschnitt>_<Thema>_scorm.zip`, siehe baue-lernpaket). Pfad und Namen zum Ordner nennt `python .agents/gemeinsam/scripts/unterrichtsmaterial.py "<Ordner>"`, im Zweifel entscheidet die Startdatei: Die `index.html` im ZIP ist die des Ordners plus die Zeile mit `scorm-api.js`. Fehlt das ZIP, anbieten, es mit baue-lernpaket zu bauen.
- Dokumente nur für die Lehrkraft (Unterrichtsentwurf, Lösungen, Bewertungsraster, Ordner `…-Unterrichtsplan/`) → Datei mit `"versteckt": true`, nie sichtbar für Schülerinnen und Schüler.
- Test-Ordner `Test-…/` → nur die `Test-<Thema>.mbz` als Aktivität mit `"typ": "test"`, in den Abschnitt, in dem der Test geschrieben wird (z. B. Termin 4). Fehlt die `.mbz`, anbieten, sie mit dem Skill moodle-test zu bauen. Anleitung `index.html`, `Vorschau.html` und `Fragen-….xml` aus dem Test-Ordner nie übernehmen (die Vorschau enthält alle Lösungen).
- Nie übernehmen: Ordner `…-Feedback/` (enthalten Auszüge aus Schülerarbeiten), Fragen-Dateien `.xml` (stecken schon in der Test-`.mbz`) und Kalenderdateien `.ics`.

**Download-Links der Lernpakete (nur bei Zustellung `power-automate`, `zustellung.md`):** Jedes ZIP unter `BYCS-SYNC/Pakete/` bekommt im Teamordner von selbst einen eigenen geteilten Link (Power Automate, Form `https://…/download.aspx?share=…&x=.zip`). Die Links stehen nicht im Repo, sondern auf der Linkseite "ByCS-Links". Bei `download` entfällt das: kein `link`, die ZIPs kommen mit (ein `"link": "linkseite"` bricht dann mit einer Meldung ab).
- Im Kursplan bei jedem SCORM-Paket `"link": "linkseite"` eintragen. Das Skript holt den Link beim Bau selbst (über `.agents/gemeinsam/scripts/linkseite.py`, Adresse aus der Verknüpfung `# ByCS-Links` im Teamordner). Nie einen Link abtippen, raten oder in den Kursplan schreiben.
- Vorher prüfen, ob jedes Paket einen Link hat: `python .agents/gemeinsam/scripts/linkseite.py`. Fehlt einer, ist das Paket noch nicht gepusht oder OneDrive noch nicht fertig: erst pushen, kurz warten, noch einmal prüfen. Auf GitHub wartet der Kursbau nach einem neuen Paket bis zu 5 Minuten auf den Link. Nur wenn die Lehrkraft es so will, das Paket ohne `link` mitliefern und das im Bericht sagen.
- Links aus einem vorhandenen Kurs prüfen (z. B. ob ein Kurs noch alte Links nutzt): `python .agents/skills/baue-kurs/scripts/build-mbz.py --links <Sicherung.mbz>` ordnet jeden Link über die Prüfsumme dem passenden ZIP zu.
- Ein E-Learning mit eigenen Dateien daneben: Der Kurs bekommt die gebaute Fassung der Seite (Kern und Bilder eingebettet, `bauen.py`). Liegen große Medien (Video, 3D-Modell) daneben, funktioniert die Seite nur als SCORM-Paket: dann das ZIP nehmen, nie die einzelne HTML. Fehlt das ZIP, warnen und anbieten, es mit baue-lernpaket zu bauen. Vor dem Bauen mit Grep prüfen, ob `src=` oder `href=` auf Dateien außerhalb zeigt (`data:`, `http`, `#` sowie `kern/` und `bilder/` sind in Ordnung).

**Gestaltung („wie die Unterlagen“):** Abschnittstexte übernehmen das Design der Unterlagen, das Kursbild kommt aus dem Skill kursbanner (Schritt 1). Moodle entfernt `<style>`-Blöcke, darum nur **Inline-Stile** (`style="…"`) mit den Schulfarben aus dem Schulprofil (`python .agents/gemeinsam/scripts/profil.py`) und den Farben der Vorlage (`.agents/gemeinsam/templates/Allgemeinbildung.html`, helle Fassung):
- Kopfband: Hintergrund `Farbe-Haupt`, Schrift `Farbe-Papier`, Unterzeile `#C9D1DE`, Akzentlinie und Augenbraue `Farbe-Akzent`
- Phasenleisten je Sozialform (Leiste / Hintergrund): Einzel `Farbe-Haupt`/`#EEF2FA`, Partner `#14706D`/`#E4F3F2`, Gruppe `Farbe-Akzent`/`#FFF4DC`, Plenum `#5B3E96`/`#EFEAF8`, Wahl `#4A5568`/`#EEEDE8`
- Titel und Minuten aus den fertigen Seiten auslesen, nicht abtippen.

**Blockplan (ein Kurs für mehrere Blockgruppen):** Haben die Klassen eines Kurses verschiedene Blockwochen (z. B. MGF10, Blöcke 1–3), die Termine aus den Blockplan-PDFs als `gruppen` in den Kursplan schreiben (Montage der Schulwochen ablesen, nie raten) und jedem Abschnitt `offen_ab` geben. Der Bau prüft, dass jedes Datum ein Montag ist und die Wochen in Reihenfolge stehen. Nach dem Wiederherstellen in der Lernplattform: Teilnehmer/innen → Gruppen, die Lernenden ihrer Klassengruppe zuweisen; ohne Gruppe sieht niemand einen freigegebenen Abschnitt. Ausprobieren ohne Testkonto: sich selbst einer Gruppe zuweisen und Rolle wechseln → „Schüler/in“. Beim Wiederherstellen „Gruppen und Gruppierungen einschließen“ angehakt lassen.

**Felder im Kursplan** (alle außer `datei` optional):
| Feld | Bedeutung |
|---|---|
| `kurs.vollname`, `kurs.kurzname`, `kurs.startdatum` | Pflicht |
| `kurs.banner`, `kurs.zusammenfassung` | Kursbild (PNG/JPG), Kursbeschreibung (HTML) |
| `allgemein_zusammenfassung`, `abschnitte[].zusammenfassung` | Abschnittstext (HTML, Inline-Stile) |
| `datei` | Pfad zur Datei, zum SCORM-ZIP oder zur Test-`.mbz` |
| `link` | nur SCORM: immer `"linkseite"` (das Skript holt den geteilten Download-Link des ZIPs von der Linkseite; das Paket wird dann bei jedem Start neu geladen). Ohne `link` wird das ZIP nur mitgeliefert |
| `typ` | `datei` (Standard), `scorm` oder `test` |
| `titel`, `dateiname` | Name in Moodle (Test: Standard aus der `.mbz`, "Test - <Thema>"); Dateiname in Moodle (statt `index.html`) |
| `beschreibung` | Text unter der Aktivität (HTML) |
| `versteckt` | `true` = für Schülerinnen und Schüler verborgen |
| `abschluss` | nur SCORM: `abgeschlossen` oder `bestanden` |
| `voraussetzung` | Titel der Aktivität, die vorher abgeschlossen sein muss |
| `gruppen` | Blockplan: Liste `{"name", "klassen", "beschreibung", "schulwochen"}`, je Block die Montage seiner Schulwochen in Reihenfolge (`JJJJ-MM-TT`). Mit `klassen` (z. B. `["MGF10a", "MGF10d"]`) entsteht **je Klasse eine Gruppe** (für den Notenexport je Klasse), Klassennamen mit kleinem Buchstaben am Ende. Die Sicherung legt die Gruppen an, die Mitglieder teilt die Lehrkraft nach dem Wiederherstellen ein |
| `abschnitte[].offen_ab` | Nummer der Schulwoche: Der Abschnitt ist für jede Gruppe ab Montag 0:01 ihrer n-ten Schulwoche sichtbar und bleibt offen, vorher ganz verborgen (Lehrkräfte sehen immer alles). Mehrere Abschnitte dürfen dieselbe Nummer haben (z. B. BW2 schon mit BW1) |
