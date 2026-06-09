/**
 * spiritvale.js — zero-dependency JS client for the SpiritVale Community Hub API
 *
 * Usage (browser or Node ≥18):
 *   import { getLatest, getIndex, getPatch, getDiff } from './spiritvale.js';
 *
 * Or from CDN (once site is live):
 *   import { getLatest } from 'https://spiritvale.tama.sh/clients/spiritvale.js';
 *
 * All functions return Promises. Throws on non-2xx responses.
 * CORS is open on the origin — no proxy needed.
 */

const BASE = 'https://spiritvale.tama.sh';

async function _get(path) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`spiritvale: HTTP ${r.status} for ${path}`);
  return r.json();
}

/** Latest patch note (latest.json) */
export function getLatest() {
  return _get('/patches/latest.json');
}

/** Full patch index (index.json) — version list + last_polled_at */
export function getIndex() {
  return _get('/patches/index.json');
}

/**
 * Single patch by version string.
 * @param {string} version  e.g. "0.17.0"
 */
export function getPatch(version) {
  return _get(`/patches/v${version}.json`);
}

/** Flat search index (all bullet entries across all patches) */
export function getSearchIndex() {
  return _get('/search-index.json');
}

/**
 * Worldstate aggregation endpoint — single fetch gives latest patch, health,
 * pending drafts, deadline alerts, stats, and upcoming game milestones.
 * Equivalent to warframestat.us /pc worldstate.
 */
export function getState() {
  return _get('/state.json');
}

/**
 * Compute a cumulative diff between two versions using the public index.
 * Returns { added, changed, fixed, removed } arrays where each entry carries
 * a `_version` annotation so callers can render per-version badges.
 *
 * @param {string} fromVersion  e.g. "0.13.0"
 * @param {string} toVersion    e.g. "0.17.0"
 */
export async function getDiff(fromVersion, toVersion) {
  const index = await getIndex();
  const versions = index.versions.map(v => v.version);
  const fromIdx = versions.indexOf(fromVersion);
  const toIdx   = versions.indexOf(toVersion);
  if (fromIdx === -1 || toIdx === -1) throw new Error('spiritvale: unknown version in getDiff');

  // index is newest-first; slice from toIdx to fromIdx (exclusive upper bound)
  const slice = versions.slice(toIdx, fromIdx).reverse();
  const CHANGE_KEYS = ['added', 'changed', 'fixed', 'removed', 'deprecated', 'security'];
  const result = Object.fromEntries(CHANGE_KEYS.map(k => [k, []]));

  for (const v of slice) {
    const patch = await getPatch(v);
    for (const key of CHANGE_KEYS) {
      for (const entry of patch[key] ?? []) {
        result[key].push({ text: entry, _version: v });
      }
    }
  }
  return result;
}
