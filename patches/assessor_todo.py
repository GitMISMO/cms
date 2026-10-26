"""The assessor view's To Do, split the way Jonna asked (26 Oct 2026).

To Do holds what the firm is working: the engagements where the next move is the firm's, and
under them "In Your Queue, Waiting on Someone Else" - ones the firm has already worked (demo or
review done, results in, remediation open, approved) that are now with the company, MISMO or the
VP. Coming to You is only for engagements the firm has not touched yet. The Assessor Portal
(GitMISMO/assessors) draws the same three groups. Applied by export-from-artifact.py.
"""
NAME = "Assessor To Do: in your queue vs coming to you"

WORKED = ('["AwaitingArtifacts", "ArtifactReview", "PrelimResultsSubmitted", "PrelimQueryOpen", '
          '"RemediationOpen", "RemediationEscalated", "RemediationSubmitted", "RemediationQueryOpen", '
          '"AppealOpen", "ScopeReviewVp", "ScopeReviewCompany", "ApprovedPendingLicense", "LicenseSent"]')


def once(s, old, new):
    n = s.count(old)
    if n != 1:
        raise SystemExit("export failed: assessor To Do anchor found %d times: %s" % (n, old[:70]))
    return s.replace(old, new)


def apply(s):
    if "var asInQueue = " in s:
        return s
    s = once(s,
        'return !(f.waiting && f.waiting.indexOf("Assessor") >= 0);\n        })).filter(showToFirm);',
        'return !(f.waiting && f.waiting.indexOf("Assessor") >= 0);\n        })).filter(showToFirm);\n'
        '        var AS_WORKED = ' + WORKED + ';\n'
        '        var asWorked = function(f) { return AS_WORKED.indexOf(currentState(f)) >= 0 || doneForFirm(f); };\n'
        '        var asInQueue = others.filter(function(f) { return asWorked(f) && !scriptOutstanding(f); });\n'
        '        others = others.filter(function(f) { return !asWorked(f); });')
    s = once(s,
        '<span>Coming to You</span><small>waiting on somebody else</small></div>"',
        '<span>Coming to You</span><small>not started yet</small></div>"')
    s = once(s,
        '\'<div class="hl-tile flat"><b>\' + others.length + "</b><span>Coming to You</span>',
        '\'<div class="hl-tile flat"><b>\' + asInQueue.length + "</b><span>In Your Queue</span><small>waiting on somebody else</small></div>" + '
        '\'<div class="hl-tile flat"><b>\' + others.length + "</b><span>Coming to You</span>')
    s = once(s,
        '" coming once somebody else moves first." : "Nothing else is queued behind them."',
        '" coming to you, not started yet." : asInQueue.length ? "" : "Nothing else is queued behind them."')
    s = once(s,
        'say += ", out of " + em(mine.length) + " on the board. " + (',
        'say += ", out of " + em(mine.length) + " on the board. " + (asInQueue.length ? em(asInQueue.length) + " you have worked " + (asInQueue.length === 1 ? "is" : "are") + " waiting on somebody else. " : "") + (')
    s = once(s,
        'engTable(withMe, "Nothing is waiting on you right now.") + "</div>" + (blocked.length',
        'engTable(withMe, "Nothing is waiting on you right now.") + (asInQueue.length ? '
        '\'<div style="margin:22px 0 10px;padding-top:16px;border-top:1px solid var(--border)">\' + '
        '\'<h3 style="margin:0 0 4px;font-size:15px;font-weight:600">In Your Queue, Waiting on Someone Else</h3>\' + '
        '\'<p class="psub" style="margin:0">You have already worked these. They come back to you when the company, MISMO or the VP has moved.</p></div>\' + '
        'engTable(asInQueue, "") : "") + "</div>" + (blocked.length')
    s = once(s,
        '", but waiting on somebody else first. " + "Nothing to do on these yet.',
        '", but waiting on somebody else first, and not started yet. " + "Nothing to do on these yet.')
    return s
