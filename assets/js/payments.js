// Payment layer — provider-agnostic. No provider chosen yet, no keys in frontend.
// Wire a real provider later by implementing createCheckout() against your OWN backend
// endpoint; the backend holds the secret key and returns a redirect URL.
// Download/access URLs are intentionally NOT present in page source — they are issued
// by the backend only after the provider confirms payment (webhook -> signed link).

// Canonical product matrix — client-confirmed final IDs/names/prices.
export const PRODUCTS = {
  'catalog_collections': { id: 'catalog_collections', name: 'Каталоги готовых трендовых и базовых коллекций', price: 390, currency: 'RUB' },
  'factory_check_9':     { id: 'factory_check_9',     name: '9 шагов проверки фабрики',                        price: 490, currency: 'RUB' },
  'brand_china_7':       { id: 'brand_china_7',       name: 'Как запустить свой бренд через Китай',            price: 490, currency: 'RUB' },
  'guangzhou_markets':   { id: 'guangzhou_markets',   name: 'Список рынков Гуанчжоу с адресами',                price: 490, currency: 'RUB' },
  // Service, not a download: after payment the backend confirms and schedules.
  // No calendar/date-time picker — Liana contacts the buyer herself after payment,
  // so the only fields collected before payment are name + a single contact field.
  'personal-consultation': { id: 'personal-consultation', name: 'Личная консультация с Лианой Гини', price: 15000, currency: 'RUB',
    kind: 'service', collect: ['name', 'contact'] },
};

// Backend endpoints (PHP on the hosting, see /api). Secrets live only on the server.
export const ENDPOINTS = {
  createCheckout: '/api/checkout.php',   // POST {productId, name?, contact?, marketingConsent?} -> {checkoutUrl, orderId}
  // Robokassa then calls /api/result.php (ResultURL) and returns the buyer to
  // /api/success.php (SuccessURL) -> /api/access.php with download buttons.
};

export const STATES = { IDLE: 'idle', PENDING: 'pending', SUCCESS: 'success', ERROR: 'error' };

// CTA -> checkout: our backend creates the order and returns a signed Robokassa URL.
// extra: {name, contact} for the consultation, {marketingConsent} for everything.
export async function startCheckout(productId, extra = {}) {
  const product = PRODUCTS[productId];
  if (!product) throw new Error('Unknown product: ' + productId);
  try {
    const r = await fetch(ENDPOINTS.createCheckout, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ productId, ...extra }),
    });
    const data = await r.json();
    if (!r.ok || !data.checkoutUrl) return { state: STATES.ERROR, product };
    return { state: STATES.PENDING, product, checkoutUrl: data.checkoutUrl, orderId: data.orderId };
  } catch (e) {
    return { state: STATES.ERROR, product };
  }
}

// Future Robokassa payload for the consultation service — data model only, not
// sent anywhere (no provider connected yet, no keys in the frontend). Built by
// the checkout UI once the buyer's name/contact/consent are collected in the
// consent-gate modal, so it's ready to hand to a real provider call the moment
// one is wired in. Digital products don't go through this — they stay on the
// existing productId-only startCheckout() path above, untouched.
export function buildConsultationOrder({ name, contact, pdConsent, marketingConsent }) {
  const product = PRODUCTS['personal-consultation'];
  return {
    productId: product.id,
    name: product.name,
    amount: product.price,
    currency: product.currency,
    buyerName: (name || '').trim(),
    buyerContact: (contact || '').trim(),
    pdConsent: !!pdConsent,
    marketingConsent: !!marketingConsent,
  };
}

// Exact copy for the post-payment confirmation screen, for once Robokassa is
// connected and startCheckout() can actually resolve to STATES.SUCCESS for a
// real consultation order. Not rendered anywhere yet: today startCheckout()
// always resolves to STATES.IDLE, so no code path can reach this — it only
// becomes reachable when a real provider call is wired in to return 'success'.
export const CONSULTATION_SUCCESS_MESSAGE = {
  title: 'ОПЛАТА ПРОШЛА',
  body: 'КОМАНДА СВЯЖЕТСЯ С ВАМИ\nДЛЯ СОГЛАСОВАНИЯ ДАТЫ И ВРЕМЕНИ КОНСУЛЬТАЦИИ.',
};

// Called on return from the provider (?orderId=...). Backend verifies, then issues
// a short-lived signed download link.
export async function resolveDelivery(orderId) {
  if (!orderId) return { state: STATES.IDLE };
  return { state: STATES.PENDING, orderId };
}
