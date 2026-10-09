# MISMO Certification Management System

The page served at **https://resources.mismo.org/cms/**.

## This repository is public, and that governs what is in it

GitHub Pages needs a public repository to serve a custom domain. So this repository holds the
page's code and **no certification records**: no company MISMO assesses, no fee, no invoice,
no assessment result, no email address, no assessor expense.

That is not a convention anybody has to remember. `index.html` here is built by
`tools/deploy/public-bundle.py`, which works from an **allow list** — a key is published only
if somebody has decided it should be, and anything new is left out until they do. Every record
key is kept in the file but emptied, so the page still draws its own "nothing here" states
instead of breaking.

The same build also strips the source comments. They explain why each rule exists, and they do
that by naming the company the rule came from, so they belong inside MISMO and not here.

`tools/deploy/leak-check.py` then reads the finished file as a stranger would and refuses the
push if it finds an email address, a company MISMO assesses, an invoice number or a figure.

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

## Connected: the shared sign-in and the relay (9 Oct 2026)

The page now opens only behind the MISMO Resources sign-in (People & Access, key `cms`), loads the real records from
`cms-data` through the relay, and saves edits there. It is done by **`relay-connect.js`** in this repository, which
gives the page the three services it asks Claude for (`user`, `db`, `downloads`), so the page's own logic runs
unchanged:

- **Records** (`portal-data.json`, `data/<file>.json`) are only ever *read*, after sign-in, in place of the empty
  public placeholders. The public file still carries none.
- **Edits**: each collection the page writes (`cycleState`, `invoices`, `orgEdits`, `scores`, `activity`, ...) is
  `data/db-<collection>.json` in `cms-data`, saved through the relay with the version it read; if someone saved in
  between, the change is re-applied on top of theirs.
- **Access**: Edit may save; View opens read-only and the page shows its own view-only notice.

**For the build (`public-bundle.py`): carry these four hooks into every new `index.html`,** or the next build
disconnects the page:

1. `<script src="/assets/session.js"></script>` just before `</head>`
2. the application script's opening tag as `<script type="text/x-cms-app" id="cms-app">` (relay-connect.js starts
   it once the records are in)
3. `<span id="rs-account"></span>` in the masthead, after the `mast-exit` button
4. `<script src="relay-connect.js"></script>` just before `</body>`

## How this is updated

Claude builds `index.html` and pushes it to `main`; Pages publishes within about a minute. It
is built, never hand-edited here — an edit made in this repository is overwritten by the next
build.

## Settings this page depends on

- **Pages**: Settings → Pages → Deploy from a branch → `main` → `/ (root)`
- **Custom domain**: `resources.mismo.org`, already serving `/summit-hq/`, `/service-orders/`,
  `/sponsorship/`, `/qr/` and the rest. No DNS change for this one.
