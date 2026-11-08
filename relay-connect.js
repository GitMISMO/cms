/* =============================================================================================================
   relay-connect.js: the Certification Management System on resources.mismo.org (Perry, 9 Oct 2026)

   The page in index.html is built to run inside Claude, where it asks for three services: "user" (who is signed in,
   may they write), "db" (its edit collections: cycleState, invoices, orgEdits, scores, activity, ...) and "downloads".
   On resources.mismo.org this file provides the same three through MISMO's shared sign-in and relay, so the page's own
   logic runs unchanged, and it loads the real records from the private cms-data repository in place of the empty
   public placeholders before the page starts.

   What the page needs, kept to three hooks so a rebuild can carry them:
     1. <script src="/assets/session.js"></script> in <head>                      (the shared sign-in)
     2. the application script tagged <script type="text/x-cms-app" id="cms-app">  (started here, once the records are in)
     3. <span id="rs-account"></span> in the masthead, and <script src="relay-connect.js"></script> last in <body>

   Records:  portal-data.json and data/<file>.json in cms-data are only ever READ here: they are what Jonna's build
             produces from MACTS and the correction files.
   Edits:    each collection the page writes is data/db-<collection>.json in cms-data, {docs: {<id>: <body>}}, read and
             written through the relay with the version it last read (a conflict re-reads and re-applies the change).
   Access:   who may open it, and who may save (Edit) or only look (View), is set per person in People & Access, key cms.
   ============================================================================================================= */
