"""Saving never undoes what someone else saved in the meantime (November 5, 2026).

relay-connect.js now writes only what a save actually changed, merged into the newest copy of the
record (see its "saving without overwriting anyone" section). This patch adds the page's half:

1. The invoice fields in the record panel are held as a draft from the first keystroke, all five
   of them (order, invoice date, amount, paid, paid on), and could sit half-edited for hours.
   Saving wrote all five as they were when typing began, so a payment someone else recorded in
   the meantime went back to unpaid. Now only the fields changed in the draft are saved; the rest
   keep what the invoice says now.
2. Company details and the website card: if someone else changed the same field after the person
   started typing in it, they are asked which to keep (OK keeps what they typed, Cancel keeps the
   other person's value for those fields; their other changes still save).
3. The page names the records its panel is showing (window.__cmsPanelDocs), so relay-connect.js
   can say in the panel when someone else saves one of them.

Applied by export-from-artifact.py; every anchor must be found exactly once.
"""

NAME = "Saving keeps what others saved meanwhile"

FIXES = [
    # 1. somewhere to keep what a field said when typing in it began, and the question to ask
    ('''    var invEdit = {};''',
     '''    var invEdit = {};
    /* November 5, 2026: what an invoice, company or website field said when someone began editing
       it, so a save can keep what others saved in the meantime and ask when both changed the same field */
    var invFrom = {}, draftFrom = {};
    function sameDraft(x, y) { return String(x == null ? "" : x).trim() === String(y == null ? "" : y).trim(); }
    function dropDraftFrom(prefix) { Object.keys(draftFrom).forEach((function(k) { if (k.indexOf(prefix) === 0) delete draftFrom[k]; })); }
    function askDraftClash(who, list) {
        if (!list.length) return true;
        var show = function(v) { v = v === true ? "Yes" : v === false ? "No" : String(v == null ? "" : v).trim(); return v === "" ? "(blank)" : v.length > 80 ? v.slice(0, 80) + "\\u2026" : v; };
        return window.confirm("While you had " + who + " open, someone else saved a different value in the same " + (list.length === 1 ? "field" : "fields") + ":\\n\\n" +
            list.map((function(x) { return "\\u2022 " + x.label + " \\u2014 theirs: " + show(x.theirs) + "   \\u00b7   yours: " + show(x.mine); })).join("\\n") +
            "\\n\\nOK keeps yours. Cancel keeps theirs for " + (list.length === 1 ? "this field" : "these fields") + " \\u2014 your other changes still save.");
    }'''),
    # 1. the invoice draft remembers where it started
    ('''                var d = invEdit[row] || (invEdit[row] = invoiceDraft(byRow(row) || {
                    row: row
                }));''',
     '''                var d = invEdit[row];
                if (!d) {
                    d = invEdit[row] = invoiceDraft(byRow(row) || {
                        row: row
                    });
                    invFrom[row] = { draft: d, from: clone(d) };
                }'''),
    # 1. ...and saving takes only what was changed in it
    ('''    function saveInvoice(row) {
        var d = invEdit[row];
        if (!d) return;
        var f = byRow(row) || {
            row: row,
            org: "",
            program: ""
        };''',
     '''    function saveInvoice(row) {
        var d = invEdit[row];
        if (!d) return;
        var f = byRow(row) || {
            row: row,
            org: "",
            program: ""
        };
        /* November 5, 2026: a field not changed in the draft keeps what the invoice says now, so a
           payment someone else recorded while this sat open is not undone */
        var fr = invFrom[row];
        delete invFrom[row];
        if (fr && fr.draft === d) {
            var i0 = invoiceOf(f) || {}, both = [];
            var now = { orderId: i0.orderId || "", invoicedOn: i0.invoicedOn || "", amount: i0.amount != null ? String(i0.amount) : "", paid: !!i0.paid, paidOn: i0.paidOn || "" };
            var INV_LAB = { orderId: "Order ID", invoicedOn: "Invoiced On", amount: "Amount", paid: "Paid", paidOn: "Paid On" };
            Object.keys(now).forEach((function(k) {
                if (sameDraft(d[k], fr.from[k])) d[k] = now[k];
                else if (!sameDraft(now[k], fr.from[k]) && !sameDraft(now[k], d[k])) both.push({ k: k, label: INV_LAB[k], theirs: now[k], mine: d[k] });
            }));
            if (!askDraftClash("the invoice for " + (f.org || "this certification"), both)) both.forEach((function(x) { d[x.k] = now[x.k]; }));
        }'''),
    # 2. company details: where each field started
    ('''                (orgDraft[slug] = orgDraft[slug] || {})[i.dataset.of] = i.value;''',
     '''                if (draftFrom["org:" + slug + ":" + i.dataset.of] === undefined) {
                    var o0 = orgOf((ORG_BY_SLUG[slug] || {}).name || (orgEdits[slug] || {}).org || slug);
                    draftFrom["org:" + slug + ":" + i.dataset.of] = o0[i.dataset.of] == null ? "" : String(o0[i.dataset.of]);
                }
                (orgDraft[slug] = orgDraft[slug] || {})[i.dataset.of] = i.value;'''),
    ('''        var patch = {}, changed = [];
        ORG_FIELDS.forEach((function(f) {
            if (d[f.k] === undefined) return;
            var v = String(d[f.k]).trim();
            var was = o[f.k] == null ? "" : String(o[f.k]);
            if (v === was) return;
            patch[f.k] = v || null;
            changed.push(f.lab.toLowerCase());
        }));
        delete orgDraft[slug];''',
     '''        var patch = {}, changed = [], both = [];
        ORG_FIELDS.forEach((function(f) {
            if (d[f.k] === undefined) return;
            var v = String(d[f.k]).trim();
            var was = o[f.k] == null ? "" : String(o[f.k]);
            if (v === was) return;
            var from = draftFrom["org:" + slug + ":" + f.k];
            if (from !== undefined && !sameDraft(from, was)) both.push({ k: f.k, label: f.lab, theirs: was, mine: v });
            patch[f.k] = v || null;
            changed.push(f.lab.toLowerCase());
        }));
        /* November 5, 2026: someone else changed a field typed in here: ask whose to keep */
        if (!askDraftClash(o.name || "this company", both)) both.forEach((function(x) {
            delete patch[x.k];
            changed.splice(changed.indexOf(x.label.toLowerCase()), 1);
        }));
        dropDraftFrom("org:" + slug + ":");
        delete orgDraft[slug];'''),
    ('''                delete orgDraft[b.dataset.ocancel];''',
     '''                delete orgDraft[b.dataset.ocancel];
                dropDraftFrom("org:" + b.dataset.ocancel + ":");'''),
    # 2. the website card, the same way
    ('''                (webDraft[key] = webDraft[key] || {})[i.dataset.wf] = i.value;''',
     '''                if (draftFrom["web:" + key + ":" + i.dataset.wf] === undefined) {
                    var c0 = webCertOf(key) || {}, e0 = (certEdits[key] || {}).website || {}, k0 = i.dataset.wf;
                    draftFrom["web:" + key + ":" + k0] = e0[k0] !== undefined ? e0[k0] : (c0.website || {})[k0] == null ? "" : (c0.website || {})[k0];
                }
                (webDraft[key] = webDraft[key] || {})[i.dataset.wf] = i.value;'''),
    ('''        for (var j in d) next[j] = String(d[j]).trim() || null;''',
     '''        /* November 5, 2026: a field someone else changed after typing began here: ask whose to keep */
        var wboth = [];
        for (var wj in d) {
            var wnow = cur[wj] !== undefined ? cur[wj] : (c.website || {})[wj], wfrom = draftFrom["web:" + key + ":" + wj];
            if (wfrom !== undefined && !sameDraft(wnow, wfrom) && !sameDraft(wnow, d[wj])) wboth.push({ k: wj, label: wj.replace(/([a-z])([A-Z])/g, "$1 $2").replace(/^./, (function(x) { return x.toUpperCase(); })), theirs: wnow, mine: d[wj] });
        }
        if (!askDraftClash("the website card for " + (c.org || "this certification"), wboth)) wboth.forEach((function(x) { delete d[x.k]; }));
        dropDraftFrom("web:" + key + ":");
        for (var j in d) next[j] = String(d[j]).trim() || null;'''),
    ('''                delete webDraft[b.dataset.wcancel];''',
     '''                delete webDraft[b.dataset.wcancel];
                dropDraftFrom("web:" + b.dataset.wcancel + ":");'''),
    # 3. the records the open panel shows
    ('''    function closePanel() {
        panel = null;''',
     '''    /* November 5, 2026: the saved records the open panel is showing, as collection/id, so
       relay-connect.js can say in the panel when someone else saves one of them */
    window.__cmsPanelDocs = function() {
        if (!panel || [ "record", "full", "org" ].indexOf(panel.mode) < 0) return [];
        var out = [], f = panel.row != null ? byRow(panel.row) : null;
        var safe = function(s) { return String(s).replace(/[^A-Za-z0-9_.~-]/g, "_"); };
        if (panel.row != null) [ "cycle-state", "invoices", "applications", "assessments", "script-prep", "scenario-log", "follow-ups" ].forEach((function(n) { out.push(n + "/" + panel.row); }));
        var key = panel.key || (f ? certKey(f) : null);
        if (key) [ "cert-edits", "renewal-quotes", "mark-license" ].forEach((function(n) { out.push(n + "/" + safe(key)); }));
        var org = panel.mode === "org" ? panel.name : f ? f.org : key ? String(key).split("|")[0] : null;
        if (org) out.push("org-edits/" + orgSlug(org));
        return out;
    };
    function closePanel() {
        panel = null;'''),
]


def apply(s):
    if "window.__cmsPanelDocs" in s:
        return s
    for old, new in FIXES:
        n = s.count(old)
        if n != 1:
            raise SystemExit("export failed: merge-saves anchor found %d times: %r" % (n, old[:80]))
        s = s.replace(old, new)
    return s
