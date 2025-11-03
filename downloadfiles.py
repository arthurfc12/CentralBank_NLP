import os
import csv
import time
import requests
from datetime import date, timedelta

BASE = "https://www.bcb.gov.br/content/copom/atascopom/"
SAVE_FOLDER = "copom_pdfs"
START_MEETING = 200
END_MEETING = 273
INITIAL_DATE = date(2016, 7, 20)  # known date for #200

# tuning knobs
TYPICAL_GAP_DAYS = 45
NEARBY_WINDOW_DAYS = 30     # ring search around expected date
FAR_LOOKAHEAD_DAYS = 120    # extra lookahead after nearby ring
HEAD_TIMEOUT = 8
GET_TIMEOUT = 30

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

def ensure_folder(path: str):
    os.makedirs(path, exist_ok=True)

def yyyymmdd(d: date) -> str:
    return d.strftime("%Y%m%d")

def yyyy_mm_dd(d: date) -> str:
    return d.strftime("%Y-%m-%d")

def candidate_filenames(n: int, d: date):
    d_compact = yyyymmdd(d)          # 20160831
    d_dashed  = yyyy_mm_dd(d)        # 2016-08-31
    # Only the realistic variants (case + dashed vs compact)
    yield f"Copom{n}-not{d_compact}{n}.pdf"
    yield f"COPOM{n}-not{d_compact}{n}.pdf"
    yield f"Copom{n}-not{d_dashed}-{n}.pdf"
    yield f"COPOM{n}-not{d_dashed}-{n}.pdf"

def url_is_pdf(url: str) -> bool:
    try:
        r = requests.head(url, headers=HEADERS, timeout=HEAD_TIMEOUT, allow_redirects=True)
        if r.status_code == 200 and "pdf" in r.headers.get("content-type", "").lower():
            return True
        # Some servers don’t send content-type on HEAD—fallback to a quick GET
        r = requests.get(url, headers=HEADERS, timeout=HEAD_TIMEOUT, stream=True)
        return r.status_code == 200 and "pdf" in r.headers.get("content-type", "").lower()
    except requests.RequestException:
        return False

def download_pdf(url: str, out_path: str) -> bool:
    try:
        with requests.get(url, headers=HEADERS, timeout=GET_TIMEOUT, stream=True) as r:
            if r.status_code != 200 or "pdf" not in r.headers.get("content-type", "").lower():
                return False
            with open(out_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 64):
                    if chunk:
                        f.write(chunk)
        return True
    except requests.RequestException:
        return False

def ring_offsets(nearby: int, far: int):
    # 0, +1, -1, +2, -2, ... up to nearby
    yield 0
    for k in range(1, nearby + 1):
        yield k
        yield -k
    # then a lighter forward sweep to far (every 2 days)
    for k in range(nearby + 1, far + 1, 2):
        yield k

def main():
    ensure_folder(SAVE_FOLDER)
    index_rows = []
    downloaded = 0
    skipped = 0
    not_found = 0

    # meeting #200 is known; use it to seed the next lower bound
    last_date = INITIAL_DATE

    for n in range(START_MEETING, END_MEETING + 1):
        # skip if already present
        if any(fn.lower().startswith(f"copom{n}-not") and fn.lower().endswith(".pdf")
               for fn in os.listdir(SAVE_FOLDER)):
            skipped += 1
            index_rows.append([n, "", "", "skipped (exists)"])
            # still advance lower bound a bit to preserve monotonicity
            last_date = last_date + timedelta(days=1)
            continue

        # expected next meeting date
        expected = last_date + timedelta(days=TYPICAL_GAP_DAYS)
        print(f"\n🔎 Meeting #{n}: searching near {expected.isoformat()}")

        found_url = None
        found_date = None
        found_name = None

        # try ring around expected, then forward sweep
        tries = 0
        for off in ring_offsets(NEARBY_WINDOW_DAYS, FAR_LOOKAHEAD_DAYS):
            d = expected + timedelta(days=off)
            # meeting dates must strictly increase
            if d <= last_date:
                continue

            for fname in candidate_filenames(n, d):
                url = BASE + fname
                tries += 1
                if url_is_pdf(url):
                    found_url = url
                    found_date = d
                    found_name = fname
                    break
            if found_url:
                break

            if tries % 50 == 0:
                print(f"  ... {tries} attempts so far (last tried {d.isoformat()})")

        if not found_url:
            print(f"❌ Meeting #{n}: no PDF found within +{FAR_LOOKAHEAD_DAYS}d of expected.")
            not_found += 1
            # advance lower bound conservatively
            last_date = last_date + timedelta(days=10)
            index_rows.append([n, "", "", "not found"])
            continue

        out_path = os.path.join(SAVE_FOLDER, found_name)
        if os.path.exists(out_path):
            print(f"⏭️ Skipped (exists): {out_path}")
            skipped += 1
            index_rows.append([n, found_date.isoformat(), found_url, "skipped"])
        else:
            print(f"⬇️ Downloading: {found_name}")
            if download_pdf(found_url, out_path):
                print(f"✅ Saved: {out_path}")
                downloaded += 1
                index_rows.append([n, found_date.isoformat(), found_url, "downloaded"])
            else:
                print("❌ Found URL but failed to download (network/content).")
                not_found += 1
                index_rows.append([n, found_date.isoformat(), found_url, "failed"])

        # next meeting must be after this one
        last_date = found_date + timedelta(days=1)
        time.sleep(0.15)  # be polite

    # write index
    index_csv = os.path.join(SAVE_FOLDER, "index.csv")
    with open(index_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["meeting_number", "date_found(ISO)", "url", "status"])
        w.writerows(index_rows)

    print("\nSummary:")
    print(f"  ✅ Downloaded PDFs: {downloaded}")
    print(f"  ⏭️ Skipped (already existed): {skipped}")
    print(f"  ❌ Not found: {not_found}")
    print(f"\n📁 Files saved to: {os.path.abspath(SAVE_FOLDER)}")
    print(f"🗂️ Index: {index_csv}")

if __name__ == "__main__":
    main()
