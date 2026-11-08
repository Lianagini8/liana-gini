// Production enquiry submission: POST to our own /api/enquiry.php, which emails the
// operator from the hosting in Russia. No third-party form processor is involved.

export const ENQUIRY_ENDPOINT = '/api/enquiry.php';
export const WIRED = true;

export const STATES = { IDLE: 'idle', PENDING: 'pending', SUCCESS: 'success', ERROR: 'error' };

export const FIELDS = ['product', 'design', 'volume', 'targetCost', 'phone', 'contactHandle'];

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
