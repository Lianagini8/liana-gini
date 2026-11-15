<?php
// FailURL Робокассы: оплата отменена или не прошла.
require __DIR__ . '/lib.php';
$o = order_load((int)($_REQUEST['InvId'] ?? 0));
if ($o && !empty($o['lang'])) lang($o['lang']);
page(t('Оплата не прошла'), '<p>' . t('Деньги не списаны. Можно попробовать ещё раз.') . '</p><p><a class="btn" href="' . (lang() === 'en' ? site_url() . '/' : '/') . '#products">' . t('Вернуться к материалам') . '</a></p>');
