# helper_scripts/data_functions.py

# Standard library imports
import json
from typing import List, Dict

# Third-party imports
# None

# Own modules
from helper_scripts.globals import LOCAL_DATA_PATH_DIR


BOT_DATA_FILE = LOCAL_DATA_PATH_DIR / "bot_data.json"


# MARK: Bot Data
def load_bot_data() -> dict:
    """Load the entire bot_data.json file."""
    if not BOT_DATA_FILE.exists():
        return {}
    with open(BOT_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bot_data(data: dict):
    """Save a full dict back into bot_data.json."""
    with open(BOT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# MARK: Guild Data
def get_guild_data(guild_id: int) -> dict:
    """Return the data for a specific guild ID, creating it if missing."""
    data = load_bot_data()
    guilds = data.setdefault("guild_data", {})

    guild_id_str = str(guild_id)

    # Create empty structure if missing
    if guild_id_str not in guilds:
        guilds[guild_id_str] = {"tracked_bots": [], "scheduled_channels": []}
        save_bot_data(data)

    return guilds[guild_id_str]


def set_guild_data(guild_id: int, guild_dict: dict):
    """Write the updated guild data back into bot_data.json."""
    data = load_bot_data()
    guilds = data.setdefault("guild_data", {})

    guilds[str(guild_id)] = guild_dict
    save_bot_data(data)


# MARK: Tracked Bots
def get_tracked_bots(guild_id: int) -> List[Dict[str, str]]:
    """Return the tracked bots for a specific guild."""
    guild_data = get_guild_data(guild_id)
    return guild_data.get("tracked_bots", [])


def set_tracked_bots(guild_id: int, tracked: List[Dict[str, str]]):
    """Set the tracked bots list for a specific guild."""
    guild_data = get_guild_data(guild_id)
    guild_data["tracked_bots"] = tracked
    set_guild_data(guild_id, guild_data)
