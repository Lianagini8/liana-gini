<?php
// SuccessURL Робокассы: покупатель вернулся после оплаты.
require __DIR__ . '/lib.php';

$sum = (string)($_REQUEST['OutSum'] ?? '');
$inv = (string)($_REQUEST['InvId'] ?? '');
$sig = (string)($_REQUEST['SignatureValue'] ?? '');
if (!sig_ok($sum, $inv, $sig, rk('pass1'))) page('Ссылка недействительна', '<p>Если вы оплатили заказ, напишите нам, мы пришлём материалы.</p><p><a href="/">На главную</a></p>', 400);

$o = order_load((int)$inv);
if (!$o) page('Заказ не найден', '<p><a href="/">На главную</a></p>', 404);

if ($o['status'] !== 'paid') {
  // уведомление ResultURL обычно приходит за секунды; ждём до ~1 минуты
  $try = (int)($_GET['try'] ?? 0);
  if ($try < 20) {
    $q = http_build_query(['OutSum' => $sum, 'InvId' => $inv, 'SignatureValue' => $sig, 'try' => $try + 1]);
    page('Проверяем оплату', '<p>Это займёт несколько секунд, не закрывайте страницу.</p>', 200,
      '<meta http-equiv="refresh" content="3;url=/api/success.php?' . h($q) . '">');
  }
  page('Оплата обрабатывается', '<p>Банк ещё подтверждает платёж. Ссылка на материалы придёт на почту, указанную при оплате. Если письма нет в течение часа, напишите нам.</p>');
}

if (!PRODUCTS[$o['product']]['files']) {
  page('Оплата прошла', '<p>Команда свяжется с вами для согласования даты и времени консультации.</p><p><a href="/">На главную</a></p>');
}
header('Location: ' . access_url($o), true, 303);
