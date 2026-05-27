# PROJECT: spiritvale-site

**Status**: 🟢 Active · **Started**: 2026-05-25 · **Owner**: เจ้านาย (Tam4shii)

## WHY
เจ้านายเล่นเกม **SpiritVale** (Steam app 3918510) — อยาก host patch note ของเกมไว้ที่โดเมนตัวเอง (`spiritvale.tama.sh`) เพื่อใช้ผูกกับ Claude artifact (และอาจขยายเป็น community hub ในอนาคต)

## SUCCESS
- ✅ Artifact ของ Claude fetch `https://spiritvale.tama.sh/patch.json` ได้โดยไม่ติด CORS
- ✅ Update patch ใหม่ = แค่ commit + push → live ภายใน ~1 min
- ✅ Landing page เปิด browser แล้วเห็นได้ (เผื่อคนพิมพ์ตรง)

## STACK
- **Hosting**: Cloudflare Pages (free tier)
- **DNS**: Cloudflare (zone `tama.sh`)
- **Repo**: GitHub `Tam4shii/spiritvale-site` (public, no secrets)
- **Files**: static HTML + JSON + `_headers` (CORS)

## REPO
- URL: https://github.com/Tam4shii/spiritvale-site
- Branch: `main` (auto-deploy)

## INFRA
- CF Pages project: `spiritvale-site`
- Custom domain: `spiritvale.tama.sh` (CNAME → `spiritvale-site.pages.dev`)
- Zone ID: `25183c6035ca60f9e2e57ac277e65192` (tama.sh)

## DEPS
ไม่มี build step — pure static. ไม่มี dependency

## PHASE 0 (Now)
- [x] Local scaffold + `patch.json`
- [x] Push GitHub repo (patches/ structure + _redirects + immutable cache headers — 2026-05-25)
- [ ] Connect CF Pages (manual: dash.cloudflare.com → Pages → New → Connect GitHub → Tam4shii/spiritvale-site)
- [ ] Custom domain + DNS (manual: CF Pages → Custom domain → spiritvale.tama.sh)
- [ ] Fill in real artifact URL in `patches/v0.17.0.json` + `patches/latest.json` + `patch.json` (set `"url"` field — currently `null`, safe for clients to check `if patch.url`)
- [ ] Verify CORS from artifact

## PHASE 1 (Post-launch hardening)
- [x] **Content-Security-Policy** — already in `_headers` (default-src 'self'; script/style 'unsafe-inline'; img data: https:; connect 'self'; frame-ancestors 'self')
- [x] **/feed.xml (Atom)** — created 2026-05-26; serves from `/feed.xml`; `application/atom+xml` header in `_headers`; update summary when patch arrays are filled
- [x] **`patches/manifest.json` alias** — `/manifest.json` and `/patches/manifest.json` both 302 → `/patches/index.json` (added to `_redirects` 2026-05-26)
- [x] **favicon.svg** — purple spirit star icon; eliminates 404 on page load (2026-05-26)
- [x] **patch viewer bug fix** — `/patch/` now fetches each version's `archive_url` for full data; previously old patches always showed "coming soon…" (2026-05-26)

## FUTURE (ถ้าจะขยาย)
- [x] HTML patch viewer ที่ `/patch/` (built 2026-05-26 — full archive + per-section rendering; **live only after CF Pages is connected** — see Phase 0 above)
- [x] JSON Schema at `/schema/patch.json` (published 2026-05-26 — validates Added/Changed/Fixed/Removed contract; `$schema` wired into all `patches/*.json`)
- [x] **Full patch archive** (2026-05-27) — 7 historical patches promoted from draft to versioned files (v0.13.2 → v0.16.7); all bullets classified into added/changed/fixed/removed; `patches/index.json` updated with all 8 versions; **committed + pushed to GitHub** (commit 2913165)
- [x] **v0.17.0 patch content** (2026-05-27) — parsed Steam announcement (gid 1833334318576172) into 13 added / 21 changed / 3 fixed / 1 removed; updated `v0.17.0.json`, `latest.json`, `patch.json`, `index.json`, `CHANGELOG.md`; pushed (commit fb95744)
- Build guides / class info
- Boss tracker / event calendar
- API endpoints อื่นๆ (เช่น `/builds`, `/items`)

## BLOCKERS (Boss Actions Required)
| # | Action | Where | Notes |
|---|---|---|---|
| 1 | Connect CF Pages | [dash.cloudflare.com → Pages → New → Connect GitHub → Tam4shii/spiritvale-site](https://dash.cloudflare.com/) | No build command, output dir = `/` |
| 2 | Set custom domain | CF Pages → Custom domains → `spiritvale.tama.sh` | CNAME auto-created; ~5 min DNS propagation |
| 3 | ~~Fill v0.17.0 patch arrays~~ | ✅ Done 2026-05-27 — 13 added, 21 changed, 3 fixed, 1 removed (commit fb95744) | |
| 4 | Set artifact URL | `patches/v0.17.0.json` + `patches/latest.json` + `patch.json` — `"url"` field (currently `null`) | Paste Claude artifact link; page auto-links it |
| 5 | Verify CORS from artifact | `fetch("https://spiritvale.tama.sh/patches/latest.json")` in artifact console | Should 200 with `Access-Control-Allow-Origin: *` |

## RISKS
- 🟡 **CF Pages free tier**: 500 builds/month, 100k requests/day — เยอะมากสำหรับ static, ไม่น่าจะถึง
- 🟡 **DNS propagation**: ~5 นาที หลังเพิ่ม CNAME
- 🟢 **No secrets in repo** — public repo ปลอดภัย

## NOTES
- เกม SpiritVale = playtest (เจ้านายเล่นมาตั้งแต่ ~2026-05-14, 3046+ นาที playtime)
- Patch note ตัวแรกที่ host = v0.17.0 "The Echoing Spire" (2026-05-25)
