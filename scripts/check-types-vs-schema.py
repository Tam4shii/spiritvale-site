#!/usr/bin/env python3
"""
check-types-vs-schema.py — validate clients/spiritvale.d.ts is in sync with schema sources.

Checks:
  1. SearchEntry.type union in .d.ts contains all category keys present in openapi.json enum
  2. DiffResult fields in .d.ts cover all category keys from schema/patch.json

Run via: make check-types
Exit 0 = in sync. Exit 1 = drift detected (with explanation).
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
DTS  = ROOT / "clients" / "spiritvale.d.ts"
OPENAPI = ROOT / "openapi.json"
SCHEMA  = ROOT / "schema" / "patch.json"

# Category keys that getDiff and SearchEntry must cover
SCHEMA_CATEGORIES = {"added", "changed", "fixed", "removed", "deprecated", "security"}

errors = []

# --- 1. openapi.json SearchEntry.type enum ---
with open(OPENAPI) as f:
    openapi = json.load(f)

search_entry = openapi["components"]["schemas"]["SearchEntry"]["properties"]["type"]
openapi_enum = set(search_entry.get("enum", []))
missing_openapi = SCHEMA_CATEGORIES - openapi_enum
if missing_openapi:
    errors.append(f"openapi.json SearchEntry.type enum missing: {sorted(missing_openapi)}")

# --- 2. .d.ts SearchEntry.type union ---
dts = DTS.read_text()

m = re.search(r'type:\s*([^;]+);', dts)
if not m:
    errors.append(".d.ts: could not find SearchEntry.type union")
else:
    union_str = m.group(1)
    quoted = set(re.findall(r'"([^"]+)"', union_str))
    missing_dts = SCHEMA_CATEGORIES - quoted
    if missing_dts:
        errors.append(f".d.ts SearchEntry.type union missing: {sorted(missing_dts)}")

# --- 3. .d.ts DiffResult fields ---
with open(SCHEMA) as f:
    schema = json.load(f)

# Categories are optional array properties in schema/patch.json
schema_cats = {k for k, v in schema["properties"].items()
               if v.get("type") == "array" and k in SCHEMA_CATEGORIES}

diff_block_m = re.search(r'interface DiffResult \{(.+?)\}', dts, re.DOTALL)
if not diff_block_m:
    errors.append(".d.ts: could not find DiffResult interface")
else:
    diff_body = diff_block_m.group(1)
    declared = set(re.findall(r'^\s+(\w+)\??\s*:', diff_body, re.MULTILINE))
    missing_diff = schema_cats - declared
    if missing_diff:
        errors.append(f".d.ts DiffResult missing fields: {sorted(missing_diff)}")

if errors:
    print("check-types-vs-schema: DRIFT DETECTED")
    for e in errors:
        print(f"  ✗ {e}")
    print("\nFix: update clients/spiritvale.d.ts and openapi.json to match schema/patch.json")
    sys.exit(1)
else:
    print("check-types-vs-schema: OK — .d.ts and openapi.json in sync with schema")
