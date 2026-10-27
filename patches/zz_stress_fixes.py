"""Fixes from the full stress test (27 Oct 2026).

1. Opening a record from the Action Queue did nothing. The to-do list's buttons (a company
   name, Open, the certification and renewal links) opened the side panel, and the page's
   "click anywhere else closes the panel" listener closed it again in the same click, because
   those buttons were not on its list of things that open a panel. They are now.

2. A certification whose Mark License has gone out through the flow could not be opened. The
   flow returns the agreement's file name as plain text, and the panel expected an object with
   a date, so it stopped with an error (PhoenixTeam's showed it first). The panel now accepts
   either.

Applied by export-from-artifact.py; every anchor must be found exactly once.
"""

NAME = "Stress test fixes: Action Queue opens records; licence document as text"

FIXES = [
    ('var PANEL_OPENERS = "#drawer, .rowbtn, .col, .card, .cnt-row, .drow, .erow, .qpick, " + ".hl-tile, .ss-item, .ss-results, .stat";',
     'var PANEL_OPENERS = "#drawer, .rowbtn, .col, .card, .cnt-row, .drow, .erow, .qpick, " + ".hl-tile, .ss-item, .ss-results, .stat"'
     ' + ", [data-tdopen], [data-tdcert], [data-tdrenewal], [data-tdorg], [data-tdinv], [data-tdstart]";'),
    ('''        var L = licOf(c);
        var st = L.status || "not_sent";
        if (st === "not_sent" && c.markLicense === "executed") st = "signed";
        var fromMacts = st === "signed" && !L.signedAt;''',
     '''        var L = licOf(c);
        if (L.document && typeof L.document !== "object") L = Object.assign({}, L, { document: { name: String(L.document), at: L.signedAt || L.sentAt || null } });
        var st = L.status || "not_sent";
        if (st === "not_sent" && c.markLicense === "executed") st = "signed";
        var fromMacts = st === "signed" && !L.signedAt;'''),
    (' · on file since " + esc(fmt(L.document.at.slice(0, 10)))',
     '" + (L.document.at ? " · on file since " + esc(fmt(String(L.document.at).slice(0, 10))) : "")'),
]


def apply(s):
    if "[data-tdopen], [data-tdcert]" in s:
        return s
    for old, new in FIXES:
        n = s.count(old)
        if n != 1:
            raise SystemExit("export failed: stress-fix anchor found %d times: %s" % (n, old[:70]))
        s = s.replace(old, new)
    return s
