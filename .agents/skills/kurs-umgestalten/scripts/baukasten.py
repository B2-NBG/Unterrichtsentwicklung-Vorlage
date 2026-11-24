"""
baukasten.py - Farbschema-Baukasten für einen Kurs: zeigt die echten Reiter, Unterabschnitte und Aktivitäten der
Sicherung mit Icons und Kopfband-Sätzen aus dem Kursplan. Die Lehrkraft wählt Farben und Stil und gibt der KI den
Gestaltungscode. Die Seite funktioniert ohne Internet.

Aufruf im Projektordner:
  python .agents/skills/kurs-umgestalten/scripts/baukasten.py --plan <Kursplan> --sicherung <ByCS.mbz>
Ergebnis: Ressourcen/Kurssicherungen-ByCS/Farbschema-Baukasten-<Kurzname>.html (nur lokal, enthält Namen aus dem Kurs).
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kurslib import (ABLAGE, BANNER_EINHEITLICH, HAUSFARBEN, PAPIER, SKILL, Sicherung, gruppen_baum, lese_plan,  # noqa: E402
                     ohne_icon, projektpfad, slug)

TYP = {"scorm": "scorm", "resource": "datei", "folder": "datei", "assign": "aufgabe", "hvp": "h5p", "h5pactivity": "h5p",
       "quiz": "quiz", "url": "url", "label": "label", "page": "seite", "book": "seite"}


def kursinfo(s: Sicherung, plan: dict) -> dict:
    sek, mod = s.abschnitte(), s.module()
    deleg = {a["itemid"]: nr for nr, a in sek.items() if a["unter"]}
    reiter = {ohne_icon(r["name"]): r for r in plan["reiter"]}
    unter_icons = plan.get("unterabschnitte", {})

    def mit_icon(icon, basis): return f"{icon} {basis}" if icon else basis

    def inhalte(nr, tiefe=0):
        liste = []
        for cmid in sek[nr]["seq"]:
            mm = mod.get(cmid)
            if not mm or mm["typ"] == "qbank":
                continue
            if mm["typ"] == "subsection":
                if mm["inst"] in deleg and tiefe < 3:
                    u = sek[deleg[mm["inst"]]]
                    liste.append({"sub": html.escape(mit_icon(unter_icons.get(u["basis"], ""), u["basis"])),
                                  "items": inhalte(u["nr"], tiefe + 1), "h": 0 if mm["sichtbar"] else 1})
                continue
            name = mm["name"] if len(mm["name"]) <= 70 else mm["name"][:67] + "…"
            liste.append({"t": TYP.get(mm["typ"], "seite"), "n": html.escape(name), "h": 0 if mm["sichtbar"] else 1})
        return liste

    kurs = []
    for g in gruppen_baum(sek):
        a = sek[g[0]]
        e = reiter.get(a["basis"], {})
        k = e.get("bereich") or "A"
        tab = {"k": k, "n": html.escape(mit_icon(e.get("icon", ""), a["basis"])), "h": 0 if a["sichtbar"] else 1,
               "subs": [{"n": "📚 Übersicht", "icon": e.get("icon") or "📚", "titel": html.escape(e.get("titel") or a["basis"]),
                         "s": html.escape(e.get("satz", "")), "items": inhalte(g[0])}]}
        for nr in g[1:]:
            u = sek[nr]
            eu = reiter.get(u["basis"], {})
            sub = {"n": html.escape(mit_icon(eu.get("icon", ""), u["basis"])), "s": html.escape(eu.get("satz", "")),
                   "items": inhalte(nr)}
            if eu.get("titel"):
                sub["titel"] = html.escape(eu["titel"])
            if eu.get("bereich") and eu["bereich"] != k:
                sub["k"] = eu["bereich"]
            tab["subs"].append(sub)
        kurs.append(tab)

    kb = plan.get("kursbild", {})
    b = kb.get("banner", {})
    foto = ""
    if b.get("foto") and projektpfad(b["foto"]).exists():
        p = projektpfad(b["foto"])
        foto = f"data:image/{'png' if p.suffix.lower() == '.png' else 'jpeg'};base64," + base64.b64encode(p.read_bytes()).decode()
    titel, stufe = b.get("titel", "").upper(), b.get("stufe", "").upper()
    return {"vollname": plan["kurs"]["vollname"], "kurzname": plan["kurs"]["kurzname"], "code": plan.get("gestaltungscode", ""),
            "kopfzeile": plan["kurs"].get("kopfzeile", plan["kurs"]["vollname"]),
            "bereiche": plan["bereiche"], "kurs": kurs,
            "kb": {"zeile": kb.get("zeile", "").upper(), "titel": kb.get("titel", "")},
            "banner": {"titel": titel, "stufe": stufe, "untertitel": b.get("untertitel", ""), "foto": foto,
                       "lt": min(700, round(695 * max(len(titel), 1) / 6)), "ls": min(640, round(425 * max(len(stufe), 1) / 10))}}


def main():
    p = argparse.ArgumentParser(description="Farbschema-Baukasten für einen Kurs erzeugen.")
    p.add_argument("--plan", required=True, help="Kursplan (Name in Ressourcen/Kursumbau/ oder Pfad)")
    p.add_argument("--sicherung", required=True, help="Sicherung aus der ByCS (.mbz)")
    p.add_argument("--out", help="Ziel (.html), sonst in Ressourcen/Kurssicherungen-ByCS/")
    a = p.parse_args()
    plan = lese_plan(a.plan)
    ki = kursinfo(Sicherung(a.sicherung), plan)
    t = (SKILL / "templates" / "Farbschema-Baukasten.html").read_text(encoding="utf-8")
    e = lambda x: html.escape(x, quote=True)  # noqa: E731
    namen = [v.split(" ", 1)[-1] for v in plan["bereiche"].values()]
    for k, v in {"{{VOLLNAME}}": e(ki["vollname"]), "{{KURZNAME}}": e(ki["kurzname"]),
                 "{{BEREICHE}}": e(", ".join(namen[:-1]) + " und " + namen[-1]),
                 # Hausfarben aus dem Schulprofil (kurslib): Farbschema "SCHULE", Papierfarbe und einheitliches Banner
                 **{"{{HAUS_%s}}" % k: v for k, v in HAUSFARBEN.items()}, "{{HAUS_P}}": PAPIER,
                 **{"{{BANNER_%d}}" % i: v for i, v in enumerate(BANNER_EINHEITLICH)}}.items():
        t = t.replace(k, v)
    daten = json.dumps(ki, ensure_ascii=False).replace("</", "<\\/")
    t = t.replace("/*KURSINFO*/null", daten, 1)
    if "{{" in t or "/*KURSINFO*/" in t:
        sys.exit("Fehler: Platzhalter im Baukasten nicht ersetzt")
    ziel = Path(a.out) if a.out else ABLAGE / f"Farbschema-Baukasten-{slug(plan['kurs']['kurzname'])}.html"
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(t, encoding="utf-8")
    print(f"Baukasten: {ziel}  ({len(ki['kurs'])} Hauptreiter)")


if __name__ == "__main__":
    main()
