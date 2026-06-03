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

### Classic prefix commands (still supported)

| Command | Description |
|---|---|
| `!patch` | Latest patch embed |
| `!patch <version>` | Specific version, e.g. `!patch 0.17.0` |
| `!diff <from> <to>` | Cumulative changes between two versions |
| `!versions` | List all tracked versions |

> **Note**: The first time the bot starts, it calls `bot.tree.sync()` to register slash commands globally with Discord. This takes up to an hour to propagate to all servers. For instant updates in one server during testing, use guild-scoped sync — see discord.py docs.

## Files

| File | Purpose |
|---|---|
| `discord-example.py` | Bot entrypoint — import and run |
| `.env.example` | Environment variable template |
| `../spiritvale.py` | Zero-dependency API client (no extra installs) |
