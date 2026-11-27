#!/usr/bin/env python3
"""Собирает английскую версию сайта в папку en/ из русских файлов и таблицы перевода.

Русские файлы не меняются. lianagini.com показывает содержимое en/ (правило в .htaccess).
После запуска: node _tools/prerender.mjs en/index.html en/mobile.html

Запуск: python3 _tools/build_en.py [путь к xlsx]
Если xlsx указан, переводы обновляются в _tools/en-translations.json (колонка F «Правка Кати»
важнее колонки I). Без аргумента сборка идёт по сохранённому JSON.
"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'en'
STORE = ROOT / '_tools' / 'en-translations.json'
CYR = re.compile(r'[А-Яа-яЁё]')
ARROWS = '←→↑↓↗'

HTML_FILES = [
    'index.html', 'mobile.html', 'hero.dc.html',
    *[f'section-{n:02d}.dc.html' for n in range(2, 11)],
    'oferta.html', 'user-agreement.html', 'privacy-policy.html', 'pd-consent.html', 'ad-consent.html', 'cookie-policy.html', 'requisites.html',
]
JS_FILES = ['assets/js/payments.js', 'assets/js/cookie-banner.js']

BLOCK = set('div p h1 h2 h3 h4 h5 h6 li td th a button label section header footer nav ul ol option summary dt dd figcaption blockquote form article aside main tr table select input textarea img title body head html meta link'.split())
SKIP = {'style', 'script', 'svg', 'template'}
TOKEN = re.compile(r"""<!--.*?-->|<[a-zA-Z/!](?:"[^"]*"|'[^']*'|[^'">])*>|[^<]+|<""", re.S)
ATTR = re.compile(r"""([\w:-]+)=("[^"]*"|'[^']*')""")
JS_STR = re.compile(r"""'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"|`((?:[^`\\]|\\.)*)`""", re.S)

# Цены на английской версии (Кристина 09.11.2026)
# Оплата через Робокассу в рублях (решение Лианы 11.11), поэтому на карточках «≈», а в окне оплаты сумма в рублях.
PRICES = [('15&nbsp;000&nbsp;₽', '≈ $185'), ('15 000 ₽', '≈ $185'), ('15 000 ₽', '≈ $185'), ('390 ₽', '≈ $5'), ('390 ₽', '≈ $5'), ('490 ₽', '≈ $6'), ('490 ₽', '≈ $6')]
PRICE_LABEL = ("product.price.toLocaleString('ru-RU') + ' ₽'", "({390:'390 ₽ (≈ $5)',490:'490 ₽ (≈ $6)',15000:'15 000 ₽ (≈ $185)'})[product.price]")
MOBILE_LABEL = ('this.state.checkoutProduct.priceLabel :', "(({'≈ $5':'390 ₽ (≈ $5)','≈ $6':'490 ₽ (≈ $6)','≈ $185':'15 000 ₽ (≈ $185)'})[this.state.checkoutProduct.priceLabel] || this.state.checkoutProduct.priceLabel) :")

# Фразы, которых нет в таблице в таком виде: разметка делит их иначе.
EXTRA = {
    'наверх': 'Back to top',
    'посчитать партию': 'Cost my order',  # термин Кати 12.11: партия = order
    'посчитать первую партию': 'Cost my first order',
    '260 продаж в день': '260 sales a day.',
    # названия каталогов, добавленных 15.11.2026
    'пальто и куртки 2026/27': 'Coats and Jackets 2026/27',
    'женская верхняя одежда, весна 2026/2027': 'Women’s Spring Outerwear 2026/2027',
    'замшевые и кожаные юбки 2026/27': 'Suede and Leather Skirts 2026/27',
    'выращенные бриллианты': 'Lab-Grown Diamonds',
    'каталог 2': 'Catalogue 2',
    'каталог 3': 'Catalogue 3',
    'политике cookie': 'Cookie Policy',
    'команда лианы гини работает в гуанчжоу': 'Liana Gini’s team works in Guangzhou.',
    'разработка и производство одежды, обуви и аксессуаров в китае: от идеи и образца до контроля готовой партии': 'We develop and manufacture clothing, footwear and accessories in China, from idea and sample to quality control of the finished order',
    'востоковед, магистр делового администрирования. переговорная экспертиза, многолетний опыт работы с производством в китае': 'Asian studies graduate, MBA. Skilled negotiator with years of hands-on experience with manufacturing in China',
    'мы используем файлы cookie и локальное хранилище для корректной работы сайта. подробнее — в': 'We use cookies and local storage to keep the site working properly. See our ',  # пробел перед ссылкой
}

