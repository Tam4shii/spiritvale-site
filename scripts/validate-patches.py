#!/usr/bin/env python3
"""
validate-patches.py — verifies every patches/v*.json and patches/latest.json
against schema/patch.json using the jsonschema library.

Usage:
    python3 scripts/validate-patches.py

Exit code 0 = all pass, 1 = one or more failures.

Install dep once:
    pip install jsonschema
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent

try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema not installed — run: pip install jsonschema", file=sys.stderr)
    sys.exit(1)

with open(ROOT / "schema" / "patch.json") as f:
    schema = json.load(f)

patch_files = sorted((ROOT / "patches").glob("v*.json")) + [ROOT / "patches" / "latest.json"]

results = []
for pf in patch_files:
    if not pf.exists():
        continue
    with open(pf) as f:
        data = json.load(f)
    try:
        jsonschema.validate(instance=data, schema=schema)
        results.append((pf.relative_to(ROOT), "PASS", None))
    except jsonschema.ValidationError as e:
        results.append((pf.relative_to(ROOT), "FAIL", e.message))

passed = sum(1 for _, s, _ in results if s == "PASS")
failed = len(results) - passed

for path, status, msg in results:
    mark = "✓" if status == "PASS" else "✗"
    line = f"{mark} {path}: {status}"
    if msg:
        line += f"\n    └─ {msg}"
    print(line)

print(f"\nResult: {passed}/{len(results)} passed", end="")
if failed:
    print(f", {failed} FAILED")
    sys.exit(1)
else:
    print(" — all OK")
