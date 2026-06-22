# PROJECT: spiritvale-site

**Status**: 🟢 Active · **Started**: 2026-05-25 · **Owner**: เจ้านาย (Tam4shii)

## 🚨 PENDING DECISIONS (updated 2026-06-09 step4)

| # | Item | Urgency | Action |
|---|---|---|---|
| 1 | **PR #1** — [SpiritVale Official Date release (June 8 / June 12 / July 15)](https://github.com/Tam4shii/spiritvale-site/pull/1) | 🟢 SILENCED — Telegram alerts archived (run#35); decide at EA (Jul 15) | **Context**: PR branch (`steam-patch-draft/spiritvale-official-date-release`) adds `patches/draft-spiritvale-official-date-release.json` only. The milestone banner (`showMilestoneBanner()` in `index.html`) already encodes June 12 demo + July 15 EA live on main. PR is safe to **close** with note "superseded by milestone banner". No pings until EA launch. |
| 2 | **Push 5 local commits to origin/main** | 🟡 MEDIUM — local only, CF Pages not serving latest | Local `main` is 5 ahead of `origin/main`. Commits are clean (`make check` ✅). Push when CF Pages is confirmed connected (see item 3). |
| 3 | **CF Pages not connected** | 🟡 MEDIUM — `spiritvale.tama.sh` not serving live | Go to dash.cloudflare.com → Pages → connect `Tam4shii/spiritvale-site` |

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

## COMPLETED FEATURES
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
- [x] **Markdown mirror archive + `make check` validation gate** (2026-05-30) — `scripts/build-md-mirror.py` generates `archive/YYYY-MM-DD-vX.Y.Z.md` for every patch JSON (GitHub-native readable, AI/fork-scrapable surface); 10 dated markdown files committed (v0.13.0 → v0.17.0). `make check` added: xmllint sitemap.xml + json.tool on all JSON artifacts — canonical pre-commit validation gate. `mirror` target wired into `build` dep chain. Pushed (commit bba8261). **Verified 2026-05-30: `make check` exits 0 — all 6 artifacts (sitemap.xml, tag/index.json, patches/index.json, search-index.json, feed.json, feed.xml) pass.**
- [x] **Discord draft-detection notification** (2026-05-30) — added step to `pull-steam-news.yml`: when GH Actions detects a new Steam patch and opens a PR, a Discord embed (amber, "Review needed") fires to `DISCORD_PATCH_WEBHOOK`. Distinct from existing `discord-notify.yml` (green embed, fires on merge to main). Two-stage push loop: detect → amber notify → boss classifies → merge → green notify.
- [x] **CONTRIBUTING.md** (2026-05-30) — community contribution guide: patch submission workflow, schema contract, PR checklist, `make build check` gate; modelled on warframestat.us / wago.tools open-data contribution patterns.
- [x] **Embed widget + poll timestamp** (2026-05-30) — `embed/index.html`: JS snippet + iframe widget for dropping latest patch card into Claude artifacts/fan sites; auto-detects embedded mode; `_headers` updated with frame-ancestors * for `/embed/*`; `pull-steam-news.py` stamps `last_polled_at` into `patches/index.json` after every GH Actions run; homepage nav + sitemap + llms.txt updated. Committed + pushed (commit d9bdd01).
- [x] **Hardening iteration** (2026-05-30) — `stamp_index()` wrapped in try/except (audit-trail failure is non-fatal to poll run); CSP diff for `/embed/*` documented in `_headers`; `embed/index.html` gets `noindex,nofollow` (iframe consumer, not search target); `openapi.json` (OpenAPI 3.1) added covering 9 endpoints — already accessible via `/v1/openapi.json` through existing `_redirects` rewrite; llms.txt wired. `make check` exits 0. Pushed (commit 15b9b01).
- [x] **`_headers` security audit trail + CDN stale-while-revalidate** (2026-05-30) — `/embed/*` CSP comment expanded into explicit 4-point audit log (changed vs. unchanged directives + rationale for each); `stale-while-revalidate` added to all mutable endpoints (`/patch.json`, `/patches/latest.json`, `/patches/index.json` → 300s; `/feed.*` → 600s) — CDN serves cached response instantly while re-fetching in background (warframestat.us CDN pattern). Immutable `/patches/v*.json` unchanged.

