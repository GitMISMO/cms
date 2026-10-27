"""A stage move keeps what was already recorded on the cycle (26 Oct 2026).

A move used to replace the cycle's whole record in cycle-state, so the demonstration date,
findings, remediation target, payment details and anything else recorded earlier were lost on
the next move. Now a move keeps them, and changes only the stage, reason, note, who and when.

The one exception is the demonstration date: moving back to choosing a date (a reschedule)
clears it, so an old date is never shown as booked, and opening a new round of remediation
clears the old remediation target (the company gives a new one on its remediation page). My Approvals (approvals.html) does the
same. Applied by export-from-artifact.py; every anchor must be found exactly once.
"""

NAME = "Stage moves keep the cycle's earlier details"

OLD = '''        moves[f.row] = {
            state: toState,
            reason: reason || null,
            note: note || null,
            by: entry.by,
            at: entry.at
        };
        lastChange = entry;'''

NEW = '''        var kept = {};
        if (moves[f.row]) for (var kk in moves[f.row]) if ([ "state", "reason", "note", "by", "at", "decidedOn" ].indexOf(kk) < 0) kept[kk] = moves[f.row][kk];
        if ([ "AwaitingDemoSelection", "PreAssessmentDiscussion", "DemoProposed" ].indexOf(toState) >= 0) delete kept.demoOn;
        if (toState === "RemediationOpen") { delete kept.remediationTarget; delete kept.remediationTargetBy; }
        kept.state = toState;
        kept.reason = reason || null;
        kept.note = note || null;
        kept.by = entry.by;
        kept.at = entry.at;
        moves[f.row] = kept;
        lastChange = entry;'''


def apply(s):
    if "var kept = {};" in s:
        return s
    n = s.count(OLD)
    if n != 1:
        raise SystemExit("export failed: keep-cycle-details anchor found %d times" % n)
    return s.replace(OLD, NEW)
