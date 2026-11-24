---
name: skript-abgleicher
description: Arbeitet einen fachlich neueren Quelltext (z. B. ein Skript, SuS- und Lös-Fassung) in GENAU EINE E-Learning-Seite ein oder baut daraus eine neue Seite nach der Vorlage Fachunterricht.html, mit Lösungen, Bewertung und Papierfassungen für den Leerdruck. Verwenden, wenn mehrere Seiten parallel aus einem Skript aktualisiert oder neu gebaut werden (je Seite ein Helfer).
---

Du arbeitest im Projektordner der Lehrkraft. Du baust **eine** Seite. Andere Helfer bauen gleichzeitig andere Seiten.

## Was du bekommst (im Auftrag)
- Pfade der Quelle: SuS-Fassung und Lös-Fassung, dazu die PDF-Druckfassung (Ort und Namen: Fachregel des Fachs).
- Kapitel der Quelle (z. B. `k5, k6, k7`).
- Zielseite: vorhandene `Unterricht/.../index.html` oder neuer Pfad mit Kopfdaten (Titel, Untertitel, Beruf, Ausbildungsjahr, Lernfeld · Blockwoche, Hilfsmittel).
- Niveaus (drei Niveaus oder ohne) und die Änderungswünsche der Lehrkraft für diese Seite.
- Dein Arbeitsordner (nur dort Zwischendateien).

## Vorher lesen
1. `AGENTS.md` (bindend) und `.agents/gemeinsam/regeln/seite.md`, `abschluss.md` (Abschnitt 1, Prüfen).
2. `.agents/skills/baue-e-learning/skript-uebernahme.md` (Ablauf und Zuordnung), `bausteine.md`, `druckfassung.md`, `module-grafiken.md`.
3. Die Fachregel des Fachs (`faecher.md`) mit ihren Festlegungen und Quellen (sie haben Vorrang vor der Quelle).
4. Die Zielseite (falls vorhanden) und die Quelle. Große Dateien nur in Teilen lesen, `data:`-Inhalte nie ausgeben.
   Text der Quelle ohne Bilder: ein Python-Skript im Arbeitsordner ersetzt `data:[^"')]+` durch `DATA` und schreibt eine Arbeitskopie.

## Regeln
- **Du schreibst nur in:** deine Zielseite, deinen Arbeitsordner und neue Dateien unter `Ressourcen/Bilder/<Thema>/`.
- **Nicht anfassen:** AGENTS.md, Regeln, Skills, Vorlagen, `faecher.txt`, das Handbuch, `Ressourcen/Inhalt.md`, andere Seiten und die Quelle selbst. Was dort fehlt, meldest du im Bericht.
- **Vorlagenblöcke** zwischen `<!-- Fachunterricht.html:… -->`-Markierungen und die Dateien in `kern/` nie ändern. Eigenes CSS und JS kommt in zusätzliche Blöcke nach den Vorlagenblöcken, Module der Quelle unverändert (Schritt 4a).
- **Keine Commits,** kein `git`-Schreibbefehl, kein `build-scorm.py`, kein `code -r`.
- **Base64:** nie ausgeben oder abtippen. Bilder mit `.agents/gemeinsam/scripts/medien-einsetzen.py`, Module per Skript kopieren.
- **Lösungen:** nur in `details.sol`, `section.answers`, `.sol-only` und als `data-ok` / `data-keys`.
- **Lösungsvorschläge** nur mit Quelle (Lös-Fassung, Festlegungen und Quellen der Fachregel).
- **Papierfassung:** Jede interaktive Aufgabe bekommt eine Papierfassung (`print-alt`) nach dem Katalog in `druckfassung.md`.
- **Fachliche Festlegungen** der Fachregel gelten überall (Technisches Zeichnen: Allgemeintoleranz, Durchmesser `⌀`,
  Sägeaufmaß nach der Quelle).
- Neue Seite: Vorlage `.agents/gemeinsam/templates/Fachunterricht.html` kopieren, TEMPLATE-Kommentar löschen, die Schrift nach der Fachregel setzen (Technisches Zeichnen: `<meta name="schrift" content="zeichnen">` vor `<title>`) und den Lösungs-Hash aus `.agents/gemeinsam/data/solution-password.txt` eintragen.

## Zum Schluss
1. `python .agents/gemeinsam/scripts/sync-vorlage.py --datei <Seite> --schreiben` und `python .agents/gemeinsam/scripts/bauen.py --auslagern <Seite> --schreiben`, mit Bildern danach `bauen.py --bilder <Seite> --schreiben` (am Mac `python3`)
2. `python .agents/gemeinsam/scripts/seite-pruefen.py <Seite> --arbeitsordner <Arbeitsordner>`, bis es BESTANDEN meldet. Screenshot und Leerdruck ansehen (PDF-Seiten mit pypdfium2 aus einer venv im Arbeitsordner in Bilder umwandeln).
3. Bericht an die Hauptsitzung, kurz und vollständig:
   - Zielseite und Quellkapitel mit Bearbeitungsnummer
   - Aufgaben je Niveau: übernommen, neu, entfallen
   - Lösungen verknüpft, automatisch bewertet oder nicht
   - Aufgaben ohne Lösungsvorschlag (keine Quelle)
   - eingebaute Änderungswünsche
   - gebaute Papierfassungen
   - Abweichungen vom Quelltext mit Grund (für die Rückmeldung an den Ersteller)
   - neue Dateien in `Ressourcen/Bilder/`
   - Ergebnis von `seite-pruefen.py`
   - offene Punkte und Fragen an die Lehrkraft
