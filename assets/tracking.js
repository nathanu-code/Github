/* ============================================================================
   TRACKING LAYER
   ----------------------------------------------------------------------------
   Fixes the three measurement defects found in the teardown:

     1. Lead double-fire. The reference funnel fired fbq('track','Lead') on the
        landing-page CTA click AND again on quiz completion, so one person
        generated two Leads, and a click-then-bounce generated one. Here Lead
        fires exactly once per session, at completion, and never on a click.

     2. No Schedule event. The reference funnel ran a campaign named SCHEDULE
        with no Schedule event anywhere in its code. Here a real Schedule event
        fires when the booking iframe reports a confirmed appointment.

     3. Google Ads tag with no conversion. gtag('config') alone records nothing.
        Here a conversion event fires on booking, provided a conversion label
        is set in config.

   Every function no-ops safely when the matching ID is absent from config.
   ========================================================================== */

(function (window, document) {
  'use strict';

  var CFG = (window.FUNNEL_CONFIG || {});
  var T = CFG.tracking || {};

  /* ---- once-only guard -------------------------------------------------
     sessionStorage survives the LP -> quiz navigation, which is what makes
     cross-page dedupe possible at all. It throws in some privacy modes, so
     an in-memory set backs it up (correct within a page, which is the case
     that matters for a double-bound click handler).
     -------------------------------------------------------------------- */
  var memo = {};

  function alreadyFired(key) {
    if (memo[key]) return true;
    try {
      if (window.sessionStorage.getItem(key)) return true;
    } catch (e) { /* storage blocked — fall through to memo only */ }
    return false;
  }

  function markFired(key) {
    memo[key] = true;
    try { window.sessionStorage.setItem(key, '1'); } catch (e) {}
  }

  function once(key, fn) {
    if (alreadyFired(key)) return false;
    markFired(key);
    try { fn(); } catch (e) { warn('handler failed for ' + key, e); }
    return true;
  }

  function warn() {
    if (window.console && console.warn) {
      console.warn.apply(console, ['[tracking]'].concat([].slice.call(arguments)));
    }
  }

  /* ---- session id ------------------------------------------------------
     Shared between the browser pixel and any server-side Conversions API
     call so Meta can deduplicate the two reports of the same event.
     Pass the same value as `event_id` from your CRM workflow.
     -------------------------------------------------------------------- */
  function sessionId() {
    var k = '_fnl_sid';
    var v;
    try { v = window.sessionStorage.getItem(k); } catch (e) {}
    if (!v) {
      v = 's' + Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
      try { window.sessionStorage.setItem(k, v); } catch (e) {}
    }
    return v;
  }

  function eventId(name) { return name + '.' + sessionId(); }

  /* ---- attribution -----------------------------------------------------
     MUST run on the landing page, not just the quiz: the ad click lands on
     the LP carrying the UTMs, and the navigation to the quiz drops them.
     Capturing here (this file loads on both pages) and persisting to
     sessionStorage is what carries campaign / ad set / ad identity all the
     way into the CRM record.
     -------------------------------------------------------------------- */

  var UTM_KEYS = [
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term', 'utm_id',
    'campaign_id', 'medium_id', 'content_id', 'fbclid', 'gclid', 'ttclid', 'li_fat_id'
  ];

  function captureUtm() {
    var store = {};
    try { store = JSON.parse(window.sessionStorage.getItem('_fnl_utm') || '{}') || {}; } catch (e) {}

    var qs;
    try { qs = new URLSearchParams(window.location.search); } catch (e) { return store; }

    var changed = false;
    UTM_KEYS.forEach(function (k) {
      var v = qs.get(k);
      // First touch wins: a later page load without params must not blank
      // out attribution already captured for this session.
      if (v && !store[k]) { store[k] = v; changed = true; }
    });

    if (changed || !store._landed_at) {
      if (!store._landed_at) store._landed_at = new Date().toISOString();
      if (!store._landing_page) store._landing_page = window.location.pathname;
      try { window.sessionStorage.setItem('_fnl_utm', JSON.stringify(store)); } catch (e) {}
    }
    return store;
  }

  /* ---- platform bootstrap --------------------------------------------- */

  function initMeta() {
    if (!T.metaPixelId) return;
    /* eslint-disable */
    !function (f, b, e, v, n, t, s) {
      if (f.fbq) return; n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      };
      if (!f._fbq) f._fbq = n; n.push = n; n.loaded = !0; n.version = '2.0'; n.queue = [];
      t = b.createElement(e); t.async = !0; t.src = v;
      s = b.getElementsByTagName(e)[0]; s.parentNode.insertBefore(t, s);
    }(window, document, 'script', 'https://connect.facebook.net/en_US/fbevents.js');
    /* eslint-enable */
    window.fbq('init', T.metaPixelId);
    window.fbq('track', 'PageView');
  }

  function initGoogle() {
    if (!T.googleAdsId) return;
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + encodeURIComponent(T.googleAdsId);
    document.head.appendChild(s);
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', T.googleAdsId);
  }

  function initClarity() {
    if (!T.clarityId) return;
    /* eslint-disable */
    (function (c, l, a, r, i, t, y) {
      c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
      t = l.createElement(r); t.async = 1; t.src = 'https://www.clarity.ms/tag/' + i;
      y = l.getElementsByTagName(r)[0]; y.parentNode.insertBefore(t, y);
    })(window, document, 'clarity', 'script', T.clarityId);
    /* eslint-enable */
  }

  /* ---- event emitters --------------------------------------------------
     Naming mirrors the funnel stages so campaign optimization can target
     the real outcome (Schedule) rather than an upstream proxy.
     -------------------------------------------------------------------- */

  function meta(type, name, params, id) {
    if (typeof window.fbq !== 'function') return;
    try {
      window.fbq(type, name, params || {}, id ? { eventID: id } : undefined);
    } catch (e) { warn('fbq failed', name, e); }
  }

  var Track = {

    /* Fired when someone opens the quiz. A soft signal — deliberately NOT
       Meta's standard Lead event, so Lead stays clean for optimization. */
    applicationStart: function () {
      return once('_fnl_appstart', function () {
        meta('trackCustom', 'ApplicationStart', { funnel: 'design-call' });
      });
    },

    /* Fired the moment contact details are captured at step 3. This is the
       partial-capture signal: the person is reachable from here on, even if
       they never finish. Still not Lead — they have not qualified yet. */
    applicationPartial: function (data) {
      return once('_fnl_apppartial', function () {
        meta('trackCustom', 'ApplicationPartial', {
          funnel: 'design-call',
          step: (data && data.step) || 3
        });
      });
    },

    /* Fired once, at quiz completion. THIS is the single Lead event.
       It cannot fire from a button click, and it cannot fire twice. */
    applicationComplete: function (data) {
      return once('_fnl_appcomplete', function () {
        var d = data || {};
        var params = {
          qualified: d.qualified ? 'yes' : 'no',
          project: d.project || '',
          timeline: d.timeline || '',
          budget: d.budget || ''
        };
        meta('track', 'Lead', params, eventId('Lead'));
        meta('trackCustom', 'ApplicationComplete', params);
      });
    },

    /* Fired on a confirmed booking. The event the ad campaign should
       actually optimize toward. */
    schedule: function (detail) {
      return once('_fnl_schedule', function () {
        meta('track', 'Schedule', { content_name: 'design-call' }, eventId('Schedule'));

        if (typeof window.gtag === 'function' && T.googleAdsId) {
          if (T.googleAdsBookingLabel) {
            window.gtag('event', 'conversion', {
              send_to: T.googleAdsId + '/' + T.googleAdsBookingLabel
            });
          } else {
            warn('googleAdsId is set but googleAdsBookingLabel is empty — ' +
                 'no Google Ads conversion will be recorded. Add the label in config.js.');
          }
        }

        if (window.console && console.info) {
          console.info('[tracking] Schedule fired', detail || '');
        }
      });
    }
  };

  /* ---- booking listener ------------------------------------------------
     The booking calendar renders in a cross-origin iframe, so the parent
     page cannot see the confirmation directly — which is exactly why the
     reference funnel had no Schedule event at all. The widget does post a
     message on completion, so listen for it.

     IMPORTANT: the exact payload shape is provider-specific and versioned.
     This matcher is deliberately broad, and every message from the booking
     origin is logged to the console so you can confirm the real shape
     against a live test booking. See docs/ghl-setup.md — the server-side
     Conversions API path is the reliable backstop and should be configured
     regardless of whether this listener matches.
     -------------------------------------------------------------------- */

  var BOOKING_ORIGIN_RE = /(^|\.)(leadconnectorhq|msgsndr)\.com$/i;
  var BOOKED_RE = /(appointment|booking|booked|scheduled|slot_confirmed)/i;

  function listenForBooking() {
    window.addEventListener('message', function (e) {
      var host;
      try { host = new URL(e.origin).hostname; } catch (err) { return; }
      if (!BOOKING_ORIGIN_RE.test(host)) return;

      // Log every message from the booking widget — this is how you discover
      // the real event name to match on. Remove once confirmed.
      if (window.console && console.debug) {
        console.debug('[tracking] booking widget message:', e.data);
      }

      var d = e.data;
      var probe = '';
      if (typeof d === 'string') {
        probe = d;
      } else if (d && typeof d === 'object') {
        probe = [d.type, d.event, d.action, d.name, d.page].filter(Boolean).join(' ');
      }

      if (BOOKED_RE.test(String(probe))) Track.schedule(probe);
    }, false);
  }

  /* ---- boot ------------------------------------------------------------ */

  captureUtm();   // before anything else — the LP load is the only
                  // moment the ad's UTM parameters are present.
  initMeta();
  initGoogle();
  initClarity();
  listenForBooking();

  window.Track = Track;
  window.Track.eventId = eventId;
  window.Track.sessionId = sessionId;
  window.Track.utm = captureUtm;

})(window, document);
