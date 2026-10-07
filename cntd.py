#!/usr/bin/env python3
"""
cntd-downloader: скачать документ с docs.cntd.ru как оффлайн HTML.

  python3 cntd.py <URL> [--out FILE] [--embed-images] [--delay SECS]
                         [--no-styles] [--fonts] [--key KEY]

Полная версия доступна only 20:00-22:00 МСК.
"""

import sys, re, time, base64, json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

API = "https://docs.cntd.ru/api/document"

# DOCS_API_KEY — статический, вшит в SSR-конфиг Nuxt.js при деплое.
# Извлечение: см. SKILL.md "API-ключ".
APP_KEY = "39dfb4bf-79ba-4916-aff1-849edc97a706"


def _get(url: str) -> bytes:
    req = Request(url, headers={"x-application-key": APP_KEY, "User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=30) as r:
        return r.read()


def doc_id_from_url(url: str) -> str:
    m = re.search(r'/document/(\d+)', url)
    if not m:
        sys.exit(f"❌ Не извлечь ID из: {url}")
    return m.group(1)


def fetch_title(doc_id: str) -> str:
    try:
        data = _get(f"{API}/{doc_id}")
        j = json.loads(data)
        name = j.get("data", {}).get("clean_name", "")
        if name:
            return name
    except Exception:
        pass
    return f"Document {doc_id}"


def fetch_block(doc_id: str, n: int) -> str | None:
    try:
        raw = _get(f"{API}/{doc_id}/content/text/block/{n}?strict=true")
        s = raw.decode("utf-8", errors="replace").strip()
        if not s or (s.startswith("{") and '"errors"' in s):
            return None
        return s
    except HTTPError:
        return None
    except (URLError, TimeoutError):
        return None


def fetch_all_blocks(doc_id: str, delay: float) -> list[str]:
    blocks, empties = [], 0
    while True:
        n = len(blocks) + 1
        sys.stdout.write(f"\r  Блок {n}...")
        sys.stdout.flush()
        html = fetch_block(doc_id, n)
        if html is None:
            empties += 1
            if empties >= 2:
                sys.stdout.write(f"\r  Всего блоков: {len(blocks)}     \n")
                break
            time.sleep(delay)
            continue
        empties = 0
        blocks.append(html)
        sys.stdout.write(f"\r  Блок {n}: {len(html):,} символов  \n")
        time.sleep(delay)
    return blocks


def embed_images(html: str, delay: float) -> str:
    urls = list(dict.fromkeys(re.findall(r'src="(https?://[^"]+)"', html)))
    if not urls:
        return html
    print(f"  Изображений: {len(urls)}")
    for i, url in enumerate(urls):
        sys.stdout.write(f"\r    [{i+1}/{len(urls)}] ...{url[-40:]}")
        sys.stdout.flush()
        try:
            data = _get(url)
            ext = url.rsplit(".", 1)[-1].lower()
            mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                    "gif": "image/gif", "svg": "image/svg+xml"}.get(ext, "image/png")
            html = html.replace(url, f"data:{mime};base64,{base64.b64encode(data).decode()}")
        except Exception:
            pass
        time.sleep(delay)
    print(f"\r    Готово: {len(urls)} изображений                ")
    return html


def build_html(title: str, body: str, styles: bool = True, fonts: bool = False) -> str:
    css = ""
    if styles:
        css = """
body{font-family:Arial,sans-serif;max-width:960px;margin:0 auto;padding:50px 0;line-height:1.4em;color:#444;font-size:15px}
.document-text{word-wrap:break-word;font-size:16px;line-height:22px}
.document-text_block>div,.document-text_block>h1,.document-text_block>h2,.document-text_block>h3,.document-text_block>h4,.document-text_block>h5,.document-text_block>h6,.document-text_block>img,.document-text_block>p,.document-text_block>ul{padding:0 57px 0 89px}
.document-text_block>table{margin:0 57px 0 89px;border-collapse:collapse}
.document-text_block h1,.document-text_block h2,.document-text_block h3,.document-text_block h4,.document-text_block h5,.document-text_block h6,.document-text_block p{margin:0 0 1em}
.document-text_block p.formattext{margin:0}
.headertext{font-weight:700}.centertext{text-align:center}
.indenttext{text-indent:2em}.formattext{margin:0}
.topleveltext{margin:0}a{color:#3451a0;text-decoration:underline}
.base64.sign{display:none}img{max-width:100%;height:auto}
table{border-collapse:collapse;border-spacing:0}
td,td img{vertical-align:top}
@media print{body{padding:0;max-width:none}a{color:#000;text-decoration:none}}"""
    if fonts:
        css += """
@import url('https://fonts.googleapis.com/css2?family=PT+Serif:wght@400;700&family=PT+Sans:wght@400;700&display=swap');
body{font-family:'PT Serif',Arial,sans-serif}
.headertext,.centertext{font-family:'PT Sans',Arial,sans-serif}"""
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>{css}</style>
</head>
<body>
<!-- offline copy -->
{body}
</body>
</html>"""


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        sys.exit(0)

    global APP_KEY
    url, out, embed, delay, styles, fonts, key = args[0], None, False, 0.3, True, False, ""
    i = 1
    while i < len(args):
        if args[i] == "--out" and i+1 < len(args): out = args[i+1]; i += 2
        elif args[i] == "--embed-images": embed = True; i += 1
        elif args[i] == "--delay" and i+1 < len(args): delay = float(args[i+1]); i += 2
        elif args[i] == "--no-styles": styles = False; i += 1
        elif args[i] == "--fonts": fonts = True; i += 1
        elif args[i] == "--key" and i+1 < len(args): key = args[i+1]; i += 2
        else: i += 1

    if key:
        APP_KEY = key

    did = doc_id_from_url(url)
    print(f"📄 {did}")

    title = fetch_title(did)
    print(f"📝 {title}")

    blocks = fetch_all_blocks(did, delay)
    if not blocks:
        sys.exit("❌ Нет блоков. Полная версия: 20:00-22:00 МСК.")

    combined = "\n".join(blocks)
    if embed:
        print("🖼️  Встраивание изображений...")
        combined = embed_images(combined, delay)

    if not out:
        out = f"document_{did}.html"

    Path(out).write_text(build_html(title, combined, styles, fonts), encoding="utf-8")
    print(f"✅ {out} ({Path(out).stat().st_size/1024:.0f} КБ)")


if __name__ == "__main__":
    main()
