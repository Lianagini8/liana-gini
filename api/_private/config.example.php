<?php
// ОБРАЗЕЦ. На хостинге скопируйте в config.php (в эту же папку api/_private/)
// и впишите значения. config.php в репозиторий НЕ добавлять: там пароли.
return [
  // Робокасса → Мои магазины → Технические настройки
  'robokassa' => [
    'login'     => 'ИДЕНТИФИКАТОР_МАГАЗИНА',
    'pass1'     => 'ПАРОЛЬ_1',
    'pass2'     => 'ПАРОЛЬ_2',
    'test'      => true,          // true — тестовые платежи (тестовые пароли), false — боевые
    'test_pass1'=> 'ТЕСТОВЫЙ_ПАРОЛЬ_1',
    'test_pass2'=> 'ТЕСТОВЫЙ_ПАРОЛЬ_2',
    'hash'      => 'md5',         // алгоритм расчёта хеша из Технических настроек: md5 / sha256 / sha384 / sha512
    'receipt'   => true,          // передавать чек (54-ФЗ, Робочеки)
    'sno'       => 'usn_income',  // система налогообложения: usn_income (доходы) или usn_income_outcome (доходы минус расходы)
  ],
  // Yandex Object Storage: статический ключ сервисного аккаунта (только чтение)
  'storage' => [
    'bucket'     => 'lianagini-materials',
    'key_id'     => 'ИДЕНТИФИКАТОР_КЛЮЧА',
    'secret'     => 'СЕКРЕТНЫЙ_КЛЮЧ',
    'endpoint'   => 'storage.yandexcloud.net',
    'region'     => 'ru-central1',
  ],
  'site'         => 'https://lianagini.ru',
  'notify_email' => 'liana.Giniyatulina@yandex.com', // уведомления о заказах
  'mail_from'    => 'no-reply@lianagini.ru',
  'access_days'  => 30,   // сколько дней покупатель может скачивать файлы
  'max_downloads'=> 40,   // лимит скачиваний на заказ
];
