"""
discord-example.py — SpiritVale patch bot with slash commands

Uses the zero-dependency spiritvale.py SDK (no extra HTTP clients needed).

Slash commands (modern Discord UX — autocompletes in the input bar):
    /latest              — latest patch embed
    /patch version       — specific version, e.g. /patch 0.17.0
    /diff from to        — cumulative changes between two versions
    /search query        — search patch entries by keyword

Classic prefix commands (still work for power users and DM contexts):
    !patch [version]     — show latest or specific patch
    !diff <v1> <v2>      — cumulative diff
    !versions            — list all tracked versions

Requirements:
    pip install -r clients/bots/requirements.txt

Setup:
    1. Create a bot at https://discord.com/developers/applications
    2. Bot tab → Reset Token → copy token → paste into .env
    3. Privileged Gateway Intents → enable Message Content Intent
    4. OAuth2 → URL Generator → scope: bot + applications.commands, perm: Send Messages
    5. Run:
         cp clients/bots/.env.example clients/bots/.env
         python clients/bots/discord-example.py
"""

import os
import sys

# Allow running from the repo root or from clients/bots/
_bot_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_bot_dir, ".."))

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_bot_dir, ".env"))
except ImportError:
    pass

import discord
from discord import app_commands
from discord.ext import commands, tasks

from spiritvale import get_bot_json, get_diff, get_health, get_index, get_latest, get_patch, get_search_index

ANNOUNCE_CHANNEL_ID = int(os.getenv("SPIRITVALE_CHANNEL_ID", "0"))

BADGES = {
    "added": "🟢",
    "changed": "🟡",
    "fixed": "🔵",
    "removed": "🔴",
    "deprecated": "⚠️",
    "security": "🔒",
}

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


def _patch_embed(patch: dict) -> discord.Embed:
    embed = discord.Embed(
        title=f"SpiritVale {patch['version']} — {patch['title']}",
        url=f"https://spiritvale.tama.sh/patch/?v={patch['version']}",
        color=0x57F287,
    )
    for key, badge in BADGES.items():
        entries = patch.get(key) or []
        if not entries:
            continue
        lines = [f"{badge} {e}" for e in entries[:5]]
        if len(entries) > 5:
            lines.append(f"…and {len(entries) - 5} more")
        embed.add_field(name=key.capitalize(), value="\n".join(lines), inline=False)
    embed.set_footer(text="spiritvale.tama.sh · /patch /diff /search")
    return embed


_last_known_version: str | None = None


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    # Sync slash commands globally. In production, prefer setup_hook() or a
    # one-time sync script to avoid Discord rate limits on every restart.
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
    except Exception as exc:
        print(f"[sync] error: {exc}")
    if ANNOUNCE_CHANNEL_ID:
        poll_new_patch.start()


@tasks.loop(minutes=5)
async def poll_new_patch():
    global _last_known_version
    try:
        index = get_index()
        current = index["latest_version"]
        if _last_known_version is None:
            _last_known_version = current
            return
        if current != _last_known_version:
            channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
            if channel:
                patch = get_latest()
                embed = _patch_embed(patch)
                embed.color = 0xFAA61A
                await channel.send(content="@here **New SpiritVale patch!**", embed=embed)
            _last_known_version = current
    except Exception as exc:
        print(f"[poll] error: {exc}")


# ── Slash commands ──────────────────────────────────────────────────────────

@bot.tree.command(name="latest", description="Show the latest SpiritVale patch")
async def latest_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        # Use pre-formatted embed from bot.json (tarkov.dev reference bot pattern) —
        # avoids rebuilding the embed from raw patch data on every invocation.
        bot_data = get_bot_json()
        raw = bot_data["latest"]["embed"]
        # bot.json uses thumbnail_url (flat); discord.Embed.from_dict expects {thumbnail: {url}}
        embed_dict = {k: v for k, v in raw.items() if k != "thumbnail_url"}
        if raw.get("thumbnail_url"):
            embed_dict["thumbnail"] = {"url": raw["thumbnail_url"]}
        embed = discord.Embed.from_dict(embed_dict)
        await interaction.followup.send(embed=embed)
    except Exception:
        # Fallback: build embed from raw patch data if bot.json is unavailable or malformed
        data = get_latest()
        await interaction.followup.send(embed=_patch_embed(data))


@bot.tree.command(name="patch", description="Show a specific SpiritVale patch by version")
@app_commands.describe(version="Version number, e.g. 0.17.0")
async def patch_slash(interaction: discord.Interaction, version: str):
    await interaction.response.defer()
    try:
        data = get_patch(version)
        await interaction.followup.send(embed=_patch_embed(data))
    except Exception as exc:
        await interaction.followup.send(f"❌ {exc}", ephemeral=True)


