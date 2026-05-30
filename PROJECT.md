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
- [x] **v0.13.4 gap filled** (2026-05-27) — patch present in upstream/steam.json but missing from archive; added `patches/v0.13.4.json` (Paladin Revamp: 1 added, 6 changed, 1 fixed); updated index/feed/sitemap/llms.txt/CHANGELOG; pushed (commit 0e1db96); archive now complete: 9 versions (v0.13.2 → v0.17.0)
- [x] **v0.17.0 patch content** (2026-05-27) — parsed Steam announcement (gid 1833334318576172) into 13 added / 21 changed / 3 fixed / 1 removed; updated `v0.17.0.json`, `latest.json`, `patch.json`, `index.json`, `CHANGELOG.md`; pushed (commit fb95744)
- [x] **sitemap.xml accuracy** (2026-05-28) — fixed stale v0.17.0 entry (pending→never/0.7) + updated lastmod for index.json and latest.json from 2026-05-25→2026-05-27; pushed (commit c48ee78)
- [x] **index.json steam_news_id** (2026-05-28) — added `steam_news_id` to all 9 version entries in `patches/index.json`; GH Actions deduplication now uses both GID + version-string matching; pushed (commit abe0c01). **Key alignment verified**: `pull-steam-news.py:54` reads `v["steam_news_id"]` — exact match to field name; deduplication is wired correctly.
- [x] **diff viewer at `/diff/`** (2026-05-28) — client-side cumulative diff between any two versions; fetches `patches/index.json` + individual patch files, aggregates added/changed/fixed/removed across all versions in range, renders with per-entry version badge; includes JSON export + clipboard copy + shareable URL (`?from=X&to=Y`); also handles `/diff/vX...vY` pathname notation for LLM-friendly linking; matches existing design system
- [x] **sitemap.xml lastmod audit** (2026-05-28) — all 9 patch entries verified accurate (match `index.json` release dates); added missing `/diff/` entry (lastmod 2026-05-28, priority 0.8) and `/schema/patch.json` entry (lastmod 2026-05-26, priority 0.4); committed + pushed
- [x] **homepage + llms.txt discoverability fix** (2026-05-28) — `/diff/` card added to landing page nav links (was missing after diff viewer shipped); `llms.txt` updated with `?from=X&to=Y` URL param docs for LLM consumers; pushed (commit c06080a)
- [x] **patch viewer: "View on Steam →" link** (2026-05-28) — each patch card in `/patch/` now shows a direct link to the original Steam announcement (`steam_url` field was already in all 9 `patches/v*.json` files but was never surfaced in the UI); 1-line change to `renderPatch()` footer
- [x] **scripts/validate-patches.py committed + README expanded** (2026-05-28) — `scripts/validate-patches.py` was referenced in README but never tracked by git; committed + pushed (commit 4fdd062). README endpoint table expanded from 2→11 rows covering all live routes; "Add a new patch" section rewritten as 5-step checklist matching current process.
- [x] **feed.json discoverability** (2026-05-28) — `feed.json` (JSON Feed 1.1) existed with proper Content-Type headers but was missing from sitemap, llms.txt, and HTML `<link rel="alternate">` tags; `/diff/` was the only page with no feed discovery tags at all. Added to all 5 locations (commit bac3627).
- [x] **full-text search at `/search/`** (2026-05-29) — client-side search page across all 128 patch entries; `scripts/build-search-index.py` generates `search-index.json` (flattened bullets: id/version/type/text/url); sitemap + llms.txt + homepage nav updated; feed.json enriched with `language`, `icon`, per-item `tags[]` + `_steam_gid`; absolute hrefs on all `<link rel="alternate">` tags; 404.html head polished. Committed + pushed (commit fedfaef).
- [x] **stale-index guard + OG image generator** (2026-05-29) — `build-search-index.py` now outputs `patch_count`; `search/index.html` reads count dynamically; `.github/workflows/validate-index.yml` fails CI if index is stale; `scripts/hooks/pre-commit` auto-regenerates on commit; `Makefile` adds `install-hooks` + `og` targets; `scripts/build-og-images.py` generates 1200×630 PNG per patch using Pillow (purple/dark design, version + title + change-type pills + teaser bullet). Committed + pushed (commit 43ea6ae).
- [x] **OG images generated + wired into all pages** (2026-05-29) — ran `make og`, produced 9 PNG files in `og/`; added `og:image` + `og:image:width/height` + `twitter:image` + upgraded `twitter:card` to `summary_large_image` on all 4 pages (index, patch, diff, search); diff/search pages also got missing `og:type` + `og:site_name`. Default image = `og/v0.17.0.png` (latest patch). All OG images committed.
- [x] **v0.13.0 Shinobi Revamp + PWA offline support** (2026-05-29) — committed previously uncommitted work: `patches/v0.13.0.json` (8 added, 30 changed, 16 fixed, 0 removed) + `og/v0.13.0.png`; archive now complete at 10 versions (v0.13.0 → v0.17.0, 182 total entries); added `manifest.json` (PWA web app manifest) + `sw.js` (service worker — offline cache for 4 pages + core JSON assets); updated index.json, search-index.json, sitemap.xml, feeds, CHANGELOG, llms.txt, all 4 HTML pages. Pushed (commit e50a3d6).
- [x] **Steam API check** (2026-05-30) — `make check-steam` (also runs as `.github/scripts/pull-steam-news.py`): no new patches since v0.17.0 "The Echoing Spire". All 10 GIDs accounted for; "Servers downtime!" item correctly filtered by PATCH_KEYWORDS. Added `make check-steam` target to Makefile for easy local dry-runs.
- [x] **Tag pages shipped + discoverability wired** (2026-05-30) — `scripts/build-tag-pages.py` and `tag/` (9 per-tag HTML pages + index.html + index.json) were generated by the Makefile `tags` target since commit 0b59481 but never committed; committed now. `index.html` nav card added ("🏷️ Browse by Tag → /tag/"); `sitemap.xml` updated with /tag/ index + 9 per-tag entries; `llms.txt` updated with tag endpoint docs + tag/index.json. Pushed (commit 44b8c34).
- [x] **Markdown mirror archive + `make check` validation gate** (2026-05-30) — `scripts/build-md-mirror.py` generates `archive/YYYY-MM-DD-vX.Y.Z.md` for every patch JSON (GitHub-native readable, AI/fork-scrapable surface); 10 dated markdown files committed (v0.13.0 → v0.17.0). `make check` added: xmllint sitemap.xml + json.tool on all JSON artifacts — canonical pre-commit validation gate. `mirror` target wired into `build` dep chain. Pushed (commit bba8261).
- **NEXT**: Monitor for next SpiritVale patch (GH Actions runs daily at 01:00 UTC via `pull-steam-news.yml` — auto-creates PR when new patch found). When new patch arrives: classify bullets → remove `raw_body` → update index/feed/sitemap/CHANGELOG → `make build og` → commit + push.
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
- 🔴 **BLOCKER: CF Pages not connected** — sitemap, feed, and all SEO/redirect changes have zero live effect until Blocker #1 (CF Pages connect) and Blocker #2 (custom domain) are completed by เจ้านาย. Every push is only on GitHub; `spiritvale.tama.sh` is not yet live.
- 🟡 **CF Pages free tier**: 500 builds/month, 100k requests/day — เยอะมากสำหรับ static, ไม่น่าจะถึง
- 🟡 **DNS propagation**: ~5 นาที หลังเพิ่ม CNAME
- 🟢 **No secrets in repo** — public repo ปลอดภัย

## NOTES
- เกม SpiritVale = playtest (เจ้านายเล่นมาตั้งแต่ ~2026-05-14, 3046+ นาที playtime)
- Patch note ตัวแรกที่ host = v0.17.0 "The Echoing Spire" (2026-05-25)
