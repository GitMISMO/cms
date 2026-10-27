#!/usr/bin/env python3
"""
Build resources.mismo.org/cms/index.html from the "Artifact - CMS" page on claude.ai.

Why this file exists
--------------------
The artifact and the hosted page are the same application with one difference that
matters: on claude.ai the runtime hands the page `window.claude` (it declares the
db, downloads and user capabilities), so saving works with no wiring at all. A page
served from GitHub Pages gets nothing of the sort - it has to be given the same three
services by relay-connect.js, which also holds the sign-in and reads the records out
of the private cms-data repository.

Every hand-made export so far has dropped some part of that wiring, and the page then
looks perfect and silently cannot save. This script is the export, so that stops
happening. Run it; do not do it by hand.

Usage
-----
    python3 export-from-artifact.py ARTIFACT.html -o index.html

ARTIFACT.html is the page as claude.ai serves it (Artifact -> read, or View source).
"""

import argparse
import json
import re
import sys

# Record-bearing keys: present in the bundle so the page still draws its own
# "nothing here" states, but emptied, because this repository is public.
# A key NOT listed here is published as-is, so anything new is emptied by default
# below and only moves into KEEP once somebody has decided it should be public.
KEEP = {
    "programs", "states", "assessors", "counts", "asOf", "generated",
    "rejections", "warnings", "forms", "pricing", "certScripts",
    "assessorFirms", "consultantScorecard", "consultantSubmissions",
    "applicantForms", "individualCerts", "summits",
    "frameResults", "frameScenarios", "frameScoring", "frameSources",
}

APP_OPEN = '<script type="text/x-cms-app" id="cms-app">'
SESSION = '<script src="/assets/session.js"></script>'
RELAY = ('<script src="relay-connect.js?v=2026-10-27c"></script>'
         '  <!-- resources.mismo.org: sign-in, records and saving through the relay -->')
ACCOUNT = '<span id="rs-account"></span>'

# The relay answers BAD_ID to any collection id containing a capital letter.
RENAME = {
    "certEdits": "cert-edits", "cycleState": "cycle-state", "formEdits": "form-edits",
    "frameAsk": "frame-ask", "frameReview": "frame-review", "frameScores": "frame-scores",
    "markLicense": "mark-license", "orgEdits": "org-edits", "scenAssign": "scen-assign",
    "scenarioLog": "scenario-log", "scriptPrep": "script-prep",
}


def fail(msg):
    sys.exit("export failed: " + msg)


def strip_comments(js):
    """Remove every comment from the application. None if terser is not installed."""
    import os
    import shutil
    import subprocess
    import tempfile
    terser = (shutil.which("terser")
              or (os.path.join("node_modules", ".bin", "terser")
                  if os.path.exists(os.path.join("node_modules", ".bin", "terser")) else None))
    if not terser:
        return None
    d = tempfile.mkdtemp()
    src, dst = os.path.join(d, "in.js"), os.path.join(d, "out.js")
    open(src, "w", encoding="utf-8").write(js)
    r = subprocess.run([terser, src, "--no-compress", "--no-mangle",
                        "--format", "comments=false,beautify=true", "-o", dst],
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail("terser could not read the application: " + (r.stderr or "").strip()[:300])
    out = open(dst, encoding="utf-8").read()
    if len(out) < len(js) * 0.5:
        fail("comment stripping removed too much (%d -> %d bytes); not writing" % (len(js), len(out)))
    return out


def unwrap(src):
    """claude.ai serves the page inside a skeleton of its own. Take the real document."""
    i = src.find('<html lang="en">')
    if i < 0:
        fail('no <html lang="en"> - is this the artifact page?')
    j = src.rfind("</html>")
    return src[i:j + len("</html>")]


# What a stranger must never find in a public repository. An address at mismo.org and
# the obvious placeholders are allowed; everything else is somebody's contact detail.
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}")
INVOICE = re.compile(r"\b6[23]\d{5}\b")          # Aptify invoice numbers
FIGURE = re.compile(r"\$[\d,]{3,}")
ALLOWED_EMAIL = re.compile(r"@(mismo\.org|mba\.org|company\.com|example\.com)$", re.I)
FIRM_KEYS = {"assessors", "assessorFirms"}


def assessed_companies(doc):
    """
    Every company in the records, less the assessor firms.

    The assessor firms are published on purpose - the page says who may assess what. A
    company MISMO assesses is not, and naming one is enough to say it is in a programme.
    Taken from the records themselves rather than a list somebody has to maintain, so a
    company added next month is covered without anyone remembering to add it here.
    """
    firms = {str(f.get("name") or f.get("firm") or "").strip()
             for f in (doc.get("assessors") or []) if isinstance(f, dict)}
    firms |= {k.strip() for k in (doc.get("assessorFirms") or {})}
    names = set()
    for o in (doc.get("organizations") or []):
        if not isinstance(o, dict):
            continue
        for n in [o.get("name")] + list(o.get("spellings") or []):
            n = str(n or "").strip()
            if len(n) >= 4 and n not in firms:
                names.add(n)
    return names


