# Vorlagen der Teams

Hier legt jedes Team eigene Vorlagen für E-Learnings ab: `Vorlagen/<Teamname>/<Name>.html` (Teamname wie auf GitHub,
z. B. `Vorlagen/metall/Werkstatt.html`). Ändern dürfen den Ordner nur das Team und die Werkzeug-Verantwortlichen. Diese
Datei und alles direkt in `Vorlagen/` ist Werkzeug. Regeln: `.agents/gemeinsam/regeln/seite.md` und `schutz.md`.
Arbeitet eine Lehrkraft allein (`Schutz | aus` im Schulprofil), gibt es keine Teams: eigene Vorlagen liegen dann in
`Vorlagen/Eigene/<Name>.html`, sonst gilt alles hier genauso.

## Layout-Vorlage (Normalfall): eigenes Aussehen, gemeinsamer Kern
Bewertung, Abgabe, Punkte für die ByCS, PDF-Export, Leerdruck, Hell/Dunkel und Lösungssperre kommen aus
`Fachunterricht.html` und bleiben überall gleich. Das Team gestaltet Kopf, Seitenaufbau und Aussehen.

1. `.agents/gemeinsam/templates/Fachunterricht.html` (oder `Allgemeinbildung.html`) nach
   `Vorlagen/<Teamname>/<Name>.html` kopieren.
2. Den TEMPLATE-Kommentar am Anfang behalten und anpassen: Er beschreibt die Bausteine der Vorlage.
3. Die vier markierten Bereiche `<!-- Fachunterricht.html:head|tools|modals|scripts -->` nie ändern.
4. Eigener Stil kommt in **einen** Block direkt nach `<!-- /Fachunterricht.html:head -->`, eigenes Script in
   **einen** Block direkt nach `<!-- /Fachunterricht.html:scripts -->`:
   ```
   <!-- <Teamname>/<Name>.html:stil -->
   <style> … </style>
   <!-- /<Teamname>/<Name>.html:stil -->
   ```
   (für das Script genauso mit `:script` und `<script>`). Außerhalb dieser Blöcke steht kein `<style>` und kein
   `<script>`. Der eigene Stil überschreibt nur das Aussehen, das eigene Script macht nur Navigation und Anzeige.
5. Kopie von `Allgemeinbildung.html`: die Markierungen `Allgemeinbildung.html:stil|script` umbenennen und die
   Kommentarzeilen `/* Layout "Lernschritte": … */` ändern.
6. Keine externen Ressourcen, die Name-Zelle (`id="nameOut"`) bleibt, `<meta name="loesung-hash" content="">` bleibt leer.
7. Prüfen: `python .agents/gemeinsam/scripts/vorlage-pruefen.py Vorlagen/<Teamname>/<Name>.html`.

Stil und Script der Vorlage liegen zusätzlich als Dateien in `Vorlagen/<Teamname>/kern/` (`sync-vorlage.py --vorlagen`
erzeugt sie, nie von Hand ändern); Seiten laden sie nach `bauen.py --auslagern <Seite> --schreiben` über relative Adressen.

Ändert sich später der eigene Stil oder das eigene Script: `python .agents/gemeinsam/scripts/sync-vorlage.py`
(Probelauf), dann `--schreiben`. Alle Seiten aus dieser Vorlage bekommen die neue Fassung, danach die Lernpakete neu
bauen. Ändert sich `Fachunterricht.html`, bringen die Werkzeug-Verantwortlichen mit `sync-vorlage.py --vorlagen` auch
die Vorlagen der Teams auf den neuen Stand.

## Freie Vorlage (Ausnahme): alles selbst gebaut
Ohne den gemeinsamen Kern. Seiten daraus haben **keine Bewertung** (das Lernpaket meldet nur „bearbeitet“), keinen
Leerdruck und keinen PDF-Export aus der Vorlage, und sie werden nur auf die Grundregeln geprüft.

1. Im Kopf stehen `<meta name="vorlage-art" content="frei">`,
   `<meta name="vorlage" content="<Teamname>/<Name>.html">` und `<meta name="loesung-hash" content="">`.
   Beide `vorlage`-Zeilen bleiben in jeder Seite aus der Vorlage stehen.
2. Die Grundregeln gelten weiter: eine Datei, offline (keine externen Ressourcen), Lösungen nur hinter dem
   Passwort-Hash, kein Feld für den Schülernamen.
3. Eine Freigabe braucht es nicht. Prüfen: `python .agents/gemeinsam/scripts/vorlage-pruefen.py Vorlagen/<Teamname>/<Name>.html`.
