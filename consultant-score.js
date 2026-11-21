/* Certified Consultant points scorecard (21 Nov 2026).
   One set of rules, used by the CMS scorecard page; the saved result is what a company sees in its portal.
   The rules are MISMO's Point Structure (the old Smartsheet "Certified Consultant - Point Structure"), less
   "MISMO Work Product" (Jonna, 21 Nov 2026: drop it). Everyone MISMO's systems tie to the company counts,
   plus anyone added by hand, less anyone taken off by hand.
   Sources: Member 360 (membership level, via the CMS's membership record), Elections HQ (leaders), Meeting
   Trackers (workgroup and summit attendance), the CMS (CMSP/AMSP holders, Product certifications) and the
   weekly Aptify report CMS_Consultant_Points_Feed (CMB/AMP designations, MISMO event speakers).
   No names of companies in this file (public repo). */
(function (root) {
  "use strict";

  var CATS = [
    { key: "membership", label: "Membership", window: "year" },
    { key: "leadership", label: "Leadership", window: "active" },
    { key: "participation", label: "Participation", window: "12mo" },
    { key: "mismoEd", label: "MISMO Education / Certification", window: "active" },
    { key: "otherEd", label: "Other Education / Certification", window: "active" },
    { key: "ancillary", label: "Ancillary Points", window: "12mo" }
  ];
  /* minimums: [10 employees and under, 11 employees and over] */
  var MIN = {
    initial: { membership: [1, 1], leadership: [5, 10], participation: [10, 20], mismoEd: [3, 9], otherEd: [0, 0], ancillary: [0, 0] },
    renewal: { membership: [1, 1], leadership: [5, 10], participation: [10, 20], mismoEd: [3, 9], otherEd: [3, 7], ancillary: [3, 7] }
  };
  /* every way to earn points; cat, points, and the plain name shown on the scorecard */
  var ITEMS = {
    member: { cat: "membership", pts: 1, name: "MISMO Member" },
    champAssociate: { cat: "membership", pts: 3, name: "Associate Level Champion" },
    champExecutive: { cat: "membership", pts: 5, name: "Executive Level Champion" },
    champChair: { cat: "membership", pts: 10, name: "Chair Level Champion" },
    board: { cat: "leadership", pts: 10, name: "Board Member" },
    rsgc: { cat: "leadership", pts: 10, name: "RSGC Member" },
    csgc: { cat: "leadership", pts: 10, name: "CSGC Member" },
    chairIM: { cat: "leadership", pts: 10, name: "Chair or Vice Chair - Information Management" },
    chairAWG: { cat: "leadership", pts: 10, name: "Chair or Vice Chair - Architecture Workgroup" },
    chairDWG: { cat: "leadership", pts: 10, name: "Chair or Vice Chair - Development Workgroup" },
    chairCOP: { cat: "leadership", pts: 10, name: "Chair or Vice Chair - Community of Practice" },
    chairEdu: { cat: "leadership", pts: 10, name: "Chair or Vice Chair - Education Council" },
    chairNPI: { cat: "leadership", pts: 10, name: "Chair or Vice Chair - New Product Incubator" },
    repIM: { cat: "leadership", pts: 5, name: "Workgroup IM Representative" },
    repAWG: { cat: "leadership", pts: 5, name: "Workgroup AWG Representative" },
    repEdu: { cat: "leadership", pts: 5, name: "Workgroup Education Council Representative" },
    summit: { cat: "participation", pts: 4, name: "MISMO Summit Attendance" },
    summitPanel: { cat: "participation", pts: 2, name: "Served on a Summit Presentation Panel" },
    workgroup: { cat: "participation", pts: 4, name: "Workgroup Attendance (66% of meetings)" },
    bootcamp: { cat: "participation", pts: 5, name: "MISMO Bootcamp Instructor" },
    cmsp: { cat: "mismoEd", pts: 10, name: "CMSP" },
    amsp: { cat: "mismoEd", pts: 3, name: "AMSP" },
    cmb: { cat: "otherEd", pts: 5, name: "CMB" },
    amp: { cat: "otherEd", pts: 2, name: "AMP" },
    industryPanel: { cat: "ancillary", pts: 2, name: "Served on Industry Panel / Presentation" },
    webinar: { cat: "ancillary", pts: 3, name: "Developed / Participated in a MISMO Webinar" },
    article: { cat: "ancillary", pts: 3, name: "Authored a Published MISMO-Related Industry Article" },
    productCert: { cat: "ancillary", pts: 3, name: "MISMO Product Certification" }
  };
  /* items MISMO can add by hand on the scorecard (things no system holds) */
  var HAND = ["industryPanel", "article", "webinar", "summitPanel", "bootcamp", "summit", "workgroup", "cmb", "amp", "board", "rsgc", "csgc",
    "chairIM", "chairAWG", "chairDWG", "chairCOP", "chairEdu", "chairNPI", "repIM", "repAWG", "repEdu"];

  var SUFFIX = /\b(llc|l l c|inc|incorporated|llp|lp|corp|corporation|co|company|ltd|limited|plc|pllc|pc|the|na|n a|usa|us)\b/g;
  function normCo(s) {
    return String(s || "").toLowerCase().replace(/&/g, " and ").replace(/\([^)]*\)/g, " ").replace(/[^a-z0-9 ]+/g, " ")
      .replace(SUFFIX, " ").replace(/\s+/g, " ").trim();
  }
  function personKey(name) { return String(name || "").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z]/g, ""); }
  function day(v) { if (!v) return null; var s = String(v).slice(0, 10); return /^\d{4}-\d{2}-\d{2}$/.test(s) ? s : null; }
  function minusMonths(iso, n) { var d = new Date(iso + "T12:00:00Z"); d.setUTCMonth(d.getUTCMonth() - n); return d.toISOString().slice(0, 10); }

  /* does this company name belong to the org? */
  function coMatcher(org) {
    var names = {};
    [org.name, org.legalName, org.aptifyName].concat(org.spellings || []).forEach(function (n) { var k = normCo(n); if (k) { names[k] = 1; names[k.replace(/ /g, "")] = 1; } });
    var id = org.aptify ? String(org.aptify).replace(/^c/, "") : null;
    return function (company, companyId) {
      if (id && companyId != null && String(companyId).replace(/^c/, "") === id) return true;
      var k = normCo(company);
      return !!k && (names[k] || names[k.replace(/ /g, "")]) ? true : false;
    };
  }

  function leaderItem(l) {
    var pos = String(l.position || ""), g = String(l.group || "") + " " + String(l.formerGroup || ""), t = String(l.gtype || "");
    if (t === "board") return /president/i.test(pos) ? null : "board";
    if (/residential standards governance/i.test(g)) return "rsgc";
    if (/commercial standards governance/i.test(g)) return "csgc";
    if (/^IM Rep/i.test(pos)) return "repIM";
    if (/^AWG Rep/i.test(pos)) return "repAWG";
    if (/^Education Rep/i.test(pos)) return "repEdu";
    if (!/chair/i.test(pos)) return null;
    if (/information management/i.test(g)) return "chairIM";
    if (/architecture/i.test(g)) return "chairAWG";
    if (/education council/i.test(g)) return "chairEdu";
    if (/incubator/i.test(g)) return "chairNPI";
    if (t === "aof" || /\bcop\b|community of practice/i.test(g)) return "chairCOP";
    return "chairDWG";
  }
  function activeOn(l, asOf) {
    if (String(l.status || "active") !== "active" && !(l.termEnd && l.termEnd >= asOf)) return false;
    if (l.termStart && day(l.termStart) && day(l.termStart) > asOf) return false;
    if (l.termEnd && day(l.termEnd) && day(l.termEnd) < asOf && String(l.status) !== "active") return false;
    return true;
  }

  /* src: { membership: {level, member} | null,
            leaders: [Elections HQ leader docs],
            indPeople: {id: person}, indCycles: {id: cycle},
            aptify: [rows of the Aptify report],
            certs: [CMS certifications],
            meetings: { groups: {gk: {name}}, byGroup: {gk: [{d, cancelled, p: [personKeys]}]}, people: {key: {name, ck}}, companies: {ck: {name}} } | null,
            feed: Meeting Trackers feeds/cert-points | null }
     o: { org, kind: "initial"|"renewal", asOf: "YYYY-MM-DD", size: "small"|"large", edits: {add:[names], remove:[names], items:[...]} } */
  function score(o, src) {
    var org = o.org, asOf = o.asOf, from12 = minusMonths(asOf, 12), kind = o.kind === "renewal" ? "renewal" : "initial";
    var isOurs = coMatcher(org), edits = o.edits || {}, removed = {}, added = {};
    (edits.remove || []).forEach(function (n) { removed[personKey(n)] = 1; });
    (edits.add || []).forEach(function (n) { if (personKey(n)) added[personKey(n)] = n; });
    var people = {}, items = [], notes = [];
    function person(name, how) {
      var k = personKey(name); if (!k || removed[k]) return null;
      var p = people[k] || (people[k] = { key: k, name: name, how: {}, points: 0 });
      if (how) p.how[how] = 1;
      return p;
    }
    function add(code, who, detail, sourceName, extra) {
      var it = ITEMS[code]; if (!it) return;
      var row = { code: code, cat: it.cat, name: it.name, pts: it.pts, person: who ? who.name : null, detail: detail || "", source: sourceName };
      if (extra) for (var k in extra) row[k] = extra[k];
      if (who) who.points += it.pts;
      items.push(row);
    }
    Object.keys(added).forEach(function (k) { person(added[k], "Added by MISMO"); });

    /* Membership (current year) */
    var m = src.membership;
    if (m && m.member) {
      add("member", null, m.label || "", "Member 360");
      var lv = String(m.level || "");
      if (/^associate/i.test(lv)) add("champAssociate", null, lv, "Member 360");
      if (/^executive/i.test(lv)) add("champExecutive", null, lv, "Member 360");
      if (/^chair/i.test(lv)) add("champChair", null, lv, "Member 360");
    }

    /* Leadership (active on the date): who leads what, by company */
    var leadsGroup = {};
    (src.leaders || []).forEach(function (l) {
      if (!l || !l.name) return;
      var mine = isOurs(l.company) || !!added[personKey(l.name)];
      if (!mine || !activeOn(l, asOf)) return;
      var code = leaderItem(l); if (!code) return;
      var who = person(l.name, "Elections HQ"); if (!who) return;
      if (/chair/i.test(String(l.position || ""))) { [l.group, l.formerGroup].forEach(function (g) { if (g) (leadsGroup[who.key] = leadsGroup[who.key] || {})[normCo(g)] = 1; }); }
      add(code, who, (l.position || "") + ", " + (l.group || ""), "Elections HQ");
    });

    /* CMSP / AMSP holders on the date (the CMS's own records) */
    var held = {};
    Object.keys(src.indCycles || {}).forEach(function (id) {
      var c = src.indCycles[id]; if (!c || !c.person || !c.certDate) return;
      var cd = day(c.certDate), ex = day(c.expiry);
      if (!cd || cd > asOf || (ex && ex < asOf)) return;
      (held[c.person] = held[c.person] || {})[c.program] = 1;
    });
    Object.keys(src.indPeople || {}).forEach(function (pid) {
      var p = src.indPeople[pid]; if (!p || !held[pid]) return;
      var nm = ((p.first || "") + " " + (p.last || "")).trim();
      if (!isOurs(p.company) && !added[personKey(nm)]) return;
      var who = person(nm, "CMS (CMSP/AMSP)"); if (!who) return;
      if (held[pid].CMSP) add("cmsp", who, "Active " + "CMSP", "CMS");
      else if (held[pid].AMSP) add("amsp", who, "Active AMSP", "CMS");
    });

    /* Aptify: CMB / AMP designations (people at the company now), MISMO event speakers (last 12 months) */
    var seenDes = {};
    (src.aptify || []).forEach(function (r) {
      var nm = ((r.FirstName || "") + " " + (r.LastName || "")).trim();
      if (!nm || (!isOurs(r.Company, r.CompanyID) && !added[personKey(nm)])) return;
      if (r.Kind === "designation") {
        var des = String(r.Detail || "").toUpperCase().split(/[^A-Z]+/);
        var who = person(nm, "Aptify"); if (!who || seenDes[who.key]) return; seenDes[who.key] = 1;
        if (des.indexOf("CMB") >= 0) add("cmb", who, "CMB designation", "Aptify");
        if (des.indexOf("AMP") >= 0) add("amp", who, "AMP designation", "Aptify");
      } else if (r.Kind === "speaker") {
        var d = day(r.EventDate); if (!d || d < from12 || d > asOf) return;
        var t = String(r.EventType || "").trim(), title = String(r.Detail || "");
        var code = /boot\s*camp/i.test(title) ? "bootcamp" : /webinar/i.test(t) ? "webinar" : /session/i.test(t) ? "summitPanel" : "industryPanel";
        var w = person(nm, "Aptify"); if (!w) return;
        add(code, w, title + " (" + d + ")", "Aptify", { date: d });
      }
    });

    /* Meeting Trackers: workgroup attendance (66% of meetings held in the 12 months) and summits attended */
    var mt = src.meetings, feed = src.feed;
    var mtCompanyOf = {};
    if (feed && feed.people) {
      Object.keys(feed.people).forEach(function (k) { var p = feed.people[k]; mtCompanyOf[k] = { name: p.name, company: p.company, companyId: p.aptifyId }; });
    } else if (mt && mt.people) {
      Object.keys(mt.people).forEach(function (k) { var p = mt.people[k]; if (p && !p.mergedInto) mtCompanyOf[k] = { name: p.name, company: (mt.companies[p.ck] || {}).name || "", ck: p.ck }; });
    }
    function mtMine(k) {
      if (people[k]) return people[k];
      var c = mtCompanyOf[k]; if (!c) return null;
      if (!isOurs(c.company, c.companyId)) return null;
      return person(c.name, "Meeting Trackers");
    }
    if (feed && feed.people) {
      Object.keys(feed.people).forEach(function (k) {
        var p = feed.people[k], who = mtMine(personKey(p.name) || k); if (!who) return;
        Object.keys(p.groups || {}).forEach(function (gk) {
          var g = p.groups[gk], held = 0, came = 0;
          Object.keys(g.months || {}).forEach(function (mo) { var dd = mo + "-15"; if (dd >= from12 && dd <= asOf) { held += +g.months[mo].held || 0; came += +g.months[mo].attended || 0; } });
          if (held && came / held >= 0.66 && !((leadsGroup[who.key] || {})[normCo(g.name)])) add("workgroup", who, g.name + ": " + came + " of " + held + " meetings", "Meeting Trackers");
        });
        (p.summits || []).forEach(function (s) { var dd = day(s.date); if (dd && dd >= from12 && dd <= asOf) add("summit", who, s.name, "Meeting Trackers", { date: dd }); });
      });
    } else if (mt && mt.byGroup) {
      Object.keys(mt.byGroup).forEach(function (gk) {
        var list = mt.byGroup[gk].filter(function (x) { return x && !x.cancelled && x.d >= from12 && x.d <= asOf; });
        if (!list.length) return;
        var count = {};
        list.forEach(function (x) { (x.p || []).forEach(function (k) { count[k] = (count[k] || 0) + 1; }); });
        var gname = (mt.groups[gk] || {}).name || gk;
        Object.keys(count).forEach(function (k) {
          if (count[k] / list.length < 0.66) return;
          var who = mtMine(k); if (!who) return;
          if ((leadsGroup[who.key] || {})[normCo(gname)]) return;
          add("workgroup", who, gname + ": " + count[k] + " of " + list.length + " meetings", "Meeting Trackers");
        });
      });
      notes.push("Summit attendance comes in once Meeting Trackers shares its attendance list with the CMS.");
    }

    /* Product certifications the company holds (active on the date) */
    (src.certs || []).forEach(function (c) {
      if (!c || c.program !== "Product" || !isOurs(c.org)) return;
      var since = day(c.originalCertifiedOn) || "0000";
      if (since > asOf || (c.status && !/active/i.test(c.status) && c.live === false)) return;
      add("productCert", null, c.product || "Product", "CMS");
    });

    /* added by hand on the scorecard */
    (edits.items || []).forEach(function (h) {
      if (!h || !ITEMS[h.code]) return;
      var d = day(h.date);
      if (ITEMS[h.code].cat === "participation" || ITEMS[h.code].cat === "ancillary") { if (d && (d < from12 || d > asOf)) return; }
      var who = h.person ? person(h.person, "Added by MISMO") : null;
      add(h.code, who, h.detail || "", "Added by MISMO" + (h.by ? " (" + h.by + ")" : ""), { date: d, hand: h.id || null });
    });

    var size = o.size === "small" ? 0 : 1, mins = MIN[kind], cats = {}, total = 0, allMet = true;
    CATS.forEach(function (c) {
      var pts = items.filter(function (i) { return i.cat === c.key; }).reduce(function (s, i) { return s + i.pts; }, 0);
      var min = mins[c.key][size], met = pts >= min;
      cats[c.key] = { label: c.label, points: pts, min: min, met: met };
      total += pts; if (!met) allMet = false;
    });
    var list = Object.keys(people).map(function (k) { var p = people[k]; return { name: p.name, points: p.points, how: Object.keys(p.how) }; })
      .sort(function (a, b) { return b.points - a.points || a.name.localeCompare(b.name); });
    return { org: org.name, kind: kind, asOf: asOf, from: from12, size: o.size === "small" ? "small" : "large", total: total, meetsAll: allMet,
      categories: cats, people: list, items: items, notes: notes };
  }

  var api = { CATS: CATS, MIN: MIN, ITEMS: ITEMS, HAND: HAND, score: score, normCo: normCo, personKey: personKey, coMatcher: coMatcher };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.ConsultantScore = api;
})(this);
