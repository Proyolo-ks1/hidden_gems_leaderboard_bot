# commands/leaderboard.py

from discord.ext import commands
from typing import Optional
from helper_scripts.data_functions import get_tracked_bots
from helper_scripts.helper_functions import send_leaderboard

class LeaderboardCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="leaderboard", aliases=["lb", "top"], help="Zeigt das Leaderboard an. !top [number] [text] [no_tracked]")
    async def leaderboard_command(self, ctx, top_x: Optional[str] = None, mode: Optional[str] = None):
        if top_x == "help":
            return await ctx.send("Usage: !top [number] [text] [no_tracked]")

        guild_id = ctx.guild.id if ctx.guild else ctx.author.id
        
        top_x_int = 0
        force_text = (mode and mode.lower() == "text") or (top_x and top_x.lower() == "text")

        if top_x and top_x.isdigit():
            top_x_int = int(top_x)

        tracked_bots = get_tracked_bots(guild_id=guild_id)

        await send_leaderboard(
            channel=ctx.channel,
            tracked_bots=tracked_bots,
            top_x=top_x_int if top_x_int > 0 else 0,
            force_text=force_text,
            as_thread=False,
        )

async def setup(bot):
    await bot.add_cog(LeaderboardCommand(bot))