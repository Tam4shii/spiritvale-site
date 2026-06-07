# SpiritVale Discord Bot

Minimal Discord bot built on `clients/spiritvale.py`. Mirrors the warframestat.us
community-on-ramp pattern: one file, no database, zero server cost.

## Quick start

```bash
pip install discord.py python-dotenv
cp .env.example .env
# Edit .env — paste your DISCORD_BOT_TOKEN
python clients/bots/discord-example.py
```

## Bot setup (one-time)

1. Go to <https://discord.com/developers/applications> → **New Application**
2. **Bot** tab → **Reset Token** → copy the token → paste into `.env`
3. **Privileged Gateway Intents** → enable **Message Content Intent**
4. **OAuth2 → URL Generator** → scope `bot`, permission `Send Messages` → invite to your server

## Commands

### Slash commands (modern — appear in Discord's autocomplete)

| Command | Description |
|---|---|
| `/latest` | Latest patch embed |
| `/patch version:0.17.0` | Specific version |
| `/diff from:0.13.0 to:0.18.0` | Cumulative changes between two versions |
| `/search query:shinobi` | Search all patch entries by keyword |
| `/status` | Poll-monitor health card — severity, hours since last Steam check, patch count |

### Classic prefix commands (still supported)

| Command | Description |
|---|---|
| `!patch` | Latest patch embed |
| `!patch <version>` | Specific version, e.g. `!patch 0.17.0` |
| `!diff <from> <to>` | Cumulative changes between two versions |
| `!versions` | List all tracked versions |

> **Note**: The first time the bot starts, it calls `bot.tree.sync()` to register slash commands globally with Discord. This takes up to an hour to propagate to all servers. For instant updates in one server during testing, use guild-scoped sync — see discord.py docs.

## Deploy (free hosting)

The bot has no database and makes only outbound HTTPS calls to `spiritvale.tama.sh`,
so any free-tier platform that can run a Python process works.

### Railway

```bash
# One-time: install Railway CLI
npm install -g @railway/cli

# From repo root:
railway login
railway init          # follow prompts → new project
railway vars set DISCORD_BOT_TOKEN=<your_token>
railway vars set SPIRITVALE_CHANNEL_ID=<channel_id>   # optional
railway up --service spiritvale-bot
```

Railway detects the `Procfile` in this directory and runs `worker: python discord-example.py`.
Add-on cost: $0 on Hobby plan (500 free hours/month).

### Fly.io

```bash
# One-time: install flyctl
curl -L https://fly.io/install.sh | sh

# From clients/bots/:
fly launch --name spiritvale-bot --no-deploy
fly secrets set DISCORD_BOT_TOKEN=<your_token>
fly secrets set SPIRITVALE_CHANNEL_ID=<channel_id>    # optional
fly deploy
```

Fly.io runs the bot as a persistent VM; free tier (shared-cpu-1x, 256 MB) is enough.
Use `fly logs` to tail output.

## Files

| File | Purpose |
|---|---|
| `discord-example.py` | Bot entrypoint — import and run |
| `.env.example` | Environment variable template |
| `Procfile` | Process declaration for Railway / Heroku-style platforms |
| `../spiritvale.py` | Zero-dependency API client (no extra installs) |
