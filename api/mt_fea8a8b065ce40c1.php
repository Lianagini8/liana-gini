<?php
// Временная диагностика отправки почты. Удалить после проверки.
header('Content-Type: text/plain; charset=utf-8');
$to = 'belovachristina1995@gmail.com';
$h = "From: LIANA GINI <no-reply@lianagini.ru>\r\nContent-Type: text/plain; charset=UTF-8";
$r1 = mail($to, '=?UTF-8?B?' . base64_encode('Тест 1 (с -f)') . '?=', "Тест отправки 1", $h, '-fno-reply@lianagini.ru');
$r2 = mail($to, '=?UTF-8?B?' . base64_encode('Тест 2 (без -f)') . '?=', "Тест отправки 2", $h);
echo "mail1=" . var_export($r1, true) . "\nmail2=" . var_export($r2, true) . "\n";
echo "sendmail_path=" . ini_get('sendmail_path') . "\nhost=" . gethostname() . "\n";
echo "disabled=" . ini_get('disable_functions') . "\n";
