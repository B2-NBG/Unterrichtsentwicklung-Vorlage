# Eine Seite bauen oder ändern

Gilt für jede `.html`-Seite in `Unterricht/`: E-Learning, Arbeitsblatt, Unterrichtsplan, Feedback, Testvorbereitung.
Übungs-Apps (Vorlage im Skill uebungs-app) und Test-Anleitungen (erzeugt `build-test-mbz.py`) haben eine eigene Vorlage, der Rest gilt auch für sie.

## Vorlage
- Jede Seite ist EINE `.html`-Datei und beginnt mit `.agents/gemeinsam/templates/Fachunterricht.html` (Schriftfeld) oder
  `Allgemeinbildung.html` (Layout "Lernschritte": Schritt-Leiste, Phasen mit Timer). Welche, klärt der Auswahldialog
  (`dialog.md`). Alles hier gilt für beide.
- **Vorlagen der Teams** (`Vorlagen/<Teamname>/<Name>.html`, Aufbau und Prüfung `Vorlagen/LIESMICH.md`): Eine Layout-Vorlage
  hat die Blöcke aus `Fachunterricht.html` und eigenen Stil und Script in `<Teamname>/<Name>.html:stil|script`. Eine
  **freie Vorlage** (`<meta name="vorlage-art" content="frei">`) hat keinen Kern, keine Bewertung, keinen Leerdruck, keinen
  PDF-Export: Das im Bericht offen sagen.
- **Neue Seite:** die ganze Vorlage kopieren, den TEMPLATE-Kommentar löschen, dann in dieser Reihenfolge
  1. `python .agents/gemeinsam/scripts/sync-vorlage.py --datei <Seite> --schreiben` (setzt die Markierungen und bei
     `<meta name="schrift" content="zeichnen">` die Schrift fürs Zeichnen aus dem Schulprofil),
  2. `python .agents/gemeinsam/scripts/bauen.py --auslagern <Seite> --schreiben` (Stil und Script des Kerns werden aus
     `.agents/gemeinsam/templates/kern/` verlinkt, die Seite bleibt klein),
  3. nach dem Einbetten von Bildern `bauen.py --bilder <Seite> --schreiben` (legt sie als Dateien in `<Thema>/bilder/` ab).
- **Quelle und gebaute Fassung:** `index.html` ist die Quelle, per Doppelklick im Projektordner geöffnet. Außerhalb des
  Projektordners fehlen `kern/` und `bilder/`, die Seite sieht kaputt aus. Eine einzelne Datei zum Weitergeben erzeugt
  `bauen.py <Seite>` (Temp-Ordner); Lernpaket, Kurs, Prüfung und Schülerinnen und Schüler bekommen die gebaute Fassung.
- **Blöcke und `kern/` nie anfassen:** Die markierten Blöcke und die Dateien in `kern/` (`<style>` und `<script>` der
  Vorlage) nie von Hand ändern. Schulfarben (`var(--haus-…)`), Logo der Vorlage und Schrift fürs Zeichnen kommen aus dem
  Schulprofil. Ändert sich eine Vorlage oder `schule.txt`: `sync-vorlage.py --vorlagen` (auch Team-Vorlagen und `kern/`),
  dann `sync-vorlage.py` (Probelauf) und `--schreiben` (alle Seiten), danach die Pakete neu bauen.

## Schriftfeld in `<header>`
Titel, Untertitel, Beruf, Ausbildungsjahr, Lernfeld · Blockwoche, Hilfsmittel.
- Klasse, Beruf, Fach, Abschnitt kommen aus dem Auswahldialog (`dialog.md`), nie raten. Das Ausbildungsjahr folgt aus der
  Klasse. "Lernfeld · Blockwoche" trägt den vollen Namen des Fachs aus `faecher.txt`. Eine zusätzliche Zelle aus dem
  Original (z. B. Allgemeintoleranz) kommt als eigene Zeile `<div class="wide">` nach der Name-Zelle.
- **Kurzkopf** `<div class="tb kurz">` (nur Benennung und Name) bei allgemeinbildenden Fächern (Ethik, Politik und
  Gesellschaft, Deutsch, Englisch, Religion, Sport) und bei Dokumenten nur für die Lehrkraft (Feedback, Unterrichtsplan).
- Die **Name-Zelle** bleibt unverändert (der Schülername kommt aus der Lernplattform). Das `<span class="ver">` bleibt leer: Version
  und Änderungsliste (Kommentar `VERSIONEN` nach `<title>`) trägt baue-lernpaket ein. Hell ist der Standard (mit
  Hell/Dunkel-Schalter), die Seite muss gut druckbar sein (A4 regelt die Vorlage).

