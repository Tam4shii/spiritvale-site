.PHONY: build index tags validate mirror stats health badge diff-endpoints check check-ci check-types check-stats check-clean og install-hooks check-steam check-baseline check-sdk check-drafts help

# Regenerate all derived artifacts (run before committing a new patch).
build: index tags validate mirror stats health badge diff-endpoints

# Rebuild search-index.json from patches/v*.json.
# MUST run whenever a patch file is added or modified.
index:
	python3 scripts/build-search-index.py

# Generate /tag/<slug>/ static pages from search-index.json.
# Run after `make index` to reflect latest tag data.
tags:
	python3 scripts/build-tag-pages.py

# Validate all patch files against schema/patch.json.
validate:
	python3 scripts/validate-patches.py

# Generate dated markdown mirror of each patch (archive/YYYY-MM-DD-vX.Y.Z.md).
mirror:
	python3 scripts/build-md-mirror.py

# Generate stats.json — patch cadence, change totals, top tags (OpenDota pattern).
# Run after `make index` so search-index.json is current.
stats:
	python3 scripts/build-stats.py

# Generate badge/latest.json — shields.io Endpoint-URL badge (current patch version).
# Embed: https://img.shields.io/endpoint?url=https://spiritvale.tama.sh/badge/latest.json
badge:
	python3 scripts/build-badge.py

# Generate api/health.json — structured freshness endpoint.
# Derives stale/warn/critical from stats.json last_polled_at.
# Consumable by Grafana, uptime monitors, Discord bots without client-side math.
# NOTE: api/health.json IS a committed artifact (not ephemeral / not gitignored).
# If it goes missing: check `git log -- api/health.json` — it should appear in recent commits.
# Root cause for missing file is typically a `git clean -f` or stale loop run that didn't regenerate it.
# Fix: run `make health` then commit. The `make check` target now validates its presence.
health:
	python3 scripts/build-health.py

# Generate server-side diff JSON for every adjacent and cumulative version pair.
# Produces diff/v{from}...v{to}.json — immutable, CDN-cacheable, SDK/bot-friendly.
# Pattern mirrors wago.tools URL scheme. Avoids client-side N+1 patch fetches.
diff-endpoints:
	python3 scripts/build-diff-endpoints.py

# Validate XML and JSON derived artifacts for crawler correctness.
check:
	@echo "--- sitemap.xml ---" && xmllint --noout sitemap.xml && echo "sitemap.xml: OK"
	@echo "--- tag/index.json ---" && python3 -m json.tool tag/index.json > /dev/null && echo "tag/index.json: OK"
	@echo "--- patches/index.json ---" && python3 -m json.tool patches/index.json > /dev/null && echo "patches/index.json: OK"
	@echo "--- search-index.json ---" && python3 -m json.tool search-index.json > /dev/null && echo "search-index.json: OK"
	@echo "--- feed.json ---" && python3 -m json.tool feed.json > /dev/null && echo "feed.json: OK"
	@echo "--- feed.xml ---" && xmllint --noout feed.xml && echo "feed.xml: OK"
	@echo "--- stats.json ---" && python3 -m json.tool stats.json > /dev/null && echo "stats.json: OK"
	@echo "--- api/health.json ---" && python3 -m json.tool api/health.json > /dev/null && echo "api/health.json: OK"
	@python3 -c "\
import json, sys; \
h = json.load(open('api/health.json')); \
sev = h.get('severity', 'unknown'); \
print(f'health severity: {sev}') if sev in ('ok','warn') else (print(f'ERROR: health.json severity={sev}', file=sys.stderr) or sys.exit(1))"
	@echo "--- diff/index.json ---" && python3 -m json.tool diff/index.json > /dev/null && echo "diff/index.json: OK"
	@python3 -c "\
import json, sys; \
idx = json.load(open('patches/index.json')); \
base = json.load(open('state/steam-news-baseline.json')) if __import__('os').path.exists('state/steam-news-baseline.json') else {}; \
iv = idx.get('latest_version'); bv = base.get('latest_version'); \
(print(f'baseline: OK (both {iv})') if iv == bv else (print(f'ERROR: baseline drift — index={iv} but baseline={bv}; run make check-steam to sync', file=sys.stderr) or sys.exit(1))) \
if bv else print('baseline: SKIP (no baseline file yet)')"
	@echo "All checks passed."

# Validate clients/spiritvale.d.ts and openapi.json are in sync with schema/patch.json.
# Add to CI alongside `make check` to catch type drift before publish.
check-types:
	python3 scripts/check-types-vs-schema.py

# Verify stats.json is not stale relative to its inputs (patches/index.json, tag/index.json, search-index.json).
# Mirrors validate-stats.yml CI gate for local pre-commit use.
check-stats:
	@python3 -c "\
import json, subprocess, sys, tempfile, os; \
d = json.load(open('stats.json')); \
[d.pop(k, None) for k in ('generated_at', 'last_polled_at')]; \
json.dump(d, open('/tmp/stats-before.json', 'w'), sort_keys=True)"
	@python3 scripts/build-stats.py > /dev/null
	@python3 -c "\
import json; \
d = json.load(open('stats.json')); \
[d.pop(k, None) for k in ('generated_at', 'last_polled_at')]; \
json.dump(d, open('/tmp/stats-after.json', 'w'), sort_keys=True)"
	@diff /tmp/stats-before.json /tmp/stats-after.json \
	  && echo "stats.json is fresh ✓" \
	  || (echo "ERROR: stats.json is stale — run make stats and commit" && exit 1)

