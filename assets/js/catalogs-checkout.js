// Покупка каталогов направления на /katalogi/ (27.11.2026).
// Тот же путь, что у главной: payments.js → POST /api/checkout.php → Робокасса.
import { startCheckout, STATES } from '/assets/js/payments.js';

// Направления, файлы которых уже загружены в хранилище. Пока список пуст, оплата не открывается.
const AVAILABLE = new Set(['catalog_diamonds']);

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const modal = document.getElementById('kat-modal');
const form = document.getElementById('kat-form');
const nameEl = document.getElementById('kat-modal-name');
const status = document.getElementById('kat-status');
let productId = null;
let opener = null;
let busy = false;

function open(btn) {
  productId = btn.dataset.productId;
  if (!AVAILABLE.has(productId)) {
    const note = btn.parentElement.querySelector('.kat-wait') || Object.assign(document.createElement('p'), { className: 'kat-wait', role: 'status' });
    note.textContent = 'Каталоги этого направления появятся в продаже в ближайшие дни.';
    btn.after(note);
    return;
  }
  opener = btn;
  nameEl.textContent = btn.dataset.productName || '';
  status.textContent = '';
  modal.hidden = false;
  form.elements.email.focus();
}
function close() {
  modal.hidden = true;
  if (opener) opener.focus();
}
document.querySelectorAll('.kat-buy').forEach((b) => b.addEventListener('click', () => open(b)));
document.getElementById('kat-cancel').addEventListener('click', close);
modal.addEventListener('click', (e) => { if (e.target === modal) close(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !modal.hidden) close(); });

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (busy) return;
  const email = form.elements.email.value.trim();
  const okEmail = EMAIL_RE.test(email);
  const okPd = form.elements.pdConsent.checked;
  document.getElementById('kat-email-err').hidden = okEmail;
  document.getElementById('kat-pd-err').hidden = okPd;
  if (!okEmail) { form.elements.email.focus(); return; }
  if (!okPd) return;
  busy = true;
  status.textContent = 'Создаём заказ и переходим к оплате…';
  let res;
  try {
    res = await startCheckout(productId, { email, marketingConsent: form.elements.marketingConsent.checked });
  } catch (err) {
    res = { state: STATES.ERROR };
  }
  if (res && res.checkoutUrl) { window.location.assign(res.checkoutUrl); return; }
  busy = false;
  status.textContent = 'Не удалось перейти к оплате. Попробуйте ещё раз.';
});
