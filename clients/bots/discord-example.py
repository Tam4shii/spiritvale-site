"""
discord-example.py — minimal SpiritVale patch bot

Uses the zero-dependency spiritvale.py SDK (no extra HTTP clients needed).

Commands:
    !patch           — show latest patch summary
    !patch <version> — show a specific version, e.g. !patch 0.17.0
    !diff <v1> <v2>  — cumulative changes between two versions
    !versions        — list all tracked patch versions

Requirements:
    pip install discord.py

Setup:
    1. Create a bot at https://discord.com/developers/applications
    2. Copy the bot token
    3. Invite the bot to your server (Message Content Intent required)
    4. Run:
         export DISCORD_BOT_TOKEN=your_token_here
         python clients/bots/discord-example.py
"""

import os
import sys

# Allow running from the repo root or from clients/bots/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import discord
from discord.ext import commands

from spiritvale import get_diff, get_index, get_latest, get_patch

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
    embed.set_footer(text="spiritvale.tama.sh · !help patch")
    return embed


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
