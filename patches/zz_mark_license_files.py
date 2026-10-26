"""Past Mark License Agreements from MACTS, linked on each certification (Jonna, 26 Oct 2026).

The Smartsheet attachments were exported to SharePoint (Certification Applications/MACTS
Attachments/All MACTS Attachments.zip). The 185 Mark License Agreements in it were filed by
company under Certification Applications/Mark License Agreements, and indexed in cms-data
data/mark-license-files.json (read by relay-connect.js as D.markLicenseFiles).

The Mark License section of a certification now lists the signed copies MACTS held for that
company and program, each opening the PDF in SharePoint. Applied by export-from-artifact.py;
every anchor must be found exactly once, or the build stops.
"""

NAME = "Past Mark License Agreements linked on each certification"

MODULE = r'''
    /* ---- Past Mark License Agreements (26 Oct 2026): see patches/zz_mark_license_files.py ---- */
    var ML_SITE = "https://mortgagebankersassociation.sharepoint.com";
    function mlFilesFor(c) {
        var idx = D.markLicenseFiles || {}, s = slugName(c.org);
        return (idx.files || []).filter((function(x) {
            return x.org && slugName(x.org) === s && (!x.program || x.program === c.program);
        })).sort((function(a, b) {
            function n(x) { var m = /Renewal\s*(\d+)/.exec(x.cycle || ""); return /Initial/.test(x.cycle || "") ? 0 : m ? +m[1] : 99; }
            return n(b) - n(a);
        }));
    }
    function mlFilesHTML(c) {
        var list = mlFilesFor(c);
        if (!list.length) return "";
        return '<div class="pc-lab" style="margin-top:14px">Signed Copies from MACTS</div>' + '<ul class="ml-files">' + list.map((function(x) {
            var url = ML_SITE + encodeURI(x.path);
            return '<li><a href="' + esc(url) + '" target="_blank" rel="noopener">' + esc((x.cycle ? x.program + " " + x.cycle : x.file)) + "</a>"
                + (x.cycle ? ' <span class="quiet">' + esc(x.file) + "</span>" : "") + "</li>";
        })).join("") + "</ul>";
    }
'''

CSS = '''  .ml-files{margin:4px 0 0; padding-left:18px; font-size:13px; line-height:1.7;}
  .ml-files .quiet{color:var(--ink-3); font-size:11.5px;}
'''


def once(s, old, new):
    n = s.count(old)
    if n != 1:
        raise SystemExit("export failed: Mark License files anchor found %d times: %s" % (n, old[:70]))
    return s.replace(old, new)


def apply(s):
    if "function mlFilesHTML(" in s:
        return s
    s = once(s, '    function licPanelHTML(c) {', MODULE + '    function licPanelHTML(c) {')
    s = once(s, '        })).join("") + "</tbody></table></details>" : "") + "</div>";\n    }\n    function licActionsHTML',
                '        })).join("") + "</tbody></table></details>" : "") + mlFilesHTML(c) + "</div>";\n    }\n    function licActionsHTML')
    s = once(s, 'fromMacts ? " Recorded in MACTS before this system; no copy of the signed document " + "is held here yet." : "")',
                'fromMacts ? " Recorded in MACTS before this system." + (mlFilesFor(c).length ? " The signed copies MACTS held are linked below." : " No signed copy was found among the MACTS attachments.") : "")')
    s = once(s, '  .qgroup{margin-bottom:24px;}', CSS + '  .qgroup{margin-bottom:24px;}')
    return s
