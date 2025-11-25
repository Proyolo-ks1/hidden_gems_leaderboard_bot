# helper_scripts/globals.py

# Standard library imports
from pathlib import Path

# Third-party imports
# None

# Own modules
# None


BASE_DIR = Path(__file__).parent.parent
LOCAL_DATA_PATH_DIR = BASE_DIR / "local_data"
IMAGES_DIR = BASE_DIR / "images"
LANGUAGE_LOGOS_DIR = IMAGES_DIR / "languages"

DOTENV_PATH = Path("..") / "environment_variables.env"