- [x] **Per-tag Atom feeds** (2026-05-31) — `build-tag-pages.py` extended to emit `tag/<slug>/feed.xml` (Atom RFC 4287) for all 9 tags; entries grouped by patch version, newest-first; `<link rel="alternate" type="application/atom+xml">` auto-discovery added to per-tag HTML; `_headers` wired with `application/atom+xml; charset=utf-8` + stale-while-revalidate=600; sitemap.xml +9 entries; llms.txt documented. SteamDB pattern: fans subscribe to "Shinobi only" or "Boss only" changes. Pushed (commit e637a45).
- [x] **Self-documenting poll_tz + JS client SDK** (2026-05-31) — `poll_tz: "UTC"` added to `patches/index.json` + `openapi.json` PatchIndex schema enriched with UTC description (Step 2 fix: future readers won't mistake UTC date gaps for staleness). `clients/spiritvale.js` added — zero-dep ES module (`getLatest`, `getIndex`, `getPatch`, `getDiff`); works in browser + Node ≥18 (Step 3 fix: warframestat.us SDK fleet pattern). All changes in one atomic commit. llms.txt wired. `make check` ✅. Pushed (commit d13db09).
- [x] **TypeScript declarations for JS SDK** (2026-05-31) — `clients/spiritvale.d.ts` added: full type coverage for all 5 exported functions + 8 shared interfaces (PatchNote, PatchIndex, PatchVersionEntry, ChangeCounts, SearchIndex, SearchEntry, DiffResult, DiffEntry); types derived from schema/patch.json and live index.json shape. JSDoc stale "128+" count removed (count grows with patches). `make check` ✅. Pushed (commit 719a457).
- [x] **Type-sync guard + SearchEntry fix** (2026-05-31) — `scripts/check-types-vs-schema.py` added as `make check-types` gate; `SearchEntry.type` union updated to include `deprecated | security` (was drifting from schema); `getDiff()` accumulates deprecated/security keys; pushed (commit cb02b0c).
- [x] **`clients/README.md`** (2026-05-31) — SDK usage documentation with browser + Node examples, function table, TypeScript import guide, error handling pattern, and CORS note; wired into GitHub directory rendering for discoverability.
- [x] **validate-stats.yml CI guard + `make check-stats`** (2026-05-31) — `.github/workflows/validate-stats.yml` added: fails CI if `stats.json` is stale relative to `patches/index.json`, `tag/index.json`, or `search-index.json` (mirrors `validate-index.yml` pattern). `make check-stats` provides the same gate locally. `stats.json` + `patches/index.json` `last_polled_at` stamped from previous idle-loop run. Committed + pushed (commit 65f29af).
- [x] **Python SDK `clients/spiritvale.py`** (2026-05-31) — zero-dependency Python client (stdlib `urllib.request`, Python ≥ 3.8); 5 functions matching JS SDK surface: `get_latest`, `get_index`, `get_patch`, `get_search_index`, `get_diff`; diff logic smoke-tested against local JSON (34 added, 72 changed across v0.13.0→v0.17.0); README expanded with Python section (examples, function table, error handling). Competitive pattern: warframestat.us Python SDK is the primary driver of Discord-bot adoption — Python ecosystem = discord.py bots + data scrapers.
- [x] **v0.18.0 "New and Revamped Maps" shipped** (2026-06-03) — idle-loop Forge detected uncommitted v0.18.0 classified patch; moved `draft-0.18.0.json` → `patches/drafts/`; generated `og/v0.18.0.png`; rebuilt health.json (severity ok, match=true); committed full release: 11 versions (v0.13.0 → v0.18.0, 196 total entries: 45 added, 108 changed, 41 fixed, 2 removed). archive/2026-06-02-v0.18.0.md + tag pages (autocast, balance, buff, economy, equipment, nerf, new-system) all committed.

## FUTURE IDEAS (ถ้าจะขยาย)
- Build guides / class info
- Boss tracker / event calendar
- REST API endpoints (e.g. `/builds`, `/items`)
- Multi-language toggle (TH/EN)

## Monitoring Schedule (Dead-Window Aware)

> Pattern: warframestat.us / wago.tools explicitly document known quiet windows to avoid alert fatigue during periods when no patches are expected.

| Period | Window | Expected Activity | Poll cadence | Notes |
|---|---|---|---|---|
| Post-playtest | 2026-06-08 → 2026-06-12 | Demo prep; minor hotfixes possible | daily (GH Actions 01:00 UTC) | Demo launched June 12 |
| **Dead window** | **2026-06-22 → 2026-07-15** | **No patches expected** (dev focus = EA polish) | **daily (unchanged — free)** | Alerts are noise; stale-draft pings suppressed |
| EA Launch window | 2026-07-15 → 2026-07-22 | High patch probability (day-one fixes) | daily | Resume full alert sensitivity |
| Post-EA steady | 2026-07-22 + | Normal cadence | daily | Typical 1-2 week patch cycle |

**Dead-window alert behaviour**: GH Actions still polls daily (cron cost = 0). Stale-draft alerts during the dead window are expected noise — not a signal to act. Next meaningful check: **2026-07-15** (Early Access launch).

## Next Steps

> **Monitoring mode** — no active development task; waiting for next Steam patch.

When GH Actions (`pull-steam-news.yml`, 01:00 UTC daily) opens a draft PR:
1. Discord amber embed fires automatically (DISCORD_PATCH_WEBHOOK) — boss gets pinged
2. Open `patches/draft-<slug>.json`
3. Classify bullets from `raw_body` → `added` / `changed` / `fixed` / `removed`
4. Delete the `raw_body` field; set `"current": true`; flip previous latest to `false`
5. Rename file to `patches/v{version}.json`; update `patches/index.json`
6. Run `make build og check` — confirm exit 0
7. Commit + push → CF Pages auto-deploys; Discord green embed fires on merge
8. **Run `make check-steam`** — syncs `state/steam-news-baseline.json` to new version (prevents drift; `make check` will fail on next run if skipped)

**Staleness root cause (documented 2026-06-02)**: `pull-steam-news.yml` writes `last_polled_at` into `patches/index.json` on the GH Actions runner, but monitoring-only runs (no draft) never committed/pushed that change to `main` — the workspace change was silently discarded. `stats.json` / `health.json` were also never rebuilt by the workflow. Fixed: added "Rebuild stats + health, commit poll timestamp" step to `pull-steam-news.yml` — now runs `make stats && make health` and commits the 3 files after every poll, draft or not.

**Baseline drift root cause (documented 2026-06-03)**: `state/steam-news-baseline.json` is written by `pull-steam-news.py:save_baseline()` — it only runs during `make check-steam` / GH Actions poll. When a new patch is committed directly (e.g., Step 26's v0.18.0 commit), the script is never called and the baseline stays at the old version. **Process guard added (Step 28)**: `make check` now asserts `baseline.latest_version == index.latest_version`; fails with actionable message if drift is detected. Named process gap: the release checklist (Next Steps §6) must include `make check-steam` or `make check-baseline` as the final step after committing any new patch version.

**v0.18.0 deployment status**: v0.18.0 "New and Revamped Maps" was published on 2026-06-02 (Steam) and committed to `main` on 2026-06-03 (commit includes archive, OG image, tag pages). Site reflects the latest patch as of that commit. CF Pages is **not** connected (Blocker #1) — live URL `spiritvale.tama.sh` not yet serving; GitHub Pages preview only.
**Last `make check` run**: 2026-06-07T08:33Z (idle-loop Forge 2026-06-07 run#11) — ✅ exit 0 (all 8 artifacts valid; baseline OK at 0.18.0)
**Last `make check-stats` run**: 2026-06-03T01:19Z (idle-loop Forge Step 30) — ✅ fresh; `per_version_changes` field added to stats.json (11 versions)
**Last Steam check**: 2026-06-07T08:33:03Z (idle-loop Forge 2026-06-07 run#11) — ✅ live Steam API poll (HTTP 200); items_found=10; new_draft=false. **🚨 ANNOUNCEMENT DRAFT STILL PENDING**: `patches/drafts/announcement-spiritvale-official-date-release.json` — seen_count=5 (first_seen: 2026-06-05T20:31Z); [URGENT] alert #4 sent via Telegram (15h to deadline). Awaiting boss decision on routing (PR #1).
**🚨🚨 DEADLINE TODAY**: Playtest ends **2026-06-08 (TOMORROW)**. Demo launches **2026-06-12**. Early Access **2026-07-15** ~$15 USD. `make check-deadlines` → CRITICAL (days_until=1).
**Poll terminology note** (added run#6): "dry-run" is ambiguous — future logs must say "live Steam API poll" (real HTTP call) or "skipped/mocked" explicitly. Never use "dry-run" for monitoring-mode polls.
**run#11 status** (2026-06-07 idle-loop Forge):
- ✅ `make check` exit 0 — all 8 artifacts valid; baseline OK at 0.18.0
- ✅ Live Steam poll: items_found=10; no new patch; [URGENT] alert #4 sent (15h to deadline)
- ✅ **entity pages shipped** — 7 entity timelines + index; sitemap/llms.txt/homepage wired
- 🚨 PR #1 still OPEN — boss action required
**run#12 status** (2026-06-07 idle-loop Forge):
- ✅ `make check` exit 0 — all artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: items_found=10; no new patch; stale_draft seen_count=6; alert suppressed (<12h ago)
- ✅ **health.json false-warn fix** — `build-health.py` now reads `state/last-poll.json` as freshness fallback; prevents false warn/critical during monitoring gaps. Commit 7de892a pushed.
- 🚨 PR #1 still OPEN — boss action required (deadline passed 2026-06-08)
**run#13 status** (2026-06-07 idle-loop Forge):
- ✅ **build-health.py comment hardened** — dual-source fallback comment now explicitly says "gitignored"; FileNotFoundError path annotated as "expected on clean clone / CI". Prevents future regression from a reader simplifying the logic.
- ✅ **`/status` slash command shipped** — `discord-example.py` + `spiritvale.py` (`get_health()`) — severity color-coded embed (green/amber/red); surfaces hours_since_poll, latest_version, total_patches directly in Discord. Warframestat.us pattern: Discord bot as primary adoption driver.
- ℹ️ **Suppressed draft state (expected)**: `patches/drafts/announcement-spiritvale-official-date-release.json` seen_count=6 as of run#12. Alert suppression is correct — last alert was sent <12h prior. Next run will re-evaluate; if seen_count increments without a new alert, check `ALERT_COOLDOWN_HOURS` in `pull-steam-news.py`.
**run#14 status** (2026-06-07 idle-loop Forge):
- ✅ `make check` exit 0 — all artifacts valid; baseline OK at 0.18.0; **health severity: ok** (dual-source fallback working)
- ✅ **Merge conflict resolved** — local branch had diverged from remote (1 local commit vs 7 remote commits since `0f2da51`); rebased `5d4bca1` (WebSub stale-alert log) on top of remote; resolved conflict in `.github/scripts/pull-steam-news.py` by preserving both PR1 escalation constants and WebSub constants; pushed `a82f66c` to origin/main
- ℹ️ **Root cause of health `warn`**: `patches/index.json.last_polled_at` is stale at 2026-06-05; `build-health.py` falls back to `state/last-poll.json` (gitignored, written by local poll runs) → health now reads `ok` locally. GH Actions runner will also write `state/last-poll.json` before building health (workflow unchanged — this was already working in run#12).
- 🚨 PR #1 still OPEN — boss action required (deadline 2026-06-08 passed)
**run#15 status** (2026-06-08 idle-loop Forge):
- ✅ `make check` exit 0 — all artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest
- ✅ State committed — `state/draft-seen-counts.json` (seen_count=7, last_seen=2026-06-07T18:06Z)
- 🚨 PR #1 still OPEN — URGENT alert #5 sent (6h remaining at poll time); playtest ended 2026-06-08; announcement covers June 12 demo + July 15 Early Access ~$15
**run#19 status** (2026-06-08 idle-loop Forge):
- ✅ `make check` exit 0 — all artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; stale alert suppressed (<12h)
- ✅ **PR #1 pre-classified** — `patches/draft-spiritvale-official-date-release.json` now has 8 classified bullets in added/changed/fixed/removed; `raw_body` removed (schema compliance); pushed to PR branch `422733e`. PR is now merge-ready — boss only needs to decide merge vs close.
- 🚨 PR #1 still OPEN — boss action required (playtest ended June 8, Demo June 12 in 4 days)
**run#18 status** (2026-06-08 idle-loop Forge):
- ✅ `make check` exit 0 — all artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ **Interrupted rebase resolved** — `api/health.json` had merge conflict markers; regenerated via `make health`, staged, continued rebase. `feat(news): OG tags + body expand` (0a352d2) now on main
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest
- ✅ Pushed `7c6ca06` to origin/main (2 commits: feat + state)
- 🚨 PR #1 OVERDUE — alert #7 sent; playtest ended 2026-06-08 (9h past deadline); boss action required
**run#20 status** (2026-06-09 idle-loop Forge):
- ✅ `make check` exit 0 — all artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; stale alert suppressed (<12h)
- ✅ **`/news/` nav card wired to homepage** — page existed but was missing from `index.html` nav grid; also added `<link rel="alternate">` for `news/feed.xml` in `<head>`. Pushed (commit 0d95458). Demo launches **June 12 (3 days)**.
- 🚨 PR #1 still OPEN — boss action required (deadline passed 2026-06-08, alert #8 sent)
**run#21 status** (2026-06-09 idle-loop Forge):
- ✅ `make check` exit 0 — all artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; stale alert suppressed (<12h)
- ✅ **Demo launch countdown banner shipped** — `index.html`: time-gated banner shows "Demo in N days" until June 12, "Demo live! EA July 15" until July 15, then auto-hides; dismissable via localStorage; links to /news/. Pushed (commit 3468049).
- 🚨 PR #1 still OPEN — boss action required (playtest ended June 8, Demo June 12 tomorrow)
**run#22 status** (2026-06-09 idle-loop Forge):
- ✅ `make check` exit 0 — all artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; stale draft seen_count=9 (local sync), remote shows 12
- ✅ **6 local commits pushed to origin/main** — rebased on top of remote (remote had 7 commits since last local sync); resolved state-file conflict by skipping local state commit (remote's seen_count=12 is more authoritative); commits include: licenses, .gitignore clarification, CF Pages deploy check, /news/ nav, phase-aware banner, banner date clarification + pyproject.toml
- 🚨 PR #1 still OPEN — Demo launches **June 12 (3 days)** — boss action required: (a) merge → publishes /news/ page, (b) close → archives draft

**run#31 status** (2026-06-19 idle-loop Forge):
- ✅ `make check` exit 0 — all 11 artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: items_found=10; no new patch; v0.18.0 still latest; `state/last-poll.json` = 2026-06-19T13:21:48Z
- ✅ **Demo launched June 12** — milestone banner showing "Demo is live! EA July 15" ✅ (phase='demo-live' logic verified)
- ✅ **Dead window starts June 22** (3 days) — alert suppression already active (PR#1 alerts downgraded to weekly); monitoring continues daily (free cron)
- ℹ️ State: `state/draft-seen-counts.json` seen_count=35 committed (was 32); PR#1 still OPEN (boss action required — (a) merge or (b) close)
- 🚨 PR #1 still OPEN — pre-classified, merge-ready: https://github.com/Tam4shii/spiritvale-site/pull/1

**run#39 status** (2026-06-21 idle-loop Forge — Step 4 iteration):
- ✅ `make check-dead-window` — 3/3 boundary tests passed before window opens 2026-06-22 tomorrow (Step 2 fix: guard verified, not just "already coded")
- ✅ **Known-artifact documentation** — `patches/drafts/README.md` now has "Known Stale Artifacts" section explaining WHY announcement draft is safe to ignore (dead window, content superseded by milestone banner) + items_found=10 healthy-baseline note (Step 2 fix: decision documented, not silently dismissed)
- ✅ **Public `/status` page** — `status/index.html` added; consumes `api/health.json`; severity pill, version, hours-since-poll, dead-window banner, baseline match row (Step 3 pattern: the-hideout/status public status page)
- ✅ Pushed commit 252be1a to origin/main; `make check` exit 0 all 11 artifacts valid

**run#35 status** (2026-06-20 idle-loop Forge — Step 4 iteration):
- ✅ **Alert fatigue fix**: `pr1` blocker archived in `persistent-blockers.json` (alert_count was 22, deadline expired 12d ago). `check-deadlines.py` now skips `archived:true` entries → exit 0, no Telegram.
- ✅ **Dead-window code guard**: `DEAD_WINDOWS=[("2026-06-22","2026-07-15")]` added to `check-deadlines.py` (warframestat.us pattern). Severity auto-caps at "warn" during window → Telegram suppressed + exit 0. Takes effect Jun 22.
- ✅ `state.json` rebuilt — `deadline_alerts=0`, `worst_severity=ok`
- ℹ️ PR #1 still OPEN (merge-ready) — Telegram escalation silenced; boss to decide merge vs close at EA launch (2026-07-15)

**run#34 status** (2026-06-20 idle-loop Forge):
- ✅ `make check` exit 0 — all 11 artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; seen_count=38 (was 37)
- ✅ State committed — `state/draft-seen-counts.json` + `state/persistent-blockers.json` pushed (commit a58c14f)
- 🚨 PR #1 still OPEN — hyper-stale (38 cycles); URGENT alert #22 sent; dead window starts Jun 22 (2 days)

**run#32 status** (2026-06-20 idle-loop Forge):
- ✅ `make check` exit 0 — all 11 artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; seen_count=36 (was 35)
- ✅ **MCP server shipped** — `mcp/server.py` (FastMCP, 5 tools: get_latest_patch/list_patches/get_patch/search_patches/get_diff); works against local files, no HTTP needed; committed+pushed
- ✅ **SDK get_bot_json()** — `clients/spiritvale.py` adds `get_bot_json()` function; discord-example.py `/latest` command updated to use pre-formatted bot.json embed (tarkov.dev reference bot pattern)
- 🚨 PR #1 still OPEN — dead window starts in **2 days** (Jun 22); alert #21 sent; boss action: merge or close

**run#38 status** (2026-06-21 idle-loop Forge):
- ✅ `make check` exit 0 — all 11 artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; seen_count=40 (was 39)
- ✅ State committed — `state/draft-seen-counts.json` pushed (commit bec381d)
- ℹ️ Dead window starts **tomorrow (2026-06-22)** — last pre-dead-window monitoring run; alert suppression takes effect Jun 22
- ℹ️ PR #1 auto-silenced (13d overdue); boss action at EA launch 2026-07-15

**run#44 status** (2026-06-22 idle-loop Forge):
- ✅ `make check` exit 0 — all 11 artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; seen_count=45 (was 44)
- ✅ **Bug fix**: `state.json` had stale `dead_window.active=false` (GH Actions commit `2473bc1` updated `api/health.json` but didn't rebuild `state.json`); ran `build-state.py` to sync — now correctly shows `active=true, severity=ok`
- ✅ State committed — `state/draft-seen-counts.json` + `state.json` pushed; dead window ACTIVE (Jun 22–Jul 15)
- ℹ️ PR #1 auto-silenced; boss action at EA launch 2026-07-15

**run#43 status** (2026-06-22 idle-loop Forge):
- ✅ `make check` exit 0 — all 11 artifacts valid; baseline OK at 0.18.0; health severity: warn (stale poll — expected during dead window)
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; seen_count=44 (was 43)
- ✅ State committed — `state/draft-seen-counts.json` pushed; dead window ACTIVE (Jun 22–Jul 15)
- ✅ **Improvements shipped**: Makefile `make monitor` DECISION output line; index.html delta banner shows missed-patch count ("3 new patches" vs generic "new update")
- ℹ️ PR #1 auto-silenced; boss action at EA launch 2026-07-15

**run#42 status** (2026-06-22 idle-loop Forge):
- ✅ `make check` exit 0 — all 11 artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; seen_count=43 (was 42)
- ✅ State committed — `state/draft-seen-counts.json` pushed (commit 7ea8b6a)
- ℹ️ Dead window INACTIVE until midnight UTC Jun 22 (~6h); will be ACTIVE on next GH Actions poll (01:00 UTC)
- ℹ️ PR #1 auto-silenced (13d overdue); boss action at EA launch 2026-07-15

**run#41 status** (2026-06-21 idle-loop Forge):
- ✅ `make check` exit 0 — all 11 artifacts valid; baseline OK at 0.18.0; health severity: ok
- ✅ Live Steam poll: HTTP 200; items_found=10; no new patch; v0.18.0 still latest; seen_count=42 (was 41)
- ✅ State committed — `state/draft-seen-counts.json` pushed (commit 69fd743)
- ℹ️ **Dead window starts TOMORROW (2026-06-22)** — alert suppression takes effect; no new patches expected until EA launch Jul 15
- ℹ️ PR #1 auto-silenced (13d overdue); boss action at EA launch 2026-07-15

**Next idle-loop action**: Monitoring mode — **dead window active Jun 22–Jul 15**; no new patches expected until EA launch. Run daily poll + `make check`; commit state only if seen_count changes. Next meaningful check: **2026-07-15** (EA launch day).
**Last push to origin/main**: run#44 (2026-06-22) — state.json dead_window sync fix + seen_count=45.
**Push/CI status**: commit 4e9bc6b pushed to `origin/main` (2026-06-05 idle-loop Forge — poll timestamp update + announcement flagged). CF Pages NOT connected (Blocker #1 open) → pushes do **not** trigger deployments.
**Poll refactor (2026-06-03)**: `pull-steam-news.py` no longer calls `stamp_index` on monitoring-only runs — writes gitignored `state/last-poll.json` instead; eliminates no-op commit noise. `clients/bots/requirements.txt` added; `.env` loading via python-dotenv; `SPIRITVALE_CHANNEL_ID` documented in `.env.example`.
**CI fix (2026-06-01)**: `validate-schema.yml` was failing with `ajv: parameter -d is required` — fixed by replacing positional glob args with a `for f in ...; do ajv -d "$f"; done` loop (commit 87ec0be). Will auto-verify on next patches/** push.
**`last_polled_at` null origin**: field was initialized as `null` in commit `15b9b01` (2026-05-30 hardening). First value (`2026-05-30T18:07:01Z`) written by idle-loop local dry-run on 2026-05-31; not by GH Actions (GH Actions requires CF Pages + DISCORD_PATCH_WEBHOOK secret, neither configured yet).

## BLOCKERS (Boss Actions Required)
| # | Action | Where | Notes |
|---|---|---|---|
| 1 | Connect CF Pages | [dash.cloudflare.com → Pages → New → Connect GitHub → Tam4shii/spiritvale-site](https://dash.cloudflare.com/) | No build command, output dir = `/` · **last checked: 2026-05-30 — still pending** |
| 2 | Set custom domain | CF Pages → Custom domains → `spiritvale.tama.sh` | CNAME auto-created; ~5 min DNS propagation · depends on #1 |
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
