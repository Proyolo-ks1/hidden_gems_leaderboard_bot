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

        if top_x and top_x.lower() == "help":
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
        force_text = mode and mode.lower() == "text"
        if top_x and top_x.lower() == "text":
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
                    "✅ Dieser Channel wird jetzt täglich um 01:00 CET das Leaderboard erhalten."
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
                    "Bitte gib den Namen des Bots an, z.B. `!track add ZitronenBot`"
                )
                return

            leaderboard_json, _ = get_leaderboard_json()
            if "error" in leaderboard_json[0]:
                await ctx.send(leaderboard_json[0]["error"])
                return

            # Filter bots matching the given name (case-insensitive)
            matching_bots = [
                bot
                for bot in leaderboard_json
                if bot.get("Bot", "").lower() == arg.lower()
            ]

            if not matching_bots:
                await ctx.send(f"Kein Bot mit dem Namen `{arg}` gefunden.")
                return

            if len(matching_bots) > 1:
                # Send numbered list for disambiguation
                msg_lines = [
                    f"{idx+1}. {b.get('Col1','')} {b.get('Bot','')} ({b.get('Autor / Team','')})"
                    for idx, b in enumerate(matching_bots)
                ]
                await ctx.send(
                    "Mehrere Bots gefunden. Bitte wiederhole den Befehl mit Index:\n"
                    + "\n".join(msg_lines)
                )
                return

            # Single match: add to tracked
            bot_info = matching_bots[0]

            # Append to the list
            tracked_bots.append(
                {
                    "name": bot_info.get("Bot"),
                    "emoji": bot_info.get("Col1", ""),
                    "author": bot_info.get("Autor / Team", ""),
                }
            )

            # Save updated list
            set_tracked_bots(guild_id=guild_id, tracked=tracked_bots)

            # Green confirmation embed
            embed = discord.Embed(
                title="✅ Bot erfolgreich getrackt!",
                description=f"`{bot_info.get('Bot')}` wurde zur Tracking-Liste hinzugefügt.",
                color=0x00FF00,
            )
            await ctx.send(embed=embed)
            return

        elif action == "remove":
            if not arg:
                await ctx.send(
                    "Bitte gib den Index des zu entfernenden Bots an, z.B. `!track remove 2`"
                )
                return

            try:
                index = int(arg) - 1
                if index < 0 or index >= len(tracked_bots):
                    await ctx.send("Ungültiger Index.")
                    return

                removed_bot = tracked_bots.pop(index)
                set_tracked_bots(guild_id=guild_id, tracked=tracked_bots)

                # Red confirmation embed
                embed = discord.Embed(
                    title="🗑️ Bot entfernt",
                    description=f"`{removed_bot['name']}` wurde aus der Tracking-Liste entfernt.",
                    color=0x00FF00,
                )
                await ctx.send(embed=embed)

            except ValueError:
                await ctx.send("Ungültige Eingabe. Bitte gib eine Zahl an.")

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
