/* Click through the whole CMS with empty records, as a stranger's browser would, and fail on any
   script error (review, 7 Nov 2026). The page is served from this repository; the shared sign-in
   and MISMO's relay are stood in for, answering every read with an empty record set, so nothing
   here touches the real records or saves anything. The full click-through with the real records
   runs in cms-data, which is private.

   Run: node tests/click-through.js   (needs playwright and its Chromium) */
"use strict";
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const ROOT = path.join(__dirname, "..");
const TYPES = { ".html": "text/html", ".js": "application/javascript", ".css": "text/css", ".json": "application/json" };

/* The shared Back-button helper (resources.mismo.org/assets/back.js, owned by Forms and shared pages) is tested as it
   is live, never copied here: MISMO_BACK can point at a local copy instead (for trying a change before it is published). */
let BACK = null;
async function backJs() {
  if (BACK !== null) return BACK;
  try {
    if (process.env.MISMO_BACK) BACK = fs.readFileSync(process.env.MISMO_BACK, "utf8");
    else { const r = await fetch("https://resources.mismo.org/assets/back.js"); BACK = r.ok ? await r.text() : ""; }
  } catch (e) { BACK = ""; }
  return BACK;
}
/* The page from this repository; the shared sign-in, the shared Back helper and the relay stood in for. */
async function serve(page, records) {
  await page.route("**/*", async route => {
    const u = new URL(route.request().url());
    if (u.hostname === "resources.mismo.org") {
      if (u.pathname === "/assets/session.js") return route.fulfill({ contentType: "application/javascript", body:
        "window.ResourcesSession={token:()=>'t',canEdit:()=>false,current:()=>({name:'Test Person',email:'test@mismo.org'}),requireAccess:()=>Promise.resolve(),mount:()=>{}};" });
      if (u.pathname === "/assets/back.js") return route.fulfill({ contentType: "application/javascript", body: await backJs() });
      if (u.pathname.startsWith("/cms/")) {
        let f = path.join(ROOT, u.pathname.slice(5) || "index.html");
        if (f.endsWith(path.sep)) f = path.join(f, "index.html");
        if (fs.existsSync(f) && fs.statSync(f).isFile()) return route.fulfill({ contentType: TYPES[path.extname(f)] || "application/octet-stream", body: fs.readFileSync(f) });
      }
      return route.fulfill({ status: 404, body: "" });
    }
    if (/lambda-url\.[\w-]+\.on\.aws$/.test(u.hostname)) {
      if (route.request().method() !== "GET") return route.fulfill({ status: 403, contentType: "application/json", body: '{"error":"VIEW_ONLY"}' });
      if (/\/file\/portal-data\.json$/.test(u.pathname)) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ content: Buffer.from(records).toString("base64") }) });
      if (/\/data\/db-/.test(u.pathname)) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ data: { docs: {} }, sha: null }) });
      if (/\/data\//.test(u.pathname)) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ data: {}, sha: null }) });
      return route.fulfill({ contentType: "application/json", body: "{}" });
    }
    return route.abort();
  });
}

