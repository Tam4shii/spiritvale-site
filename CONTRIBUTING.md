# Contributing to spiritvale-site

This repository is a community-maintained patch archive for [SpiritVale](https://store.steampowered.com/app/3918510).
All data is plain JSON — no build server, no backend, no accounts required.

---

## Ways to contribute

| Type | What to open |
|------|-------------|
| New patch data | PR with `patches/vX.Y.Z.json` |
| Correction to existing bullets | PR editing the relevant `patches/v*.json` |
| New script / tool | PR under `scripts/` |
| Bug in a page (patch viewer, diff, search) | GitHub Issue |

---

## Adding a new patch — step by step

1. **Copy the schema template**

   ```bash
   cp patches/v0.17.0.json patches/vX.Y.Z.json
   ```

2. **Fill every field** — validate against `/schema/patch.json`:

   ```jsonc
   {
     "$schema": "https://spiritvale.tama.sh/schema/patch.json",
     "version": "X.Y.Z",
     "title": "Patch Title",
     "date": "YYYY-MM-DD",
     "current": false,
     "url": null,
     "steam_url": "https://store.steampowered.com/news/...",
     "steam_news_id": "<gid from Steam API>",
     "added":   [{ "text": "...", "tags": [] }],
     "changed": [{ "text": "...", "tags": [] }],
     "fixed":   [{ "text": "...", "tags": [] }],
     "removed": [{ "text": "...", "tags": [] }]
   }
   ```

   Valid tags come from `tag/index.json` (e.g. `balance`, `equipment`, `skills`, `bug-fix`).

3. **Update index and derived files**

   ```bash
   # Add an entry to patches/index.json (prepend — latest first)
   # Then regenerate search index, feeds, sitemap, tag pages, OG images:
   make build og
   ```

4. **Run the validation gate** — PR will be blocked if this fails:

   ```bash
   make check
   ```

   All 6 artifacts (sitemap.xml, tag/index.json, patches/index.json, search-index.json, feed.json, feed.xml) must exit 0.

5. **Open a PR** with title `patch: add vX.Y.Z <title>`.

---

## Schema contract

`patches/*.json` files are validated by `scripts/validate-patches.py` and the JSON Schema at `/schema/patch.json`.

Key invariants:
- `version` must be semver string matching the filename stem.
- `date` must be ISO 8601 (`YYYY-MM-DD`).
- Each bullet must have a non-empty `text` field.
- `tags` must be a subset of the tags listed in `tag/index.json`.
- Only one patch file may have `"current": true` at a time.

---

## PR checklist

```
[ ] patches/vX.Y.Z.json added and valid
[ ] patches/index.json updated (new entry prepended, previous latest set current=false)
[ ] make build run — search-index.json, tag pages, feeds regenerated
[ ] make check exits 0
[ ] CHANGELOG.md entry added
```

---

## Running locally

No server needed — open `index.html` in a browser, or use:

```bash
python3 -m http.server 8080
```

Install git hooks so `make check` runs before every commit:

```bash
make install-hooks
```
