"""
kursbild.py - Kursbild nach Gestaltungscode und Kursplan, wie im Farbschema-Baukasten.

Einstellung b im Code: k Kacheln, s Farbstreifen, t nur Text (1200 x 500); f Foto-Banner im Stil des Skills
kursbanner (1600 x 900; v e einheitlich in den Hausfarben oder v s aus dem Farbschema; n m mittig oder n o etwas höher).
Texte aus dem Kursplan unter "kursbild" ("zeile", "titel"; für das Foto-Banner "banner": titel, stufe, untertitel, foto).
Gerendert wird mit Chrome oder Edge (headless), Windows und Mac.

Allein: python .agents/skills/kurs-umgestalten/scripts/kursbild.py --plan <Kursplan> --out <Bild.png>
"""
from __future__ import annotations

import argparse
import base64
import os
import shutil
import subprocess
import sys
import tempfile
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kurslib import BANNER_EINHEITLICH, HAUSFARBEN, cr, fehler, lese_code, lese_plan, projektpfad, tint  # noqa: E402


def browser() -> str:
    for b in ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
              r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
              shutil.which("google-chrome") or "", shutil.which("chromium") or "", shutil.which("msedge") or ""]:
        if b and os.path.exists(b):
            return b
    fehler("Kein Chrome oder Edge gefunden: Das Kursbild braucht einen davon.")


def foto_banner(plan, O, f) -> tuple[str, int, int]:
    b = plan["kursbild"].get("banner") or fehler("Kursplan: kursbild.banner fehlt (Foto-Banner, Einstellung bf)")
    G, F, B, I = f["G"], f["F"], f["B"], f["I"]
    if O["v"] == "s" and G != HAUSFARBEN["G"]:   # bei den Hausfarben ist "aus dem Schema" = einheitlich
        akz = sorted([F, B, I], key=lambda c: cr(c, G), reverse=True)[0]
        bg, txt, sub = G, "#FFFFFF", tint(G, .22)
    else:
        bg, txt, sub, akz = BANNER_EINHEITLICH
    foto_pfad = projektpfad(b["foto"]) if b.get("foto") else None
    if foto_pfad and not foto_pfad.exists():
        fehler(f"Foto nicht gefunden: {b['foto']}")
    foto = ""
    if foto_pfad:
        art = "png" if foto_pfad.suffix.lower() == ".png" else "jpeg"
        daten = base64.b64encode(foto_pfad.read_bytes()).decode()
        foto = f'<image href="data:image/{art};base64,{daten}" x="800" y="0" width="800" height="900" preserveAspectRatio="xMidYMid slice"/>'
    font = 'font-family="Inter,\'Segoe UI\',system-ui,Arial"'
    dy = -60 if O["n"] == "o" else 0
    titel, stufe = b["titel"].upper(), b.get("stufe", "").upper()
    # Breiten wie beim Kursbanner-Skill (METALL 695, GRUNDSTUFE 425), für andere Wörter nach Länge
    lt, ls = min(700, round(695 * len(titel) / 6)), min(640, round(425 * len(stufe) / 10))
    text = (f'<text x="100" y="{415 + dy}" fill="{txt}" {font} font-size="168" font-weight="900" textLength="{lt}" lengthAdjust="spacingAndGlyphs">{escape(titel)}</text>'
            f'<rect x="100" y="{488 + dy}" width="96" height="7" fill="{akz}"/>'
            + (f'<text x="100" y="{578 + dy}" fill="{txt}" {font} font-size="50" font-weight="500" letter-spacing="9" textLength="{ls}" lengthAdjust="spacingAndGlyphs">{escape(stufe)}</text>' if stufe else "")
            + f'<text x="100" y="{640 + dy}" fill="{sub}" {font} font-size="27" letter-spacing="1">{escape(b.get("untertitel", ""))}</text>')
    svg = (f'<svg width="1600" height="900" viewBox="0 0 1600 900" xmlns="http://www.w3.org/2000/svg">'
           f'<defs><linearGradient id="v" x1="800" x2="1180" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{bg}"/>'
           f'<stop offset="1" stop-color="{bg}" stop-opacity="0"/></linearGradient></defs>'
           f'<rect width="1600" height="900" fill="{bg}"/>{foto}<rect x="799" width="381" height="900" fill="url(#v)"/>{text}</svg>')
    return svg, 1600, 900


