<?php
// Страница покупателя со списком файлов (ссылка из письма и после оплаты).
require __DIR__ . '/lib.php';
$o = access_check();
$p = PRODUCTS[$o['product']];
if (access_expired($o)) page('Срок доступа истёк', '<p>Напишите нам, и мы продлим доступ к материалам.</p>', 410);

$rows = '';
foreach ($p['files'] as $i => $f) {
  $rows .= '<div class="f"><span>' . h($f['title']) . '<small>PDF, ' . h($f['size']) . '</small></span><a class="btn" href="/api/get.php?o=' . $o['id'] . '&t=' . h($o['token']) . '&f=' . $i . '">Скачать PDF</a></div>';
}
$until = date('d.m.Y', (int)$o['paid_at'] + 86400 * (int)(cfg()['access_days'] ?? 30));
page('Спасибо за покупку', '<p>«' . h($p['name']) . '»</p>' . $rows .
  '<p class="note">Сохраните эту страницу: ссылки работают до ' . $until . '. Ссылка также отправлена на вашу почту.</p>');
