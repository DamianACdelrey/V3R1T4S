/* V3R1T4S site. Renders data.json (built from the repo by site/build.py).
   Every string in data.json comes from contributor-controlled files, so: text goes in with textContent only (never
   innerHTML), every string is length-capped, and every link is built here from a fixed GitHub prefix plus ids that
   must match strict patterns. data.json carries no URLs. */
(function () {
  'use strict';
  var GH = 'https://github.com/elder-plinius/V3R1T4S';
  var SLUG = /^[a-z0-9][a-z0-9-]{0,99}$/;
  var PKG = /^\d{4}-\d{2}-\d{2}-[A-Za-z0-9][A-Za-z0-9_.-]{0,63}-[0-9a-f]{8}$/;
  var DAY = /^(\d{4})-(\d{2})-(\d{2})$/;
  var CREDIT = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$/;
  var SAFE_URL = /^https:\/\/github\.com\/elder-plinius\/V3R1T4S\/[A-Za-z0-9._~\/?=&%-]*$/;
  var MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  var MARK = { o: ['✅', 'Listed by the table owner'], v: ['🧪', 'Verified by us, not yet listed by the table owner'] };
  var FEED_STEP = 12, KU_STEP = 40;

  function $(s) { return document.querySelector(s); }
  function str(x, n) { x = (x == null ? '' : String(x)); return x.length > n ? x.slice(0, n - 1) + '…' : x; }
  function int(x) { return typeof x === 'number' && isFinite(x) && x >= 0 && x < 1e9 ? Math.floor(x) : null; }
  function fmt(n) { return Number(n).toLocaleString('en-US'); }
  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    return e;
  }
  function link(url, cls, txt) {
    var a = el('a', cls, txt);
    if (SAFE_URL.test(url)) a.href = url;
    return a;
  }
  function emoji(x) {
    x = str(x, 16);
    return /^[©®‼-㊙\ud83c-🠀-\udfff️‍]{1,16}$/.test(x) ? x : '◆';
  }
  function dayLabel(d) {
    var m = DAY.exec(d);
    var mon = m && MONTHS[+m[2] - 1];
    return mon && +m[3] >= 1 && +m[3] <= 31 ? mon + ' ' + (+m[3]) + ', ' + m[1] : d;
  }

  /* ---------------- daily discoveries */
  var feed = [], feedShown = FEED_STEP;

  function feedItem(x) {
    var li = el('li', 'it');
    var e = el('span', 'e', emoji(x.e)); e.setAttribute('aria-hidden', 'true');
    var b = el('div', 'b');
    var href = SLUG.test(x.f) && PKG.test(x.k) ? GH + '/tree/main/known-knowns/' + x.f + '/' + x.k : null;
    b.appendChild(href ? link(href, 't', str(x.t, 140)) : el('span', 't', str(x.t, 140)));
    var meta = el('div', 'meta');
    var mk = MARK[x.s] || MARK.v;
    var st = el('span', 'st', mk[0]); st.setAttribute('role', 'img'); st.setAttribute('aria-label', mk[1]); st.title = mk[1];
    meta.appendChild(st);
    if (x.m) meta.appendChild(el('span', 'mg', str(x.m, 60)));
    if (CREDIT.test(x.c)) meta.appendChild(el('span', 'cr', 'by ' + x.c));
    b.appendChild(meta);
    li.appendChild(e); li.appendChild(b);
    li.appendChild(el('span'));
    return li;
  }

  function renderFeed() {
    var box = $('#feed'); box.textContent = '';
    if (!feed.length) { box.appendChild(el('p', 'empty', 'Nothing merged yet.')); return; }
    var group = null, last = null;
    feed.slice(0, feedShown).forEach(function (x) {
      if (x.d !== last) {
        last = x.d;
        var sec = el('section', 'day');
        sec.appendChild(el('h3', null, dayLabel(x.d)));
        group = el('ol'); sec.appendChild(group); box.appendChild(sec);
      }
      group.appendChild(feedItem(x));
    });
    var more = $('#feed-more');
    var left = feed.length - feedShown;
    more.hidden = left <= 0;
    more.textContent = 'Show more (' + fmt(Math.max(left, 0)) + ')';
  }

  /* ---------------- leaderboard */
  function renderBoard(rows) {
    var bo = $('#board'); bo.textContent = '';
    rows.slice(0, 10).forEach(function (r, i) {
      if (!CREDIT.test(r.c) || int(r.n) == null) return;
      var li = el('li');
      li.appendChild(el('span', 'r', String(i + 1)));
      var n = el('span', 'n', r.c); n.title = r.c;
      li.appendChild(n);
      li.appendChild(el('span', 'c', fmt(r.n)));
      bo.appendChild(li);
    });
  }

  /* ---------------- known unknowns */
  var ku = [], cats = {}, catList = [], kuCat = null, kuShown = KU_STEP, kuHits = [];

  function kuFilter() {
    var q = str($('#q').value, 100).toLowerCase().split(/\s+/).filter(Boolean);
    kuHits = ku.filter(function (k) {
      if (kuCat && k.cat !== kuCat) return false;
      if (!q.length) return true;
      var hay = k._hay;
      return q.every(function (w) { return hay.indexOf(w) !== -1; });
    });
  }

  function renderKu() {
    var ul = $('#kul'); ul.textContent = '';
    kuHits.slice(0, kuShown).forEach(function (k) {
      var c = cats[k.cat] || {};
      var li = el('li');
      var e = el('span', 'e', c.e || '◆'); e.setAttribute('aria-hidden', 'true');
      var b = el('div');
      b.appendChild(link(GH + '/blob/main/known-unknowns/' + k.cat + '/' + k.id + '.md', null, str(k.t, 180)));
      var bits = [c.name || k.cat];
      if (k.k) bits.push(str(k.k, 12));
      if (k.cp) bits.push(str(k.cp, 24));
      b.appendChild(el('span', 'meta', bits.join(' · ')));
      li.appendChild(e); li.appendChild(b); ul.appendChild(li);
    });
    if (!kuHits.length) ul.appendChild(el('li', 'empty', 'No match. Suggest it?'));
    var more = $('#ku-more'), left = kuHits.length - kuShown;
    more.hidden = left <= 0;
    more.textContent = 'Show more (' + fmt(Math.max(left, 0)) + ')';
    $('#ku-count').textContent = kuHits.length === ku.length ? fmt(ku.length) : fmt(kuHits.length) + ' / ' + fmt(ku.length);
  }

  function updateKu(announce) {
    kuShown = KU_STEP; kuFilter(); renderKu();
    if (announce) $('#ku-live').textContent = fmt(kuHits.length) + ' open problems';
  }

  function chip(id, label, n) {
    var b = el('button', 'chip');
    b.type = 'button';
    b.setAttribute('aria-pressed', String(id === kuCat));
    b.dataset.cat = id || '';
    b.appendChild(document.createTextNode(label));
    b.appendChild(el('span', 'k', fmt(n)));
    b.addEventListener('click', function () {
      kuCat = id;
      document.querySelectorAll('#chips .chip').forEach(function (c) {
        c.setAttribute('aria-pressed', String((c.dataset.cat || null) === kuCat));
      });
      updateKu(true);
    });
    return b;
  }

  function renderChips() {
    var box = $('#chips'); box.textContent = '';
    box.appendChild(chip(null, 'All', ku.length));
    catList.forEach(function (c) { box.appendChild(chip(c.id, c.e + ' ' + c.name, c.n)); });
  }

  /* ---------------- data */
  function load(D) {
    if (!D || D.schema !== 'v3r1t4s-site/2') throw new Error('bad data');
    feed = (Array.isArray(D.feed) ? D.feed : []).filter(function (x) {
      return x && DAY.test(x.d) && typeof x.t === 'string';
    }).slice(0, 20000);
    renderFeed();
    renderBoard(Array.isArray(D.board) ? D.board : []);
    (Array.isArray(D.cats) ? D.cats : []).forEach(function (c) {
      if (!c || !SLUG.test(c.id) || cats[c.id]) return;
      var o = { id: c.id, name: str(c.name, 40), e: emoji(c.e), n: int(c.n) || 0 };
      cats[c.id] = o; catList.push(o);
    });
    ku = (Array.isArray(D.ku) ? D.ku : []).filter(function (k) {
      return k && SLUG.test(k.id) && SLUG.test(k.cat) && cats[k.cat];
    }).slice(0, 20000).map(function (k) {
      return { id: k.id, cat: k.cat, t: str(k.t, 180), k: k.k ? str(k.k, 12) : null, cp: k.cp ? str(k.cp, 24) : null,
               _hay: (str(k.t, 180) + ' ' + k.id + ' ' + cats[k.cat].name).toLowerCase() };
    });
    catList.sort(function (a, b) { return b.n - a.n || (a.name < b.name ? -1 : 1); });
    renderChips();
    updateKu(false);
  }

  function fail() {
    var box = $('#feed'); box.textContent = '';
    var p = el('p', 'empty', 'Could not load the list. ');
    p.appendChild(link(GH + '/tree/main/known-knowns', null, 'Browse it on GitHub →'));
    box.appendChild(p);
  }

  function boot() {
    $('#feed-more').addEventListener('click', function () { feedShown += FEED_STEP; renderFeed(); });
    $('#ku-more').addEventListener('click', function () { kuShown += KU_STEP; renderKu(); });
    var t = null;
    $('#q').addEventListener('input', function () { clearTimeout(t); t = setTimeout(function () { updateKu(true); }, 120); });

    /* copy */
    var btn = $('#copy'), live = $('#live');
    btn.addEventListener('click', function () {
      var txt = $('#cmd').textContent;
      function done(ok) {
        btn.textContent = ok ? 'Copied' : 'Select';
        live.textContent = ok ? 'Copied to clipboard' : 'Press Ctrl+C to copy';
        if (!ok) { var s = window.getSelection(), r = document.createRange(); r.selectNodeContents($('#cmd')); s.removeAllRanges(); s.addRange(r); }
        setTimeout(function () { btn.textContent = 'Copy'; live.textContent = ''; }, 1800);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(function () { done(true); }, function () { done(false); });
      else done(false);
    });

    /* theme */
    var root = document.documentElement, tog = $('#tog');
    function isDark() { var a = root.getAttribute('data-theme'); return a ? a === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; }
    function sync() { tog.setAttribute('aria-pressed', String(isDark())); }
    tog.addEventListener('click', function () {
      var n = isDark() ? 'light' : 'dark';
      root.setAttribute('data-theme', n);
      try { localStorage.setItem('v3r1t4s-theme', n); } catch (e) {}
      sync();
    });
    sync();

    if (!window.fetch) { fail(); return; }
    fetch('data.json', { cache: 'no-cache', credentials: 'omit' })
      .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
      .then(load)
      .catch(fail);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
