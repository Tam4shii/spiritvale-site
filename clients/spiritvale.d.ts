/**
 * spiritvale.d.ts — TypeScript declarations for spiritvale.js
 *
 * Usage (TypeScript resolves this file automatically from spiritvale.js):
 *   import { getLatest } from './spiritvale.js';
 *   import type { PatchNote, PatchIndex } from './spiritvale.js';
 */

/** A single classified change entry within getDiff results */
export interface DiffEntry {
  text: string;
  /** Version string in which this change appeared, e.g. "0.17.0" */
  _version: string;
}

/** Return value of getDiff — cumulative changes across a version range */
export interface DiffResult {
  added: DiffEntry[];
  changed: DiffEntry[];
  fixed: DiffEntry[];
  removed: DiffEntry[];
  /** Present when patches in the range have deprecated entries */
  deprecated?: DiffEntry[];
  /** Present when patches in the range have security entries */
  security?: DiffEntry[];
}

/** Counts of change entries in a patch, as stored in PatchIndex */
export interface ChangeCounts {
  added: number;
  changed: number;
  fixed: number;
  removed: number;
}

/** One entry in PatchIndex.versions */
export interface PatchVersionEntry {
  version: string;
  title: string;
  /** YYYY-MM-DD */
  date: string;
  current?: boolean;
  archive_url: string;
  steam_news_id?: string;
  change_counts: ChangeCounts;
}

/** Shape of /patches/index.json */
export interface PatchIndex {
  latest_version: string;
  last_polled_at: string | null;
  /** Always "UTC" — timestamps in this index are UTC */
  poll_tz: "UTC";
  versions: PatchVersionEntry[];
}

/** Shape of /patches/v*.json and /patches/latest.json */
export interface PatchNote {
  $schema?: string;
  version: string;
  title: string;
  /** YYYY-MM-DD */
  date: string;
  current?: boolean;
  url: string | null;
  added: string[];
  changed: string[];
  fixed: string[];
  removed: string[];
  deprecated?: string[];
  security?: string[];
  steam_news_id?: string;
  steam_url?: string | null;
  released_at?: string;
  /** Systems, classes, or content areas affected — e.g. ['Paladin', 'crafting', 'UI'] */
  affects?: string[];
  breaking?: boolean;
  /** Only present in auto-generated drafts — remove before merging */
  raw_body?: string;
}

/** One entry in SearchIndex.entries */
export interface SearchEntry {
  id: string;
  version: string;
  patch_title: string;
  /** YYYY-MM-DD */
  date: string;
  type: "added" | "changed" | "fixed" | "removed" | "deprecated" | "security";
  text: string;
  tags: string[];
  url: string;
}

/** Shape of /search-index.json */
export interface SearchIndex {
  patch_count: number;
  entries: SearchEntry[];
}

/** A known game lifecycle milestone (demo, early-access, etc.) */
export interface Milestone {
  key: string;
  label: string;
  /** YYYY-MM-DD */
  date: string;
  phase: "playtest-end" | "demo" | "early-access" | "full-release";
  /** Present for monetised milestones */
  price_usd?: number;
  days_until: number;
  past: boolean;
}

/** Shape of /state.json — worldstate aggregation endpoint */
export interface WorldState {
  generated_at: string;
  latest_version: string;
  last_polled_at: string | null;
  poll_tz: "UTC";
  latest: {
    version: string;
    title: string;
    date: string;
    change_counts: ChangeCounts;
    archive_url: string;
    steam_news_id?: string;
  } | null;
  index_summary: { total_versions: number; items_found: number };
  health: {
    severity: "ok" | "warn" | "critical";
    stale: boolean;
    hours_since_poll: number;
    message: string;
    steam_baseline_match: boolean;
  };
  stats_summary: {
    total_patches: number;
    total_entries: number;
    change_totals: ChangeCounts;
    avg_days_between_patches: number;
  };
  pending_drafts: Array<{ filename: string; seen_count: number; first_seen_at: string; last_seen_at: string; alerted_at?: string }>;
  pending_drafts_count: number;
  deadline_alerts: Array<{ key: string; description: string; deadline: string; days_until: number; severity: string }>;
  worst_deadline_severity: string | null;
  milestones: Milestone[];
  upcoming_milestones: Milestone[];
  next_milestone: Milestone | null;
  _links: Record<string, string>;
}

/** Latest patch note (patches/latest.json) */
export function getLatest(): Promise<PatchNote>;

/** Full patch index (patches/index.json) — version list + last_polled_at */
export function getIndex(): Promise<PatchIndex>;

/**
 * Single patch by version string.
 * @param version  e.g. "0.17.0"
 */
export function getPatch(version: string): Promise<PatchNote>;

/** Flat search index (all bullet entries across all patches) */
export function getSearchIndex(): Promise<SearchIndex>;

/**
 * Worldstate aggregation endpoint — single fetch gives latest patch, health,
 * pending drafts, deadline alerts, stats, and upcoming game milestones.
 * Equivalent to warframestat.us /pc worldstate.
 */
export function getState(): Promise<WorldState>;

/**
 * Compute a cumulative diff between two versions.
 * Returns change entries for all versions strictly after fromVersion up to and including toVersion.
 * Each entry includes a _version annotation for per-patch badge rendering.
 *
 * @param fromVersion  base version, e.g. "0.13.0"
 * @param toVersion    target version, e.g. "0.17.0"
 * @remarks fromVersion must be chronologically earlier than toVersion; reversed order throws "unknown version".
 */
export function getDiff(fromVersion: string, toVersion: string): Promise<DiffResult>;
