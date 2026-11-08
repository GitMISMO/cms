#!/usr/bin/env python3
"""Nothing private in this public repository (review, 7 Nov 2026).

This repository has to be public for GitHub Pages, so it may hold the page's code and the shape of
the system, never the records. The artifact build used to check that on every export; the page is
now edited here directly, so the same checks run on every change instead:

  - no contact address other than mismo.org, mba.org and the made-up example ones
  - no Aptify invoice number, and no dollar figure in the CMS page
  - the record keys in the page's built-in data are empty
  - the four hooks that let the page sign in and save are all there
  - every collection id is lowercase (the relay refuses any other, and saving silently stops)

Company names are checked too, from the private records, by the "Public pages" check in cms-data:
the list of companies cannot be written down here without publishing it.
Run: python3 tests/check-public.py
"""
import json, os, re, sys

ROOT = os.path.join(os.path.dirname(__file__), "..")
SKIP = {"next.html"}
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
ALLOWED_EMAIL = re.compile(r"@(mismo\.org|mba\.org|company\.com|example\.com|yourcompany\.com)$", re.I)
INVOICE = re.compile(r"\b6[23]\d{5}\b")
FIGURE = re.compile(r"\$[\d,]{3,}")
HOOKS = [('<script src="/assets/session.js"></script>', "the shared sign-in (session.js)"),
         ('<script type="text/x-cms-app" id="cms-app">', "the parked application script"),
         ('id="rs-account"', "the account chip"),
         ('relay-connect.js', "relay-connect.js")]
RECORD_KEYS = ("organizations", "certifications", "money", "inFlight", "pipelines", "newApplications")

problems = []
for f in sorted(os.listdir(ROOT)):
    if f in SKIP or not re.search(r"\.(html|js|md|json)$", f):
        continue
    t = open(os.path.join(ROOT, f), encoding="utf-8").read()
    bad = sorted({e for e in EMAIL.findall(t) if not ALLOWED_EMAIL.search(e)})
    if bad:
        problems.append("%s carries contact address(es): %s" % (f, ", ".join(bad[:5])))
    inv = sorted(set(INVOICE.findall(t)))
    if inv:
        problems.append("%s carries Aptify invoice number(s): %s" % (f, ", ".join(inv[:5])))
    if f == "index.html":
        fig = sorted(set(FIGURE.findall(t)))
        if fig:
            problems.append("index.html carries dollar figure(s): %s" % ", ".join(fig[:5]))
        for need, what in HOOKS:
            if need not in t:
                problems.append("index.html is missing %s, so the page would not sign in or save" % what)
        upper = sorted({c for c in re.findall(r'collection\(["\']([A-Za-z0-9-]+)["\']', t) if any(ch.isupper() for ch in c)})
        if upper:
            problems.append("collection ids the relay refuses (capital letters): %s" % ", ".join(upper))
        m = re.search(r'<script[^>]*id="cms-data"[^>]*>([\s\S]*?)</script>', t)
        if not m:
            problems.append("index.html has no built-in data block (cms-data)")
        else:
            try:
                d = json.loads(m.group(1))
                full = [k for k in RECORD_KEYS if d.get(k)]
                if full:
                    problems.append("records in the public page's built-in data: %s" % ", ".join(full))
            except ValueError as e:
                problems.append("the built-in data block does not parse: %s" % e)

for p in problems:
    print("PROBLEM  " + p)
print("%d problem(s)." % len(problems))
sys.exit(1 if problems else 0)
