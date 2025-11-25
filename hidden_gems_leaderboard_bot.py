# hidden_gems_leaderboard_bot.py

# Standard library imports
import os
import json
import socket
from pathlib import Path

# Third-party imports
import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from dotenv import load_dotenv

# Own custom scripts / modules
from helper_scripts.bot_commands import register_commands
from helper_scripts.helper_functions import (
    post_lb_in_scheduled_channels,
    send_leaderboard,
)
from helper_scripts.globals import DOTENV_PATH, LOCAL_DATA_PATH_DIR


BOT_DATA_FILE = LOCAL_DATA_PATH_DIR / "bot_data.json"

os.makedirs(LOCAL_DATA_PATH_DIR, exist_ok=True)


def main():
    # 1. Loading env
    # 2. Initializing bot
    # 3. Scheduler

    # Load saved channels on startup
    if BOT_DATA_FILE.exists():
        with open(BOT_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            scheduled_channels = data.get("scheduled_channels", {})
            channels_to_post = set(int(ch_id) for ch_id in scheduled_channels.keys())
    else:
        scheduled_channels = {}
        channels_to_post = set()

    def save_channels():
        with open(BOT_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"scheduled_channels": scheduled_channels},
                f,
                ensure_ascii=False,
                indent=2,
            )

    # Load Environment Variables

    load_dotenv(dotenv_path=DOTENV_PATH)
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if DISCORD_BOT_TOKEN is None:
        raise ValueError("DISCORD_BOT_TOKEN ist nicht in der .env gesetzt!")

    ADMINS = set(
        int(x.strip())
        for x in os.getenv("ADMINS_DISCORD_ACCOUNT_IDS", "").split(",")
        if x.strip().isdigit()
    )

    intents = discord.Intents.default()
    intents.message_content = True
    hostname = socket.gethostname()
    prefix = "?"
    if hostname == "turtle-01":
        prefix = "!"

    bot = commands.Bot(command_prefix=prefix, intents=intents)

    # Scheduler mit CET
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Berlin"))

    # ----------------- Bot Ready & Scheduler -----------------
    @bot.event
    async def on_ready():
        print(f"Bot ist online als {bot.user}")

        # Scheduler starten
        if not scheduler.get_jobs():
            job = scheduler.add_job(
                post_lb_in_scheduled_channels,
                CronTrigger(hour=3, minute=00),
                args=[bot],
            )
            scheduler.start()

            next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            print(f"Scheduler gestartet! Nächster Post um: {next_run}")
        else:
            for job in scheduler.get_jobs():
                next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                print(f"Scheduler bereits aktiv. Nächster Lauf: {next_run}")

    # ----------------- Command Logging -----------------
    @bot.event
    async def on_command(ctx: commands.Context):
        print(
            f"[COMMAND] {ctx.author} hat '{ctx.command}' in {ctx.channel} ausgeführt."
        )

    @bot.event
    async def on_command_error(ctx, error):
        print(f"[ERROR] Command '{ctx.command}' von {ctx.author} schlug fehl: {error}")

    register_commands(
        bot,
        ADMINS,
        channels_to_post,
        scheduled_channels,
        save_channels,
        send_leaderboard,
    )

    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