(async () => {
  const browser = await chromium.launch();
  let failures = 0, steps = 0;
  for (const [width, scheme] of [[1400, "light"], [390, "dark"]]) {
    const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme });
    const page = await ctx.newPage();
    const errs = [];
    page.on("pageerror", e => errs.push("script error: " + e.message));
    page.on("console", m => { if (m.type() === "error" && !/Failed to load resource|ERR_|net::/i.test(m.text())) errs.push("console: " + m.text()); });
    await serve(page, "{}");
    await page.goto("https://resources.mismo.org/cms/");
    await page.waitForSelector("#cms-cover", { state: "detached", timeout: 30000 }).catch(() => errs.push("the page never finished loading"));
    const mark = async name => { steps++; if (errs.length) { failures += errs.length; errs.splice(0).forEach(e => console.log("PROBLEM  " + width + "px " + scheme + " @ " + name + ": " + e)); } };
    await mark("load");
    const views = await page.$$eval("[data-view]", b => [...new Set(b.map(x => x.getAttribute("data-view")))]);
    for (const v of views) {
      await page.evaluate(v => { const b = document.querySelector('[data-view="' + v + '"]'); if (b) b.click(); }, v);
      await page.waitForTimeout(500);
      await mark("view " + v);
      /* open the first thing in each view that opens a record panel, then close it */
      const opened = await page.evaluate(() => { const el = [...document.querySelectorAll("[data-pkrow],[data-tdcert],[data-pkcert],[data-tdorg],[data-pkorg]")].find(x => x.offsetParent); if (!el) return false; el.click(); return true; });
      if (opened) {
        await page.waitForTimeout(400); await mark("record panel from " + v);
        const tabs = await page.$$eval("#d-body [data-dtab]", b => b.map(x => x.getAttribute("data-dtab"))).catch(() => []);
        for (const t of tabs) { await page.evaluate(t => { const b = document.querySelector('#d-body [data-dtab="' + t + '"]'); if (b) b.click(); }, t); await page.waitForTimeout(150); await mark("panel tab " + t); }
        await page.evaluate(() => { const c = document.querySelector("#d-close, .dclose"); if (c) c.click(); });
      }
      const text = await page.evaluate(() => document.body.innerText);
      if (/\bNaN\b/.test(text)) { failures++; console.log("PROBLEM  " + width + "px " + scheme + " @ view " + v + ": the page shows NaN"); }
    }
    await ctx.close();
  }
  /* The browser's Back button (CN-033, Jonna, 25 Nov 2026): two menu pages and Back returns to the first, Forward goes
     again; a record's panel and Back closes it and stays on the page; a panel closed with its X leaves no step behind.
     One made-up company, so there is a record to open. Clicks are real clicks: only what a person does makes a step. */
  {
    const ctx = await browser.newContext({ viewport: { width: 1400, height: 900 } });
    const page = await ctx.newPage();
    const errs = [];
    page.on("pageerror", e => errs.push("script error: " + e.message));
    page.on("console", m => { if (m.type() === "error" && !/Failed to load resource|ERR_|net::/i.test(m.text())) errs.push("console: " + m.text()); });
    await serve(page, JSON.stringify({ organizations: [{ name: "Example Test Company", status: "active", certifications: [], spellings: [] }] }));
    await page.goto("https://resources.mismo.org/cms/");
    await page.waitForSelector("#cms-cover", { state: "detached", timeout: 30000 }).catch(() => errs.push("the page never finished loading"));
    const problem = msg => { failures++; console.log("PROBLEM  Back button: " + msg); };
    const state = () => page.evaluate(() => ({
      view: (document.querySelector('#mismonav button.navlink[aria-current="page"]') || {}).dataset?.view || "",
      panel: document.body.classList.contains("panel-open"), helper: !!window.MismoBack }));
    const go = async v => { await page.click('#mismonav button.navlink[data-view="' + v + '"]'); await page.waitForTimeout(700); };
    const back = async () => { await page.evaluate(() => history.back()); await page.waitForTimeout(900); };
    const openRecord = async () => { await go("records"); await page.click('.view.on .rowbtn[data-org]'); await page.waitForTimeout(700); };
    await page.waitForTimeout(1200);              /* back.js settles on the opening page */
    let st = await state();
    const start = st.view;
    if (!st.helper) problem("the shared Back helper (/assets/back.js) did not load");
    else if (!start) problem("no menu button carries aria-current on the opening page");
    else {
      await go("records"); await go("programs");
      st = await state(); if (st.view !== "programs") problem("Programs did not open: " + JSON.stringify(st));
      await back(); st = await state(); if (st.view !== "records") problem("Back from Programs should land on Companies: " + JSON.stringify(st));
      await page.evaluate(() => history.forward()); await page.waitForTimeout(900);
      st = await state(); if (st.view !== "programs") problem("Forward should go to Programs again: " + JSON.stringify(st));
      await back(); await back(); st = await state(); if (st.view !== start) problem("Back to where the page opened (" + start + "): " + JSON.stringify(st));
      /* a panel: Back closes it first and stays on the page, then goes to the page before */
      await openRecord(); st = await state();
      if (!st.panel) problem("the company did not open in the record panel");
      await back(); st = await state(); if (st.panel || st.view !== "records") problem("Back should close the panel and stay on Companies: " + JSON.stringify(st));
      await back(); st = await state(); if (st.view !== start) problem("Back after the panel should go to the page before Companies: " + JSON.stringify(st));
      /* closing the panel with its X leaves no step behind */
      await openRecord();
      await page.click("#d-close"); await page.waitForTimeout(700);
      if ((await state()).panel) problem("the X did not close the panel");
      await back(); st = await state(); if (st.view !== start) problem("after closing the panel with its X, Back should go straight to the page before: " + JSON.stringify(st));
    }
    steps++;
    if (errs.length) { failures += errs.length; errs.forEach(e => console.log("PROBLEM  Back button: " + e)); }
    await ctx.close();
  }
  await browser.close();
  console.log(steps + " steps, " + failures + " problem(s).");
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