## Lösungssperre und Passwort
- `content` von `<meta name="loesung-hash">` auf den Wert `hash=` aus `.agents/gemeinsam/data/solution-password.txt`
  setzen (fehlt die Datei: `einrichtung.md`). **Überall derselbe Hash:** auch bei übernommenen eigenen Dateien,
  Zusatzmodulen und Übungs-Apps. Nie ein Passwort im Klartext in eine Seite (`pruefen.py` erkennt typische Muster).
- Hat eine übernommene Seite ein eigenes Passwort, die Prüfung auf den Hash umstellen (`module-grafiken.md` im Skill
  baue-e-learning). Ändert die Lehrkraft das Passwort: den neuen Hash in alle E-Learnings in `Unterricht/` eintragen,
  ihre Pakete neu bauen.

## Aufgaben und Lösungen
- Kurze, klare Anweisungen, bei neuem Material eine Aufgabe pro nummeriertem Schritt. Beim Umbau bleibt der Originaltext
  wörtlich, Teilaufgaben (a, b, c) bekommen je ein eigenes Eingabefeld. **Schreibfelder** (`<textarea>`, Textfeld,
  Radio/Checkbox, `<select>` mit leerer erster Option) gehören INNERHALB von `<div class="task"><span class="tt">...</span>`
  (beim Drucken werden Aufgaben ohne Eintrag durch "Hier fehlt noch etwas" ersetzt).
- **Lösungen** gehören in `<details class="sol">` (Lösungsvorschlag je Aufgabe) oder `<section class="answers">` (nur
  für Lehrkräfte, z. B. Bewertungsraster), gesperrt bis zum Lehrkraft-Passwort. Nach "Abgeben" (ein Versuch) sehen die
  Schülerinnen und Schüler Bewertung und `details.sol`, auch im PDF-Export; `section.answers` und `.sol-only` nie. Bei
  versehentlicher Abgabe nimmt die Lehrkraft sie mit "Abgabe zurücknehmen" und ihrem Passwort zurück.
- **Lösungsvorschläge:** Jede inhaltliche Aufgabe bekommt einen kurzen Vorschlag in `details.sol`, nur mit Aussagen mit
  Quelle (Musterlösung, Material der Lehrkraft oder belegte Fundstelle mit Angabe). Für eine Fundstelle darf ohne
  Rückfrage im Web gesucht werden (nur Fachbegriffe, keine Schülerdaten). Ohne Quelle gibt es keinen Vorschlag, die
  Aufgabe wird im Bericht genannt. Bei eigener Meinung oder eigenen Beispielen nur Vergleichskriterien ("Eigene
  Meinung, keine Musterlösung. Vergleiche: …"). Organisationsaufgaben brauchen keinen (`bausteine.md` im Skill baue-e-learning).

## Ressourcen und eigener Code
- **Keine externen Ressourcen:** Bilder, Skripte, Stylesheets und Schriften kommen nie von außen, klickbare Links
  (`<a href>`) nach außen sind erlaubt. `seite-pruefen.py` prüft das an der gebauten Fassung; in der Quelle sind nur
  relative Verweise auf `kern/` und `bilder/` erlaubt.
- **Bilder** liegen als Dateien (png, jpg, gif, svg, webp) in `<Thema>/bilder/` und stehen als `src="bilder/…"`; nur diese
  Schreibweise bettet der Bau ein. Jedes `<img>` hat einen `alt`-Text (`alt=""` nur für Schmuck). In CSS (`url(...)`) und Script-Texten bleiben `data:`-Adressen eingebettet. Große
  Medien (Video, 3D-Modell) kommen als Datei in denselben Ordner (nicht in `bilder/`), die Seite geht dann nur als SCORM-Paket.
- **Module aus einer bestehenden Datei der Lehrkraft** (3D-Ansicht, Simulationen, Spiele) kommen unverändert in zusätzliche
  `<style>`/`<script>` NACH den Blöcken (erlaubte Anpassungen: `module-grafiken.md` im Skill baue-e-learning).
- **Beim bloßen Umbau** nie von sich aus neuen interaktiven Code schreiben. Bei **neuem E-Learning aus PDFs** und
  **Testvorbereitung** ist zusätzliches CSS und reines JavaScript für interaktive Aufgaben erlaubt (Sortieren, Zuordnen,
  Anklicken, Simulationen), in zusätzlichen Blöcken nach den Vorlagenblöcken, offline, ohne Bibliotheken.
