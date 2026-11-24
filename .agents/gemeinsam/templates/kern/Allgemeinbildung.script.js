
/* Layout "Lernschritte": Schritt-Leiste, Phasen mit Timer, Ergebnis-Seite. Nur Navigation und Anzeige;
   Bewertung, Speichern, Abgabe, PDF und Lösungssperre erledigt das Script aus Fachunterricht.html darüber. */
(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };
  function esc(s) { var d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  var body = document.body, nav = $('#stepnav'), steps = $$('main > section.step'), cur = 0, links = [];
  var KEY = 'steps-cur|' + location.pathname + '|' + document.title;

  /* ---------- Phasen: Sozialform, Minuten, Timer (immer nur einer läuft) ---------- */
  var FORMS = { einzel: 'Einzelarbeit', partner: 'Partnerarbeit', gruppe: 'Gruppenarbeit', plenum: 'Plenum', wahl: 'Wahlaufgabe' };
  var tm = null;
  function beep() {
    try {
      var C = window.AudioContext || window.webkitAudioContext; if (!C) return;
      var a = new C();
      [0, .35, .7].forEach(function (t) { var o = a.createOscillator(), g = a.createGain(); o.frequency.value = 880; g.gain.value = .15; o.connect(g); g.connect(a.destination); o.start(a.currentTime + t); o.stop(a.currentTime + t + .2); });
    } catch (e) { /* ohne Ton weiter */ }
  }
  function stopTimer() { if (!tm) return; clearInterval(tm.id); tm.btn.textContent = 'Timer starten'; tm.disp.textContent = ''; tm.p.classList.remove('run', 'over'); tm = null; }
  function tick() {
    if (!tm) return;
    var r = Math.max(0, Math.round((tm.end - Date.now()) / 1000)), m = Math.floor(r / 60), s = r % 60;
    tm.disp.textContent = (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
    if (r <= 0) { clearInterval(tm.id); tm.p.classList.remove('run'); tm.p.classList.add('over'); tm.disp.textContent = 'Zeit ist um'; tm.btn.textContent = 'Timer starten'; tm = null; beep(); }
  }
  $$('.phasebar').forEach(function (p) {
    var f = p.getAttribute('data-form') || 'einzel', min = parseFloat(String(p.getAttribute('data-min') || '').replace(',', '.')) || 0, title = p.textContent.trim();
    p.classList.add('ph-' + f);
    p.innerHTML = '<span class="pf">' + esc(p.getAttribute('data-label') || FORMS[f] || f) + '</span><span class="pt">' + esc(title) + '</span>' +
                  (min ? '<span class="pm">' + String(min).replace('.', ',') + ' Min</span>' : '');
    if (!min) return;
    var disp = document.createElement('span'), btn = document.createElement('button');
    disp.className = 'ph-time'; disp.setAttribute('aria-live', 'off');
    btn.type = 'button'; btn.className = 'btn alt ph-btn'; btn.textContent = 'Timer starten';
    btn.addEventListener('click', function () {
      if (tm && tm.btn === btn) { stopTimer(); return; }
      stopTimer(); p.classList.remove('over');
      tm = { id: setInterval(tick, 250), btn: btn, disp: disp, p: p, end: Date.now() + min * 60000 };
      btn.textContent = 'Timer stoppen'; p.classList.add('run'); tick();
    });
    p.appendChild(btn); p.appendChild(disp);
  });

  if (!steps.length || !nav) return;

  /* ---------- Schritte: Leiste, Stunden-Label, Zurück/Weiter ---------- */
  function headOf(s) { return s.querySelector('h2, .h2'); }
  function titleOf(s) { var h = headOf(s); return s.getAttribute('data-title') || (h ? h.textContent.replace(/^\s*\d+\s*[·.:-]\s*/, '').trim() : ''); }
  steps.forEach(function (s, i) {
    var b = document.createElement('button'), t = titleOf(s), l = s.getAttribute('data-lesson') || '';
    b.type = 'button'; b.className = 'pill'; b.textContent = String(i + 1);
    b.title = t + (l ? ' · ' + l : ''); b.setAttribute('aria-label', 'Schritt ' + (i + 1) + (t ? ': ' + t : ''));
    b.addEventListener('click', function () { show(i); });
    nav.appendChild(b);
    if (l) { var d = document.createElement('div'), h = headOf(s); d.className = 'lesson'; d.textContent = l; s.insertBefore(d, h && h.parentNode === s ? h : s.firstChild); }
    var p = document.createElement('div'), bk = document.createElement('button'), nx = document.createElement('button');
    p.className = 'pager';
    bk.type = 'button'; bk.className = 'btn alt'; bk.textContent = 'Zurück';
    nx.type = 'button'; nx.className = 'btn'; nx.textContent = 'Weiter';
    if (i === 0) bk.style.visibility = 'hidden';
    if (i === steps.length - 1) nx.style.visibility = 'hidden';
    bk.addEventListener('click', function () { show(i - 1); });
    nx.addEventListener('click', function () { show(i + 1); });
    p.appendChild(bk); p.appendChild(nx); s.appendChild(p);
  });
  var pills = $$('.pill', nav);
  function show(i, keepScroll) {
    if (i < 0 || i >= steps.length) return;
    cur = i;
    steps.forEach(function (s, k) { s.classList.toggle('on', k === i); });
    pills.forEach(function (p, k) { p.classList.toggle('on', k === i); if (k === i) p.setAttribute('aria-current', 'step'); else p.removeAttribute('aria-current'); });
    nav.scrollLeft = pills[i].offsetLeft - (nav.clientWidth - pills[i].offsetWidth) / 2;
    try { localStorage.setItem(KEY, String(i)); } catch (e) { /* ohne Speicher weiter */ }
    if (steps[i].classList.contains('result')) renderResult();
    if (!keepScroll) {   /* neuer Schritt beginnt oben, direkt unter der Leiste */
      var hb = $('header.titleblock'), y = hb ? hb.getBoundingClientRect().bottom + window.pageYOffset : 0;
      if (window.pageYOffset > y) window.scrollTo(0, y);
    }
  }

  /* ---------- Fortschritt: Punkt an der Leiste, wenn alle Pflichtaufgaben eines Schritts bearbeitet sind ---------- */
  function stepDone(s) {
    var all = $$('.task[data-done]', s), req = all.filter(function (t) { return !t.closest('.level.challenge'); }), list = req.length ? req : all;
    return list.length > 0 && list.every(function (t) { return t.getAttribute('data-done') === '1'; });
  }
  function renderResult() {
    var box = $('#stepResult'); if (!box) return;
    var showQ = body.classList.contains('submitted') || body.classList.contains('solOpen'), rows = '', n = 0, d = 0;
    links = [];
    steps.forEach(function (s, i) {
      $$('.task[data-done]', s).forEach(function (t) {
        var ok = t.getAttribute('data-done') === '1', q = showQ ? (t.getAttribute('data-q') || '') : '', tt = ((t.querySelector('.tt') || {}).textContent || 'Aufgabe').trim();
        var pt = t.getAttribute(showQ ? 'data-ptsq' : 'data-pts') || '';   /* Höchstpunkte, im Lehrkraft-Modus und nach der Abgabe erreichte Punkte */
        n++; if (ok) d++; links.push([i, t]);
        rows += '<tr><td>' + (i + 1) + '</td><td><button type="button" class="linkbtn" data-k="' + (links.length - 1) + '">' + esc(tt) + '</button>' +
                (t.closest('.level.challenge') ? ' <small>(Profiniveau, freiwillig)</small>' : '') +
                '</td><td class="' + (ok ? 'st-ok' : 'st-open') + '">' + (ok ? 'bearbeitet' : 'offen') + (q ? '<br><small>' + esc(q) + '</small>' : '') + '</td><td>' + esc(pt) + '</td></tr>';
      });
    });
    var res = (($('#resultInfo') || {}).textContent || '').trim(), sub = $('#subBtn'), canSub = !!(sub && !sub.hidden);
    box.innerHTML = (n ? '<div class="bar" aria-hidden="true"><i style="width:' + Math.round(d / n * 100) + '%"></i></div><p><b>' + d + ' von ' + n + ' Aufgaben bearbeitet</b></p>' +
                         '<table><thead><tr><th>Schritt</th><th>Aufgabe</th><th>Stand</th><th>Punkte</th></tr></thead><tbody>' + rows + '</tbody></table>'
                       : '<p>Auf dieser Seite gibt es keine Aufgaben mit Eingabefeldern.</p>') +
                    (res ? '<p><b>' + esc(res) + '</b></p>' : '') +
                    '<div class="stepactions">' + (canSub ? '<button type="button" class="btn" data-act="sub">Abgeben</button>' : '') +
                    '<button type="button" class="btn' + (canSub ? ' alt' : '') + '" data-act="pdf">Als PDF speichern</button></div>';
  }
  var rbox = $('#stepResult');
  if (rbox) rbox.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    var act = b.getAttribute('data-act'), k = b.getAttribute('data-k');
    if (act === 'sub') { $('#subBtn').click(); return; }
    if (act === 'pdf') { $('#pdfBtn').click(); return; }
    if (k === null || !links[+k]) return;
    var t = links[+k][1], f = t.querySelector('input:not([type=hidden]), textarea, select');
    show(links[+k][0]); t.scrollIntoView({ block: 'center' });
    if (f) { try { f.focus({ preventScroll: true }); } catch (x) { f.focus(); } }
  });
  var pend = 0;
  function refresh() { pend = 0; pills.forEach(function (p, k) { p.classList.toggle('done', stepDone(steps[k])); }); if (steps[cur].classList.contains('result')) renderResult(); }
  function soon() { if (!pend) pend = setTimeout(refresh, 60); }
  if (window.MutationObserver) {   /* data-done / data-q setzt das Script der Vorlage, body.submitted / solOpen ebenso */
    new MutationObserver(soon).observe($('main'), { subtree: true, attributes: true, attributeFilter: ['data-done', 'data-q', 'data-ptsq'] });
    new MutationObserver(soon).observe(body, { attributes: true, attributeFilter: ['class'] });
  }

  /* ---------- Druck: alle Schritte zeigen, Textfelder und Seitenumbrüche neu messen (ausgeblendete Schritte waren 0 px hoch) ---------- */
  window.addEventListener('beforeprint', function () {
    body.classList.add('printAll');
    if (!body.classList.contains('blankPrint')) $$('textarea').forEach(function (a) { a.style.height = 'auto'; a.style.height = a.scrollHeight + 'px'; });
    $$('main .task, main .card').forEach(function (t) { t.classList.toggle('keep', t.getBoundingClientRect().height <= 250); });
  });
  window.addEventListener('afterprint', function () { body.classList.remove('printAll'); });

  body.classList.add('stepsOn');
  var start = 0;
  try { start = parseInt(localStorage.getItem(KEY), 10) || 0; } catch (e) { /* ohne Speicher weiter */ }
  show(Math.min(Math.max(start, 0), steps.length - 1), true);
  refresh();
})();
