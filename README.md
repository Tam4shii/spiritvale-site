# spiritvale-site

Community hub for **SpiritVale** (Steam app 3918510) — hosts patch notes JSON for Claude artifacts and other clients.

Live: https://spiritvale.tama.sh

## Endpoints

| Path | Description | CORS |
|---|---|---|
| `/` | Landing page | — |
| `/patch.json` | Patch notes manifest (consumed by Claude artifact) | `*` |

## Deploy

Auto-deployed via Cloudflare Pages on push to `main`.

## Add a new patch

Edit `patch.json` → commit → push. Live in ~1 min (CF Pages build).

## Validate patch files

```
pip install jsonschema   # once
python3 scripts/validate-patches.py
```

Runs `jsonschema.validate` against `schema/patch.json` for every `patches/v*.json` and `patches/latest.json`. Exit code 0 = all pass.
