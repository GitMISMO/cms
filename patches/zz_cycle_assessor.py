"""An assessor picked on the Action Queue is saved, even for a cycle with no certification yet
(27 Oct 2026).

The to-do list's assessor picker saved the choice on the certification (db-cert-edits.json). A
cycle with no certification on record yet (a new application) only had it set on the page, so it
was gone on the next load and no email, booking page or Assessor Portal ever saw it. It is now
saved on the cycle's own record in cycle-state (`assessor`, an added field), with a line in the
activity log, and read back onto the cycle on every load. The background jobs read the same
field (cycle-state assessor, else the certification's, else the board's).

Applied by export-from-artifact.py; every anchor must be found exactly once.
"""

NAME = "Assessor picked for a cycle with no certification is saved"

OLD_PICK = '''                else { f.assessor = v; toast(f.org + " — assessor set to " + v + ".", "good"); }'''
NEW_PICK = '''                else {
                    f.assessor = v;
                    moves[f.row] = Object.assign({ state: currentState(f) }, moves[f.row], { assessor: v });
                    var aen = { row: f.row, org: f.org, program: f.program, from: "", to: "", kind: "edit",
                        note: "Assessor set to " + v, reason: null, at: (new Date).toISOString(), by: me && me.name ? me.name : "You" };
                    activity.unshift(aen);
                    persist(f.row, aen);
                    toast(f.org + " — assessor set to " + v + ".", "good");
                }'''

OLD_LOAD = '''                moves = next;
                renderPipe();
                renderQueueCounts();'''
NEW_LOAD = '''                moves = next;
                Object.keys(moves).forEach((function(r) {
                    var m = moves[r], cf = m && m.assessor ? byRow(+r) : null;
                    if (cf) cf.assessor = m.assessor;
                }));
                renderPipe();
                renderQueueCounts();'''


def once(s, old, new):
    n = s.count(old)
    if n != 1:
        raise SystemExit("export failed: cycle assessor anchor found %d times: %s" % (n, old[:70]))
    return s.replace(old, new)


def apply(s):
    if "kind: \"edit\",\n                        note: \"Assessor set to \"" in s:
        return s
    s = once(s, OLD_PICK, NEW_PICK)
    s = once(s, OLD_LOAD, NEW_LOAD)
    return s
