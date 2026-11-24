# Werkzeuge: eine KI, viele Anbieter

Das Projekt läuft mit der KI-Erweiterung von Anthropic, OpenAI (Codex), GitHub Copilot und Google (Gemini). Alle arbeiten
nach denselben Regeln. Hier steht, was für jede gilt und was sie tun soll, wenn ihr Werkzeug etwas anders heißt.

## Wer liest was
- **`AGENTS.md`** liest jedes Werkzeug selbst; für Gemini steht es in `.gemini/settings.json`.
- **Skills** liegen als Quelle in `.agents/skills/<name>/SKILL.md` (Codex, Gemini und Copilot lesen sie dort). Für Werkzeuge,
  die in `.claude/skills/` suchen, erzeugt `pruefen.py --erneuern` dort je Skill eine Verweisdatei: gleicher Kopf, Text
  "Lies die Quelle ganz und arbeite danach". Die Verweisdateien und `.gemini/settings.json` nie von Hand ändern.
  Liest ein Werkzeug beide Orte, taucht ein Skill doppelt auf; das ist gewollt.
- Ein Skill ist erst geladen, wenn die KI seine Quelle ganz gelesen hat.

## Auswahldialog
Hat die KI ein Frage-Werkzeug, stellt sie jede Frage damit (Empfehlung zuerst). Sonst schreibt sie eine Nachricht mit
nummerierten Optionen je Frage, die Empfehlung zuerst, und wartet auf die Antwort. Nie raten.

## Helfer
Die Aufträge für Teilaufgaben stehen in `.agents/helfer/<name>.md`. Kann die KI Unterhelfer starten, bekommt jeder den
Auftrag "Lies `.agents/helfer/<name>.md` und arbeite danach", parallel, wo die Aufgaben unabhängig sind. Sonst führt die KI
die Schritte selbst aus, einen nach dem anderen. Ein Helfer berichtet nur, behoben wird danach.

## PDFs und Bilder
Mit dem Lesewerkzeug der KI. Hat sie keines für PDFs, dann `pdftotext` oder pypdfium2 in einer venv in `tmp/`.

## Arbeitsordner
Zwischenstände, Prüfbilder und Skripte, die nicht ins Projekt gehören, liegen im eigenen Ablageort der Sitzung. Hat die
KI keinen, dann in `tmp/` (steht nicht in Git).

## Schreibweise
In Regeln, Skills und Meldungen heißt es "die KI" (sie). Anweisungen an die KI stehen in der Du-Form.
Ausnahme: Dateinamen, die ein Werkzeug verlangt (`.claude/`, `.gemini/`).

## Commits
Eine Commit-Nachricht der KI endet mit der Zeile `Co-Authored-By:` des Werkzeugs. Setzt es keine eigene, dann
`Co-Authored-By: KI (<Werkzeug>) <noreply@invalid>`. Daran erkennt GitHub, dass eine KI beteiligt war (Mitdokumentieren, `handbuch.md`).
