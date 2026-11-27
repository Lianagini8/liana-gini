// Production enquiry submission: POST to our own /api/enquiry.php, which emails the
// operator from the hosting in Russia. No third-party form processor is involved.

export const ENQUIRY_ENDPOINT = '/api/enquiry.php';
export const WIRED = true;

export const STATES = { IDLE: 'idle', PENDING: 'pending', SUCCESS: 'success', ERROR: 'error' };

export const FIELDS = ['plan', 'product', 'design', 'volume', 'targetCost', 'phone', 'messenger', 'contactHandle'];

// 27.11: три консультации в форме записи (макет Кати)
export const CONSULTS = {
  sell: { productId: 'personal-consultation', label: 'Уже продаю одежду: формирование ассортимента и расчёт партии' },
  brand: { productId: 'personal-consultation', label: 'Запускаю первый бренд: формирование коллекции и расчёт первой партии' },
  company: { productId: 'company-consultation', label: 'Открываю компанию в Китае: как открыть и вести компанию' },
};

export function validate(payload) {
  const errors = {};
  if (!payload.product?.trim()) errors.product = 'required';
  if (!payload.phone?.trim()) errors.phone = 'required';
  if (!payload.pdConsent) errors.pdConsent = 'required';
  return { valid: Object.keys(errors).length === 0, errors };
}

export async function submitEnquiry(payload) {
  const { valid, errors } = validate(payload);
  if (!valid) return { state: STATES.ERROR, errors, reason: 'validation-failed' };
  if (!WIRED) return { state: STATES.ERROR, reason: 'enquiry-channel-not-connected' };

  try {
    const res = await fetch(ENQUIRY_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) return { state: STATES.ERROR, reason: 'request-failed' };
    const data = await res.json().catch(() => null);
    if (data && data.success === true) return { state: STATES.SUCCESS };
    return { state: STATES.ERROR, reason: 'enquiry-rejected', detail: data };
  } catch (err) {
    return { state: STATES.ERROR, reason: 'network-error' };
  }
}

// С 25.11.2026 бриф ведёт на оплату консультации (решение Лианы: бесплатных заявок с сайта нет).
// Бриф уходит вместе с заказом и приходит Лиане в письме об оплате, отдельного письма до оплаты нет.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validatePaid(p) {
  const errors = {};
  if (!p.product?.trim()) errors.product = 'required';
  if (!p.phone?.trim()) errors.phone = 'required';
  if (!p.name?.trim()) errors.name = 'required';
  if (!EMAIL_RE.test((p.email || '').trim())) errors.email = 'required';
  if (!p.pdConsent) errors.pdConsent = 'required';
  return { valid: Object.keys(errors).length === 0, errors };
}

export async function payConsultation(p) {
  const { valid, errors } = validatePaid(p);
  if (!valid) return { state: STATES.ERROR, errors, reason: 'validation-failed' };
  if (p._honey && p._honey.trim()) return { state: STATES.ERROR, reason: 'bot' };
  const c = CONSULTS[p.consult] || CONSULTS.sell;
  const brief = { consult: c.label };
  for (const k of FIELDS) brief[k] = (p[k] || '').trim();
  const contact = [brief.phone, [brief.messenger, brief.contactHandle].filter(Boolean).join(': ')].filter(Boolean).join(', ');
  try {
    const { startCheckout } = await import('/assets/js/payments.js');
    const res = await startCheckout(c.productId, {
      name: p.name.trim(), contact, email: p.email.trim(), marketingConsent: !!p.marketingConsent, brief,
    });
    if (res.checkoutUrl) return { state: STATES.PENDING, checkoutUrl: res.checkoutUrl };
    return { state: STATES.ERROR, reason: 'checkout-failed' };
  } catch (err) {
    return { state: STATES.ERROR, reason: 'network-error' };
  }
}
