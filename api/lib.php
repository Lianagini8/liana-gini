<?php
// Общая логика оплаты: Робокасса + выдача файлов из приватного бакета Yandex Object Storage.
// Ключи и пароли лежат только на хостинге в api/_private/config.php (не в репозитории).

declare(strict_types=1);

const PRIVATE_DIR = __DIR__ . '/_private';
const DATA_DIR    = PRIVATE_DIR . '/data';
const GUARD       = "<?php exit; ?>\n"; // файлы данных — .php, чтобы веб-сервер никогда не отдал их содержимое

// Каталог товаров. Цены и названия совпадают с assets/js/payments.js.
const PRODUCTS = [
  'catalog_collections' => [
    'name' => 'Каталоги готовых трендовых и базовых коллекций', 'price' => 390, 'object' => 'intellectual_activity',
    'files' => [
      ['key' => 'katalog-1.pdf', 'title' => 'Каталог 1', 'size' => '9 МБ'],
      ['key' => 'katalog-2.pdf', 'title' => 'Каталог 2', 'size' => '32 МБ'],
      ['key' => 'katalog-3.pdf', 'title' => 'Каталог 3', 'size' => '32 МБ'],
      ['key' => 'lookbook.pdf',  'title' => 'Lookbook', 'size' => '75 МБ'],
    ],
  ],
  'factory_check_9' => [
    'name' => '9 шагов проверки фабрики', 'price' => 490, 'object' => 'intellectual_activity',
    'files' => [['key' => 'guide-9-shagov-proverki-fabriki.pdf', 'title' => '9 шагов проверки фабрики', 'size' => '3 МБ']],
  ],
  'brand_china_7' => [
    'name' => 'Как запустить свой бренд через Китай', 'price' => 490, 'object' => 'intellectual_activity',
    'files' => [['key' => 'guide-zapusk-brenda-7-shagov.pdf', 'title' => 'Как запустить свой бренд через Китай', 'size' => '3 МБ']],
  ],
  'guangzhou_markets' => [
    'name' => 'Список рынков Гуанчжоу с адресами', 'price' => 490, 'object' => 'intellectual_activity',
    'files' => [['key' => 'guide-rynki-guanchzhou.pdf', 'title' => 'Рынки Гуанчжоу', 'size' => '2 МБ']],
  ],
  'personal-consultation' => [
    'name' => 'Личная консультация с Лианой Гини', 'price' => 15000, 'object' => 'service',
    'files' => [],
  ],
];

function cfg(): array {
  static $c = null;
  if ($c === null) {
    $f = PRIVATE_DIR . '/config.php';
    if (!is_file($f)) { http_response_code(503); exit('Оплата временно недоступна.'); }
    $c = require $f;
  }
  return $c;
}

function rk(string $k) {
  $r = cfg()['robokassa'];
  if ($k === 'pass1' || $k === 'pass2') return !empty($r['test']) ? $r['test_' . $k] : $r[$k];
  return $r[$k] ?? null;
}

function rk_hash(string $s): string {
  $algo = strtolower((string)(rk('hash') ?: 'md5'));
  return strtoupper(hash($algo, $s));
}

// ---------- хранилище заказов ----------

function data_dir(): string {
  if (!is_dir(DATA_DIR)) mkdir(DATA_DIR, 0700, true);
  return DATA_DIR;
}

function next_order_id(): int {
  $f = data_dir() . '/counter.php';
  $h = fopen($f, 'c+');
  flock($h, LOCK_EX);
  $raw = stream_get_contents($h);
  $n = (int)trim(str_replace(GUARD, '', (string)$raw));
  $n = $n > 0 ? $n + 1 : 1001;
  ftruncate($h, 0); rewind($h);
  fwrite($h, GUARD . $n);
  flock($h, LOCK_UN); fclose($h);
  return $n;
}

function order_path(int $id): string { return data_dir() . '/order-' . $id . '.php'; }

function order_load(int $id): ?array {
  $f = order_path($id);
  if ($id <= 0 || !is_file($f)) return null;
  $j = json_decode(substr((string)file_get_contents($f), strlen(GUARD)), true);
  return is_array($j) ? $j : null;
}

function order_save(array $o): void {
  file_put_contents(order_path((int)$o['id']), GUARD . json_encode($o, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT), LOCK_EX);
}

// ---------- Робокасса ----------

function receipt_json(array $p): string {
  return json_encode([
    'sno'   => rk('sno') ?: 'usn_income',
    'items' => [[
      'name'           => mb_substr($p['name'], 0, 128),
      'quantity'       => 1,
      'sum'            => $p['price'],
      'payment_method' => 'full_payment',
      'payment_object' => $p['object'],
      'tax'            => 'none',
    ]],
  ], JSON_UNESCAPED_UNICODE);
}

function payment_url(array $o): string {
  $p = PRODUCTS[$o['product']];
  $sum = number_format((float)$p['price'], 2, '.', '');
  $login = rk('login');
  $parts = [$login, $sum, (string)$o['id']];
  $q = [
    'MerchantLogin' => $login,
    'OutSum'        => $sum,
    'InvId'         => $o['id'],
    'Description'   => mb_substr($p['name'], 0, 100),
    'Culture'       => 'ru',
    'Encoding'      => 'utf-8',
  ];
  if (rk('receipt')) {
    $receipt = urlencode(receipt_json($p)); // в подписи — один раз закодированный чек
    $parts[] = $receipt;
    $q['Receipt'] = $receipt;               // http_build_query закодирует второй раз, как требует Робокасса
  }
  $parts[] = rk('pass1');
  $q['SignatureValue'] = rk_hash(implode(':', $parts));
  if (!empty($o['email'])) $q['Email'] = $o['email']; // подставится на странице оплаты, туда же уйдёт чек
  if (rk('test')) $q['IsTest'] = 1;
  return 'https://auth.robokassa.ru/Merchant/Index.aspx?' . http_build_query($q);
}

