.PHONY: build index tags validate mirror stats health check check-ci check-types check-stats og install-hooks check-steam help

# Regenerate all derived artifacts (run before committing a new patch).
build: index tags validate mirror stats health

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

# Generate api/health.json — structured freshness endpoint.
# Derives stale/warn/critical from stats.json last_polled_at.
# Consumable by Grafana, uptime monitors, Discord bots without client-side math.
health:
	python3 scripts/build-health.py

# Validate XML and JSON derived artifacts for crawler correctness.
check:
	@echo "--- sitemap.xml ---" && xmllint --noout sitemap.xml && echo "sitemap.xml: OK"
	@echo "--- tag/index.json ---" && python3 -m json.tool tag/index.json > /dev/null && echo "tag/index.json: OK"
	@echo "--- patches/index.json ---" && python3 -m json.tool patches/index.json > /dev/null && echo "patches/index.json: OK"
	@echo "--- search-index.json ---" && python3 -m json.tool search-index.json > /dev/null && echo "search-index.json: OK"
	@echo "--- feed.json ---" && python3 -m json.tool feed.json > /dev/null && echo "feed.json: OK"
	@echo "--- feed.xml ---" && xmllint --noout feed.xml && echo "feed.xml: OK"
	@echo "--- stats.json ---" && python3 -m json.tool stats.json > /dev/null && echo "stats.json: OK"
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

help:
	@echo "Targets:"
	@echo "  make build         — index + validate (run before any patch commit)"
	@echo "  make index         — rebuild search-index.json"
	@echo "  make validate      — validate all patches against schema"
	@echo "  make og            — generate OG preview images (requires pillow)"
	@echo "  make tags          — generate /tag/<slug>/ static pages"
	@echo "  make mirror        — generate archive/YYYY-MM-DD-vX.Y.Z.md for each patch"
	@echo "  make check         — validate sitemap.xml + JSON artifacts (xmllint + json.tool)"
	@echo "  make check-types   — validate .d.ts + openapi.json in sync with schema/patch.json"
	@echo "  make check-stats   — verify stats.json is not stale relative to its inputs"
	@echo "  make install-hooks — install git pre-commit hook"
	@echo "  make check-steam   — check Steam API for new patch notes (local dry-run)"
	@echo "  make check-ci      — verify GH Actions cron is firing (requires gh CLI)"
	@echo "  make stats         — generate stats.json (cadence, change totals, top tags)"
	@echo "  make health        — generate api/health.json (structured freshness endpoint)"
