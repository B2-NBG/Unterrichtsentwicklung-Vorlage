---
name: schule-einrichten
description: Richtet die Schule im Dialog ein - Schulprofil (Schule, Schulart, Schulfarben, Logo, Lernplattform, allein oder Kollegium) und Lehrkraft-Passwort über ein verdecktes Fenster. Verwenden bei "Richte mein Schulprofil ein", "Schule einrichten", "Schulfarben", "Logo", "Lehrkraft-Passwort setzen".
---

# Schule einrichten

## Zuerst
- `git pull --rebase`, dann `python .agents/gemeinsam/scripts/pruefen.py --rechte` (am Mac `python3`). Das
  Schulprofil `.agents/gemeinsam/data/schule.txt` ist Werkzeug: Nur bei "Werkzeug-Verantwortliche: ja" weiter (in einem
  frischen Repo aus der Vorlage steht `Schutz | aus`, dann ist das so). Sonst den Wunsch an die
  Werkzeug-Verantwortlichen weitergeben.
- `schule.txt` ganz lesen: Die Kommentare darin erklären jeden Schlüssel. Werte nur an ihrer Stelle ändern, Kommentare
  und Reihenfolge bleiben. Nie raten: Was die Lehrkraft nicht sagt und kein Beispielprofil liefert, bleibt, wie es ist.

## Im Dialog fragen (Auswahldialog, höchstens vier Fragen auf einmal)
Nur fragen, was sich ändern soll. Bei einem frischen Repo alles, sonst nur das Genannte (z. B. nur das Logo).
1. **Allein oder Kollegium:** allein = `Schutz | aus` und `Zustellung | download`. Kollegium = `Schutz | teams`
   (GitHub-Organisation mit Teams, danach Abschnitt "Kollegium"), Zustellung `download` oder `power-automate`.
2. **Schulart:** Liegt `Beispiele/Profile/` im Repo, die passenden Profile anbieten (Dateinamen, höchstens vier) und
   das gewählte als Grundlage nach `schule.txt` kopieren; es bringt Klassenmuster, Jahrgänge, Abschnitte, Lehrplan und
   Kalender der Schulart mit. Sonst Schulart, Klassenmuster und Jahrgänge einzeln klären.
3. **Schule:** voller Name und Kurzname (Kopf der Seiten, Kursnamen); Land.
4. **Erscheinungsbild:** Schulfarben als Hex-Werte (`#2F4858`) oder neutral lassen. Logo als PNG: Die Lehrkraft legt die
   Datei in den Projektordner oder nennt den Pfad; nach `.agents/gemeinsam/data/erscheinungsbild/logo.png` kopieren
   (fürs Kursbanner `kursbanner-logo.png`, sonst dasselbe Bild). Fehlt ein Logo, bleibt der Platzhalter.
5. **Lernplattform:** Name und Adresse der Moodle-Instanz. Version, Kategorie, Besitzer und Site-Hash stehen in einer
   frischen Kurssicherung: Legt die Lehrkraft eine `.mbz` dazu, `moodle_backup.xml` daraus lesen (Schlüssel wie in den
   Kommentaren von `schule.txt`). Ohne Sicherung die Beispielwerte lassen und das am Ende sagen.
Niveaus, Bestehensgrenze und Notenstufen nicht ändern: Vorlagen und Lernpakete rechnen derzeit fest damit (der
Selbsttest lehnt andere Werte ab). Fächer und Berufe ergänzt der Auswahldialog später von selbst (`dialog.md`).

## Schreiben und prüfen
1. `schule.txt` schreiben, dann `python .agents/gemeinsam/scripts/profil.py`: zeigt alle Angaben und prüft die
   Pflichtangaben. Fehler beheben.
2. `python .agents/gemeinsam/scripts/sync-vorlage.py --vorlagen` (Farben und Logo in die Vorlagen), danach
   `python .agents/gemeinsam/scripts/pruefen.py --vorlage-bestaetigen` nur, wenn der Selbsttest die geänderten Vorlagen
   meldet und die Änderung von hier stammt.
3. **Lehrkraft-Passwort** (frisches Repo oder auf Wunsch): `python .agents/gemeinsam/scripts/pw-hash.py` selbst starten.
   Bei der Lehrkraft öffnet sich ein verdecktes Fenster (zweimal eingeben), gespeichert wird nur der Hash in
   `.agents/gemeinsam/data/solution-password.txt`. Vorher sagen, dass gleich ein Fenster kommt. Nie im Chat nach dem
   Passwort fragen, es nie ausgeben, nie als Argument übergeben. Meldet das Skript, dass weder Fenster noch Terminal
   gehen (Cloud-Sitzung): Die Lehrkraft startet es später am eigenen Rechner selbst.
4. `python .agents/gemeinsam/scripts/pruefen.py --erneuern` (schreibt die erzeugten Blöcke in AGENTS.md, Regeln und
   Handbuch neu). Commit nach `abschluss.md`: Ändern Farben oder Logo vorhandene Lernpakete, meldet die Prüfung
   "Lernpaket betroffen: ja", dann erst fragen.

## Kollegium (nur bei `Schutz | teams`)
Danach mit den Werkzeug-Verantwortlichen nach `schutz-admin.md` und `einrichtung-admin.md`: Team der
Werkzeug-Verantwortlichen (`Team-Werkzeug`), Teams und ihre Klassen und Fächer in `schutz.txt`, GitHub-App zum Lesen
der Teams. Die Rulesets setzt die KI am Rechner selbst: `python .agents/gemeinsam/scripts/schutz-github.py --anwenden`,
danach `--pruefen` (braucht Admin-Recht am Repo und die gespeicherte GitHub-Anmeldung; geht nicht in einer
Cloud-Sitzung). Für Rulesets in einem privaten Repo braucht die Organisation den Tarif GitHub Team.

## Bericht
In wenigen Sätzen: was eingestellt ist, was noch Beispielwert ist (z. B. Moodle-Werte ohne Sicherung), ob das Passwort
gesetzt ist, und was gepusht ist.
