# MISMO Certification Management System

The page served at **https://resources.mismo.org/cms/**.

## Which repository serves this page

**This one.** `resources.mismo.org` is the organization's Pages domain, held by
`GitMISMO.github.io`; this repository is a *project site* published under it, so it owns the
`/cms/` path. GitHub's own Settings → Pages here says "Your site is live at
http://resources.mismo.org/cms/".

There is a `cms/` folder inside `GitMISMO.github.io` as well. **It serves nothing.** A project
repository wins the path over a folder of the same name in the organization site, so anything
uploaded there is shadowed: it commits cleanly, reports success, and never reaches the web.
That cost a working day in October 2026 — the page simply did not change, with no error
anywhere to explain why. If an upload appears to do nothing, check which repository it went to
before changing anything else.

## This repository is public, and that governs what is in it

GitHub Pages needs a public repository to serve a custom domain. So this repository holds the
page's code and **no certification records**: no company MISMO assesses, no fee, no invoice,
no assessment result, no email address, no assessor expense.

That is not a convention anybody has to remember. `index.html` is built by
**`export-from-artifact.py`** (in this repository, at the root), which works from an **allow
list** — a key is published only if somebody has decided it should be, and anything new is
left out until they do. Every record key is kept in the file but emptied, so the page still
draws its own "nothing here" states instead of breaking.

**Deciding to publish a key is not deciding to publish whatever later lands in it.** By
October 2026 `frameResults` had grown fifteen contact addresses, `consultantSubmissions` one,
and `pricing` four invoice numbers and twelve figures — all keys that had been published
safely for months while they were still empty skeletons. So the build also empties any
allow-listed key that has come to hold records, and names each one it emptied in its output.

The build strips the source comments too. They explain why each rule exists, and they do that
by naming the company the rule came from, so they belong inside MISMO and not here. It uses
terser rather than a regular expression: a comment stripper that does not understand strings
and regex literals will quietly corrupt half a megabyte of somebody's application.

Finally it reads the finished file the way a stranger would, and **refuses to write** if it
finds a contact address, an invoice number, a figure, or a company MISMO assesses. The four
assessor firms are allowed, because the page is meant to say who may assess what — and
several of them are certified themselves, so the firm list is exempt from that test rather
than the names being special-cased.

## What is published, and what it shows

| Published | Left out |
| --- | --- |
| The ten programs: terms, grace periods, documents required, whether there is a demo | Every certification and cycle |
| The 31-state lifecycle and its legal transitions | Every fee, invoice and assessor expense |
| The four assessor firms | Every questionnaire, score and submitted file |
| MISMO's summit dates | The certification scripts |

So the page shows **the shape of the system with nothing in it**, and says so in a banner at
the top. The working board is inside MISMO.

