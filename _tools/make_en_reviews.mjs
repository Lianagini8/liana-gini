#!/usr/bin/env node
/**
 * Рисует отзывы клиентов на английском в виде сообщений из чата:
 * assets/media/en-review-1.jpg и en-review-2.jpg. Текст это перевод настоящих отзывов,
 * на сайте под картинками стоит подпись «Translated from Russian». Без неё картинки не ставить.
 * Запуск: node _tools/make_en_reviews.mjs
 */
import { createRequire } from 'node:module';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const require = createRequire(process.env.PLAYWRIGHT_CORE || '/Users/macos/Desktop/Сайты/_tools/casegen/');
const { chromium } = require('playwright-core');
const CHROME = process.env.CHROME_PATH || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const REVIEWS = [
  { file: 'en-review-1.jpg', sender: '~ 💗WILDBERRIES_Alina', time: '13:25', text: 'Good afternoon! The backpacks are good according to the fulfilment centre’s feedback, though we haven’t seen them in person yet :)<br>Thank you for your help in choosing the product! :))' },
  { file: 'en-review-2.jpg', sender: '', time: '19:40', text: 'The time has come and I am turning to Veronika and Liana again ❤️<br>After the first shipment, the girls showed me their professionalism: customer focus, product quality, delivery speed and simply a good, kind attitude.<br>Thank you, girls, for doing your job conscientiously and well!<br>Wishing you prosperity and success 🌸' },
];

const page = (r) => `<!doctype html><meta charset="utf-8"><style>
  body { margin: 0; }
  #s { width: 540px; box-sizing: border-box; padding: 8px 40px 10px 14px; background: #efe7de; font-family: "Helvetica Neue", Arial, sans-serif; }
  .b { background: #fff; border-radius: 12px; padding: 8px 12px 7px; }
  .n { color: #7b7b7b; font-size: 14px; margin-bottom: 3px; }
  .t { color: #111; font-size: 17.5px; line-height: 1.32; }
  .h { color: #8a8a8a; font-size: 12px; text-align: right; margin-top: 2px; }
</style><div id="s"><div class="b">${r.sender ? `<div class="n">${r.sender}</div>` : ''}<div class="t">${r.text}</div><div class="h">${r.time}</div></div></div>`;

const browser = await chromium.launch({ executablePath: CHROME, headless: true });
const ctx = await browser.newContext({ viewport: { width: 540, height: 400 }, deviceScaleFactor: 2 });
const p = await ctx.newPage();
for (const r of REVIEWS) {
  await p.setContent(page(r));
  await p.waitForTimeout(200);
  const el = p.locator('#s');
  const box = await el.boundingBox();
  await el.screenshot({ path: path.join(ROOT, 'assets/media', r.file), type: 'jpeg', quality: 88 });
  console.log(r.file, `${Math.round(box.width * 2)}x${Math.round(box.height * 2)}`);
}
await browser.close();
