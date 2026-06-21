.PHONY: build index tags entities validate mirror stats health badge diff-endpoints jsonld state snapshot-state csv check check-ci check-types check-stats check-clean check-monitor og install-hooks check-steam check-baseline check-sdk check-drafts check-deadlines check-deploy check-dead-window help

# Regenerate all derived artifacts (run before committing a new patch).
build: index tags entities validate mirror stats health badge diff-endpoints jsonld state csv

# Rebuild search-index.json from patches/v*.json.
# MUST run whenever a patch file is added or modified.
index:
	python3 scripts/build-search-index.py

# Generate /tag/<slug>/ static pages from search-index.json.
# Run after `make index` to reflect latest tag data.
tags:
	python3 scripts/build-tag-pages.py

# Generate /entity/<slug>/ timeline pages from search-index.json.
# Extracts entity mentions by tag AND text match (poedb.tw pattern — cross-version balance history).
# Run after `make index` to reflect latest data.
entities:
	python3 scripts/build-entity-pages.py

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

# Inject Schema.org JSON-LD into index.html and patch/index.html for rich-result SEO.
# Pattern: SteamDB/wago.tools — structured data drives Google rich results for
# "<game> <version> patch notes" queries. Idempotent via marker comments.
jsonld:
	python3 scripts/build-jsonld.py

# Generate server-side diff JSON for every adjacent and cumulative version pair.
# Produces diff/v{from}...v{to}.json — immutable, CDN-cacheable, SDK/bot-friendly.
# Pattern mirrors wago.tools URL scheme. Avoids client-side N+1 patch fetches.
diff-endpoints:
	python3 scripts/build-diff-endpoints.py

# Generate patches/export.csv — flat CSV of all patch entries (wago.tools data export pattern).
# Universally importable: Excel, pandas, R, Google Sheets, discord.py bots.
# Source: search-index.json. Run after `make index` to reflect latest data.
csv:
	python3 scripts/build-csv-export.py

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
	@echo "--- state.json ---" && python3 -m json.tool state.json > /dev/null && echo "state.json: OK"
	@python3 -c "\
import json, sys; \
idx = json.load(open('patches/index.json')); \
base = json.load(open('state/steam-news-baseline.json')) if __import__('os').path.exists('state/steam-news-baseline.json') else {}; \
iv = idx.get('latest_version'); bv = base.get('latest_version'); \
(print(f'baseline: OK (both {iv})') if iv == bv else (print(f'ERROR: baseline drift — index={iv} but baseline={bv}; run make check-steam to sync', file=sys.stderr) or sys.exit(1))) \
if bv else print('baseline: SKIP (no baseline file yet)')"
	@python3 -c "\
with open('_headers') as f: h = f.read(); \
assert 'cdn.redoc.ly' in h, 'ERROR: cdn.redoc.ly missing from /api/ CSP in _headers — Redoc bundle will be blocked'; \
assert 'worker-src blob:' in h, 'ERROR: worker-src blob: missing from /api/ CSP in _headers — Redoc web worker will be blocked'; \
print('_headers CSP: OK (cdn.redoc.ly + worker-src blob: present)')"
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

# Read-only health status — safe for idle-loop monitoring passes.
# Reads the committed api/health.json as-is; does NOT rebuild, write, or commit anything.
# Use this in automated monitors instead of `make health` to prevent scope creep
# (i.e. automated runs modifying tracked source files without an explicit task assignment).
# Exits 0 for ok/warn, exits 1 for critical/missing.
check-monitor:
	@python3 -c "\
import json, sys, os; \
p = 'api/health.json'; \
h = json.load(open(p)) if os.path.exists(p) else {'severity': 'critical', 'message': 'api/health.json not found — run make health first'}; \
sev = h.get('severity', 'unknown'); hrs = h.get('hours_since_poll'); \
hrs_str = f'{hrs}h ago' if hrs is not None else 'unknown'; \
print(f'monitor: severity={sev} | polled={hrs_str} | {h.get(\"message\",\"\")}'); \
decision = 'No action. Monitoring continues.' if sev in ('ok', 'warn') else f'ESCALATE — severity={sev}. Run: make health check-steam'; \
print(f'DECISION: {decision}'); \
sys.exit(0 if sev in ('ok', 'warn') else 1)"

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

# Verify latest CF Pages deployment succeeded after a git push.
# Requires: CLOUDFLARE_API_TOKEN env var. Skips gracefully if token not set or CF Pages
# not yet connected (Blocker #1). Run after `git push` to confirm the fix is live.
check-deploy:
	python3 scripts/check-deploy.py

# Check state/persistent-blockers.json for time-sensitive deadlines.
# Distinct from stale-draft alerts (seen_count): this ladder fires on calendar dates.
# Exits non-zero when any deadline is critical (≤2d), urgent (≤5d), or expired.
# Writes state/deadline-status.json with per-blocker severity breakdown.
check-deadlines:
	python3 scripts/check-deadlines.py

