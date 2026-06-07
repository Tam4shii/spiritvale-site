# spiritvale.js — JS/TS Client SDK

[![npm](https://img.shields.io/npm/v/@spiritvale/client)](https://www.npmjs.com/package/@spiritvale/client)

Zero-dependency ES module for the SpiritVale Community Hub API.
Works in browser (native ESM) and Node ≥ 18 (native fetch).
Full TypeScript types are co-located in `spiritvale.d.ts`.

## Install

```bash
# npm / pnpm / yarn
npm install @spiritvale/client
```

Or import directly from the site (no install):

```js
// Browser / Deno — CDN import
import { getLatest } from 'https://spiritvale.tama.sh/clients/spiritvale.js';

// Node ≥ 18 — after npm install
import { getLatest } from '@spiritvale/client';
```

## Functions

| Function | Returns | Description |
|---|---|---|
| `getLatest()` | `Promise<PatchNote>` | Latest patch note (`/patches/latest.json`) |
| `getIndex()` | `Promise<PatchIndex>` | Version list + poll metadata (`/patches/index.json`) |
| `getPatch(version)` | `Promise<PatchNote>` | Single patch by version string, e.g. `"0.17.0"` |
| `getSearchIndex()` | `Promise<SearchIndex>` | All 182+ classified bullet entries (`/search-index.json`) |
| `getDiff(from, to)` | `Promise<DiffResult>` | Cumulative change diff across a version range |

## Usage examples

### Show the latest patch

```js
import { getLatest } from 'https://spiritvale.tama.sh/clients/spiritvale.js';

const patch = await getLatest();
console.log(`${patch.version} — ${patch.title}`);
console.log(`Added: ${patch.added.length}, Changed: ${patch.changed.length}`);
```

### List all versions

```js
import { getIndex } from 'https://spiritvale.tama.sh/clients/spiritvale.js';

const index = await getIndex();
for (const v of index.versions) {
  console.log(`${v.version}  ${v.title}  (${v.date})`);
}
```

### Diff between two versions

```js
import { getDiff } from 'https://spiritvale.tama.sh/clients/spiritvale.js';

const diff = await getDiff('0.13.0', '0.17.0');
console.log(`${diff.added.length} added, ${diff.changed.length} changed`);
for (const entry of diff.added) {
  console.log(`  [${entry._version}] ${entry.text}`);
}
```

### Search all bullets

```js
import { getSearchIndex } from 'https://spiritvale.tama.sh/clients/spiritvale.js';

const index = await getSearchIndex();
const shinobi = index.entries.filter(e => e.tags.includes('shinobi'));
console.log(`${shinobi.length} Shinobi-related changes`);
```

## TypeScript

`spiritvale.d.ts` is auto-resolved by TypeScript when you import `spiritvale.js`.
Key types exported:

```ts
import type {
  PatchNote,        // /patches/v*.json shape
  PatchIndex,       // /patches/index.json shape
  PatchVersionEntry,
  SearchIndex,
  SearchEntry,
  DiffResult,
  DiffEntry,
} from './spiritvale.js';
```

## Error handling

All functions throw on non-2xx HTTP responses:

```js
try {
  const patch = await getPatch('99.0.0'); // doesn't exist
} catch (err) {
  console.error(err.message); // "spiritvale: HTTP 404 for /patches/v99.0.0.json"
}
```

## CORS

All endpoints on `spiritvale.tama.sh` respond with `Access-Control-Allow-Origin: *`.
No proxy needed — call directly from browser context.

---

# spiritvale.py — Python Client SDK

Zero-dependency Python module (stdlib `urllib.request` only). Works on Python ≥ 3.8.

## Install

No install required — copy `clients/spiritvale.py` into your project:

```bash
curl -O https://spiritvale.tama.sh/clients/spiritvale.py
```

## Functions

| Function | Returns | Description |
|---|---|---|
| `get_latest()` | `dict` | Latest patch note (`/patches/latest.json`) |
| `get_index()` | `dict` | Version list + poll metadata (`/patches/index.json`) |
| `get_patch(version)` | `dict` | Single patch by version string, e.g. `"0.17.0"` |
| `get_search_index()` | `dict` | All classified bullet entries (`/search-index.json`) |
| `get_diff(from, to)` | `dict` | Cumulative change diff across a version range |

## Usage examples

### Show the latest patch

```python
from spiritvale import get_latest

patch = get_latest()
print(f"{patch['version']} — {patch['title']}")
print(f"Added: {len(patch['added'])}, Changed: {len(patch['changed'])}")
```

### List all versions

```python
from spiritvale import get_index

index = get_index()
for v in index['versions']:
    print(f"{v['version']}  {v['title']}  ({v['date']})")
```

### Diff between two versions

```python
from spiritvale import get_diff

diff = get_diff('0.13.0', '0.17.0')
print(f"{len(diff['added'])} added, {len(diff['changed'])} changed")
for entry in diff['added']:
    print(f"  [{entry['_version']}] {entry['text']}")
```

### Search all bullets

```python
from spiritvale import get_search_index

index = get_search_index()
shinobi = [e for e in index['entries'] if 'shinobi' in e.get('tags', [])]
print(f"{len(shinobi)} Shinobi-related changes")
```

## Error handling

Functions raise `urllib.error.HTTPError` on non-2xx responses:

```python
from urllib.error import HTTPError
from spiritvale import get_patch

try:
    patch = get_patch('99.0.0')  # doesn't exist
except HTTPError as e:
    print(e.code)  # 404
```

---

# Discord Bot Example

`clients/bots/discord-example.py` is a ready-to-fork Discord bot built on the Python SDK above.

## Requirements

```bash
pip install discord.py
```

## Commands

| Command | Description |
|---|---|
| `!patch` | Embed showing the latest patch summary |
| `!patch <version>` | Embed for a specific version, e.g. `!patch 0.17.0` |
| `!diff <from> <to>` | Cumulative changes between two versions |
| `!versions` | List all tracked patch versions |

## Run

```bash
export DISCORD_BOT_TOKEN=your_token_here
python clients/bots/discord-example.py
```

The bot imports `spiritvale.py` from the parent directory — no additional configuration needed.
