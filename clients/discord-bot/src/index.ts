/**
 * SpiritVale Discord Bot — Cloudflare Workers
 *
 * Handles: Discord slash command webhook (POST /discord) + cron patch-check.
 * Deploy: wrangler deploy  |  One-click: see README deploy button.
 *
 * Slash commands: /latest  /patch <version>  /status
 * Cron (*/5 * * * *): announces new patches to PATCH_WEBHOOK_URL.
 */

const BASE = 'https://spiritvale.tama.sh';

interface Env {
  DISCORD_PUBLIC_KEY: string;
  DISCORD_BOT_TOKEN: string;
  PATCH_WEBHOOK_URL: string;
  STATE: KVNamespace; // stores last_version for cron dedup
}

// --- helpers ---

function hex(s: string): Uint8Array {
  return new Uint8Array(s.match(/.{2}/g)!.map(b => parseInt(b, 16)));
}

async function verifyRequest(req: Request, publicKey: string): Promise<boolean> {
  const sig = req.headers.get('x-signature-ed25519');
  const ts  = req.headers.get('x-signature-timestamp');
  if (!sig || !ts) return false;
  const body = await req.clone().text();
  const key = await crypto.subtle.importKey('raw', hex(publicKey), 'Ed25519', false, ['verify']);
  return crypto.subtle.verify('Ed25519', key, hex(sig), new TextEncoder().encode(ts + body));
}

async function api(path: string): Promise<any> {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`HTTP ${r.status} for ${path}`);
  return r.json();
}

function patchEmbed(patch: any, color = 0x57f287): object {
  const ICONS: Record<string, string> = { added: '🟢', changed: '🟡', fixed: '🔵', removed: '🔴' };
  const fields = Object.entries(ICONS).flatMap(([k, icon]) => {
    const list: string[] = patch[k] ?? [];
    if (!list.length) return [];
    const value = list.slice(0, 5).map(e => `${icon} ${e}`).join('\n')
      + (list.length > 5 ? `\n…+${list.length - 5} more` : '');
    return [{ name: k[0].toUpperCase() + k.slice(1), value, inline: false }];
  });
  return { title: `SpiritVale ${patch.version} — ${patch.title}`,
           url: `${BASE}/patch/?v=${patch.version}`, color, fields,
           footer: { text: 'spiritvale.tama.sh · /patch /diff /search' } };
}

// --- cron: post to webhook when latest_version changes ---

async function checkPatch(env: Env): Promise<void> {
  const idx     = await api('/patches/index.json');
  const current = idx.latest_version as string;
  const last    = await env.STATE.get('last_version');
  if (last === current) return;
  const patch = await api('/patches/latest.json');
  await fetch(env.PATCH_WEBHOOK_URL, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ content: '@here **New SpiritVale patch!**',
                           embeds: [patchEmbed(patch, 0xfaa61a)] }),
  });
  await env.STATE.put('last_version', current);
}

// --- slash command handler ---

async function handleInteraction(req: Request, env: Env): Promise<Response> {
  if (!(await verifyRequest(req, env.DISCORD_PUBLIC_KEY)))
    return new Response('Unauthorized', { status: 401 });

  const body: any = await req.json();
  if (body.type === 1) return Response.json({ type: 1 }); // PING → PONG

  const name: string = body.data?.name ?? '';
  try {
    if (name === 'latest') {
      const patch = await api('/patches/latest.json');
      return Response.json({ type: 4, data: { embeds: [patchEmbed(patch)] } });
    }
    if (name === 'patch') {
      const version: string = body.data.options?.[0]?.value ?? '';
      const patch = await api(`/patches/v${version}.json`);
      return Response.json({ type: 4, data: { embeds: [patchEmbed(patch)] } });
    }
    if (name === 'status') {
      const h = await api('/api/health.json');
      const color: number = ({ ok: 0x57f287, warn: 0xfaa61a, critical: 0xed4245 } as any)[h.severity] ?? 0x99aab5;
      return Response.json({ type: 4, data: { embeds: [{ title: `SpiritVale — ${String(h.severity).toUpperCase()}`,
        description: h.message ?? '', color, footer: { text: `${BASE}/api/health.json` },
        fields: [{ name: 'Latest', value: h.latest_version ?? '—', inline: true },
                 { name: 'Patches', value: String(h.total_patches ?? '—'), inline: true },
                 { name: 'Last polled', value: h.hours_since_poll != null ? `${h.hours_since_poll}h ago` : 'unknown', inline: true }] }] } });
    }
    return Response.json({ type: 4, data: { content: `Unknown command: ${name}`, flags: 64 } });
  } catch (err) {
    return Response.json({ type: 4, data: { content: `❌ ${err}`, flags: 64 } });
  }
}

// --- Worker entrypoint ---

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    if (req.method === 'POST' && new URL(req.url).pathname === '/discord')
      return handleInteraction(req, env);
    return new Response('SpiritVale Bot · POST /discord for interactions', { status: 200 });
  },
  async scheduled(_event: ScheduledEvent, env: Env): Promise<void> {
    await checkPatch(env);
  },
} satisfies ExportedHandler<Env>;