One judgment call worth knowing: the program cards carry a count ("28 active of 50 on
record"). Those are aggregates, and MISMO already publishes its certified-company directory,
so they are derivable. If that is not wanted, drop `programs` from the allow list.

## Where the records actually live

In **`cms-data`**, which is private, reached through MISMO's relay. A page served from here
cannot read a private repository by itself — a browser has no credential for one. The relay
holds the GitHub token and is what bridges the two, which is why the private repository and
the relay arrive together rather than separately.

- `portal-data.json` — the records, spread into the page's data as top-level keys
- `data/<name>.json` — the price list, the instruments, the forms, the FRAME material

Both are read by `relay-connect.js` at sign-in. There is no build step for them: commit a file
in `cms-data` and the relay serves it on the next page load.

## Collection names must be lowercase

The relay answers **`BAD_ID`** to any collection id containing a capital letter. It does this
whatever `projects.json` permits, so a collection can be correctly allow-listed and still be
refused.

Ten of this page's seventeen collections were camelCase — `cycleState`, `orgEdits`,
`certEdits`, `formEdits`, `scriptPrep`, `frameScores`, `frameReview`, `frameAsk`,
`scenAssign`, `scenarioLog` — which meant **saving had never worked at all** for lifecycle
transitions or company edits, from the day the relay was connected until 20 October 2026.
Nothing was lost, because nothing was ever written. They are now `cycle-state`, `org-edits`
and so on, and the build refuses to write a page that reintroduces one.

## Connected: the shared sign-in and the relay

The page opens only behind the MISMO Resources sign-in (People & Access, key `cms`), loads the
real records from `cms-data` through the relay, and saves edits there. `relay-connect.js` in
this repository gives the page the three services it asks Claude for (`user`, `db`,
`downloads`), so the page's own logic runs unchanged.

**This is the whole difference between the artifact and this page.** On claude.ai the runtime
hands the artifact `window.claude` because it declares the `db`, `downloads` and `user`
capabilities, so saving works there with no wiring whatsoever. A page served from GitHub Pages
gets nothing of the sort. Every hand-made export dropped some part of the wiring, and the page
then looked perfect and silently could not save. That is what the build is for.

- **Records** are only ever *read*, after sign-in, in place of the empty public placeholders.
- **Edits**: each collection the page writes (`cycle-state`, `invoices`, `org-edits`,
  `scores`, `activity`, ...) is `data/db-<collection>.json` in `cms-data`, saved through the
  relay with the version it read; if someone saved in between, the change is re-applied on top
  of theirs.
- **Access**: Edit may save; View opens read-only and the page shows its own view-only notice.

The build carries these four hooks into every `index.html`, and **refuses to write the file if
any is missing**:

1. `<script src="/assets/session.js"></script>` just before `</head>`
2. the application script's opening tag as `<script type="text/x-cms-app" id="cms-app">`
   (relay-connect.js starts it once the records are in)
3. `<span id="rs-account"></span>` in the masthead, after the `mast-exit` button
4. `<script src="relay-connect.js"></script>` just before `</body>`

## How this is updated

The page is built from **Artifact - CMS** on claude.ai, which is where the work happens:

```
python3 export-from-artifact.py ARTIFACT.html -o index.html
```

`ARTIFACT.html` is the artifact page as claude.ai serves it. The script needs `terser`
(`npm install terser`); without it the comments are left in and it says so loudly rather than
writing a file that looks finished.

Then commit `index.html` here, and the records separately in `cms-data`. **Order matters when
the records bring a key the page has not seen before** — publish the page first, so it is
ready for them. Doing it the other way round hides whatever the old page cannot render, with
no error to show for it.

`index.html` is built, never hand-edited here — an edit made in this repository is overwritten
by the next build.

## Settings this page depends on

- **Pages**: Settings → Pages → Deploy from a branch → `main` → `/ (root)`
- **Custom domain**: inherited from the organization's `resources.mismo.org`. Nothing to set
  here, and no DNS change for this one.

## Pages beside the CMS (hand-written, not built)

- `playbook.html`: the Certification Email Playbook.
- `approvals.html`: My Approvals, the VP's one-click decisions.
- `sent.html`: every email the certification system has sent.
- **The Sent Emails tab.** The **Sent Emails** tab beside Activity in the CMS is that page,
  embedded (`sent.html?embed=1`).
  - It is added by `relay-connect.js` (`addSentEmailsTab`), not by `index.html`, so a rebuild from
    the artifact cannot drop it.
  - Move it into the artifact at the next rebuild if you like, and delete `addSentEmailsTab`
    when you do.

## Patches on top of the artifact

`export-from-artifact.py` applies every `patches/*.py`, in name order, after the build. Each
patch stops the build if its anchors are missing, so a rebuild cannot silently drop one.

- `follow_up_card.py`: Follow Up and On Hold cards on the Action Queue, in both views.
  - Follow Up holds cycles a person moved there (with a reason and a chase-again date), the
    MACTS follow-up list, and anything waiting on the company for 30 days.
  - What people decide is kept in `data/db-follow-ups.json`.
- `no_license_panel.py`: removes the separate Mark Licenses Outstanding panel.

`index.html` as committed has both applied.
