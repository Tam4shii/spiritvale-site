#!/usr/bin/env python3
"""
Generate Schema.org JSON-LD structured data and inject into HTML pages.

Pages updated:
  index.html        → SoftwareApplication (game metadata + latest version)
  patch/index.html  → ItemList of TechArticle (one per patch version)

Pattern from SteamDB + wago.tools: JSON-LD on patch pages drives Google rich results
for "<game> <version> patch notes" queries — highest-leverage static SEO change available.

Injection is idempotent: uses <!-- LD+JSON START --> / <!-- LD+JSON END --> markers.
Re-running replaces the existing block without duplicating it.
"""
import json
import re
import sys
from pathlib import Path

BASE_URL = "https://spiritvale.tama.sh"
INDEX_PATH = Path("patches/index.json")
PAGES = {
    "index": Path("index.html"),
    "patch": Path("patch/index.html"),
}

MARKER_START = "<!-- LD+JSON START -->"
MARKER_END = "<!-- LD+JSON END -->"


def load_index() -> dict:
    if not INDEX_PATH.exists():
        print(f"ERROR: {INDEX_PATH} not found — run from repo root", file=sys.stderr)
        sys.exit(1)
    return json.loads(INDEX_PATH.read_text())


def build_home_jsonld(index: dict) -> dict:
    latest = index.get("latest_version", "unknown")
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "SpiritVale Community Hub",
        "url": f"{BASE_URL}/",
        "description": (
            "Unofficial community hub for SpiritVale (Steam app 3918510) — "
            "patch notes archive, search, feeds, and SDK."
        ),
        "about": {
            "@type": "SoftwareApplication",
            "name": "SpiritVale",
            "applicationCategory": "GameApplication",
            "operatingSystem": "Windows",
            "softwareVersion": latest,
            "offers": {
                "@type": "Offer",
                "price": "14.99",
                "priceCurrency": "USD",
                "availability": "https://schema.org/PreOrder",
            },
        },
    }


def build_patch_jsonld(index: dict) -> dict:
    versions = index.get("versions", [])
    items = []
    for pos, v in enumerate(versions, start=1):
        ver = v.get("version", "")
        title = v.get("title", "")
        date = v.get("date", "")
        items.append(
            {
                "@type": "ListItem",
                "position": pos,
                "item": {
                    "@type": "TechArticle",
                    "headline": f"SpiritVale v{ver} — {title}",
                    "url": f"{BASE_URL}/patch/#v{ver}",
                    "datePublished": date,
                    "softwareVersion": ver,
                    "author": {"@type": "Organization", "name": "SpiritVale Dev Team"},
                },
            }
        )
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "SpiritVale Patch Notes",
        "description": "Complete patch notes archive for SpiritVale — all versions.",
        "url": f"{BASE_URL}/patch/",
        "numberOfItems": len(versions),
        "itemListElement": items,
    }


def make_script_block(jsonld: dict) -> str:
    return (
        f"{MARKER_START}\n"
        f'<script type="application/ld+json">\n'
        f"{json.dumps(jsonld, indent=2, ensure_ascii=False)}\n"
        f"</script>\n"
        f"{MARKER_END}"
    )


def inject(html: str, jsonld: dict) -> str:
    block = make_script_block(jsonld)
    if MARKER_START in html:
        html = re.sub(
            re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END),
            block,
            html,
            flags=re.DOTALL,
        )
    else:
        html = html.replace("</head>", f"{block}\n</head>", 1)
    return html


def process_page(path: Path, jsonld: dict) -> None:
    if not path.exists():
        print(f"WARN: {path} not found — skipping", file=sys.stderr)
        return
    original = path.read_text(encoding="utf-8")
    updated = inject(original, jsonld)
    if updated == original:
        print(f"  {path}: no change (JSON-LD already up to date)")
    else:
        path.write_text(updated, encoding="utf-8")
        print(f"  {path}: JSON-LD injected/updated")


def main() -> None:
    index = load_index()
    print(f"Loaded {len(index.get('versions', []))} versions from {INDEX_PATH}")

    process_page(PAGES["index"], build_home_jsonld(index))
    process_page(PAGES["patch"], build_patch_jsonld(index))

    print("JSON-LD build complete.")


if __name__ == "__main__":
    main()
