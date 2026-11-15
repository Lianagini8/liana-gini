<?php
// SuccessURL Робокассы: покупатель вернулся после оплаты.
require __DIR__ . '/lib.php';

$sum = (string)($_REQUEST['OutSum'] ?? '');
$inv = (string)($_REQUEST['InvId'] ?? '');
$sig = (string)($_REQUEST['SignatureValue'] ?? '');
$o = order_load((int)$inv);
if ($o && !empty($o['lang'])) lang($o['lang']);
$home = '<p><a href="' . (lang() === 'en' ? site_url() . '/' : '/') . '">' . t('На главную') . '</a></p>';
if (!sig_ok($sum, $inv, $sig, rk('pass1'))) page(t('Ссылка недействительна'), '<p>' . t('Если вы оплатили заказ, напишите нам, мы пришлём материалы.') . '</p>' . $home, 400);

if (!$o) page(t('Заказ не найден'), $home, 404);

if ($o['status'] !== 'paid') {
  // уведомление ResultURL обычно приходит за секунды; ждём до ~1 минуты
  $try = (int)($_GET['try'] ?? 0);
  if ($try < 20) {
    $q = http_build_query(['OutSum' => $sum, 'InvId' => $inv, 'SignatureValue' => $sig, 'try' => $try + 1]);
    page(t('Проверяем оплату'), '<p>' . t('Это займёт несколько секунд, не закрывайте страницу.') . '</p>', 200,
      '<meta http-equiv="refresh" content="3;url=/api/success.php?' . h($q) . '">');
  }
  page(t('Оплата обрабатывается'), '<p>' . t('Банк ещё подтверждает платёж. Ссылка на материалы придёт на почту, указанную при оплате. Если письма нет в течение часа, напишите нам.') . '</p>');
}

if (!PRODUCTS[$o['product']]['files']) {
  page(t('Оплата прошла'), '<p>' . t('Команда свяжется с вами для согласования даты и времени консультации.') . '</p>' . $home);
}
header('Location: ' . access_url($o), true, 303);