# Строки, где финальный текст Кати (12.11) расходится с русским сайтом. Перевод должен совпадать с русским.
FIXES = {
    # Кристина 12.11: консультация 30–60 минут (у Кати было «30 minutes», на сайте было 60).
    '30–60 минут продуктивного разговора с Лианой Гини, который закроет ВСЕ ваши вопросы, сформирует персональную дорожную карту от продукта до карго.':
        '30–60 minutes with Liana Gini that will answer ALL your questions and give you a personal roadmap from product to freight.',
    # Кати: «Our own developments». Разработки клиента, а не наши.
    'Для собственных разработок предусмотрена работа по NDA.':
        'For your own designs, we work under an NDA.',
    'Для собственных разработок предусмотрена работа по NDA — особенно важно для новых моделей, эксклюзивных тканей и решений, принадлежащих бренду клиента.':
        'For your own designs, we work under an NDA, which matters most for new styles, exclusive fabrics and anything that belongs to the client’s brand.',
    # У Кати адрес сайта выпал из фразы. Документы на английском лежат на lianagini.com.
    '1.1. Сайт — интернет-ресурс Исполнителя, расположенный по адресу https://lianagini.ru (включая связанные страницы, формы обратной связи и чат-бот).':
        '1.1. Website means the Contractor’s internet resource located at https://lianagini.com (including related pages, feedback forms and the chatbot).',
    '1.3. Политика действует в отношении всех персональных данных, обрабатываемых Оператором, в том числе получаемых через сайт Оператора https://lianagini.ru (далее — Сайт), формы обратной связи и чат-бот.':
        '1.3. The Policy applies to all personal data processed by the Operator, including data obtained through the Operator’s website https://lianagini.com (hereinafter referred to as the “Website”), feedback forms and the chatbot.',
    # В юридическом ряду подвала все ссылки с заглавных, у Кати одна строчными.
    'Согласие на рассылки': 'Marketing Consent',
    # Лиана 24.11: для иностранных клиентов не ГОСТ, а международные стандарты.
    'Размерные сетки — по ГОСТу.': 'Size charts to international standards.',
    # 25.11: бриф ведёт на оплату консультации. Заголовок и подзаголовок Кати, перевод мой (Кате на вычитку).
    'ОБСУДИМ ВАШЕ ПРОИЗВОДСТВО НА КОНСУЛЬТАЦИИ': 'A CONSULTATION ON YOUR PRODUCTION',
    'Обсудим ваше производство на консультации': 'A consultation on your production',
    # 26.11: фразу о зачёте суммы в заказ Кристина убрала (Лиана уточняет у юриста).
    'Консультация оплачивается заранее: 15 000, 30–60 мин.':
        'The consultation is paid in advance: 15,000\u00a0RUB (≈\u00a0$185), 30–60\u00a0min.',
    'Как к вам обращаться?': 'What should we call you?',
    'Имя': 'Name',
    'Email для чека': 'Email for the receipt',
    'Перейти к оплате →': 'Proceed to payment',
    'ПЕРЕЙТИ К ОПЛАТЕ →': 'PROCEED TO PAYMENT',
    'После оплаты команда свяжется с вами и согласует время консультации.': 'After payment, the team will contact you to arrange the consultation time.',
    'Создаём заказ и переходим к оплате…': 'Creating your order and going to payment…',
    'Заполните задачу, телефон, имя и email для чека.': 'Please fill in your task, phone, name and email for the receipt.',
    'Не удалось перейти к оплате. Попробуйте ещё раз или напишите в Telegram.': 'Could not go to payment. Please try again or message us on Telegram.',
    'Укажите имя, чтобы продолжить.': 'Please enter your name to continue.',
    'Укажите email, на него придёт чек.': 'Please enter your email: the receipt will be sent there.',
    'Мессенджер для связи': 'Messenger to contact you',
    'Что входит в консультацию': 'What the consultation includes',
    # 27.11: форма записи на консультацию по макету Кати
    'ЗАПИСЬ НА КОНСУЛЬТАЦИЮ': 'BOOK A CONSULTATION',
    'Запись на консультацию': 'Book a consultation',
    'Заполните анкету, чтобы Лиана заранее изучила вашу задачу. После оплаты мы свяжемся с вами и согласуем удобное время.':
        'Fill in the form so Liana can review your project in advance. After payment, we will contact you to arrange a convenient time.',
    'Консультация оплачивается заранее. Если после консультации вы размещаете заказ, эта сумма засчитывается в его стоимость.':
        'The consultation is paid in advance. If you place an order after the consultation, this amount is credited towards it.',
    'Выберите консультацию': 'Choose a consultation',
    'Уже продаю одежду': 'I already sell clothing',
    'Запускаю первый бренд': 'I am launching my first brand',
    '30–60 мин · 15 000 ₽': '30–60\u00a0min · 15,000\u00a0RUB (≈\u00a0$185)',
    'Понимаю, что консультация платная': 'I understand that the consultation is paid',
    'Заполните задачу, телефон, имя, email для чека и отметьте, что консультация платная.':
        'Please fill in your task, phone, name and email for the receipt, and confirm that the consultation is paid.',
    'ОПЛАТИТЬ ≈ $185 →': 'PAY 15,000 RUB (≈ $185)',
    'Оплатить ≈ $185 →': 'Pay 15,000 RUB (≈ $185)',
    'ОПЛАТИТЬ 20 000 ₽ →': 'PAY 20,000 RUB',
    'Оплатить 20 000 ₽ →': 'Pay 20,000 RUB',
    'Консультация: как открыть и вести компанию в Китае': 'Consultation: how to open and run a company in China',
    'Каталоги: лабораторные бриллианты': 'Catalogues: lab-grown diamonds',
    'Каталоги: одежда': 'Catalogues: clothing',
    'Каталоги: мебель и декор': 'Catalogues: furniture and decor',
}

