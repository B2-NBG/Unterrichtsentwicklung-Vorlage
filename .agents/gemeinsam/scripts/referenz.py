"""
referenz.py - Sicherheitsnetz beim Umbau des Werkzeugs: baut alle Lernpakete und Kurse zweimal, einmal mit dem
Arbeitsstand und einmal mit einem Commit (Standard HEAD, jeweils mit dessen eigenen Skripten), und vergleicht den
Inhalt Datei für Datei. Ein Umbau, der nichts ändern soll (z. B. Schulprofil mit den Werten der eigenen Schule), muss "alles gleich"
melden. Weicht etwas ab, nennt das Skript Paket und Datei.

Aufruf im Projektordner (am Mac python3 statt python):
  python .agents/gemeinsam/scripts/referenz.py                 Arbeitsstand gegen HEAD
  python .agents/gemeinsam/scripts/referenz.py --gegen <Commit> Arbeitsstand gegen einen anderen Commit
  python .agents/gemeinsam/scripts/referenz.py --nur PuG       nur Pakete und Kurse, deren Pfad "PuG" enthält
Rückgabe: 0 = alles gleich, 1 = Abweichung oder Baufehler. Dauert einige Minuten (zwei volle Bauten).

Damit gleich auch gleich heißt, ist beim Bau festgelegt, was sonst jedes Mal anders wäre: Uhrzeit, Zufallszahlen und
Sicherungs-Kennung der Kurse und die Download-Links (statt der Linkseite feste Ersatz-Links, ohne Netz). Verglichen wird
der Inhalt jeder Datei im ZIP bzw. in der .mbz, nicht die Zeitstempel der Archive.
Nicht im Workflow "Werkzeug testen" (dort gäbe es nichts zu vergleichen), nur von Hand vor und nach einem Umbauschritt.
Arbeitet in einem Temp-Ordner (git worktree für den Commit), das Repo bleibt unverändert. Nur Python-Standardbibliothek.
"""
import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile

HIER = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HIER)))
SCORM = ('.agents', 'skills', 'baue-lernpaket', 'scripts', 'build-scorm.py')
KURSBAU = ('.agents', 'skills', 'baue-kurs', 'scripts', 'build-mbz.py')
ZEIT = 1767225600          # 01.01.2026, 00:00 UTC: feste Uhrzeit für die Kurse
SAAT = 4711                # feste Zufallszahlen je Kurs
ERSATZ_LINK = 'https://links.invalid/'
ZIP_ZEIT = (2026, 1, 1, 0, 0, 0)   # festes Datum der Einträge in jedem ZIP (sonst das Änderungsdatum der Datei)
TEXT = ('.html', '.htm', '.js', '.css', '.xml', '.svg', '.json', '.txt', '.md', '.csv')


def _modul(name, pfad):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _summe(name, daten):
    """SHA-256 des Inhalts. Textdateien ohne Unterschied CRLF/LF: Git checkt am Rechner CRLF aus, auf GitHub LF, und
    einzelne Dateien am Rechner haben noch LF. Das sagt nichts über das Werkzeug."""
    if name.lower().endswith(TEXT):
        daten = daten.replace(b'\r\n', b'\n')
    return hashlib.sha256(daten).hexdigest()


def inhalt(archiv):
    """{Datei im Archiv: SHA-256 des Inhalts} für ein ZIP oder eine .mbz (tar.gz)."""
    out = {}
    if zipfile.is_zipfile(archiv):
        with zipfile.ZipFile(archiv) as z:
            for n in z.namelist():
                if not n.endswith('/'):
                    out[n] = _summe(n, z.read(n))
    else:
        with tarfile.open(archiv, 'r:*') as t:
            for m in t.getmembers():
                if m.isfile():
                    out[m.name] = _summe(m.name, t.extractfile(m).read())
    return out


def bauen(root, nur):
    """Baut alles mit den Skripten aus root (in einem eigenen Prozess aufgerufen). Rückgabe: {Name: {…} oder Fehlertext}."""
    import random
    import time
    import uuid
    os.environ.pop('GITHUB_ACTIONS', None)   # gebaut() schreibt sonst ins Repo statt in den Temp-Ordner
    time.time = lambda: float(ZEIT)
    uuid.uuid4 = lambda: uuid.UUID(int=SAAT)
    von_datei = zipfile.ZipInfo.from_file.__func__

    def fest(cls, *args, **kw):   # ZIP-Einträge mit festem Datum: Kurse enthalten die Prüfsumme der Lernpakete
        info = von_datei(cls, *args, **kw)
        info.date_time = ZIP_ZEIT
        return info
    zipfile.ZipInfo.from_file = classmethod(fest)
    ergebnis = {}
    still = io.StringIO()
    with contextlib.redirect_stdout(still):
        scorm = _modul('build_scorm', os.path.join(root, *SCORM))
    um = scorm.unterrichtsmaterial
    for ordner in um.lernpakete():
        ordner = ordner.strip().strip('/')
        if nur and nur not in ordner:
            continue
        try:
            with contextlib.redirect_stdout(still):
                z = scorm.bauen(os.path.join(um.ROOT, *ordner.split('/')), nur_packen=True)
            ergebnis['Paket ' + ordner] = inhalt(z)
        except Exception as e:   # absichtlich breit: jeder Baufehler wird gemeldet, der Vergleich läuft weiter
            ergebnis['Paket ' + ordner] = 'Baufehler: %s: %s' % (type(e).__name__, e)
    kurse = [k for k in um.kursplaene() if not nur or nur in k]
    if kurse:
        kursbau = _modul('build_mbz', os.path.join(root, *KURSBAU))   # ohne Umleitung: stellt beim Laden die Ausgabe um
        kursbau.linkseite.holen = lambda: {}
        kursbau.linkseite.link = lambda paket, links=None: ERSATZ_LINK + os.path.basename(paket.replace('\\', '/'))
    for k in kurse:
        random.seed(SAAT)
        try:
            with contextlib.redirect_stdout(still):
                mbz = kursbau.bauen_aus_plan(k)
                ok = kursbau.pruefen(mbz) == 0
            ergebnis['Kurs ' + k] = inhalt(mbz) if ok else 'Prüfung der Kurssicherung nicht bestanden'
        except BaseException as e:   # build-mbz.py beendet sich bei Fehlern mit SystemExit
            if isinstance(e, KeyboardInterrupt):
                raise
            ergebnis['Kurs ' + k] = 'Baufehler: %s: %s' % (type(e).__name__, e)
    return ergebnis


