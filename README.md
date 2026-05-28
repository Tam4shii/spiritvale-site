# spiritvale-site

Community hub for **SpiritVale** (Steam app 3918510) — hosts patch notes JSON for Claude artifacts and other clients.

Live: https://spiritvale.tama.sh

## Endpoints

| Path | Description | CORS |
|---|---|---|
| `/` | Landing page | — |
| `/patch.json` | Patch notes manifest (consumed by Claude artifact) | `*` |
| `/patches/index.json` | All versions index with metadata | `*` |
| `/patches/latest.json` | Current version full patch data | `*` |
| `/patches/v{x.y.z}.json` | Individual version data (9 versions archived) | `*` |
| `/patch/` | HTML patch viewer — browse full archive | — |
| `/diff/` | Cumulative diff viewer between any two versions | — |
| `/feed.xml` | Atom feed of patch releases | — |
| `/schema/patch.json` | JSON Schema for `patches/v*.json` | `*` |
| `/llms.txt` | LLM-readable API guide | — |
| `/sitemap.xml` | Sitemap | — |

## Deploy

Auto-deployed via Cloudflare Pages on push to `main`.

## Add a new patch

1. Create `patches/v{x.y.z}.json` from the schema template
2. Update `patches/index.json` (add entry, bump `latest_version`)
3. Update `patches/latest.json` and `patch.json`
4. Update `feed.xml`, `sitemap.xml`, `CHANGELOG.md`
5. Commit + push → CF Pages auto-deploys in ~1 min

## Validate patch files

```
pip install jsonschema   # once
python3 scripts/validate-patches.py
```

Runs `jsonschema.validate` against `schema/patch.json` for every `patches/v*.json` and `patches/latest.json`. Exit code 0 = all pass.