# Turnkey («под ключ») во вкладке обрезалось до «Turnkey Cl…» и читалось как Turkey —
# для производства в Китае это худшее недоразумение. «Под ключ» осталось в описании.
SEO_TITLE = 'Clothing Manufacturing in China | Liana Gini'
SEO_DESC = 'We develop and manufacture clothing, footwear and accessories in China, turnkey: from idea and sample to quality control of the finished order. Liana Gini’s team works in Guangzhou.'

issues = []


def key(s):
    s = html.unescape(str(s)).replace(' ', ' ').replace('\\u00A0', ' ').replace('\\n', ' ').replace('​', '').replace('‑', '-')
    s = re.sub(r'\{\{\s*([^}]*?)\s*\}\}', r'{\1}', s)
    s = re.sub(f'[{ARROWS}]', '', s)
    s = re.sub(r'\s+', ' ', s).strip().strip('—–- ').rstrip('.:').casefold().replace('ё', 'е')
    return s


def load_table(path):
    import openpyxl
    wb = openpyxl.load_workbook(path)
    out = {}
    for name in ['Сайт', 'Документы', 'Соглашение', 'Оплата и письма']:
        if name not in wb.sheetnames:
            continue
        ws = wb[name]
        head = [c.value for c in ws[1]]
        ru, final, katya = head.index('Русский'), head.index('English — редактура ChatGPT'), head.index('Правка Кати')
        for r in ws.iter_rows(min_row=2, values_only=True):
            if not r[ru]:
                continue
            fix = str(r[katya] or '').strip()
            out[key(r[ru])] = fix if fix and fix.casefold() not in ('ок', 'ok') else str(r[final])
    return out


