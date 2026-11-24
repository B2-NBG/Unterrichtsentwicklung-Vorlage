"""
kurslib.py - gemeinsame Bausteine des Skills kurs-umgestalten.

Sicherung (.mbz) lesen und schreiben, Abschnitte und Aktivitäten, Kursplan (Ressourcen/Kursumbau/*.json),
Gestaltungscode aus dem Farbschema-Baukasten, Farben und Zeiten (Berlin).
Nur Python-Standardbibliothek (Windows und Mac, ab Python 3.9).
"""
from __future__ import annotations

import datetime as dt
import html
import json
import re
import sys
import tarfile
import time
import unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
PROJEKT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJEKT / ".agents" / "gemeinsam" / "scripts"))
from mbz import Archiv  # noqa: E402
import profil  # noqa: E402  (Schulprofil schule.txt: Schulfarben)

ABLAGE = PROJEKT / "Ressourcen" / "Kurssicherungen-ByCS"   # nur lokal (.gitignore)
WADA = SKILL / "daten" / "wada-colors.json"                # Sanzo Wada, digitalisiert von mattdesl


def fehler(text: str):
    print(f"Fehler: {text}", file=sys.stderr)
    sys.exit(1)


# ---------- Namen ----------
def norm(text: str) -> str:
    return unicodedata.normalize("NFC", html.unescape(text)).strip()


def ohne_icon(name: str) -> str:
    """'📏 TZ1 / Einheiten' -> 'TZ1 / Einheiten'. Ein Name ohne Icon bleibt, wie er ist."""
    return re.sub(r"^[^\w(\[„\"]+\s+", "", norm(name))


def slug(text: str) -> str:
    """Kurzname -> Dateiname: 'MGF10 FU 26/27' -> 'MGF10-FU-2627'."""
    t = text.replace("/", "")
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("Ä", "Ae"), ("Ö", "Oe"), ("Ü", "Ue"), ("ß", "ss")):
        t = t.replace(a, b)
    return re.sub(r"[^A-Za-z0-9]+", "-", t).strip("-")


# ---------- Zeit (Berlin, MEZ/MESZ nach EU-Regel) ----------
def _letzter_sonntag(jahr: int, monat: int) -> dt.date:
    tag = dt.date(jahr, monat + 1, 1) - dt.timedelta(days=1)
    return tag - dt.timedelta(days=(tag.weekday() + 1) % 7)


def berlin(tag: dt.date, stunde: int = 0, minute: int = 0) -> int:
    sommer = _letzter_sonntag(tag.year, 3) < tag <= _letzter_sonntag(tag.year, 10)
    utc = dt.datetime(tag.year, tag.month, tag.day, stunde, minute, tzinfo=dt.timezone.utc) - dt.timedelta(hours=2 if sommer else 1)
    return int(utc.timestamp())


def datum(text: str) -> dt.date:
    """'17.11.2026' oder '2026-11-17'."""
    m = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", text.strip())
    try:
        return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else dt.date.fromisoformat(text.strip())
    except ValueError:
        fehler(f"'{text}' ist kein Datum (TT.MM.JJJJ)")


def de(tag: dt.date) -> str:
    return tag.strftime("%d.%m.%Y")


# ---------- Sicherung ----------
def feld(xml: str, tag: str) -> str:
    m = re.search(rf"<{tag}>(.*?)</{tag}>", xml, re.S)
    return m.group(1) if m else ""


def ersetze(xml: str, tag: str, wert: str, wo: str = "") -> str:
    neu, n = re.subn(rf"<{tag}>.*?</{tag}>", lambda _: f"<{tag}>{wert}</{tag}>", xml, count=1, flags=re.S)
    if n != 1:
        fehler(f"<{tag}> nicht gefunden {wo}")
    return neu


