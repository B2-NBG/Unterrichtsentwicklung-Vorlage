
(function () {
  var $ = function (s) { return document.querySelector(s); };
  var root = document.documentElement;
  var tasks = [].slice.call(document.querySelectorAll('.task'));
  var lms = window.ScormReport || null;   /* kommt aus scorm-api.js, nur im SCORM-Paket vorhanden */
  var completeSent = false;

  /* ---------- Name und Punkte aus/an die Lernplattform ---------- */
  /* Abgeschlossen = alle Aufgaben des Einsteiger- und Prüfungsniveaus bearbeitet. Punkte = Bewertung (siehe grade), gewichtet
     Einsteigerniveau 40 %, Prüfungsniveau 40 %, Profiniveau 20 %, bestanden ab 70 %. Aufgaben ohne hinterlegte Lösung zählen bearbeitet = volle Punkte. */
  function levelOf(t) { var l = t.closest('.level'); return l && l.classList.contains('foundation') ? 'foundation' : (l && l.classList.contains('challenge') ? 'challenge' : 'core'); }
  /* Gewicht der Aufgabe im Niveau (data-gewicht, z. B. die Punkte aus dem Original), sonst 1 */
  function weightOf(t) { var v = parseFloat(String(t.getAttribute('data-gewicht') || '').replace(',', '.')); return v > 0 ? v : 1; }
  /* Kennung in den Moodle-Berichten: Titel bis zum Gedankenstrich ("Aufgabe 1.1 - Titel" -> Aufgabe-1.1), ohne Leer- und Sonderzeichen;
     scorm-api.js hängt Niveau und Höchstpunkte an */
  function taskLabel(t, i) {
    var s = ((t.querySelector('.tt') || {}).textContent || '').replace(/\s+/g, ' ').trim().split(/ [-–—] |: /)[0];
    s = s.replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/Ä/g, 'Ae').replace(/Ö/g, 'Oe').replace(/Ü/g, 'Ue').replace(/ß/g, 'ss')
         .replace(/[^A-Za-z0-9.,_-]+/g, '-').replace(/-{2,}/g, '-').replace(/^[-.,]+|[-.,]+$/g, '').slice(0, 40);
    return s || 'Aufgabe-' + (i + 1);
  }
  function pText(x) { return String(Math.round(x * 10) / 10).replace('.', ','); }   /* Punkte: immer ganze Zahlen */
  var LW = { foundation: 40, core: 40, challenge: 20 }, lvCount = { foundation: 0, core: 0, challenge: 0 }, lvWeight = { foundation: 0, core: 0, challenge: 0 };
  var taskInfo = {}, labels = {}, scored = 0, sent = {};
  var submitted = false, subDate = '', frozen = false;   /* Abgabe: danach gesperrt, Bewertung und Lösungsvorschläge sichtbar */
  tasks.forEach(function (t, i) {
    if (isDone(t) === null) return;
    var l = levelOf(t), lb = taskLabel(t, i), n = 1;
    while (labels[lb + (n > 1 ? '-' + n : '')]) n++;   /* gleicher Titel: Aufgabe-2.1, Aufgabe-2.1-2 */
    lb += n > 1 ? '-' + n : ''; labels[lb] = 1;
    lvCount[l]++; lvWeight[l] += weightOf(t); scored++;
    taskInfo['a' + (i + 1)] = { level: l, weight: weightOf(t), label: lb };
  });
  /* Höchstpunkte je Aufgabe wie in scorm-api.js, nur ganze Punkte (Summe 100): 100 auf die vorhandenen Niveaus (40:40:20), den Anteil des
     Niveaus nach Gewicht auf seine Aufgaben. Anteile abrunden, die Restpunkte einzeln an die größten Reste, bei Gleichstand an die letzten
     (drei gleiche Aufgaben mit zusammen 40 = 13, 13, 14; nur Einsteiger- und Profiniveau = 67 und 33) */
  function share(sum, w) {
    var W = 0, p = [], r = [], idx = [], rest = sum, i, q, f;
    for (i = 0; i < w.length; i++) W += w[i];
    for (i = 0; i < w.length; i++) { q = W > 0 ? sum * w[i] / W : 0; f = Math.floor(q + 1e-9); p[i] = f; r[i] = Math.round((q - f) * 1e6); rest -= f; idx[i] = i; }
    idx.sort(function (a, b) { return r[b] - r[a] || b - a; });
    for (i = 0; i < rest && i < idx.length; i++) p[idx[i]]++;
    return p;
  }
  var maxP = {};
  (function () {
    var ls = [], lk, lp;
    for (lk in LW) { if (lvCount[lk]) ls.push(lk); }
    lp = share(100, ls.map(function (l) { return LW[l]; }));
    ls.forEach(function (l, j) {
      var idx = [], p;
      tasks.forEach(function (t, i) { var m = taskInfo['a' + (i + 1)]; if (m && m.level === l) idx.push(i); });
      p = share(lp[j], idx.map(function (i) { return taskInfo['a' + (i + 1)].weight; }));
      idx.forEach(function (i, n) { maxP[i] = p[n]; });
    });
  })();
  if (lms) { try { lms.init(scored ? { levels: lvCount, tasks: taskInfo, quality: true, submit: true } : { scoring: false }); } catch (e) { /* ohne Lernplattform weiter */ } }

  /* ---------- Bewertung: hinterlegte Lösungen (data-ok, data-keys) ---------- */
  function fieldsOf(t) { return [].filter.call(t.querySelectorAll('input:not([type=button]):not([type=submit]):not([type=hidden]), textarea, select'), function (f) { return !f.closest('details.sol, .sol-only'); }); }
  function norm(s) { return String(s).toLowerCase().replace(/\s+/g, ' ').trim(); }
  function numOf(s) { var m = String(s).replace(/\s+/g, '').replace(',', '.').match(/^[-+]?\d*\.?\d+(e[-+]?\d+)?/i); return m ? parseFloat(m[0]) : NaN; }
  /* Vergleichsschlüssel für Textantworten: "594 × 841 mm" = "594x841" = "594 * 841"; Leerzeichen, Komma/Punkt, nachgestelltes mm egal */
  function key(s) { return norm(s).replace(/[×*]/g, 'x').replace(/\s+/g, '').replace(/,/g, '.').replace(/mm$/, ''); }
  function hits(v, ok, tol) {   /* Alternativen mit | getrennt; Zahlen mit Toleranz data-tol, Text ohne Groß-/Kleinschreibung */
    return String(ok).split('|').some(function (a) {
      if (/^[-+]?\d*[.,]?\d+$/.test(a.replace(/\s+/g, ''))) {   /* Zahl: Eingabe darf eine Einheit dahinter haben ("12,5 mm") */
        var n = numOf(a), x = numOf(v);
        return !isNaN(x) && Math.abs(x - n) <= (tol ? Math.abs(numOf(tol)) : 1e-9 * Math.max(1, Math.abs(n)));
      }
      return key(a) !== '' && key(v) === key(a);
    });
  }
  function labelOf(f) { var l = f.closest('label'); return String(l ? l.textContent : f.value).replace(/\s+/g, ' ').trim(); }
  /* Ergebnis einer interaktiven Aufgabe im Ergebnisfeld (data-score): "6 von 8" -> 0,75. data-score="richtig" verlangt "x von y richtig".
     null = noch kein passendes Ergebnis (z. B. "noch nicht geprüft") */
  function scoreOf(f) {
    var w = (f.getAttribute('data-score') || '').trim().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    var m = String(f.value).match(new RegExp('(\\d+)\\s*von\\s*(\\d+)' + (w ? '\\s*' + w : ''), 'i'));
    return m && +m[2] > 0 ? Math.min(1, +m[1] / +m[2]) : null;
  }
  /* Anteil richtig 0..1; null = keine hinterlegte Lösung (dann zählt nur bearbeitet / offen) */
  function grade(t) {
    var ff = fieldsOf(t), items = [], seen = {}, box = { need: 0, right: 0, wrong: 0 };
    ff.forEach(function (f) {
      if (f.type === 'radio') {
        if (seen[f.name]) return; seen[f.name] = 1;
        var grp = ff.filter(function (g) { return g.type === 'radio' && g.name === f.name; });
        if (!grp.some(function (g) { return g.hasAttribute('data-ok'); })) return;
        items.push(grp.some(function (g) { return g.checked && g.hasAttribute('data-ok'); }) ? 1 : 0);
      } else if (f.type === 'checkbox') {
        if (f.hasAttribute('data-ok')) { box.need++; if (f.checked) box.right++; } else if (f.checked) box.wrong++;
      } else if (f.tagName === 'SELECT') {
        if (!f.querySelector('option[data-ok]')) return;
        var o = f.options[f.selectedIndex]; items.push(o && o.hasAttribute('data-ok') ? 1 : 0);
      } else if (f.tagName === 'TEXTAREA') {
        var keys = (f.getAttribute('data-keys') || '').split(';').filter(function (k) { return k.trim(); }), v = norm(f.value), n = 0;
        if (!keys.length) return;
        keys.forEach(function (k) { if (k.split('|').some(function (a) { return norm(a) && v.indexOf(norm(a)) > -1; })) n++; });
        items.push(n / keys.length);
      } else if (f.hasAttribute('data-score')) {
        var sc = scoreOf(f); items.push(sc === null ? 0 : sc);
      } else if (f.hasAttribute('data-ok')) {
        items.push(hits(f.value, f.getAttribute('data-ok'), f.getAttribute('data-tol')) ? 1 : 0);
      }
    });
    if (box.need) items.push(Math.max(0, (box.right - box.wrong) / box.need));   /* Mehrfachauswahl: falsche Kreuze ziehen ab */
    return items.length ? items.reduce(function (a, b) { return a + b; }, 0) / items.length : null;
  }
  function answerText(t) {
    var out = [];
    fieldsOf(t).forEach(function (f) {
      if (f.type === 'radio' || f.type === 'checkbox') { if (f.checked) out.push(labelOf(f)); }
      else if (f.tagName === 'SELECT') { if (f.value !== '') out.push(f.options[f.selectedIndex].text.trim()); }
      else if (f.value.trim()) out.push(f.value.trim());
    });
    return out.join(' | ').replace(/\s*\n\s*/g, ' / ');
  }
  function expectedText(t) {
    var out = [];
    fieldsOf(t).forEach(function (f) {
      if ((f.type === 'radio' || f.type === 'checkbox') && f.hasAttribute('data-ok')) out.push(labelOf(f));
      else if (f.tagName === 'SELECT') { var o = f.querySelector('option[data-ok]'); if (o) out.push(o.text.trim()); }
      else if (f.tagName === 'TEXTAREA') { if (f.getAttribute('data-keys')) out.push('Begriffe: ' + f.getAttribute('data-keys')); }
      else if (f.hasAttribute('data-score')) out.push('Ergebnis der interaktiven Aufgabe "x von y' + (f.getAttribute('data-score') ? ' ' + f.getAttribute('data-score') : '') + '" = Anteil');
      else if (f.hasAttribute('data-ok')) out.push(f.getAttribute('data-ok') + (f.getAttribute('data-tol') ? ' (±' + f.getAttribute('data-tol') + ')' : ''));
    });
    return out.join(' | ');
  }
  /* Meldung je Aufgabe: nur wenn sich bearbeitet, Bewertung oder Antwort geändert hat. first = beim Öffnen (Abgleich mit Lernplattform) */
  /* Gesamtergebnis 0-100 wie in scorm-api.js: Summe der erreichten ganzen Punkte je Aufgabe, Aufgaben ohne hinterlegte Lösung = bearbeitet */
  function taskShare(t) { var d = isDone(t), g = d ? grade(t) : 0; return g === null ? 1 : Math.round(g * 100) / 100; }   /* 0..1 */
  /* erreichte Punkte einer Aufgabe: Bewertung 0..1 x Höchstpunkte, auf ganze Punkte gerundet (halbe auf) */
  function earnedP(t, i) { return Math.round(Math.round((maxP[i] || 0) * taskShare(t) * 1e6) / 1e6); }
  function pageScore() {
    var pts = 0;
    tasks.forEach(function (t, i) { if (taskInfo['a' + (i + 1)]) pts += earnedP(t, i); });
    return Math.min(100, pts);
  }
  function reportAll(first) {
    if (!scored || !lms || !lms.connected || frozen) return 0;
    var n = 0;
    tasks.forEach(function (t, i) {
      var d = isDone(t); if (d === null) return;
      var id = 'a' + (i + 1), g = grade(t), s = g === null ? null : Math.round(g * 100) / 100, r = d ? answerText(t) : '', k = (d ? 1 : 0) + '|' + s + '|' + r;
      if (first) {
        var st = lms.taskState(id);
        if (st ? (st.d === (d ? 1 : 0) && st.s === (s === null ? (d ? 1 : 0) : s)) : !d) { sent[id] = k; return; }
      }
      if (sent[id] === k) return;
      sent[id] = k; n++;
      try { lms.task(id, { level: levelOf(t), done: d, score: s, response: r, description: ((t.querySelector('.tt') || {}).textContent || id), correctResponse: expectedText(t) }); } catch (e) { /* still */ }
    });
    return n;
  }
  function lmsName() { try { return (lms && lms.connected) ? lms.studentName() : ''; } catch (e) { return ''; } }
  function showName() { var n = lmsName(); $('#nameOut').textContent = n || '–'; }

  /* ---------- Aufgaben: bearbeitet / offen ---------- */
  /* true = etwas eingetragen, false = leer, null = Aufgabe hat keine Eingabefelder */
  function isDone(t) {
    var f = t.querySelectorAll('input:not([type=button]):not([type=submit]):not([type=hidden]), textarea, select'), i, e;
    if (!f.length) return null;
    for (i = 0; i < f.length; i++) {
      e = f[i];
      if (e.type === 'checkbox' || e.type === 'radio') { if (e.checked) return true; }
      else if (e.tagName === 'SELECT') { if (e.value !== '') return true; }
      else if (e.value.replace(/\s+/g, '') !== '') return true;
    }
    return false;
  }
  function update() {
    var total = 0, done = 0, optional = 0;
    tasks.forEach(function (t, i) {
      var d = isDone(t);
      if (d === null) { t.removeAttribute('data-done'); t.removeAttribute('data-pts'); t.removeAttribute('data-ptsq'); return; }
      total++; if (d) done++;
      /* Auswertung (sichtbar im Lehrkraft-Modus und nach der Abgabe) */
      var g = d ? grade(t) : null;
      if (!d) { t.removeAttribute('data-q'); t.removeAttribute('data-qc'); }
      else if (g === null) { t.setAttribute('data-q', 'ohne automatische Bewertung: mit der Lösung vergleichen'); t.setAttribute('data-qc', 'none'); }
      else { t.setAttribute('data-q', g >= 1 ? 'richtig' : g <= 0 ? 'falsch' : Math.round(g * 100) + ' % richtig'); t.setAttribute('data-qc', g >= 1 ? 'ok' : g <= 0 ? 'bad' : 'part'); }
      /* Punkte: Höchstpunkte immer, erreichte im Lehrkraft-Modus und nach der Abgabe */
      t.setAttribute('data-pts', pText(maxP[i]) + ' P.');
      t.setAttribute('data-ptsq', pText(earnedP(t, i)) + ' von ' + pText(maxP[i]) + ' P.');
      /* Profiniveau (schwarz) ist freiwillig: Einsteigerniveau + Prüfungsniveau = 80 % der Punkte (Mindestanforderung, Bestehensgrenze 70 %) */
      if (t.closest('.level.challenge')) optional++;
      t.setAttribute('data-done', d ? '1' : '0');
    });
    $('#doneInfo').textContent = total ? done + ' von ' + total + ' Aufgaben bearbeitet' + (optional ? ' (Profiniveau freiwillig)' : '') : '';
    ampel();
    /* Seite ohne Aufgaben (nur Lesestoff): mit dem Öffnen abgeschlossen */
    if (!scored && lms && !completeSent) { completeSent = true; try { lms.complete(); } catch (e) { /* still */ } }
  }

  /* ---------- Ampel: vorläufiger Stand nach den bisher erreichten Punkten (aus 100), ohne Summe ----------
     Rot unter 40 %, gelb bis zur Bestehensgrenze, grün ab der Bestehensgrenze, über 90 % ein Stern. Die Bestehensgrenze kommt aus der
     Lernplattform (lms.passMark(), Manifest 0.7), ohne Verbindung gilt 70. Lernpakete sind Übungspakete,
     die Lernenden dürfen ihren Stand sehen (Entscheidung der Lehrkraft vom 13.11.2026). */
  var AMPEL_GELB = 40, AMPEL_STERN = 90;
  var AMPEL_TEXT = { rot: 'Es ist noch viel zu tun', gelb: 'Es ist nicht mehr weit', gruen: 'Bestehensgrenze erreicht', stern: 'Profilevel erreicht' };
  function passMark() { try { var p = lms && lms.connected && lms.passMark ? +lms.passMark() : 70; return p > 0 ? p : 70; } catch (e) { return 70; } }
  function ampel() {
    var a = $('#ampel');
    if (!scored) { if (a) a.hidden = true; return; }
    if (!a) { a = document.createElement('div'); a.id = 'ampel'; a.setAttribute('role', 'status'); a.setAttribute('aria-live', 'polite'); document.body.appendChild(a); }
    var sc = pageScore(), pm = passMark(), k = (sc > AMPEL_STERN && sc >= pm) ? 'stern' : sc >= pm ? 'gruen' : sc >= AMPEL_GELB ? 'gelb' : 'rot';
    if (a.className !== k) { a.className = k; a.textContent = AMPEL_TEXT[k]; }
    a.hidden = false;
  }

  /* ---------- Abgabe: einmalig, danach gesperrt (die Lehrkraft kann sie mit ihrem Passwort zurücknehmen) ---------- */
  var locked = [];   /* von lockFields gesperrte Felder; schon vorher gesperrte (z. B. readonly data-score) bleiben gesperrt */
  function lockFields() {
    locked = [];
    allFields.forEach(function (f) {
      var p = (f.tagName === 'TEXTAREA' || (f.tagName === 'INPUT' && /^(text|number|search|email|url|tel)$/.test(f.type))) ? 'readOnly' : 'disabled';
      if (!f[p]) { f[p] = true; locked.push([f, p]); }
    });
  }
  function unlockFields() { locked.forEach(function (x) { x[0][x[1]] = false; }); locked = []; }
  function showSubmitted() {
    submitted = true;
    document.body.classList.add('submitted');
    lockFields();
    update();
    $('#subBtn').hidden = true;
    $('#unsubBtn').hidden = false;
    var sc = pageScore();
    $('#resultInfo').textContent = 'Abgegeben' + (subDate ? ' am ' + subDate : '') + ': ' + sc + ' %' + (sc >= passMark() ? ' (bestanden)' : ' (nicht bestanden, Grenze ' + passMark() + ' %)');
    if (!$('#subNote')) {
      var m = document.createElement('div'), mn = $('main');
      m.className = 'merke'; m.id = 'subNote';
      m.innerHTML = '<b>Abgegeben.</b> Deine Antworten sind gesperrt. Bei jeder Aufgabe steht jetzt deine Bewertung, und du kannst den Lösungsvorschlag aufklappen. ' +
                    'Vergleiche vor allem die Aufgaben "ohne automatische Bewertung" mit der Lösung. Mit "Als PDF speichern" bekommst du deine Antworten mit Lösungsvorschlag. ' +
                    'Aus Versehen abgegeben? Deine Lehrkraft kann die Abgabe zurücknehmen.';
      mn.insertBefore(m, mn.firstChild);
    }
  }
  function openSub() {
    var req = [], opt = 0, unchecked = [];
    tasks.forEach(function (t) {
      var tt = ((t.querySelector('.tt') || {}).textContent || 'Aufgabe').trim();
      /* Interaktive Aufgabe bearbeitet, aber Ergebnis noch nicht geprüft (kein "x von y") */
      if (fieldsOf(t).some(function (f) { return f.hasAttribute('data-score') && f.value.trim() && scoreOf(f) === null; })) unchecked.push(tt);
      if (isDone(t) !== false) return;
      if (levelOf(t) === 'challenge') opt++; else req.push(tt);
    });
    $('#subOpen').textContent = (req.length ? 'Noch nicht bearbeitet (zählt 0 Punkte): ' + req.join(', ') + '. ' : '') +
                                (unchecked.length ? 'Noch nicht auf "Prüfen" geklickt (zählt 0 Punkte): ' + unchecked.join(', ') : '');
    $('#subOpt').textContent = opt ? 'Profiniveau noch offen (freiwillig): ' + opt + (opt === 1 ? ' Aufgabe' : ' Aufgaben') : '';
    $('#subModal').hidden = false; document.body.classList.add('modalOpen');
    setTimeout(function () { $('#subCancel').focus(); }, 30);
  }
  function closeSub() { $('#subModal').hidden = true; document.body.classList.remove('modalOpen'); }
  function doSubmit() {
    closeSub();
    if (submitted) return;
    var d = new Date();
    subDate = ('0' + d.getDate()).slice(-2) + '.' + ('0' + (d.getMonth() + 1)).slice(-2) + '.' + d.getFullYear();
    showSubmitted();
    if (lms && lms.connected) {
      clearTimeout(saveTimer);
      save();                                     /* letzter Stand + Abgabe-Vermerk */
      try { lms.submit(); } catch (e) { /* still */ }
    }
    frozen = true;
  }
  /* Lehrkraft (nach Passwort): Abgabe zurücknehmen, die Lernenden arbeiten weiter und geben später neu ab */
  function undoSubmit() {
    if (!submitted) return;
    submitted = false; subDate = ''; frozen = false;
    unlockFields();
    document.body.classList.remove('submitted');
    setSol(false);
    [].forEach.call(document.querySelectorAll('details.sol[open]'), function (d) { d.open = false; });   /* Lösungsvorschläge wieder gesperrt */
    var n = $('#subNote'); if (n) n.parentNode.removeChild(n);
    $('#resultInfo').textContent = '';
    $('#unsubBtn').hidden = true;
    $('#subBtn').hidden = !scored;
    update();
    if (lms && lms.connected) {
      try { lms.unsubmit(); } catch (e) { /* still */ }
      clearTimeout(saveTimer);
      save();                                     /* Stand ohne Abgabe-Vermerk */
    }
    $('#saveInfo').textContent = 'Abgabe zurückgenommen: Du kannst weiterarbeiten.'; $('#saveInfo').className = 'info';
  }

  /* ---------- Drucken ---------- */
  function cssStr(s) { return '"' + String(s).replace(/[\\"]/g, '\\$&').replace(/[\r\n]+/g, ' ') + '"'; }
  function nameText() { var n = $('#nameOut').textContent.trim(); return n === '–' ? '' : n; }
  function beforePrint() {
    var blank = document.body.classList.contains('blankPrint');
    if (!blank) {
      update();
      [].forEach.call(document.querySelectorAll('textarea'), function (a) { a.style.height = 'auto'; a.style.height = a.scrollHeight + 'px'; });
    }
    markBreaks();
    var h1 = $('.tb h1'), st = $('#print-head');
    if (!st) { st = document.createElement('style'); st.id = 'print-head'; document.head.appendChild(st); }
    var nils = /Zeichenschrift/.test(($('#zeichen-schriften') || {}).textContent || ''), pf = '; font:9pt ' + (nils ? '"Zeichenschrift", ' : '') + 'Arial, sans-serif; color:#555; }';
    st.textContent = '@page { @top-left { content:' + cssStr(h1 ? h1.textContent : document.title) + pf +
                     ' @top-right { content:' + cssStr('Name: ' + ((!blank && nameText()) || '______________________')) + pf + ' }';
  }

  /* Seitenumbrüche: Aufgaben bis etwa ein Viertel einer A4-Seite werden nicht getrennt (.keep), längere dürfen umbrechen.
     Gemessen mit Testseiten: so bleibt jede Seite außer der letzten mindestens etwa 3/4 gefüllt. */
  function markBreaks() {
    tasks.forEach(function (t) { t.classList.toggle('keep', t.getBoundingClientRect().height <= 250); });
  }

  /* ---------- Leeres Arbeitsblatt für die analoge Bearbeitung (nur Lehrkraft-Modus) ----------
     Druckt alle Aufgaben ohne Einträge und ohne Lösungen (Druckdialog, "Als PDF speichern" möglich). Die Einträge auf der Seite bleiben erhalten. */
  var blankKeep = null, CIRC = '①②③④⑤⑥⑦⑧⑨⑩';
  function blankEl(tag, cls, txt) {
    var e = document.createElement(tag); e.className = cls; e.setAttribute('data-blank', '');
    if (txt != null) e.textContent = txt;
    return e;
  }
  /* Auswahlfelder wie in den Druckfassungen der Skripte fürs Zeichnen: kurz = Linie + "(a / b)"; gleiche Auswahl in >= 3 Feldern oder in einer Tabelle =
     ein Kasten "Auswahl:"; sonst Nummer an der Lücke und ein Kasten "Auswahl für die nummerierten Lücken" (alphabetisch) */
  function blankSelects(t) {
    var sel = [].filter.call(t.querySelectorAll('select'), function (s) { return !s.closest('details.sol, .sol-only, .print-alt, .screen-only'); });
    if (!sel.length) return;
    var opts = sel.map(function (s) { return [].filter.call(s.options, function (x) { return x.value !== ''; }).map(function (x) { return x.text.trim(); }); });
    var key = function (o) { return o.slice().sort().join('\u0001'); }, k0 = key(opts[0]);
    var same = opts.every(function (o) { return key(o) === k0; }), inTab = sel.every(function (s) { return s.closest('td, th'); });
    var shared = same && (sel.length >= 3 || (inTab && sel.length >= 2));
    var groups = [], gk = {}, sortDe = function (a, b) { return a.localeCompare(b, 'de', { numeric: true }); };
    sel.forEach(function (s, i) {
      var o = opts[i], abs = s.style.position === 'absolute', b = blankEl('span', abs ? 'pbox' : 'pblank');
      if (abs) b.style.cssText = s.style.cssText;
      else b.style.minWidth = Math.min(60, Math.max(16, Math.max.apply(null, o.map(function (x) { return x.length; }).concat([0])) * 1.9)) + 'mm';   /* Breite nach der längsten Option (wie in den Druckfassungen) */
      if (!shared) {
        if (!abs && !s.closest('td, th') && o.join(' / ').length <= 30) {
          s.insertAdjacentElement('afterend', b); b.insertAdjacentElement('afterend', blankEl('span', 'popt', '(' + o.join(' / ') + ')'));
          return;
        }
        var k = key(o);
        if (!(k in gk)) { gk[k] = groups.length; groups.push(o); }
        b.appendChild(blankEl('span', 'pnr', gk[k] < 10 ? CIRC[gk[k]] : '(' + (gk[k] + 1) + ')'));
      }
      s.insertAdjacentElement('afterend', b);
    });
    var tt = t.querySelector('.tt'), sol = t.querySelector(':scope > details.sol');
    if (shared) {
      var p = blankEl('p', 'pwords'), bb = document.createElement('b'); bb.textContent = 'Auswahl:';
      p.appendChild(bb); p.appendChild(document.createTextNode(opts[0].slice().sort(sortDe).join(' · ')));
      if (tt) tt.insertAdjacentElement('afterend', p); else t.insertBefore(p, t.firstChild);
    } else if (groups.length) {
      var box = blankEl('div', 'pwords'), bt = document.createElement('b'); bt.textContent = 'Auswahl für die nummerierten Lücken:';
      box.appendChild(bt);
      groups.forEach(function (o, i) {
        var line = document.createElement('span'); line.textContent = (i < 10 ? CIRC[i] : '(' + (i + 1) + ')') + '  ' + o.slice().sort(sortDe).join(' · ');
        box.appendChild(line);
      });
      if (sol) t.insertBefore(box, sol); else t.appendChild(box);
    }
  }
  function printBlank() {
    if (blankKeep) return;
    blankKeep = { s: snapshot(), name: $('#nameOut').textContent };
    restore({ f: 2, k: {} });   /* nur für den Druck leeren, ohne Speichern */
    tasks.forEach(function (t) { t.removeAttribute('data-done'); t.removeAttribute('data-q'); t.removeAttribute('data-qc'); t.removeAttribute('data-ptsq'); });
    try { document.dispatchEvent(new CustomEvent('leerdruck', { detail: { an: true } })); } catch (e) { /* Modul-Fehler stoppen den Druck nicht */ }
    tasks.forEach(blankSelects);
    [].forEach.call(document.querySelectorAll('main .task textarea'), function (a) {
      var n = +a.getAttribute('data-zeilen') || Math.max(3, +a.getAttribute('rows') || 5);   /* Schreiblinien: data-zeilen, sonst rows (mind. 3), ohne Angabe 5 */
      a.setAttribute('data-h', a.style.height); a.style.height = (n * 32) + 'px';
    });
    var tb = $('.tb'), pm = blankEl('div', 'pmeta');
    ['Name:', 'Klasse:', 'Datum:'].forEach(function (l) { var sp = document.createElement('span'); sp.textContent = l; sp.appendChild(document.createElement('i')); pm.appendChild(sp); });
    if (tb) tb.insertAdjacentElement('afterend', pm);
    $('#nameOut').textContent = '';
    document.body.classList.add('blankPrint');
    try { window.print(); } finally { endBlank(); }
  }
  function endBlank() {
    if (!blankKeep) return;
    document.body.classList.remove('blankPrint');
    [].forEach.call(document.querySelectorAll('[data-blank], .blank-opts'), function (n) { n.remove(); });
    [].forEach.call(document.querySelectorAll('main .task textarea[data-h]'), function (a) { a.style.height = a.getAttribute('data-h'); a.removeAttribute('data-h'); });
    try { document.dispatchEvent(new CustomEvent('leerdruck', { detail: { an: false } })); } catch (e) { /* still */ }
    restore(blankKeep.s);
    $('#nameOut').textContent = blankKeep.name;
    blankKeep = null;
    update();
  }

  /* ---------- PDF-Export (nur Text; Bewertung und Lösungsvorschlag erst nach der Abgabe) ---------- */
  function slug(s) {   /* Dateiname: Schreibweise bleibt, erstes Zeichen groß, höchstens 80 Zeichen an einer Wortgrenze (AGENTS.md) */
    s = String(s).replace(/ä/g, 'ae').replace(/ö/g, 'oe').replace(/ü/g, 'ue').replace(/Ä/g, 'Ae').replace(/Ö/g, 'Oe').replace(/Ü/g, 'Ue').replace(/ß/g, 'ss').replace(/[^A-Za-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    if (s.length > 80) s = s.slice(0, 81).replace(/-[^-]*$/, '').slice(0, 80);
    return s.charAt(0).toUpperCase() + s.slice(1);
  }
  function pdfTitle(h1) {   /* Seitentitel ohne angehängte Schriftfeld-Überschrift: "Kapitel 1 – Thema – Überschrift" -> "Kapitel 1 – Thema" */
    var t = document.title.replace(/\s+/g, ' ').trim(), end = ' – ' + String(h1).replace(/\s+/g, ' ').trim();
    return t.length > end.length && t.slice(-end.length) === end ? t.slice(0, -end.length) : t;
  }
  function taskText(t) {
    var c = t.cloneNode(true), tt = c.querySelector('.tt'), o, k, i;
    if (tt) tt.remove();
    [].forEach.call(c.querySelectorAll('.lines, button, details.sol, .sol-only, .no-pdf, .paper, .print-alt, svg, script, style'), function (n) { n.remove(); });   /* svg: Beschriftung von Zeichnungen nicht als lose Zahlen */
    o = [].filter.call(t.querySelectorAll('input, textarea, select'), function (f) { return !f.closest('.lines, details.sol, .sol-only, .no-pdf, .print-alt'); });
    k = c.querySelectorAll('input, textarea, select');
    for (i = 0; i < k.length; i++) {
      var a = o[i], b = k[i], txt = '', v;
      if (a.tagName === 'TEXTAREA') { v = a.value.trim(); txt = '\n' + (v || '(leer)') + '\n'; }
      else if (a.tagName === 'SELECT') { txt = '[' + (a.value !== '' ? a.options[a.selectedIndex].text : '___') + ']'; }
      else if (a.type === 'checkbox' || a.type === 'radio') { txt = a.checked ? '(x) ' : '( ) '; var lb = b.closest('label'); if (lb) lb.insertAdjacentText('afterend', '\n'); }
      else if (a.type === 'hidden' || a.type === 'button' || a.type === 'submit') { txt = ''; }
      else { v = a.value.trim(); txt = '[' + (v || '___') + ']'; }
      b.replaceWith(document.createTextNode(txt));
    }
    return plain(c);
  }
  function plain(c) {
    [].forEach.call(c.querySelectorAll('br'), function (n) { n.replaceWith(document.createTextNode('\n')); });
    [].forEach.call(c.querySelectorAll('p, div, li, h2, h3, h4, tr, ol, ul, table'), function (n) { n.insertAdjacentText('afterend', '\n'); });
    return c.textContent.replace(/[ \t\r\f\v\u00a0]+/g, ' ').split('\n').map(function (s) { return s.trim(); }).join('\n').replace(/\n{3,}/g, '\n\n').trim();
  }
  /* Musterl\u00f6sung einer Aufgabe als Text (nur nach der Abgabe im PDF) */
  function solText(t) {
    var s = t.querySelector('details.sol'); if (!s) return '';
    var c = s.cloneNode(true);
    [].forEach.call(c.querySelectorAll('summary, script, style, .no-pdf'), function (n) { n.remove(); });
    return plain(c);
  }
  /* PDF-Export: auf Seiten mit Schriften fürs Zeichnen erst die Schrift laden (wird eingebettet), sonst und bei Fehlern Helvetica */
  var ttLaden = null;
  function ladeSchrift() {
    if (!ttLaden) ttLaden = PDFW.loadTT().catch(function () { PDFW.noTT(); return false; });
    return ttLaden;
  }
  function makePdf() {
    ladeSchrift().then(function (tt) {
      try { makePdfNow(); }
      catch (e) {
        if (!tt) { setTimeout(function () { throw e; }); return; }
        PDFW.noTT(); ttLaden = Promise.resolve(false);   /* Ersatzweg: Helvetica */
        try { makePdfNow(); } catch (e2) { setTimeout(function () { throw e2; }); }
      }
    });
  }
  function makePdfNow() {
    var ML = 18, CW = 174, TOP = 24, BOT = 278, LH = 4.7;
    var GRAY = [.42, .46, .50], INK = [.11, .17, .23], RED = [.78, .20, .18], GREEN = [.12, .48, .29], LINE = [.72, .76, .80], YEL = [1, .96, .80];
    var title = ($('.tb h1') || {}).textContent || document.title, sub = ($('.tb .name p') || {}).textContent || '', name = nameText();
    var doc = new PDFW.Doc({ info: { title: title, author: name, subject: sub } }), y = TOP;
    function fit(s, size, bold, w) { s = String(s); if (PDFW.width(s, size, bold) <= w) return s; while (s.length > 1 && PDFW.width(s + '...', size, bold) > w) s = s.slice(0, -1); return s + '...'; }
    function wrap(s, size, bold, maxW) {
      var out = [];
      String(s).split('\n').forEach(function (par) {
        if (!par.trim()) { out.push(''); return; }
        var line = '';
        par.split(/\s+/).forEach(function (w) {
          var t = line ? line + ' ' + w : w;
          if (PDFW.width(t, size, bold) <= maxW) { line = t; return; }
          if (line) { out.push(line); line = ''; }
          while (PDFW.width(w, size, bold) > maxW) { var k = w.length; while (k > 1 && PDFW.width(w.slice(0, k), size, bold) > maxW) k--; out.push(w.slice(0, k)); w = w.slice(k); }
          line = w;
        });
        out.push(line);
      });
      return out;
    }
    function ensure(h) { if (y + h > BOT) { doc.addPage(); y = TOP; } }
    function cell(x, cy, w, h, label, value, big) {
      doc.rect(x, cy, w, h, { stroke: INK, lw: .35 });
      doc.text(label, x + 2, cy + 3.6, 6.5, false, GRAY);
      if (!value) return;
      /* lange Werte (z. B. ein Lernfeldname) in zwei kleineren Zeilen statt abgeschnitten */
      if (big || PDFW.width(value, 9.5, false) <= w - 4) { doc.text(fit(value, 9.5, !!big, w - 4), x + 2, cy + 8.6, 9.5, !!big, INK); return; }
      wrap(value, 8, false, w - 4).slice(0, 2).forEach(function (l, i) { doc.text(l, x + 2, cy + 6.9 + i * 3.1, 8, false, INK); });
    }
    /* Schriftfeld */
    var cells = [].slice.call(document.querySelectorAll('.tb > div:not(.name)')).map(function (d) {
      var s = d.querySelector('small'); return { l: s ? s.textContent : '', v: d.classList.contains('who') ? name : d.textContent.replace(s ? s.textContent : '', '').trim(), w: d.classList.contains('wide') };
    });
    doc.rect(ML, y, 116, 22, { stroke: INK, lw: .35 });
    doc.text('Benennung', ML + 2, y + 3.6, 6.5, false, GRAY);
    /* Version oben rechts im Benennungsfeld, im PDF mit Datum (V1.3 · 28.10.2026) */
    var vr = $('.tb .ver'), ver = vr ? vr.textContent.trim() : '';
    if (ver && vr.getAttribute('data-datum')) ver += ' · ' + vr.getAttribute('data-datum');
    if (ver) doc.text(ver, ML + 114 - PDFW.width(ver, 6.5, false), y + 3.6, 6.5, false, GRAY);
    doc.text(fit(title, 15, true, 112), ML + 2, y + 12.5, 15, true, INK);
    doc.text(fit(sub, 9, false, 112), ML + 2, y + 18.5, 9, false, GRAY);
    if ($('.tb.kurz')) {
      /* Variante "kurz" (Ethik): neben der Benennung nur der Name, Zusatzzellen (.wide) darunter in voller Breite */
      doc.rect(ML + 116, y, 58, 22, { stroke: INK, lw: .35 });
      doc.text('Name', ML + 118, y + 3.6, 6.5, false, GRAY);
      if (name) doc.text(fit(name, 11, true, 54), ML + 118, y + 12.5, 11, true, INK);
      y += 22;
      cells.forEach(function (c) { if (c.w) { cell(ML, y, 174, 11, c.l, c.v); y += 11; } });
      y += 5;
    } else {
      cells.forEach(function (c, i) {
        var pos = [[ML + 116, y, 58, 11], [ML + 116, y + 11, 58, 11], [ML, y + 22, 58, 11], [ML + 58, y + 22, 58, 11], [ML + 116, y + 22, 58, 11], [ML, y + 33, 174, 11]][i];
        if (pos) cell(pos[0], pos[1], pos[2], pos[3], c.l, c.v, i === 4);
      });
      y += 33 + (cells.length > 5 ? 11 : 0) + 5;
    }
    var d = new Date();
    doc.text('Erstellt am ' + ('0' + d.getDate()).slice(-2) + '.' + ('0' + (d.getMonth() + 1)).slice(-2) + '.' + d.getFullYear(), ML, y, 8, false, GRAY);
    y += 7;
    var SOL = [.12, .37, .60];
    if (submitted) { doc.text($('#resultInfo').textContent, ML, y, 11, true, pageScore() >= passMark() ? GREEN : RED); y += 8; }
    /* nach der Abgabe: Bewertung und Lösungsvorschlag unter jeder Aufgabe */
    function extra(el) {
      if (!submitted) return;
      var q = el.getAttribute('data-q'), qc = el.getAttribute('data-qc'), pq = el.getAttribute('data-ptsq'), st = solText(el);
      if (q || pq) {
        wrap('Bewertung: ' + (q && pq ? q + ' – ' + pq : q || pq), 9.5, true, CW - 4).forEach(function (l) {
          ensure(LH + 1); doc.text(l, ML + 2, y + 3.4, 9.5, true, qc === 'ok' ? GREEN : (qc === 'bad' || !q) ? RED : GRAY); y += LH;
        });
        y += 1;
      }
      if (st) {
        ensure(LH * 2); doc.text('Lösungsvorschlag:', ML + 2, y + 3.4, 9.5, true, SOL); y += LH;
        wrap(st, 9.5, false, CW - 8).forEach(function (l) { ensure(LH); if (l) doc.text(l, ML + 6, y + 3.4, 9.5, false, SOL); y += LH; });
      }
    }
    /* Überschriften und Aufgaben in Dokumentreihenfolge */
    [].forEach.call(document.querySelectorAll('main h2, main h3, main .task'), function (el) {
      if (el.closest('.answers, .print-alt') || (el.tagName !== 'DIV' && el.closest('.task'))) return;
      if (el.tagName !== 'DIV') {
        var hs = el.tagName === 'H2' ? 13 : 11.5, hl = wrap(el.textContent.trim(), hs, true, CW);
        ensure(hl.length * (hs * .5) + 8 + 22); y += 2;   /* + Platz für den Anfang der nächsten Aufgabe: keine Überschrift allein am Seitenende */
        hl.forEach(function (l) { doc.text(l, ML, y + 4, hs, true, INK); y += hs * .5; });
        y += 2;
        var pm = el.closest('.phasehead') && el.closest('.phasehead').querySelector('.phmeta');
        if (pm) {
          var pt = [].map.call(pm.querySelectorAll('.chip'), function (c) { return c.textContent.trim(); }).join('  |  ');
          wrap(pt, 9.5, false, CW).forEach(function (l) { ensure(5); doc.text(l, ML, y + 3, 9.5, false, GRAY); y += 5; });
          y += 1;
        }
        return;
      }
      var tt =el.querySelector('.tt'), done = isDone(el), pt = el.getAttribute('data-pts'), tl = wrap((tt ? tt.textContent.trim() : 'Aufgabe') + (pt ? ' (' + pt + ')' : ''), 11, true, CW - 34);
      ensure(tl.length * 5 + 12 + 3 * LH);   /* Aufgabentitel nur mit mindestens drei Zeilen Inhalt auf derselben Seite */
      doc.rect(ML, y, CW, tl.length * 5 + 2.5, { fill: done === false ? [.98, .90, .90] : [.90, .93, .96] });
      tl.forEach(function (l, i) { doc.text(l, ML + 2, y + 4 + i * 5, 11, true, INK); });
      if (done !== null) doc.text(done ? 'bearbeitet' : 'nicht bearbeitet', ML + CW - 2 - PDFW.width(done ? 'bearbeitet' : 'nicht bearbeitet', 8, true), y + 4, 8, true, done ? GREEN : RED);
      y += tl.length * 5 + 5;
      if (done === false) {
        ensure(8); doc.text('Hier fehlt noch etwas: Diese Aufgabe wurde nicht bearbeitet.', ML + 2, y + 3, 10, true, RED); y += 10;
        if (submitted) { extra(el); y += 4; doc.line(ML, y - 2, ML + CW, y - 2, .2, LINE); }
        return;
      }
      wrap(taskText(el), 10, false, CW - 4).forEach(function (l) { ensure(LH); if (l) doc.text(l, ML + 2, y + 3.4, 10, false, INK); y += LH; });
      extra(el);
      y += 4; doc.line(ML, y - 2, ML + CW, y - 2, .2, LINE);
    });
    /* Kopf- und Fußzeile auf jeder Seite */
    var n = doc.pages.length;
    doc.pages.forEach(function (_, i) {
      doc.cur = doc.pages[i];
      doc.text(fit(title, 8, false, 110), ML, 12, 8, false, GRAY);
      var nm = 'Name: ' + (name || '______________'); doc.text(nm, ML + CW - PDFW.width(nm, 8, false), 12, 8, false, GRAY);
      doc.line(ML, 14, ML + CW, 14, .2, LINE);
      var pg = 'Seite ' + (i + 1) + ' von ' + n; doc.text(pg, ML + CW - PDFW.width(pg, 8, false), 290, 8, false, GRAY);
    });
    var blob = new Blob([doc.build()], { type: 'application/pdf' }), a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = (slug(pdfTitle(title)) || 'Ergebnis') + (name ? '_' + slug(name) : '') + '.pdf';
    document.body.appendChild(a); a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }

  /* ---------- Hell / Dunkel ---------- */
  function isDark() { return root.getAttribute('data-theme') === 'dark'; }  /* Standard: hell */
  try { var sv = localStorage.getItem('page-theme'); if (sv === 'dark' || sv === 'light') root.setAttribute('data-theme', sv); } catch (e) { /* ohne Speicher weiter */ }
  $('#tglTheme').addEventListener('click', function () {
    var next = isDark() ? 'light' : 'dark'; root.setAttribute('data-theme', next);
    try { localStorage.setItem('page-theme', next); } catch (e) { /* still */ }
  });

  /* ---------- Lösungen: Passwort für Lehrkräfte ---------- */
  function meta(n) { var m = document.querySelector('meta[name="' + n + '"]'); return m ? m.getAttribute('content') || '' : ''; }
  var pend = null, body = document.body;
  function openModal() { $('#pwModal').hidden = false; body.classList.add('modalOpen'); }
  function closeModal() { $('#pwModal').hidden = true; body.classList.remove('modalOpen'); }
  function askPw(cb, txt) {   /* txt: Liste mit Titel, Satz und Button-Text; ohne txt: Lösungen freischalten */
    txt = txt || ['Lösungen – nur für Lehrkräfte', 'Die Lösungen sind durch ein Passwort geschützt.', 'Lösungen freischalten'];
    $('#pwT').textContent = txt[0]; $('#pwForm p').textContent = txt[1]; $('#pwForm [type=submit]').textContent = txt[2];
    pend = cb; $('#pwIn').value = ''; $('#pwErr').textContent = ''; openModal(); setTimeout(function () { $('#pwIn').focus(); }, 30);
  }
  function setSol(on) {
    body.classList.toggle('solOpen', on);
    var b = $('#tglSol'); b.setAttribute('aria-pressed', on ? 'true' : 'false');
    b.textContent = on ? 'Lehrkraft-Modus: Lösungen verbergen' : 'Lehrkraft-Modus: Lösungen zeigen';
  }
  $('#tglSol').addEventListener('click', function () { if (body.classList.contains('solOpen')) setSol(false); else askPw(function () { setSol(true); }); });
  $('#pwForm').addEventListener('submit', function (e) {
    e.preventDefault();
    var hash = meta('loesung-hash'), v = $('#pwIn').value.trim().toUpperCase();
    if (!hash) { $('#pwErr').textContent = 'Für diese Seite ist kein Passwort hinterlegt.'; return; }
    if (sha256(meta('loesung-salt') + v) === hash) { var cb = pend; pend = null; closeModal(); if (cb) setTimeout(cb, 0); }
    else { $('#pwErr').textContent = 'Falsches Passwort.'; $('#pwIn').select(); }
  });
  $('#pwCancel').addEventListener('click', function () { pend = null; closeModal(); });
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    if (!$('#pwModal').hidden) { pend = null; closeModal(); }
    if (!$('#subModal').hidden) closeSub();
  });
  $('#subBtn').addEventListener('click', openSub);
  $('#subOk').addEventListener('click', doSubmit);
  $('#subCancel').addEventListener('click', closeSub);
  $('#unsubBtn').addEventListener('click', function () {
    askPw(undoSubmit, ['Abgabe zurücknehmen – nur für Lehrkräfte', 'Mit dem Lehrkraft-Passwort wird die Abgabe zurückgenommen. Danach kann weitergearbeitet und neu abgegeben werden.', 'Abgabe zurücknehmen']);
  });
  /* Lösungsvorschläge (details.sol) lassen sich nur nach Passwort öffnen */
  [].forEach.call(document.querySelectorAll('details.sol > summary'), function (s) {
    s.addEventListener('click', function (e) {
      if (body.classList.contains('solOpen') || body.classList.contains('submitted')) return;   /* nach der Abgabe frei */
      e.preventDefault(); askPw(function () { setSol(true); s.parentNode.open = true; });
    });
  });

  /* ---------- Fortschritt in der Lernplattform speichern (SCORM suspend_data) ----------
     Format { f: 2, k: { Schlüssel: Wert }, sub, sd }: Checkbox/Radio = 1, Auswahl = selectedIndex, sonst Text.
     Schlüssel je Feld: data-k aus der Seite, sonst <Aufgabe>-<Nr.>. Aufgabe = id der Aufgabe, sonst a1, a2 ... (gezählt werden nur
     Aufgaben ohne id), Nr. = laufende Nummer der Felder ohne data-k in dieser Aufgabe; Felder außerhalb von Aufgaben: x-<Nr.>.
     So passt ein gespeicherter Stand auch zu einer geänderten Fassung der Seite (ein Feld mehr oder weniger).
     Altes Format { n, v: [[Position, Wert]] } wird weiter gelesen (nach Position) und beim nächsten Speichern umgeschrieben. */
  var allFields = [].slice.call(document.querySelectorAll('main input:not([type=button]):not([type=submit]):not([type=hidden]), main textarea, main select'));
  var fields = allFields.filter(function (f) { return !f.closest('details.sol, .sol-only'); });   /* ohne Felder in Lösungsvorschläge */
  var fkeys = fieldKeys(), saveTimer = null;
  var hold = false, restoreGap = false, gapMsg = '';   /* hold: gespeicherte Eingaben passen nicht, nichts melden oder speichern, bis die Lernenden selbst etwas eintragen */
  function fieldKeys() {
    var own = {}, used = {}, tno = {}, pos = {}, n = 0;
    fields.forEach(function (f) { var k = f.getAttribute('data-k'); if (k) own[k] = 1; });
    tasks.forEach(function (t, i) { if (!t.id) tno[i] = 'a' + (++n); });
    return fields.map(function (f) {
      var k = f.getAttribute('data-k'), t, tid;
      if (!k || used[k]) {
        t = f.closest('.task'); tid = t ? (t.id || tno[tasks.indexOf(t)]) : 'x';
        do { pos[tid] = (pos[tid] || 0) + 1; k = tid + '-' + pos[tid]; } while (own[k] || used[k]);   /* nie einen Schlüssel doppelt vergeben */
      }
      used[k] = 1;
      return k;
    });
  }
  function filled(s) {   /* true = Stand enthält mindestens eine Eingabe */
    if (!s || typeof s !== 'object') return false;
    if (s.k && typeof s.k === 'object') { for (var k in s.k) { if (s.k.hasOwnProperty(k)) return true; } return false; }
    return Array.isArray(s.v) && s.v.length > 0;
  }
  function snapshot() {
    var k = {};
    fields.forEach(function (f, i) {
      if (f.tagName === 'SELECT') { if (f.selectedIndex > 0) k[fkeys[i]] = f.selectedIndex; }
      else if (f.type === 'checkbox' || f.type === 'radio') { if (f.checked) k[fkeys[i]] = 1; }
      else if (f.value !== '') k[fkeys[i]] = f.value;
    });
    var o = { f: 2, k: k };
    if (submitted) { o.sub = 1; o.sd = subDate; }   /* Abgabe-Vermerk */
    return o;
  }
  function fits(f, v) {   /* passt der gespeicherte Wert zur Art des Feldes? */
    if (f.tagName === 'SELECT') return typeof v === 'number' && v % 1 === 0 && v > 0 && v < f.options.length;
    if (f.type === 'checkbox' || f.type === 'radio') return v === 1;
    return typeof v === 'string';
  }
  /* Felder auf einen gespeicherten Stand setzen: jedes Feld, dessen Schlüssel vorkommt; unbekannte Schlüssel werden übersprungen,
     Felder ohne gespeicherten Wert bleiben leer. true = mindestens ein Wert gesetzt. restoreGap = nicht alles ließ sich zuordnen. */
  function restore(s) {
    var put = [], lost = 0, list = fields, at = {}, k;
    restoreGap = false;
    if (!s || typeof s !== 'object') return false;
    if (s.k && typeof s.k === 'object') {
      fkeys.forEach(function (x, i) { at[x] = fields[i]; });
      for (k in s.k) { if (s.k.hasOwnProperty(k)) { if (at.hasOwnProperty(k) && fits(at[k], s.k[k])) put.push([at[k], s.k[k]]); else lost++; } }
    } else if (Array.isArray(s.v)) {   /* altes Format: nach Position, auch bei abweichender Feldanzahl (lieber teilweise als gar nicht) */
      list = allFields;
      s.v.forEach(function (p) { var f = p && allFields[p[0]]; if (f && fits(f, p[1])) put.push([f, p[1]]); else lost++; });
      if (s.n !== allFields.length) lost++;   /* andere Fassung: Zuordnung nach Position ist unsicher */
    } else return false;
    restoreGap = lost > 0;
    if (!put.length && filled(s)) return false;   /* nichts passt: Felder unverändert lassen */
    list.forEach(function (f) {
      if (f.tagName === 'SELECT') f.selectedIndex = 0;
      else if (f.type === 'checkbox' || f.type === 'radio') f.checked = false;
      else f.value = '';
    });
    put.forEach(function (p) {
      var f = p[0];
      if (f.tagName === 'SELECT') f.selectedIndex = p[1];
      else if (f.type === 'checkbox' || f.type === 'radio') f.checked = true;
      else f.value = p[1];
    });
    return put.length > 0;
  }
  function save() {
    if (!lms || !lms.connected || frozen || hold) return;   /* nach der Abgabe wird nichts mehr gespeichert */
    var s = snapshot(), old = lms.loadState(), info = $('#saveInfo');
    if (!filled(s) && filled(old)) return;   /* nie gespeicherte Eingaben durch einen leeren Stand ersetzen (auch nicht im Bericht) */
    var r = reportAll(false);
    if (!filled(s) && !submitted && old === null) { if (r) lms.flush(); return; }
    var ok = lms.saveState(s);
    if (!ok && r) lms.flush();
    if (saveFail) return;   /* roter Hinweis "Nicht gespeichert" bleibt stehen */
    info.textContent = ok ? (gapMsg || bakMsg || 'Fortschritt gespeichert') : 'Achtung: Zu viele Zeichen zum Zwischenspeichern. Bitte als PDF sichern!';
    info.className = 'info' + (ok && !gapMsg ? '' : ' bad');
  }
  function saveSoon() { clearTimeout(saveTimer); saveTimer = setTimeout(save, 800); }
  /* Lernplattform bestätigt das Speichern nicht (abgemeldet, Verbindung weg): roter Hinweis unten, bis es wieder klappt.
     safe = Eingaben sind in diesem Browser gesichert (scorm-api.js spielt sie beim nächsten Öffnen zurück). */
  var saveFail = false, bakMsg = '';
  function saveStatus(ok, safe) {
    var info = $('#saveInfo'), al = $('#saveAlarm');
    if (ok) {
      if (!saveFail) return;
      saveFail = false; if (al) al.hidden = true;
      info.textContent = gapMsg || 'Fortschritt gespeichert'; info.className = 'info' + (gapMsg ? ' bad' : '');
      return;
    }
    saveFail = true;
    if (!al) {
      al = document.createElement('div'); al.id = 'saveAlarm'; al.setAttribute('role', 'alert');
      al.innerHTML = '<p></p><button type="button" class="btn">Als PDF speichern</button>';
      al.querySelector('button').addEventListener('click', function () { $('#pdfBtn').click(); });
      document.body.appendChild(al);
    }
    al.querySelector('p').innerHTML = '<b>Nicht gespeichert!</b> Die Verbindung zur ByCS ist unterbrochen (abgemeldet?). ' +
      (safe ? 'Deine Eingaben sind in diesem Browser gesichert: Lernpaket schließen, neu anmelden und auf diesem Rechner wieder öffnen.'
            : 'Speichere sofort als PDF und sag deiner Lehrkraft Bescheid.');
    al.hidden = false;
    info.textContent = 'Nicht gespeichert'; info.className = 'info bad';
  }

  showName();
  if (lms && lms.connected) {
    var ps = lms.loadState(), got = false;
    try { got = restore(ps); } catch (e) { /* ohne Wiederherstellung weiter */ }
    if (got && lms.fromBackup && lms.fromBackup()) bakMsg = 'Eingaben aus der Sicherung im Browser wiederhergestellt';
    if (got) $('#saveInfo').textContent = bakMsg || 'Fortschritt wiederhergestellt';
    /* Gespeicherte Eingaben, aber keine passt zu dieser Fassung: den Stand in der Lernplattform (Eingaben und Bericht) nicht
       mit leeren Feldern überschreiben, bis die Lernenden selbst etwas eintragen */
    hold = filled(ps) && !got;
    try {   /* schon abgegeben (frühere Sitzung): gesperrt anzeigen, nichts mehr melden */
      if ((ps && ps.sub) || lms.isSubmitted()) { subDate = (ps && ps.sd) || ''; frozen = true; showSubmitted(); $('#saveInfo').textContent = ''; }
    } catch (e) { /* still */ }
    if (filled(ps) && (hold || restoreGap)) {
      gapMsg = 'Gespeicherter Stand passt nicht ganz zu dieser Version – bitte Lehrkraft informieren.';
      $('#saveInfo').textContent = gapMsg; $('#saveInfo').className = 'info bad';
    }
    try { if (!hold && reportAll(true)) lms.flush(); } catch (e) { /* still */ }
    lms.beforeFinish(function () { clearTimeout(saveTimer); save(); });
    if (lms.onSaveStatus) lms.onSaveStatus(saveStatus);   /* nach den Start-Meldungen: ein schon fehlgeschlagenes Speichern wird gleich gemeldet */
  }
  function release() { hold = false; bakMsg = ''; }   /* erste eigene Eingabe: ab jetzt gilt der Stand auf der Seite */
  document.addEventListener('input', release);
  document.addEventListener('change', release);
  document.addEventListener('input', update);
  document.addEventListener('change', update);
  document.addEventListener('input', saveSoon);
  document.addEventListener('change', saveSoon);
  window.addEventListener('beforeprint', beforePrint);
  window.addEventListener('afterprint', endBlank);
  $('#pdfBtn').addEventListener('click', makePdf);
  $('#blankBtn').addEventListener('click', printBlank);
  if (/Zeichenschrift/.test(($('#zeichen-schriften') || {}).textContent || '')) setTimeout(ladeSchrift, 1500);   /* Schrift für den PDF-Export vorladen */
  if (scored && !submitted) $('#subBtn').hidden = false;
  update();
  save();
})();