def upper_ratio(t):
    letters = [c for c in t if c.isalpha()]
    return sum(c.isupper() for c in letters) / max(1, len(letters))


def render(raw, en):
    """Переносит на английский текст стрелки и заглавные буквы исходной строки."""
    plain = html.unescape(raw).replace('\\u00A0', ' ').strip()
    head = re.match(rf'^[{ARROWS}]\s*', plain)
    tail = re.search(rf'\s*[{ARROWS}]$', plain)
    if upper_ratio(plain) >= 0.6:
        en = en.upper()
    if head:
        en = head.group(0) + en
    if tail:
        en += tail.group(0)
    return en


def lookup(T, raw):
    return T.get(key(raw))


def tr_html(T, src, name):
    tokens = [m.group(0) for m in TOKEN.finditer(src)]
    skip = 0
    seg = []  # индексы токенов текущего блока

    def flush():
        nonlocal seg
        texts = [i for i in seg if not tokens[i].startswith('<')]
        joined = ' '.join(tokens[i] if not tokens[i].startswith('<') else (' ' if re.match(r'<br', tokens[i], re.I) else '') for i in seg)
        seg_list, seg = seg, []
        if not CYR.search(joined):
            return
        en = lookup(T, joined)
        if en is not None:
            # пробелы между тегами не трогаем: перевод встаёт на место первого настоящего текста
            texts = [i for i in texts if tokens[i].strip()]
            first = texts[0]
            lead = re.match(r'\s*', tokens[first]).group(0)
            trail = re.search(r'\s*$', tokens[texts[-1]]).group(0)
            tokens[first] = lead + html.escape(render(joined, en), quote=False) + trail
            for i in texts[1:]:
                tokens[i] = ''
            for i in seg_list:
                if re.match(r'<br', tokens[i], re.I):
                    tokens[i] = ''
            return
        for i in texts:  # разметка делит фразу на части: переводим каждую
            if CYR.search(tokens[i]):
                en = lookup(T, tokens[i])
                if en is None:
                    issues.append((name, 'text', re.sub(r'\s+', ' ', tokens[i]).strip()))
                    continue
                t = tokens[i]
                tokens[i] = re.match(r'\s*', t).group(0) + html.escape(render(t, en), quote=False) + re.search(r'\s*$', t).group(0)

    for i, tok in enumerate(tokens):
        if tok.startswith('<!--'):
            continue
        if tok.startswith('<') and len(tok) > 1:
            m = re.match(r'</?\s*([a-zA-Z0-9-]+)', tok)
            tag = m.group(1).lower() if m else ''
            closing = tok.startswith('</')
            if tag in SKIP:
                if not closing and not tok.endswith('/>'):
                    skip += 1
                elif closing:
                    skip = max(0, skip - 1)
                flush()
                continue
            if skip:
                continue
            if not closing and CYR.search(tok):
                def attr(a):
                    v = a.group(2)[1:-1]
                    if not CYR.search(v) or '{{' in v:
                        return a.group(0)
                    en = lookup(T, v)
                    if en is None:
                        issues.append((name, 'attr:' + a.group(1), v))
                        return a.group(0)
                    q = a.group(2)[0]
                    return f'{a.group(1)}={q}{html.escape(en, quote=True)}{q}'
                tokens[i] = tok = ATTR.sub(attr, tok)
            if tag in BLOCK or tag == 'br' and False:
                flush()
            elif tag in ('br', 'span', 'b', 'i', 'em', 'strong', 'small', 'sup', 'sub', 'u'):
                seg.append(i)
            else:
                flush()
            continue
        if not skip:
            seg.append(i)
    flush()
    return ''.join(tokens)


