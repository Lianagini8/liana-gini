<?php
// Отдаёт файл: проверяет заказ и перенаправляет на подписанную ссылку бакета (живёт 10 минут).
require __DIR__ . '/lib.php';
$o = access_check();
$files = PRODUCTS[$o['product']]['files'];
$i = (int)($_GET['f'] ?? -1);
if (!isset($files[$i])) page('Файл не найден', '', 404);
if (access_expired($o)) page('Срок доступа истёк', '<p>Напишите нам, и мы продлим доступ к материалам.</p>', 410);
if ((int)$o['downloads'] >= (int)(cfg()['max_downloads'] ?? 40)) page('Лимит скачиваний исчерпан', '<p>Напишите нам, если нужен повторный доступ.</p>', 429);

$o['downloads'] = (int)$o['downloads'] + 1;
order_save($o);
header('Cache-Control: no-store');
header('Location: ' . presign($files[$i]['key'], $files[$i]['title'] . '.pdf'), true, 302);
