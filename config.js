/* ============================================================================
   FUNNEL CONFIG — single source of truth for the landing page and the quiz.
   Edit this file to re-point the funnel at a different brand or offer.
   Nothing else needs to change.
   ========================================================================== */

window.FUNNEL_CONFIG = {

  /* ---- BRAND -------------------------------------------------------- */
  brand: {
    name: 'Grandeur Design Supply',
    shortName: 'Grandeur',
    tagline: 'Cabinetry & Design Supply',
    // Where the LP sends people who click any CTA.
    quizUrl: '/quiz.html',
    year: 2026
  },

  /* ---- TRACKING ------------------------------------------------------
     Leave any ID as an empty string to disable that platform entirely.
     The tracking layer no-ops cleanly on missing IDs.
     ------------------------------------------------------------------- */
  tracking: {
    metaPixelId: '',              // e.g. '123456789012345'
    googleAdsId: '',              // e.g. 'AW-123456789'
    // Google Ads conversion label for a booked call. Required for the
    // Google conversion to fire at all — the tag alone records nothing.
    googleAdsBookingLabel: '',    // e.g. 'AbC-D_efG-hIjKlMnOp'
    clarityId: ''                 // Microsoft Clarity project id
  },

  /* ---- WEBHOOKS ------------------------------------------------------
     Both the partial (step 3) and complete (step 8) payloads POST here.
     Branch inside your CRM workflow on the `completion` field.
     Add more than one URL to fan out.
     ------------------------------------------------------------------- */
  webhooks: [
    // 'https://services.leadconnectorhq.com/hooks/XXXX/webhook-trigger/YYYY'
  ],

  /* ---- BOOKING -------------------------------------------------------
     The calendar shown to qualified applicants. Contact details are
     appended as query params so the booking form arrives prefilled.
     ------------------------------------------------------------------- */
  booking: {
    calendarUrl: '',              // e.g. 'https://api.leadconnectorhq.com/widget/bookings/your-cal'
    durationLabel: '30 minutes'
  },

  /* ---- LANDING PAGE COPY --------------------------------------------- */
  lp: {
    urgencyBar: 'Now booking September installs — limited design slots',
    rating: { stars: 5, score: '4.9', count: '400+ Oahu kitchens' },

    // Stacks the three biggest objections into one line.
    headline: 'Get Your New Kitchen Cabinets in 3 Weeks — Not 3 Months.',
    subhead: 'See how Oahu homeowners are getting semi-custom cabinetry at builder pricing, delivered in weeks.',
    // A category claim, not a feature claim.
    differentiator: 'The only Hawaii supplier that warehouses cabinets locally — no 12-week mainland backorder.',

    steps: ['Watch the Walkthrough', 'Book Your Design Call', 'See Real Kitchens'],

    // Video: type is 'vidalytics' | 'youtube' | 'vimeo' | 'none'
    video: {
      type: 'none',
      id: '',                     // Vidalytics embed id, or YouTube/Vimeo video id
      posterAlt: 'Kitchen cabinet walkthrough'
    },

    // Friction-killer. Rendered under EVERY call to action on both pages.
    ctaMeta: 'Free · 30 minutes · No deposit required',
    ctaPrimary: 'See If We Can Hit Your Timeline →',
    ctaSecondary: 'Book My Free Design Call →',

    // Counters animate from zero when scrolled into view.
    stats: [
      { target: 400,   prefix: '',  suffix: '+',      label: 'Kitchens Supplied' },
      { target: 3,     prefix: '',  suffix: ' Weeks', label: 'Typical Lead Time' },
      { target: 40,    prefix: '',  suffix: '%',      label: 'Under Big-Box Pricing' }
    ],

    gallery: {
      heading: 'See What We Actually Deliver',
      subheading: 'Real Oahu installs · Real customer photos',
      note: "These aren't renderings. This is what ships.",
      // Add image URLs here. Local paths work too: 'assets/proof/01.jpg'
      images: []
    },

    // Reframes the visitor's past failure as a diagnosis, not a verdict.
    close: {
      heading: "Every quote so far has been too slow or too expensive.",
      subheading: "Here's why — and what actually fixes it.",
      body: 'Book a free design call. Bring your measurements or just your ideas. Walk away with a real number and a real date either way.'
    },

    disclaimer: 'Lead times and pricing vary by selection, finish, and availability. Quoted timelines reflect in-stock and semi-custom lines.'
  },

  /* ---- QUIZ ----------------------------------------------------------
     Order matters. The step with `type: 'contact'` is where contact
     details are captured and the PARTIAL webhook fires — put it early
     (step 3 of 8 is the tested position) so abandoners are still reachable.
     ------------------------------------------------------------------- */
  quiz: {
    title: 'Quick fit-check · 60 seconds',

    steps: [
      {
        key: 'role',
        type: 'choice',
        eyebrow: 'Your project',
        question: 'What best describes you?',
        help: 'No wrong answer — it just helps us route you to the right person.',
        options: [
          { icon: '🏠', label: 'Homeowner',            sub: "It's my own kitchen or bath" },
          { icon: '🔨', label: 'Builder / Contractor',  sub: "I'm building or remodeling for a client" },
          { icon: '📐', label: 'Designer / Architect',  sub: "I'm specifying for a project" },
          { icon: '🏘️', label: 'Investor / Property Mgr', sub: 'Rental, flip, or multi-unit' }
        ]
      },
      {
        key: 'project',
        type: 'choice',
        eyebrow: 'The scope',
        question: 'What are you working on?',
        help: 'We supply all of these — it just changes who you talk to.',
        options: [
          { icon: '🍳', label: 'Full kitchen remodel',      sub: 'New layout, new cabinets, new everything' },
          { icon: '✨', label: 'Cabinets only',             sub: 'Same layout, replacing the boxes and doors' },
          { icon: '🛁', label: 'Bath vanities',             sub: 'One or more bathrooms' },
          { icon: '🏡', label: 'Whole home / multiple rooms', sub: 'Kitchen plus other spaces' }
        ]
      },
      {
        /* ---- THE MONEY STEP ----------------------------------------
           Sits at 3 of 8, before every qualifying question. As soon as
           this submits, the PARTIAL webhook fires — so everyone who
           abandons at steps 4-8 is still a reachable contact.
           ----------------------------------------------------------- */
        key: 'contact',
        type: 'contact',
        eyebrow: 'Quick intro',
        question: 'First — who are we helping?',
        help: 'Just a name and the best way to reach you, so we can save your progress and send your call details.',
        fields: {
          firstNameLabel: 'First name',
          firstNameError: 'Enter your first name.',
          phoneLabel: 'Best phone number',
          phoneError: 'Enter a valid phone number.',
          // Their funnel captured phone only and hardcoded email to "".
          // Email is captured here so there is an actual nurture path.
          emailLabel: 'Email',
          emailError: 'Enter a valid email address.',
          emailRequired: true
        },
        countryCodes: [
          { flag: '🇺🇸', code: '+1',  label: 'US' },
          { flag: '🇨🇦', code: '+1',  label: 'CA' },
          { flag: '🇦🇺', code: '+61', label: 'AU' },
          { flag: '🇬🇧', code: '+44', label: 'UK' },
          { flag: '🌐',  code: '',    label: 'Other' }
        ],
        consent: 'By continuing, I consent to receive communications from ' +
                 'Grandeur Design Supply about my project via phone, SMS/text, and email at ' +
                 'the details provided, including automated messages. Consent is not a ' +
                 'condition of purchase. Message & data rates may apply. Reply STOP to opt out.',
        // Objection handling disguised as a help tooltip.
        whyLabel: 'Why do you need my phone?',
        whyBody: 'So we can send your call confirmation and reminders by text, and reach ' +
                 'you quickly if anything about your appointment changes. We never sell ' +
                 'your details, and you can opt out any time by replying STOP.'
      },
      {
        key: 'timeline',
        type: 'choice',
        eyebrow: 'Your timing',
        question: 'When do you need the cabinets installed?',
        help: 'This decides whether we quote in-stock or semi-custom lines.',
        options: [
          { icon: '🚀', label: 'ASAP — within 30 days',  sub: 'Job is waiting on cabinets' },
          { icon: '📅', label: '1 – 3 months',            sub: 'Planned and moving' },
          { icon: '🗓️', label: '3 – 6 months',            sub: 'Still designing' },
          { icon: '💭', label: 'Just exploring',          sub: 'No firm date yet' }
        ]
      },
      {
        key: 'details',
        type: 'text',
        eyebrow: 'The space',
        question: 'Tell us about the space.',
        help: 'Rough size, current layout, the style you want. A sentence is plenty.',
        placeholder: 'e.g. Galley kitchen, about 12 linear feet, want shaker in a white or light oak...',
        error: 'Give us a sentence so we can actually help.',
        minLength: 10
      },
      {
        /* Anchored slider. Defaults to a typical project, not to zero —
           the midpoint becomes the reference point for everything after. */
        key: 'size',
        type: 'slider',
        eyebrow: 'The size',
        question: 'Roughly how much cabinetry?',
        help: 'Linear feet of run — measure the walls the cabinets sit against. Estimate is fine.',
        min: 5,
        max: 60,
        step: 1,
        default: 25,                 // anchor: a typical full kitchen
        unit: ' linear ft',
        maxLabel: '60+ linear ft'
      },
      {
        /* Free text that hands whoever takes the call their own script,
           in the prospect's words, before the call starts. */
        key: 'challenge',
        type: 'text',
        eyebrow: 'The real one',
        question: "What's the #1 thing holding this project up right now?",
        help: "Don't skip this. If we work together, this is what we solve first.",
        placeholder: 'e.g. Every quote has been 10+ weeks out, or came back double our budget...',
        error: 'A sentence or two, please — this is what we solve on the call.',
        minLength: 10
      },
      {
        /* ---- THE GATE ----------------------------------------------
           The ONLY question that changes routing. Everything above it
           builds commitment and arms the sales call.
           ----------------------------------------------------------- */
        key: 'budget',
        type: 'choice',
        eyebrow: 'Getting started',
        question: "What's your budget for the cabinetry itself?",
        help: 'Cabinets and hardware only — not countertops, appliances, or install labor.',
        options: [
          // `disqualify: true` routes to the soft-decline screen.
          { icon: '',   label: 'Under $5,000',   sub: "(please don't book — see below)", value: 'Under $5k', disqualify: true },
          { icon: '',   label: '$5,000 – $15,000',  value: '$5k-15k' },
          { icon: '',   label: '$15,000 – $35,000', value: '$15k-35k' },
          { icon: '',   label: '$35,000 – $75,000', value: '$35k-75k' },
          { icon: '',   label: '$75,000+',          value: '$75k+' }
        ],
        // Takeaway close. Makes the slot feel scarce and earned.
        footnote: '⏱️ Please only book if you\'re ready to move. This is a real 1:1 with a ' +
                  'designer — we block the slot and turn others away to be there.'
      }
    ],

    /* ---- OUTCOME: QUALIFIED ---- */
    win: {
      heading: "You're a fit. Pick your time 👇",
      body: 'Based on your answers we can hit your timeline. Grab a free 30-minute slot ' +
            'below and we\'ll map out exact pricing and a delivery date for your project.',
      meta: 'Free · 30 minutes · No deposit required'
    },

    /* ---- OUTCOME: DISQUALIFIED ----
       Their version dead-ended here with an href="#". This routes to a
       genuine lower-tier offer instead, so the traffic still monetizes
       and the contact stays warm. */
    soft: {
      heading: 'Not the right fit — yet.',
      body: 'At that budget a semi-custom order is not going to work, and we would rather ' +
            'tell you now than waste your time on a call.',
      bodyTwo: 'But we almost certainly still have something for you. Island Home Cabinets ' +
               'carries surplus and overstock cabinet sets that move well under $5,000 — ' +
               'same quality, just whatever happens to be on the floor that week.',
      ctaLabel: 'See This Week\'s In-Stock Cabinets →',
      ctaUrl: 'https://islandhomecabinets.com',   // <-- point at the real inventory page
      ctaMeta: 'Free · No appointment needed'
    }
  }
};