# Dry-run self-test for the dead-window suppression logic in pull-steam-news.py.
# Imports is_in_dead_window() from the actual script (no constant duplication) and tests
# 3 boundary cases: one day inside, one day before, and the exclusive end date.
# Catches silent flag breakage before the window opens — run once after any edit to the
# DEAD_WINDOW_START/END constants or is_in_dead_window() function.
check-dead-window:
	@python3 -c "\
import importlib.util; \
spec = importlib.util.spec_from_file_location('psn', '.github/scripts/pull-steam-news.py'); \
mod = importlib.util.module_from_spec(spec); \
spec.loader.exec_module(mod); \
from datetime import datetime, timezone, timedelta; \
dw_s = datetime.fromisoformat(mod.DEAD_WINDOW_START).replace(tzinfo=timezone.utc); \
dw_e = datetime.fromisoformat(mod.DEAD_WINDOW_END).replace(tzinfo=timezone.utc); \
inside = dw_s + timedelta(days=1); before = dw_s - timedelta(days=1); \
assert mod.is_in_dead_window(inside), f'FAIL: {inside.date()} should be IN window'; \
assert not mod.is_in_dead_window(before), f'FAIL: {before.date()} should be OUTSIDE window'; \
assert not mod.is_in_dead_window(dw_e), f'FAIL: end date {dw_e.date()} is exclusive — should be OUTSIDE window'; \
print(f'check-dead-window: OK — 3/3 boundary tests passed ({mod.DEAD_WINDOW_START} → {mod.DEAD_WINDOW_END})')"

# Generate news/ namespace — announcement index, HTML listing, and Atom feed.
# Pattern: warframestat.us /news/ — announcements/roadmaps distinct from versioned patches.
# Source: patches/drafts/announcement-*.json. Run after adding new announcement drafts.
# Outputs: news/index.json, news/index.html, news/feed.xml
news:
	python3 scripts/build-news-index.py

# Generate state.json — worldstate aggregation endpoint.
# Single-fetch summary: latest patch + health + pending drafts + deadline alerts.
# Pattern: warframestat.us /pc worldstate — collapses 3 client RTTs to 1.
# Accessible at /state.json and /v1/state.json (via _redirects /v1/* rewrite).
state:
	python3 scripts/build-state.py

# Save a dated snapshot of state.json to state/history/YYYY-MM-DD.json.
# Pattern: calamity-inc/warframe-worldstate-history — auto-committed daily snapshots
# enable forensic diffing ("what changed between June 8 and July 15?").
# Idempotent: multiple runs on the same date overwrite rather than accumulate.
# Run manually or wire into the idle-loop commit step to build the history archive.
snapshot-state:
	@python3 -c "\
import json, shutil, os, datetime; \
src = 'state.json'; \
today = datetime.date.today().isoformat(); \
dst = f'state/history/{today}.json'; \
os.makedirs('state/history', exist_ok=True); \
shutil.copy(src, dst); \
print(f'snapshot-state: {dst} ✓')"

help:
	@echo "Targets:"
	@echo "  make build          — index + validate (run before any patch commit)"
	@echo "  make index          — rebuild search-index.json"
	@echo "  make validate       — validate all patches against schema"
	@echo "  make og             — generate OG preview images (requires pillow)"
	@echo "  make tags           — generate /tag/<slug>/ static pages"
	@echo "  make entities       — generate /entity/<slug>/ timeline pages (text-extracted, poedb pattern)"
	@echo "  make mirror         — generate archive/YYYY-MM-DD-vX.Y.Z.md for each patch"
	@echo "  make check          — validate sitemap.xml + JSON artifacts + baseline drift"
	@echo "  make check-baseline — assert baseline version == index latest_version (drift guard)"
	@echo "  make check-types    — validate .d.ts + openapi.json in sync with schema/patch.json"
	@echo "  make check-stats    — verify stats.json is not stale relative to its inputs"
	@echo "  make check-clean    — assert git working tree is clean (commit gate)"
	@echo "  make check-monitor  — read-only health status (idle-loop safe, no writes)"
	@echo "  make install-hooks  — install git pre-commit hook"
	@echo "  make check-steam    — poll Steam API; new_draft=true (patch) | new_announcement=true (non-semver); stamps index + baseline"
	@echo "  make check-drafts   — list unreviewed patch + announcement drafts in patches/drafts/"
	@echo "  make check-ci       — verify GH Actions cron is firing (requires gh CLI)"
	@echo "  make check-sdk      — dry-run npm pack for @spiritvale/client (pre-release gate)"
	@echo "  make check-deploy   — verify latest CF Pages deployment succeeded (requires CLOUDFLARE_API_TOKEN)"
	@echo "  make state          — generate state.json worldstate aggregation endpoint (/v1/state.json)"
	@echo "  make snapshot-state — save state/history/YYYY-MM-DD.json dated snapshot (forensics archive)"
	@echo "  make stats          — generate stats.json (cadence, change totals, top tags)"
	@echo "  make health         — generate api/health.json (structured freshness endpoint)"
	@echo "  make diff-endpoints — generate diff/v{from}...v{to}.json static endpoints"
	@echo "  make jsonld         — inject Schema.org JSON-LD into index.html + patch/index.html (SEO)"
	@echo "  make badge          — generate badge/latest.json + badge/freshness.json (shields.io endpoint badges)"
	@echo "  make check-deadlines — check state/persistent-blockers.json for calendar deadlines (distinct from stale-draft alerts)"
	@echo "  make check-dead-window — dry-run verify is_in_dead_window() boundaries (3 test cases, imports from pull-steam-news.py)"
	@echo "  make news           — build news/ namespace (index.json + index.html + feed.xml) from announcement drafts"