def tr_js(T, code, name):
    def one(m):
        raw = m.group(1) if m.group(1) is not None else m.group(2) if m.group(2) is not None else m.group(3)
        q = m.group(0)[0]
        if raw is None or not CYR.search(raw):
            return m.group(0)
        body, suffix = raw, ''
        if '||' in raw:
            body, suffix = raw.split('||', 1)
            suffix = '||' + suffix
        en = lookup(T, body)
        if en is None:
            issues.append((name, 'js', body[:140]))
            return m.group(0)
        en = render(body, en).replace('\\', '\\\\').replace(q, '\\' + q).replace('\n', ' ')
        return q + en + suffix + q
    # комментарии не трогаем: строки внутри них не показываются на сайте
    parts = re.split(r'(/\*.*?\*/|(?<![:\'"])//[^\n]*)', code, flags=re.S)
    return ''.join(p if i % 2 else JS_STR.sub(one, p) for i, p in enumerate(parts))


def tr_scripts(T, src, name):
    def one(m):
        if 'ld+json' in m.group(1) or re.search(r'\bsrc=', m.group(1)):
            return m.group(0)
        return f'<script{m.group(1)}>' + tr_js(T, m.group(2), name) + '</script>'
    return re.sub(r'<script([^>]*)>(.*?)</script>', one, src, flags=re.S | re.I)


def to_source(s):
    hs, he = s.find('<!--dc-prerender:head-->'), s.find('<!--/dc-prerender:head-->')
    if hs != -1 and he != -1:
        s = s[:hs] + s[he + len('<!--/dc-prerender:head-->'):]
    bs, be = s.find('<!--dc-prerender:body-->'), s.find('<!--/dc-prerender:body-->')
    if bs != -1 and be != -1:
        block = s[bs:be]
        op = re.search(r'<x-dc(?:\s[^>]*)?>', block)
        cl = block.rfind('</x-dc>')
        s = s[:bs] + block[op.start():cl + len('</x-dc>')] + s[be + len('<!--/dc-prerender:body-->'):]
    return s


def by_sentences(T, text):
    """Ответы в разметке склеены из нескольких строк таблицы: ищем самые длинные куски."""
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    out, i = [], 0
    while i < len(parts):
        for j in range(len(parts), i, -1):
            en = lookup(T, ' '.join(parts[i:j]))
            if en is not None:
                out.append(en)
                i = j
                break
        else:
            return None
    return ' '.join(out)


def tr_ld(T, node):
    if isinstance(node, dict):
        return {k: tr_ld(T, v) for k, v in node.items()}
    if isinstance(node, list):
        return [tr_ld(T, v) for v in node]
    if isinstance(node, str):
        node = node.replace('https://lianagini.ru', 'https://lianagini.com')
        if CYR.search(node):
            en = lookup(T, node) or by_sentences(T, node)
            if en is None:
                issues.append(('json-ld', 'text', node[:140]))
                return node
            return en
    return node


def seo_head(T, s, page):
    m = re.search(r'<!--seo:head.*?<!--/seo:head-->', s, flags=re.S)
    if not m:
        issues.append((page, 'seo', 'нет блока seo:head'))
        return s
    head = re.sub(r'<link rel="alternate" hreflang="[a-z]+"[^>]*>\n', '', m.group(0))
    head = re.sub(r'<title>.*?</title>', f'<title>{SEO_TITLE}</title>', head, flags=re.S)
    for attr in ('name="description"', 'property="og:title"', 'property="og:description"'):
        text = SEO_TITLE if 'title' in attr else SEO_DESC
        head = re.sub(rf'(<meta {attr} content=")[^"]*(")', lambda a: a.group(1) + html.escape(text, quote=True) + a.group(2), head)
    head = head.replace('ru_RU', 'en_US').replace('https://lianagini.ru', 'https://lianagini.com')
    ld = re.search(r'(<script type="application/ld\+json">)(.*?)(</script>)', head, flags=re.S)
    if ld:
        data = tr_ld(T, json.loads(ld.group(2)))
        head = head[:ld.start(2)] + '\n' + json.dumps(data, ensure_ascii=False, indent=1) + '\n' + head[ld.end(2):]
    links = '<link rel="alternate" hreflang="en" href="https://lianagini.com/">\n<link rel="alternate" hreflang="ru" href="https://lianagini.ru/">\n'
    head = re.sub(r'(<link rel="canonical"[^>]*>\n)', lambda a: a.group(1) + links, head, count=1)
    return s[:m.start()] + head + s[m.end():]


