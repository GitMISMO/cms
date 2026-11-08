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

(async () => {
  const browser = await chromium.launch();
  let failures = 0, steps = 0;
  for (const [width, scheme] of [[1400, "light"], [390, "dark"]]) {
    const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme });
    const page = await ctx.newPage();
    const errs = [];
    page.on("pageerror", e => errs.push("script error: " + e.message));
    page.on("console", m => { if (m.type() === "error" && !/Failed to load resource|ERR_|net::/i.test(m.text())) errs.push("console: " + m.text()); });
    await page.route("**/*", async route => {
      const u = new URL(route.request().url());
      if (u.hostname === "resources.mismo.org") {
        if (u.pathname === "/assets/session.js") return route.fulfill({ contentType: "application/javascript", body:
          "window.ResourcesSession={token:()=>'t',canEdit:()=>false,current:()=>({name:'Test Person',email:'test@mismo.org'}),requireAccess:()=>Promise.resolve(),mount:()=>{}};" });
        if (u.pathname.startsWith("/cms/")) {
          let f = path.join(ROOT, u.pathname.slice(5) || "index.html");
          if (f.endsWith(path.sep)) f = path.join(f, "index.html");
          if (fs.existsSync(f) && fs.statSync(f).isFile()) return route.fulfill({ contentType: TYPES[path.extname(f)] || "application/octet-stream", body: fs.readFileSync(f) });
        }
        return route.fulfill({ status: 404, body: "" });
      }
      if (/lambda-url\.[\w-]+\.on\.aws$/.test(u.hostname)) {
        if (route.request().method() !== "GET") return route.fulfill({ status: 403, contentType: "application/json", body: '{"error":"VIEW_ONLY"}' });
        if (/\/file\/portal-data\.json$/.test(u.pathname)) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ content: Buffer.from("{}").toString("base64") }) });
        if (/\/data\/db-/.test(u.pathname)) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ data: { docs: {} }, sha: null }) });
        if (/\/data\//.test(u.pathname)) return route.fulfill({ contentType: "application/json", body: JSON.stringify({ data: {}, sha: null }) });
        return route.fulfill({ contentType: "application/json", body: "{}" });
      }
      return route.abort();
    });
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
  await browser.close();
  console.log(steps + " steps, " + failures + " problem(s).");
  process.exit(failures ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
