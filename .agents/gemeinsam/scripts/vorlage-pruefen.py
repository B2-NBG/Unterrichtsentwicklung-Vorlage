"""
vorlage-pruefen.py - prüft die Vorlagen der Teams in Vorlagen/<team>/<Name>.html.

Aufruf (im Projektordner, am Mac python3 statt python):
  python .agents/gemeinsam/scripts/vorlage-pruefen.py                    alle Vorlagen der Teams
  python .agents/gemeinsam/scripts/vorlage-pruefen.py Vorlagen/<Teamname>/Name.html [weitere]

Zwei Arten (Regeln: seite.md, Anleitung: Vorlagen/LIESMICH.md):
  Layout-Vorlage (Normalfall): eigenes Aussehen, gemeinsamer Kern. Geprüft wird: Anfang <!doctype html>, Ende </html>,
    TEMPLATE-Kommentar am Anfang (beschreibt die Bausteine), die vier markierten Blöcke aus Fachunterricht.html
    (head, tools, modals, scripts) sind da und aktuell (sonst: sync-vorlage.py --vorlagen), eigener Stil und eigenes
    Script stehen nur in den markierten Blöcken "<team>/<Name>.html:stil" und "<team>/<Name>.html:script", keine
    externen Ressourcen, <meta name="loesung-hash"> ist da, die Name-Zelle (id="nameOut") ist da.
  Freie Vorlage: <meta name="vorlage-art" content="frei"> und <meta name="vorlage" content="<team>/<Name>.html">.
    Geprüft wird: Anfang und Ende, keine externen Ressourcen, <meta name="loesung-hash"> ist da. Seiten daraus haben keine Bewertung.
pruefen.py ruft pruefe() für jede geänderte Vorlage auf (vor dem Commit und auf GitHub).
Exitcode 0 = alles bestanden, 1 = Fehler gefunden. Nur Python-Standardbibliothek.
"""
import importlib.util
import os
import re
import sys

HIER = os.path.dirname(os.path.abspath(__file__))


def _modul(name, pfad):
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location(name, pfad)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sync = _modul('sync_vorlage', os.path.join(HIER, 'sync-vorlage.py'))


def extern(s):
    """Externe Ressourcen (nicht offline): Liste von Fundstellen."""
    funde = [s[m.start():m.start() + 80] for m in
             re.finditer(r'<(?:img|script|iframe|source|video|audio)\b[^>]*\ssrc\s*=\s*["\']?https?:', s)]
    funde += [s[m.start():m.start() + 80] for m in re.finditer(r'<link\b[^>]*href\s*=\s*["\']?https?:', s)]
    funde += [s[m.start():m.start() + 80] for m in re.finditer(r'@import\s+(?:url\()?["\']?https?:', s)]
    return funde


def pruefe(pfad):
    """(Fehler, Hinweise) für eine Vorlage Vorlagen/<team>/<Name>.html."""
    fehler, hinweise = [], []
    s, _ = sync.lesen(pfad)
    k = sync.kennung(pfad)
    if not s.lstrip().lower().startswith('<!doctype html>'):
        fehler.append('1. Zeile ist nicht <!doctype html>')
    if not s.rstrip().endswith('</html>'):
        fehler.append('Datei endet nicht mit </html>')
    fehler += ['externe Ressource (nicht offline): ' + f for f in extern(s)]
    if not re.search(r'<meta\s+name="loesung-hash"\s+content="[^"]*"', s):
        fehler.append('<meta name="loesung-hash" content=""> fehlt (Lösungssperre)')
    if sync.ist_frei(s):
        if sync.vorlage_von(s).lower() != k.lower():
            fehler.append('Freie Vorlage: <meta name="vorlage" content="%s"> fehlt oder nennt eine andere Datei' % k)
        hinweise.append('Freie Vorlage: Seiten daraus haben keine Bewertung und werden nur auf die Grundregeln geprüft.')
        return fehler, hinweise
    if not re.search(r'<!--\s*\n\s*TEMPLATE', s):
        fehler.append('TEMPLATE-Kommentar am Anfang fehlt (zweite Zeile "<!--", dann "  TEMPLATE …" mit den Bausteinen)')
    if 'Allgemeinbildung.html:' in sync.ohne_kommentare(s).join(('', '')) or '<!-- Allgemeinbildung.html:' in s \
            or '/* Layout "Lernschritte":' in s:
        fehler.append('Reste von Allgemeinbildung.html: Die Markierungen "Allgemeinbildung.html:stil|script" in "%s:stil|script" '
                      'umbenennen und die Kommentarzeilen /* Layout "Lernschritte": … */ im eigenen Stil und Script '
                      'ändern (sonst hält sync-vorlage.py Seiten daraus für Lernschritte-Seiten)' % k)
    try:
        fach = sync.bloecke_aus(sync.lesen(sync.FACH)[0], 'Fachunterricht.html', sync.F_BLOECKE)
        if sync.kern_einsetzen(s, fach, k) != s:
            fehler.append('Blöcke aus Fachunterricht.html sind nicht aktuell: sync-vorlage.py --vorlagen ausführen')
        rest = s
        for datei, namen in (('Fachunterricht.html', sync.F_BLOECKE), (k, sync.A_BLOECKE)):
            for n in namen:
                b = sync.bereich_markiert(rest, datei, n)
                if b is not None:
                    rest = rest[:b[0]] + rest[b[1]:]
        rest = sync.ohne_kommentare(rest)
        if re.search(r'<(?:script|style)\b', rest, re.I):
            fehler.append('<style> oder <script> außerhalb der markierten Blöcke. Eigener Stil gehört zwischen '
                          '%s und %s, eigenes Script zwischen %s und %s' % (sync.markierung(k, 'stil') + sync.markierung(k, 'script')))
        if not sync.eigene_bloecke(s, k):
            hinweise.append('Keine eigenen Blöcke: Die Vorlage unterscheidet sich nur im Seitenaufbau von Fachunterricht.html.')
    except sync.Fehler as e:
        fehler.append(str(e))
    if 'id="nameOut"' not in s:
        fehler.append('Name-Zelle fehlt (<b id="nameOut">–</b>): Der Schülername kommt aus der ByCS')
    return fehler, hinweise


def main(argv=None):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # profil.py liegt daneben, egal wer main() aufruft
    import profil
    profil.utf8_ausgabe()
    pfade = [os.path.abspath(p) for p in (sys.argv[1:] if argv is None else argv)] or [p for _, p, _, _, _ in sync.team_vorlagen()]
    if not pfade:
        print('Keine Vorlagen der Teams in Vorlagen/<team>/.')
        return 0
    gesamt = 0
    for p in pfade:
        fehler, hinweise = pruefe(p)
        print('%s: %s' % (os.path.relpath(p, sync.ROOT).replace(os.sep, '/'), 'BESTANDEN' if not fehler else 'FEHLER (%d)' % len(fehler)))
        for f in fehler:
            print('  FEHLER  ' + f)
        for h in hinweise:
            print('  Hinweis ' + h)
        gesamt += len(fehler)
    return 1 if gesamt else 0


if __name__ == '__main__':
    sys.exit(main())
