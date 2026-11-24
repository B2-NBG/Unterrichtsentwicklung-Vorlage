# Unterrichtsentwicklung mit KI: Vorlage für Moodle-Schulen

Ein Werkzeug, mit dem Lehrkräfte zusammen mit einer KI im Editor Unterrichtsmaterial bauen: E-Learnings als eine
HTML-Seite (mit drei Niveaus, Lösungssperre, PDF-Export und leerem Arbeitsblatt), Lernpakete (SCORM) mit Punkten für
Moodle, fertige Moodle-Tests und ganze Kurssicherungen. Alle Regeln stehen in `AGENTS.md` und `.agents/`, die KI liest
sie in jeder Sitzung. Prüfungen vor dem Commit und auf GitHub sorgen dafür, dass nur Fertiges bei den Lernenden
ankommt.

Allein nutzbar, gedacht für ein **Kollegium**: Teams, Schutz für Werkzeug und Unterricht der Abteilungen, gemeinsame
Notizbücher und eine Zustellung aller Pakete nach jedem Push.

> **Euer eigenes Repo muss privat sein.** Lösungen und Bewertungen stehen im Quelltext der Seiten und Pakete, und die
> Downloads eines öffentlichen Repos kann jede Person mit GitHub-Konto laden. Öffentlich ist nur diese Vorlage.

## Was ihr braucht
- ein GitHub-Konto (im Kollegium: eine GitHub-Organisation der Schule),
- Visual Studio Code mit einer KI-Erweiterung (von Anthropic, OpenAI, GitHub oder Google) und einem bezahlten Abo des
  Anbieters. **Tipp:** Verifizierte Lehrkräfte bekommen über [GitHub Education](https://github.com/education/teachers)
  kostenlos GitHub Copilot Pro und für die Schule den Tarif GitHub Team (Bedingungen und aktuellen Stand dort prüfen;
  Antrag unter GitHub → Settings → Education benefits),
- Python 3 (am Mac `python3`) und Edge oder Chrome für die Seitenprüfung,
- eine Moodle-Lernplattform (z. B. die ByCS in Bayern).

## Allein in fünf Schritten
1. **Eigenes Repo anlegen:** oben auf „Use this template“ → „Create a new repository“, Sichtbarkeit **Private**.
2. **Holen und öffnen:** In VS Code „Repository klonen“, einen Ordner außerhalb von OneDrive wählen, öffnen und ihm
   vertrauen.
3. **Schulprofil einrichten:** Der KI sagen: „Richte mein Schulprofil ein.“ Sie fragt im Dialog nach Schulart
   (Beispiele in `Beispiele/Profile/`), Name, Hausfarben, Logo, Lernplattform und ob ihr allein oder im Kollegium
   arbeitet, schreibt `.agents/gemeinsam/data/schule.txt` und setzt alles in Vorlagen und Handbuch ein.
4. **Lehrkraft-Passwort setzen:** gehört zum selben Gespräch. Die KI öffnet ein verdecktes Fenster, das Passwort kommt
   nie in den Chat. Gespeichert wird nur ein Hash in `.agents/gemeinsam/data/solution-password.txt`, der mit committet
   wird. Damit sperrt jede Seite ihre Lösungen. (Von Hand: `python .agents/gemeinsam/scripts/pw-hash.py`.)
5. **Erste Seite bauen:** Die KI bitten, z. B. „Erstelle ein Arbeitsblatt zu …“ oder „Baue ein E-Learning aus diesen
   PDFs“. Fragt sie „Committen und pushen?“, mit Ja antworten. Etwa eine Minute später liegen die Lernpakete auf GitHub
   unter Actions → Lauf → Artifacts zum Herunterladen.

In `Unterricht/` liegen Beispielseiten, ein Beispieltest und ein Beispielkurs (Lehrkraft-Passwort dort: `demo`). Ihr
könnt sie ansehen, behalten oder löschen. Die Kolleginnen und Kollegen finden alles Weitere in `#Handbuch.html`.

## Im Kollegium
Werkzeug-Verantwortliche richten einmal ein (Anleitung für die KI: `.agents/gemeinsam/regeln/einrichtung-admin.md` und
`schutz-admin.md`):
- **Organisation und Teams:** ein Team der Werkzeug-Verantwortlichen (`schule.txt`, `Team-Werkzeug`), Teams je Abteilung
  oder Fachbereich, ihre Klassen und Fächer in `.agents/gemeinsam/data/schutz.txt`, `Schutz | teams`.
- **Rulesets:** `python .agents/gemeinsam/scripts/schutz-github.py --anwenden` setzt die Regeln, mit denen GitHub
  verbotene Pushes abweist. Das kann auch die KI in VS Code für euch ausführen, wenn ihr Admin am Repo seid (sie nutzt
  eure gespeicherte GitHub-Anmeldung, aus einer Cloud-Sitzung im Browser geht es nicht). Für diese Rulesets in einem
  privaten Repo braucht die Organisation den Tarif GitHub Team. Verifizierte Lehrkräfte bekommen ihn über
  [GitHub Education](https://github.com/education/teachers) kostenlos.
- **Teams lesen:** eine GitHub-App mit Leserecht auf die Mitglieder, ihre Daten als Secrets im Environment `zustellung`.
- **Zustellung:** `download` (Pakete im Lauf auf GitHub) oder `power-automate` (ein Flow legt alle Pakete in einen
  Teamordner in OneDrive/SharePoint, jedes Paket behält seinen Download-Link). Anleitung für den Flow:
  `einrichtung-admin.md`.

## Lizenz und Beiträge
Copyright (C) 2026 @gretl3000. Freie Software unter der GNU General Public License, Version 3 oder später, mit einer
Ausnahme für gebautes Unterrichtsmaterial (Seiten, Lernpakete, Tests, Kurse): Was ihr mit dem Werkzeug baut, dürft ihr
unter einer Lizenz eurer Wahl weitergeben. Änderungen am Werkzeug selbst bleiben GPL. Einzelheiten: `LICENSE` und
`LIZENZ-AUSNAHME.md`.

Diese Vorlage entsteht aus einem privaten Repo und wird von dort aus erneuert. Fehler und Wünsche gern als Issue.
