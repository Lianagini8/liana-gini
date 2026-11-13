// Оформление консультации на /konsultaciya/ (07.11.2026).
// Использует существующий payments.js → POST /api/checkout.php → страница оплаты Робокассы.
// Своей оплаты здесь нет: цену и заказ создаёт сервер, секретов в браузере нет.
// Успех оплаты подтверждает только сервер (ResultURL Робокассы → /api/result.php,
// затем /api/success.php проверяет статус заказа). Эта страница успех не показывает.
import { startCheckout, STATES } from '/assets/js/payments.js';

const PRODUCT_ID = 'personal-consultation';
// Та же проверка, что в mobile.html; сервер дополнительно проверяет FILTER_VALIDATE_EMAIL.
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const form = document.getElementById('consult-form');
if (form) {
  const btn = form.querySelector('button[type="submit"]');
  const status = document.getElementById('consult-status');
  const fields = {
    name: form.elements.name,
    contact: form.elements.contact,
    email: form.elements.email,
    pdConsent: form.elements.pdConsent,
  };
  const checks = {
    name: () => fields.name.value.trim().length > 0,
    contact: () => fields.contact.value.trim().length > 0,
    email: () => EMAIL_RE.test(fields.email.value.trim()),
    pdConsent: () => fields.pdConsent.checked,
  };
  let busy = false;

  const setError = (key, on) => {
    const el = fields[key];
    const msg = document.getElementById(el.getAttribute('aria-describedby'));
    el.setAttribute('aria-invalid', on ? 'true' : 'false');
    if (msg) msg.hidden = !on;
  };
  const say = (text, kind) => {
    status.textContent = text;
    status.dataset.kind = kind || '';
  };

  Object.keys(fields).forEach((key) => {
    const ev = fields[key].type === 'checkbox' ? 'change' : 'input';
    fields[key].addEventListener(ev, () => { if (checks[key]()) setError(key, false); });
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (busy) return; // повторное нажатие во время обработки

    let firstBad = null;
    Object.keys(checks).forEach((key) => {
      const ok = checks[key]();
      setError(key, !ok);
      if (!ok && !firstBad) firstBad = fields[key];
    });
    if (firstBad) {
      say('Проверьте отмеченные поля.', 'error');
      firstBad.focus();
      return;
    }

    busy = true;
    btn.disabled = true;
    form.setAttribute('aria-busy', 'true');
    say('Создаём заказ и переходим к оплате…', 'pending');

    let res;
    try {
      res = await startCheckout(PRODUCT_ID, {
        name: fields.name.value.trim(),
        contact: fields.contact.value.trim(),
        email: fields.email.value.trim(),
        pdConsent: fields.pdConsent.checked,
        marketingConsent: form.elements.marketingConsent.checked,
      });
    } catch (err) {
      res = { state: STATES.ERROR };
    }

    if (res && res.state === STATES.PENDING && res.checkoutUrl) {
      // Переход на страницу оплаты Робокассы. Данные формы остаются, если покупатель вернётся назад.
      window.location.assign(res.checkoutUrl);
      return;
    }

    // Ошибка сети или сервера: данные формы не стираем, кнопку возвращаем.
    busy = false;
    btn.disabled = false;
    form.removeAttribute('aria-busy');
    say(navigator.onLine === false
      ? 'Нет соединения с интернетом. Проверьте связь и нажмите кнопку ещё раз, данные сохранены.'
      : 'Не удалось перейти к оплате. Попробуйте ещё раз через минуту, данные сохранены.', 'error');
  });

  // Возврат кнопкой «назад» со страницы оплаты: страница может прийти из кэша браузера с заблокированной кнопкой.
  window.addEventListener('pageshow', () => {
    busy = false;
    btn.disabled = false;
    form.removeAttribute('aria-busy');
    if (status.dataset.kind === 'pending') say('', '');
  });
}
