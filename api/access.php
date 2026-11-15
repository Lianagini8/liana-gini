<?php
// Страница покупателя со списком файлов (ссылка из письма и после оплаты).
require __DIR__ . '/lib.php';
$o = access_check();
$p = PRODUCTS[$o['product']];
if (access_expired($o)) page(t('Срок доступа истёк'), '<p>' . t('Напишите нам, и мы продлим доступ к материалам.') . '</p>', 410);

$rows = '';
foreach ($p['files'] as $i => $f) {
  $rows .= '<div class="f"><span>' . h(t($f['title'])) . '<small>PDF, ' . h(str_replace('МБ', t('МБ'), $f['size'])) . '</small></span><a class="btn" href="/api/get.php?o=' . $o['id'] . '&t=' . h($o['token']) . '&f=' . $i . '">' . t('Скачать PDF') . '</a></div>';
}
$until = date('d.m.Y', (int)$o['paid_at'] + 86400 * (int)(cfg()['access_days'] ?? 30));
page(t('Спасибо за покупку'), '<p>«' . h(t($p['name'])) . '»</p>' . $rows .
  '<p class="note">' . strtr(t('Сохраните эту страницу: ссылки работают до {дата}. Ссылка также отправлена на вашу почту.'), ['{дата}' => $until]) . '</p>');
