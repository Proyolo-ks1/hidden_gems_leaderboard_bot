from discord.ext import commands
from typing import Optional
from helper_scripts.data_functions import get_tracked_bots, set_tracked_bots
from helper_scripts.helper_functions import get_leaderboard_json
import discord

class TrackingCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="track", aliases=["t"])
    async def track_command(self, ctx, action: Optional[str] = None, *, arg: Optional[str] = None):
        guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        tracked = get_tracked_bots(guild_id)

        if action == "list":
            if not tracked: return await ctx.send("📭 Keine getrackten Bots.")
            embed = discord.Embed(title="Tracked Bots")
            for i, b in enumerate(tracked, 1):
                embed.add_field(name=f"{i}. {b['name']}", value=b['author'], inline=False)
            await ctx.send(embed=embed)
        
        elif action == "add" and arg:
            lb, _ = get_leaderboard_json()
            # Simple matching logic (simplified for brevity)
            found = next((b for b in lb if b.get("Bot").lower() == arg.lower()), None)
            if found:
                entry = {"name": found["Bot"], "author": found["Autor / Team"], "emoji": found.get("Col1","")}
                if entry not in tracked:
                    tracked.append(entry)
                    set_tracked_bots(guild_id, tracked)
                    await ctx.send(f"✅ {arg} getrackt.")
                else:
                    await ctx.send("⚠️ Bereits getrackt.")
            else:
                await ctx.send("❌ Bot nicht im Leaderboard gefunden.")

        elif action == "remove" and arg and arg.isdigit():
            idx = int(arg) - 1
            if 0 <= idx < len(tracked):
                removed = tracked.pop(idx)
                set_tracked_bots(guild_id, tracked)
                await ctx.send(f"🗑️ {removed['name']} entfernt.")
            else:
                await ctx.send("❌ Ungültiger Index.")
        else:
            await ctx.send("Usage: !track [list|add <name>|remove <index>]")

async def setup(bot):
    await bot.add_cog(TrackingCommand(bot))