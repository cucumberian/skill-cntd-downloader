---
name: cntd-downloader
description: "Скачивание документов с docs.cntd.ru как оффлайн HTML. Динамически загружает все блоки документа, встраивает изображения. Триггеры: cntd, cntd-downloader, скачать документ, cntd.ru, нормативный документ, ГОСТ, СП, СНиП, скачать ГОСТ, скачать СП."
---

# cntd-downloader — Скачать документ с docs.cntd.ru

Документы на docs.cntd.ru грузятся динамически по блокам при пролистывании.
Скрипт итеративно скачивает все блоки через API и собирает в один оффлайн HTML.
Заголовок документа извлекается из API `/api/document/{id}`.

## Важно: временные ограничения API

Полная версия документа доступна только **с 20:00 до 24:00** по Москве.
В остальное время доступны только первые блоки. Если нужно скачать полностью —
запускайте в это окно.

## Использование

```bash
# Базовое — скачать HTML со стилями
python3 /home/human/.agents/skills/cntd-downloader/cntd.py <URL>

# Со встроенными изображениями (для полного оффлайна)
python3 /home/human/.agents/skills/cntd-downloader/cntd.py <URL> --embed-images

# С Google Fonts (PT Serif + PT Sans)
python3 /home/human/.agents/skills/cntd-downloader/cntd.py <URL> --fonts

# Без стилей (голый HTML)
python3 /home/human/.agents/skills/cntd-downloader/cntd.py <URL> --no-styles

# Указать имя файла
python3 /home/human/.agents/skills/cntd-downloader/cntd.py <URL> --out document.html

# Задержка между запросами (секунды, по умолчанию 0.3)
python3 /home/human/.agents/skills/cntd-downloader/cntd.py <URL> --delay 1

# Передать API-ключ вручную
python3 /home/human/.agents/skills/cntd-downloader/cntd.py <URL> --key YOUR_KEY
```

## Примеры

```bash
# СП 32.13330.2018
python3 /home/human/.agents/skills/cntd-downloader/cntd.py \
  https://docs.cntd.ru/document/554820821 \
  --embed-images --out SP_32.13330.2018.html

# Любой другой документ
python3 /home/human/.agents/skills/cntd-downloader/cntd.py \
  https://docs.cntd.ru/document/1200003608
```

## Формат URL

Любой URL вида `https://docs.cntd.ru/document/{ID}` или
`https://docs.cntd.ru/document/{ID}/...` — скрипт извлечёт ID автоматически.

## Флаги

| Флаг | Описание |
|------|----------|
| `--embed-images` | Встроить изображения как base64 (полный оффлайн) |
| `--out FILE` | Имя выходного файла |
| `--delay SECS` | Задержка между запросами (по умолчанию 0.3) |
| `--no-styles` | Отключить CSS-стили |
| `--fonts` | Добавить Google Fonts (PT Serif + PT Sans) |
| `--key KEY` | API-ключ (переопределить захардкоженный) |

## API-ключ

### Как работает

Ключ — статический UUID, вшит в SSR-конфиг Nuxt.js при деплое.
Одинаковый для всех посетителей, не зависит от сессии/клиента/времени.
Захардкожен в `cntd.py` как `APP_KEY`.

### Как извлечь вручную (если деплоили новый релиз)

Страница документа редиректит на SSO-авторизацию при доступе через `curl`/`urlopen`.
Нужен реальный браузер:

1. Открыть https://docs.cntd.ru/document/554820821 в браузере
2. DevTools → Console:
   ```js
   // Конфиг доступен в window.__NUXT__.config или в HTML-источнике
   document.body.innerHTML.match(/DOCS_API_KEY:"([^"]+)"/)[1]
   ```
3. Или в Sources найдите `config:` блок — там `DOCS_API_KEY`, `CAS_SSO`, `HOTDOCS_API_KEY`, `FORM_KEY`

### Что за ключи в конфиге

| Поле | Назначение |
|------|-----------|
| `DOCS_API_KEY` | API docs.cntd.ru — **этот нужен скрипту** (`x-application-key`) |
| `CAS_SSO` | SSO-авторизация (auth.kodeks.ru) |
| `HOTDOCS_API_KEY` | API hotdocs (другой сервис) |
| `FORM_KEY` | Формы на сайте |

### Быстрая проверка (curl не работает — редиректит)

```bash
# Не сработает — страница редиректит на SSO:
curl -s "https://docs.cntd.ru/document/554820821" | grep DOCS_API_KEY

# Работает — ключ в JS-бандле (старый способ, надёжнее):
curl -s "https://docs.cntd.ru/resources/$(curl -s https://docs.cntd.ru/document/554820821 | grep -oP '/resources/\w+\.js' | head -1 | sed 's|/resources/||')" | grep -oP '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}' | head -5
```

## CSS-стили

Скрипт автоматически скачивает CSS с cntd.ru (11 файлов) и фильтрует правила,
релевантные контенту документа. Если дизайн сайта изменится — CSS подхватится
автоматически. Если нужно принудительно обновить — добавить/убрать URL в список
`CSS_URLS` в начале `cntd.py`.

## Структура скилла

```
/home/human/.agents/skills/cntd-downloader/
├── SKILL.md   # Этот файл
└── cntd.py    # Скрипт скачивания
```
