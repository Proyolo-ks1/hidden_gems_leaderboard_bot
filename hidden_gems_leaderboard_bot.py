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
    post_leaderboard_in_channels,
    send_leaderboard,
)

BASE_DIR = Path(__file__).parent
DATA_FILE = BASE_DIR / "bot_data.json"
LOCAL_DATA = BASE_DIR / "local_data"
IMAGES_DIR = BASE_DIR / "images"
LANGUAGE_LOGOS_DIR = IMAGES_DIR / "languages"

os.makedirs(LOCAL_DATA, exist_ok=True)


def main():
    # all your current top-level code goes here:
    # loading env, initializing bot, scheduler, etc.

    # Load saved channels on startup
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            scheduled_channels = data.get("scheduled_channels", {})
            channels_to_post = set(int(ch_id) for ch_id in scheduled_channels.keys())
    else:
        scheduled_channels = {}
        channels_to_post = set()

    def save_channels():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                {"scheduled_channels": scheduled_channels},
                f,
                ensure_ascii=False,
                indent=2,
            )

    # Load Environment Variables
    dotenv_path = Path("..") / "environment_variables.env"
    load_dotenv(dotenv_path=dotenv_path)
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
    if hostname == "PC-Konsti" or hostname == "KS-uni-HP-ZBook":
        bot = commands.Bot(command_prefix="?", intents=intents)
    else:
        bot = commands.Bot(command_prefix="!", intents=intents)

    # Scheduler mit CET
    scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/Berlin"))

    # ----------------- Bot Ready & Scheduler -----------------
    @bot.event
    async def on_ready():
        print(f"Bot ist online als {bot.user}")

        # Scheduler starten
        if not scheduler.get_jobs():
            job = scheduler.add_job(
                post_leaderboard_in_channels,
                CronTrigger(hour=1, minute=00),
                args=[bot, channels_to_post],
            )
            scheduler.start()

            next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
            print(f"Scheduler gestartet! Nächster Post um: {next_run}")
        else:
            for job in scheduler.get_jobs():
                next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S %Z")
                print(f"Scheduler bereits aktiv. Nächster Lauf: {next_run}")

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
