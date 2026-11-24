"""
pw-hash.py - erzeugt den Hash für das Lehrkraft-Passwort (Lösungssperre in .agents/gemeinsam/templates/Fachunterricht.html).
Aufruf (im Projektordner, am Mac python3 statt python):  python .agents/gemeinsam/scripts/pw-hash.py
Das Passwort wird verdeckt abgefragt (Fenster, sonst Terminal) und NICHT gespeichert. Nie als Argument (stünde in der
Befehlsgeschichte). Gespeichert wird nur der Hash in .agents/gemeinsam/data/solution-password.txt (wird mit committet).
Das Fenster erscheint auch, wenn die KI das Skript startet (Skill schule-einrichten): Das Passwort kommt nie in den Chat.
Groß-/Kleinschreibung ist egal, nur ASCII-Zeichen (keine Umlaute).
Nur Python-Standardbibliothek (Windows und Mac).
"""
import getpass
import hashlib
import os
import re
import sys

SALT = 'bs-lernpaket|'


def make_hash(password):
    p = password.strip().upper()
    if len(p) < 4:
        raise ValueError('Passwort zu kurz (mindestens 4 Zeichen).')
    if re.search(r'[^\x20-\x7E]', p):
        raise ValueError('Bitte nur ASCII-Zeichen verwenden (keine Umlaute).')
    return hashlib.sha256((SALT + p).encode('ascii')).hexdigest()


def fragen(text):
    """Verdeckt fragen: Fenster (tkinter), sonst Terminal. None: Fragen geht hier nicht oder abgebrochen."""
    try:
        import tkinter
        from tkinter import simpledialog
        w = tkinter.Tk()
        w.withdraw()
        w.attributes('-topmost', True)
        try:
            return simpledialog.askstring('Lehrkraft-Passwort', text, show='*', parent=w)
        finally:
            w.destroy()
    except Exception:   # kein tkinter oder kein Bildschirm
        pass
    if sys.stdin and sys.stdin.isatty():
        try:
            return getpass.getpass(text + ' ')
        except (EOFError, KeyboardInterrupt):
            return None
    return None


def main():
    if len(sys.argv) > 1:
        print('FEHLER: Das Passwort nie als Argument angeben, es stünde sonst in der Befehlsgeschichte. Ohne Argument '
              'aufrufen, es wird verdeckt abgefragt.')
        return 1
    password = fragen('Lehrkraft-Passwort für die Lösungen (mindestens 4 Zeichen, keine Umlaute):')
    if password is None:
        print('FEHLER: Kein Passwort eingegeben (abgebrochen, oder hier geht weder ein Fenster noch eine Eingabe im Terminal).')
        return 1
    if fragen('Zur Kontrolle das Passwort noch einmal:') != password:
        print('FEHLER: Die beiden Eingaben sind verschieden. Nichts gespeichert, bitte noch einmal.')
        return 1
    try:
        h = make_hash(password)
    except ValueError as e:
        print('FEHLER: %s' % e)
        return 1
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')   # Ordner .agents/gemeinsam/data
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, 'solution-password.txt')
    with open(path, 'w', encoding='ascii') as f:
        f.write('salt=%s\nhash=%s\n' % (SALT, h))
    print('Gespeichert in ' + path)
    print('hash=' + h)
    return 0


if __name__ == '__main__':
    sys.exit(main())
