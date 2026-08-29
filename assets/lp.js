/* ============================================================================
   LANDING PAGE
   Renders entirely from window.FUNNEL_CONFIG. No copy is hardcoded here.
   ========================================================================== */

(function (window, document) {
  'use strict';

  var CFG = window.FUNNEL_CONFIG;
  if (!CFG) { console.error('[lp] config.js did not load'); return; }

  var LP = CFG.lp, B = CFG.brand;
  var $  = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return [].slice.call((r || document).querySelectorAll(s)); };

  function text(sel, val) { var el = $(sel); if (el) el.textContent = val || ''; }

  /* ---- header, hero ---------------------------------------------------- */

  text('#urgency', LP.urgencyBar);

  var logo = $('#logo');
  if (logo) {
    logo.textContent = B.name;
    if (B.tagline) {
      var s = document.createElement('span');
      s.textContent = B.tagline;
      logo.appendChild(s);
    }
  }

  var r = LP.rating || {};
  var rt = $('#rating');
  if (rt && r.score) {
    rt.innerHTML = '<span class="stars">' + '★'.repeat(r.stars || 5) + '</span>' +
                   '<span>' + r.score + (r.count ? ' · ' + r.count : '') + '</span>';
  }

  text('#headline', LP.headline);
  text('#subhead',  LP.subhead);
  text('#diff',     LP.differentiator);

  /* ---- step rail ------------------------------------------------------- */

  var stepsEl = $('#steps');
  if (stepsEl) {
    (LP.steps || []).forEach(function (name, i) {
      var d = document.createElement('div');
      d.className = 'step' + (i === 0 ? ' on' : '');
      d.innerHTML =
        '<div class="step-n">' + (i + 1) + '</div>' +
        '<div><span class="step-label">Step ' + (i + 1) + ' of ' + LP.steps.length + '</span>' +
        '<span class="step-name"></span></div>';
      $('.step-name', d).textContent = name;
      stepsEl.appendChild(d);
    });
  }

  /* ---- video ----------------------------------------------------------- */

  (function renderVideo() {
    var v = LP.video || {}, host = $('#vid-inner');
    if (!host) return;

    if (!v.type || v.type === 'none' || !v.id) {
      // Keep the slot visible so the layout is honest about what's missing.
      host.innerHTML = '<div class="vid-placeholder"><div>' +
        '<strong>Video slot</strong><br>Set <code>lp.video</code> in <code>config.js</code>' +
        '</div></div>';
      return;
    }

    if (v.type === 'youtube') {
      host.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' +
        encodeURIComponent(v.id) + '?rel=0" title="' + (v.posterAlt || 'Video') +
        '" allow="accelerometer; encrypted-media; picture-in-picture" allowfullscreen></iframe>';

    } else if (v.type === 'vimeo') {
      host.innerHTML = '<iframe src="https://player.vimeo.com/video/' +
        encodeURIComponent(v.id) + '" title="' + (v.posterAlt || 'Video') +
        '" allow="autoplay; fullscreen; picture-in-picture" allowfullscreen></iframe>';

    } else if (v.type === 'vidalytics') {
      // Vidalytics ships its own loader; give it the mount node it expects.
      var mount = document.createElement('div');
      mount.id = 'vidalytics_embed_' + v.id;
      mount.style.cssText = 'width:100%;position:relative;padding-top:56.25%';
      host.appendChild(mount);
      var s = document.createElement('script');
      s.async = true;
      s.src = 'https://fast.vidalytics.com/embeds/' + encodeURIComponent(v.id) + '/loader.min.js';
      document.head.appendChild(s);
    }
  })();

  /* ---- CTAs -----------------------------------------------------------
     One destination, every button. The friction-killer renders under all
     of them from a single config value so they can never drift apart.
     -------------------------------------------------------------------- */

  $$('[data-cta]').forEach(function (btn, i) {
    btn.textContent = i === 0 ? (LP.ctaPrimary || 'Book Now →')
                              : (LP.ctaSecondary || LP.ctaPrimary || 'Book Now →');
    btn.addEventListener('click', goToQuiz);
  });

  $$('[data-cta-meta]').forEach(function (el) { el.textContent = LP.ctaMeta || ''; });

  function goToQuiz() {
    // Soft signal only. Meta's standard Lead event deliberately does NOT
    // fire here — a click is not a lead, and firing it twice was the
    // measurement bug this build exists to avoid.
    if (window.Track) window.Track.applicationStart();

    // Full navigation rather than a modal iframe: nested third-party
    // iframes are the single most common reason these funnels break.
    window.location.href = B.quizUrl || '/quiz.html';
  }

  /* ---- stat counters --------------------------------------------------- */

  (function renderStats() {
    var host = $('#stats');
    if (!host) return;

    (LP.stats || []).forEach(function (st) {
      var d = document.createElement('div');
      d.className = 'stat';
      d.innerHTML = '<div class="stat-n">' + (st.prefix || '') + '0' + (st.suffix || '') + '</div>' +
                    '<div class="stat-l"></div>';
      $('.stat-l', d).textContent = st.label;
      $('.stat-n', d).setAttribute('data-target', st.target);
      $('.stat-n', d).setAttribute('data-prefix', st.prefix || '');
      $('.stat-n', d).setAttribute('data-suffix', st.suffix || '');
      host.appendChild(d);
    });

    var nodes = $$('.stat-n', host);
    if (!nodes.length) return;

    function run(el) {
      var target = parseFloat(el.getAttribute('data-target')) || 0;
      var pre = el.getAttribute('data-prefix') || '';
      var suf = el.getAttribute('data-suffix') || '';
      var dur = 1100, t0 = null;

      function frame(ts) {
        if (t0 === null) t0 = ts;
        var p = Math.min((ts - t0) / dur, 1);
        var eased = 1 - Math.pow(1 - p, 3);
        var val = Math.round(target * eased);
        el.textContent = pre + val.toLocaleString() + suf;
        if (p < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    }

    if (!('IntersectionObserver' in window)) { nodes.forEach(run); return; }

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { run(e.target); io.unobserve(e.target); }
      });
    }, { threshold: 0.4 });

    nodes.forEach(function (n) { io.observe(n); });
  })();

  /* ---- proof gallery --------------------------------------------------- */

  var images = (LP.gallery && LP.gallery.images) || [];

  text('#gal-h',    LP.gallery && LP.gallery.heading);
  text('#gal-sub',  LP.gallery && LP.gallery.subheading);
  text('#gal-note', LP.gallery && LP.gallery.note);

  (function renderGallery() {
    var grid = $('#grid');
    if (!grid) return;

    if (!images.length) {
      grid.className = 'gallery-empty';
      grid.innerHTML = 'No proof images yet. Add photo URLs to ' +
                       '<code>lp.gallery.images</code> in <code>config.js</code>.';
      return;
    }

    images.forEach(function (src, i) {
      var fig = document.createElement('figure');
      var img = document.createElement('img');
      img.src = src;
      img.loading = 'lazy';
      img.alt = 'Completed project ' + (i + 1);
      fig.appendChild(img);
      fig.addEventListener('click', function () { openLb(i); });
      grid.appendChild(fig);
    });
  })();

  /* ---- lightbox -------------------------------------------------------- */

  var lb = $('#lb'), lbImg = $('#lbImg'), lbCount = $('#lbCount'), idx = 0;

  function openLb(i) { idx = i; paintLb(); lb.classList.add('on'); document.body.style.overflow = 'hidden'; }
  function closeLb()  { lb.classList.remove('on'); document.body.style.overflow = ''; }
  function navLb(d)   { if (!images.length) return; idx = (idx + d + images.length) % images.length; paintLb(); }
  function paintLb()  {
    lbImg.src = images[idx];
    lbImg.alt = 'Completed project ' + (idx + 1);
    lbCount.textContent = (idx + 1) + ' / ' + images.length;
  }

  if (lb) {
    $('#lbClose').addEventListener('click', closeLb);
    $('#lbPrev').addEventListener('click', function (e) { e.stopPropagation(); navLb(-1); });
    $('#lbNext').addEventListener('click', function (e) { e.stopPropagation(); navLb(1); });
    lb.addEventListener('click', function (e) { if (e.target === lb) closeLb(); });

    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('on')) return;
      if (e.key === 'Escape') closeLb();
      if (e.key === 'ArrowLeft') navLb(-1);
      if (e.key === 'ArrowRight') navLb(1);
    });

    // Swipe on touch devices.
    var sx = null;
    lb.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; }, { passive: true });
    lb.addEventListener('touchend', function (e) {
      if (sx === null) return;
      var dx = e.changedTouches[0].clientX - sx;
      if (Math.abs(dx) > 40) navLb(dx < 0 ? 1 : -1);
      sx = null;
    }, { passive: true });
  }

  /* ---- closing section, footer, sticky bar ----------------------------- */

  text('#close-h',    LP.close && LP.close.heading);
  text('#close-sub',  LP.close && LP.close.subheading);
  text('#close-body', LP.close && LP.close.body);

  text('#foot-copy', '© ' + (B.year || new Date().getFullYear()) + ' ' + B.name + '. All rights reserved.');
  text('#foot-disc', LP.disclaimer);

  (function stickyBar() {
    var el = $('#sticky');
    if (!el) return;
    var shown = false;
    window.addEventListener('scroll', function () {
      var y = window.scrollY || window.pageYOffset;
      if (!shown && y > 480) { shown = true; el.classList.add('on'); }
      else if (shown && y <= 480) { shown = false; el.classList.remove('on'); }
    }, { passive: true });
  })();

})(window, document);
