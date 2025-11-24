# helper_scripts/bot_commands.py

# Standard library imports
from typing import Optional, List, Dict

# Third-party imports
import discord
from discord.ext import commands
from discord import TextChannel

# Own modules
from helper_scripts.helper_functions import get_leaderboard_json
from helper_scripts.data_functions import get_tracked_bots, set_tracked_bots


def register_commands(
    bot: commands.Bot,
    ADMINS: set,
    channels_to_post: set,
    scheduled_channels: dict,
    save_channels,
    send_leaderboard,
):
    # MARK: !leaderboard / top
    @bot.command(name="leaderboard", aliases=["lb", "top"])
    async def leaderboard_command(
        ctx: commands.Context, top_x: Optional[str] = None, mode: Optional[str] = None
    ):
        """Zeigt Leaderboard, optional Top x: "!leaderboard x (alias: lb, top)" """

        if top_x.lower() == "help":
            await ctx.send(
                f"## Nutzung von `{ctx.prefix}leaderboard`"
                f"\n-# (aliases: {ctx.prefix}lb, {ctx.prefix}top)"
                "\n"
                "\n`!top [top_x] [force_text] [no_tracked]`"
                "\n- `[top_x]       ` → zeige nur die top [top_x] Einträge des Leaderboards"
                '\n- `["text"]      ` → erzwingt Textformat statt Bilder'
                '\n- `["no_tracked"]` → sendet keine tracked Bots'
                "\n-# ℹ️ Syntax: `<param>` = erforderlicher parameter, `[param]` = optionaler parameter"
            )
            return

        # Determine guild ID (or use author ID for DM)
        guild_id = ctx.guild.id if ctx.guild else ctx.author.id

        # Convert top_x to int if provided
        top_x_int = None
        if top_x:
            try:
                top_x_int = int(top_x)
                if top_x_int <= 0:
                    top_x_int = None
            except ValueError:
                # ignore if top_x is "text" or other mode
                if top_x.lower() != "text":
                    await ctx.send("❌ Ungültige Zahl. Bitte gib eine ganze Zahl ein.")
                    return

        # Decide if we force text mode
        #you dont have to check mode if you already check lower
        force_text = mode.lower() == "text"
        if top_x.lower() == "text":
            force_text = True
            top_x_int = None

        # Get tracked bots for this guild/DM
        tracked_bots = get_tracked_bots(guild_id=guild_id)

        # Call the updated send_leaderboard
        await send_leaderboard(
            channel=ctx.channel,
            tracked_bots=tracked_bots,
            top_x=top_x_int,
            force_text=force_text,
            as_thread=False,  # or True if you implement thread posting
        )

    # MARK: !schedule
    @bot.command(name="schedule", aliases=["s"])
    async def schedule_command(ctx: commands.Context, action: str = ""):
        """Start, stop oder list scheduled leaderboard posts"""
        valid_actions = ["start", "stop", "list"]

        # Wenn keine Aktion angegeben oder ungültig
        if not action or action.lower() not in valid_actions:
            await ctx.send(
                f"## Nutzung von `{ctx.prefix}schedule`"
                f"\n-# (aliases: {ctx.prefix}s)"
                "\n"
                "\n- `start` → Scheduler für diesen Channel aktivieren"
                "\n- `stop ` → Scheduler für diesen Channel deaktivieren"
                "\n- `list ` → Zeigt alle registrierten Channels (Admins only)"
                "\n-# ℹ️ Syntax: `<param>` = erforderlicher parameter, `[param]` = optionaler parameter"
            )
            return

        action = action.lower()
        channel_id = ctx.channel.id
        channel = ctx.channel
        guild = ctx.guild

        if guild is None or not isinstance(channel, TextChannel):
            await ctx.send(
                "❌ Dieser Befehl kann nur in Server-Textkanälen verwendet werden."
            )
            return

        # START
        if action == "start":
            if channel_id in channels_to_post:
                await ctx.send("ℹ️ Dieser Channel bekommt das Leaderboard bereits.")
            else:
                channels_to_post.add(channel_id)
                scheduled_channels[str(channel_id)] = f"{guild.name}#{channel.name}"
                save_channels()
                await ctx.send(
                    "✅ Dieser Channel wird jetzt täglich um 03:00 CET das Leaderboard erhalten."
                )

        # STOP
        elif action == "stop":
            if channel_id in channels_to_post:
                channels_to_post.remove(channel_id)
                scheduled_channels.pop(str(channel_id), None)
                save_channels()
                await ctx.send(
                    "✅ Dieser Channel erhält das Leaderboard ab jetzt nicht mehr."
                )
            else:
                await ctx.send(
                    "ℹ️ Dieser Channel war nicht für das Leaderboard registriert."
                )

        # LIST (Admins only)
        elif action == "list":
            if ctx.author.id not in ADMINS:
                await ctx.send(
                    "🚫 Du hast keine Admin-Rechte, um diese Liste anzusehen."
                )
                return

            if not scheduled_channels:
                await ctx.send("📭 Es sind aktuell keine Channels registriert.")
            else:
                lines = []
                for ch_id, full_name in scheduled_channels.items():
                    if "#" in full_name:
                        server, channel_name = full_name.split("#", 1)
                    else:
                        server, channel_name = full_name, "Unbekannt"
                    lines.append(
                        f"**Server:** `{server.strip()}` -> **Channel:** `#{channel_name.strip()}`"
                    )
                msg = "\n".join(lines)
                await ctx.send(f"📋 **Aktuell registrierte Channels:**\n\n{msg}")

        else:
            await ctx.send(
                "❌ Ungültiger Parameter. Nutze `start`, `stop` oder `list`."
            )

    # MARK: !stopbot
    @bot.command(name="stopbot", aliases=["stop"])
    async def stop_bot_command(ctx: commands.Context):
        """Stoppt den Bot (Admins only)"""
        if ctx.author.id not in ADMINS:
            await ctx.send("🚫 Du hast keine Berechtigung, diesen Befehl zu nutzen.")
            return

        await ctx.send("⏹️ Bot wird heruntergefahren...")
        await bot.close()

    # MARK: !ping
    @bot.command(name="ping", aliases=["p"])
    async def ping_command(ctx: commands.Context):
        """Responds with bot latency."""
        latency_ms = round(ctx.bot.latency * 1000)
        await ctx.send(f"🏓 Pong! {latency_ms}ms")

    # MARK: !track
    @bot.command(name="track", aliases=["t"])
    async def track_command(
        ctx: commands.Context,
        action: Optional[str] = None,
        *,
        arg: Optional[str] = None,
    ):
        """Manage tracked bots: list/add/remove"""
        guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        tracked_bots: List[Dict] = get_tracked_bots(guild_id=guild_id)

        # Determine if this is a DM or a server
        location_type = (
            f"DM: {ctx.author.name}"
            if ctx.guild is None
            else f"Server: {ctx.guild.name}"
        )
        embed_color = 0xB1CCDB

        if action == "list":
            if not tracked_bots:
                embed = discord.Embed(
                    title=f"Tracked Bots in {location_type}",
                    description="📭 Keine Bots werden aktuell getrackt.",
                    color=embed_color,
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title=f"Tracked Bots in {location_type}", color=embed_color
            )

            for idx, info in enumerate(tracked_bots, start=1):
                embed.add_field(
                    name=f"{idx}. {info['emoji']} {info['name']}",
                    value=f"Autor: {info['author']}",
                    inline=False,
                )

            await ctx.send(embed=embed)

        elif action == "add":
            if not arg:
                await ctx.send(
                    "Bitte gib den Namen des Bots an, z.B. `!track add ZitronenBot` oder mehrere durch Kommas getrennt."
                )
                return

            leaderboard_json, _ = get_leaderboard_json()
            if "error" in leaderboard_json[0]:
                await ctx.send(leaderboard_json[0]["error"])
                return

            # Split by commas and strip whitespace
            bot_names = [name.strip() for name in arg.split(",") if name.strip()]
            added_bots = []
            not_found = []

            MAX_TRACKED_BOTS = 25

            for bot_name in bot_names:
                if len(tracked_bots) >= MAX_TRACKED_BOTS:
                    not_found.append(
                        bot_name
                        + f" (kann nicht hinzugefügt werden, Limit erreicht ({MAX_TRACKED_BOTS}))"
                    )
                    continue

                matching_bots = [
                    bot
                    for bot in leaderboard_json
                    if bot.get("Bot", "").lower() == bot_name.lower()
                ]

                if not matching_bots:
                    not_found.append(bot_name)
                    continue

                if len(matching_bots) > 1:
                    not_found.append(bot_name + " (mehrdeutig)")
                    continue

                bot_info = matching_bots[0]

                # Check if bot already tracked (compare full dict)
                bot_dict = {
                    "name": bot_info.get("Bot"),
                    "emoji": bot_info.get("Col1", ""),
                    "author": bot_info.get("Autor / Team", ""),
                }
                if any(b == bot_dict for b in tracked_bots):
                    not_found.append(bot_name + " (bereits getrackt)")
                    continue

                tracked_bots.append(bot_dict)
                added_bots.append(bot_info.get("Bot"))

            # Save updated list
            set_tracked_bots(guild_id=guild_id, tracked=tracked_bots)

            # Build embed for confirmation
            embed = discord.Embed(
                title="Folgende Bots wurden hinzugefügt",
                color=0x00FF00,
            )

            if added_bots:
                for bot_name in added_bots:
                    # find the info from tracked_bots
                    bot_info = next(
                        (b for b in tracked_bots if b["name"] == bot_name), None
                    )
                    if bot_info:
                        embed.add_field(
                            name=f"{bot_info['emoji']} {bot_info['name']}",
                            value=f"Autor: {bot_info['author']}",
                            inline=False,
                        )

            if not_found:
                embed.add_field(
                    name="⚠️ Nicht gefunden / mehrdeutig",
                    value="\n".join(not_found),
                    inline=False,
                )

            await ctx.send(embed=embed)
            return

        elif action == "remove":
            if not arg:
                await ctx.send(
                    "Bitte gib den Index des zu entfernenden Bots an, z.B. `!track remove 2` oder mehrere durch Kommas getrennt."
                )
                return

            indices = []
            not_found = []
            # Parse comma-separated indices
            for part in arg.split(","):
                part = part.strip()
                if not part:
                    continue
                try:
                    idx = int(part) - 1
                    if 0 <= idx < len(tracked_bots):
                        indices.append(idx)
                    else:
                        not_found.append(part)
                except ValueError:
                    not_found.append(part)

            removed_bots = []
            # Remove in reverse order to avoid index shifting
            for idx in sorted(indices, reverse=True):
                removed_bots.append(tracked_bots.pop(idx))

            set_tracked_bots(guild_id=guild_id, tracked=tracked_bots)

            # Build embed
            embed = discord.Embed(title="Folgende Bots wurden entfernt", color=0xFF0000)

            if removed_bots:
                for bot_info in removed_bots:
                    embed.add_field(
                        name=f"{bot_info['emoji']} {bot_info['name']}",
                        value=f"Autor: {bot_info['author']}",
                        inline=False,
                    )

            if not_found:
                embed.add_field(
                    name="⚠️ Ungültige Indizes",
                    value="\n".join(not_found),
                    inline=False,
                )

            await ctx.send(embed=embed)

        else:
            await ctx.send(
                f"## Nutzung von `{ctx.prefix}track`"
                f"\n-# (aliases: {ctx.prefix}t)"
                "\n"
                "\n- `add <Botname>      ` → fügt Bot zu zum tracking mit namen `<Botname>`"
                "\n- `remove <list index>` → entfernt bot vom tracking mit index `<list index>`"
                "\n- `list               ` → Zeigt alle tracked Bots"
                "\n-# ℹ️ Syntax: `<param>` = erforderlicher parameter, `[param]` = optionaler parameter"
            )
            return
