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
