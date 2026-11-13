// Self-contained first-visit cookie notice. Injects its own markup so every
// page just needs <script src="assets/js/cookie-banner.js" defer></script>.
//
// Banner copy describes what the site ACTUALLY does right now (necessary
// storage only — see assets/js/cookie-banner.js's own localStorage use,
// audited: no analytics/tracking currently loads anywhere on the site).
// The lawyer-prepared Cookie Policy itself (cookie-policy.html) is NOT
// touched here — it separately describes technical + analytical cookies as
// a category the site may use; if/when analytics is actually added, this
// banner copy should be revisited together with that policy text.
(function () {
  var STORAGE_KEY = 'lg_cookie_ack_v1';

  function alreadyAcknowledged() {
    try { return localStorage.getItem(STORAGE_KEY) === '1'; } catch (e) { return false; }
  }
  function acknowledge() {
    try { localStorage.setItem(STORAGE_KEY, '1'); } catch (e) {}
  }

  function cookiePolicyHref() {
    // Absolute path: landing pages live in folders (/o-liane-gini/), where a
    // relative 'cookie-policy.html' would resolve to /o-liane-gini/cookie-policy.html.
    return '/cookie-policy.html';
  }

  // Reports the banner's own rendered height as a CSS custom property, so any
  // page that cares (currently just mobile.html's app-shell) can reserve that
  // much space at the bottom while the banner is up, instead of letting the
  // banner's fixed overlay sit on top of whatever content/CTA happens to be
  // scrolled to the bottom edge. Inert on any page that doesn't reference the
  // variable (e.g. desktop) — setting an unused custom property changes
  // nothing there.
  function setSafeBottom(px) {
    document.documentElement.style.setProperty('--lg-cookie-safe-bottom', px + 'px');
  }
  function syncSafeBottom(el) {
    setSafeBottom(el ? el.offsetHeight : 0);
  }

  function mount() {
    if (alreadyAcknowledged()) return;
    if (document.getElementById('lg-cookie-banner')) return;

    var style = document.createElement('style');
    style.textContent =
      '#lg-cookie-banner{position:fixed;left:0;right:0;bottom:0;z-index:2147483000;' +
      'display:flex;align-items:center;justify-content:center;gap:16px;flex-wrap:wrap;' +
      'padding:14px 20px;padding-bottom:calc(14px + env(safe-area-inset-bottom));' +
      'background:#181715;color:#F2EFE8;font-family:Manrope,-apple-system,BlinkMacSystemFont,sans-serif;' +
      'box-shadow:0 -2px 24px rgba(0,0,0,0.2);}' +
      '#lg-cookie-banner p{margin:0;font-size:12px;line-height:1.5;max-width:560px;opacity:0.85;}' +
      '#lg-cookie-banner a{color:#F2EFE8;text-decoration:underline;}' +
      '#lg-cookie-banner button{flex-shrink:0;font-family:inherit;border:none;cursor:pointer;' +
      'background:#541F2B;color:#F2EFE8;font-size:12px;font-weight:700;letter-spacing:0.5px;' +
      'text-transform:uppercase;padding:11px 20px;}' +
      '#lg-cookie-banner button:hover{background:#8C4457;}' +
      '#lg-cookie-banner button:focus-visible{outline:2px solid #F2EFE8;outline-offset:2px;}';
    document.head.appendChild(style);

    var el = document.createElement('div');
    el.id = 'lg-cookie-banner';
    el.setAttribute('role', 'region');
    el.setAttribute('aria-label', 'Уведомление об использовании cookie');

    var p = document.createElement('p');
    p.textContent = 'Мы используем файлы cookie и локальное хранилище для корректной работы сайта. Подробнее — в ';
    var a = document.createElement('a');
    a.href = cookiePolicyHref();
    a.textContent = 'Политике Cookie';
    p.appendChild(a);
    p.appendChild(document.createTextNode('.'));

    var btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = 'Принять';
    var onResize = function () { syncSafeBottom(el); };
    btn.addEventListener('click', function () {
      acknowledge();
      el.remove();
      window.removeEventListener('resize', onResize);
      setSafeBottom(0); // no permanent reserved space once dismissed
    });

    el.appendChild(p);
    el.appendChild(btn);
    document.body.appendChild(el);

    // Measure after layout (banner text can wrap differently per viewport),
    // and keep it in sync across resizes/orientation changes while it's up.
    requestAnimationFrame(function () { syncSafeBottom(el); });
    window.addEventListener('resize', onResize);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mount);
  } else {
    mount();
  }
})();
