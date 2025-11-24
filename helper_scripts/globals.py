# helper_scripts/globals.py

# Standard library imports
from pathlib import Path

# Third-party imports
# None

# Own modules
# None


BASE_DIR = Path(__file__).parent.parent
BOT_DATA_PATH = BASE_DIR / "bot_data.json"

DOTENV_PATH = Path("..") / "environment_variables.env"
