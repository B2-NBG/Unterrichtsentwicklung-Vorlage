"""
uebersicht.py - zeigt die Gliederung einer Moodle-Kurssicherung (Reiter, Unterreiter, Unterabschnitte, Anzahl der Inhalte,
Kursbeginn) und gleicht sie mit Kursplan und Blockplan ab. Mit --entwurf entsteht ein Kursplan-Entwurf für einen neuen Kurs.

Aufruf im Projektordner:
  python .agents/skills/kurs-umgestalten/scripts/uebersicht.py --sicherung <Sicherung.mbz> [--plan <Kursplan>]
  python .agents/skills/kurs-umgestalten/scripts/uebersicht.py --sicherung <Sicherung.mbz> --entwurf Ressourcen/Kursumbau/Kursumbau-<Kurs>.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kurslib import Sicherung, de, fehler, gruppen_baum, lese_plan, ohne_icon, projektpfad  # noqa: E402


def icon_von(name: str) -> str:
    basis = ohne_icon(name)
    return name[:len(name) - len(basis)].strip() if basis != name else ""


def main():
    p = argparse.ArgumentParser(description="Gliederung einer Moodle-Kurssicherung zeigen und mit dem Kursplan abgleichen.")
    p.add_argument("--sicherung", required=True)
    p.add_argument("--plan", help="Kursplan zum Abgleichen")
    p.add_argument("--entwurf", help="Kursplan-Entwurf hierhin schreiben (nur wenn es die Datei noch nicht gibt)")
    a = p.parse_args()

    s = Sicherung(a.sicherung)
    k = s.kurs()
    sek, mod = s.abschnitte(), s.module()
    deleg = {x["itemid"]: nr for nr, x in sek.items() if x["unter"]}
    beginn = dt.datetime.fromtimestamp(k["kursbeginn"]).date() if k["kursbeginn"] else None
    print(f"Kurs: {k['vollname']}  ({k['kurzname']}), Format {k['format']}, Kursbeginn {de(beginn) if beginn else '-'}")
    if k["format"] != "onetopic":
        print("Achtung: kein Reiter-Kurs (Onetopic). Gestalten geht nur mit Onetopic, der Blockplan auch so.")

    def anzahl(nr):
        n = 0
        for cmid in sek[nr]["seq"]:
            mm = mod.get(cmid)
            if mm and mm["typ"] == "subsection" and mm["inst"] in deleg:
                n += anzahl(deleg[mm["inst"]])
            elif mm and mm["typ"] != "qbank":
                n += 1
        return n

    def unter(nr):
        return [sek[deleg[mod[c]["inst"]]] for c in sek[nr]["seq"] if c in mod and mod[c]["typ"] == "subsection" and mod[c]["inst"] in deleg]

    plan = lese_plan(a.plan) if a.plan else None
    im_plan = {ohne_icon(r["name"]) for r in plan["reiter"]} if plan else set()
    bp = {}
    if plan and plan.get("blockplan"):
        bp = {ohne_icon(x): w for x, w in json.loads(projektpfad(plan["blockplan"]).read_text(encoding="utf-8"))["abschnitte"].items()}
    alle_unter = set()
    for g in gruppen_baum(sek):
        for i, nr in enumerate(g):
            x = sek[nr]
            marke = ("" if x["sichtbar"] else " [verborgen]") + (f" [Schulwoche {bp[x['basis']]}]" if x["basis"] in bp else "")
            marke += " [FEHLT IM KURSPLAN]" if plan and x["basis"] not in im_plan else ""
            print(f"{'' if i == 0 else '    '}{nr:>3} {x['name']}  ({anzahl(nr)} Inhalte){marke}")
            for u in unter(nr):
                alle_unter.add(u["basis"])
                print(f"{'        ' if i else '    '}  · {u['name']}  ({anzahl(u['nr'])})")
    if plan:
        weg = sorted(im_plan - {x["basis"] for x in sek.values() if not x["unter"]})
        if weg:
            print("Im Kursplan, aber nicht im Kurs:", ", ".join(weg))
        ohne = sorted(b for b in alle_unter if b not in plan.get("unterabschnitte", {}))
        if ohne:
            print("Unterabschnitte ohne Icon im Kursplan:", ", ".join(ohne))
        bp_weg = sorted(set(bp) - {x["basis"] for x in sek.values() if not x["unter"]})
        if bp_weg:
            print("Im Blockplan, aber nicht im Kurs:", ", ".join(bp_weg))

    if a.entwurf:
        ziel = projektpfad(a.entwurf)
        if ziel.exists():
            fehler(f"{a.entwurf} gibt es schon. Bestehende Kursplaene nicht überschreiben.")
        haupt = [sek[g[0]] for g in gruppen_baum(sek)]
        bereiche_kand = [h for h in haupt[1:] if not re.search(r"test", h["basis"], re.I)][:3]
        buchst = {h["nr"]: b for h, b in zip(bereiche_kand, "FBI")}
        reiter = []
        for g in gruppen_baum(sek):
            for i, nr in enumerate(g):
                x = sek[nr]
                e = {"name": x["basis"], "icon": icon_von(x["name"])}
                if i == 0:
                    e["bereich"] = "A" if nr == 0 else buchst.get(nr, "T" if re.search(r"test", x["basis"], re.I) else "A")
                e["satz"] = ""
                reiter.append(e)
        vollname = re.sub(r"\s+V\d+$", "", k["vollname"])
        entwurf = {
            "_hinweis": "Entwurf aus uebersicht.py: Icons, Bereiche, Sätze (ein Satz 'Darum geht's' je Reiter) und Kursbild-Texte ergänzen.",
            "kurs": {"vollname": vollname, "kurzname": re.sub(r"\s+V\d+$", "", k["kurzname"]), "kopfzeile": vollname},
            "blockplan": None, "gestaltungscode": "SCHULE",
            "bereiche": {buchst[h["nr"]]: (icon_von(h["name"]) + " " + h["basis"]).strip() for h in bereiche_kand},
            "kursbild": {"zeile": "", "titel": "", "banner": {"titel": "", "stufe": "", "untertitel": "", "foto": ""}},
            "reiter": reiter,
            "unterabschnitte": {b: icon_von(next(x["name"] for x in sek.values() if x["unter"] and x["basis"] == b)) for b in sorted(alle_unter)},
        }
        for b in "FBI":
            entwurf["bereiche"].setdefault(b, f"Bereich {b}")
        ziel.parent.mkdir(parents=True, exist_ok=True)
        ziel.write_text(json.dumps(entwurf, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"Entwurf geschrieben: {ziel}")


if __name__ == "__main__":
    main()
