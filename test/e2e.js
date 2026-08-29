/* ============================================================================
   End-to-end funnel test.

   Walks the real pages in a real browser across both routing outcomes and
   asserts the behaviours the build exists to guarantee: partial-capture
   timing, payload shape, UTM survival across the page navigation, pixel
   dedupe, slider anchoring, calendar prefill, and validation.

     node test/server.js &     # or: npm start
     node test/e2e.js          # or: npm test
   ========================================================================== */
const { chromium } = require('playwright-core');

const BASE = process.env.BASE || 'http://localhost:8099';
const CHROME = process.env.CHROME_PATH || '/opt/pw-browsers/chromium';

function log(ok, msg) { console.log((ok ? '  PASS  ' : '  FAIL  ') + msg); if (!ok) process.exitCode = 1; }

async function hits() {
  const r = await fetch(BASE + '/__hits');
  return r.json();
}

(async () => {
  await fetch(BASE + '/__reset');   // isolate this run from any previous one
  const browser = await chromium.launch({ executablePath: CHROME });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  page.on('console', m => {
    // "Failed to load resource" carries no URL; response listener covers those.
    if (m.type() === 'error' && !/Failed to load resource/i.test(m.text())) errors.push('console: ' + m.text());
  });
  // The stub calendar URL is a deliberate 404 in this harness, not a page bug.
  page.on('response', r => {
    if (r.status() >= 400 && !/leadconnectorhq\.com/.test(r.url())) errors.push('http ' + r.status() + ' ' + r.url());
  });

  /* ---------- LANDING PAGE ---------- */
  console.log('\n=== LANDING PAGE ===');
  await page.goto(BASE + '/lp.html?utm_source=Meta+Ads&utm_campaign=TOF%2FCBO%2FVSL%2FSCHEDULE%2FWINNERS%2F08-24&utm_content=Ad+3+-v2', { waitUntil: 'networkidle' });

  log((await page.textContent('h1')).includes('3 Weeks'), 'H1 renders from config');
  log((await page.textContent('#diff')).includes('warehouses cabinets locally'), 'differentiator renders');

  const ctas = await page.$$('[data-cta]');
  log(ctas.length === 3, `3 CTAs rendered (found ${ctas.length})`);

  const metas = await page.$$eval('[data-cta-meta]', els => els.map(e => e.textContent));
  log(metas.length === 3 && metas.every(m => m.includes('No deposit required')),
      'friction-killer under EVERY CTA (' + metas.length + '/3)');

  // stat counters animate on scroll
  await page.evaluate(() => document.querySelector('.stats').scrollIntoView());
  await page.waitForTimeout(1500);
  const statTxt = await page.$eval('.stat-n', e => e.textContent);
  log(statTxt.trim() === '400+', `stat counter animated to target (got "${statTxt}")`);

  // sticky bar
  await page.evaluate(() => window.scrollTo(0, 900));
  await page.waitForTimeout(400);
  log(await page.$eval('#sticky', e => e.classList.contains('on')), 'sticky CTA appears after scroll');

  /* ---------- QUIZ: QUALIFIED PATH ---------- */
  console.log('\n=== QUIZ — QUALIFIED PATH ===');
  await page.click('.sticky [data-cta]');
  await page.waitForURL('**/quiz.html', { timeout: 5000 });
  log(true, 'CTA navigates to quiz');

  log((await page.textContent('#stepNum')).includes('Step 1 / 8'), '8 steps built from config');

  await page.click('#scr-0 .opt');                       // step 1: Homeowner
  await page.waitForTimeout(150);
  await page.click('#scr-1 .opt');                       // step 2: Full kitchen remodel
  await page.waitForTimeout(150);

  log((await page.textContent('#stepNum')).includes('Step 3 / 8'), 'reached contact step at 3 of 8');

  let before = (await hits()).length;
  log(before === 0, 'no webhook fired before contact captured');

  // fill contact
  await page.fill('#scr-2 input[type=text]', 'Nathan');
  await page.fill('#scr-2 input[type=tel]', '8085551234');
  await page.fill('#scr-2 input[type=email]', 'nathan@example.com');
  await page.click('#scr-2 .btn');
  await page.waitForTimeout(800);

  const afterContact = await hits();
  log(afterContact.length === 1, `PARTIAL webhook fired at step 3 (${afterContact.length} hit)`);
  if (afterContact.length) {
    const p = afterContact[0];
    log(p.completion === 'partial', `  completion === "partial" (got "${p.completion}")`);
    log(p.lead_status === 'Partial', `  lead_status === "Partial" (got "${p.lead_status}")`);
    log(p.first_name === 'Nathan', `  first_name captured (got "${p.first_name}")`);
    log(p.phone === '+18085551234', `  phone with country code (got "${p.phone}")`);
    log(p.email === 'nathan@example.com', `  email captured — not "" (got "${p.email}")`);
    log(p.utm && p.utm.utm_campaign && p.utm.utm_campaign.includes('WINNERS'),
        `  UTM carried through (campaign: ${p.utm && p.utm.utm_campaign})`);
    log(!!p.event_id, `  event_id present for CAPI dedup (${p.event_id})`);
  }

  // steps 4-8
  await page.click('#scr-3 .opt');                       // timeline: ASAP
  await page.waitForTimeout(150);
  await page.fill('#scr-4 textarea', 'Galley kitchen about 12 linear feet, want shaker in white oak.');
  await page.click('#scr-4 .btn');
  await page.waitForTimeout(150);

  const sliderVal = await page.textContent('#scr-5 .slider-val');
  log(sliderVal.trim() === '25 linear ft', `slider anchored at 25, not 0 (got "${sliderVal}")`);
  await page.click('#scr-5 .btn');
  await page.waitForTimeout(150);

  await page.fill('#scr-6 textarea', 'Every quote so far has been ten weeks out and over budget.');
  await page.click('#scr-6 .btn');
  await page.waitForTimeout(150);

  const dq = await page.$eval('#scr-7 .opt.dq .opt-s', e => e.textContent);
  log(dq.includes("don't book"), `self-selecting disqualifier labelled (got "${dq}")`);

  // pick a qualifying band
  await page.click('#scr-7 .opts .opt:nth-child(3)');    // $15k-35k
  await page.waitForTimeout(1600);

  log(await page.$eval('#scr-win', e => e.classList.contains('on')), 'qualified -> booking screen');

  const calSrc = await page.$eval('#calHost iframe', e => e.src).catch(() => '');
  log(calSrc.includes('first_name=Nathan'), 'calendar prefilled with name');
  log(calSrc.includes('email=nathan%40example.com'), 'calendar prefilled with email');

  const all = await hits();
  log(all.length === 2, `COMPLETE webhook fired (total ${all.length} hits: partial + complete)`);
  const c = all[1];
  if (c) {
    log(c.completion === 'complete', `  completion === "complete"`);
    log(c.qualified === 'yes', `  qualified === "yes"`);
    log(c.lead_status === 'Qualified', `  lead_status === "Qualified"`);
    log(c.challenge && c.challenge.includes('ten weeks'), `  challenge free-text captured`);
    log(c.size === '25 linear ft', `  slider value captured (got "${c.size}")`);
  }

  /* ---------- PIXEL DEDUPE ---------- */
  console.log('\n=== PIXEL DISCIPLINE ===');
  const fired = await page.evaluate(() => {
    const keys = ['_fnl_appstart', '_fnl_apppartial', '_fnl_appcomplete'];
    return keys.map(k => k + '=' + sessionStorage.getItem(k));
  });
  log(fired.every(f => f.endsWith('=1')), 'each funnel event marked fired exactly once: ' + fired.join(', '));

  // Re-calling applicationComplete must be a no-op (the double-fire bug).
  const second = await page.evaluate(() => window.Track.applicationComplete({ qualified: true }));
  log(second === false, 'second applicationComplete() call is suppressed (no double Lead)');

  /* ---------- QUIZ: DISQUALIFIED PATH ---------- */
  console.log('\n=== QUIZ — DISQUALIFIED PATH ===');
  const page2 = await ctx.newPage();
  page2.on('pageerror', e => errors.push(String(e)));
  await page2.goto(BASE + '/quiz.html', { waitUntil: 'networkidle' });

  await page2.click('#scr-0 .opt'); await page2.waitForTimeout(120);
  await page2.click('#scr-1 .opt'); await page2.waitForTimeout(120);
  await page2.fill('#scr-2 input[type=text]', 'Kai');
  await page2.fill('#scr-2 input[type=tel]', '8085559999');
  await page2.fill('#scr-2 input[type=email]', 'kai@example.com');
  await page2.click('#scr-2 .btn'); await page2.waitForTimeout(500);
  await page2.click('#scr-3 .opt'); await page2.waitForTimeout(120);
  await page2.fill('#scr-4 textarea', 'Small rental kitchen, six linear feet.');
  await page2.click('#scr-4 .btn'); await page2.waitForTimeout(120);
  await page2.click('#scr-5 .btn'); await page2.waitForTimeout(120);
  await page2.fill('#scr-6 textarea', 'Budget is very tight on this rental unit.');
  await page2.click('#scr-6 .btn'); await page2.waitForTimeout(120);
  await page2.click('#scr-7 .opt.dq');                   // Under $5k
  await page2.waitForTimeout(1600);

  log(await page2.$eval('#scr-soft', e => e.classList.contains('on')), 'disqualified -> soft decline screen');

  const softHref = await page2.$eval('#softCta', e => e.getAttribute('href'));
  log(softHref && softHref !== '#', `decline CTA points somewhere real (got "${softHref}")`);

  const dqHits = await hits();
  const last = dqHits[dqHits.length - 1];
  log(last.qualified === 'no', 'disqualified payload marked qualified="no"');
  log(last.lead_status === 'Nurture', 'disqualified payload lead_status="Nurture"');
  log(dqHits.filter(h => h.first_name === 'Kai').length === 2,
      'disqualified visitor STILL produced partial + complete (contact retained)');

  /* ---------- VALIDATION ---------- */
  console.log('\n=== VALIDATION ===');
  const page3 = await ctx.newPage();
  await page3.goto(BASE + '/quiz.html', { waitUntil: 'networkidle' });
  await page3.click('#scr-0 .opt'); await page3.waitForTimeout(120);
  await page3.click('#scr-1 .opt'); await page3.waitForTimeout(120);
  const hitsBeforeBad = (await hits()).length;
  await page3.click('#scr-2 .btn');                      // submit empty
  await page3.waitForTimeout(400);
  log((await hits()).length === hitsBeforeBad, 'empty contact form does NOT fire a webhook');
  log(await page3.$eval('#scr-2 .err', e => e.classList.contains('on')), 'validation errors shown');
  await page3.fill('#scr-2 input[type=text]', 'Test');
  await page3.fill('#scr-2 input[type=tel]', '8085551111');
  await page3.fill('#scr-2 input[type=email]', 'not-an-email');
  await page3.click('#scr-2 .btn'); await page3.waitForTimeout(300);
  log((await page3.textContent('#stepNum')).includes('Step 3 / 8'), 'bad email blocks advance');

  console.log('\n=== JS ERRORS ===');
  const real = errors.filter(e => !/favicon|ERR_|net::|leadconnector|form_embed/i.test(e));
  log(real.length === 0, real.length ? 'errors: ' + real.join(' | ') : 'no page errors');

  await browser.close();
  console.log(process.exitCode ? '\nSOME CHECKS FAILED\n' : '\nALL CHECKS PASSED\n');
})();