function sig_ok(string $sum, string $inv, string $sig, string $pass): bool {
  return hash_equals(rk_hash($sum . ':' . $inv . ':' . $pass), strtoupper(trim($sig)));
}

// ---------- выдача файлов ----------

function access_url(array $o): string {
  return rtrim(cfg()['site'], '/') . '/api/access.php?o=' . $o['id'] . '&t=' . $o['token'];
}

function access_check(): array {
  $id = (int)($_GET['o'] ?? 0);
  $t  = (string)($_GET['t'] ?? '');
  $o  = order_load($id);
  if (!$o || empty($o['token']) || !hash_equals($o['token'], $t)) page('Ссылка недействительна', '<p>Проверьте ссылку из письма или напишите нам.</p>', 404);
  if (($o['status'] ?? '') !== 'paid') page('Оплата ещё не подтверждена', '<p>Обновите страницу через минуту.</p>', 402);
  return $o;
}

function access_expired(array $o): bool {
  return time() > (int)$o['paid_at'] + 86400 * (int)(cfg()['access_days'] ?? 30);
}

// Подписанная ссылка AWS SigV4 (Yandex Object Storage совместим с S3), живёт $ttl секунд.
function presign(string $key, string $downloadName, int $ttl = 600, ?int $ts = null): string {
  $s = cfg()['storage'];
  $host = $s['endpoint'];
  $region = $s['region'] ?? 'ru-central1';
  $now = gmdate('Ymd\THis\Z', $ts ?? time());
  $day = substr($now, 0, 8);
  $scope = "$day/$region/s3/aws4_request";
  $path = '/' . $s['bucket'] . '/' . implode('/', array_map('rawurlencode', explode('/', $key)));
  $params = [
    'X-Amz-Algorithm'  => 'AWS4-HMAC-SHA256',
    'X-Amz-Credential' => $s['key_id'] . '/' . $scope,
    'X-Amz-Date'       => $now,
    'X-Amz-Expires'    => (string)$ttl,
    'X-Amz-SignedHeaders' => 'host',
    'response-content-disposition' => "attachment; filename=\"download.pdf\"; filename*=UTF-8''" . rawurlencode($downloadName),
  ];
  ksort($params);
  $qs = implode('&', array_map(fn($k, $v) => rawurlencode($k) . '=' . rawurlencode($v), array_keys($params), $params));
  $canonical = "GET\n$path\n$qs\nhost:$host\n\nhost\nUNSIGNED-PAYLOAD";
  $toSign = "AWS4-HMAC-SHA256\n$now\n$scope\n" . hash('sha256', $canonical);
  $k = hash_hmac('sha256', $day, 'AWS4' . $s['secret'], true);
  $k = hash_hmac('sha256', $region, $k, true);
  $k = hash_hmac('sha256', 's3', $k, true);
  $k = hash_hmac('sha256', 'aws4_request', $k, true);
  $sig = hash_hmac('sha256', $toSign, $k);
  return "https://$host$path?$qs&X-Amz-Signature=$sig";
}

// ---------- письма ----------

function send_mail(string $to, string $subject, string $text): void {
  if (!filter_var($to, FILTER_VALIDATE_EMAIL)) return;
  $from = cfg()['mail_from'] ?? 'no-reply@lianagini.ru';
  $headers = "From: LIANA GINI <$from>\r\nContent-Type: text/plain; charset=UTF-8\r\nContent-Transfer-Encoding: 8bit";
  @mail($to, '=?UTF-8?B?' . base64_encode($subject) . '?=', $text, $headers, '-f' . $from);
}

// ---------- страница в стиле сайта ----------

function h(string $s): string { return htmlspecialchars($s, ENT_QUOTES, 'UTF-8'); }

function page(string $title, string $body, int $code = 200, string $head = ''): void {
  http_response_code($code);
  header('Content-Type: text/html; charset=utf-8');
  header('Cache-Control: no-store');
  header('X-Robots-Tag: noindex');
  echo '<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    . '<meta name="robots" content="noindex"><title>' . h($title) . ' — LIANA GINI</title>' . $head
    . '<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700&display=swap" rel="stylesheet">'
    . '<style>body{margin:0;background:#F2EFE8;color:#181715;font-family:Manrope,system-ui,sans-serif;line-height:1.5}'
    . '.w{max-width:620px;margin:0 auto;padding:56px 20px 72px}.logo{font-weight:700;letter-spacing:3px;font-size:14px;color:#181715;text-decoration:none}'
    . 'h1{font-size:30px;line-height:1.15;text-transform:uppercase;margin:40px 0 16px;letter-spacing:.3px}p{font-size:16px;margin:0 0 14px}'
    . '.f{display:flex;justify-content:space-between;align-items:center;gap:16px;padding:18px 0;border-bottom:1px solid rgba(24,23,21,.15)}'
    . '.f span{font-weight:600}.f small{display:block;font-weight:400;opacity:.55;font-size:13px}.btn{display:inline-block;background:#541F2B;color:#F2EFE8;text-decoration:none;font-weight:700;font-size:13px;letter-spacing:.5px;text-transform:uppercase;padding:12px 18px;white-space:nowrap}'
    . '.btn:hover{background:#181715}.note{opacity:.65;font-size:14px;margin-top:22px}a{color:#541F2B}</style></head><body><div class="w">'
    . '<a class="logo" href="/">LIANA GINI</a><h1>' . h($title) . '</h1>' . $body . '</div></body></html>';
  exit;
}
