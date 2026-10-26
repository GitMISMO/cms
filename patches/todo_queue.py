"""The Action Queue as one to-do list, and Prospects (Jonna, 26 Oct 2026).

Jonna found the queue hard to follow: thirteen cards counted every open cycle, most of them
waiting on somebody else, and the invoice drop was two clicks deep in Renewals. She also needed
a way to stop chasing a company that is not going ahead (FAST) without losing it.

The page now opens on "Your To-Do": only the things that need MISMO, grouped by what to do, each
with the one button that does it. The invoice is dropped straight onto its line.

  Raise the Invoice              renewals whose quotation is due within 14 days (or late) and has
                                 no Aptify order yet: drop the PDF, type the order number, done
  Mark License Needs an Email    approved, ready to go, no signer email on file
  Assign an Assessor             open cycles with no assessor
  Send the Welcome Email         paid, and nobody has told them how to book the demo
  Certification Script           a script still to prepare
  Expire or Keep?                past the anniversary, no renewal opened, not on hold
  Record the Next Step           the move is MISMO's and nothing above covers it
  Follow Up Today                stuck, and the chase-again date has come

Everything else is folded under "Waiting on Others" (with the company, the assessor, Jonathan,
the system, follow up later, on hold), and companies not going through certification are under
"Prospects". "Move to Prospects" (on a follow-up line, and on a cycle's own panel) closes the
company's open cycles as Application Expired and sets the company to prospect, through the
existing org-edits collection; "Start Application" opens New Application for them, and saving it
makes them active again. Closed cycles and prospects are also kept off the phase board, which is
how FAST was still showing.

The numbers tiles, the phase board and the Certification Scripts reference are folded at the
foot of the page. Applied by export-from-artifact.py after follow_up_card.py; every anchor must
be found exactly once, or the build stops.
"""

NAME = "Action Queue as a to-do list, with Prospects"

CSS = r'''
  /* ---- Action Queue to-do list (26 Oct 2026): see patches/todo_queue.py ---- */
  .td-head{display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; margin:0 0 14px;}
  .td-head .td-n{font-size:30px; font-weight:700; color:var(--ink); line-height:1; font-variant-numeric:tabular-nums;}
  .td-head .td-say{color:var(--ink-2); font-size:14px;}
  .td-group{border:1px solid var(--border); border-radius:9px; background:var(--surface); margin-bottom:14px; overflow:hidden;}
  .td-ghead{display:flex; align-items:center; gap:10px; flex-wrap:wrap; padding:11px 16px; background:var(--surface-2); border-bottom:1px solid var(--border);}
  .td-ghead h3{font-size:14px; margin:0;}
  .td-ghead .td-c{font-size:11px; background:var(--chip); color:var(--ink-2); border-radius:20px; padding:1px 8px; font-weight:600;}
  .td-ghead .td-help{font-size:12px; color:var(--ink-3); flex:1 1 260px;}
  .td-item{display:flex; gap:10px 16px; align-items:center; justify-content:space-between; flex-wrap:wrap; padding:12px 16px; border-top:1px solid var(--border);}
  .td-group .td-item:first-of-type{border-top:none;}
  .td-item.bad{box-shadow:inset 3px 0 0 var(--bad);}
  .td-main{flex:1 1 240px; min-width:0;}
  .td-org{background:none; border:none; padding:0; font:inherit; font-weight:600; font-size:14px; color:var(--ink); cursor:pointer; text-align:left;}
  .td-org:hover{text-decoration:underline;}
  .td-meta{font-size:12.5px; color:var(--ink-2); margin-top:2px; line-height:1.45;}
  .td-meta .bad, .td-warn{color:var(--bad);}
  .td-warn{font-size:12px; margin-top:4px;}
  .td-acts{display:flex; gap:8px; flex-wrap:wrap; align-items:center;}
  .td-acts .lc-btn{white-space:nowrap;}
  .td-inv{display:flex; gap:8px; flex-wrap:wrap; align-items:center; flex:1 1 420px; justify-content:flex-end;}
  .td-drop{border:1.5px dashed var(--border-strong); border-radius:7px; padding:7px 10px; font-size:12.5px; color:var(--ink-3); display:flex; align-items:center; gap:10px; min-height:36px;}
  .td-drop.over{border-color:var(--navy-mid); background:var(--sky-wash); color:var(--ink);}
  .td-drop.have{border-style:solid; color:var(--ink-2);}
  .td-drop.have b{color:var(--good);}
  .td-num{width:170px !important; padding:7px 9px !important;}
  .td-lic{flex:1 1 100%;}
  .td-lic .lic-send{margin-top:4px;}
  .td-sel{width:auto !important; padding:6px 9px !important;}
  .td-clear{border:1px dashed var(--border); border-radius:9px; padding:22px; text-align:center; color:var(--ink-2); font-size:14px; margin-bottom:14px;}
  .td-fold{border:1px solid var(--border); border-radius:9px; margin-bottom:14px; background:var(--surface);}
  .td-fold>summary{cursor:pointer; padding:12px 16px; font-weight:600; font-size:14px; list-style:none; display:flex; gap:8px 10px; align-items:center; flex-wrap:wrap;}
  .td-fold>summary::-webkit-details-marker{display:none;}
  .td-fold>summary:before{content:"\25B8"; color:var(--ink-3); display:inline-block; transition:transform .15s;}
  .td-fold[open]>summary:before{transform:rotate(90deg);}
  .td-chip{font-size:11.5px; font-weight:500; color:var(--ink-2); background:var(--chip); border-radius:20px; padding:2px 9px;}
  .td-fbody{padding:0 16px 12px;}
  .td-fbody h4{font-size:11.5px; letter-spacing:.07em; text-transform:uppercase; color:var(--ink-3); margin:14px 0 2px;}
  .td-fbody .td-bn{font-size:12px; color:var(--ink-3); margin:0 0 4px;}
  .td-row{display:flex; gap:4px 12px; align-items:baseline; flex-wrap:wrap; width:100%; text-align:left; background:none; border:none; border-top:1px solid var(--border); padding:8px 0; font:inherit; color:var(--ink); cursor:pointer;}
  .td-row:hover .td-rn{text-decoration:underline;}
  .td-rn{font-weight:600; font-size:13.5px;}
  .td-rm{font-size:12.5px; color:var(--ink-2);}
  .td-prow{display:flex; gap:8px 14px; align-items:center; justify-content:space-between; flex-wrap:wrap; border-top:1px solid var(--border); padding:9px 0;}
  .td-more{margin-top:26px; border-top:1px solid var(--border); padding-top:6px;}
  .td-more>summary{cursor:pointer; color:var(--ink-3); font-size:12.5px; padding:8px 0;}
  .td-more[open]>summary{margin-bottom:14px;}
'''

