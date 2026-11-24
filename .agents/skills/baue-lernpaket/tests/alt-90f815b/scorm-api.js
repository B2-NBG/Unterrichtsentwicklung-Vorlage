/*
  scorm-api.js - SCORM-2004-Anbindung fuer ByCS Lernplattform (Moodle). Offline-tauglich, keine Abhaengigkeiten.
  Nicht veraendern. Das E-Learning ruft nur ScormReport auf:

    ScormReport.init({ total: 10 });            // einmal beim Start: Anzahl der bewerteten Aufgaben
    ScormReport.answer('q1', true, {            // nach JEDER bewerteten Aufgabe (Teilpunkt)
      type: 'choice',                           // choice | true-false | fill-in | matching | numeric | performance
      response: 'b',                            // Antwort der Lernenden (choice: Buchstabe a, b, c ...)
      correctResponse: 'b',                     // optional: richtige Antwort
      weighting: 1                              // optional, Standard 1
    });
    ScormReport.complete();                     // nur fuer Inhalte ohne Punkte (reines Durchlesen)
    ScormReport.init({ scoring: false });       // nur Name lesen, keine Punkte (Notbehelf; Dokumente melden stattdessen ihren Bearbeitungsstand, siehe unten)
    ScormReport.studentName();                  // Name der Lernenden aus der Lernplattform
    ScormReport.saveState(obj);                 // Fortschritt (JSON-faehiges Objekt) in der Lernplattform speichern
    ScormReport.loadState();                    // gespeicherten Fortschritt holen (oder null)
    ScormReport.stateLimit                      // erlaubte Zeichen in suspend_data (SCORM 2004: 64000)
    ScormReport.beforeFinish(fn);               // fn wird direkt vor dem Beenden aufgerufen (letztes Speichern)

  Differenzierte Aufgaben (Standard fuer neue Pakete): Einsteigerniveau (blau) 40 %, Prüfungsniveau (rot) 40 %, Profiniveau (schwarz) 20 % der Punkte.
    ScormReport.init({ levels: { foundation: 5, core: 5, challenge: 3 } });   // Anzahl bewerteter Aufgaben je Niveau
    ScormReport.answer('q1', true, { level: 'foundation', type: 'choice', response: 'b' });
  Der Anteil eines Niveaus verteilt sich gleichmaessig auf seine Aufgaben. Fehlt ein Niveau, werden die uebrigen im Verhaeltnis 40:40:20 auf 100 % hochgerechnet.
  Dokumente (page.html): ScormReport.init({ levels: {...}, partial: true }) und ScormReport.answer('a1', true|false, { level: ..., type: 'performance' }) je bearbeiteter Aufgabe.
    Es gibt keine automatische Korrektur: Punkte = Bearbeitungsstand (bearbeitet = Punkte), gewichtet 40/40/20. Mit partial ist die Seite schon bei 80 % "completed" und "passed"
    (Einsteigerniveau + Prüfungsniveau bearbeitet); das Profiniveau bringt die restlichen 20 %.
  Dokumente mit Bewertung (aktuelle page.html): ScormReport.init({ levels: {...}, quality: true }) und je Aufgabe
    ScormReport.task('a1', { level: 'core', done: true, score: 0.5, response: 'Antworttext', description: 'Aufgabe 1.1 - Titel', correctResponse: '...' });
    done  = Aufgabe bearbeitet (etwas eingetragen). Abgeschlossen ("completed"), sobald alle Aufgaben des Einsteiger- und Prüfungsniveaus bearbeitet sind.
    score = wie gut (0 bis 1, Teilpunkte erlaubt). null = nicht automatisch prüfbar: dann zählt bearbeitet als volle Punkte.
    Punkte 0-100 = Bewertung, gewichtet 40/40/20. Bestanden ab 80 %.
    Jede Aufgabe hat genau EINE Interaktion im Moodle-Bericht (wird bei Änderung überschrieben): Titel, Antwort der Lernenden, erwartete Antwort,
    Ergebnis (correct / incorrect / Anteil 0..1 / neutral = nur bearbeitet). task() schreibt ohne Commit; danach ScormReport.flush() oder saveState().
  Abgabe (aktuelle page.html): ScormReport.init({ levels: {...}, quality: true, submit: true }) und beim Klick auf "Abgeben" ScormReport.submit().
    Vor der Abgabe: "incomplete", keine Punkte (Interaktionen und Fortschritt werden aber laufend gemeldet).
    Mit der Abgabe: "completed", Punkte, "passed" (ab 80) oder "failed". Danach nimmt die Schnittstelle keine Änderungen mehr an
    (task, saveState). Der Versuch bleibt "suspend", damit die Seite beim erneuten Öffnen den abgegebenen Stand zeigt.
  ScormReport.isSubmitted()                     // true, wenn schon abgegeben (auch aus einer früheren Sitzung)
  ScormReport.taskState('a1')                   // { d: 1/0 bearbeitet, s: 0..1 Bewertung } oder undefined
  ScormReport.state('a1')                       // 1 / 0 / undefined: bereits gemeldete Antwort (aus dem gespeicherten Fortschritt)
  Gemeldet werden immer cmi.score.raw / min / max / scaled, cmi.completion_status und cmi.success_status (ohne diese Werte zeigt Moodle 0 Punkte).
  Ohne levels: Punkte = richtige Aufgaben / total x 100 (ganze Zahl, 0 bis 100).
  Bestehensgrenze ist immer 80 % (= Einsteigerniveau + Prüfungsniveau komplett). Sind alle Aufgaben beantwortet: passed (ab 80) oder failed.
  Einmal bestanden bleibt bestanden. Wird die Datei ohne Lernplattform geoeffnet, passiert nichts.
*/
(function (w) {
  'use strict';

  var MASTERY = 80;
  var LEVEL_WEIGHT = { foundation: 40, core: 40, challenge: 20 };   // Einsteigerniveau blau, Prüfungsniveau rot, Profiniveau schwarz
  var api = null, started = false, finished = false, startMs = 0, hooks = [];
  var total = 0, levelN = null, levelOf = {}, answers = {}, pageState = null, icount = 0, wasPassed = false, wasCompleted = false, scoring = true, partial = false;
  var quality = false, done = {}, iIndex = {};   /* quality: bearbeitet (done) und Bewertung (answers) getrennt; iIndex: feste Interaktion je Aufgabe */
  var needSubmit = false, submitted = false;     /* Abgabe-Modus: Punkte und Status erst mit submit() */

  function findApi(win) {
    var hops = 0;
    try {
      while (win && !win.API_1484_11 && win.parent && win.parent !== win && hops < 20) { win = win.parent; hops++; }
      return (win && win.API_1484_11) || null;
    } catch (e) { return null; }
  }

  function call(m, arg) { try { return api ? String(api[m](arg)) : ''; } catch (e) { return ''; } }
  function get(k) { try { return api ? String(api.GetValue(k)) : ''; } catch (e) { return ''; } }
  function set(k, v) { try { if (api) api.SetValue(k, String(v)); } catch (e) { /* still */ } }
  function commit() { call('Commit', ''); }

  function sessionTime(ms) {
    var s = Math.floor(ms / 1000);
    return 'PT' + Math.floor(s / 3600) + 'H' + (Math.floor(s / 60) % 60) + 'M' + (s % 60) + 'S';
  }
  function cleanId(id) { return String(id).replace(/[^A-Za-z0-9_\-]/g, '_').substring(0, 250); }
  /* Text fuer description (CMILangString250): Moodle lehnt "{" und Zeilenumbrueche ab */
  function langStr(s, n) { return String(s).replace(/[{}]/g, '').replace(/\s+/g, ' ').trim().substring(0, n); }

  function counts() {
    var c = 0, n = 0, k;
    for (k in answers) { if (answers.hasOwnProperty(k)) { n++; c += +answers[k] || 0; } }   /* Teilpunkte 0..1 zaehlen anteilig */
    return { correct: c, answered: n };
  }

  /* Bearbeitet-Pruefung (quality): alle Aufgaben des Einsteiger- und Prüfungsniveaus bearbeitet (fehlen beide: alle Aufgaben) */
  function allTasksDone() {
    var n = {}, k, l, need = levelN ? ((levelN.foundation || levelN.core) ? ['foundation', 'core'] : ['challenge']) : null, c = 0;
    for (k in done) { if (done.hasOwnProperty(k) && done[k] === 1) { c++; l = levelOf[k] || 'core'; n[l] = (n[l] || 0) + 1; } }
    if (!need) return total > 0 && c >= total;
    for (k = 0; k < need.length; k++) { l = need[k]; if (levelN[l] && (n[l] || 0) < levelN[l]) return false; }
    return true;
  }
  function doneCount() { var c = 0, k; for (k in done) { if (done.hasOwnProperty(k) && done[k] === 1) c++; } return c; }

  /* Punkte 0-100: mit Niveaus gewichtet (40/40/20), sonst richtige / total */
  function levelSum() { var s = 0, l; for (l in levelN) { if (levelN.hasOwnProperty(l) && levelN[l] > 0) s += LEVEL_WEIGHT[l]; } return s; }
  function result() {
    var c = counts();
    if (!levelN) return { raw: total > 0 ? Math.min(100, Math.round(100 * c.correct / total)) : 0, answered: c.answered };
    var ok = {}, k, l, pts = 0, sumW = levelSum();
    for (k in answers) { if (answers.hasOwnProperty(k) && +answers[k] > 0) { l = levelOf[k] || 'core'; ok[l] = (ok[l] || 0) + (+answers[k]); } }
    for (l in levelN) { if (levelN.hasOwnProperty(l) && levelN[l] > 0) pts += LEVEL_WEIGHT[l] * Math.min(1, (ok[l] || 0) / levelN[l]); }
    return { raw: sumW ? Math.round(100 * pts / sumW) : 0, answered: c.answered };
  }

  /* suspend_data: {"a":{Aufgaben-ID:0/1},"s":<Zustand der Seite>}; gibt false zurueck, wenn zu lang */
  function writeSuspend() {
    var o = {}, k, has = false;
    for (k in answers) { if (answers.hasOwnProperty(k)) { has = true; break; } }
    if (has) o.a = answers;
    if (has && levelN) o.l = levelOf;
    if (quality) { o.d = done; o.i = iIndex; }
    if (submitted) o.x = 1;
    if (pageState !== null) o.s = pageState;
    var s = JSON.stringify(o);
    if (s.length > ScormReport.stateLimit) return false;
    set('cmi.suspend_data', s);
    return true;
  }

  function update(noCommit) {
    if (!api || !scoring) return;
    var c = result(), raw = c.raw;
    if (needSubmit && !submitted) {   /* noch nicht abgegeben: nur Fortschritt, keine Punkte */
      set('cmi.progress_measure', total > 0 ? Math.min(1, doneCount() / total) : 0);
      set('cmi.completion_status', 'incomplete');
      writeSuspend();
      if (!noCommit) commit();
      return;
    }
    var allDone = needSubmit ? true : (quality ? allTasksDone() : (partial ? raw >= MASTERY : (c.answered >= total && total > 0))), passed = raw >= MASTERY || wasPassed;
    if (allDone) { wasCompleted = true; if (passed) wasPassed = true; }
    set('cmi.score.min', 0); set('cmi.score.max', 100); set('cmi.score.raw', raw); set('cmi.score.scaled', raw / 100);
    set('cmi.progress_measure', total > 0 ? Math.min(1, (quality ? doneCount() : c.answered) / total) : 0);
    set('cmi.completion_status', (allDone || wasCompleted) ? 'completed' : 'incomplete');
    set('cmi.success_status', allDone ? (passed ? 'passed' : 'failed') : (wasPassed ? 'passed' : 'unknown'));
    writeSuspend();
    if (!noCommit) commit();
  }

  var ScormReport = {
    connected: false,
    stateLimit: 64000,

    init: function (opts) {
      if (started) return;
      started = true;
      startMs = new Date().getTime();
      scoring = !(opts && opts.scoring === false);
      partial = !!(opts && opts.partial);
      quality = !!(opts && opts.quality);
      needSubmit = !!(opts && opts.submit);
      total = (opts && opts.total) ? Math.max(1, Math.floor(opts.total)) : 0;
      if (opts && opts.levels) {
        levelN = {}; total = 0;
        for (var lv in LEVEL_WEIGHT) { if (LEVEL_WEIGHT.hasOwnProperty(lv)) { var cnt = Math.max(0, Math.floor(opts.levels[lv] || 0)); if (cnt) { levelN[lv] = cnt; total += cnt; } } }
        if (!total) levelN = null;
      }
      api = findApi(w) || (w.opener ? findApi(w.opener) : null);
      if (!api) return;
      if (call('Initialize', '') === 'false') { api = null; return; }
      ScormReport.connected = true;
      var status = get('cmi.completion_status');
      wasPassed = (get('cmi.success_status') === 'passed');
      wasCompleted = (status === 'completed');
      var sd = get('cmi.suspend_data');
      if (sd) { try { var o = JSON.parse(sd); if (o && typeof o === 'object') { answers = o.a || {}; levelOf = o.l || {}; done = o.d || {}; iIndex = o.i || {}; submitted = needSubmit && o.x === 1; pageState = (o.s === undefined) ? null : o.s; } } catch (e) { answers = {}; done = {}; iIndex = {}; pageState = null; } }
      if (needSubmit && status === 'completed') submitted = true;   /* im Abgabe-Modus heisst "completed" immer: abgegeben */
      var n = parseInt(get('cmi.interactions._count'), 10);
      icount = isNaN(n) ? 0 : n;
      if (status === '' || status === 'not attempted' || status === 'unknown') set('cmi.completion_status', 'incomplete');
      update();
    },

    answer: function (id, correct, info) {
      if (!started) return;
      var key = cleanId(id);
      answers[key] = correct ? 1 : 0;
      info = info || {};
      var weight = 1;
      if (levelN) {
        var lv = LEVEL_WEIGHT[info.level] ? info.level : 'core';
        levelOf[key] = lv;
        weight = levelN[lv] ? Math.round(10000 * LEVEL_WEIGHT[lv] / levelSum() / levelN[lv]) / 100 : 0;
      }
      if (api) {
        var p = 'cmi.interactions.' + icount + '.';
        set(p + 'id', key);
        set(p + 'timestamp', new Date().toISOString().replace(/\.\d+Z$/, 'Z'));
        set(p + 'type', info.type || 'choice');
        if (info.correctResponse != null) set(p + 'correct_responses.0.pattern', String(info.correctResponse).substring(0, 255));
        set(p + 'weighting', info.weighting != null ? info.weighting : weight);
        if (info.response != null) set(p + 'learner_response', String(info.response).substring(0, 255));
        set(p + 'result', correct ? 'correct' : 'incorrect');
        icount++;
      }
      update();
    },

    /* Eine Aufgabe melden (Dokumente mit quality): bearbeitet + Bewertung + Antwort, eine feste Interaktion je Aufgabe. Ohne Commit. */
    task: function (id, info) {
      if (!started || submitted) return;   /* nach der Abgabe keine Änderungen mehr */
      info = info || {};
      var key = cleanId(id), d = info.done ? 1 : 0, checked = info.score != null;
      var s = checked ? Math.max(0, Math.min(1, +info.score || 0)) : d;
      s = Math.round(s * 100) / 100;
      answers[key] = s; done[key] = d;
      var weight = 1;
      if (levelN) {
        var lv = LEVEL_WEIGHT[info.level] ? info.level : 'core';
        levelOf[key] = lv;
        weight = levelN[lv] ? Math.round(10000 * LEVEL_WEIGHT[lv] / levelSum() / levelN[lv]) / 100 : 0;
      }
      if (api) {
        var n = iIndex.hasOwnProperty(key) ? iIndex[key] : -1;
        if (n < 0 || n >= icount) { n = icount++; iIndex[key] = n; }   /* neue Interaktion nur beim ersten Mal */
        var p = 'cmi.interactions.' + n + '.';
        set(p + 'id', key);
        set(p + 'type', 'other');   /* "other": freier Text bis 4000 Zeichen, von Moodle ohne Formatpruefung angenommen */
        set(p + 'timestamp', new Date().toISOString().replace(/\.\d+Z$/, 'Z'));
        set(p + 'weighting', weight);
        if (info.description) set(p + 'description', langStr(info.description, 250));
        if (info.correctResponse) set(p + 'correct_responses.0.pattern', String(info.correctResponse).substring(0, 4000));
        set(p + 'learner_response', (d ? String(info.response || 'bearbeitet') : 'offen').substring(0, 4000));
        set(p + 'result', !checked ? 'neutral' : (s >= 1 ? 'correct' : (s <= 0 ? 'incorrect' : String(s))));
      }
      update(true);
    },
    taskState: function (id) { var k = cleanId(id); return answers.hasOwnProperty(k) ? { d: done[k] === 1 ? 1 : 0, s: +answers[k] } : undefined; },
    flush: function () { if (api) commit(); },

    /* Abgabe: ab jetzt completed + Punkte + passed/failed; danach keine Änderungen mehr */
    submit: function () {
      if (!started || submitted) return;
      submitted = true;
      update();
    },
    isSubmitted: function () { return submitted; },

    /* Reiner Lesestoff ohne bewertbare Aufgaben: abgeschlossen = 100 Punkte, bestanden */
    complete: function () {
      if (!started || !api) return;
      wasCompleted = true;
      set('cmi.completion_status', 'completed');
      if (!levelN && total === 0) {
        wasPassed = true;
        set('cmi.score.min', 0); set('cmi.score.max', 100); set('cmi.score.raw', 100); set('cmi.score.scaled', 1);
        set('cmi.progress_measure', 1);
        set('cmi.success_status', 'passed');
      }
      commit();
    },

    /* bereits gemeldete Antwort (1 richtig/bearbeitet, 0 falsch/leer, undefined = noch nie gemeldet) */
    state: function (id) { return answers[cleanId(id)]; },

    /* Name der Lernenden aus der Lernplattform ("Nachname, Vorname" wird zu "Vorname Nachname"). Nur zur Anzeige, wird nicht gespeichert. */
    studentName: function () {
      var n = get('cmi.learner_name').trim(), p;
      if (n.indexOf(',') > -1) { p = n.split(','); n = (p.slice(1).join(',').trim() + ' ' + p[0].trim()).trim(); }
      return n;
    },

    /* Zustand der Seite (Eingaben) speichern. true = gespeichert, false = nicht moeglich oder zu lang. */
    saveState: function (obj) {
      if (!api || submitted) return false;
      var keep = pageState;
      pageState = obj;
      if (!writeSuspend()) { pageState = keep; return false; }
      commit();
      return true;
    },
    loadState: function () { return pageState; },
    beforeFinish: function (fn) { hooks.push(fn); },

    finish: function () {
      if (finished || !started) return;
      finished = true;
      hooks.forEach(function (fn) { try { fn(); } catch (e) { /* still */ } });
      if (!api) return;
      var st = get('cmi.completion_status');
      set('cmi.session_time', sessionTime(new Date().getTime() - startMs));
      /* Abgabe-Modus: immer suspend, damit der abgegebene Stand (Bewertung, Lösungen) beim erneuten Öffnen erhalten bleibt */
      set('cmi.exit', (needSubmit || st === 'incomplete' || st === 'unknown') ? 'suspend' : 'normal');
      commit();
      call('Terminate', '');
    },

    letter: function (i) { return 'abcdefghijklmnopqrstuvwxyz'.charAt(i); }
  };

  w.ScormReport = ScormReport;
  w.addEventListener('pagehide', ScormReport.finish);
  w.addEventListener('beforeunload', ScormReport.finish);
  w.addEventListener('unload', ScormReport.finish);
})(window);