def en_reviews(s):
    """Скриншоты отзывов заменяются переводом. Подпись о переводе обязательна: клиенты писали по-русски."""
    swaps = [
        ("height:120px;background-image:url('assets/media/review-fabric.jpg');background-size:368px auto;background-position:center 12%;background-repeat:no-repeat;",
         "aspect-ratio:1080/335;background-image:url('assets/media/en-review-1.jpg');background-size:100% auto;background-repeat:no-repeat;"),
        ("height:104px;background-image:url('assets/media/review-shipment.jpg');background-size:423px auto;background-position:center 26%;background-repeat:no-repeat;",
         "aspect-ratio:1080/468;background-image:url('assets/media/en-review-2.jpg');background-size:100% auto;background-repeat:no-repeat;"),
        ('FROM A CONVERSATION WITH THE CLIENT', 'FROM A CONVERSATION WITH THE CLIENT, TRANSLATED FROM RUSSIAN'),
    ]
    for a, b in swaps:
        if a not in s:
            issues.append(('section-06', 'reviews', a[:60]))
        s = s.replace(a, b)
    note = '      <div style="font-size:8px;letter-spacing:1.5px;text-transform:uppercase;margin-top:8px;opacity:.45;">Translated from Russian</div>\n'
    return re.sub(r"(<div[^\n]*en-review-2\.jpg[^\n]*\n)", lambda m: m.group(1) + note, s, count=1)


# Слаги посадочных страниц: они есть только на .ru. Если такая ссылка
# осталась в английской сборке, на .com она даст 404.
RU_ONLY_SLUGS = (
    'o-liane-gini', 'konsultaciya', 'baier-v-kitae', 'detskaya-odezhda', 'nizhnee-bele',
    'gotovye-kollekcii', 'svoy-brend-odezhdy', 'rynki-guanchzhou', 'kontrol-kachestva',
    'sportivnaya-odezhda', 'tkani', 'furnitura', 'furnitura-s-logotipom',
    'soprovozhdenie-v-guanchzhou', 'kak-najti-fabriku', 'katalogi',
)
# Блоки со ссылками на посадочные (меню «Услуги»/«Материалы», ссылки «Название →»
# в разделах главной) помечены комментариями ru-pages и вырезаются для .com целиком.
RU_PAGES_BLOCKS = {
    'hero.dc.html': ['nav-desktop'],
    'section-03.dc.html': ['step1', 'step2', 'step3', 'step5'],
    'section-05.dc.html': ['team'],
    'section-06.dc.html': ['cases'],
    'section-07.dc.html': ['catalogs'],
    'section-09.dc.html': ['agency', 'company-consult'],
    'section-10.dc.html': ['company-option', 'company-plan'],
    'mobile.html': ['services-mobile', 'steps-mobile', 'team-mobile', 'cases-mobile', 'catalogs-mobile', 'agency-mobile', 'company-consult-mobile', 'company-option-mobile', 'company-plan-mobile'],
}
# Что встаёт на место блока в английской сборке (до перевода, поэтому по-русски).
RU_PAGES_EN = {
    'nav-desktop': '        <a href="#services" style="font-size:12px;font-weight:500;letter-spacing:1px;text-transform:uppercase;color:{{ ivory }};" style-hover="color:{{ accent }};">Услуги</a>\n',
}


