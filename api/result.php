<?php
// ResultURL Робокассы (POST): подтверждение оплаты сервер-сервер. Ответ OK{InvId}.
require __DIR__ . '/lib.php';
header('Content-Type: text/plain; charset=utf-8');

$sum = (string)($_REQUEST['OutSum'] ?? '');
$inv = (string)($_REQUEST['InvId'] ?? '');
$sig = (string)($_REQUEST['SignatureValue'] ?? '');
if (!sig_ok($sum, $inv, $sig, rk('pass2'))) { http_response_code(400); exit('bad sign'); }

$o = order_load((int)$inv);
if (!$o) { http_response_code(404); exit('no order'); }
if (abs((float)$sum - (float)$o['amount']) > 0.01) { http_response_code(400); exit('bad sum'); }

if ($o['status'] !== 'paid') {
  $o['status']  = 'paid';
  $o['paid_at'] = time();
  $rkEmail = mb_substr(trim((string)($_REQUEST['EMail'] ?? '')), 0, 200);
  if (empty($o['email'])) $o['email'] = $rkEmail; // основной источник: поле на сайте; Робокасса передаёт почту не всегда
  order_save($o);

  $p = PRODUCTS[$o['product']];
  if (!empty($o['lang'])) lang($o['lang']);
  if ($p['files']) {
    send_mail($o['email'], t('Ваши материалы LIANA GINI'),
      t('Спасибо за покупку!') . "\n\n«" . t($p['name']) . "»\n\n" . t('Скачать файлы:') . ' ' . access_url($o) .
      "\n\n" . strtr(t('Ссылка действует {N} дней.'), ['{N}' => (int)(cfg()['access_days'] ?? 30)]) . "\n\nLIANA GINI\n" . site_url());
  }
  lang('ru'); // уведомление Лиане всегда на русском
  send_mail(cfg()['notify_email'] ?? '', "Оплата №{$o['id']}: {$p['name']}",
    "Заказ №{$o['id']}\nТовар: {$p['name']}\nСумма: {$o['amount']} ₽\nEmail покупателя: {$o['email']}" .
    ($o['name'] !== '' ? "\nИмя: {$o['name']}" : '') . ($o['contact'] !== '' ? "\nКонтакт: {$o['contact']}" : '') .
    "\nСогласие на рекламу: " . ($o['marketing'] ? 'да' : 'нет') . (($o['lang'] ?? '') === 'en' ? "\nСайт: lianagini.com" : '') . brief_text($o));
}
echo 'OK' . $o['id'];

// Бриф, который покупатель заполнил перед оплатой консультации.
function brief_text(array $o): string {
  $labels = ['product' => 'Опишите вашу задачу', 'design' => 'Есть готовый дизайн или прототип', 'volume' => 'Планируемый объём',
    'targetCost' => 'Целевая себестоимость', 'phone' => 'Телефон', 'contactHandle' => 'Email / мессенджер'];
  $b = $o['brief'] ?? [];
  if (!$b) return '';
  $t = "\n\nБРИФ К КОНСУЛЬТАЦИИ\n";
  foreach ($labels as $k => $label) $t .= "\n$label:\n" . ($b[$k] ?? '—') . "\n";
  return $t;
}
