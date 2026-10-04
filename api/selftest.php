<?php
// Временная проверка доступа к бакету (удалить после проверки). Возвращает только статусы.
require __DIR__ . '/lib.php';
if (($_GET['k'] ?? '') !== 'e1a0e7114feb6c8f2b23255b') { http_response_code(404); exit; }
header('Content-Type: application/json; charset=utf-8');
$out = ['php' => PHP_VERSION, 'mail' => function_exists('mail')];
foreach (PRODUCTS as $p) foreach ($p['files'] as $f) {
  $u = presign($f['key'], $f['title'] . '.pdf', 60);
  $ch = curl_init($u);
  curl_setopt_array($ch, [CURLOPT_RANGE => '0-3', CURLOPT_RETURNTRANSFER => true, CURLOPT_TIMEOUT => 20]);
  $body = curl_exec($ch);
  $out[$f['key']] = [curl_getinfo($ch, CURLINFO_HTTP_CODE), $body === '%PDF' ? 'pdf' : substr((string)$body, 0, 80), curl_error($ch)];
  curl_close($ch);
}
echo json_encode($out, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
