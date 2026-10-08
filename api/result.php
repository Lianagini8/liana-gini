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
  if ($p['files']) {
    send_mail($o['email'], 'Ваши материалы LIANA GINI',
      "Спасибо за покупку!\n\n«{$p['name']}»\n\nСкачать файлы: " . access_url($o) .
      "\n\nСсылка действует " . (int)(cfg()['access_days'] ?? 30) . " дней.\n\nLIANA GINI\n" . cfg()['site']);
  }
  send_mail(cfg()['notify_email'] ?? '', "Оплата №{$o['id']}: {$p['name']}",
    "Заказ №{$o['id']}\nТовар: {$p['name']}\nСумма: {$o['amount']} ₽\nEmail покупателя: {$o['email']}" .
    ($o['name'] !== '' ? "\nИмя: {$o['name']}" : '') . ($o['contact'] !== '' ? "\nКонтакт: {$o['contact']}" : '') .
    "\nСогласие на рекламу: " . ($o['marketing'] ? 'да' : 'нет'));
}
echo 'OK' . $o['id'];
