// Centralized legal/requisites values. Do not invent values here — fill in
// only once the client confirms them, then wire into oferta.html /
// privacy-policy.html / pd-consent.html / ad-consent.html / the site footer,
// wherever a blank was left in this pass.
//
// CONFIRMED by client (2026-08-26):
//   - E-mail — liana.Giniyatulina@yandex.com. Filled in on the 3 pages where
//     the lawyer-supplied text requires the operator's contact e-mail:
//     Policy §8.2 (privacy-policy.html), PD Consent cl. 4 (pd-consent.html),
//     Ad Consent cl. 3 (ad-consent.html). Offer §14 "Реквизиты" itself never
//     had a separate e-mail line in the source document, so nothing to fill
//     there. No longer unresolved.
//
// Still unresolved in the supplied DOCX files:
//   - Site URL       — Offer §1.1 "Сайт — ... расположенный по адресу
//                       __________", Policy §1.3 leave the site's own URL
//                       blank.
//   - Revision date   — Both the Offer and the Policy header read
//                       'Редакция от «___» __________ 20__ г.' — no date
//                       was filled in.
//
// These two are left empty (not fake values) so nothing false gets
// published; the site currently omits these fields from public pages rather
// than showing literal "__________" placeholders.

export const LEGAL_EMAIL = 'liana.Giniyatulina@yandex.com';
export const SITE_URL = 'https://lianagini.ru'; // вписан в оферту п. 1.1 и политику п. 1.3 (05.11.2026)
export const LEGAL_REVISION_DATE = ''; // TODO: confirm with client — see notes above
