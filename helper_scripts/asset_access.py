# helper_scripts/asset_access.py

# Standard library imports
import re
from enum import Enum
from typing import Type
from PIL import Image
import os

# Third-party imports
from discord import Embed, PartialEmoji

# Own custom scripts
from helper_scripts.globals import BASE_DIR


#       |==========================|
#       |      ASSET_ACCES.PY      |
#       |==========================|


IMAGE_DIR = BASE_DIR / "images"
LANGUAGE_LOGOS_DIR = IMAGE_DIR / "languages"
TWEMOJI_DIR = IMAGE_DIR / "twemoji"


# MARK: parse_custom_emoji()
def parse_custom_emoji(emoji_str: str) -> PartialEmoji:
    match = re.match(r"<a?:(\w+):(\d+)>", emoji_str)
    if match:
        name, id_str = match.groups()
        return PartialEmoji(name=name, id=int(id_str))
    else:
        raise ValueError("Invalid custom emoji format")


# --- Icons ---
class EIcons(Enum):
    NO_EMOJI_FOUND = parse_custom_emoji("<:notFound:1434998126275596398>")


# --- Programming Language Logos partial emojis ---
language_logos_partial_emojis = {
    "ts": parse_custom_emoji("<:TS:1435771634072948908>"),
    "rust": parse_custom_emoji("<:RUST:1437187917431832696>"),
    "ruby": parse_custom_emoji("<:RUBY:1443010353465262142>"),
    "python": parse_custom_emoji("<:PYTHON:1435771628473811067>"),
    "php": parse_custom_emoji("<:PHP:1435771627282632709>"),
    "perl": parse_custom_emoji("<:PERL:1435771626246377614>"),
    "lua": parse_custom_emoji("<:LUA:1443010335450599554>"),
    "julia": parse_custom_emoji("<:JULIA:1435771623738314804>"),
    "js": parse_custom_emoji("<:JS:1435771622203068437>"),
    "java": parse_custom_emoji("<:JAVA:1443010310008213555>"),
    "go": parse_custom_emoji("<:GO:1435771619187621938>"),
    "fsharp": parse_custom_emoji("<:FSHARP:1435771617975468092>"),
    "dart": parse_custom_emoji("<:DART:1443010321974296699>"),
    "csharp": parse_custom_emoji("<:CSHARP:1435771611117654026>"),
    "cpp": parse_custom_emoji("<:CPP:1435771610211811490>"),
    "c": parse_custom_emoji("<:C:1435771608361996471>"),
    "powershell": parse_custom_emoji("<:powershell:1437200535663935618>"),
    "noLanguage": parse_custom_emoji("<:noLanguage:1437201661645819966>"),
}

# --- Programming Language Logos plain strings ---
language_logos = {
    "ts": "<:TS:1435771634072948908>",
    "rust": "<:RUST:1437187917431832696>",
    "ruby": "<:RUBY:1443010353465262142>",
    "python": "<:PYTHON:1435771628473811067>",
    "php": "<:PHP:1435771627282632709>",
    "perl": "<:PERL:1435771626246377614>",
    "lua": "<:LUA:1443010335450599554>",
    "julia": "<:JULIA:1435771623738314804>",
    "js": "<:JS:1435771622203068437>",
    "java": "<:JAVA:1443010310008213555>",
    "go": "<:GO:1435771619187621938>",
    "fsharp": "<:FSHARP:1435771617975468092>",
    "dart": "<:DART:1443010321974296699>",
    "csharp": "<:CSHARP:1435771611117654026>",
    "cpp": "<:CPP:1435771610211811490>",
    "c": "<:C:1435771608361996471>",
    "powershell": "<:powershell:1437200535663935618>",
    "noLanguage": "<:noLanguage:1437201661645819966>",
}


def get_dyn_emoji_str(enum_class: Type[Enum], member_name: str) -> str:
    """
    Safely get the .value of an Enum member dynamically.
    """
    fallback = EIcons.NO_EMOJI_FOUND
    return str(getattr(enum_class, member_name, fallback).value)


LANGUAGE_ICONS = {
    "php": "php-logo-256.png",
    "python": "python-logo-256.png",
    "cpp": "cpp-logo-256.png",
    "c": "c-logo-256.png",
    "rust": "rust-logo-256.png",
    "go": "go-logo-256.png",
    "ts": "ts-logo-256.png",
    "ruby": "ruby-logo-256.png",
    "java": "java-logo-256.png",
    "js": "js-logo-256.png",
    "csharp": "csharp-logo-256.png",
    "powershell": "powershell-logo-256.png",
    "dart": "dart-logo-256.png",
    "fsharp": "fsharp-logo-256.png",
    "julia": "julia-logo-256.png",
    "lua": "lua-logo-256.png",
    "perl": "perl-logo-256.png",
    "noLanguage": "no-logo-256.png",
}


def get_lang_icon(lang_str: str) -> Image.Image:
    """Return the local icon image matching the language string."""
    lang_key = lang_str.strip().lower()  # normalize input

    # exact match first
    if not lang_key:
        filename = LANGUAGE_ICONS["noLanguage"]
    else:
        if lang_key in LANGUAGE_ICONS:
            filename = LANGUAGE_ICONS[lang_key]
        else:
            # fallback icon if no match found
            filename = LANGUAGE_ICONS["noLanguage"]

    return Image.open(os.path.join(LANGUAGE_LOGOS_DIR, filename)).resize((32, 32))


# --- Twemoji access ---
def get_twemoji_image(emoji: str, size: int = 32) -> Image.Image:
    """
    Given a Unicode emoji, return a PIL.Image from the local twemoji repo.
    Automatically resizes to `size` x `size`.
    """
    # Convert emoji to codepoints string
    codepoints = "_".join(f"{ord(c):x}" for c in emoji)
    path = TWEMOJI_DIR / f"{codepoints}.png"
    if not path.exists():
        # fallback transparent image
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        return img

    img = Image.open(path).convert("RGBA")
    if size != img.width:
        img = img.resize((size, size), Image.Resampling.LANCZOS)
    return img


async def send_embed_all_emojis(ctx):
    """
    Returns a single string that contains all plain-string language emojis.
    Useful for quickly verifying whether all emojis render correctly.
    """
    embed = Embed(title="🛠️ Test aller Emojis", color=0x00FF00)
    for lang, emoji in language_logos.items():
        # name = Sprache, value = Emoji selbst
        embed.add_field(name=lang.capitalize(), value=emoji, inline=True)

    await ctx.send(embed=embed)