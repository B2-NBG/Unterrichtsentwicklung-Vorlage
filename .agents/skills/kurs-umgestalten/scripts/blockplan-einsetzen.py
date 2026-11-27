"""
blockplan-einsetzen.py - setzt einen Blockplan in eine vorhandene Moodle-Kurssicherung (.mbz) ein.

Jeder genannte Abschnitt (Reiter) ist danach für jede Klassengruppe ab Montag 0:01 ihrer n-ten Schulwoche sichtbar und
bleibt offen; vorher ist er ganz verborgen (Lehrkräfte sehen immer alles). Genutzt werden die Klassengruppen, die die
Moodle über die Klassen-Einschreibung anlegt (z. B. "K - MGF10a (6082)"). Alles andere in der Sicherung bleibt, wie es ist.
Reiternamen werden ohne Icon verglichen ("⚙️ Fertigungstechnik" = "Fertigungstechnik").

Meist ruft umgestalten.py das mit auf. Allein (nur Blockplan, sonst nichts):
  python .agents/skills/kurs-umgestalten/scripts/blockplan-einsetzen.py --sicherung <Sicherung.mbz> --plan <Blockplan.json> --out <neu.mbz>

Blockplan (JSON): "bloecke" (je Block "klassen" und die Montage seiner "schulwochen"), "gruppenname" (Muster mit {klasse}),
"abschnitte" (Reitername -> Nummer der Schulwoche), optional "gruppen_entfernen" (Gruppennamen).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kurslib import Sicherung, berlin, datum, ersetze, feld, fehler, norm, ohne_icon  # noqa: E402


def montag_0001(text: str) -> int:
    tag = datum(text)
    if tag.weekday() != 0:
        fehler(f"{text} ist kein Montag.")
    return berlin(tag, 0, 1)


def setze_blockplan(s: Sicherung, plan: dict) -> list[str]:
    """Setzt die Freigaben in s ein und gibt einen Bericht (Zeilen) zurück."""
    # Gruppen: vorhandene Klassengruppen finden, nicht gewünschte entfernen
    gruppen = s.text("groups.xml")
    entfernen = set(plan.get("gruppen_entfernen", []))
    weg = []
    for block in re.findall(r"  <group id=\"\d+\">.*?</group>\n", gruppen, re.S):
        if norm(feld(block, "name")) in entfernen:
            gruppen = gruppen.replace(block, "")
            weg.append(norm(feld(block, "name")))
    fehlt_g = entfernen - set(weg)
    if fehlt_g:
        print(f"Hinweis: Gruppe(n) zum Entfernen nicht in der Sicherung: {sorted(fehlt_g)}")
    gruppen_id = {norm(n): i for i, n in re.findall(r'<group id="(\d+)">\s*<name>(.*?)</name>', gruppen, re.S)}

    zweige_je_woche: dict[int, list] = {}
    for b in plan["bloecke"]:
        wochen = b["schulwochen"]
        if wochen != sorted(wochen):
            fehler(f"{b['name']}: Schulwochen nicht in zeitlicher Reihenfolge")
        for klasse in b["klassen"]:
            name = plan["gruppenname"].format(klasse=klasse)
            if name not in gruppen_id:
                fehler(f"Gruppe '{name}' gibt es in der Sicherung nicht. Vorhanden: {sorted(gruppen_id)}")
            for n, d in enumerate(wochen, start=1):
                zweige_je_woche.setdefault(n, []).append(
                    {"op": "&", "c": [{"type": "group", "id": int(gruppen_id[name])},
                                      {"type": "date", "d": ">=", "t": montag_0001(d)}]})

    # Abschnitte: Freigabe setzen und sichtbar schalten (das Sperren übernimmt die Freigabe)
    gesucht = {ohne_icon(k): v for k, v in plan["abschnitte"].items()}
    gefunden: dict[str, int] = {}
    bericht = []
    for pfad in sorted(s.dateien):
        if not re.fullmatch(r"sections/section_\d+/section\.xml", pfad):
            continue
        xml = s.text(pfad)
        name = ohne_icon(feld(xml, "name"))
        if name not in gesucht or feld(xml, "component") not in ("", "$@NULL@$"):
            continue  # Unterabschnitt (mod_subsection) mit gleichem Namen: folgt seinem Reiter
        if feld(xml, "number") == "0":
            fehler("Abschnitt 0 (Allgemein) lässt sich in Moodle nicht sperren")
        gefunden[name] = gefunden.get(name, 0) + 1
        woche = gesucht[name]
        if woche not in zweige_je_woche:
            fehler(f"'{name}': Schulwoche {woche} gibt es im Blockplan nicht")
        freigabe = json.dumps({"op": "|", "show": False, "c": zweige_je_woche[woche]}, separators=(",", ":"))
        xml = ersetze(xml, "availabilityjson", escape(freigabe), pfad)
        war_verborgen = feld(xml, "visible") == "0"
        xml = ersetze(xml, "visible", "1", pfad)
        s.setze(pfad, xml)
        bericht.append((int(feld(xml, "number")), name, woche, war_verborgen))
    fehlt = [k for k in gesucht if k not in gefunden]
    doppelt = [k for k, n in gefunden.items() if n > 1]
    if fehlt or doppelt:
        fehler(f"Reiter aus dem Blockplan nicht gefunden: {fehlt}; mehrfach vorhanden: {doppelt}")

    # Freigaben anderer Abschnitte und Aktivitäten dürfen nicht auf entfernte Gruppen zeigen
    alle_ids = set(gruppen_id.values())
    for pfad, inhalt in s.dateien.items():
        if pfad.endswith(("section.xml", "module.xml")):
            for gid in re.findall(r"&quot;type&quot;:&quot;group&quot;,&quot;id&quot;:(\d+)|\"type\":\"group\",\"id\":(\d+)",
                                  inhalt.decode("utf-8")):
                gid = next(x for x in gid if x)
                if gid not in alle_ids:
                    fehler(f"{pfad}: Voraussetzung zeigt auf eine entfernte Gruppe ({gid})")
    s.setze("groups.xml", gruppen)

    zeilen = [f"  Abschnitt {nr:>2}  {name:<50} offen ab Schulwoche {w:>2}" + ("  (war verborgen, jetzt sichtbar)" if war else "")
              for nr, name, w, war in sorted(bericht)]
    zeilen += [f"  {b['name']}: " + ", ".join(plan["gruppenname"].format(klasse=k) for k in b["klassen"]) for b in plan["bloecke"]]
    if weg:
        zeilen.append(f"  Entfernt: {', '.join(weg)}")
    return zeilen


def main():
    p = argparse.ArgumentParser(description="Blockplan (Freigabe je Klasse nach Datum) in eine Moodle-Sicherung einsetzen.")
    p.add_argument("--sicherung", required=True, help="Moodle-Kurssicherung (.mbz, ohne Nutzerdaten)")
    p.add_argument("--plan", required=True, help="Blockplan (.json)")
    p.add_argument("--out", required=True, help="neue Sicherung (.mbz)")
    a = p.parse_args()
    s = Sicherung(a.sicherung)
    zeilen = setze_blockplan(s, json.loads(Path(a.plan).read_text(encoding="utf-8")))
    s.schreibe(a.out)
    print(f"Geschrieben: {a.out}")
    print("\n".join(zeilen))


if __name__ == "__main__":
    main()
