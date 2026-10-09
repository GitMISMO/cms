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
  var FILES = { pricing: 'pricing', certScripts: 'cert-scripts', assessorFirms: 'assessor-firms', consultantScorecard: 'consultant-scorecard',
    consultantSubmissions: 'consultant-submissions', applicantForms: 'applicant-forms', individualCerts: 'individual-certifications',
    summits: 'summits', frameResults: 'frame-results', frameScenarios: 'frame-scenarios', frameScoring: 'frame-scoring', frameSources: 'frame-sources' };
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
  function readData(name) {
    return call('GET', '/data/' + name).then(function (r) {
      if (r.status !== 200 || r.json.data == null) throw err('unavailable', 'data/' + name + '.json (' + (r.json.error || r.status) + ')');
      var d = r.json.data; delete d.savedBy; delete d.savedAt; return d;
    });
  }
  function loadRecords() {
    var D = JSON.parse(document.getElementById('cms-data').textContent);
    var jobs = [call('GET', '/file/portal-data.json').then(function (r) {
      if (r.status !== 200 || !r.json.content) throw err('unavailable', 'portal-data.json (' + (r.json.error || r.status) + ')');
      var P = JSON.parse(fromBase64(r.json.content));
      Object.keys(P).forEach(function (k) { D[k] = P[k]; });
    })];
    Object.keys(FILES).forEach(function (k) { jobs.push(readData(FILES[k]).then(function (v) { D[k] = v; })); });
    jobs.push(Promise.all([readData('frame-questionnaire'), readData('emortgage-questionnaires')]).then(function (r) {
      var forms = { FRAME: r[0] }, docs = (r[1] && r[1].docs) || {};
      Object.keys(EMORTGAGE).forEach(function (code) { if (docs[EMORTGAGE[code]]) forms[code] = docs[EMORTGAGE[code]]; });
      D.forms = forms;
    }));
    return Promise.all(jobs).then(function () { D.publicPreview = false; return D; });
  }

  /* ---------- "db": the page's edit collections, one private file each ---------- */
  var COLL = {};
  function coll(name) { return COLL[name] || (COLL[name] = { name: name, docs: {}, sha: null, loaded: null, subs: [], queue: Promise.resolve() }); }
  function fileOf(name) { return 'db-' + String(name).replace(/[^A-Za-z0-9_-]/g, '_'); }
  function fetchColl(c) {
    return call('GET', '/data/' + fileOf(c.name)).then(function (r) {
      if (r.status !== 200) throw err(r.status === 403 ? 'permission_denied' : 'unavailable', r.json.error || String(r.status));
      var d = r.json.data; c.docs = (d && d.docs) || {}; c.sha = r.json.sha || null; return c;
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
  function notify(c) { var s = snapshot(c); c.subs.slice().forEach(function (sub) { try { sub.next(s); } catch (e) { if (window.console) console.error(e); } }); }
  /* one write at a time per collection; on a conflict, re-read and apply the change again on top of what is there */
  function write(name, change) {
    var c = coll(name);
    function attempt(tries) {
      var next = clone(c.docs) || {}; change(next);
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
  /* other people's changes: re-read what this page is watching every minute while it is open and visible */
  setInterval(function () {
    if (document.hidden) return;
    Object.keys(COLL).forEach(function (n) { var c = COLL[n]; if (!c.subs.length) return; var was = c.sha;
      c.queue = c.queue.then(function () { return fetchColl(c).then(function () { if (c.sha !== was) notify(c); }); }).catch(function () {}); });
  }, 60000);
  function docRef(name, id) {
    var c = coll(name);
    return {
      id: id,
      set: function (body) { return write(name, function (d) { d[id] = clone(body); }); },
      replace: function (body) { return write(name, function (d) { d[id] = clone(body); }); },
      update: function (body) { return write(name, function (d) { d[id] = Object.assign({}, d[id] || {}, clone(body)); }); },
      'delete': function () { return write(name, function (d) { delete d[id]; }); },
      get: function () { return load(c).then(function () { var v = c.docs[id]; return { id: id, exists: v !== undefined, data: function () { return clone(v); } }; }); },
      onSnapshot: function (next, error) {
        var sub = { next: function () { var v = c.docs[id]; next({ id: id, exists: v !== undefined, data: function () { return clone(v); } }); } };
        c.subs.push(sub); load(c).then(function () { sub.next(); }, function (e) { if (error) error(e); });
        return function () { c.subs = c.subs.filter(function (x) { return x !== sub; }); };
      }
    };
  }
  function query(name, opts) {
    var c = coll(name);
    return {
      orderBy: function (field, dir) { return query(name, Object.assign({}, opts, { order: [field, dir || 'asc'] })); },
      limit: function (n) { return query(name, Object.assign({}, opts, { limit: n })); },
      get: function () { return load(c).then(function () { return snapshot(c, opts); }); },
      onSnapshot: function (next, error) {
        var sub = { next: function (s) { next(opts.order || opts.limit != null ? snapshot(c, opts) : s); } }; c.subs.push(sub);
        load(c).then(function () { next(snapshot(c, opts)); }, function (e) { if (error) error(e); });
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
    cover.remove();
  }).catch(function (e) {
    if (e && (e.code === 'NO_ACCESS' || e.code === 'SIGNED_OUT')) return;   /* the shared sign-in shows its own screen */
    fail(String((e && e.message) || e));
  });
})();
