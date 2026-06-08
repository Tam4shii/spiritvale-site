# SpiritVale Discord Bot — Cloudflare Workers

Zero-infrastructure Discord bot for the [SpiritVale Community Hub](https://spiritvale.tama.sh).
Runs serverless on Cloudflare Workers free tier (100k req/day, cron included).

[![Deploy to Cloudflare Workers](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/Tam4shii/spiritvale-site/tree/main/clients/discord-bot)

## Slash commands

| Command | Description |
|---|---|
| `/latest` | Latest patch embed with all change sections |
| `/patch 0.18.0` | Specific patch by version number |
| `/status` | Data freshness / patch monitor health |

## Cron behaviour

Every 5 minutes the worker fetches [`/patches/index.json`](https://spiritvale.tama.sh/patches/index.json) and compares `latest_version` to the last-known value stored in KV. When the version changes it posts an `@here` embed to `PATCH_WEBHOOK_URL`.

## Setup (5 steps)

### 1. Create a Discord bot

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications) → **New Application**
2. **Bot** tab → **Reset Token** → copy it
3. **General Info** → copy the **Public Key**
4. **OAuth2 → URL Generator** → scope: `bot` + `applications.commands`, permissions: `Send Messages` → invite to your server
5. Create a **Webhook** in the channel where patch announcements should go (Channel Settings → Integrations → Webhooks)

### 2. Create KV namespace

```bash
npx wrangler kv:namespace create STATE
# Copy the printed `id` into wrangler.toml → kv_namespaces[0].id
```

### 3. Set secrets

```bash
npx wrangler secret put DISCORD_PUBLIC_KEY   # from Discord Dev Portal → General Info
npx wrangler secret put DISCORD_BOT_TOKEN    # Bot tab → Reset Token
npx wrangler secret put PATCH_WEBHOOK_URL    # Discord channel webhook URL
```

### 4. Deploy

```bash
npm install
npm run deploy
# Prints: https://spiritvale-discord-bot.<your-subdomain>.workers.dev
```

### 5. Register slash commands

```bash
DISCORD_APP_ID=<your-app-id> DISCORD_BOT_TOKEN=<your-token> npm run register
```

Then in Discord **Dev Portal → Bot → Interactions Endpoint URL** set it to:
```
https://spiritvale-discord-bot.<your-subdomain>.workers.dev/discord
```

## Local dev

```bash
npm run dev
# Tunnel with: npx cloudflared tunnel --url http://localhost:8787
```

## Architecture

```
Discord → POST /discord → handleInteraction() → fetch spiritvale.tama.sh → embed reply
Cron (*/5 min) → checkPatch() → compare KV → fetch webhook if new version
```

Data comes entirely from the public `spiritvale.tama.sh` JSON API — no database, no backend.
The Python long-running bot in `../bots/` has more commands; this Workers bot prioritises zero-ops deployment.
