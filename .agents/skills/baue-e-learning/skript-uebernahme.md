# baue-e-learning – Skript übernehmen: neueren Quelltext in E-Learnings einarbeiten

Teil des Skills baue-e-learning (Ablauf in `SKILL.md`). Gilt, wenn ein fachlich neuerer Quelltext (z. B. ein Skript für das Technische Zeichnen) in bestehende E-Learnings kommt oder daraus neue E-Learnings in der Aufteilung dieses Repos entstehen. Für viele Seiten auf einmal den Agenten **skript-abgleicher** nutzen, je Seite einen, parallel (`.agents/helfer/skript-abgleicher.md`).

## Quellen und Zuordnung
- Hat das Fach eine Fachregel (`faecher.md`), nennt sie Quellen, Vorrang der Festlegungen und die schon festgelegte
  Zuordnung, dazu die Tabelle, welcher Baustein der Quelle welcher Baustein der Seite wird. Immer die neueste Fassung der
  Quelle nehmen und im Bericht nennen.
- Ist die Zuordnung noch nicht festgelegt: zuerst eine Tabelle *Kapitel der Quelle → Zielseite* aufstellen und der
  Lehrkraft zeigen. Die Abschnitte dieses Repos bleiben.
- Neue Seiten aus einer Quelle: nach Thema und Arbeitszeit teilen, höchstens so viele Pakete, wie die Lehrkraft vorgibt,
  Richtwert 45–90 Minuten Bearbeitungszeit je Seite. Grundlage sind Aufgabenzahl, Zeichenaufträge und Test.

## Umbau
Die Seite wird frei neu aufgebaut. Der Speicherstand der Schülerinnen und Schüler muss nur erhalten bleiben, wenn die Lehrkraft es sagt. Vorhandene `data-k` ohne Auftrag nicht wiederverwenden.

Bausteine der Quelle werden Bausteine der Vorlage (`bausteine.md`): Abschnitt, Aufgabe im passenden Niveau-Block,
Felder mit `data-k` und `data-ok`, Lösungen in `details.sol` (Lehrkraftteile in `section.answers` bzw. `.sol-only`).
Eine eigene Freischaltung der Quelle entfällt, die Vorlage sperrt über das Lehrkraft-Passwort. Eingebettete Bilder über
`.agents/gemeinsam/scripts/medien-einsetzen.py`, nie base64 abtippen. Interaktive Module unverändert nach Schritt 4a
(`module-grafiken.md`), dazu immer die Papierfassung aus `druckfassung.md`.

Regeln:
- **Wortlaut:** Der Text bleibt wörtlich, außer eine Festlegung verlangt eine Änderung oder ein Fehler ist offensichtlich. Beides kommt in den Bericht. Teilaufgaben (a, b, c) bekommen je ein eigenes Feld.
- **Fachliche Festlegungen und Schrift** (Durchmesser, Allgemeintoleranz, Schrift fürs Zeichnen): Fachregel des Fachs.
- **Niveaus:** Die Aufgaben des Skripts auf Einsteiger-, Prüfungs- und Profiniveau verteilen, nach Schritt 1 Niveaus (Vorschau zeigen, außer die Lehrkraft hat schon entschieden).
- **Version:** Neuer Inhalt ist beim Paketbau eine Hauptversion. In der Frage zum Commit vor laufenden Bearbeitungen warnen.

## Bericht und Rückmeldung
- **Je Seite:**
  - übernommene, neue und entfallene Aufgaben
  - verknüpfte Lösungen
  - Aufgaben ohne Quelle für einen Lösungsvorschlag
  - gebaute Papierfassungen
  - Abweichungen vom Text der Quelle mit Grund
  - offene Punkte
- **Rückmeldung an den Ersteller:** Alle Verbesserungen und Abweichungen sammeln, je Punkt *Quelle, Kapitel, was, warum*. Wohin sie kommen, sagt die Fachregel; in die Quelle selbst wird nichts geschrieben.