MODULE = r'''
    /* ---- Action Queue to-do list and Prospects (26 Oct 2026): see patches/todo_queue.py ---- */
    var TD_INV_AHEAD = 14;
    var TD_JONATHAN = [ "PrelimResultsSubmitted", "RemediationSubmitted", "ReviewScheduled", "ScopeReviewVp", "AppealOpen" ];
    var TD_SYSTEM = [ "RenewalPrep", "ApprovedPendingLicense" ];
    var tdFold = { waiting: false, prospects: false };
    var tdPending = false;
    function tdOrgStatus(name) {
        var e = orgEdits[orgSlug(name)] || {};
        if (e.status) return e.status;
        var b = ORG_BY_SLUG[orgSlug(name)];
        return b && b.status || "active";
    }
    function tdProspect(name) { return tdOrgStatus(name) === "prospect"; }
    function tdOpen(f) { return !fuClosed(f) && !tdProspect(f.org); }
    function tdEffOrg(o) {
        var e = orgEdits[orgSlug(o.name)] || {};
        if (!e.status || e.status === o.status) return o;
        var out = {};
        for (var k in o) out[k] = o[k];
        out.status = e.status;
        return out;
    }
    function tdDays(f) { var d = fuDaysInState(f); return d == null ? "" : d <= 0 ? "moved today" : d === 1 ? "1 day" : d + " days"; }
    function tdWhat(f) {
        return esc(f.program) + (f.product ? " · " + esc(f.product) : "") + " · " + esc(kindLabel(f).toLowerCase());
    }
    function tdModel() {
        var todo = { invoice: [], license: [], assessor: [], welcome: [], script: [], expiry: [], record: [], followup: [] };
        var wait = { company: [], assessor: [], jonathan: [], system: [], later: [], hold: [] };
        if (!certs || typeof QUOTE_LEAD !== "number" || typeof LIC_SAID !== "object") return { todo: todo, wait: wait, prospects: [] };
        var taken = {};
        renewalRows().forEach((function(r) {
            if (r.hold || quoteRaised(r.quote) || r.invoice || r.dueIn == null || r.dueIn > TD_INV_AHEAD || r.dueIn <= -365) return;
            if (tdProspect(r.cert.org)) return;
            todo.invoice.push(r);
        }));
        Object.keys(licenses || {}).forEach((function(k) {
            var L = licenses[k];
            if (!L || L.status !== "needs_contact") return;
            var c = certs.filter((function(x) { return certKey(x) === k; }))[0];
            if (!c || tdProspect(c.org)) return;
            var f = openCycleFor(k);
            if (f) taken[f.row] = 1;
            todo.license.push({ c: c, f: f });
        }));
        var seen = {};
        (D.inFlight || []).forEach((function(f) {
            if (seen[f.row] || taken[f.row]) return;
            seen[f.row] = 1;
            if (!tdOpen(f)) return;
            if (fuHeld(f)) { wait.hold.push(f); return; }
            var st = currentState(f), c = certFor(f);
            if (welcomeDue(f)) { todo.welcome.push(f); return; }
            var x = followUpOf(f);
            if (x) { (fuDue(x) ? todo.followup : wait.later).push(f); return; }
            if (scriptOutstanding(f)) { todo.script.push(f); return; }
            if (!(c && c.assessor) && !f.assessor) { todo.assessor.push(f); return; }
            if (TD_JONATHAN.indexOf(st) >= 0) { wait.jonathan.push(f); return; }
            if (TD_SYSTEM.indexOf(st) >= 0) { wait.system.push(f); return; }
            var w = String((STATE[st] || {}).waiting || f.waiting || "");
            if (/assessor/i.test(w)) wait.assessor.push(f);
            else if (/company/i.test(w)) wait.company.push(f);
            else todo.record.push(f);
        }));
        (live || []).forEach((function(c) {
            if (c.condition !== "PastDue" || holdOf(c) || tdProspect(c.org)) return;
            if (openCycleFor(certKey(c))) return;
            todo.expiry.push(c);
        }));
        var pros = {};
        (D.organizations || []).forEach((function(o) { if (tdOrgStatus(o.name) === "prospect") pros[orgSlug(o.name)] = o.name; }));
        Object.keys(orgEdits || {}).forEach((function(s) { var e = orgEdits[s]; if (e && e.status === "prospect" && !pros[s]) pros[s] = e.org || s; }));
        var prospects = Object.keys(pros).map((function(s) { return pros[s]; })).sort((function(a, b) { return a.localeCompare(b); }));
        return { todo: todo, wait: wait, prospects: prospects };
    }
    function todoCount() {
        var m = tdModel(), n = 0;
        Object.keys(m.todo).forEach((function(k) { n += m.todo[k].length; }));
        return n;
    }
    var TD_GROUPS = [
        [ "invoice", "Raise the Invoice", "Drop the Aptify invoice PDF on the line, type the order number, and Mark as Sent. The renewal page offers it to the company from then on." ],
        [ "license", "Mark License Needs an Email", "Approved and ready to go, but there is no signer email on file. Add it and the agreement goes out through DocuSign." ],
        [ "assessor", "Assign an Assessor", "Nobody is assigned, so nothing can be sent to an assessor yet." ],
        [ "welcome", "Send the Welcome Email", "They have paid and have not been told how to book the demonstration." ],
        [ "script", "Certification Script", "The script still has to be prepared before the demonstration." ],
        [ "expiry", "Expire or Keep?", "Past the anniversary with no renewal opened. Open the record to raise the renewal or let it expire." ],
        [ "record", "Record the Next Step", "The move is MISMO's. Open it and record what happens next." ],
        [ "followup", "Follow Up Today", "Stuck, and the chase-again date has come. Note what you did and pick the next date, or move them to Prospects if they are not going ahead." ]
    ];
    function tdItem(key, inner, acts, bad) {
        return '<div class="td-item' + (bad ? " bad" : "") + '">' + inner + (acts ? '<div class="td-acts">' + acts + "</div>" : "") + "</div>";
    }
    function tdBtn(label, attr, ghost) {
        return '<button class="lc-btn' + (ghost ? " ghost" : "") + '" type="button" ' + attr + ">" + esc(label) + "</button>";
    }
    function tdRowLine(key, x) {
        if (key === "invoice") {
            var r = x, c = r.cert, k = esc(r.key);
            var when = r.dueIn < 0 ? '<span class="bad">' + -r.dueIn + (r.dueIn === -1 ? " day" : " days") + " late</span>" : r.dueIn === 0 ? '<span class="bad">due today</span>' : "due in " + r.dueIn + (r.dueIn === 1 ? " day" : " days");
            var main = '<div class="td-main"><button class="td-org" type="button" data-tdrenewal="' + k + '">' + esc(c.org) + "</button>"
                + '<div class="td-meta">' + esc(c.program) + (c.product ? " · " + esc(c.product) : "") + " renewal · quotation by " + esc(fmt(r.quoteBy)) + " (" + when + ")"
                + (r.expected != null ? " · " + esc(money(r.expected)) : "") + (r.aptify ? " · Aptify customer " + esc(r.aptify) : "") + "</div>"
                + (r.blockers.length ? '<div class="td-warn">' + r.blockers.map(esc).join(" ") + "</div>" : "") + "</div>";
            var inv = canWrite ? '<div class="td-inv">'
                + '<div class="td-drop" data-tdinv="' + k + '"><span class="td-dz">Drop the invoice PDF here</span>'
                + '<button class="lc-btn ghost tiny" type="button" data-tdpick="' + k + '">Choose a File</button>'
                + '<input type="file" accept="application/pdf,.pdf" hidden data-tdfile="' + k + '"></div>'
                + '<input class="pc-input td-num" data-tdnum="' + k + '" placeholder="Aptify order number" aria-label="Aptify order number for ' + esc(c.org) + '">'
                + tdBtn("Mark as Sent", 'data-tdsent="' + k + '"') + "</div>" : '<span class="na-hint">Sign in to record an invoice.</span>';
            return '<div class="td-item' + (r.dueIn < 0 ? " bad" : "") + '">' + main + inv + "</div>";
        }
        if (key === "license") {
            var lc = x.c;
            return '<div class="td-item">' + '<div class="td-main"><button class="td-org" type="button" data-tdcert="' + esc(certKey(lc)) + '">' + esc(lc.org) + "</button>"
                + '<div class="td-meta">' + esc(lc.program) + (lc.product ? " · " + esc(lc.product) : "") + " · approved, Mark License Agreement ready to send</div></div>"
                + (canWrite ? '<div class="td-lic">' + licActionsHTML(lc, "needs_contact") + "</div>" : "") + "</div>";
        }
        if (key === "expiry") {
            var ec = x;
            return tdItem(key, '<div class="td-main"><button class="td-org" type="button" data-tdcert="' + esc(certKey(ec)) + '">' + esc(ec.org) + "</button>"
                + '<div class="td-meta">' + esc(ec.program) + (ec.product ? " · " + esc(ec.product) : "") + ' · <span class="bad">' + Math.abs(ec.days || 0) + " days past the anniversary of " + esc(fmt(ec.anniversary)) + "</span></div></div>",
                tdBtn("Open and Decide", 'data-tdcert="' + esc(certKey(ec)) + '"'), true);
        }
        var f = x, st = currentState(f);
        var head = '<div class="td-main"><button class="td-org" type="button" data-tdopen="' + f.row + '">' + esc(f.org) + "</button>"
            + '<div class="td-meta">' + tdWhat(f) + " · " + esc(titleOfState(st)) + (tdDays(f) ? " · " + tdDays(f) : "");
        if (key === "followup") {
            var fx = followUpOf(f) || {};
            head += "</div>" + '<div class="td-meta">' + esc(fx.reason || "On the follow-up list") + (fx.kind === "list" ? " (from the MACTS follow-up list)" : fx.kind === "auto" ? " (flagged automatically)" : "") + "</div></div>";
            return tdItem(key, head, canWrite ? tdBtn("Note and Next Date", 'data-fuedit="' + f.row + '"') + tdBtn("Back to Active", 'data-fuclear="' + f.row + '"', true) + tdBtn("Move to Prospects", 'data-tdprospect="' + f.row + '"', true) : "", fx.severity === "high");
        }
        head += "</div></div>";
        if (key === "assessor") {
            return tdItem(key, head, canWrite ? '<select class="pc-input td-sel" data-tdassessor="' + f.row + '" aria-label="Assessor for ' + esc(f.org) + '"><option value="">Choose the assessor…</option>'
                + ASSESSORS.map((function(a) { return "<option>" + esc(a) + "</option>"; })).join("") + "</select>" : "");
        }
        if (key === "welcome") return tdItem(key, head, canWrite ? tdBtn("Mark the Welcome Email Sent", 'data-tdwelcome="' + f.row + '"') + tdBtn("Open", 'data-tdopen="' + f.row + '"', true) : "", true);
        return tdItem(key, head, tdBtn("Open", 'data-tdopen="' + f.row + '"'));
    }
    var TD_WAIT = [
        [ "company", "With the Company", "Their move: documents, a demo date, payment, a signature, fixes." ],
        [ "assessor", "With the Assessor", "Demos, reviews and results. They record these in the Assessor Portal." ],
        [ "jonathan", "With Jonathan", "Results and scope decisions on My Approvals." ],
        [ "system", "The System Is Handling It", "Renewal notices and reminders, and Mark License Agreements going out through DocuSign." ],
        [ "later", "Follow Up Later", "On Follow Up, with a chase-again date still to come." ],
        [ "hold", "On Hold", "MISMO's delay. Nothing chases these until the hold is released." ]
    ];
    function tdWaitRow(key, f) {
        var st = currentState(f), extra = "";
        if (key === "later") { var x = followUpOf(f) || {}; extra = (x.reason ? " · " + esc(x.reason) : "") + (x.nextOn ? " · chase again " + esc(fmt(x.nextOn)) : ""); }
        if (key === "system" && st === "ApprovedPendingLicense") { var c = certFor(f), L = c ? licOf(c) : null; extra = L ? " · Mark License: " + esc((LIC_SAID[L.status] || L.status || "").toLowerCase()) : ""; }
        return '<button class="td-row" type="button" data-tdopen="' + f.row + '"><span class="td-rn">' + esc(f.org) + '</span><span class="td-rm">' + tdWhat(f) + " · " + esc(titleOfState(st)) + (tdDays(f) ? " · " + tdDays(f) : "") + extra + "</span></button>";
    }
    function tdLastProgram(name) {
        var s = slugName(name), hit = null;
        (D.inFlight || []).forEach((function(f) { if (slugName(f.org) === s) hit = f; }));
        if (!hit) (D.certifications || []).forEach((function(c) { if (slugName(c.org) === s) hit = c; }));
        return hit;
    }
    function tdProspectRow(name) {
        var e = orgEdits[orgSlug(name)] || {}, last = tdLastProgram(name);
        var why = e.status === "prospect" ? (e.statusReason || "Not going through certification") + (e.statusSince ? ", since " + fmt(e.statusSince) : "") : "Not going through certification";
        return '<div class="td-prow"><div class="td-main"><button class="td-org" type="button" data-tdorg="' + esc(name) + '">' + esc(name) + "</button>"
            + '<div class="td-meta">' + (last ? esc(last.program) + (last.product ? " · " + esc(last.product) : "") + " · " : "") + esc(why) + "</div></div>"
            + (canWrite ? '<div class="td-acts">' + tdBtn("Start Application", 'data-tdstart="' + esc(name) + '"', true) + "</div>" : "") + "</div>";
    }
    function renderTodo() {
        var host = $("todo");
        if (!host) return;
        var ae = document.activeElement;
        if (ae && host.contains(ae) && /^(INPUT|SELECT|TEXTAREA)$/.test(ae.tagName)) { tdPending = true; return; }
        tdPending = false;
        var m = tdModel(), n = 0, html = "";
        TD_GROUPS.forEach((function(g) {
            var rows = m.todo[g[0]];
            if (!rows.length) return;
            n += rows.length;
            html += '<div class="td-group" data-tdgroup="' + g[0] + '"><div class="td-ghead"><h3>' + esc(g[1]) + '</h3><span class="td-c">' + rows.length + '</span><span class="td-help">' + esc(g[2]) + "</span></div>"
                + rows.map((function(x) { return tdRowLine(g[0], x); })).join("") + "</div>";
        }));
        var wn = 0;
        TD_WAIT.forEach((function(b) { wn += m.wait[b[0]].length; }));
        var head = '<div class="td-head"><span class="td-n">' + n + '</span><span class="td-say">' + (n === 1 ? "thing needs you." : "things need you.")
            + (wn ? " " + wn + " more " + (wn === 1 ? "is" : "are") + " waiting on somebody else." : "") + "</span></div>";
        if (!n) html = '<div class="td-clear">Nothing needs you right now.</div>';
        var waitHtml = wn ? '<details class="td-fold" data-tdfold="waiting"' + (tdFold.waiting ? " open" : "") + "><summary>Waiting on Others (" + wn + ")"
            + TD_WAIT.filter((function(b) { return m.wait[b[0]].length; })).map((function(b) { return '<span class="td-chip">' + esc(b[1]) + " " + m.wait[b[0]].length + "</span>"; })).join("") + "</summary>"
            + '<div class="td-fbody">' + TD_WAIT.filter((function(b) { return m.wait[b[0]].length; })).map((function(b) {
                return "<h4>" + esc(b[1]) + '</h4><p class="td-bn">' + esc(b[2]) + "</p>" + m.wait[b[0]].map((function(f) { return tdWaitRow(b[0], f); })).join("");
            })).join("") + "</div></details>" : "";
        var proHtml = m.prospects.length ? '<details class="td-fold" data-tdfold="prospects"' + (tdFold.prospects ? " open" : "") + "><summary>Prospects (" + m.prospects.length + ')<span class="td-chip">not going through certification</span></summary>'
            + '<div class="td-fbody"><p class="td-bn">Nothing chases these. Start Application when one comes back; Move to Prospects on a Follow Up line puts a company here.</p>'
            + m.prospects.map(tdProspectRow).join("") + "</div></details>" : "";
        host.innerHTML = head + html + waitHtml + proHtml;
        m.todo.invoice.forEach((function(r) { loadInvoice(r.key, (function(rec) { tdPaintDrop(r.key, rec); })); }));
    }
    function tdFind(attr, key) {
        var host = $("todo");
        if (!host) return null;
        var all = host.querySelectorAll("[" + attr + "]");
        for (var i = 0; i < all.length; i++) if (all[i].getAttribute(attr) === key) return all[i];
        return null;
    }
    function tdPaintDrop(key, rec) {
        var d = tdFind("data-tdinv", key);
        if (!d) return;
        var z = d.querySelector(".td-dz"), pick = d.querySelector("[data-tdpick]");
        d.classList.toggle("have", !!rec);
        if (z) z.innerHTML = rec ? "<b>✓</b> " + esc(rec.name || "invoice.pdf") + " attached" : "Drop the invoice PDF here";
        if (pick) pick.textContent = rec ? "Replace" : "Choose a File";
    }
    function tdTakeFile(key, file) {
        if (!file) return;
        if (!/pdf$/i.test(file.name) && file.type !== "application/pdf") { toast("An invoice needs to be a PDF.", "warn"); return; }
        if (file.size > 8 * 1024 * 1024) { toast("That file is over 8 MB, which is too big to keep here.", "warn"); return; }
        var r = renewalRows().filter((function(x) { return x.key === key; }))[0];
        var fr = new FileReader();
        fr.onload = function() {
            var rec = { name: file.name, size: file.size, type: "application/pdf", data: String(fr.result).split(",")[1] || "", at: (new Date).toISOString(), by: me && me.name || "someone", key: key };
            var z = tdFind("data-tdinv", key);
            if (z && z.querySelector(".td-dz")) z.querySelector(".td-dz").textContent = "Saving…";
            ensureToken(key, (function() {
                saveInvoice(key, rec, (function(ok) {
                    tdPaintDrop(key, ok ? rec : invCache[key] || null);
                    if (ok) {
                        toast((r ? r.cert.org + " — " : "") + "invoice attached. Type the Aptify order number and Mark as Sent.", "good");
                        var num = tdFind("data-tdnum", key);
                        if (num && !num.value) num.focus();
                    }
                }));
            }));
        };
        fr.readAsDataURL(file);
    }
    function tdMarkSent(key) {
        var r = renewalRows().filter((function(x) { return x.key === key; }))[0];
        if (!r) return;
        if (!db || !canWrite) { toast("Nothing is being saved — you are signed out, or have view-only access.", "warn"); return; }
        var inp = tdFind("data-tdnum", key);
        var num = String(inp && inp.value || "").trim();
        if (!num) { toast("Type the Aptify order number first, so the daily check can match the payment.", "warn"); if (inp) inp.focus(); return; }
        var c = r.cert, was = quotes[key] || {};
        var body = { key: key, org: c.org, program: c.program, product: c.product || null, anniversary: c.anniversary, amount: r.expected,
            number: num, orderState: "invoice", raisedAt: (new Date).toISOString(), raisedBy: me && me.name || "someone" };
        if (was.token) body.token = was.token;
        if (was.note) body.note = was.note;
        quotes[key] = body;
        if (inp) inp.blur();
        Promise.resolve(db.doc("renewal-quotes/" + key.replace(/[^A-Za-z0-9_.~-]/g, "_")).set(body)).catch(onWriteRefused);
        var entry = { row: null, org: c.org, program: c.program, from: "", to: "", kind: "renewal-invoice", note: "renewal invoice recorded as sent, Aptify order " + num, reason: null, at: body.raisedAt, by: body.raisedBy };
        activity.unshift(entry);
        try { Promise.resolve(db.collection("activity").add(entry)).catch(onWriteRefused); } catch (e) {}
        toast(c.org + " — recorded, and off the list." + (invCache[key] ? "" : " No PDF is attached yet, so the renewal page cannot offer it until one is."), invCache[key] ? "good" : "warn");
        renderAll();
    }
    function tdToProspects(row) {
        var f = (D.inFlight || []).filter((function(x) { return x.row === row; }))[0];
        if (!f) return;
        if (!db || !canWrite) { toast("Nothing is being saved — you are signed out, or have view-only access.", "warn"); return; }
        var s = slugName(f.org);
        var stillLive = (live || []).filter((function(c) { return slugName(c.org) === s; }));
        var open = (D.inFlight || []).filter((function(x) { return slugName(x.org) === s && !fuClosed(x); }));
        var msg = stillLive.length
            ? f.org + " still holds " + stillLive.length + " live certification" + (stillLive.length === 1 ? "" : "s") + ", so the company stays an active provider. This closes only the " + f.program + " cycle, as Application Expired."
            : "Move " + f.org + " to Prospects?\n\n" + (open.length > 1 ? "Their " + open.length + " open cycles close" : "Their open " + f.program + " cycle closes") + " as Application Expired, they come off Follow Up and the queue, and nothing chases them. They are listed under Prospects, and Start Application brings them back.";
        var why = window.prompt(msg + "\n\nWhy? (it goes on the record)", "Not moving forward with certification");
        if (why === null) return;
        why = String(why).trim() || "Not moving forward with certification";
        var note = "Moved to Prospects from the Action Queue.";
        if (stillLive.length) {
            recordMove(f, "ApplicationExpired", why, note);
            toast(f.org + " — " + f.program + " cycle closed.", "good");
            renderAll();
            return;
        }
        open.forEach((function(x) { recordMove(x, "ApplicationExpired", why, note); }));
        editOrg(f.org, { status: "prospect", statusReason: why, statusSince: isoDay(new Date) }, "moved to Prospects — " + why);
        tdFold.prospects = true;
        renderTodo();
    }
    function tdStart(name) {
        var last = tdLastProgram(name), prog = "";
        if (last) {
            var p = (D.programs || []).filter((function(x) { return x.name === last.program || x.code === last.program || x.mactsType === last.program || x.code === last.programCode; }))[0];
            prog = p ? p.mactsType || p.code : "";
        }
        newApp = { kind: "initial", state: "DocumentsRequested", org: name, program: prog, receivedOn: D.asOf || (new Date).toISOString().slice(0, 10) };
        renderNewApp();
        var el = $("newapp");
        if (el && el.scrollIntoView) el.scrollIntoView({ behavior: "smooth", block: "start" });
        toast("Fill in the application for " + name + " and Add to the Board. They come off Prospects when it is saved.", "good");
    }
    (function tdWire() {
        var host = $("todo");
        if (!host) return;
        host.addEventListener("toggle", (function(e) {
            var d = e.target;
            if (d && d.getAttribute && d.getAttribute("data-tdfold")) tdFold[d.getAttribute("data-tdfold")] = d.open;
        }), true);
        host.addEventListener("focusout", (function() {
            setTimeout((function() { if (tdPending) renderTodo(); }), 150);
        }));
        host.addEventListener("click", (function(e) {
            var t = e.target && e.target.closest ? e.target.closest("[data-tdopen],[data-tdcert],[data-tdrenewal],[data-tdpick],[data-tdsent],[data-tdprospect],[data-tdwelcome],[data-tdstart],[data-tdorg]") : null;
            if (!t) return;
            if (t.hasAttribute("data-tdopen")) { openPanelRecord(+t.getAttribute("data-tdopen"), null, null); return; }
            if (t.hasAttribute("data-tdcert")) { openPanelCert(t.getAttribute("data-tdcert"), null); return; }
            if (t.hasAttribute("data-tdrenewal")) { openRenewal(t.getAttribute("data-tdrenewal")); return; }
            if (t.hasAttribute("data-tdpick")) { var inp = tdFind("data-tdfile", t.getAttribute("data-tdpick")); if (inp) inp.click(); return; }
            if (t.hasAttribute("data-tdsent")) { tdMarkSent(t.getAttribute("data-tdsent")); return; }
            if (t.hasAttribute("data-tdwelcome")) { markWelcomeSent(+t.getAttribute("data-tdwelcome")); renderTodo(); return; }
            if (t.hasAttribute("data-tdstart")) { tdStart(t.getAttribute("data-tdstart")); return; }
            if (t.hasAttribute("data-tdorg")) { if (typeof openPanelOrg === "function") openPanelOrg(t.getAttribute("data-tdorg")); return; }
        }));
        host.addEventListener("change", (function(e) {
            var t = e.target;
            if (t && t.hasAttribute && t.hasAttribute("data-tdfile")) { tdTakeFile(t.getAttribute("data-tdfile"), t.files && t.files[0]); t.value = ""; return; }
            if (t && t.hasAttribute && t.hasAttribute("data-tdassessor")) {
                var f = byRow(+t.getAttribute("data-tdassessor")), c = f && certFor(f), v = t.value;
                if (!f || !v) return;
                t.blur();
                if (c) editCert(c, { assessor: v }, null);
                else { f.assessor = v; toast(f.org + " — assessor set to " + v + ".", "good"); }
                tdPending = false;
                renderAll();
            }
        }));
        host.addEventListener("keydown", (function(e) {
            var t = e.target;
            if (e.key === "Enter" && t && t.hasAttribute && t.hasAttribute("data-tdnum")) { e.preventDefault(); tdMarkSent(t.getAttribute("data-tdnum")); }
        }));
        [ "dragenter", "dragover" ].forEach((function(ev) {
            host.addEventListener(ev, (function(e) {
                var d = e.target && e.target.closest ? e.target.closest("[data-tdinv]") : null;
                if (!d) return;
                e.preventDefault();
                d.classList.add("over");
            }));
        }));
        host.addEventListener("dragleave", (function(e) {
            var d = e.target && e.target.closest ? e.target.closest("[data-tdinv]") : null;
            if (d && !d.contains(e.relatedTarget)) d.classList.remove("over");
        }));
        host.addEventListener("drop", (function(e) {
            var d = e.target && e.target.closest ? e.target.closest("[data-tdinv]") : null;
            if (!d) return;
            e.preventDefault();
            d.classList.remove("over");
            tdTakeFile(d.getAttribute("data-tdinv"), e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]);
        }));
        setTimeout((function() { renderTodo(); renderQueueCounts(); }), 0);
    })();
    document.addEventListener("click", (function(e) {
        var t = e.target && e.target.closest ? e.target.closest("[data-tdprospect]") : null;
        if (!t) return;
        e.preventDefault();
        tdToProspects(+t.getAttribute("data-tdprospect"));
    }), true);
'''

