# spiritvale.js — JS/TS Client SDK

Zero-dependency ES module for the SpiritVale Community Hub API.
Works in browser (native ESM) and Node ≥ 18 (native fetch).
Full TypeScript types are co-located in `spiritvale.d.ts`.

## Install

No install required — import directly from the site:

```js
// Browser or Deno — CDN import (once spiritvale.tama.sh is live)
import { getLatest } from 'https://spiritvale.tama.sh/clients/spiritvale.js';

// Node ≥ 18 (copy file locally or reference from this repo)
import { getLatest } from './clients/spiritvale.js';
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