def drop_ru_pages(s, name):
    """Посадочные страницы есть только на .ru: в английской сборке ссылок на них быть не должно."""
    for key in RU_PAGES_BLOCKS.get(name, []):
        pat = r'[ \t]*<!-- ru-pages:%s -->.*?<!-- /ru-pages:%s -->\n' % (re.escape(key), re.escape(key))
        s, n = re.subn(pat, lambda m: RU_PAGES_EN.get(key, ''), s, flags=re.S)
        if n != 1:
            issues.append((name, 'ru-pages', 'не найден блок ru-pages:' + key))
    left = re.findall(r'<!-- ru-pages:([a-z0-9-]+) -->', s)
    if left:
        issues.append((name, 'ru-pages', 'блок не вырезан, добавьте в RU_PAGES_BLOCKS: ' + ', '.join(left)))
    if name == 'section-10.dc.html':
        # ссылка на страницу консультации заменяется на блок консультации этой же страницы
        if 'href="/konsultaciya/"' not in s:
            issues.append((name, 'footer', 'не найдена ссылка на /konsultaciya/'))
        s = s.replace('href="/konsultaciya/"', 'href="#consultation"')
    before = s
    s = re.sub(r'(?:\s*·)?\s*<a href="/(?:o-liane-gini|konsultaciya)/"[^>]*>[^<]*</a>', '', s)
    if s == before and name == 'section-10.dc.html':
        issues.append((name, 'footer', 'не найдена ссылка на /o-liane-gini/'))
    for slug in RU_ONLY_SLUGS:
        if 'href="/%s/"' % slug in s:
            issues.append((name, 'ru-pages', 'осталась ссылка на русскую страницу /%s/' % slug))
    return s


# Переключатель версий. На русском сайте активен RU и ссылка ведёт на .com,
# на английском наоборот. Язык в подписи называем на самом этом языке.
LANG_SWITCH = {
    'top-desktop': '<div style="width:130px;flex-shrink:0;display:flex;align-items:center;justify-content:flex-end;">\n      <div style="display:flex;align-items:center;gap:9px;font-size:12px;font-weight:500;letter-spacing:1px;background:rgba(14,11,10,0.38);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);padding:7px 13px;">\n        <a href="https://lianagini.ru/" hreflang="ru" style="color:{{ ivory }};opacity:0.6;" style-hover="color:{{ accent }};opacity:1;">RU</a>\n        <span style="color:{{ ivory }};opacity:0.35;" aria-hidden="true">/</span>\n        <span style="color:{{ ivory }};" aria-current="true">EN</span>\n      </div>\n    </div>',
    'footer-desktop': '<a href="https://lianagini.ru/" hreflang="ru" style="font-size:11px;font-weight:600;letter-spacing:1.2px;text-transform:uppercase;color:{{ ivory }};opacity:0.7;" style-hover="opacity:1;color:{{ accentLight }};">РУССКАЯ ВЕРСИЯ</a>',
    'top-mobile': '<div style="display:flex;align-items:center;gap:7px;font-size:11px;font-weight:600;letter-spacing:1px;">\n          <a href="https://lianagini.ru/" hreflang="ru" style="color:{{ ink }};opacity:0.5;">RU</a>\n          <span style="opacity:0.25;" aria-hidden="true">/</span>\n          <span aria-current="true">EN</span>\n        </div>',
    'footer-mobile': '<a href="https://lianagini.ru/" hreflang="ru" style="color:{{ ivory }};opacity:1;">Русская версия</a>',
}
SWITCH_FILES = ('hero.dc.html', 'section-10.dc.html', 'mobile.html')


def lang_switch(s, name):
    """Меняет переключатель версий на английский вариант. Идёт после перевода:
    подписи RU/EN и «Русская версия» переводить не нужно."""
    def rep(m):
        k = m.group(1)
        if k not in LANG_SWITCH:
            issues.append((name, 'switch', 'нет английского варианта для ' + k))
            return m.group(0)
        return '<!-- lang-switch:%s -->%s<!-- /lang-switch:%s -->' % (k, LANG_SWITCH[k], k)

    before = s
    s = re.sub(r'<!-- lang-switch:([a-z-]+) -->.*?<!-- /lang-switch:\1 -->', rep, s, flags=re.S)
    if s == before and name in SWITCH_FILES:
        issues.append((name, 'switch', 'переключатель версий не найден'))
    return s


