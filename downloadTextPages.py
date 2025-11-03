# downloadTextPages.py
# pip install playwright
# python -m playwright install

import re
import sys
import csv
import html
import asyncio
import unicodedata
from pathlib import Path
from contextlib import suppress
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

OUT_DIR = Path("copom_texts")
MAX_RETRIES = 3
HEADLESS = True

def clean_text(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = s.replace("\r", "")
    s = re.sub(r"[ \t\f\v]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()

def slug_ddmmyyyy(url: str) -> str | None:
    m = re.search(r"/(\d{8})(?:/)?$", url)
    return m.group(1) if m else None

async def dismiss_cookie_banner(page):
    selectors = [
        "#onetrust-accept-btn-handler",
        "button#onetrust-accept-btn-handler",
        "button:has-text('Aceitar')",
        "button:has-text('Aceitar todos')",
        "button:has-text('OK')",
    ]
    for sel in selectors:
        with suppress(Exception):
            if await page.locator(sel).count():
                await page.locator(sel).click(timeout=1000)
                await page.wait_for_timeout(200)
                break

async def extract_main_text(page) -> str:
    with suppress(PWTimeout):
        await page.wait_for_load_state("networkidle", timeout=8000)
    await dismiss_cookie_banner(page)

    candidates = [
        "main",
        "article",
        "div#conteudo",
        "div.conteudo",
        "section",
        "div.container",
        "div[role='main']",
        "app-root",  # Angular root (as a fallback)
    ]
    for sel in candidates:
        loc = page.locator(sel)
        try:
            if await loc.count():
                t = await loc.inner_text()
                t = clean_text(html.unescape(t))
                if len(t) > 200:  # lower threshold since we’re saving everything
                    return t
        except Exception:
            pass

    t = await page.inner_text("body")
    return clean_text(html.unescape(t))

async def fetch_one(page, url: str):
    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
    await page.wait_for_timeout(1200)  # let app hydrate
    text = await extract_main_text(page)
    return text

async def scrape_from_txt(txt_path: Path):
    OUT_DIR.mkdir(exist_ok=True)
    urls = [
        line.strip()
        for line in txt_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    print(f"🔗 Loaded {len(urls)} URLs from {txt_path.name}")

    rows = []
    saved = failed = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=HEADLESS)
        ctx = await browser.new_context()
        page = await ctx.new_page()

        for i, url in enumerate(urls, 1):
            slug = slug_ddmmyyyy(url)
            if not slug:
                print(f"⚠️ [{i}/{len(urls)}] URL missing date slug, skipping: {url}")
                rows.append(["", url, "", "no_slug"])
                continue

            filename = OUT_DIR / f"{slug}.txt"
            if filename.exists():
                print(f"⏭️ [{i}/{len(urls)}] Exists → {filename.name}")
                rows.append([slug, url, filename.name, "skipped_exists"])
                continue

            ok = False
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    text = await fetch_one(page, url)
                    # Save whatever we got (some older pages may be short)
                    filename.write_text(text + "\n", encoding="utf-8")
                    print(f"✅ [{i}/{len(urls)}] Saved → {filename.name}")
                    rows.append([slug, url, filename.name, "saved"])
                    saved += 1
                    ok = True
                    break
                except Exception as e:
                    if attempt == MAX_RETRIES:
                        print(f"💥 [{i}/{len(urls)}] Failed: {url} ({type(e).__name__})")
                        rows.append([slug, url, "", f"failed:{type(e).__name__}"])
                        failed += 1
                await page.wait_for_timeout(400)

        await browser.close()

    with open(OUT_DIR / "index.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["date_slug_ddmmyyyy", "url", "saved_filename", "status"])
        w.writerows(rows)

    print("\nSummary:")
    print(f"  ✅ Saved: {saved}")
    print(f"  💥 Failed: {failed}")
    print(f"\n📁 Folder: {OUT_DIR.resolve()}")
    print(f"🗂️ Index:  {(OUT_DIR / 'index.csv').resolve()}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python downloadTextPages.py links.txt")
        sys.exit(1)
    txt_path = Path(sys.argv[1])
    if not txt_path.exists():
        print(f"File not found: {txt_path}")
        sys.exit(1)
    asyncio.run(scrape_from_txt(txt_path))