@bot.tree.command(name="diff", description="Cumulative changes between two SpiritVale versions")
@app_commands.describe(from_ver="Starting version, e.g. 0.13.0", to_ver="Ending version, e.g. 0.18.0")
async def diff_slash(interaction: discord.Interaction, from_ver: str, to_ver: str):
    await interaction.response.defer()
    try:
        result = get_diff(from_ver, to_ver)
        total = sum(len(v) for v in result.values())
        lines = [f"**SpiritVale {from_ver} → {to_ver}** ({total} changes)\n"]
        for key, badge in BADGES.items():
            entries = result.get(key) or []
            if not entries:
                continue
            lines.append(f"{badge} **{key.capitalize()}** ({len(entries)})")
            for e in entries[:4]:
                lines.append(f"  • [{e['_version']}] {e['text']}")
            if len(entries) > 4:
                lines.append(f"  …and {len(entries) - 4} more")
        await interaction.followup.send("\n".join(lines)[:2000])
    except Exception as exc:
        await interaction.followup.send(f"❌ {exc}", ephemeral=True)


@bot.tree.command(name="search", description="Search SpiritVale patch entries by keyword")
@app_commands.describe(query="Keyword to search for, e.g. 'shinobi' or 'stamina'")
async def search_slash(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    try:
        index = get_search_index()
        entries = index.get("entries") or []
        q = query.lower()
        hits = [e for e in entries if q in e.get("text", "").lower()]
        if not hits:
            await interaction.followup.send(f"No results for **{query}**", ephemeral=True)
            return
        lines = [f"**Search: \"{query}\"** — {len(hits)} result(s)\n"]
        for e in hits[:8]:
            badge = BADGES.get(e.get("type", ""), "•")
            lines.append(f"{badge} [{e['version']}] {e['text']}")
        if len(hits) > 8:
            lines.append(f"\n…and {len(hits) - 8} more · [full search](https://spiritvale.tama.sh/search/?q={query})")
        await interaction.followup.send("\n".join(lines)[:2000])
    except Exception as exc:
        await interaction.followup.send(f"❌ {exc}", ephemeral=True)


@bot.tree.command(name="status", description="Show SpiritVale patch monitor health (data freshness)")
async def status_slash(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        h = get_health()
        severity = h.get("severity", "unknown")
        color = {"ok": 0x57F287, "warn": 0xFAA61A, "critical": 0xED4245}.get(severity, 0x99AAB5)
        hours = h.get("hours_since_poll")
        hours_str = f"{hours}h ago" if hours is not None else "unknown"
        embed = discord.Embed(
            title=f"SpiritVale Monitor — {severity.upper()}",
            description=h.get("message", ""),
            color=color,
        )
        embed.add_field(name="Latest", value=h.get("latest_version") or "—", inline=True)
        embed.add_field(name="Patches", value=str(h.get("total_patches") or "—"), inline=True)
        embed.add_field(name="Last polled", value=hours_str, inline=True)
        embed.set_footer(text="spiritvale.tama.sh/api/health.json")
        await interaction.followup.send(embed=embed)
    except Exception as exc:
        await interaction.followup.send(f"❌ {exc}", ephemeral=True)


# ── Classic prefix commands (backwards-compatible) ──────────────────────────

@bot.command(name="patch")
async def patch_cmd(ctx, version: str = None):
    """Show patch summary. Usage: !patch  or  !patch 0.17.0"""
    try:
        data = get_patch(version) if version else get_latest()
        await ctx.send(embed=_patch_embed(data))
    except Exception as exc:
        await ctx.send(f"❌ {exc}")


@bot.command(name="diff")
async def diff_cmd(ctx, from_ver: str, to_ver: str):
    """Show cumulative changes between versions. Usage: !diff 0.13.0 0.17.0"""
    try:
        result = get_diff(from_ver, to_ver)
        total = sum(len(v) for v in result.values())
        lines = [f"**SpiritVale {from_ver} → {to_ver}** ({total} changes)\n"]
        for key, badge in BADGES.items():
            entries = result.get(key) or []
            if not entries:
                continue
            lines.append(f"{badge} **{key.capitalize()}** ({len(entries)})")
            for e in entries[:4]:
                lines.append(f"  • [{e['_version']}] {e['text']}")
            if len(entries) > 4:
                lines.append(f"  …and {len(entries) - 4} more")
        await ctx.send("\n".join(lines)[:2000])
    except Exception as exc:
        await ctx.send(f"❌ {exc}")


@bot.command(name="versions")
async def versions_cmd(ctx):
    """List all tracked patch versions. Usage: !versions"""
    try:
        index = get_index()
        lines = ["**SpiritVale patch history**"]
        for v in index["versions"][:12]:
            lines.append(f"  `{v['version']}` — {v['title']} ({v['date']})")
        remaining = len(index["versions"]) - 12
        if remaining > 0:
            lines.append(f"  …and {remaining} more · spiritvale.tama.sh")
        await ctx.send("\n".join(lines))
    except Exception as exc:
        await ctx.send(f"❌ {exc}")


if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("Error: DISCORD_BOT_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)
    bot.run(token)