def php_str(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def main():
    if len(sys.argv) > 1:
        STORE.write_text(json.dumps(load_table(sys.argv[1]), ensure_ascii=False, indent=0), encoding='utf-8')
    T = json.loads(STORE.read_text(encoding='utf-8'))
    T.update(EXTRA)
    T.update({key(ru): en for ru, en in FIXES.items()})
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / 'js').mkdir(parents=True)

    for name in HTML_FILES:
        s = (ROOT / name).read_text(encoding='utf-8')
        s = to_source(s) if name in ('index.html', 'mobile.html') else s
        for a, b in PRICES:
            s = s.replace(a, b)
        s = s.replace(*PRICE_LABEL)
        if name == 'mobile.html':
            if MOBILE_LABEL[0] not in s:
                issues.append((name, 'price', 'не найдена подпись цены в окне оплаты'))
            s = s.replace(*MOBILE_LABEL)
        s = s.replace('name@mail.ru', 'name@example.com')
        s = drop_ru_pages(s, name)
        # Метки этапов и на русском сайте английские. Катя 12.11: «партия» = order, не batch.
        s = s.replace('opacity:0.5;">BATCH</span>', 'opacity:0.5;">ORDER</span>').replace("'QC', 'BATCH'", "'QC', 'ORDER'")
        # Лиана 24.11: на английской версии QC вместо Control.
        if name == 'hero.dc.html':
            if '>Control / Sample / Production<' not in s:
                issues.append((name, 'qc', 'не найдена строка Control / Sample / Production'))
            s = s.replace('>Control / Sample / Production<', '>QC / Sample / Production<')
        s = s.replace('/assets/js/payments.js', '/js/payments.js').replace('assets/js/cookie-banner.js', 'js/cookie-banner.js')
        s = re.sub(r'<html([^>]*)lang="ru"', r'<html\1lang="en"', s, count=1)
        if name in ('index.html', 'mobile.html'):
            s = seo_head(T, s, name)
        s = tr_scripts(T, s, name)
        s = tr_html(T, s, name)
        if name == 'section-06.dc.html':
            s = en_reviews(s)
        s = lang_switch(s, name)
        (OUT / name).write_text(s, encoding='utf-8')

    for rel in JS_FILES:
        s = tr_js(T, (ROOT / rel).read_text(encoding='utf-8'), rel)
        (OUT / 'js' / Path(rel).name).write_text(s, encoding='utf-8')

    s = (ROOT / 'sw.js').read_text(encoding='utf-8').replace('liana-gini-shell-', 'liana-gini-en-shell-')
    (OUT / 'sw.js').write_text(s, encoding='utf-8')

    # robots, карта сайта и манифест для lianagini.com
    (OUT / 'robots.txt').write_text('User-agent: *\nDisallow: /api/\n\nSitemap: https://lianagini.com/sitemap.xml\n', encoding='utf-8')
    pages = ['', 'oferta.html', 'user-agreement.html', 'privacy-policy.html', 'pd-consent.html', 'ad-consent.html', 'cookie-policy.html', 'requisites.html']
    urls = ''.join(f'  <url><loc>https://lianagini.com/{p}</loc></url>\n' for p in pages)
    (OUT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding='utf-8')
    man = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    man.update(name='Liana Gini | Production in China', description=lookup(T, man['description']) or SEO_DESC, lang='en')
    (OUT / 'manifest.json').write_text(json.dumps(man, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    # строки страниц оплаты и писем: api/_en.php
    php = ''
    for f in sorted((ROOT / 'api').glob('*.php')):
        if f.name != '_en.php':
            php += f.read_text(encoding='utf-8')
    wanted = set(re.findall(r"\bt\('([^']+)'\)", php)) | set(re.findall(r"'(?:name|title)' => '([^']*[А-Яа-яЁё][^']*)'", php))
    rows = []
    for ru in sorted(wanted):
        en = lookup(T, ru)
        if en is None:
            issues.append(('api', 'php', ru))
            continue
        rows.append(f"  {php_str(ru)} => {php_str(en)},\n")
    (ROOT / 'api' / '_en.php').write_text("<?php\n// Создаётся _tools/build_en.py, руками не править.\nreturn [\n" + ''.join(rows) + "];\n", encoding='utf-8')

    seen = list(dict.fromkeys(issues))
    print(f'en/: {len(HTML_FILES)} страниц, не переведено: {len(seen)}')
    for name, kind, text in seen:
        print(f'  [{name}] {kind}: {text[:130]}')


if __name__ == '__main__':
    main()