# Assert the working tree is clean before marking a step complete.
# Add to loop monitoring protocol: run after every commit gate.
# Exits non-zero if any tracked file is modified or staged — catches stale carry-over.
check-clean:
	@git diff --quiet && git diff --cached --quiet \
	  && echo "Working tree is clean ✓" \
	  || (echo "ERROR: uncommitted changes detected — commit or stash before proceeding" && exit 1)

# Generate per-patch OG social-preview images to og/*.png.
# Run: make og  (requires: pip install pillow)
og:
	python3 scripts/build-og-images.py

# Check Steam AppNews for new patch notes (mirrors what GH Actions runs daily).
check-steam:
	python3 .github/scripts/pull-steam-news.py

# Verify GH Actions cron (pull-steam-news.yml) has been firing successfully.
# Requires: gh CLI authenticated. Run periodically to confirm monitoring is alive.
check-ci:
	@echo "--- GH Actions: pull-steam-news (last 7 runs) ---"
	gh run list --workflow=pull-steam-news.yml --limit=7
	@echo ""
	@echo "--- GH Actions: validate-schema (last 3 runs) ---"
	gh run list --workflow=validate-schema.yml --limit=3

# Install the pre-commit hook that auto-regenerates search-index.json.
install-hooks:
	cp scripts/hooks/pre-commit .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
	@echo "Pre-commit hook installed."

check-baseline:
	@python3 -c "\
import json, sys, os; \
idx = json.load(open('patches/index.json')); \
base = json.load(open('state/steam-news-baseline.json')) if os.path.exists('state/steam-news-baseline.json') else {}; \
iv = idx.get('latest_version'); bv = base.get('latest_version'); \
sys.exit(0) if not bv else (sys.exit(0) if iv == bv else (print(f'ERROR: baseline drift — index={iv} but baseline={bv}; run make check-steam', file=sys.stderr) or sys.exit(1)))"
	@echo "Baseline version matches index ✓"

# List all unreviewed drafts in patches/drafts/ — patch drafts and announcement drafts.
# Mirrors SteamDB's "unprocessed items" browse pattern: surface pending work locally
# without needing CI. new_draft=false ≠ empty; announcements land here too.
# seen_count: how many poll cycles the draft has sat unreviewed (from state/draft-seen-counts.json).
check-drafts:
	@echo "--- Patch drafts (patches/drafts/draft-*.json) ---"
	@ls patches/drafts/draft-*.json 2>/dev/null | while read f; do \
	  echo "  $$f"; \
	  python3 -c "import json,sys; d=json.load(open('$$f')); print(f'    version={d.get(\"version\")}  title={d.get(\"title\",\"\")[:60]}')"; \
	done || echo "  (none)"
	@echo ""
	@echo "--- Announcement drafts (patches/drafts/announcement-*.json) ---"
	@ls patches/drafts/announcement-*.json 2>/dev/null | while read f; do \
	  base=$$(basename "$$f"); \
	  echo "  $$f"; \
	  python3 -c "\
import json, os, sys; \
d = json.load(open('$$f')); \
sc = json.load(open('state/draft-seen-counts.json')) if os.path.exists('state/draft-seen-counts.json') else {}; \
entry = sc.get('$$base', {}); \
seen = entry.get('seen_count', 0); \
first = entry.get('first_seen_at', 'unknown'); \
staleness = f'[STALE: seen {seen}x since {first[:10]}]' if seen > 0 else '[NEW — not yet polled as stale]'; \
print(f'    date={d.get(\"date\")}  title={d.get(\"title\",\"\")[:55]}'); \
print(f'    {staleness}')"; \
	done || echo "  (none)"
	@echo ""
	@echo "  Review workflow: patches/drafts/README.md"

# Validate @spiritvale/client is publish-ready without uploading to npm.
# Run before cutting a GitHub release to confirm package contents, types, and README are correct.
# Mirrors the warframestat.us "distribution beats discoverability" model — SDK ships as npm package.
check-sdk:
	@echo "--- npm pack dry-run (clients/) ---"
	cd clients && npm pack --dry-run
	@echo "SDK package check passed ✓"

help:
	@echo "Targets:"
	@echo "  make build          — index + validate (run before any patch commit)"
	@echo "  make index          — rebuild search-index.json"
	@echo "  make validate       — validate all patches against schema"
	@echo "  make og             — generate OG preview images (requires pillow)"
	@echo "  make tags           — generate /tag/<slug>/ static pages"
	@echo "  make mirror         — generate archive/YYYY-MM-DD-vX.Y.Z.md for each patch"
	@echo "  make check          — validate sitemap.xml + JSON artifacts + baseline drift"
	@echo "  make check-baseline — assert baseline version == index latest_version (drift guard)"
	@echo "  make check-types    — validate .d.ts + openapi.json in sync with schema/patch.json"
	@echo "  make check-stats    — verify stats.json is not stale relative to its inputs"
	@echo "  make check-clean    — assert git working tree is clean (commit gate)"
	@echo "  make install-hooks  — install git pre-commit hook"
	@echo "  make check-steam    — poll Steam API; new_draft=true (patch) | new_announcement=true (non-semver); stamps index + baseline"
	@echo "  make check-drafts   — list unreviewed patch + announcement drafts in patches/drafts/"
	@echo "  make check-ci       — verify GH Actions cron is firing (requires gh CLI)"
	@echo "  make check-sdk      — dry-run npm pack for @spiritvale/client (pre-release gate)"
	@echo "  make stats          — generate stats.json (cadence, change totals, top tags)"
	@echo "  make health         — generate api/health.json (structured freshness endpoint)"
	@echo "  make diff-endpoints — generate diff/v{from}...v{to}.json static endpoints"
	@echo "  make badge          — generate badge/latest.json (shields.io endpoint badge)"
