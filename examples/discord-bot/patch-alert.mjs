/**
 * patch-alert.mjs — SpiritVale patch watcher for Discord
 *
 * Polls the SpiritVale API and posts an embed to a Discord webhook whenever
 * a new patch lands.  Requires Node ≥18 (native fetch).  No npm install.
 *
 * Usage:
 *   DISCORD_WEBHOOK=https://discord.com/api/webhooks/ID/TOKEN node patch-alert.mjs
 *
 * Optional env vars:
 *   POLL_INTERVAL_MS   polling cadence in ms (default: 600000 = 10 min)
 */

import { getLatest } from '../../clients/spiritvale.js';

const WEBHOOK = process.env.DISCORD_WEBHOOK;
const POLL_MS = Number(process.env.POLL_INTERVAL_MS ?? 600_000);

if (!WEBHOOK) {
  console.error('Missing DISCORD_WEBHOOK env var');
  process.exit(1);
}

let seenVersion = null;

async function poll() {
  try {
    const patch = await getLatest();
    if (seenVersion === null) {
      seenVersion = patch.version;
      console.log(`[spiritvale-bot] watching from v${seenVersion}`);
      return;
    }
    if (patch.version === seenVersion) return;
    await postAlert(patch);
    seenVersion = patch.version;
  } catch (err) {
    console.error(`[spiritvale-bot] poll error: ${err.message}`);
  }
}

async function postAlert(patch) {
  const bullets = [
    ...(patch.added   ?? []).slice(0, 3).map(t => `🟢 ${t}`),
    ...(patch.changed ?? []).slice(0, 3).map(t => `🟡 ${t}`),
    ...(patch.fixed   ?? []).slice(0, 2).map(t => `🔵 ${t}`),
    ...(patch.removed ?? []).slice(0, 2).map(t => `🔴 ${t}`),
  ].slice(0, 8);

  const slug = patch.version.replace(/\./g, '-');
  const content = [
    `**SpiritVale ${patch.version} — ${patch.title}** is out!`,
    bullets.join('\n'),
    `<https://spiritvale.tama.sh/patch/${slug}>`,
  ].filter(Boolean).join('\n');

  const res = await fetch(WEBHOOK, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) console.error(`[spiritvale-bot] webhook error ${res.status}`);
  else console.log(`[spiritvale-bot] posted v${patch.version} to Discord`);
}

poll();
setInterval(poll, POLL_MS);