def offences(text, companies=()):
    bad = [e for e in set(EMAIL.findall(text)) if not ALLOWED_EMAIL.search(e)]
    out = []
    if bad:
        out.append("%d contact address(es)" % len(bad))
    if INVOICE.search(text):
        out.append("%d invoice number(s)" % len(set(INVOICE.findall(text))))
    if FIGURE.search(text):
        out.append("%d figure(s)" % len(set(FIGURE.findall(text))))
    named = sorted({c for c in companies if c in text})
    if named:
        out.append("names %d company/companies MISMO assesses (%s%s)"
                   % (len(named), ", ".join(named[:3]), "…" if len(named) > 3 else ""))
    return out


def public_bundle(raw):
    """
    Empty every record-bearing key.

    Two rules, both needed. A key not on the KEEP list is emptied, so anything new in
    the artifact stays out until somebody decides it should be published. And a key on
    the KEEP list is emptied anyway if it has come to hold records - which is what
    happened to frameResults, consultantSubmissions and pricing between the October
    exports: the same keys, quietly filled with submitted responses, contact addresses
    and invoice numbers. The decision to publish a key is not a decision to publish
    whatever later lands in it.
    """
    doc = json.loads(raw)
    companies = assessed_companies(doc)
    out, emptied, scrubbed = {}, [], []
    for k, v in doc.items():
        blank = [] if isinstance(v, list) else ({} if isinstance(v, dict) else None)
        if k not in KEEP:
            out[k] = blank
            emptied.append(k)
            continue
        # The firm list is the one place a company name is the point: the page says who
        # may assess what. Several assessor firms are also certified themselves, so their
        # names appear in the records too - that must not empty the list they belong in.
        found = offences(json.dumps(v), () if k in FIRM_KEYS else companies)
        if found:
            out[k] = blank
            scrubbed.append("%s (%s)" % (k, ", ".join(found)))
        else:
            out[k] = v
    out["publicPreview"] = True          # how the page knows it is the empty shell
    return json.dumps(out, separators=(",", ":")), emptied, scrubbed, companies


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("artifact")
    ap.add_argument("-o", "--out", default="index.html")
    a = ap.parse_args()

    s = unwrap(open(a.artifact, encoding="utf-8").read())
    steps = []

    # 1. the records come out, and are replaced by the empty public bundle
    m = re.search(r'(<script[^>]*id="cms-data"[^>]*>)(.*?)(</script>)', s, re.S)
    if not m:
        fail("no cms-data block")
    bundle, emptied, scrubbed, companies = public_bundle(m.group(2))
    s = s[:m.start(2)] + bundle + s[m.end(2):]
    steps.append("records emptied (%d keys): %s" % (len(emptied), ", ".join(sorted(emptied))))
    if scrubbed:
        steps.append("held records despite being on the publish list, so emptied too: "
                     + "; ".join(sorted(scrubbed)))

    # 2. the application is parked as text, for relay-connect.js to start once the
    #    real records are in place. Left as a live <script> it would run against the
    #    empty bundle and draw an empty board for a moment, then never reload.
    plain = [mm for mm in re.finditer(r"<script>", s)]
    if len(plain) != 1:
        fail("expected exactly one unattributed <script> (the application), found %d" % len(plain))
    s = s[:plain[0].start()] + APP_OPEN + s[plain[0].end():]
    steps.append("application parked as text/x-cms-app")

    # 3. sign-in
    if SESSION not in s:
        if "</head>" not in s:
            fail("no </head>")
        s = s.replace("</head>", SESSION + "\n</head>", 1)
        steps.append("session.js added")

    # 4. the account chip in the masthead
    if 'id="rs-account"' not in s:
        mm = re.search(r'<button class="mast-exit"[^>]*>.*?</button>', s, re.S)
        if not mm:
            fail("no mast-exit button to hang the account chip on")
        s = s[:mm.end()] + " " + ACCOUNT + s[mm.end():]
        steps.append("rs-account span added")

    # 5. the relay itself, last so the page is assembled before it runs
    if "relay-connect.js" not in s:
        k = s.rfind("</body>")
        if k < 0:
            fail("no </body>")
        s = s[:k] + RELAY + "\n" + s[k:]
        steps.append("relay-connect.js added")


    # The page decided it was unreachable whenever a relay WAS configured - the test was
    # inverted, so the "Not saving right now" notice showed permanently and said the
    # opposite of the truth. relay-connect.js happens to suppress the notice, which is why
    # this is easy to miss; the state underneath is still wrong. Read live, so the answer
    # does not depend on which of the start-up chains ran first.
    old = 'if(CMS_RELAY) return "relay-unreachable";'
    if old in s:
        s = s.replace(old, 'if(CMS_RELAY || (window.CMS_CONFIG && window.CMS_CONFIG.relay)) return "connected";')
        mm = re.search(r"function banner\s*\(\s*\)\s*\{", s)
        if mm:
            i = s.index("{", mm.end() - 1); j = i + 1; d = 1
            while d > 0:
                d += 1 if s[j] == "{" else (-1 if s[j] == "}" else 0)
                j += 1
            body = s[i:j]
            if body.count('b.style.display = "";') == 1:
                s = s[:i] + body.replace('b.style.display = "";',
                                         'b.style.display = (how === "connected") ? "none" : "";') + s[j:]
        steps.append("connected state fixed (the page called a live relay unreachable)")

    # 6. the source comments come out.
    #    They explain why each rule exists, and they do that by naming the company the rule
    #    came from - "Teraverde's unpaid invoice made its own card", and so on. Those belong
    #    inside MISMO, not in a public repository. Done with terser rather than a regex,
    #    because a comment stripper that does not understand strings and regex literals will
    #    quietly corrupt 500KB of somebody's application.
    mm = re.search(r'(<script type="text/x-cms-app" id="cms-app">)(.*?)(</script>)', s, re.S)
    if not mm:
        fail("the parked application went missing")
    stripped = strip_comments(mm.group(2))
    if stripped is None:
        steps.append("WARNING: terser not found, source comments LEFT IN - "
                     "run `npm install terser` and build again before pushing")
    else:
        s = s[:mm.start(2)] + stripped + s[mm.end(2):]
        steps.append("source comments stripped from the application")

    # 7. the browser tab. "Artifact - CMS" names the artifact in Jonna's gallery and must
    #    stay as it is there; the hosted page is not the artifact and reads just "CMS".
    mm = re.search(r"<title>[^<]*</title>", s)
    if not mm:
        fail("no <title>")
    s = s[:mm.start()] + "<title>CMS</title>" + s[mm.end():]
    steps.append("tab title set to CMS")

    # 7. collection ids the relay will accept
    n = 0
    def sub(mm):
        nonlocal n
        q, name = mm.group(1), mm.group(2)
        if name in RENAME:
            n += 1
            return "collection(%s%s%s" % (q, RENAME[name], q)
        return mm.group(0)
    s = re.sub(r'collection\((["\'])([A-Za-z-]+)\1', sub, s)
    steps.append("collection ids lowercased: %d" % n)

    # --- MISMO's additions on top of the artifact: patches/*.py, applied in name order ---
    # Each has apply(html) -> html and stops the build if its anchors are not found, so a
    # rebuild can never silently drop one (Follow Up and On Hold cards, no separate Mark
    # License panel, 26 Oct 2026).
    import glob, importlib.util, os
    here = os.path.dirname(os.path.abspath(__file__))
    for path in sorted(glob.glob(os.path.join(here, "patches", "*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        s = mod.apply(s)
        steps.append("patch applied: " + getattr(mod, "NAME", os.path.basename(path)))

    # --- refuse to write anything that is not wired up ---
    for need, what in [(SESSION, "session.js"), (APP_OPEN, "the parked application"),
                       ('id="rs-account"', "the account chip"), ("relay-connect.js", "relay-connect.js")]:
        if need not in s:
            fail("%s is missing - the page would not save" % what)
    left = [c for c in re.findall(r'collection\(["\']([A-Za-z-]+)["\']', s) if any(ch.isupper() for ch in c)]
    if left:
        fail("collection ids the relay refuses: %s" % ", ".join(sorted(set(left))))
    kept = json.loads(bundle)
    for k in ("organizations", "certifications", "money", "inFlight", "pipelines"):
        if kept.get(k):
            fail("%s is not empty - records must not go in the public repository" % k)

    # The last word: read the finished file the way a stranger would. This repository is
    # public, so a contact address or an invoice number reaching it is not a bug to fix
    # next time - it is published the moment it is pushed.
    # The firm list is published on purpose, and some firms are certified themselves, so
    # their names are legitimately in the page. Everything else named is not.
    firm_text = json.dumps({k: kept.get(k) for k in FIRM_KEYS})
    final = offences(s, {c for c in companies if c not in firm_text})
    if final:
        bad = sorted(e for e in set(EMAIL.findall(s)) if not ALLOWED_EMAIL.search(e))
        fail("the built page still carries " + ", ".join(final)
             + (("; first few: " + ", ".join(bad[:5])) if bad else ""))

    open(a.out, "w", encoding="utf-8").write(s)
    print("\n".join("  - " + x for x in steps))
    print("wrote %s (%d bytes)" % (a.out, len(s)))


if __name__ == "__main__":
    main()
