<?php
// POST {product, design?, volume?, targetCost?, phone, contactHandle?, source?, pdConsent, marketingConsent?, _honey?} -> {success}
// Заявка с сайта уходит письмом Лиане прямо с хостинга, без сторонних сервисов.
require __DIR__ . '/lib.php';
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit('{"error":"method"}'); }

$origin = parse_url((string)($_SERVER['HTTP_ORIGIN'] ?? ''), PHP_URL_HOST);
$host = explode(':', (string)($_SERVER['HTTP_HOST'] ?? ''))[0];
if (!$origin || strcasecmp($origin, $host) !== 0) { http_response_code(403); exit('{"error":"origin"}'); }

$in = json_decode((string)file_get_contents('php://input', false, null, 0, 65536), true);
if (!is_array($in)) { http_response_code(400); exit('{"error":"json"}'); }

// Скрытое поле заполняют только боты: отвечаем успехом и ничего не отправляем.
if (trim((string)($in['_honey'] ?? '')) !== '') exit('{"success":true}');

$clean = fn(string $k, int $max = 2000) => mb_substr(trim(preg_replace('/[^\P{C}\n\t]/u', '', (string)($in[$k] ?? '')) ?? ''), 0, $max);
$product = $clean('product');
$phone = $clean('phone', 100);
if ($product === '' || $phone === '' || empty($in['pdConsent'])) { http_response_code(400); exit('{"error":"fields"}'); }
if (!rate_ok('enquiry', 10, 3600)) { http_response_code(429); exit('{"error":"rate"}'); }

$contact = $clean('contactHandle', 200);
$source = str_replace(["\r", "\n"], ' ', $clean('source', 120));

$lines = [
  'Опишите вашу задачу' => $product,
  'Есть готовый дизайн или прототип' => $clean('design'),
  'Планируемый объём' => $clean('volume', 200),
  'Целевая себестоимость' => $clean('targetCost', 200),
  'Телефон' => $phone,
  'Email / мессенджер' => $contact,
];
if ($source !== '') $lines['Источник заявки'] = $source;
$lines['Согласие на обработку персональных данных'] = 'Да';
$lines['Согласие на рекламные рассылки'] = !empty($in['marketingConsent']) ? 'Да' : 'Нет';

$text = '';
foreach ($lines as $label => $value) $text .= $label . ":\n" . ($value !== '' ? $value : '—') . "\n\n";
$text .= 'Сайт: ' . $host . "\n";

$subject = $source !== '' ? "Новая заявка ($source) — LIANA GINI" : 'Новая заявка с сайта LIANA GINI';
$replyTo = filter_var($contact, FILTER_VALIDATE_EMAIL) ? $contact : '';

if (!send_mail((string)(cfg()['notify_email'] ?? ''), $subject, $text, $replyTo)) {
  http_response_code(502);
  exit('{"error":"mail"}');
}
echo '{"success":true}';