HTML_HEAD_OLD = '<p>Every open step, counted once, on the card for the most pressing reason it is open.</p>\n    </div></div>'
HTML_HEAD_NEW = ('<p>What needs you, one line each, with the button that does it. Everything waiting on somebody else is folded away below it.</p>\n'
                 '    </div><div class="phead-act" id="na-act"></div></div>\n\n'
                 '    <div id="newapp"></div>\n'
                 '    <div id="todo"></div>\n\n'
                 '    <details class="td-more" id="td-more"><summary>Numbers, Phase Board and Certification Scripts</summary>')


def once(s, old, new):
    n = s.count(old)
    if n != 1:
        raise SystemExit("export failed: to-do queue anchor found %d times: %s" % (n, old[:70]))
    return s.replace(old, new)


def apply(s):
    if "function renderTodo()" in s:
        return s
    # --- the page ---
    s = once(s, HTML_HEAD_OLD, HTML_HEAD_NEW)
    s = once(s, '        <div class="hl-date" id="hl-date"></div>\n        <div class="phead-act" id="na-act"></div>\n',
                '        <div class="hl-date" id="hl-date"></div>\n')
    s = once(s, '      <div id="newapp"></div>\n      <div id="queue" hidden></div>', '      <div id="queue" hidden></div>')
    s = once(s, '\n  </section>\n\n  <!-- ================= INVOICES ================= -->',
                '\n    </details>\n  </section>\n\n  <!-- ================= INVOICES ================= -->')
    s = once(s, '  .qgroup{margin-bottom:24px;}', CSS + '  .qgroup{margin-bottom:24px;}')
    # --- the module, beside the Follow Up module it builds on ---
    s = once(s, '    function renderQueue() {\n        var gs = queueGroups();',
                MODULE + '    function renderQueue() {\n        renderTodo();\n        var gs = queueGroups();')
    # --- the nav count is the to-do count ---
    s = once(s, '        pip.textContent = pipCount(n);\n        pip.className = "pip" + (!n ? " quiet" : late ? " bad" : "");',
                '        n = todoCount();\n        renderTodo();\n'
                '        pip.textContent = pipCount(n);\n        pip.className = "pip" + (!n ? " quiet" : late ? " bad" : "");')
    s = once(s, 'pip.title = !n ? "Nothing on the queue" : late ? late + " of " + n + " open more than " + PIP_LATE_DAYS + " days" : n + " on the queue, none open more than " + PIP_LATE_DAYS + " days";',
                'pip.title = !n ? "Nothing needs you" : n + (n === 1 ? " thing needs you" : " things need you");')
    # --- closed cycles and prospects stay off the phase board and the old cards ---
    s = once(s, 'D.inFlight.forEach((function(f) {\n            if (followUpOf(f) || fuHeld(f)) return;\n            var p = phaseOf(currentState(f));',
                'D.inFlight.forEach((function(f) {\n            if (followUpOf(f) || fuHeld(f)) return;\n            if (!tdOpen(f)) return;\n            var p = phaseOf(currentState(f));')
    s = once(s, '            if (claimed[f.row]) return;\n            if (followUpOf(f) || fuHeld(f)) return;',
                '            if (claimed[f.row]) return;\n            if (!tdOpen(f)) return;\n            if (followUpOf(f) || fuHeld(f)) return;')
    # --- Move to Prospects on a cycle's own panel too ---
    s = once(s, '\'<button class="lc-btn ghost" type="button" data-fuedit="\' + f.row + \'">Change the Reason or Date</button>\' : "")',
                '\'<button class="lc-btn ghost" type="button" data-fuedit="\' + f.row + \'">Change the Reason or Date</button>\''
                ' + \'<button class="lc-btn ghost" type="button" data-tdprospect="\' + f.row + \'">Move to Prospects</button>\' : "")')
    s = once(s, 'data-fuedit="\' + f.row + \'">Move to Follow Up</button></div>\' : "";',
                'data-fuedit="\' + f.row + \'">Move to Follow Up</button>'
                '<button class="lc-btn ghost" type="button" data-tdprospect="\' + f.row + \'">Move to Prospects</button></div>\' : "";')
    # --- a company's status reads the edit as well as the base record ---
    s = once(s, 'var list = D.organizations.filter((function(o) {', 'var list = D.organizations.map(tdEffOrg).filter((function(o) {')
    s = once(s, '        out.inactive = e.status === "inactive";', '        if (e.status) out.status = e.status;\n        out.inactive = e.status === "inactive";')
    # --- an application started for a prospect makes them active again ---
    s = once(s, '        newApp = null;\n        toast(body.org + " added to the board.");',
                '        newApp = null;\n        if (tdProspect(body.org)) editOrg(body.org, { status: "active", statusReason: null, statusSince: null }, "back from Prospects: application started");\n'
                '        toast(body.org + " added to the board.");')
    # --- the renewal panel's Mark as Sent kept losing the link's token ---
    s = once(s, '                quotes[panel.key] = body;',
                '                if (quotes[panel.key] && quotes[panel.key].token) body.token = quotes[panel.key].token;\n                quotes[panel.key] = body;')
    return s