class Sicherung:
    """Alle Dateien einer .mbz im Speicher. Schreiben mit neuem .ARCHIVE_INDEX (wie Moodle)."""

    def __init__(self, pfad):
        self.pfad = Path(pfad)
        if not self.pfad.exists():
            fehler(f"Sicherung nicht gefunden: {pfad}")
        self.dateien: dict[str, bytes] = {}
        with tarfile.open(self.pfad, "r:gz") as tar:
            for m in tar:
                if m.isfile() and m.name != ".ARCHIVE_INDEX":
                    self.dateien[m.name] = tar.extractfile(m).read()
        if re.search(rb"<name>users</name>\s*<value>1</value>", self.dateien.get("moodle_backup.xml", b"")):
            fehler("Die Sicherung enthält Nutzerdaten. Bitte in der ByCS ohne Nutzerdaten sichern.")

    def text(self, n: str) -> str:
        return self.dateien[n].decode("utf-8")

    def setze(self, n: str, t: str | bytes):
        self.dateien[n] = t.encode("utf-8") if isinstance(t, str) else t

    def schreibe(self, ziel):
        arch = Archiv(int(time.time()))
        for pfad, inhalt in self.dateien.items():
            arch.datei(pfad, inhalt)
        arch.schreibe(Path(ziel))

    # Kurs
    def kurs(self) -> dict:
        t = self.text("course/course.xml")
        return dict(vollname=norm(feld(t, "fullname")), kurzname=norm(feld(t, "shortname")),
                    format=feld(t, "format"), kursbeginn=int(feld(t, "startdate") or 0))

    # Abschnitte: nummer -> dict
    def abschnitte(self) -> dict[int, dict]:
        s = {}
        for n in self.dateien:
            if not re.fullmatch(r"sections/section_\d+/section\.xml", n):
                continue
            t = self.text(n)
            nr = int(feld(t, "number"))
            name = norm(feld(t, "name"))
            if name in ("", "$@NULL@$"):
                name = "Allgemein" if nr == 0 else f"Abschnitt {nr}"
            lv = re.search(r"<name>level</name>\s*<value>(\d)</value>", t)
            comp = feld(t, "component")
            s[nr] = dict(datei=n, nr=nr, id=int(re.search(r'<section id="(\d+)"', t).group(1)), name=name,
                         basis=ohne_icon(name), unter=comp == "mod_subsection", itemid=feld(t, "itemid"),
                         level=int(lv.group(1)) if lv else 0, sichtbar=feld(t, "visible") != "0",
                         seq=[int(x) for x in feld(t, "sequence").split(",") if x.strip().isdigit()])
        return s

    # Aktivitäten: cmid -> dict(typ, sichtbar, name, inst)
    def module(self) -> dict[int, dict]:
        m = {}
        for n in self.dateien:
            r = re.fullmatch(r"activities/(\w+?)_(\d+)/module\.xml", n)
            if not r:
                continue
            typ, cmid = r.group(1), int(r.group(2))
            t = self.text(n)
            eintrag = dict(typ=typ, sichtbar=feld(t, "visible") == "1", name="", inst=None)
            inhalt = self.dateien.get(f"activities/{typ}_{cmid}/{typ}.xml")
            if inhalt:
                x = inhalt.decode("utf-8")
                eintrag["name"] = norm(re.sub(r"<[^>]+>", " ", html.unescape(feld(x, "name"))))
                i = re.search(rf'<{typ} id="(\d+)"', x)
                eintrag["inst"] = i.group(1) if i else None
            m[cmid] = eintrag
        return m


def gruppen_baum(abschnitte: dict[int, dict]) -> list[list[int]]:
    """Hauptreiter (level 0) mit ihren Unterreitern (level 1), in Kursreihenfolge. Unterabschnitte fehlen hier."""
    gruppen, akt = [], None
    for nr in sorted(abschnitte):
        a = abschnitte[nr]
        if a["unter"]:
            continue
        if nr == 0 or a["level"] == 0 or akt is None:
            akt = [nr]
            gruppen.append(akt)
        else:
            akt.append(nr)
    return gruppen


# ---------- Kursplan ----------
def lese_plan(pfad) -> dict:
    p = Path(pfad)
    if not p.exists():
        kandidat = PROJEKT / "Ressourcen" / "Kursumbau" / (str(pfad) if str(pfad).endswith(".json") else f"{pfad}.json")
        p = kandidat if kandidat.exists() else p
    if not p.exists():
        fehler(f"Kursplan nicht gefunden: {pfad}")
    plan = json.loads(p.read_text(encoding="utf-8"))
    plan["_pfad"] = p
    for k in ("kurs", "bereiche", "reiter"):
        if k not in plan:
            fehler(f"Kursplan {p.name}: '{k}' fehlt")
    return plan


def projektpfad(text: str) -> Path:
    p = Path(text)
    return p if p.is_absolute() else PROJEKT / p


def reiter_im_plan(plan: dict) -> dict[str, dict]:
    return {ohne_icon(r["name"]): r for r in plan["reiter"]}


# ---------- Farben ----------
def rgb(h): return [int(h[i:i + 2], 16) for i in (1, 3, 5)]
def tint(h, p): return "#" + "".join(f"{round(255 - (255 - x) * p):02x}" for x in rgb(h))


