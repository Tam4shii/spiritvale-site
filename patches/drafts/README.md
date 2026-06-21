# patches/drafts/

This directory holds two types of unreviewed drafts written by `pull-steam-news.py`:

## 1. Patch drafts (`draft-*.json`)

Historical scaffolding from before the announcement-routing change. Each file pre-fills
`version`, `title`, `date`, `steam_news_id`, and `raw_body` from Steam.

**Boss action**: classify `raw_body` bullets → `added/changed/fixed/removed`, delete
`raw_body`, set `"current": true`, move to `patches/v{version}.json`, update
`patches/index.json`. These are then served by the site and validated by CI.

## 2. Announcement drafts (`announcement-*.json`)

Non-semver Steam posts (release date news, Next Fest, wipe notices, etc.) that matched
`PATCH_KEYWORDS` but had no version number in the title.

- `"version": "0.0.0"` — sentinel meaning "not a versioned game update"
- `"type": "announcement"` — skips semver validation downstream
- `new_draft=false` is **expected and correct** when only announcements are found — it means
  no new *patch* was released, even though a Steam post was detected and saved here

**Why `new_draft=false` ≠ "nothing happened"**: the script emits `new_announcement=true`
as a separate signal. CI fires a Discord notification; local runs print a `[BOSS ACTION]`
banner. Review → decide: publish as news item, archive, or ignore.

**Boss action checklist for announcement drafts**:
1. Read `announcement-<slug>.json` — check `raw_body` for what it says
2. Decide: publish, archive (`git rm` + commit), or ignore (leave untracked)
3. If publishing: move to `patches/news/` (future) or update PROJECT.md notes
4. Run `make check-clean` before pushing

## Local discovery

```bash
make check-drafts   # list all unreviewed drafts in this directory
```

## Known Stale Artifacts (safe to ignore — documented decisions)

### `announcement-spiritvale-official-date-release.json`

**Status**: EXPECTED NOISE — do not act until EA launch (2026-07-15)

**Why it's safe to ignore**:
- This is an **announcement**, not a patch (`"type": "announcement"`, `"version": "0.0.0"`). It covers the official release dates: Demo June 12, EA July 15 ~$15 USD.
- The events it announced are either **already live** (Demo launched June 12) or **upcoming** (EA July 15).
- The milestone banner (`showMilestoneBanner()` in `index.html`) already encodes these dates live on main — the announcement content is superseded by the existing UI.
- Dead window (2026-06-22 → 2026-07-15): servers are down per developer notice. No patches expected. Alert dedup stretched to 168h (weekly) during this window.

**Boss action at EA launch (2026-07-15)**: decide merge vs close on PR #1.
- Merge → publishes `/news/` page with the announcement content
- Close → archives draft (milestone banner already covers the key info)

**Machine-readable audit trail**: `state/draft-seen-counts.json["announcement-spiritvale-official-date-release.json"].triage_note` (written by idle-loop Forge run#33)

---

### `items_found=10` in poll logs

`items_found=10` is the **healthy baseline** — the script requests `count=10` from the Steam API (`STEAM_NEWS_COUNT=10`) and got back 10 items. `items_found == STEAM_NEWS_COUNT` means no items were dropped. A mismatch would trigger a `WARN: expected N items` in the logs and a count-delta alert from `check_baseline_delta()`. No reconciliation action needed when `items_found=10`.
