/**
 * spiritvale.d.ts — TypeScript declarations for spiritvale.js
 *
 * Usage:
 *   import type { PatchNote, PatchIndex } from './spiritvale.d.ts';
 *
 * Or alongside the JS module:
 *   import { getLatest } from './spiritvale.js';
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
  type: "added" | "changed" | "fixed" | "removed";
  text: string;
  tags: string[];
  url: string;
}

/** Shape of /search-index.json */
export interface SearchIndex {
  patch_count: number;
  entries: SearchEntry[];
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
 * Compute a cumulative diff between two versions.
 * Returns change entries for all versions strictly after fromVersion up to and including toVersion.
 * Each entry includes a _version annotation for per-patch badge rendering.
 *
 * @param fromVersion  base version, e.g. "0.13.0"
 * @param toVersion    target version, e.g. "0.17.0"
 */
export function getDiff(fromVersion: string, toVersion: string): Promise<DiffResult>;
