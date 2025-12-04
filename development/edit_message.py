# === Standard library imports ===
import os
import sys
import re

# === Add project root to Python path ===
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# === Third-party imports ===
import discord
from discord.ext import commands
from dotenv import load_dotenv

# === Own modules ===
from helper_scripts.globals import DOTENV_PATH

# === File paths ===
DEV_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_MESSAGE_FILE = os.path.join(DEV_DIR, "old_message_text.txt")
NEW_MESSAGE_FILE = os.path.join(DEV_DIR, "new_message_text.txt")


def extract_ids_from_link(line: str):
    """
    Accepts a discord message link and extracts:
    guild_id, channel_id, message_id
    """
    match = re.search(r"https://discord\.com/channels/(\d+)/(\d+)/(\d+)", line.strip())
    if not match:
        raise ValueError("Die erste Zeile enthält keinen gültigen Discord-Link!")

    guild_id, channel_id, message_id = match.groups()
    return int(channel_id), int(message_id)


def read_new_message_and_extract_ids():
    with open(NEW_MESSAGE_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    if not lines:
        raise ValueError("new_message_text.txt ist leer!")

    # First line must be the link
    channel_id, message_id = extract_ids_from_link(lines[0])

    # Remaining text = new message content
    new_content = "".join(lines[1:]).rstrip()

    return channel_id, message_id, new_content


async def edit_message(bot, channel_id, message_id, new_content):
    # Fetch channel
    channel = await bot.fetch_channel(channel_id)

    # Fetch message
    msg = await channel.fetch_message(message_id)

    # Save old message content first
    with open(OLD_MESSAGE_FILE, "w", encoding="utf-8") as f:
        f.write(msg.content)

    # Update message
    await msg.edit(content=new_content)

    print("Nachricht erfolgreich aktualisiert.")


def main():
    # Load env
    load_dotenv(dotenv_path=DOTENV_PATH)
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    if DISCORD_BOT_TOKEN is None:
        raise ValueError("DISCORD_BOT_TOKEN fehlt in der .env Datei!")

    # Read channel + message IDs + new content
    channel_id, message_id, new_content = read_new_message_and_extract_ids()

    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        print(f"Bot online als {bot.user}")

        try:
            await edit_message(bot, channel_id, message_id, new_content)

        except Exception as e:
            print(f"Fehler beim Bearbeiten der Nachricht: {e}")

        await bot.close()

    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
