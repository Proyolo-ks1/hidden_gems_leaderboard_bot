# commands/maps.py

import datetime
import discord
import pandas as pd
import matplotlib.pyplot as plt
import contextily as cx
import folium
from discord.ext import commands

from helper_scripts.data_analysis import scrape_data, generate_plots_images, DATA_ROOT
# Updated import to pull the new progress function
from helper_scripts.geo import get_city_coords_with_progress, get_city_color

class MapsCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_or_scrape_data(self, ctx):
        today = datetime.date.today().isoformat()
        folder = DATA_ROOT / f"scrims_out_{today}"
        data_path = folder / "data.csv"
        
        # Check if recent data exists (1 hour cache)
        if data_path.exists() and (datetime.datetime.now() - datetime.datetime.fromtimestamp(data_path.stat().st_mtime)).total_seconds() < 3600:
            print(f"[MAPS] Using cached data from {today}.")
            return pd.read_csv(data_path), folder
        
        await ctx.send("🌐 Lade Daten und Geocoding... (dies kann kurz dauern)")
        print("[MAPS] Starting scrape...")
        df_result = await self.bot.loop.run_in_executor(None, scrape_data)
        
        if isinstance(df_result, dict) and "error" in df_result:
            await ctx.send(f"❌ Scraping-Fehler: {df_result['error']}")
            return None, None

        folder.mkdir(parents=True, exist_ok=True)
        df_result.to_csv(data_path, index=False)
        # Generate stats plots while we are at it
        await self.bot.loop.run_in_executor(None, generate_plots_images, df_result, folder)
        print("[MAPS] Scrape complete. Data saved.")
        
        return df_result, folder

    @commands.command(name='map', aliases=['maps', 'm'], help="Generiert eine Karte. !maps [png | html]")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def maps_command(self, ctx: commands.Context, mode: str = 'png'):
        """
        Generiert eine Karte der Bot-Standorte.
        Modes:
        - png (default): Sendet ein statisches Bild.
        - html: Sendet eine interaktive HTML-Datei.
        """
        await ctx.defer()

        df, folder = await self.get_or_scrape_data(ctx)
        if df is None: return

        if 'city' not in df.columns or df['city'].empty:
            return await ctx.send("❌ Keine Stadt-Daten verfügbar.")

        # --- GEOCODING (with progress reporting) ---
        # Execute the function that includes progress prints in a thread
        mapped_coords = await self.bot.loop.run_in_executor(
            None, get_city_coords_with_progress, df
        )

        if not mapped_coords:
            return await ctx.send("❌ Konnte keine Koordinaten ermitteln.")

        # --- MAP GENERATION ---
        
        # Calculate Average Center and Max Count
        avg_lat = sum(c['coords'][0] for c in mapped_coords) / len(mapped_coords)
        avg_lon = sum(c['coords'][1] for c in mapped_coords) / len(mapped_coords)
        max_count = max(c['count'] for c in mapped_coords) # Recalculate max count for scaling

        if mode.lower() == 'html':
            # --- FOLIUM HTML MAP ---
            print("[MAPS] Generating Folium HTML map.")
            m = folium.Map(location=[avg_lat, avg_lon], zoom_start=6)
            
            for data in mapped_coords:
                lat, lon = data['coords']
                city_count = data['count']
                
                radius = 5 + (city_count / max_count) * 15 if max_count > 0 else 5
                color = get_city_color(city_count, max_count)

                folium.CircleMarker(
                    location=[lat, lon], 
                    radius=radius, 
                    popup=f"{data['city']} ({city_count} bots)", 
                    color=color, 
                    fill=True, 
                    fill_color=color,
                    fill_opacity=0.7
                ).add_to(m)

            map_path = folder / "map.html"
            m.save(str(map_path))
            print(f"[MAPS] HTML map saved to {map_path}")
            
            await ctx.send("🗺️ **Interaktive Karte**", file=discord.File(map_path))
        
        else:
            # --- STATIC PNG MAP (Matplotlib + Contextily) ---
            print("[MAPS] Generating static PNG map.")
            fig, ax = plt.subplots(figsize=(10, 10))
            
            lons = [c['coords'][1] for c in mapped_coords]
            lats = [c['coords'][0] for c in mapped_coords]
            sizes = [50 + (c['count'] / max_count) * 300 for c in mapped_coords]
            colors = [get_city_color(c['count'], max_count) for c in mapped_coords]

            ax.scatter(lons, lats, s=sizes, c=colors, alpha=0.8, zorder=2, edgecolors='white')
            
            try:
                # Add padding
                min_lon, max_lon = min(lons), max(lons)
                min_lat, max_lat = min(lats), max(lats)
                ax.set_xlim(min_lon - 2, max_lon + 2)
                ax.set_ylim(min_lat - 2, max_lat + 2)

                cx.add_basemap(ax, crs='EPSG:4326', source=cx.providers.CartoDB.Positron)
            except Exception as e:
                print(f"[MAPS] Basemap Error (PNG generation): {e}")

            ax.set_axis_off()
            ax.set_title(f"Bot Locations ({len(mapped_coords)} cities)", fontsize=16)

            map_path = folder / "map.png"
            fig.tight_layout()
            fig.savefig(map_path, dpi=100)
            plt.close(fig)
            print(f"[MAPS] PNG map saved to {map_path}")

            await ctx.send("🗺️ **Statische Karte**", file=discord.File(map_path))

async def setup(bot):
    await bot.add_cog(MapsCommand(bot))