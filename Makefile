.PHONY: build index validate og install-hooks check-steam help

# Regenerate all derived artifacts (run before committing a new patch).
build: index validate

# Rebuild search-index.json from patches/v*.json.
# MUST run whenever a patch file is added or modified.
index:
	python3 scripts/build-search-index.py

# Validate all patch files against schema/patch.json.
validate:
	python3 scripts/validate-patches.py

# Generate per-patch OG social-preview images to og/*.png.
# Run: make og  (requires: pip install pillow)
og:
	python3 scripts/build-og-images.py

# Check Steam AppNews for new patch notes (mirrors what GH Actions runs daily).
check-steam:
	python3 .github/scripts/pull-steam-news.py

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
	@echo "  make install-hooks — install git pre-commit hook"
	@echo "  make check-steam   — check Steam API for new patch notes (local dry-run)"
