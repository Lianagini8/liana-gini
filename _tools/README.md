# Готовый HTML для поиска (prerender)

Сайт собран в Claude Design: текст лежит в шаблоне `<x-dc>` и собирается в браузере. Без prerender роботы видят пустую страницу.

`_tools/prerender.mjs` открывает `index.html` (1440 px) и `mobile.html` (390 px, телефон) в headless Chrome и записывает в них:
- `<div id="dc-prerender">`: готовый HTML с текстом, его видят роботы и браузеры без JS;
- `<template id="dc-tpl">`: исходный шаблон `<x-dc>` байт в байт;
- маленький скрипт, который убирает готовую копию и возвращает `<x-dc>`, поэтому для посетителей сайт работает как раньше.

**После любой правки index.html, mobile.html или section-*.dc.html запускать:**

    node _tools/prerender.mjs

- `node _tools/prerender.mjs --restore` возвращает чистый шаблон (для правок в Claude Design).
- Нужен Node 18+, playwright-core (берётся из `~/Desktop/Сайты/_tools/casegen`) и Google Chrome.
- Title, description, canonical, OG и разметка Schema.org лежат в `<head>` между `<!--seo:head-->` и `<!--/seo:head-->`, prerender их не трогает.
- После правки `mobile.html` или `assets/js/dc-runtime.js` поднять версию кэша в `sw.js`.

Папка `_tools` на хостинг не выгружается (исключение в `.github/workflows/deploy-hosting.yml`).

# Посадочные страницы (07.11.2026)

Новые страницы для поиска: обычный статичный HTML без dc-runtime и без prerender. Одна адаптивная вёрстка для компьютера и телефона, отдельный mobile.html не нужен.

- Стили: `assets/css/landing.css` (палитра и шрифт главной, блоки: первый экран, секции, факты, шаги, фото с подписью, ссылки, вопросы, автор, призыв к консультации, подвал).
- Шаблон: `_tools/landing-template.html` (на хостинг не выгружается). Копировать в `/<адрес>/index.html`, заменить всё в `[ … ]` по ТЗ страницы.
- Первая страница по шаблону: `o-liane-gini/index.html`.
- Пути к файлам сайта только от корня (`/assets/...`, `/konsultaciya/`): страница лежит во вложенной папке.
- JSON-LD: ссылки на сущности главной (`https://lianagini.ru/#liana`, `#org`, `#site`), новых сущностей Лианы не заводим.
- Черновик: `<meta name="robots" content="noindex">` и блоки с классом `draft`. Перед публикацией убрать оба и добавить адрес в `sitemap.xml`.
- Ссылки только на опубликованные страницы.
- `assets/js/cookie-banner.js` ссылается на `/cookie-policy.html` от корня, поэтому работает и во вложенных папках.
- Страница консультации: `konsultaciya/index.html`. Оплата через `assets/js/consultation-checkout.js`: он вызывает существующий `startCheckout('personal-consultation', …)` из `payments.js` → `POST /api/checkout.php` → переход на страницу оплаты Робокассы. Поля, которые требует сервер: name, contact, email (email обязателен для всех продуктов). Успех оплаты показывает только `/api/success.php` после подтверждения ResultURL, сама страница успех не показывает.
