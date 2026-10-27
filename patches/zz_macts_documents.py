"""Documents from MACTS on the company record (Jonna, 27 Oct 2026).

The 1,091 attachments in the MACTS export (SharePoint: Certification Applications/MACTS
Attachments/All MACTS Attachments.zip) were filed by company under Certification Applications/
MACTS Documents: applications, questionnaires and attestations, invoices, application
agreements, recommendation reports and supporting documents. The 123 blank form templates were
left out, and the Mark License Agreements are filed separately (zz_mark_license_files.py). The
index is cms-data data/macts-documents.json (D.mactsDocuments, an optional file read by
relay-connect.js). A company's panel lists its documents by certification and round, each
opening the file in SharePoint. Applied by export-from-artifact.py after zz_macts_comments.py.
"""

NAME = "Documents from MACTS on the company record"

MODULE = r'''
    /* ---- Documents from MACTS (27 Oct 2026): see patches/zz_macts_documents.py ---- */
    function mactsDocsHTML(org) {
        var idx = D.mactsDocuments || {}, s = slugName(org.name);
        var mine = (idx.files || []).filter((function(x) { return x.org && slugName(x.org) === s; }));
        if (!mine.length) return "";
        function rank(c) { var m = /Renewal\s*(\d+)/.exec(c || ""); return /Initial/.test(c || "") ? 0 : m ? +m[1] : 99; }
        var groups = {}, order = [];
        mine.forEach((function(x) {
            var k = (x.program ? x.program + " " : "") + (x.cycle || "") || "Other Documents";
            if (!groups[k]) { groups[k] = []; order.push(k); }
            groups[k].push(x);
        }));
        order.sort((function(a, b) {
            var ga = groups[a][0], gb = groups[b][0];
            if (!ga.cycle !== !gb.cycle) return ga.cycle ? -1 : 1;
            return String(ga.program || "").localeCompare(String(gb.program || "")) || rank(gb.cycle) - rank(ga.cycle);
        }));
        var site = "https://mortgagebankersassociation.sharepoint.com";
        return '<details class="pfoot"><summary>Documents from MACTS (' + mine.length + ")</summary>" + '<div class="pfoot-b">'
            + order.map((function(k) {
                return '<div style="margin:0 0 10px"><div style="font-size:11.5px;font-weight:600;color:var(--ink-2);margin-bottom:2px">' + esc(k) + "</div>"
                    + groups[k].map((function(x) {
                        return '<div style="font-size:13px;line-height:1.6"><a href="' + esc(site + encodeURI(x.path)) + '" target="_blank" rel="noopener">' + esc(x.type || "Document") + "</a>"
                            + ' <span style="font-size:11.5px;color:var(--ink-3)">' + esc(x.file) + "</span></div>";
                    })).join("") + "</div>";
            })).join("") + "</div></details>";
    }
'''


def once(s, old, new):
    n = s.count(old)
    if n != 1:
        raise SystemExit("export failed: MACTS documents anchor found %d times: %s" % (n, old[:70]))
    return s.replace(old, new)


def apply(s):
    if "function mactsDocsHTML(" in s:
        return s
    s = once(s, '    function renderPanel() {', MODULE + '    function renderPanel() {')
    s = once(s, '+ mactsCommentsHTML(org);', '+ mactsCommentsHTML(org) + mactsDocsHTML(org);')
    return s