def kachel_bild(plan, O, f) -> tuple[str, int, int]:
    G, F = f["G"], f["F"]
    kb = plan["kursbild"]
    ber = plan["bereiche"]
    tiles = [(f[k], ber[k].split(" ")[0]) for k in "FBI"] + [(f["T"], "📝")]
    schrift = 'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif"'
    balken = "".join(f'<rect x="{i * 300}" y="475" width="300" height="25" fill="{c}"/>' for i, (c, _) in enumerate(tiles))
    V = O["b"]
    tx = {"k": 400, "s": 370, "t": 600}[V]
    if V == "k":
        inhalt = ('<circle cx="880" cy="250" r="165" fill="none" stroke="#ffffff22" stroke-width="2"/>'
                  '<circle cx="880" cy="250" r="112" fill="none" stroke="#ffffff22" stroke-width="2" stroke-dasharray="12 8"/>'
                  '<line x1="690" y1="250" x2="1070" y2="250" stroke="#ffffff22" stroke-width="2" stroke-dasharray="30 8 4 8"/>'
                  '<line x1="880" y1="60" x2="880" y2="440" stroke="#ffffff22" stroke-width="2" stroke-dasharray="30 8 4 8"/>' +
                  "".join(f'<rect x="{x}" y="{y}" width="110" height="110" rx="18" fill="{c}" stroke="#ffffff55" stroke-width="2"/>'
                          f'<text x="{x + 55}" y="{y + 74}" font-size="54" text-anchor="middle">{e}</text>'
                          for (c, e), (x, y) in zip(tiles, [(760, 130), (890, 130), (760, 260), (890, 260)])))
    elif V == "s":
        balken = ""
        inhalt = "".join(f'<rect x="{700 + i * 95}" y="0" width="95" height="500" fill="{c}"/><text x="{747 + i * 95}" y="270" font-size="50" text-anchor="middle">{e}</text>'
                         for i, (c, e) in enumerate(tiles))
    else:
        inhalt = "".join(f'<circle cx="{540 + i * 40}" cy="345" r="11" fill="{c}"/>' for i, (c, _) in enumerate(tiles))
    unten = " · ".join(v.split(" ", 1)[-1] for v in ber.values())
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="500" viewBox="0 0 1200 500">
<defs><pattern id="g" width="48" height="48" patternUnits="userSpaceOnUse"><path d="M48 0H0V48" fill="none" stroke="#ffffff10" stroke-width="1"/></pattern></defs>
<rect width="1200" height="500" fill="{G}"/><rect width="1200" height="500" fill="url(#g)"/>{balken}{inhalt}
<text x="{tx}" y="178" fill="{tint(F, .85)}" {schrift} font-size="21" font-weight="700" letter-spacing="4" text-anchor="middle">{escape(kb.get("zeile", "").upper())}</text>
<text x="{tx}" y="252" fill="#ffffff" {schrift} font-size="62" font-weight="800" text-anchor="middle">{escape(kb.get("titel", ""))}</text>
<text x="{tx}" y="298" fill="#ffffffcc" {schrift} font-size="21" text-anchor="middle">{escape(unten)}</text>
</svg>'''
    return svg, 1200, 500


def kursbild(plan) -> bytes:
    O, f = lese_code(plan["gestaltungscode"])
    if "kursbild" not in plan:
        fehler("Kursplan: 'kursbild' fehlt")
    svg, w, h = foto_banner(plan, O, f) if O["b"] == "f" else kachel_bild(plan, O, f)
    seite = f'<!doctype html><html><head><meta charset="utf-8"></head><body style="margin:0;overflow:hidden">{svg}</body></html>'
    b = browser()
    with tempfile.TemporaryDirectory() as tmp:
        html_datei, ziel = os.path.join(tmp, "kursbild.html"), os.path.join(tmp, "kursbild.png")
        Path(html_datei).write_text(seite, encoding="utf-8")
        for _ in range(2):   # bei leerem Ergebnis einmal wiederholen (wie im Skill kursbanner)
            subprocess.run([b, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1",
                            f"--window-size={w},{h}", f"--user-data-dir={os.path.join(tmp, 'profil')}",
                            f"--screenshot={ziel}", Path(html_datei).as_uri()], capture_output=True, timeout=120)
            if os.path.exists(ziel) and os.path.getsize(ziel) > 10000:
                return Path(ziel).read_bytes()
    fehler("Das Kursbild ließ sich nicht erzeugen (Browser lieferte kein Bild).")


def main():
    p = argparse.ArgumentParser(description="Kursbild nach Gestaltungscode und Kursplan erzeugen.")
    p.add_argument("--plan", required=True, help="Kursplan (Name in Ressourcen/Kursumbau/ oder Pfad)")
    p.add_argument("--out", required=True, help="Ziel (.png)")
    a = p.parse_args()
    Path(a.out).write_bytes(kursbild(lese_plan(a.plan)))
    print("Kursbild:", a.out)


if __name__ == "__main__":
    main()