def lauf(root, nur, tmp, name):
    """bauen() in einem eigenen Prozess mit eigenem Temp-Ordner (keine Module oder Pakete aus dem anderen Lauf)."""
    ziel = os.path.join(tmp, name + '.json')
    temp = os.path.join(tmp, name + '-temp')
    os.makedirs(temp)
    env = dict(os.environ, TMP=temp, TEMP=temp, TMPDIR=temp, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8')
    r = subprocess.run([sys.executable, os.path.abspath(__file__), '--bauen', root, '--aus', ziel] + (['--nur', nur] if nur else []),
                       cwd=root, env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0 or not os.path.isfile(ziel):
        raise RuntimeError('Bau mit %s ist abgebrochen:\n%s' % (name, (r.stdout + r.stderr)[-2000:]))
    with open(ziel, encoding='utf-8') as f:
        return json.load(f)


def vergleich(alt, neu):
    """Liste der Abweichungen (Texte), leer = alles gleich."""
    out = []
    for name in sorted(set(alt) | set(neu)):
        a, n = alt.get(name), neu.get(name)
        if a is None:
            out.append('%s: nur im Arbeitsstand' % name)
        elif n is None:
            out.append('%s: nur im Commit' % name)
        elif isinstance(a, str) or isinstance(n, str):
            if a != n:
                out.append('%s: Commit: %s | Arbeitsstand: %s' % (name, a if isinstance(a, str) else 'gebaut',
                                                                n if isinstance(n, str) else 'gebaut'))
            elif isinstance(n, str):
                out.append('%s: in beiden: %s' % (name, n))
        else:
            dateien = sorted(d for d in set(a) | set(n) if a.get(d) != n.get(d))
            if dateien:
                out.append('%s: %d Datei(en) anders: %s%s' % (name, len(dateien), ', '.join(dateien[:6]),
                                                             ' …' if len(dateien) > 6 else ''))
    return out


def main(argv=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # profil.py liegt daneben, egal wer main() aufruft
    import profil
    profil.utf8_ausgabe()
    ap = argparse.ArgumentParser(description='Alle Lernpakete und Kurse mit Arbeitsstand und Commit bauen und vergleichen.')
    ap.add_argument('--gegen', default='HEAD', help='Commit zum Vergleich (Standard HEAD)')
    ap.add_argument('--nur', default='', help='nur Pakete und Kurse, deren Pfad diesen Text enthält')
    ap.add_argument('--bauen', help=argparse.SUPPRESS)   # intern: in diesem Prozess mit den Skripten aus <root> bauen
    ap.add_argument('--aus', help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.bauen:
        with open(a.aus, 'w', encoding='utf-8') as f:
            json.dump(bauen(os.path.abspath(a.bauen), a.nur), f, indent=0, sort_keys=True)
        return 0

    tmp = tempfile.mkdtemp(prefix='referenz-')
    alt_root = os.path.join(tmp, 'commit')
    r = subprocess.run(['git', 'worktree', 'add', '--detach', '--quiet', alt_root, a.gegen], cwd=ROOT,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        print('FEHLER: git worktree für %s: %s' % (a.gegen, r.stderr.strip()))
        shutil.rmtree(tmp, ignore_errors=True)
        return 1
    try:
        print('Baue mit %s …' % a.gegen)
        alt = lauf(alt_root, a.nur, tmp, 'commit')
        print('Baue mit dem Arbeitsstand …')
        neu = lauf(ROOT, a.nur, tmp, 'arbeitsstand')
    except RuntimeError as e:
        print('FEHLER: %s' % e)
        return 1
    finally:
        subprocess.run(['git', 'worktree', 'remove', '--force', alt_root], cwd=ROOT, capture_output=True)
        shutil.rmtree(tmp, ignore_errors=True)
    pakete = sum(1 for n in neu if n.startswith('Paket '))
    kurse = sum(1 for n in neu if n.startswith('Kurs '))
    abw = vergleich(alt, neu)
    for z in abw:
        print('  ANDERS  ' + z)
    print('%d Lernpakete und %d Kurse verglichen: %s' % (pakete, kurse, 'alles gleich.' if not abw else '%d Abweichung(en).' % len(abw)))
    return 1 if abw else 0


if __name__ == '__main__':
    sys.exit(main())
