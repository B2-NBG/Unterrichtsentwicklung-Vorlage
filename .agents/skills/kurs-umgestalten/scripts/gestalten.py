"""
gestalten.py - gestaltet eine Moodle-Kurssicherung (Format Onetopic) nach Gestaltungscode und Kursplan.

Ändert nur Abschnittsnamen (Icons), Abschnittstexte (Kopfband, Stilblock), Reiterstile (Onetopic "tabstyles"),
Abschnittsfläche und Kursbild. Aktivitäten und Freigaben (Blockplan) bleiben unverändert.
Wird von umgestalten.py aufgerufen (Funktion gestalten).
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import time

from kurslib import PAPIER, Sicherung, cr, fehler, lese_code, ohne_icon, slug, tint

WORT = {"scorm": ("Lernpaket", "Lernpakete"), "hvp": ("Lernvideo", "Lernvideos"), "h5pactivity": ("Lernvideo", "Lernvideos"),
        "assign": ("Abgabe", "Abgaben"), "quiz": ("Test", "Tests"), "resource": ("Datei", "Dateien"), "url": ("Link", "Links"),
        "page": ("Seite", "Seiten")}
LINIE = "#111314"   # schwarz (Wada "Black")


def esc(s): return html.escape(s, quote=True)


def gestalten(s: Sicherung, plan: dict, png: bytes | None) -> list[str]:
    O, f = lese_code(plan["gestaltungscode"])
    G, TESTS_DUNKEL = f["G"], f["TESTS_DUNKEL"]
    FARBE = {k: f[k] for k in "AFBIT"}
    if O["j"] == "n":
        fehler("Icons aus (jn) ist im Umbau noch nicht umgesetzt")
    if s.kurs()["format"] != "onetopic":
        fehler("Der Kurs hat nicht das Format Onetopic (Reiter). Nur solche Kurse lassen sich so gestalten.")
    kopfzeile = plan["kurs"].get("kopfzeile", plan["kurs"]["vollname"])

    sek = s.abschnitte()
    mod = s.module()
    deleg = {a["itemid"]: nr for nr, a in sek.items() if a["unter"]}
    reiter = {ohne_icon(r["name"]): r for r in plan["reiter"]}
    unter_icons = plan.get("unterabschnitte", {})

    # ---------- Plan prüfen: jeder Reiter braucht einen Eintrag ----------
    fehlt = [f"{nr}: {a['name']}" for nr, a in sorted(sek.items()) if not a["unter"] and a["basis"] not in reiter]
    if fehlt:
        fehler("Diese Reiter fehlen im Kursplan unter \"reiter\" (uebersicht.py --entwurf hilft):\n  " + "\n  ".join(fehlt))
    ueber = sorted(set(reiter) - {a["basis"] for a in sek.values() if not a["unter"]})
    hinweise = [f"Im Kursplan, aber nicht im Kurs: {', '.join(ueber)}"] if ueber else []

    # Bereich je Abschnitt: eigener Eintrag, sonst der des Hauptreiters
    BEREICH, haupt = {}, "A"
    for nr, a in sorted(sek.items()):
        if a["unter"]:
            continue
        e = reiter[a["basis"]]
        if nr == 0 or a["level"] == 0:
            haupt = e.get("bereich") or "A"
        BEREICH[nr] = (e.get("bereich") or haupt, haupt)
        if BEREICH[nr][0] not in FARBE:
            fehler(f"Reiter '{a['name']}': Bereich '{BEREICH[nr][0]}' gibt es nicht (A, F, B, I oder T)")

    # ---------- Zählen für die Kopfband-Etiketten ----------
    def zaehle(nr, z):
        for cmid in sek[nr]["seq"]:
            mm = mod.get(cmid)
            if not mm or not mm["sichtbar"]:
                continue
            if mm["typ"] == "subsection":
                if mm["inst"] in deleg:
                    zaehle(deleg[mm["inst"]], z)
            elif mm["typ"] in WORT:
                w = WORT[mm["typ"]][0]
                z[w] = z.get(w, 0) + 1
        return z
    MEHRZAHL = {a: b for a, b in WORT.values()}

    # ---------- Maße aus dem Code (wie im Baukasten) ----------
    SP = {"k": .6, "n": 1, "l": 1.45}[O["m"]]
    KB = {"k": dict(p=.6, t=16, x=13, b=38, e=20), "n": dict(p=1, t=20, x=15, b=52, e=28),
          "g": dict(p=1.4, t=26, x=17, b=70, e=38)}[O["c"]]
    def rund(px_): return 0 if O["e"] == "e" else px_
    def px(v): return f"{round(v, 1):g}px"
    def schwach(c): return cr(c, "#ffffff") < 1.5
    SCHATTEN = "box-shadow:0 2px 8px rgba(0,0,0,.14);" if O["s"] == "j" else ""
    def flaeche(c): return {"w": "", "g": tint(c, .07), "k": tint(c, .14), "c": PAPIER}[O["f"]]

    # ---------- Kopfband (nur Inline-Stile, Tabelle statt Flexbox) ----------
    def kopfband(icon, titel, satz, c, chips):
        if O["k"] == "a":
            return ""
        dunkel = O["k"] == "d"
        if O["z"] == "n":
            chips = []
        chipstil = ("background-color:rgba(255,255,255,.14);color:#ffffff;" if dunkel
                    else f"background-color:#ffffff;color:{G};border:1px solid {tint(c, .45)};")
        chip = "".join(f'<span style="display:inline-block;font-size:12px;padding:2px 9px;margin:6px 6px 0 0;border-radius:12px;{chipstil}">{esc(x)}</span>' for x in chips)
        leiste = {"l": f"border-left:8px solid {c};", "u": f"border-bottom:6px solid {c};", "n": ""}[O["p"]]
        hg = G if dunkel else tint(c, .22)
        pv, ph = px(14 * KB["p"] * SP), px(16 * KB["p"] * SP)
        feld_ = "" if O["i"] == "n" else (
            f'<td style="width:{KB["b"] + 16}px;padding:{pv} 0 {pv} {ph};vertical-align:middle;border:0">'
            f'<div style="width:{KB["b"]}px;height:{KB["b"]}px;line-height:{KB["b"]}px;text-align:center;font-size:{KB["e"]}px;'
            f'background-color:{"#ffffff" if O["i"] == "w" else c};{"border:1px solid " + tint(c, .45) + ";" if O["i"] == "w" else ""}border-radius:{rund(12)}px">{icon}</div></td>')
        if dunkel:
            text = (f'<div style="font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:{tint(c, .9)};font-weight:700">{esc(kopfzeile)}</div>'
                    f'<div style="font-size:{KB["t"]}px;font-weight:700;color:#ffffff">{esc(titel)}</div>'
                    f'<div style="font-size:{KB["x"]}px;color:rgba(255,255,255,.85)">{esc(satz)}</div>')
        else:
            text = (f'<div style="font-size:{KB["t"]}px;font-weight:700;color:{G}">{esc(titel)}</div>'
                    f'<div style="font-size:{KB["x"]}px;color:{G}">{esc(satz)}</div>')
        return (f'<table role="presentation" style="width:100%;border-collapse:separate;border-spacing:0;background-color:{hg};{leiste}'
                f'border-radius:{rund(8)}px;margin:0 0 {px(12 * SP)} 0;{SCHATTEN}"><tbody><tr>{feld_}'
                f'<td style="padding:{pv} {ph};vertical-align:middle;border:0">{text}' + (f'<div>{chip}</div>' if chip else "") +
                '</td></tr></tbody></table>')

    # ---------- Reiterstile (Onetopic, Feld tabstyles; Maße in "others", sonst hängt Onetopic px an) ----------
    def schrift_auf(c): return "#ffffff" if cr(c, "#ffffff") >= cr(c, G) else G
    def form_haupt():
        lb = {"k": 8, "n": 0, "d": 4}[O["l"]]
        if O["q"] == "t":
            f_ = f"border-radius:{rund(7)}px {rund(7)}px 0 0;border-width:{lb}px 0 0 0;border-style:solid;"
        else:
            f_ = f"border-radius:{999 if O['q'] == 'p' else rund(4)}px;border-width:{2 if lb else 0}px;border-style:solid;margin:0 {px(4 * SP)} {px(4 * SP)} 0;"
        return f_ + f"padding:{px(8 * SP)} {px(14 * SP)} {px(7 * SP)};" + ("font-size:17px;" if O["g"] == "g" else "")
    def form_unter():
        if O["q"] == "t":
            f_ = f"border-radius:{rund(6)}px {rund(6)}px 0 0;"
        else:
            f_ = f"border-radius:{999 if O['q'] == 'p' else rund(4)}px;margin:0 {px(4 * SP)} {px(4 * SP)} 0;"
        return f_ + f"padding:{px(6 * SP)} {px(11 * SP)};" + ("font-size:16px;" if O["g"] == "g" else "")
    def hover(c):
        if O["o"] == "b":
            return {"background-color": tint(c, .5), "color": G}
        if O["o"] == "g":
            return {"background-color": G, "color": "#ffffff"}
        return None
    def unter_stile(c):
        lin = {"s": LINIE, "g": G, "b": c, "n": None}[O["u"]]
        w = int(O["d"])
        bg = "#ffffff" if O["w"] == "w" else tint(c, .12)
        if lin:
            norm_ = {"background-color": bg, "color": G, "font-weight": "normal", "others": form_unter() + f"border:{w}px solid {lin}"}
            akt = {"background-color": "#ffffff", "color": G, "font-weight": "bold",
                   "others": form_unter() + f"border:{w}px solid {lin};border-bottom:{w + 2 if O['q'] == 't' else w}px solid {lin}"}
        else:
            norm_ = {"background-color": bg, "color": G, "font-weight": "normal", "others": form_unter() + "border:0"}
            akt = {"background-color": "#ffffff", "color": G, "font-weight": "bold",
                   "others": form_unter() + f"border:0;border-bottom:3px solid {LINIE if schwach(c) else c}"}
        return norm_, akt
    def stil_haupt(k):
        c = FARBE[k]
        if k == "T" and TESTS_DUNKEL:
            d = {"default": {"background-color": tint(G, .85), "color": "#ffffff", "font-weight": "bold", "others": form_haupt() + f"border-color:{G}"},
                 "active": {"background-color": G, "color": "#ffffff",
                            "others": form_haupt() + f"border-color:#ffffff;box-shadow:inset 0 0 0 2px {G},inset 0 0 0 4px #ffffff"}}
        else:
            if O["h"] == "v":
                norm_ = {"background-color": c, "color": schrift_auf(c), "font-weight": "bold"}
            elif O["h"] == "w":
                norm_ = {"background-color": "#ffffff", "color": G, "font-weight": "bold"}
            else:
                norm_ = {"background-color": tint(c, .22), "color": G, "font-weight": "bold"}
            norm_["others"] = form_haupt() + f"border-color:{c}" + (";box-shadow:inset 0 0 0 1px #dee2e6" if O["h"] == "w" else "")
            if O["y"] == "b":
                akt = {"background-color": c, "color": schrift_auf(c), "others": form_haupt() + f"border-color:{G}"}
            else:
                akt = {"background-color": G, "color": "#ffffff", "others": form_haupt() + f"border-color:{c}"}
            d = {"default": norm_, "active": akt}
        hv = hover(c)
        if hv:
            d["hover"] = hv
        norm_u, _ = unter_stile(c)
        d["childs"] = norm_u
        d["childindex"] = dict(norm_u)
        return d
    def stil_unter(k):
        c = FARBE[k]
        norm_, akt = unter_stile(c)
        d = {"default": norm_, "active": akt}
        hv = hover(c)
        if hv:
            d["hover"] = hv
        return d

    # ---------- Stilblock im Abschnittstext: Unterabschnitte und Reiterleiste ----------
    # Moodle zeigt Abschnittstexte ungefiltert an (noclean). Onetopic zeigt nur den geöffneten Abschnitt, die Regeln
    # treffen also dessen Unterabschnitte. Keine IDs (die vergibt die Lernplattform bei der Wiederherstellung neu).
    def rahmen(nr, c):
        regeln = []
        lin = LINIE if schwach(c) else c
        sel = "li.delegated-section > .section-item"
        if O["r"] == "b":
            regeln.append(f"{sel}{{border:1px solid {tint(lin, .45)};border-left:6px solid {lin};border-radius:{rund(8)}px;background-color:#ffffff;padding:4px 14px;margin:{px(12 * SP)} 0;{SCHATTEN}}}")
        elif O["r"] == "s":
            regeln.append(f"{sel}{{border:1px solid {LINIE};border-left:6px solid {LINIE};border-radius:{rund(8)}px;background-color:#ffffff;padding:4px 14px;margin:{px(12 * SP)} 0;{SCHATTEN}}}")
        elif O["r"] == "g":
            regeln.append(f"{sel}{{border:1px solid #c8ccd1;border-radius:{rund(8)}px;background-color:#ffffff;padding:4px 14px;margin:{px(12 * SP)} 0;{SCHATTEN}}}")
        if O["x"] == "j":
            regeln.append(f"li.delegated-section .course-section-header{{background-color:{tint(c, .12)};border-radius:{rund(6)}px;padding:{px(9 * SP)} 12px}}")
        if O["q"] != "t":
            regeln.append("#tabs-tree-start .nav-tabs{border-bottom:0}")
        # Unterreiter "Übersicht" (tab_initial) trägt in Onetopic die Kennung des Hauptreiters und bekäme dessen Stil.
        # Doppelte ID im Selektor -> höherer Vorrang als die Regel des Hauptreiters; Aussehen wie die anderen Unterreiter.
        norm_, akt = unter_stile(FARBE[BEREICH[nr][1]])
        def decl(dct): return "".join(f"{k_}:{v_} !important;" if k_ != "others" else "".join(f"{x.strip()} !important;" for x in v_.split(";") if x.strip()) for k_, v_ in dct.items())
        basis = "#tabs-tree-start#tabs-tree-start .onetopic-tab-body .nav-item.subtopic.tab_initial a.nav-link"
        regeln.append(f"{basis}{{{decl(norm_)}}}{basis}.active{{{decl(akt)}}}")
        return f"<style>{''.join(regeln)}</style>"

    def setze_option(t, name, wert, sid):
        wert_x = esc(wert)
        muster = re.compile(r"(<name>" + name + r"</name>\s*<value>)(.*?)(</value>)", re.S)
        if muster.search(t):
            return muster.sub(lambda m: m.group(1) + wert_x + m.group(3), t, count=1)
        neu = (f'  <course_format_options id="{9000000000 + sid}{len(name)}">\n    <format>onetopic</format>\n'
               f'    <name>{name}</name>\n    <value>{wert_x}</value>\n  </course_format_options>\n')
        return t.replace("</section>", neu + "</section>")

    # ---------- Abschnitte umschreiben ----------
    titel_neu = {}   # section id -> neuer Name (für moodle_backup.xml)
    for nr, a in sorted(sek.items()):
        t = s.text(a["datei"])
        if a["unter"]:
            ic = unter_icons.get(a["basis"])
            if ic:
                neu = f"{ic} {a['basis']}"
                if neu != a["name"]:
                    t = re.sub(r"<name>.*?</name>", "<name>" + esc(neu) + "</name>", t, count=1, flags=re.S)
                    s.setze(a["datei"], t)
                    titel_neu[a["id"]] = neu
            continue
        e = reiter[a["basis"]]
        icon = e.get("icon") or ""
        name = a["name"] if nr == 0 or not icon else f"{icon} {a['basis']}"
        if name != a["name"]:
            t = re.sub(r"<name>.*?</name>", "<name>" + esc(name) + "</name>", t, count=1, flags=re.S)
            titel_neu[a["id"]] = name
        k = BEREICH[nr][0]
        z = zaehle(nr, {})
        chips = [f"{z[w]} {w if z[w] == 1 else MEHRZAHL[w]}" for w in dict.fromkeys(x[0] for x in WORT.values()) if w in z]
        summary = rahmen(nr, FARBE[k]) + kopfband(icon or "📚", e.get("titel") or a["basis"], e.get("satz", ""), FARBE[k], chips)
        t = re.sub(r"<summary>.*?</summary>", lambda _: "<summary>" + esc(summary) + "</summary>", t, count=1, flags=re.S)
        t = re.sub(r"<summaryformat>\d</summaryformat>", "<summaryformat>1</summaryformat>", t, count=1)
        stil = stil_haupt(k) if (nr == 0 or a["level"] == 0) else stil_unter(k)
        t = setze_option(t, "tabstyles", json.dumps(stil, ensure_ascii=False, separators=(",", ":")), a["id"])
        t = setze_option(t, "tabsectionbackground", flaeche(FARBE[k]), a["id"])
        s.setze(a["datei"], t)

    # Unterabschnitt-Aktivitäten gleich benennen
    neu_mod = {}
    for cmid, mm in mod.items():
        if mm["typ"] == "subsection":
            n = f"activities/subsection_{cmid}/subsection.xml"
            t = s.text(n)
            alt = html.unescape(re.search(r"<name>(.*?)</name>", t).group(1))
            ic = unter_icons.get(ohne_icon(alt))
            if ic:
                neu = f"{ic} {ohne_icon(alt)}"
                if neu != alt:
                    s.setze(n, t.replace(f"<name>{esc(alt)}</name>", f"<name>{esc(neu)}</name>", 1))
                    neu_mod[cmid] = neu

    # moodle_backup.xml: Titel von Abschnitten und Unterabschnitt-Aktivitäten
    t = s.text("moodle_backup.xml")
    def ersetze_titel(t, tag_id, id_wert, neu):
        block = "section" if tag_id == "sectionid" else "activity"
        muster = re.compile(r"(<" + block + r">\s*<" + tag_id + r">" + str(id_wert) + r"</" + tag_id + r">\s*(?:<[^>]+>[^<]*</[^>]+>\s*)*?<title>)(.*?)(</title>)", re.S)
        t2, n = muster.subn(lambda m: m.group(1) + esc(neu) + m.group(3), t, count=1)
        if n != 1:
            fehler(f"Titel für {tag_id} {id_wert} nicht gefunden")
        return t2
    for sid, neu in titel_neu.items():
        t = ersetze_titel(t, "sectionid", sid, neu)
    for cmid, neu in neu_mod.items():
        t = ersetze_titel(t, "moduleid", cmid, neu)
    s.setze("moodle_backup.xml", t)

    # ---------- Kursbild ersetzen ----------
    if png:
        jetzt = int(time.time())
        sha = hashlib.sha1(png).hexdigest()
        name = f"Kursbild-{slug(plan['kurs']['kurzname'])}.png"
        t = s.text("files.xml")
        blk = re.search(r'<file id="(\d+)">\s*<contenthash>(\w+)</contenthash>\s*<contextid>\d+</contextid>\s*<component>course</component>'
                        r'\s*<filearea>overviewfiles</filearea>(?:(?!</file>).)*?<filename>(?!\.<)[^<]+</filename>.*?</file>', t, re.S)
        if not blk:
            fehler("Die Sicherung hat noch kein Kursbild. Bitte in der Lernplattform erst irgendein Kursbild setzen und neu sichern.")
        alt_hash, b = blk.group(2), blk.group(0)
        b2 = re.sub(r"<contenthash>\w+</contenthash>", f"<contenthash>{sha}</contenthash>", b)
        for tag, wert in [("filename", name), ("source", name), ("filesize", str(len(png))), ("mimetype", "image/png"),
                          ("timecreated", str(jetzt)), ("timemodified", str(jetzt)), ("author", "$@NULL@$")]:
            b2 = re.sub(rf"<{tag}>.*?</{tag}>", f"<{tag}>{wert}</{tag}>", b2, count=1, flags=re.S)
        t = t.replace(b, b2)
        s.setze("files.xml", t)
        s.setze(f"files/{sha[:2]}/{sha}", png)
        if t.count(alt_hash) == 0:
            s.dateien.pop(f"files/{alt_hash[:2]}/{alt_hash}", None)

    zeilen = [f"  Gestaltet: {sum(1 for a in sek.values() if not a['unter'])} Reiter, "
              f"{sum(1 for a in sek.values() if a['unter'])} Unterabschnitte" + (", Kursbild ersetzt" if png else "")]
    return zeilen + [f"  Hinweis: {h}" for h in hinweise]
