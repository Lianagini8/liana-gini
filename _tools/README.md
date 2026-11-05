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