def lum(h):
    r = [x / 255 for x in rgb(h)]
    r = [x / 12.92 if x <= .03928 else ((x + .055) / 1.055) ** 2.4 for x in r]
    return .2126 * r[0] + .7152 * r[1] + .0722 * r[2]


def cr(a, b):
    x, y = sorted([lum(a), lum(b)], reverse=True)
    return (x + .05) / (y + .05)


# ---------- Gestaltungscode (Legende im Baukasten: OPTIONEN und "So ist der Code aufgebaut") ----------
O_STD = {"v": "e", "n": "m", "q": "t", "j": "j", "o": "n", "m": "n", "c": "n", "b": "k", "k": "h", "z": "j", "i": "f", "p": "l",
         "f": "g", "h": "t", "l": "d", "y": "g", "g": "n", "w": "g", "u": "s", "d": "1", "r": "b", "x": "n", "e": "r", "s": "n"}
ERLAUBT = {"v": "es", "n": "mo", "q": "tpk", "j": "jn", "o": "nbg", "m": "knl", "c": "kng", "b": "kstf", "k": "hda", "z": "jn",
           "i": "fwn", "p": "lun", "f": "wgkc", "h": "tvw", "l": "dkn", "y": "gb", "g": "ng", "w": "gw", "u": "sgbn", "d": "12",
           "r": "bsgn", "x": "nj", "e": "re", "s": "nj"}
# Schulfarben aus dem Schulprofil (schule.txt): G Grundfarbe, F/B/I Bereiche, PAPIER mögliche Abschnittsfläche.
# Gestaltungscode "SCHULE" = Schulfarben der Schule.
HAUSFARBEN = {k: profil.wert(n).lower() for k, n in (("G", "Farbe-Haupt"), ("F", "Farbe-Akzent"),
                                                    ("B", "Farbe-Zweit"), ("I", "Farbe-Dritt"))}
PAPIER = profil.wert("Farbe-Papier").lower()
SCHUL_CODES = ("SCHULE",)
# Einheitliches Banner (Skill kursbanner): Fläche, Text, Unterzeile, Akzent
BANNER_EINHEITLICH = (profil.wert("Farbe-Haupt"), profil.wert("Farbe-Papier"), profil.wert("Farbe-Band-Text"),
                      profil.wert("Farbe-Akzent"))


def lese_code(code: str):
    """Gibt (O, Farben) zurück. Farben: G Grundfarbe, F/B/I Bereiche, A Allgemein, T Tests, dazu TESTS_DUNKEL."""
    O = dict(O_STD)
    teile = code.strip().replace(" ", "").split("-")
    m = re.fullmatch(r"(\d{1,3})(x?)|X|SCHULE", teile.pop(0), re.I)
    if not m:
        fehler("Gestaltungscode: Anfang muss die Kombinationsnummer, SCHULE oder X sein")
    farben = {}
    if m.group(0).upper() in SCHUL_CODES:
        farben = dict(HAUSFARBEN)
    if m.group(1):
        vier = sorted([c["hex"].lower() for c in json.loads(WADA.read_text(encoding="utf-8"))
                       if int(m.group(1)) in c["combinations"]], key=lum)
        if len(vier) != 4:
            fehler(f"Kombination Nr. {m.group(1)} hat nicht vier Farben")
        farben = dict(zip("GFBI", vier))   # dunkelste = Grundfarbe, dann nach Helligkeit (wie im Baukasten)
    modus = {"A": "neutral", "T": "dunkel"}
    for p in teile:
        if re.fullmatch(r"[a-z][a-z0-9]", p) and p[0] in ERLAUBT and p[1] in ERLAUBT[p[0]]:
            O[p[0]] = p[1]
        elif p in ("an", "ae"):
            modus["A"] = "eigen" if p == "ae" else "neutral"
        elif p in ("td", "te"):
            modus["T"] = "eigen" if p == "te" else "dunkel"
        elif re.fullmatch(r"[GFBIAT][0-9a-fA-F]{6}", p):
            farben[p[0]] = "#" + p[1:].lower()
        else:
            fehler(f"Gestaltungscode: '{p}' nicht erkannt")
    if any(k not in farben for k in "GFBI"):
        fehler("Gestaltungscode: Farben fehlen (bei X alle vier als G…, F…, B…, I… angeben)")
    G = farben["G"]
    return O, dict(G=G, F=farben["F"], B=farben["B"], I=farben["I"],
                   A=farben["A"] if modus["A"] == "eigen" else tint(G, .3),
                   T=farben["T"] if modus["T"] == "eigen" else tint(G, .6),
                   TESTS_DUNKEL=modus["T"] == "dunkel")
