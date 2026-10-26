"""Follow Up and On Hold on the Action Queue (Jonna, 26 Oct 2026).

Agreement and Application mixed live work with cycles nobody may ever finish, and the Follow-Up
List could only be seen under By What Needs Doing - and nobody could add to it or clear it.
This gives both views two more cards:

  Follow Up  anything stuck, with the reason and a "chase again on" date:
               - put there by a person, from the cycle's own panel (Move to Follow Up), or
               - on the MACTS follow-up list (D.followUps), until a person clears it, or
               - automatic: waiting on the company with no movement for 30 days.
             "Back to Active" takes it off; an automatic one then stays off until the cycle
             moves to another stage.
  On Hold    cycles at On Hold, or whose certification MISMO has put on hold.

A cycle in either card is left off its phase card, so the phase cards show only live work.
What a person decides is kept in the "follow-ups" collection (data/db-follow-ups.json).

Applied by export-from-artifact.py after the build, so rebuilding index.html from the artifact
keeps it. Every anchor must be found exactly once, or the build stops.
"""

NAME = "Follow Up and On Hold cards"

MODULE = r'''
    /* ---- Follow Up and On Hold (26 Oct 2026): see patches/follow_up_card.py ---- */
    var followUpDocs = {};
    var FU_STALE_DAYS = 30;
    function fuToday() { return isoDay(new Date()); }
    function fuDaysInState(f) {
        var m = moves[f.row];
        if (m && m.at) return Math.floor((Date.now() - new Date(m.at).getTime()) / 864e5);
        if (f.age != null) {
            var since = parseDay(D.asOf);
            return f.age + (since ? Math.max(0, daysBetween(since, new Date())) : 0);
        }
        return null;
    }
    function fuStateDef(f) { return STATE[currentState(f)] || {}; }
    function fuClosed(f) { var st = currentState(f), d = fuStateDef(f); return !!d.terminal && st !== "OnHold"; }
    function fuHeld(f) {
        if (fuClosed(f)) return false;
        if (currentState(f) === "OnHold") return true;
        var c = certFor(f);
        return !!(c && holdOf(c));
    }
    function fuListEntry(f) {
        var s = slugName(f.org);
        var hit = (D.followUps || []).filter((function(x) { return slugName(x.org) === s; }))[0];
        if (!hit) return null;
        var cl = followUpDocs["org-" + s];
        return cl && cl.active === false ? null : hit;
    }
    function followUpOf(f) {
        if (fuClosed(f) || fuHeld(f)) return null;
        var st = currentState(f);
        var d = followUpDocs[String(f.row)];
        if (d && d.active) return { kind: "manual", reason: d.reason || "", nextOn: d.nextOn || null, by: d.by || "", at: d.at || null };
        if (d && d.active === false && d.clearedState === st) return null;
        var l = fuListEntry(f);
        if (l) return { kind: "list", reason: l.what || l.reason || "On the follow-up list", nextOn: null, severity: l.severity };
        var w = String((fuStateDef(f).waiting) || f.waiting || "");
        var days = fuDaysInState(f);
        if (/company/i.test(w) && !/mismo/i.test(w) && days != null && days >= FU_STALE_DAYS)
            return { kind: "auto", reason: "No movement from the company in " + days + " days", nextOn: null, days: days };
        return null;
    }
    function fuDue(x) { return !!x && (!x.nextOn || x.nextOn <= fuToday()); }
    function fuRows() {
        return (D.inFlight || []).filter((function(f) { return !!followUpOf(f); })).sort((function(a, b) {
            var x = followUpOf(a), y = followUpOf(b);
            var dx = fuDue(x) ? 0 : 1, dy = fuDue(y) ? 0 : 1;
            if (dx !== dy) return dx - dy;
            return String(x.nextOn || "").localeCompare(String(y.nextOn || "")) || String(a.org).localeCompare(String(b.org));
        }));
    }
    function holdRows() { return (D.inFlight || []).filter(fuHeld); }
    function fuSet(f, body) {
        var id = String(f.row);
        var before = followUpDocs[id] ? clone(followUpDocs[id]) : null;
        followUpDocs[id] = body;
        if (db) { try { Promise.resolve(db.doc("follow-ups/" + id).set(body)).catch(onWriteRefused); } catch (e) { onWriteRefused(e); } }
        var entry = { row: f.row, org: f.org, program: f.program, from: "", to: "", kind: "follow-up",
            note: body.active ? "Moved to Follow Up: " + (body.reason || "no reason given") + (body.nextOn ? " (chase again " + fmt(body.nextOn) + ")" : "") : "Back to active from Follow Up",
            reason: null, at: body.at, by: body.by };
        activity.unshift(entry);
        if (db) { try { Promise.resolve(db.collection("activity").add(entry)).catch(onWriteRefused); } catch (e) {} }
        if (!body.active) {
            var s = slugName(f.org);
            if ((D.followUps || []).some((function(x) { return slugName(x.org) === s; }))) {
                var org = { active: false, org: f.org, by: body.by, at: body.at };
                followUpDocs["org-" + s] = org;
                if (db) { try { Promise.resolve(db.doc("follow-ups/org-" + s).set(org)).catch(onWriteRefused); } catch (e) {} }
            }
        }
        return before;
    }
    function followUpBlock(f) {
        if (fuClosed(f)) return "";
        var x = followUpOf(f);
        var who = me && me.name ? me.name : "You";
        if (fuHeld(f)) return "";
        if (x) {
            return '<div class="pc-lab">Follow Up</div><div class="qwatch">' + esc(x.reason || "On the follow-up list")
                + (x.nextOn ? " &middot; chase again " + esc(fmt(x.nextOn)) : "")
                + (x.kind === "auto" ? " &middot; flagged automatically" : x.kind === "list" ? " &middot; from the MACTS follow-up list" : (x.by ? " &middot; " + esc(x.by) : "")) + "</div>"
                + '<div class="na-acts" style="margin:8px 0 14px">'
                + (canWrite ? '<button class="lc-btn" type="button" data-fuclear="' + f.row + '">Back to Active</button>'
                    + '<button class="lc-btn ghost" type="button" data-fuedit="' + f.row + '">Change the Reason or Date</button>' : "")
                + "</div>";
        }
        return canWrite ? '<div class="na-acts" style="margin:0 0 14px"><button class="lc-btn ghost" type="button" data-fuedit="' + f.row + '">Move to Follow Up</button></div>' : "";
    }
    document.addEventListener("click", (function(e) {
        var t = e.target && e.target.closest ? e.target.closest("[data-fuedit],[data-fuclear]") : null;
        if (!t) return;
        var row = +(t.getAttribute("data-fuedit") || t.getAttribute("data-fuclear"));
        var f = (D.inFlight || []).filter((function(x) { return x.row === row; }))[0];
        if (!f) return;
        var now = (new Date).toISOString(), who = me && me.name ? me.name : "You";
        if (t.hasAttribute("data-fuclear")) {
            fuSet(f, { row: f.row, org: f.org, program: f.program, active: false, clearedState: currentState(f), by: who, at: now });
            toast(f.org + " is back with the live work.", "good");
        } else {
            var cur = followUpOf(f) || {};
            var reason = window.prompt("Why is " + f.org + " on Follow Up? (for example: Went quiet after the agreement; invoice unpaid)", cur.reason && cur.kind === "manual" ? cur.reason : "");
            if (reason === null) return;
            var d = new Date(); d.setDate(d.getDate() + 14);
            var next = window.prompt("Chase again on (YYYY-MM-DD). Leave it blank for no date.", cur.nextOn || isoDay(d));
            if (next === null) return;
            next = String(next).trim();
            if (next && !/^\d{4}-\d{2}-\d{2}$/.test(next)) { toast("That date needs to be YYYY-MM-DD. Nothing changed.", "warn"); return; }
            fuSet(f, { row: f.row, org: f.org, program: f.program, active: true, reason: String(reason).trim(), nextOn: next || null, by: who, at: now });
            toast(f.org + " moved to Follow Up.", "good");
        }
        renderPipe(); renderQueue(); renderQueueCounts(); if (panel) renderPanel();
    }), true);
'''

