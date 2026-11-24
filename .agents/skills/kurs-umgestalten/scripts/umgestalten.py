"""
umgestalten.py - macht aus einer ByCS-Kurssicherung eine neue Fassung zum Wiederherstellen.

Schritte: Blockplan einsetzen (falls im Kursplan) -> Kursbild -> Gestaltung (Icons, Kopfband, Reiterfarben) ->
Kursbeginn = Kursbeginn des Zielkurses (sonst verschiebt Moodle alle Termine) -> Namen mit Fassung V<n> ->
Prüfung (build-mbz.py --pruefen, nur neue Fehler zählen) -> farbige Anleitung.

Aufruf im Projektordner (am Mac python3):
  python .agents/skills/kurs-umgestalten/scripts/umgestalten.py --plan <Kursplan> --sicherung <ByCS.mbz> --kursbeginn TT.MM.JJJJ

--kursbeginn: der Kursbeginn, der im Zielkurs der ByCS steht (Einstellungen, gesperrt). Pflicht.
--version: Fassungsnummer (sonst die nächste freie in Ressourcen/Kurssicherungen-ByCS/).
--kursbild-behalten: Kursbild der Sicherung nicht ersetzen.
Ergebnis in Ressourcen/Kurssicherungen-ByCS/ (nur lokal): <Kurzname>-V<n>.mbz und Anleitung-<Kurzname>-V<n>.html.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kurslib import (ABLAGE, PROJEKT, SKILL, Sicherung, berlin, datum, de, ersetze, fehler, lese_plan,  # noqa: E402
                     ohne_icon, projektpfad, slug)
from gestalten import gestalten  # noqa: E402
from kursbild import kursbild  # noqa: E402

PRUEFER = PROJEKT / ".agents" / "skills" / "baue-kurs" / "scripts" / "build-mbz.py"
blockplan_modul = __import__("importlib").import_module("blockplan-einsetzen")


def pruef_fehler(mbz: Path) -> list[str]:
    r = subprocess.run([sys.executable, str(PRUEFER), "--pruefen", str(mbz)], capture_output=True, text=True, encoding="utf-8")
    return [z.strip() for z in (r.stdout + r.stderr).splitlines() if z.startswith("FEHLER")]


def setze_kursbeginn_und_namen(s: Sicherung, plan: dict, beginn: dt.date, fassung: str):
    ts = str(berlin(beginn))
    kurs = s.text("course/course.xml")
    kurs = ersetze(kurs, "startdate", ts, "(course.xml)")
    for tag, wert in (("fullname", plan["kurs"]["vollname"]), ("shortname", plan["kurs"]["kurzname"])):
        kurs = re.sub(rf"(<course [^>]*>.*?)<{tag}>.*?</{tag}>", lambda m: f"{m.group(1)}<{tag}>{html.escape(wert + ' ' + fassung, quote=False)}</{tag}>",
                      kurs, count=1, flags=re.S)
    s.setze("course/course.xml", kurs)
    mb = s.text("moodle_backup.xml")
    s.setze("moodle_backup.xml", ersetze(mb, "original_course_startdate", ts, "(moodle_backup.xml)"))


def anleitung(plan: dict, blockplan: dict | None, datei: str, beginn: dt.date, fassung: str, quelle: str) -> str:
    t = (SKILL / "templates" / "Anleitung-Wiederherstellen.html").read_text(encoding="utf-8")
    e = lambda x: html.escape(x, quote=True)  # noqa: E731
    punkte, gruppen_satz, bp_satz = "", ".", "."
    if blockplan:
        bp_satz = ". Jeder Reiter geht je Klasse am Montag ihrer Schulwoche um 0:01 Uhr auf (Blockplan)."
        namen = [blockplan["gruppenname"].format(klasse=k) for b in blockplan["bloecke"] for k in b["klassen"]]
        gruppen_satz = ": " + ", ".join(f"<code>{e(n)}</code>" for n in namen) + "."
        # zwei Reiter zum Nachsehen: der erste und einer aus der Mitte des Jahres
        reiter = sorted(blockplan["abschnitte"].items(), key=lambda kv: kv[1])
        wahl = [reiter[0]] + ([min(reiter, key=lambda kv: abs(kv[1] - 4))] if len(reiter) > 1 else [])
        if len(wahl) == 2 and wahl[0][1] == wahl[1][1]:
            wahl = wahl[:1]
        for i, (name, woche) in enumerate(wahl):
            karten = "".join(
                f'<div class="date b{j % 4 + 1}"><div class="k">{e(b["name"])} · {e(", ".join(b["klassen"]))}</div>'
                f'<div class="d">{de(datum(b["schulwochen"][woche - 1]))}</div></div>' for j, b in enumerate(blockplan["bloecke"]))
            vor = "Voraussetzungen ansehen. So muss es aussehen (jeweils 00:01 Uhr):" if i == 0 else "zur Probe:"
            punkte += f'    <li><b>{e(ohne_icon(name))}</b> → {vor}\n      <div class="dates">{karten}</div></li>\n'
    else:
        punkte = "    <li>Einen Reiter öffnen und die Voraussetzungen ansehen.</li>\n"
    for k, v in {"{{VOLLNAME}}": e(plan["kurs"]["vollname"]), "{{DATEI}}": e(datei), "{{KURSBEGINN}}": de(beginn),
                 "{{FASSUNG}}": fassung, "{{BLOCKPLAN_SATZ}}": bp_satz, "{{GRUPPEN_SATZ}}": gruppen_satz,
                 "{{PRUEF_PUNKTE}}": punkte.rstrip("\n"), "{{STAND}}": de(dt.date.today()), "{{QUELLE}}": f" aus {e(quelle)}"}.items():
        t = t.replace(k, v)
    if "{{" in t:
        fehler("Anleitung: Platzhalter nicht ersetzt")
    return t


def main():
    p = argparse.ArgumentParser(description="ByCS-Kurssicherung umgestalten (Blockplan, Gestaltung, Kursbild, Kursbeginn).")
    p.add_argument("--plan", required=True, help="Kursplan (Name in Ressourcen/Kursumbau/ oder Pfad)")
    p.add_argument("--sicherung", required=True, help="Sicherung aus der ByCS (.mbz, ohne Nutzerdaten)")
    p.add_argument("--kursbeginn", required=True, help="Kursbeginn des Zielkurses in der ByCS (TT.MM.JJJJ)")
    p.add_argument("--version", type=int, help="Fassungsnummer (sonst die nächste freie)")
    p.add_argument("--kursbild-behalten", action="store_true", help="Kursbild der Sicherung behalten")
    a = p.parse_args()

    plan = lese_plan(a.plan)
    beginn = datum(a.kursbeginn)
    basis = slug(plan["kurs"]["kurzname"])
    ABLAGE.mkdir(parents=True, exist_ok=True)
    vorhanden = [int(m.group(1)) for f in ABLAGE.glob(f"{basis}-V*.mbz") if (m := re.fullmatch(rf"{re.escape(basis)}-V(\d+)\.mbz", f.name))]
    n = a.version or (max(vorhanden, default=0) + 1)
    fassung = f"V{n}"
    ziel = ABLAGE / f"{basis}-{fassung}.mbz"
    if ziel.exists():
        fehler(f"{ziel.name} gibt es schon. Andere --version wählen.")

    s = Sicherung(a.sicherung)
    print(f"Sicherung: {s.pfad.name}  ({s.kurs()['vollname']})")
    blockplan = None
    if plan.get("blockplan"):
        blockplan = json.loads(projektpfad(plan["blockplan"]).read_text(encoding="utf-8"))
        print("Blockplan:", plan["blockplan"])
        print("\n".join(blockplan_modul.setze_blockplan(s, blockplan)))
    png = None if a.kursbild_behalten else kursbild(plan)
    print("\n".join(gestalten(s, plan, png)))
    setze_kursbeginn_und_namen(s, plan, beginn, fassung)
    print(f"  Kursbeginn: {de(beginn)}, 00:00 · Namen: {plan['kurs']['vollname']} {fassung} / {plan['kurs']['kurzname']} {fassung}")
    s.schreibe(ziel)

    vorher, nachher = pruef_fehler(s.pfad), pruef_fehler(ziel)
    neu = [f for f in nachher if f not in vorher]
    print(f"Prüfung: {len(nachher)} Meldung(en), davon {len(nachher) - len(neu)} schon in der ByCS-Sicherung" + (", keine neuen." if not neu else ":"))
    for f in neu:
        print("  NEU", f)

    (ABLAGE / f"Anleitung-{basis}-{fassung}.html").write_text(anleitung(plan, blockplan, ziel.name, beginn, fassung, s.pfad.name), encoding="utf-8")
    print(f"Geschrieben: {ziel}")
    print(f"Anleitung:   {ABLAGE / f'Anleitung-{basis}-{fassung}.html'}")
    sys.exit(1 if neu else 0)


if __name__ == "__main__":
    main()
