---
name: kursbanner
description: Erstellt ein Kursbanner (1600x900) für einen Kurs in der Lernplattform im einheitlichen Stil der Schule (Hausfarben, Logo) mit Fach, Stufe, Untertitel und Bild. Verwenden, wenn die Lehrkraft "Kursbanner", "Banner für den Kurs" oder "Kursbild" sagt oder der Skill baue-kurs ein Kursbild braucht.
---

# kursbanner

Erzeugt ein PNG-Kursbild für die Lernplattform (Moodle) im einheitlichen Look der Schule. Alle Banner sollen gleich
aussehen, nur Text und Bild wechseln.

## Schritt 1 – Angaben klären (nur was fehlt)
- **Titel** (groß, Versalien), z. B. `METALL`, `ETHIK`
- **Stufe/Klasse** (Zeile 2, Versalien, gesperrt), z. B. `GRUNDSTUFE`, `10. KLASSE`
- **Untertitel** (klein), z. B. `Fachunterricht`, `Was ist gut? Was ist richtig?`
- **Bild** (optional): Foto oder Grafik für die rechte Seite. Ohne Bild bleibt die rechte Hälfte einfarbig oder bekommt
  eine schlichte SVG-Illustration im Stil (flache Formen, Hausfarben).
- **Hausfarben und Logo** aus dem Schulprofil, nie abtippen: `python .agents/gemeinsam/scripts/profil.py` zeigt
  `Farbe-Haupt` (Hintergrund), `Farbe-Papier` (Text), `Farbe-Band-Text` (Untertitel), `Farbe-Akzent` (Strich),
  `Farbe-Zweit`, `Farbe-Dritt` (weitere Akzente) und `Logo-Kursbanner` (Pfad im Repo). Das Logo in den Arbeitsordner kopieren.
  Der Name der Lernplattform kommt nicht ins Banner.

## Festes Design
- Format: **1600 x 900 px**, PNG, Dateiname `<Titel>-Kursbanner.png`
- Hintergrund `Farbe-Haupt`, Text `Farbe-Papier`, Untertitel `Farbe-Band-Text`, Strich unter dem Titel `Farbe-Akzent`.
  Dieselben Werte nutzen die Vorlage `Allgemeinbildung.html` und die Abschnittstexte des Skills baue-kurs.
- Schrift: Poppins/DM Sans, falls installiert, sonst **Inter** (Titel: Inter Display Black). Fehlt auch Inter: Segoe UI
  (Titel: Segoe UI Black).
- Textblock links (x = 100 px), vertikal mittig: Titel ca. 168 px (bei langen Wörtern verkleinern, damit er höchstens
  ca. 700 px breit ist), Strich 96 x 7 px, Stufe 50 px mit letter-spacing 9 px, Untertitel 27 px
- Foto rechts: volle Höhe, ca. 950 px breit, `object-fit: cover`, nach links weich in `Farbe-Haupt` ausgeblendet
  (Gradient), unten leicht abgedunkelt
- **Logo: rechts, vertikal mittig** (right 72 px, Breite 156 px, abgerundete Ecken)
- Wichtige Inhalte in der Mitte halten; die Lernplattform kann Ränder beschneiden.

## Schritt 2 – Bauen, Prüfen und Abschluss
1. Eingaben klären und Bild sowie Logo in einen Arbeitsordner kopieren (`werkzeuge.md`) (nicht ins Repo).
2. `banner.html` nach der Vorlage unten schreiben und die Platzhalter ersetzen: `{{HAUPT}}` usw. mit den Farben aus dem
   Profil (sechsstellig, `#RRGGBB`); `{{HAUPT}}d9`, `{{HAUPT}}8c` und `{{HAUPT}}00` sind dieselbe Farbe mit 85 %, 55 %
   und 0 % Deckkraft.
3. Rendern (Viewport 1600x900) mit dem installierten Edge oder Chrome, ohne Node und ohne weitere Installation:
   `--headless=new --force-device-scale-factor=1 --window-size=1600,900 --screenshot=<png> <banner.html>`, mit eigenem
   `--user-data-dir` im Arbeitsordner; bei leerem Ergebnis einmal wiederholen. Pfade zum Browser wie in
   `.agents/gemeinsam/scripts/seite-pruefen.py`.
4. Ergebnis-PNG ansehen und prüfen: Text vollständig lesbar, Titel nicht zu nah am Foto, Logo-Ecken sauber (keine
   fremden Hintergrundreste), nichts abgeschnitten. Bei Bedarf anpassen und neu rendern.
5. PNG nach `Ressourcen/Bilder/<Thema>/<Titel>-Kursbanner.png` legen, in `Ressourcen/Inhalt.md` eintragen (`ablage.md`,
   Ressourcen) und kurz sagen, wo es liegt. Im Kursplan steht dieser Pfad unter `kurs.banner` (Skill baue-kurs). Ältere
   Banner heißen `<Titel>-Banner-ByCS.png` und bleiben so.

## HTML-Vorlage
```html
<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0">
<div style="position:relative;width:1600px;height:900px;background:{{HAUPT}};overflow:hidden;font-family:Inter">
  <!-- Bild rechts (weglassen, wenn kein Bild) -->
  <img src="{{BILD}}" style="position:absolute;right:0;top:0;height:900px;width:949px;object-fit:cover">
  <div style="position:absolute;inset:0;background:linear-gradient(90deg,{{HAUPT}} 0%,{{HAUPT}} 42%,{{HAUPT}}d9 52%,{{HAUPT}}00 72%)"></div>
  <div style="position:absolute;inset:0;background:linear-gradient(0deg,{{HAUPT}}8c,{{HAUPT}}00 30%)"></div>
  <!-- Text -->
  <div style="position:absolute;left:100px;top:272px;color:{{PAPIER}}">
    <div style="font-family:'Inter Display';font-weight:900;font-size:168px;letter-spacing:4px;line-height:1">{{TITEL}}</div>
    <div style="width:96px;height:7px;border-radius:4px;background:{{AKZENT}};margin:52px 0 30px"></div>
    <div style="font-weight:500;font-size:50px;letter-spacing:9px">{{STUFE}}</div>
    <div style="font-size:27px;color:{{BAND_TEXT}};margin-top:26px;letter-spacing:1px">{{UNTERTITEL}}</div>
  </div>
  <!-- Logo rechts, vertikal mittig -->
  <img src="{{LOGO}}" style="position:absolute;right:72px;top:50%;transform:translateY(-50%);width:156px;border-radius:18px;clip-path:inset(1px round 17px)">
</div></body></html>
```

## Hinweise
- Hat ein Foto viel helle Fläche hinter dem Logo, ist das in Ordnung: Das Logo hat ein eigenes helles Feld.
- Für eine Reihe von Kursen dieselben Maße und Positionen beibehalten, damit die Kursübersicht einheitlich wirkt.
- Wenn ein vorhandenes, zu flaches Banner nur höher werden soll: auf eine 1600x900-Fläche in `Farbe-Haupt` mittig
  einsetzen (Hintergrundfarbe vorher aus einem Eckpixel lesen).