def _once(s, old, new, what):
    n = s.count(old)
    if n != 1:
        raise SystemExit("export failed: %s - anchor found %d times, expected once" % (what, n))
    return s.replace(old, new)

def apply(s):
    if "patches/follow_up_card.py" in s:
        return s
    # the module, after the chase notes it replaces in spirit
    s = _once(s, "    var chaseNotes = {};\n", "    var chaseNotes = {};\n" + MODULE, "follow-up module")

    # the phase cards leave out what is on Follow Up or On Hold, and two cards follow them
    s = _once(s,
        "        D.inFlight.forEach((function(f) {\n            var p = phaseOf(currentState(f));\n            (byPhase[p] = byPhase[p] || []).push(f);\n        }));\n        $(\"pipe\").innerHTML = BOARD_PHASES.map(",
        "        D.inFlight.forEach((function(f) {\n            if (followUpOf(f) || fuHeld(f)) return;\n            var p = phaseOf(currentState(f));\n            (byPhase[p] = byPhase[p] || []).push(f);\n        }));\n        $(\"pipe\").innerHTML = BOARD_PHASES.map(",
        "phase cards")
    s = _once(s,
        "        })).join(\"\");\n        Array.prototype.forEach.call($(\"pipe\").querySelectorAll(\".card\"), (function(b) {\n            b.addEventListener(\"click\", (function() {\n                var ph = b.dataset.phase;",
        "        })).join(\"\") + fuCards();\n        Array.prototype.forEach.call($(\"pipe\").querySelectorAll(\".card[data-fucard]\"), (function(b) {\n            b.addEventListener(\"click\", (function() {\n                var k = b.getAttribute(\"data-fucard\");\n                if (panel && panel.mode === \"queue\" && panel.group === k) closePanel(); else openPanelQueue(k);\n            }));\n        }));\n        Array.prototype.forEach.call($(\"pipe\").querySelectorAll(\".card[data-phase]\"), (function(b) {\n            b.addEventListener(\"click\", (function() {\n                var ph = b.dataset.phase;",
        "phase card wiring")
    s = _once(s, "    function renderPipe() {\n",
        "    function fuCards() {\n"
        "        return [ [ \"followup\", \"Follow Up\", fuRows(), \"Program Manager\" ], [ \"onhold\", \"On Hold\", holdRows(), \"MISMO's delay\" ] ].map((function(c) {\n"
        "            var n = c[2].length, sel = panel && panel.mode === \"queue\" && panel.group === c[0];\n"
        "            var due = c[0] === \"followup\" ? c[2].filter((function(f) { return fuDue(followUpOf(f)); })).length : 0;\n"
        "            return '<button class=\"card' + (n ? \"\" : \" quiet\") + (sel ? \" on\" : \"\") + '\" type=\"button\" data-fucard=\"' + c[0] + '\" aria-pressed=\"' + (sel ? \"true\" : \"false\") + '\">'\n"
        "                + \"<h3>\" + esc(c[1]) + '<span class=\"arr\">\\u203a</span></h3>' + '<div class=\"cfoot\"><div class=\"numrow\">'\n"
        "                + '<div class=\"big\">' + n + \" <small>\" + (n === 1 ? \"cycle\" : \"cycles\") + \"</small></div>\"\n"
        "                + '<div class=\"meta\">' + (due ? '<span class=\"chip\" style=\"color:var(--bad)\">' + due + \" to chase now</span>\" : '<span class=\"chip\">' + esc(c[3]) + \"</span>\") + \"</div>\"\n"
        "                + \"</div></div></button>\";\n"
        "        })).join(\"\");\n"
        "    }\n"
        "    function renderPipe() {\n",
        "follow-up cards")

    # the queue view: the old fixed Follow-Up List becomes the same Follow Up group, plus On Hold
    s = _once(s,
        "        out.push({\n            key: \"chase\",\n            title: \"Follow-Up List\",\n            who: \"Program Manager\",\n            kind: \"chases\",\n            rows: D.followUps || [],",
        "        out.push({\n            key: \"followup\",\n            title: \"Follow Up\",\n            who: \"Program Manager\",\n            kind: \"cycles\",\n            rows: fuRows(),\n            sub: \"Stuck, with the reason and when to chase again. Put here from a cycle's own panel, from the MACTS follow-up list, or automatically after 30 days with no movement from the company. Select one to see it; Back to Active takes it off.\"\n        });\n        out.push({\n            key: \"onhold\",\n            title: \"On Hold\",\n            who: \"MISMO's delay\",\n            kind: \"cycles\",\n            rows: holdRows(),\n            sub: \"Held by MISMO: nothing chases these, and no renewal notice goes, until the hold is released.\"\n        });\n        if (false) out.push({\n            key: \"chase\",\n            title: \"Follow-Up List\",\n            who: \"Program Manager\",\n            kind: \"chases\",\n            rows: D.followUps || [],",
        "queue follow-up group")
    s = _once(s, "            chase: 6\n        };", "            chase: 6,\n            followup: 5.5,\n            onhold: 7\n        };", "queue order")
    # a cycle in Follow Up or On Hold is not also listed under who it is waiting on
    s = _once(s,
        "        (D.inFlight || []).forEach((function(f) {\n            if (claimed[f.row]) return;\n            if (namedAbove[slugName(f.org)]) {",
        "        (D.inFlight || []).forEach((function(f) {\n            if (claimed[f.row]) return;\n            if (followUpOf(f) || fuHeld(f)) return;\n            if (namedAbove[slugName(f.org)]) {",
        "queue waiting groups")

    # each listed row says why it is on Follow Up and when to chase
    s = _once(s,
        "                    var stale = panel.group === \"payment\" && r.age != null && r.age > 14;",
        "                    var stale = panel.group === \"payment\" && r.age != null && r.age > 14 || panel.group === \"followup\" && fuDue(followUpOf(r));",
        "row flag")
    s = _once(s,
        "(stale ? '<span class=\"dr-sub bad\">Unpaid ' + r.age + \" days — past a fortnight.</span>\" : \"\")",
        "(panel.group === \"payment\" && stale ? '<span class=\"dr-sub bad\">Unpaid ' + r.age + \" days — past a fortnight.</span>\" : \"\") + (panel.group === \"followup\" ? function() { var x = followUpOf(r) || {}; return '<span class=\"dr-sub' + (fuDue(x) ? \" bad\" : \"\") + '\">' + esc(x.reason || \"\") + (x.nextOn ? \" \\u00b7 chase again \" + esc(fmt(x.nextOn)) : fuDue(x) ? \" \\u00b7 chase now\" : \"\") + \"</span>\"; }() : \"\")",
        "row reason")

    # the cycle's own panel: Move to Follow Up / Back to Active
    s = _once(s, "        return '<div class=\"pc-body\">' + extra + ", "        return '<div class=\"pc-body\">' + followUpBlock(f) + extra + ", "cycle panel")

    # what people decide is shared through the relay like everything else
    s = _once(s,
        "            d.collection(\"cert-edits\").onSnapshot((function(snap) {",
        "            d.collection(\"follow-ups\").onSnapshot((function(snap) {\n                var next = {};\n                (snap.docs || []).forEach((function(doc) { var b = doc.data(); if (b) next[doc.id] = b; }));\n                followUpDocs = next;\n                renderPipe(); renderQueue(); renderQueueCounts();\n            }), (function() {}));\n            d.collection(\"cert-edits\").onSnapshot((function(snap) {",
        "follow-ups collection")
    return s
