<?php
// POST {productId, name?, contact?, marketingConsent?} -> {checkoutUrl, orderId}
require __DIR__ . '/lib.php';
if (!rk('login') || !rk('pass1')) { http_response_code(503); exit('{"error":"not_configured"}'); } // пока нет данных Робокассы, заказ не создаём
header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') { http_response_code(405); exit('{"error":"method"}'); }
$in = json_decode((string)file_get_contents('php://input'), true) ?: [];
$pid = (string)($in['productId'] ?? '');
if (!isset(PRODUCTS[$pid])) { http_response_code(400); exit('{"error":"product"}'); }

$clean = fn($v) => mb_substr(trim(strip_tags((string)$v)), 0, 200);
$name = $clean($in['name'] ?? '');
$contact = $clean($in['contact'] ?? '');
if ($pid === 'personal-consultation' && ($name === '' || $contact === '')) { http_response_code(400); exit('{"error":"fields"}'); }

$o = [
  'id'         => next_order_id(),
  'product'    => $pid,
  'amount'     => PRODUCTS[$pid]['price'],
  'status'     => 'new',
  'created_at' => time(),
  'token'      => bin2hex(random_bytes(20)),
  'name'       => $name,
  'contact'    => $contact,
  'marketing'  => !empty($in['marketingConsent']),
  'downloads'  => 0,
];
order_save($o);
echo json_encode(['checkoutUrl' => payment_url($o), 'orderId' => $o['id']]);
