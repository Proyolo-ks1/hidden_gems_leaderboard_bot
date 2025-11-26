# commands/stats.py

from discord.ext import commands
import datetime
from pathlib import Path
import discord
from helper_scripts.data_analysis import scrape_data, generate_plots_images, DATA_ROOT

class StatsCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="stats", aliases=["st"])
    async def stats_command(self, ctx, plot_name: str = None):
        available = {
            "score": "score_hist.png", "gu": "gu_pct_hist.png",
            "cf": "cf_pct_hist.png", "fc": "fc_pct_hist.png",
            "lang": "lang_bar.png", "city": "city_bar.png"
        }
        
        if not plot_name or plot_name not in available:
            return await ctx.send(f"Verfügbar: {', '.join(available.keys())}")

        # Reuse logic to get data/plots
        today = datetime.date.today().isoformat()
        folder = DATA_ROOT / f"scrims_out_{today}"
        
        if not folder.exists():
            await ctx.send("🔄 Keine Daten von heute. Scrape...")
            df = await self.bot.loop.run_in_executor(None, scrape_data)
            if "error" in df: return await ctx.send(df["error"])
            await self.bot.loop.run_in_executor(None, generate_plots_images, df, folder)

        plot_path = folder / available[plot_name]
        if plot_path.exists():
            await ctx.send(file=discord.File(plot_path))
        else:
            await ctx.send("❌ Plot nicht gefunden.")

async def setup(bot):
    await bot.add_cog(StatsCommand(bot))