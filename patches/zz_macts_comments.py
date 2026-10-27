"""Comments from MACTS on the company record (Jonna, 27 Oct 2026).

The MACTS export's Comments sheet (27 comments, 2023-2025) was not carried over at the cutover.
They are now in cms-data data/macts-comments.json (read by relay-connect.js as an optional
file, D.mactsComments), each with the MACTS row it was on and that row's company. A company's
panel lists its comments, newest first, under Comments from MACTS. Applied by
export-from-artifact.py; every anchor must be found exactly once, or the build stops.
"""

NAME = "Comments from MACTS on the company record"

MODULE = r'''
    /* ---- Comments from MACTS (27 Oct 2026): see patches/zz_macts_comments.py ---- */
    function mactsCommentsHTML(org) {
        var all = (D.mactsComments && D.mactsComments.comments) || [], s = slugName(org.name);
        var mine = all.filter((function(c) { return c.org && slugName(c.org) === s; })).sort((function(a, b) { return String(b.at).localeCompare(String(a.at)); }));
        if (!mine.length) return "";
        return '<details class="pfoot" open><summary>Comments from MACTS (' + mine.length + ")</summary>" + '<div class="pfoot-b">'
            + mine.map((function(c) {
                return '<div style="margin:0 0 10px"><div style="font-size:11.5px;color:var(--ink-3)">' + esc(fmt(String(c.at).slice(0, 10))) + (c.by ? " · " + esc(c.by) : "") + " · MACTS row " + esc(String(c.row)) + "</div>"
                    + '<div style="font-size:13px;line-height:1.5">' + esc(c.text) + "</div></div>";
            })).join("") + "</div></details>";
    }
'''


def once(s, old, new):
    n = s.count(old)
    if n != 1:
        raise SystemExit("export failed: MACTS comments anchor found %d times: %s" % (n, old[:70]))
    return s.replace(old, new)


def apply(s):
    if "function mactsCommentsHTML(" in s:
        return s
    s = once(s, '    function renderPanel() {', MODULE + '    function renderPanel() {')
    s = once(s, '''+ "</div></details>" : "");
            wireCompany($("d-body"));''', '''+ "</div></details>" : "") + mactsCommentsHTML(org);
            wireCompany($("d-body"));''')
    return s