(function () {
  'use strict';
  var RELAY = 'https://rgvdi67cg27o5kcmiytcqbqnrm0hmztx.lambda-url.us-east-1.on.aws';
  var PROJECT = 'cms', TOOL = 'Certification Management System';
  window.CMS_CONFIG = { relay: RELAY, project: PROJECT };   /* so the page's banner names the relay if it is ever unreachable */
  var RS = window.ResourcesSession;

  /* page data key -> data/<file>.json (the base records, as Jonna's build lays them out) */
  var FILES = { pricing: 'pricing', notices: 'renewal-notices', companyContacts: 'company-contacts', certScripts: 'cert-scripts', assessorFirms: 'assessor-firms', consultantScorecard: 'consultant-scorecard',
    consultantSubmissions: 'consultant-submissions', applicantForms: 'applicant-forms', individualCerts: 'individual-certifications',
    summits: 'summits', frameResults: 'frame-results', frameScenarios: 'frame-scenarios', frameScoring: 'frame-scoring', frameSources: 'frame-sources' };
  var FILE_LABEL = { pricing: 'the price list', notices: 'the renewal notice wording', companyContacts: 'the company contact book', certScripts: 'the certification scripts',
    assessorFirms: 'the assessor firms', consultantScorecard: 'the Consultant scorecard', consultantSubmissions: 'the Consultant submissions', applicantForms: 'the application forms',
    individualCerts: 'the CMSP and AMSP list', summits: 'the summits', frameResults: 'the FRAME results', frameScenarios: 'the FRAME exercises', frameScoring: 'the FRAME scoring', frameSources: 'the FRAME sources' };
  var COLL_LABEL = { 'cycle-state': 'certification stages', invoices: 'invoices', activity: 'the Activity log', finance: 'payments', 'renewal-quotes': 'renewal invoices',
    'cert-edits': 'certification details', 'org-edits': 'company details', 'mark-license': 'Mark Licenses', 'follow-ups': 'follow-ups', membership: 'memberships',
    applications: 'applications', 'aptify-orders': 'Aptify orders', 'notice-log': 'renewal notices sent', 'stage-notice-log': 'stage emails sent', scores: 'scores',
    'assessor-notes': 'assessor notes', 'assessor-nudges': 'assessor nudges', 'invoice-sends': 'invoice emails', 'script-prep': 'certification scripts', assessments: 'assessments' };
  function collLabel(n) { return COLL_LABEL[n] || String(n).replace(/-/g, ' '); }

  /* ---------- "some records did not load" (review, 7 Nov 2026) ----------
     27 of the page's 28 record loads showed nothing when they failed, so a dropped connection looked like
     empty or old records. Every failed load now shows here until it succeeds again (the page re-reads
     every minute, so most clear by themselves). kind: 'base' = read once at the start (only a reload
     brings it back); 'load' = never loaded; 'stale' = loaded, but has not refreshed for 3 minutes. */
  var PROBLEMS = {};
  function problem(key, label, kind) { PROBLEMS[key] = { label: label, kind: kind }; drawProblems(); }
  function solved(key) { if (PROBLEMS[key]) { delete PROBLEMS[key]; drawProblems(); } }
  function drawProblems() {
    try {
      var keys = Object.keys(PROBLEMS), box = document.getElementById('rc-problems');
      if (!keys.length) { if (box) box.remove(); return; }
      if (!document.body) return;
      if (!box) {
        box = document.createElement('div'); box.id = 'rc-problems'; box.setAttribute('role', 'alert');
        box.style.cssText = 'position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:7000;width:min(640px,calc(100vw - 32px));box-sizing:border-box;' +
          'padding:12px 14px;border-radius:8px;border-left:4px solid #b42318;background:#fdecea;color:#5c1410;font:14px/1.45 "Libre Franklin",system-ui,sans-serif;box-shadow:0 6px 24px rgba(13,49,76,.18)';
        document.body.appendChild(box);
      }
      var base = keys.filter(function (k) { return PROBLEMS[k].kind === 'base'; }), load = keys.filter(function (k) { return PROBLEMS[k].kind === 'load'; }),
          stale = keys.filter(function (k) { return PROBLEMS[k].kind === 'stale'; });
      var names = function (ks) { return ks.map(function (k) { return PROBLEMS[k].label; }).join(', '); };
      var lines = [];
      if (base.length || load.length) lines.push('<b>Some records did not load:</b> ' + esc(names(base.concat(load))) + '. What you see may be missing them.');
      if (stale.length) lines.push('<b>Not updated for a few minutes:</b> ' + esc(names(stale)) + '. Other people\u2019s changes may not show yet.');
      box.innerHTML = lines.join('<br>') + '<div style="margin-top:8px;display:flex;gap:8px;flex-wrap:wrap">' +
        (base.length ? '<button type="button" data-rc="reload" style="' + BTN + '">Reload the Page</button>' : '<button type="button" data-rc="retry" style="' + BTN + '">Try Again Now</button>') +
        '<span style="align-self:center;font-size:12.5px;opacity:.85">' + (base.length ? 'Anything already saved is safe.' : 'This clears by itself once the connection is back.') + '</span></div>';
    } catch (e) { if (window.console) console.error('Load notice:', e); }
  }
  var BTN = 'font:600 13px inherit;padding:6px 12px;border-radius:4px;border:1px solid #b42318;background:#fff;color:#5c1410;cursor:pointer';
  function esc(t) { return String(t).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  document.addEventListener('click', function (ev) {
    var b = ev.target && ev.target.closest && ev.target.closest('#rc-problems [data-rc]'); if (!b) return;
    if (b.getAttribute('data-rc') === 'reload') location.reload(); else refresh(true);
  });

  /* the page looks questionnaires up by program code; the eMortgage file names eClosing ECLOSING, the programs ECLOSE */
  var EMORTGAGE = { RON: 'RON', ECLOSE: 'ECLOSING', EVAULT: 'EVAULT' };

  /* ---------- a cover while it signs in and loads ---------- */
  var cover = document.createElement('div');
  cover.id = 'cms-cover';
  cover.setAttribute('role', 'status');
  cover.style.cssText = 'position:fixed;inset:0;z-index:8000;display:flex;align-items:center;justify-content:center;background:var(--paper,#F4F7FA);color:var(--ink,#0F314C);font:600 15px "Libre Franklin",system-ui,sans-serif';
  cover.textContent = 'Loading the certification records\u2026';
  document.body.appendChild(cover);
  function fail(msg) { cover.style.cursor = 'default'; cover.innerHTML = '<div style="max-width:460px;text-align:center;line-height:1.5"><b>The certification records could not be loaded.</b><br>' + msg + '<br><br><a href="" style="color:#2C74A6">Try again</a></div>'; }

  /* ---------- the relay ---------- */
  function call(method, path, body) {
    var headers = { 'Authorization': 'Bearer ' + (RS && RS.token ? RS.token() : '') };
    if (body) headers['Content-Type'] = 'application/json';
    return fetch(RELAY + '/' + PROJECT + path, { method: method, headers: headers, body: body ? JSON.stringify(body) : undefined })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { return { status: r.status, json: j || {} }; }); });
  }
  function err(code, message) { var e = new Error(message || code); e.code = code; return e; }
  function fromBase64(b64) {
    var bin = atob(b64), bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    return new TextDecoder('utf-8').decode(bytes);
  }
  var clone = function (v) { return v === undefined ? undefined : JSON.parse(JSON.stringify(v)); };

  /* ---------- the base records: read once, before the page starts ---------- */
  /* A read that fails on a busy moment (no answer, or a server error) is tried twice more before it counts
     as failed (review, 7 Nov 2026). A refusal (403) or a missing file (404) is not retried. */
  function callRetry(method, path) {
    function go(n) {
      return call(method, path).then(function (r) {
        if ((r.status >= 500 || r.status === 429) && n < 2) return wait(n).then(function () { return go(n + 1); });
        return r;
      }, function (e) { if (n < 2) return wait(n).then(function () { return go(n + 1); }); throw e; });
    }
    function wait(n) { return new Promise(function (ok) { setTimeout(ok, n ? 4000 : 1500); }); }
    return go(0);
  }
  function readData(name) {
    return callRetry('GET', '/data/' + name).then(function (r) {
      if (r.status !== 200 || r.json.data == null) throw err('unavailable', 'data/' + name + '.json (' + (r.json.error || r.status) + ')');
      var d = r.json.data; delete d.savedBy; delete d.savedAt; return d;
    });
  }
  function loadRecords() {
    var D = JSON.parse(document.getElementById('cms-data').textContent);
    var jobs = [callRetry('GET', '/file/portal-data.json').then(function (r) {
      if (r.status !== 200 || !r.json.content) throw err('unavailable', 'portal-data.json (' + (r.json.error || r.status) + ')');
      var P = JSON.parse(fromBase64(r.json.content));
      Object.keys(P).forEach(function (k) { D[k] = P[k]; });
      /* The page counts days from D.asOf (days to an anniversary, days at a step, the date a payment or
         a new application is recorded). portal-data.json carries the date it was exported, which stays
         put while every record on top of it is live, so the page thought it was still 24 October
         (found in the 31 Oct 2026 full test). Today, in Eastern time, from here on; the export date is
         kept as D.dataAsOf. */
      D.dataAsOf = D.asOf;
      var gone = 0;
      try { gone = Math.max(0, Math.round((Date.parse(new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' })) - Date.parse(D.asOf)) / 864e5)); } catch (e) {}
      /* a cycle's "open N days" was counted at the export too */
      if (gone) ['inFlight', 'pipelines', 'newApplications'].forEach(function (k) {
        (D[k] || []).forEach(function (f) { if (f && typeof f.age === 'number') f.age += gone; });
      });
      try { D.asOf = new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' }); }
      catch (e) { var t = new Date(); D.asOf = t.getFullYear() + '-' + ('0' + (t.getMonth() + 1)).slice(-2) + '-' + ('0' + t.getDate()).slice(-2); }
    })];
    /* One of these failing used to stop the whole page for everyone (review, 6 Nov 2026). Now the page opens
       with the rest, keeps the built-in copy of the one that failed, and says so at the foot of the screen. */
    Object.keys(FILES).forEach(function (k) { jobs.push(readData(FILES[k]).then(function (v) { D[k] = v; }, function () { problem('file:' + FILES[k], FILE_LABEL[k] || FILES[k], 'base'); })); });
    /* past Mark License Agreements filed from the MACTS attachments; optional, so a missing index never stops the page */
    jobs.push(readData('mark-license-files').then(function (v) { D.markLicenseFiles = v; }, function () { D.markLicenseFiles = null; }));
    /* the MACTS Comments sheet, carried over 27 Oct 2026; optional the same way */
    jobs.push(readData('macts-comments').then(function (v) { D.mactsComments = v; }, function () { D.mactsComments = null; }));
    jobs.push(readData('macts-documents').then(function (v) { D.mactsDocuments = v; }, function () { D.mactsDocuments = null; }));
    /* what each company sent for mismo.org on its renewal page (31 Oct 2026); optional the same way */
    jobs.push(readData('website-answers').then(function (v) { D.websiteAnswers = v; }, function () { D.websiteAnswers = null; }));
    jobs.push(Promise.all([readData('frame-questionnaire'), readData('emortgage-questionnaires')]).then(function (r) {
      var forms = { FRAME: r[0] }, docs = (r[1] && r[1].docs) || {};
      Object.keys(EMORTGAGE).forEach(function (code) { if (docs[EMORTGAGE[code]]) forms[code] = docs[EMORTGAGE[code]]; });
      D.forms = forms;
    }, function () { problem('file:questionnaires', 'the questionnaires', 'base'); }));
    return Promise.all(jobs).then(function () { D.publicPreview = false; return D; });
  }

  /* ---------- saving without overwriting anyone (November 5, 2026) ----------
     The page saves a whole record each time (a cycle's stage, an invoice, a company's edits), built from
     what this browser last loaded. The page only re-reads every minute, and not at all while the tab is
     in the background, so that copy can be hours old. Saving used to write it exactly as it was, and when
     the relay said someone else had saved first, the same old copy was written again on top of theirs.
     So a teammate's change could be quietly undone: a cycle they had approved went back a stage, an
     invoice they had marked paid went back to unpaid.

     Now each save remembers what the page had for that record before the change ("seen"), and writes
     only what was actually changed here, merged into the newest copy at the moment it is written, every
     time it is tried. Everything else keeps its newest value. A list both people added to keeps both
     people's items. If both people changed the same field, the person saving is asked which to keep. A
     record someone else removed is not brought back unless the person saving says so, and the open
     record panel says when someone else saves the record it is showing. The files and fields are
     exactly as before: only what is written into them changed. */
  function stable(v) {
    if (Array.isArray(v)) return '[' + v.map(stable).join(',') + ']';
    if (v && typeof v === 'object') return '{' + Object.keys(v).filter(function (k) { return v[k] !== undefined; }).sort().map(function (k) { return JSON.stringify(k) + ':' + stable(v[k]); }).join(',') + '}';
    return JSON.stringify(v);
  }
  /* blank, null and missing are the same; 5 and "5" are the same */
  function normVal(v) {
    if (v === undefined || v === null || v === '') return '';
    if (typeof v === 'number' || typeof v === 'boolean') return String(v);
    if (typeof v === 'string') return v;
    return stable(v);
  }
  function sameVal(x, y) { return normVal(x) === normVal(y); }
  function plainObj(v) { return !!v && typeof v === 'object' && !Array.isArray(v); }
  var META = { by: 1, at: 1, updatedAt: 1, updatedBy: 1, updatedByName: 1 };   /* who saved last: never a clash */
  /* a list both people changed: what was taken out here goes, what was added here is added, theirs stays */
  function mergeList(cur, mine, base) {
    cur = Array.isArray(cur) ? cur : []; mine = Array.isArray(mine) ? mine : []; base = Array.isArray(base) ? base : [];
    var had = {}, keep = {}, have = {};
    base.forEach(function (x) { had[stable(x)] = 1; });
    mine.forEach(function (x) { keep[stable(x)] = 1; });
    var out = cur.filter(function (x) { return !(had[stable(x)] && !keep[stable(x)]); });
    out.forEach(function (x) { have[stable(x)] = 1; });
    mine.forEach(function (x) { var k = stable(x); if (!had[k] && !have[k]) { out.push(clone(x)); have[k] = 1; } });
    return out;
  }
  /* cur: the copy stored now. mine: what this page is saving. base: what this page had before its change.
     A field not changed here keeps cur's value. clashes collects the fields both people changed; keep says
     whose value each one takes once the person has been asked ('mine' or 'theirs'). */
  function mergeDoc(cur, mine, base, path, clashes, keep) {
    var out = plainObj(cur) ? clone(cur) : {}, keys = {};
    mine = plainObj(mine) ? mine : {}; base = plainObj(base) ? base : {};
    Object.keys(mine).concat(Object.keys(base)).forEach(function (k) { keys[k] = 1; });
    Object.keys(keys).forEach(function (k) {
      var m = mine[k], b = base[k], c = out[k], p = path ? path + '.' + k : k;
      if (sameVal(m, b)) return;                                         /* not changed here: the newest value stands */
      if (plainObj(m) && (plainObj(b) || b == null) && (plainObj(c) || c == null)) { out[k] = mergeDoc(c, m, b || {}, p, clashes, keep); return; }   /* field by field inside it */
      if (!sameVal(c, b) && !sameVal(c, m)) {                            /* someone else changed it too, differently */
        if (Array.isArray(m) && (Array.isArray(b) || b == null)) { out[k] = mergeList(c, m, b); return; }
        if (!META[k]) {
          if (!keep[p]) clashes.push({ path: p, theirs: c, mine: m });
          if (keep[p] !== 'mine') return;
        }
      }
      if (m === undefined) delete out[k]; else out[k] = clone(m);
    });
    return out;
  }
  function recName(doc) {
    var o = doc && (doc.org || doc.name || doc.company || doc.firm);
    return o ? String(o) + (doc.program ? ' (' + doc.program + ')' : '') : 'this record';
  }
  function fieldName(p) {
    return String(p).split('.').map(function (k) {
      return k.replace(/([a-z])([A-Z])/g, '$1 $2').replace(/^./, function (c) { return c.toUpperCase(); });
    }).join(' › ');
  }
  function showVal(v) { var t = normVal(v); return t === '' ? '(blank)' : t.length > 80 ? t.slice(0, 80) + '…' : t; }
  /* Records the page works out for itself and nobody edits (the Member 360 match, redone every six hours
     by whoever opens the CMS) are written whole, as before: the newest working-out is the right one. */
  var WHOLE = { membership: 1 };
  /* the whole change for one record, onto the copy stored now; false when there is nothing to write */
  function mergeInto(d, id, body, base, had, keep) {
    var cur = d[id];
    if (!had || !plainObj(body) || (base === undefined && cur === undefined)) { d[id] = clone(body); return true; }   /* a new record, or a collection this page never read: as before */
    if (cur === undefined) {
      /* someone else removed it after this page loaded it */
      var changedHere = Object.keys(Object.assign({}, base, body)).filter(function (k) { return !META[k] && !sameVal(body[k], base[k]); });
      if (!changedHere.length) return false;                           /* nothing of this page's own to save on it */
      if (keep['*removed'] === undefined) keep['*removed'] = window.confirm('While you had ' + recName(base) + ' open, someone else removed it.\n\nOK saves it again with your change. Cancel leaves it removed.') ? 'mine' : 'theirs';
      if (keep['*removed'] !== 'mine') return false;
      d[id] = clone(body); return true;
    }
    var clashes = [], out = mergeDoc(cur, body, base || {}, '', clashes, keep);
    if (clashes.length) {
      var yours = window.confirm('While you had ' + recName(cur) + ' open, someone else saved a different value in the same ' + (clashes.length === 1 ? 'field' : 'fields') + ':\n\n' +
        clashes.map(function (x) { return '• ' + fieldName(x.path) + ' — theirs: ' + showVal(x.theirs) + '   ·   yours: ' + showVal(x.mine); }).join('\n') +
        '\n\nOK keeps yours. Cancel keeps theirs for ' + (clashes.length === 1 ? 'this field' : 'these fields') + ' — your other changes still save.');
      clashes.forEach(function (x) { keep[x.path] = yours ? 'mine' : 'theirs'; });
      out = mergeDoc(cur, body, base || {}, '', [], keep);
    }
    if (stable(out) === stable(cur)) return false;
    d[id] = out; return true;
  }
  /* The open record panel says so when someone else saves what it is showing. index.html names the
     records its panel shows (window.__cmsPanelDocs); without that, nothing is shown. */
  var staleFor = null;
  function staleCheck(name, ids) {
    try {
      if (!ids.length || typeof window.__cmsPanelDocs !== 'function') return;
      var drawer = document.getElementById('drawer');
      if (!drawer || !drawer.classList.contains('on')) return;
      var shown = window.__cmsPanelDocs() || [];
      if (!ids.some(function (id) { return shown.indexOf(name + '/' + id) >= 0; })) return;
      var box = document.getElementById('rc-stale');
      if (!box) {
        box = document.createElement('div'); box.id = 'rc-stale'; box.setAttribute('role', 'status');
        box.style.cssText = 'margin:8px 20px 0;padding:9px 12px;border-radius:6px;font-size:13px;line-height:1.4;border-left:3px solid var(--warn,#a2701a);background:var(--surface-2,#f6fafd);color:var(--ink,#0d314c)';
        var head = drawer.querySelector('.dhead');
        if (head && head.parentNode) head.parentNode.insertBefore(box, head.nextSibling); else drawer.insertBefore(box, drawer.firstChild);
      }
      box.textContent = 'Someone else just saved this record. Saving keeps their changes and adds yours.';
      box.style.display = '';
      staleFor = stable(shown);
    } catch (e) { if (window.console) console.error('Stale notice:', e); }
  }
  setInterval(function () {   /* the notice goes when the panel closes or shows another record */
    var box = document.getElementById('rc-stale');
    if (!box || box.style.display === 'none') return;
    var drawer = document.getElementById('drawer'), shown = null;
    try { shown = typeof window.__cmsPanelDocs === 'function' ? stable(window.__cmsPanelDocs() || []) : null; } catch (e) {}
    if (!drawer || !drawer.classList.contains('on') || shown !== staleFor) box.style.display = 'none';
  }, 1500);

  /* ---------- "db": the page's edit collections, one private file each ---------- */
  var COLL = {};
  /* seen: each record as this page last had it (what it was given, plus its own saves); given: whether
     this page has been handed the collection at all (November 5, 2026) */
  function coll(name) { return COLL[name] || (COLL[name] = { name: name, docs: {}, sha: null, loaded: null, subs: [], queue: Promise.resolve(), seen: {}, given: false, pending: {} }); }
  function given(c) { c.seen = clone(c.docs) || {}; c.given = true; }
  function seenOf(c, id) { return c.given && c.seen[id] !== undefined ? clone(c.seen[id]) : undefined; }
  function fileOf(name) { return 'db-' + String(name).replace(/[^A-Za-z0-9_-]/g, '_'); }
  function fetchColl(c) {
    return callRetry('GET', '/data/' + fileOf(c.name)).then(function (r) {
      if (r.status !== 200) throw err(r.status === 403 ? 'permission_denied' : 'unavailable', r.json.error || String(r.status));
      var d = r.json.data; c.docs = (d && d.docs) || {}; c.sha = r.json.sha || null;
      c.fails = 0; c.ok = true; c.readAt = Date.now(); solved('coll:' + c.name); return c;
    }, function (e) { throw e; }).catch(function (e) {
      c.fails = (c.fails || 0) + 1;
      if (!c.ok) problem('coll:' + c.name, collLabel(c.name), 'load');
      else if (c.fails >= 3) problem('coll:' + c.name, collLabel(c.name), 'stale');
      throw e;
    });
  }
  function load(c) { return c.loaded || (c.loaded = fetchColl(c).catch(function (e) { c.loaded = null; throw e; })); }
  /* opts: {order: [field, 'asc'|'desc'], limit: n}, as the page's activity log asks for (orderBy("at","desc").limit(80)) */
  function snapshot(c, opts) {
    opts = opts || {};
    var ids = Object.keys(c.docs);
    if (opts.order) { var f = opts.order[0], desc = String(opts.order[1]).toLowerCase() === 'desc';
      ids.sort(function (a, b) { var x = (c.docs[a] || {})[f], y = (c.docs[b] || {})[f]; if (x === y) return 0; if (x === undefined) return 1; if (y === undefined) return -1; return (x < y ? -1 : 1) * (desc ? -1 : 1); }); }
    if (opts.limit != null) ids = ids.slice(0, opts.limit);
    var docs = ids.map(function (id) { var v = c.docs[id]; return { id: id, exists: true, data: function () { return clone(v); } }; });
    return { docs: docs, size: docs.length, empty: !docs.length, forEach: function (f) { docs.forEach(f); } };
  }
  function notify(c) {
    /* the records that changed from what this page had, other than its own saves still on their way */
    var was = c.seen, ids = c.given ? Object.keys(Object.assign({}, was, c.docs)).filter(function (id) { return !c.pending[id] && !sameVal(was[id], c.docs[id]); }) : [];
    given(c);
    var s = snapshot(c); c.subs.slice().forEach(function (sub) { try { sub.next(s); } catch (e) { if (window.console) console.error(e); } });
    staleCheck(c.name, ids);
  }
  /* one write at a time per collection; on a conflict, re-read and apply the change again on top of what is there.
     A change that finds nothing to write (it returns false) writes nothing, and the page is shown what is
     stored (November 5, 2026). */
  function write(name, change) {
    var c = coll(name);
    function attempt(tries) {
      var next = clone(c.docs) || {};
      if (change(next) === false) { notify(c); return Promise.resolve(); }   /* the page shows what is stored, not what it guessed */
      return call('PUT', '/data/' + fileOf(name), { content: { docs: next }, sha: c.sha }).then(function (r) {
        if (r.status === 200) { c.docs = next; c.sha = r.json.sha || c.sha; notify(c); return; }
        if (r.status === 409 && tries < 4) return fetchColl(c).then(function () { return attempt(tries + 1); });
        if (r.status === 403) throw err('invalid_argument', 'View only: not saved');   /* the page shows its own view-only notice */
        throw err('unavailable', 'Not saved (' + (r.json.error || r.status) + ')');
      });
    }
    var run = function () { return load(c).then(function () { return attempt(0); }); };
    c.queue = c.queue.then(run, run);
    return c.queue;
  }
  /* other people's changes: re-read what this page is watching every minute while it is open and visible,
     and straight away when the tab is looked at again (November 5, 2026: a tab left in the background for
     hours showed hours-old records for up to a minute after coming back) */
  /* The activity log is the one record that only grows. It is re-read every minute while the Activity screen
     is showing, and every 5 minutes otherwise (November 8, 2026). */
  var SLOW = { activity: 'view-activity' };
  function slowSkip(c) {
    var v = SLOW[c.name]; if (!v || !c.ok) return false;
    var el = document.getElementById(v); if (el && el.classList.contains('on')) return false;
    return Date.now() - (c.readAt || 0) < 5 * 60 * 1000;
  }
  function refresh(force) {
    if (document.hidden && !force) return;
    Object.keys(COLL).forEach(function (n) { var c = COLL[n]; if (!c.subs.length || (!force && slowSkip(c))) return; var was = c.sha, first = !c.ok;
      c.queue = c.queue.then(function () { return fetchColl(c).then(function () { if (c.sha !== was || first) later(c); }); }).catch(function () {}); });
  }
  /* Other people's changes redraw the page, and a redraw rebuilt the open panel, so a note being typed could
     vanish when a colleague saved (review, 6 Nov 2026). While the panel has a field being typed in, or typing
     not yet saved, their changes wait and show as soon as the field is left or the panel saves or closes.
     The page's own saves are not held. */
  var held = {};
  function typing() {
    var drawer = document.getElementById('drawer'), a = document.activeElement;
    var isText = function (el) { return el && (el.tagName === 'TEXTAREA' || el.isContentEditable || (el.tagName === 'INPUT' && !/^(button|submit|checkbox|radio|file|range|color|reset|image|hidden)$/i.test(el.type || ''))); };
    if (!drawer || !drawer.classList.contains('on')) return false;
    if (isText(a) && drawer.contains(a)) return true;                                                 /* typing in the panel now */
    var f = drawer.querySelectorAll('textarea, input');
    for (var i = 0; i < f.length; i++) if (isText(f[i]) && f[i].value !== f[i].defaultValue) return true;   /* typed in the panel, not saved yet */
    return false;
  }
  function later(c) {
    if (!typing()) { delete held[c.name]; notify(c); return; }
    held[c.name] = c; heldNote(true);
  }
  function release() {
    var names = Object.keys(held); if (!names.length || typing()) return;
    held = {}; heldNote(false);
    names.forEach(function (n) { if (COLL[n]) notify(COLL[n]); });
  }
  function heldNote(on) {
    try {
      var box = document.getElementById('rc-held'), drawer = document.getElementById('drawer');
      if (!on || !drawer || !drawer.classList.contains('on')) { if (box) box.remove(); return; }
      if (!box) {
        box = document.createElement('div'); box.id = 'rc-held'; box.setAttribute('role', 'status');
        box.style.cssText = 'margin:8px 20px 0;padding:8px 12px;border-radius:6px;font-size:12.5px;line-height:1.4;border-left:3px solid var(--sky,#74bfeb);background:var(--surface-2,#f6fafd);color:var(--ink,#0d314c)';
        var head = drawer.querySelector('.dhead');
        if (head && head.parentNode) head.parentNode.insertBefore(box, head.nextSibling); else drawer.insertBefore(box, drawer.firstChild);
      }
      box.textContent = 'Someone else saved changes. They will show once you save or close this panel, so your typing is safe.';
    } catch (e) {}
  }
  document.addEventListener('focusout', function () { setTimeout(release, 400); });
  setInterval(release, 2000);
  setInterval(refresh, 60000);
  document.addEventListener('visibilitychange', function () { if (!document.hidden) refresh(); });
  /* opening the Activity screen brings the log up to date at once if it was last read a while ago */
  document.addEventListener('click', function (e) {
    var b = e.target && e.target.closest ? e.target.closest('[data-view="activity"]') : null; if (!b) return;
    var c = COLL.activity; if (!c || !c.ok || Date.now() - (c.readAt || 0) < 60000) return;
    setTimeout(function () { c.queue = c.queue.then(function () { var was = c.sha; return fetchColl(c).then(function () { if (c.sha !== was) later(c); }); }).catch(function () {}); }, 0);
  });
  /* A save: what this page had before (seen) is taken now, when the page asks, and the change is merged
     into the stored copy each time it is tried. keep remembers the person's answers across retries. */
  function saveDoc(name, id, body) {
    var c = coll(name), base = seenOf(c, id), had = c.given, keep = {};
    if (had) { if (body === undefined || body === null) delete c.seen[id]; else c.seen[id] = clone(body); }
    c.pending[id] = (c.pending[id] || 0) + 1;
    var done = function () { if (!--c.pending[id]) delete c.pending[id]; };
    var p = write(name, function (d) { return mergeInto(d, id, body, base, had && !WHOLE[name], keep); });
    p.then(done, done);
    return p;
  }
  function removeDoc(name, id) {
    var c = coll(name), base = seenOf(c, id), had = c.given, keep = {};
    if (had) delete c.seen[id];
    return write(name, function (d) {
      if (d[id] === undefined) return false;                              /* already gone */
      if (had && !sameVal(d[id], base)) {                                  /* someone else changed it after this page loaded it */
        if (keep.remove === undefined) keep.remove = window.confirm('Someone else changed ' + recName(d[id]) + ' after this page last loaded it.\n\nOK removes it anyway. Cancel keeps their version.');
        if (!keep.remove) return false;
      }
      delete d[id];
    });
  }
  function docRef(name, id) {
    var c = coll(name);
    return {
      id: id,
      set: function (body) { return saveDoc(name, id, body); },
      replace: function (body) { return saveDoc(name, id, body); },
      update: function (body) { return write(name, function (d) { d[id] = Object.assign({}, d[id] || {}, clone(body)); }); },   /* already field by field */
      'delete': function () { return removeDoc(name, id); },
      get: function () { return load(c).then(function () { if (!c.given) given(c); var v = c.docs[id]; return { id: id, exists: v !== undefined, data: function () { return clone(v); } }; }); },
      onSnapshot: function (next, error) {
        var sub = { next: function () { var v = c.docs[id]; next({ id: id, exists: v !== undefined, data: function () { return clone(v); } }); } };
        c.subs.push(sub); load(c).then(function () { if (!c.given) given(c); sub.next(); }, function (e) { if (error) error(e); });
        return function () { c.subs = c.subs.filter(function (x) { return x !== sub; }); };
      }
    };
  }
  function query(name, opts) {
    var c = coll(name);
    return {
      orderBy: function (field, dir) { return query(name, Object.assign({}, opts, { order: [field, dir || 'asc'] })); },
      limit: function (n) { return query(name, Object.assign({}, opts, { limit: n })); },
      get: function () { return load(c).then(function () { if (!c.given) given(c); return snapshot(c, opts); }); },
      onSnapshot: function (next, error) {
        var sub = { next: function (s) { next(opts.order || opts.limit != null ? snapshot(c, opts) : s); } }; c.subs.push(sub);
        load(c).then(function () { if (!c.given) given(c); next(snapshot(c, opts)); }, function (e) { if (error) error(e); });
        return function () { c.subs = c.subs.filter(function (x) { return x !== sub; }); };
      }
    };
  }
  var db = {
    collection: function (name) {
      return Object.assign(query(name, {}), {
        doc: function (id) { return docRef(name, String(id)); },
        add: function (body) { var id = Date.now().toString(36) + Math.random().toString(36).slice(2, 8); return write(name, function (d) { d[id] = clone(body); }).then(function () { return docRef(name, id); }); }
      });
    },
    doc: function (path) { var i = String(path).indexOf('/'); return docRef(String(path).slice(0, i), String(path).slice(i + 1)); }
  };

  /* ---------- "user" and "downloads" ---------- */
  var user = {
    can: function (what) { return what === 'data.write' ? !!(RS && RS.canEdit && RS.canEdit(PROJECT)) : true; },
    me: function () { var s = RS && RS.current ? RS.current() : null; return s ? { name: s.name || s.email, email: s.email } : null; }
  };
  var downloads = {
    save: function (o) { var a = document.createElement('a'); a.href = o.url; a.download = o.filename || 'download'; document.body.appendChild(a); a.click(); a.remove(); return Promise.resolve(true); }
  };

  /* ---------- the Sent Emails tab (26 Oct 2026) ----------
     Every email the certification system has sent, from the logs the senders keep, shown as a tab
     beside Activity. The list itself is sent.html (in this repository), embedded here, so it needs
     nothing from the page's own build. It is added here rather than in the artifact so that
     rebuilding index.html from the artifact cannot drop it; it can move into the artifact at the
     next rebuild. */
  function addSentEmailsTab() {
    try {
      var act = document.querySelector('.navlink[data-view="activity"]');
      var actView = document.getElementById('view-activity');
      if (!act || !actView || document.getElementById('view-emails')) return;
      var btn = document.createElement('button');
      btn.className = 'navlink'; btn.type = 'button'; btn.setAttribute('data-view', 'emails'); btn.title = 'Sent Emails';
      btn.innerHTML = '<span class="ni"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5.5" width="18" height="13" rx="1.6"/><path d="m3.6 7 8.4 6 8.4-6"/></svg></span><span class="nl">Sent Emails</span>';
      act.parentNode.insertBefore(btn, act.nextSibling);
      var sec = document.createElement('section');
      sec.className = 'view'; sec.id = 'view-emails';
      var frame = document.createElement('iframe');
      frame.title = 'Sent Emails'; frame.style.cssText = 'width:100%;border:0;display:block;min-height:70vh';
      sec.appendChild(frame);
      actView.parentNode.insertBefore(sec, actView.nextSibling);
      btn.addEventListener('click', function () {
        if (!frame.src) frame.src = 'sent.html?embed=1';          /* loaded the first time it is opened */
        if (window.__showView) window.__showView('emails');
      });
      window.addEventListener('message', function (e) {
        if (e.origin === location.origin && e.data && e.data.sentEmailsHeight) frame.style.height = (e.data.sentEmailsHeight + 24) + 'px';
      });
    } catch (e) { if (window.console) console.error('Sent Emails tab:', e); }
  }

  /* ---------- the left nav, in the order the work is done (Jonna, 26 Oct 2026) ----------
     Daily Work holds everything that has a to-do count; Companies and Reporting the records;
     Tracking what the system has done and sent; Setup what is configured once. The two pages
     that live beside the CMS (My Approvals, the Email Playbook) sit in the nav with the rest.
     A count of nothing is not shown: a badge only appears when there is something to do.
     Done here, after the page has run, so a rebuild of index.html from the artifact keeps it. */
  var NAV = [
    /* Renewals and Invoices are records now: everything to act on is on the Action Queue's to-do list (Jonna, 27 Oct 2026). */
    /* My Approvals, the Email Playbook and Help open inside the CMS, so the nav is always there
       (Jonna, 27 Oct 2026). Migration is gone from the nav: MACTS is fully moved over. */
    /* CMSP & AMSP (27 Oct 2026): MISMO's individual certifications, off the CMSP and AMSP Master Smartsheets. */
    { label: 'Daily Work', items: ['queue', 'assessors', 'approvals', 'individual'] },
    { label: 'Records and Reporting', items: ['records', 'renewals', 'invoices', 'revenue', 'counts'] },
    { label: 'Tracking', items: ['activity', 'emails'] },
    { label: 'Setup', items: ['programs', 'pricing', 'forms', 'lifecycle', 'playbook'] },
    { label: 'Help', items: ['help'] }
  ];
  var HIDDEN = [];   /* the Migration screen ('load') was removed, 8 Nov 2026 */
  var EMBEDS = {
    approvals: { src: 'approvals.html?embed=1', label: 'My Approvals', title: 'Results waiting for a VP decision',
      icon: '<path d="M12 3.2 19.5 6v5.6c0 4.5-3.1 8.1-7.5 9.2-4.4-1.1-7.5-4.7-7.5-9.2V6Z"/><path d="m8.6 12.2 2.4 2.4 4.6-4.8"/>' },
    playbook: { src: 'playbook.html?embed=1', label: 'Email Playbook', title: 'Every certification email and its wording',
      icon: '<path d="M4.5 4.5h6.2a2.3 2.3 0 0 1 2.3 2.3v13.7a2 2 0 0 0-2-2H4.5Z"/><path d="M19.5 4.5h-4.2A2.3 2.3 0 0 0 13 6.8v13.7a2 2 0 0 1 2-2h4.5Z"/>' },
    individual: { src: 'individual.html?embed=1', label: 'CMSP & AMSP', title: 'Individual certifications: applications, renewals, certificates and reminders',
      icon: '<circle cx="12" cy="8" r="3.6"/><path d="M5 20.2c.8-3.6 3.6-5.6 7-5.6s6.2 2 7 5.6"/><path d="m15.6 3.6 1.2 1.2 2.4-2.4"/>' },
    help: { src: 'help.html?embed=1', label: 'Help', title: 'How the system and the certification process work',
      icon: '<circle cx="12" cy="12" r="8.5"/><path d="M9.6 9.4a2.5 2.5 0 0 1 4.8.9c0 1.7-2.4 2.1-2.4 3.7"/><path d="M12 17h.01"/>' }
  };
  /* A page that lives beside the CMS, shown as a view inside it (the same way as Sent Emails). */
  function addEmbedViews() {
    try {
      var nav = document.getElementById('mismonav');
      var anchor = document.getElementById('view-activity');
      if (!nav || !anchor) return;
      Object.keys(EMBEDS).forEach(function (k) {
        if (document.getElementById('view-' + k)) return;
        var e = EMBEDS[k];
        var btn = document.createElement('button');
        btn.className = 'navlink'; btn.type = 'button'; btn.setAttribute('data-view', k); btn.title = e.title;
        btn.innerHTML = '<span class="ni"><svg viewBox="0 0 24 24" aria-hidden="true">' + e.icon + '</svg></span><span class="nl">' + e.label + '</span>';
        nav.appendChild(btn);
        var sec = document.createElement('section');
        sec.className = 'view'; sec.id = 'view-' + k;
        var frame = document.createElement('iframe');
        frame.title = e.label; frame.setAttribute('data-embed', k);
        frame.style.cssText = 'width:100%;border:0;display:block;min-height:80vh';
        sec.appendChild(frame);
        anchor.parentNode.insertBefore(sec, anchor.nextSibling);
        btn.addEventListener('click', function () {
          if (!frame.src) frame.src = e.src;
          if (window.__showView) window.__showView(k);
          try { history.replaceState(null, '', '#' + k); } catch (x) {}
        });
      });
      window.addEventListener('message', function (ev) {
        if (ev.origin !== location.origin || !ev.data || !ev.data.embedHeight) return;
        var f = document.querySelector('iframe[data-embed="' + ev.data.page + '"]');
        if (f) f.style.height = (ev.data.embedHeight + 24) + 'px';
      });
    } catch (e) { if (window.console) console.error('Embedded pages:', e); }
  }
  /* A link to /cms/#help (or any view) opens that view. */
  function openFromHash() {
    try {
      var k = (location.hash || '').replace(/^#/, '');
      if (!k) return;
      var b = document.querySelector('.navlink[data-view="' + k.replace(/[^a-z-]/gi, '') + '"]');
      if (b) b.click();
    } catch (e) {}
  }
  /* The foot of the nav: when the CMS last heard from MISMO Money, and when it last gave
     MISMO Money its approvals (Jonna, 27 Oct 2026). */
  function moneySync() {
    try {
      var foot = document.querySelector('.side-foot');
      if (!foot || document.getElementById('money-sync')) return;
      var st = document.createElement('style');
      st.textContent = '#money-sync{padding:6px 10px 10px;font-size:11px;line-height:1.45;color:var(--side-dim, rgba(255,255,255,.62))}'
        + '#money-sync b{display:block;font-size:10px;letter-spacing:.08em;text-transform:uppercase;font-weight:600;margin-bottom:2px;color:var(--side-ink, #fff);opacity:.8}'
        + '#money-sync .ms-row{display:flex;gap:6px;align-items:flex-start}#money-sync .ms-dot{flex:0 0 7px;height:7px;border-radius:50%;margin-top:4px;background:#4fc79b}'
        + '#money-sync .ms-dot.old{background:#e0a83c}#money-sync .ms-dot.none{background:#8aa3b6}'
        + 'body.nav-collapsed #money-sync .ms-t, body.nav-collapsed #money-sync b{display:none}body.nav-collapsed #money-sync{padding:6px 0 10px;display:flex;flex-direction:column;align-items:center;gap:6px}';
      document.head.appendChild(st);
      var box = document.createElement('div');
      box.id = 'money-sync';
      box.innerHTML = '<b>MISMO Money</b><div class="ms-row" id="ms-in"><span class="ms-dot none"></span><span class="ms-t">Received: checking&hellip;</span></div>'
        + '<div class="ms-row" id="ms-out"><span class="ms-dot none"></span><span class="ms-t">Sent: checking&hellip;</span></div>';
      foot.insertBefore(box, foot.firstChild);
      var when = function (iso) {
        var d = new Date(iso); if (isNaN(d)) return null;
        return d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit', timeZone: 'America/New_York' }) + ' ET';
      };
      var paint = function (id, label, iso, extra, staleDays) {
        var row = document.getElementById(id); if (!row) return;
        var t = iso ? when(iso) : null;
        var age = iso ? (Date.now() - new Date(iso).getTime()) / 864e5 : null;
        row.querySelector('.ms-dot').className = 'ms-dot' + (!t ? ' none' : age > staleDays ? ' old' : '');
        row.querySelector('.ms-t').textContent = label + ': ' + (t || 'nothing yet') + (extra ? ' (' + extra + ')' : '');
        row.title = label + ' ' + (t || 'nothing yet') + (extra ? ', ' + extra : '') + (age > staleDays ? '. Older than expected.' : '');
      };
      call('GET', '/data/mismo-money-paid').then(function (r) {
        var d = r.json && r.json.data || {};
        paint('ms-in', 'Received', d.writtenAt || null, d.paymentsThrough ? 'payments through ' + d.paymentsThrough : '', 3);
      }, function () { paint('ms-in', 'Received', null, '', 3); });
      call('GET', '/data/mismo-money-approvals').then(function (r) {
        var d = r.json && r.json.data || {};
        var n = d.approvals ? Object.keys(d.approvals).length : 0;
        paint('ms-out', 'Sent', d.writtenAt || null, n ? n + ' approvals' : '', Infinity); // the date approvals last changed: never "older than expected" (27 Oct 2026)
      }, function () { paint('ms-out', 'Sent', null, '', 30); });
    } catch (e) { if (window.console) console.error('MISMO Money sync:', e); }
  }
  var PAGES = {
    approvals: { href: 'approvals.html', label: 'My Approvals', title: 'Results waiting for a VP decision',
      icon: '<path d="M12 3.2 19.5 6v5.6c0 4.5-3.1 8.1-7.5 9.2-4.4-1.1-7.5-4.7-7.5-9.2V6Z"/><path d="m8.6 12.2 2.4 2.4 4.6-4.8"/>' },
    playbook: { href: 'playbook.html', label: 'Email Playbook', title: 'Every certification email and its wording',
      icon: '<path d="M4.5 4.5h6.2a2.3 2.3 0 0 1 2.3 2.3v13.7a2 2 0 0 0-2-2H4.5Z"/><path d="M19.5 4.5h-4.2A2.3 2.3 0 0 0 13 6.8v13.7a2 2 0 0 1 2-2h4.5Z"/>' }
  };
  function organizeNav() {
    try {
      var nav = document.getElementById('mismonav');
      if (!nav || nav.getAttribute('data-organized')) return;
      var byView = {};
      Array.prototype.forEach.call(nav.querySelectorAll('.navlink[data-view]'), function (b) { byView[b.getAttribute('data-view')] = b; });
      var placed = {};
      var groups = NAV.map(function (g, gi) {
        var div = document.createElement('div');
        div.className = 'navgroup';
        div.setAttribute('aria-labelledby', 'navlbl-g' + gi);
        div.innerHTML = '<div class="navlbl" id="navlbl-g' + gi + '">' + g.label + '</div>';
        g.items.forEach(function (k) {
          if (k.charAt(0) === '@') {
            var p = PAGES[k.slice(1)];
            var a = document.createElement('a');
            a.className = 'navlink'; a.href = p.href; a.title = p.title;
            a.innerHTML = '<span class="ni"><svg viewBox="0 0 24 24" aria-hidden="true">' + p.icon + '</svg></span><span class="nl">' + p.label + '</span>';
            div.appendChild(a);
          } else if (byView[k]) { div.appendChild(byView[k]); placed[k] = 1; }
        });
        return div;
      });
      /* Anything the page has that is not named above keeps a place, at the foot of Setup; HIDDEN
         stays out of the nav (the view itself is kept). */
      Object.keys(byView).forEach(function (k) { if (!placed[k] && HIDDEN.indexOf(k) < 0) groups[groups.length - 2].appendChild(byView[k]); });
      nav.innerHTML = '';
      groups.forEach(function (g) { if (g.querySelector('.navlink')) nav.appendChild(g); });
      nav.setAttribute('data-organized', '1');
    } catch (e) { if (window.console) console.error('Nav order:', e); }
  }
  function hideZeroCounts() {
    try {
      var st = document.createElement('style');
      st.textContent = '.navlink .pip.zero{display:none !important} a.navlink{text-decoration:none; box-sizing:border-box} .navlink[data-view="renewals"] .pip, .navlink[data-view="invoices"] .pip{display:none !important}';
      document.head.appendChild(st);
      var pips = document.querySelectorAll('.navlink .pip');
      var paint = function (p) { var t = (p.textContent || '').trim(); p.classList.toggle('zero', t === '' || t === '0'); };
      Array.prototype.forEach.call(pips, function (p) {
        paint(p);
        if (window.MutationObserver) new MutationObserver(function () { paint(p); }).observe(p, { childList: true, characterData: true, subtree: true });
      });
    } catch (e) { if (window.console) console.error('Nav counts:', e); }
  }

  /* ---------- start: sign in, load, hand the page its services, run it ---------- */
  if (!RS || !RS.requireAccess) { fail('The MISMO Resources sign-in did not load. Reload the page.'); return; }
  RS.requireAccess(PROJECT, { toolName: TOOL, eyebrow: 'Programs & Operations' }).then(function () {
    var acct = document.getElementById('rs-account'); if (acct && RS.mount) RS.mount(acct);
    return loadRecords();
  }).then(function (D) {
    document.getElementById('cms-data').textContent = JSON.stringify(D);
    window.claude = { use: function (name) { return Promise.resolve(name === 'db' ? db : name === 'user' ? user : name === 'downloads' ? downloads : null); } };
    var app = document.getElementById('cms-app'), s = document.createElement('script');
    s.textContent = app.textContent; document.body.appendChild(s);
    addSentEmailsTab();
    addEmbedViews();
    organizeNav();
    hideZeroCounts();
    moneySync();
    openFromHash();
    cover.remove();
  }).catch(function (e) {
    if (e && (e.code === 'NO_ACCESS' || e.code === 'SIGNED_OUT')) return;   /* the shared sign-in shows its own screen */
    fail(String((e && e.message) || e));
  });
})();
