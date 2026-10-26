"""No separate Mark Licenses Outstanding panel on the Action Queue (Jonna, 26 Oct 2026).

Mark Licenses already show where the work is: the Mark License card on By Phase, the Mark License
Outstanding group on By What Needs Doing, and each certification's own panel (send, track,
download). Since 26 Oct a license signed in DocuSign also moves its certification to Certified
on its own. So the big panel is taken off the page; its list element stays, hidden, so the code
that fills it has somewhere harmless to write. Applied by export-from-artifact.py after the build.
"""
NAME = "No separate Mark License panel"

def apply(s):
    start = "    <!-- The Mark License list had rendering code but nowhere to render"
    if start not in s:
        if '<div id="licenselist" hidden></div>' in s:
            return s
        raise SystemExit("export failed: Mark License panel anchor not found")
    a = s.index(start)
    b = s.index('<div id="licenselist"></div>', a)
    b = s.index("</div>", b + len('<div id="licenselist"></div>')) + len("</div>")
    if b - a > 2500:
        raise SystemExit("export failed: Mark License panel larger than expected; not removed")
    return s[:a] + '    <div id="licenselist" hidden></div>' + s[b:]
