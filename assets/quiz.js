/* ============================================================================
   QUIZ ENGINE
   ----------------------------------------------------------------------------
   The whole point of this file is the partial capture.

   Contact details are collected at the step marked `type: 'contact'` — placed
   at 3 of 8 in config, BEFORE any qualifying question. The moment that step
   submits, a webhook fires with completion:"partial". Everyone who abandons
   at steps 4-8 is therefore still a reachable contact in the CRM instead of
   lost traffic. In a typical application funnel that is 40-70% of entrants.

   Only ONE question changes routing: the step whose selected option carries
   `disqualify: true`. Every other question exists to build commitment and to
   hand whoever takes the call their script before the call starts.
   ========================================================================== */

(function (window, document) {
  'use strict';

  var CFG = window.FUNNEL_CONFIG;
  if (!CFG) { console.error('[quiz] config.js did not load'); return; }

  var Q = CFG.quiz, B = CFG.brand;
  var STEPS = Q.steps || [];
  var TOTAL = STEPS.length;

  var $ = function (s, r) { return (r || document).querySelector(s); };

  var answers = {};      // key -> value
  var current = 0;       // index into STEPS
  var partialSent = false;

  /* ---- utilities -------------------------------------------------------- */

  function el(tag, cls, txt) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (txt != null) n.textContent = txt;
    return n;
  }

  function text(sel, val) { var n = $(sel); if (n) n.textContent = val || ''; }

  function validEmail(v) { return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v); }

  // Deliberately permissive: 7+ digits after stripping formatting. Over-strict
  // phone validation rejects real numbers and costs more leads than it saves.
  function validPhone(v) { return (String(v).replace(/\D/g, '').length >= 7); }

  /* ---- webhook ---------------------------------------------------------
     `keepalive` lets the request finish even as the screen changes or the
     user navigates away — without it, partials are lost exactly when they
     matter most.
     -------------------------------------------------------------------- */

  function post(payload) {
    var urls = (CFG.webhooks || []).filter(Boolean);
    if (!urls.length) {
      console.warn('[quiz] no webhooks configured — payload not sent:', payload);
      return Promise.resolve();
    }
    return Promise.all(urls.map(function (url) {
      return fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        keepalive: true
      }).catch(function (e) { console.warn('[quiz] webhook failed', url, e); });
    }));
  }

  function buildPayload(completion, qualified) {
    var p = {
      // identity
      first_name: answers.firstName || '',
      full_name:  answers.firstName || '',
      phone:      answers.phone || '',
      email:      answers.email || '',

      // meta
      completion:  completion,                            // 'partial' | 'complete'
      lead_status: completion === 'partial' ? 'Partial'
                                            : (qualified ? 'Qualified' : 'Nurture'),
      qualified:   completion === 'complete' ? (qualified ? 'yes' : 'no') : '',
      source:      'Design Call Quiz',
      // Shared with the browser pixel so a server-side Conversions API call
      // reporting the same event can be deduplicated against it.
      event_id:    window.Track ? window.Track.eventId('Lead') : '',
      submitted_at: new Date().toISOString(),

      // attribution — carried from the ad click through to the CRM record
      utm: utmParams()
    };

    // Every answered question, keyed as configured.
    STEPS.forEach(function (s) {
      if (s.type === 'contact') return;
      p[s.key] = answers[s.key] != null ? answers[s.key] : '';
    });

    return p;
  }

  /* ---- attribution ------------------------------------------------------
     Captured by tracking.js on the LANDING page (where the ad's UTMs
     actually land) and persisted across the navigation to this page. Read
     it here and attach to both webhook fires, so the CRM record knows which
     campaign, ad set and ad produced the lead.
     -------------------------------------------------------------------- */

  function utmParams() {
    return window.Track && window.Track.utm ? window.Track.utm() : {};
  }

  /* ---- screen rendering -------------------------------------------------- */

  var host = $('#screens');

  function head(step, i) {
    var f = document.createDocumentFragment();
    if (step.eyebrow) f.appendChild(el('div', 'eyebrow', step.eyebrow));
    f.appendChild(el('h2', 'q', step.question));
    if (step.help) f.appendChild(el('p', 'q-help', step.help));
    return f;
  }

  function backRow(i, onNext, nextLabel) {
    var row = el('div', 'nav-row');
    if (onNext) {
      var b = el('button', 'btn', nextLabel || 'Continue →');
      b.type = 'button';
      b.addEventListener('click', onNext);
      row.appendChild(b);
    }
    if (i > 0) {
      var back = el('button', 'back', '← Back');
      back.type = 'button';
      back.addEventListener('click', function () { go(i - 1); });
      row.appendChild(back);
    }
    return row;
  }

  function renderChoice(step, i, scr) {
    var wrap = el('div', 'opts');

    (step.options || []).forEach(function (opt) {
      var b = el('button', 'opt' + (opt.disqualify ? ' dq' : ''));
      b.type = 'button';
      if (opt.icon) b.appendChild(el('span', 'opt-icon', opt.icon));

      var body = el('span');
      body.appendChild(el('span', 'opt-t', opt.label));
      if (opt.sub) body.appendChild(el('span', 'opt-s', opt.sub));
      b.appendChild(body);

      b.addEventListener('click', function () {
        answers[step.key] = opt.value || opt.label;
        answers['_dq_' + step.key] = !!opt.disqualify;

        // Selecting advances immediately — no extra Continue click. Fewer
        // taps to the contact step means more contacts captured.
        if (i === TOTAL - 1) finish(); else go(i + 1);
      });

      wrap.appendChild(b);
    });

    scr.appendChild(wrap);
    if (step.footnote) scr.appendChild(el('div', 'footnote', step.footnote));
    scr.appendChild(backRow(i, null));
  }

  function renderText(step, i, scr) {
    var field = el('div', 'field');
    var ta = document.createElement('textarea');
    ta.placeholder = step.placeholder || '';
    ta.id = 'ta_' + step.key;
    field.appendChild(ta);
    var err = el('div', 'err', step.error || 'Please add a little more detail.');
    field.appendChild(err);
    scr.appendChild(field);

    scr.appendChild(backRow(i, function () {
      var v = ta.value.trim();
      if (v.length < (step.minLength || 1)) {
        field.classList.add('bad'); err.classList.add('on'); ta.focus();
        return;
      }
      field.classList.remove('bad'); err.classList.remove('on');
      answers[step.key] = v;
      if (i === TOTAL - 1) finish(); else go(i + 1);
    }));
  }

  function renderSlider(step, i, scr) {
    // Anchored at `default`, never at zero — the starting position becomes
    // the reference point the prospect adjusts away from.
    var start = step.default != null ? step.default : Math.round(((step.min || 0) + (step.max || 100)) / 2);
    answers[step.key] = start + (step.unit || '');

    var val = el('div', 'slider-val', start + (step.unit || ''));
    scr.appendChild(val);

    var input = document.createElement('input');
    input.type = 'range';
    input.min = step.min != null ? step.min : 0;
    input.max = step.max != null ? step.max : 100;
    input.step = step.step || 1;
    input.value = start;
    input.setAttribute('aria-label', step.question);
    scr.appendChild(input);

    var ends = el('div', 'slider-ends');
    ends.appendChild(el('span', null, (step.min != null ? step.min : 0) + (step.unit || '')));
    ends.appendChild(el('span', null, step.maxLabel || ((step.max != null ? step.max : 100) + (step.unit || ''))));
    scr.appendChild(ends);

    input.addEventListener('input', function () {
      var v = input.value + (step.unit || '');
      val.textContent = v;
      answers[step.key] = v;
    });

    scr.appendChild(backRow(i, function () {
      if (i === TOTAL - 1) finish(); else go(i + 1);
    }));
  }

  /* ---- THE MONEY STEP ---------------------------------------------------
     Name, phone and email — captured before any qualifying question.
     Submitting fires the partial webhook.
     -------------------------------------------------------------------- */

  function renderContact(step, i, scr) {
    var f = step.fields || {};
    var codes = step.countryCodes || [{ flag: '🇺🇸', code: '+1', label: 'US' }];

    // first name
    var fName = el('div', 'field');
    fName.appendChild(el('label', null, f.firstNameLabel || 'First name'));
    var inName = document.createElement('input');
    inName.type = 'text'; inName.autocomplete = 'given-name';
    fName.appendChild(inName);
    var eName = el('div', 'err', f.firstNameError || 'Enter your first name.');
    fName.appendChild(eName);
    scr.appendChild(fName);

    // phone
    var fPhone = el('div', 'field');
    fPhone.appendChild(el('label', null, f.phoneLabel || 'Best phone number'));
    var row = el('div', 'phone-row');
    var sel = document.createElement('select');
    codes.forEach(function (c) {
      var o = document.createElement('option');
      o.value = c.code;
      o.textContent = c.flag + ' ' + (c.code || c.label);
      sel.appendChild(o);
    });
    var inPhone = document.createElement('input');
    inPhone.type = 'tel'; inPhone.autocomplete = 'tel'; inPhone.inputMode = 'tel';
    row.appendChild(sel); row.appendChild(inPhone);
    fPhone.appendChild(row);
    var ePhone = el('div', 'err', f.phoneError || 'Enter a valid phone number.');
    fPhone.appendChild(ePhone);
    scr.appendChild(fPhone);

    // email — the reference funnel hardcoded this to "" and had no email
    // nurture path at all. Capturing it here is the fix.
    var fMail = el('div', 'field');
    fMail.appendChild(el('label', null, f.emailLabel || 'Email'));
    var inMail = document.createElement('input');
    inMail.type = 'email'; inMail.autocomplete = 'email';
    fMail.appendChild(inMail);
    var eMail = el('div', 'err', f.emailError || 'Enter a valid email address.');
    fMail.appendChild(eMail);
    scr.appendChild(fMail);

    // Objection handling disguised as a help tooltip.
    if (step.whyLabel) {
      var det = document.createElement('details');
      det.className = 'why';
      var sum = document.createElement('summary');
      sum.textContent = step.whyLabel;
      det.appendChild(sum);
      det.appendChild(el('p', null, step.whyBody || ''));
      scr.appendChild(det);
    }

    if (step.consent) scr.appendChild(el('div', 'consent', step.consent));

    scr.appendChild(backRow(i, function () {
      var ok = true;

      function mark(field, errEl, good) {
        field.classList.toggle('bad', !good);
        errEl.classList.toggle('on', !good);
        if (!good) ok = false;
      }

      mark(fName,  eName,  inName.value.trim().length > 0);
      mark(fPhone, ePhone, validPhone(inPhone.value));
      mark(fMail,  eMail,  f.emailRequired === false
                            ? (!inMail.value.trim() || validEmail(inMail.value.trim()))
                            : validEmail(inMail.value.trim()));

      if (!ok) return;

      answers.firstName = inName.value.trim();
      answers.phone     = (sel.value || '') + inPhone.value.trim();
      answers.email     = inMail.value.trim();

      sendPartial();
      go(i + 1);
    }, 'Continue →'));
  }

  /* ---- the partial fire -------------------------------------------------- */

  function sendPartial() {
    if (partialSent) return;
    partialSent = true;

    post(buildPayload('partial', null));
    if (window.Track) window.Track.applicationPartial({ step: current + 1 });
  }

  /* ---- build all screens ------------------------------------------------- */

  STEPS.forEach(function (step, i) {
    var scr = el('section', 'screen');
    scr.id = 'scr-' + i;
    scr.appendChild(head(step, i));

    if (step.type === 'contact')      renderContact(step, i, scr);
    else if (step.type === 'text')    renderText(step, i, scr);
    else if (step.type === 'slider')  renderSlider(step, i, scr);
    else                              renderChoice(step, i, scr);

    host.appendChild(scr);
  });

  /* ---- navigation -------------------------------------------------------- */

  function hideAll() {
    [].slice.call(document.querySelectorAll('.screen')).forEach(function (s) {
      s.classList.remove('on');
    });
  }

  function go(i) {
    current = i;
    hideAll();
    var scr = $('#scr-' + i);
    if (scr) scr.classList.add('on');
    paintProgress();
    window.scrollTo({ top: 0, behavior: 'smooth' });

    var first = scr && scr.querySelector('input, textarea');
    if (first && window.matchMedia('(min-width: 700px)').matches) first.focus();
  }

  function show(id) {
    hideAll();
    var scr = $('#scr-' + id);
    if (scr) scr.classList.add('on');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function paintProgress() {
    $('#progFill').style.width = (((current + 1) / TOTAL) * 100) + '%';
    text('#stepNum', 'Step ' + (current + 1) + ' / ' + TOTAL);
  }

  /* ---- completion --------------------------------------------------------
     The gate: qualified unless the selected option on any step was flagged
     `disqualify: true`.
     -------------------------------------------------------------------- */

  function finish() {
    var qualified = !STEPS.some(function (s) { return answers['_dq_' + s.key]; });

    // A person who reaches here without passing the contact step (possible
    // only if config puts contact last) still needs their partial recorded.
    sendPartial();

    $('#loader').classList.add('on');

    post(buildPayload('complete', qualified));

    // The single Lead event for this session. Never fires on a click,
    // never fires twice.
    if (window.Track) {
      window.Track.applicationComplete({
        qualified: qualified,
        project:   answers.project || '',
        timeline:  answers.timeline || '',
        budget:    answers.budget || ''
      });
    }

    window.setTimeout(function () {
      $('#loader').classList.remove('on');
      $('#progFill').style.width = '100%';
      if (qualified) { mountCalendar(); show('win'); }
      else           { show('soft'); }
    }, 900);
  }

  /* ---- calendar ----------------------------------------------------------
     Prefilled from the contact step so the booking form arrives populated.
     Several parameter aliases are passed because widget providers differ in
     which key they read.
     -------------------------------------------------------------------- */

  function mountCalendar() {
    var host = $('#calHost');
    var url = (CFG.booking && CFG.booking.calendarUrl) || '';

    if (!url) {
      host.innerHTML = '<div class="cal-missing">Booking calendar not configured. ' +
                       'Set <code>booking.calendarUrl</code> in <code>config.js</code>.</div>';
      return;
    }

    var fn = answers.firstName || '', ph = answers.phone || '', em = answers.email || '';
    var p = new URLSearchParams({
      first_name: fn, firstName: fn,
      name: fn, full_name: fn,
      phone: ph,
      email: em
    });

    var frame = document.createElement('iframe');
    frame.className = 'cal-frame';
    frame.src = url + (url.indexOf('?') > -1 ? '&' : '?') + p.toString();
    frame.title = 'Booking calendar';
    host.innerHTML = '';
    host.appendChild(frame);

    // The provider's embed script enables resize + booking messages.
    // tracking.js listens for those messages to fire the Schedule event.
    if (/leadconnectorhq\.com/.test(url) && !window.__ghlEmbedLoaded) {
      window.__ghlEmbedLoaded = true;
      var s = document.createElement('script');
      s.src = 'https://api.leadconnectorhq.com/js/form_embed.js';
      s.async = true;
      document.body.appendChild(s);
    }
  }

  /* ---- static copy ------------------------------------------------------- */

  (function paintStatic() {
    var logo = $('#logo');
    if (logo) {
      logo.textContent = B.name;
      if (B.tagline) { var s = el('span', null, B.tagline); logo.appendChild(s); }
    }

    text('#quizTitle', Q.title);

    text('#winH',    Q.win && Q.win.heading);
    text('#winBody', Q.win && Q.win.body);
    text('#winMeta', Q.win && Q.win.meta);

    text('#softH',     Q.soft && Q.soft.heading);
    text('#softBody',  Q.soft && Q.soft.body);
    text('#softBody2', Q.soft && Q.soft.bodyTwo);
    text('#softMeta',  Q.soft && Q.soft.ctaMeta);

    var sc = $('#softCta');
    if (sc && Q.soft) {
      sc.textContent = Q.soft.ctaLabel || 'Learn more →';
      // Their version shipped this as href="#", dead-ending every
      // disqualified visitor. Only render a live link if one is configured.
      if (Q.soft.ctaUrl && Q.soft.ctaUrl !== '#') {
        sc.href = Q.soft.ctaUrl;
      } else {
        sc.href = '#';
        sc.setAttribute('aria-disabled', 'true');
        console.warn('[quiz] quiz.soft.ctaUrl is not set — disqualified traffic has nowhere to go.');
      }
    }

    text('#foot-copy', '© ' + (B.year || new Date().getFullYear()) + ' ' + B.name + '. All rights reserved.');
    text('#foot-disc', (CFG.lp && CFG.lp.disclaimer) || '');
  })();

  go(0);

})(window, document);
