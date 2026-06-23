#!/usr/bin/env python3
"""
Scan docs for remote image references and generate an inventory for R2 mirroring.
Excludes badges and dynamic images (shields.io, star-history, etc.).
"""

import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

# Optional: requests may not be installed; fall back to urllib
REQUESTS_OK = True
try:
    import requests
except ImportError:  # pragma: no cover
    REQUESTS_OK = False
    import urllib.request

DOCS_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent

# Domains to skip (badges, dynamic charts, tracking pixels)
SKIP_DOMAINS = {
    "img.shields.io",
    "api.star-history.com",
    "badgen.net",
    "forthebadge.com",
    "codecov.io",
    "coveralls.io",
    "travis-ci.com",
    "travis-ci.org",
    "img.icons8.com",
}

# Regex for Markdown image syntax
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\((https?://[^\s\)]+)\)")


def normalize_url(url: str) -> str:
    # Remove anchor/query noise when deciding uniqueness
    return url.split("#")[0].split("?")[0]


def is_skipped(url: str) -> bool:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    # Exact match or parent domain match
    if domain in SKIP_DOMAINS:
        return True
    for skip in SKIP_DOMAINS:
        if domain.endswith(f".{skip}"):
            return True
    return False


def collect_image_refs(root: Path):
    refs = []
    seen = set()

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Skip binary/static files already local
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".mp4", ".pdf"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for alt, url in MD_IMAGE_RE.findall(text):
            if is_skipped(url):
                continue
            key = normalize_url(url)
            if key in seen:
                continue
            seen.add(key)
            refs.append(
                {
                    "url": url,
                    "alt": alt.strip(),
                    "source_file": str(path.relative_to(root)).replace("\\", "/"),
                }
            )

    return refs


def fetch_size(url: str, timeout: int = 15) -> dict:
    result = {
        "url": url,
        "content_length": None,
        "content_type": None,
        "status_code": None,
        "error": None,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
    }

    try:
        if REQUESTS_OK:
            resp = requests.head(url, headers=headers, timeout=timeout, allow_redirects=True)
            result["status_code"] = resp.status_code
            result["content_length"] = resp.headers.get("Content-Length")
            result["content_type"] = resp.headers.get("Content-Type")
            # Some hosts reject HEAD; try GET with stream as fallback
            if resp.status_code >= 400 or result["content_length"] is None:
                resp = requests.get(url, headers=headers, timeout=timeout, stream=True)
                result["status_code"] = resp.status_code
                result["content_type"] = resp.headers.get("Content-Type")
                # Read only first chunk to avoid downloading whole file
                cl = resp.headers.get("Content-Length")
                if cl:
                    result["content_length"] = cl
                else:
                    chunk = next(resp.iter_content(chunk_size=8192), b"")
                    result["content_length"] = len(chunk)
        else:
            req = urllib.request.Request(url, method="HEAD", headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                result["status_code"] = resp.status
                result["content_length"] = resp.headers.get("Content-Length")
                result["content_type"] = resp.headers.get("Content-Type")
    except Exception as e:
        result["error"] = str(e)

    return result


def human_readable_size(size_bytes):
    if size_bytes is None:
        return "unknown"
    try:
        size_bytes = int(size_bytes)
    except (ValueError, TypeError):
        return "unknown"
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def main():
    print(f"Scanning {DOCS_ROOT} for remote image references...")
    refs = collect_image_refs(DOCS_ROOT)
    print(f"Found {len(refs)} unique remote image references (excluding badges).")

    if not refs:
        print("No images to inventory.")
        return

    print("Probing image sizes...")
    sizes = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(fetch_size, ref["url"]): ref for ref in refs}
        for i, future in enumerate(as_completed(futures), 1):
            ref = futures[future]
            info = future.result()
            sizes[ref["url"]] = info
            print(f"  [{i}/{len(refs)}] {ref['url'][:80]}... size={human_readable_size(info.get('content_length'))}")

    # Merge size info into refs
    for ref in refs:
        info = sizes.get(ref["url"], {})
        ref["content_length"] = info.get("content_length")
        ref["content_type"] = info.get("content_type")
        ref["status_code"] = info.get("status_code")
        ref["error"] = info.get("error")
        ref["size_human"] = human_readable_size(info.get("content_length"))

    # Sort by size descending (unknown last)
    def sort_key(r):
        try:
            return -(int(r["content_length"]) if r["content_length"] else -1)
        except Exception:
            return -1

    refs.sort(key=sort_key)

    # Write JSON inventory
    json_path = OUTPUT_DIR / "remote-image-inventory.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "total": len(refs),
                "generated_by": "scan_remote_images.py",
                "images": refs,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    # Write CSV inventory
    csv_path = OUTPUT_DIR / "remote-image-inventory.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["url", "size_human", "content_length", "content_type", "status_code", "source_file", "alt", "error"],
        )
        writer.writeheader()
        for ref in refs:
            writer.writerow(ref)

    print(f"\nInventory written to:")
    print(f"  JSON: {json_path}")
    print(f"  CSV:  {csv_path}")

    # Summary by domain
    from collections import Counter, defaultdict
    domain_sizes = defaultdict(int)
    domain_counts = Counter()
    for ref in refs:
        domain = urlparse(ref["url"]).netloc
        domain_counts[domain] += 1
        try:
            domain_sizes[domain] += int(ref["content_length"]) if ref["content_length"] else 0
        except Exception:
            pass

    print("\nSummary by domain:")
    for domain, count in domain_counts.most_common():
        print(f"  {domain}: {count} files, total ~{human_readable_size(domain_sizes[domain])}")


if __name__ == "__main__":
    main()
