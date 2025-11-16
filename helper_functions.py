# helper_functions.py

# Standard library imports
import os
import json
from pathlib import Path
import math

# Third-party imports
import discord
from discord import TextChannel
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
import datetime
import requests

# Own modules
from asset_access import language_logos, get_lang_icon, get_twemoji_image


BASE_DIR = Path(__file__).parent
FONTS_DIR = BASE_DIR / "fonts"
LOCAL_DATA = BASE_DIR / "local_data"
OUTPUT_DIR = LOCAL_DATA / "generated_tables"
BOT_DATA_PATH = BASE_DIR / "bot_data.json"
TEXT_FONT_PATH = FONTS_DIR / "DejaVuSans.ttf"
HTML_FILE = LOCAL_DATA / "leaderboard.html"
JSON_FILE = LOCAL_DATA / "leaderboard.json"


os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_bot_data() -> dict:
    if not BOT_DATA_PATH.exists():
        return {}
    with open(BOT_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bot_data(data: dict):
    with open(BOT_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_tracked_bots() -> dict:
    data = load_bot_data()
    return data.get("tracked_bots", {})


def set_tracked_bots(tracked: dict):
    data = load_bot_data()
    data["tracked_bots"] = tracked
    save_bot_data(data)


def generate_images_from_json(
    leaderboard_json: list[dict], top_x: int | None = None
) -> list[str]:
    """Generate one or more PNG images from the leaderboard JSON."""
    text_font = ImageFont.truetype(TEXT_FONT_PATH, 18)
    line_height = 36
    padding = 5
    max_rows_per_image = 20
    rows = leaderboard_json[:top_x] if top_x else leaderboard_json
    total_rows = len(rows)

    num_images = math.ceil(total_rows / max_rows_per_image)
    rows_per_image = math.ceil(total_rows / num_images)

    images = []
    for i in range(num_images):
        start_idx = i * rows_per_image
        end_idx = min(start_idx + rows_per_image, total_rows)
        chunk = rows[start_idx:end_idx]

        img_width = 1140
        img_height = padding * 2 + (len(chunk) + 1) * line_height
        img = Image.new("RGB", (img_width, img_height), color=(25, 25, 25))
        draw = ImageDraw.Draw(img)

        # header
        columns = [
            ("#", 60),
            ("Rang", 60),
            ("🙂", 40),
            ("Bot", 200),
            ("Score", 100),
            ("GU", 90),
            ("CF", 90),
            ("FC", 90),
            ("Autor / Team", 200),
            ("Ort", 150),
            ("Lang", 60),
        ]

        # Extract headers and widths
        header_titles, col_widths = zip(*columns)

        # Calculate col_x positions automatically
        col_x = [5]  # first column starts at x=5
        for w in col_widths[:-1]:
            col_x.append(col_x[-1] + w)

        # Headers
        for col_idx, head in enumerate(header_titles):
            if col_idx != 2:  # not emoji column
                draw.text(
                    (col_x[col_idx], padding), head, fill=(255, 200, 0), font=text_font
                )

        # Rows
        y = padding + line_height
        for row_idx, entry in enumerate(chunk, start=start_idx + 1):
            rank = entry.get("Rang", "")
            emoji_str = entry.get("Col1", "")
            bot = entry.get("Bot", "")
            score = entry.get("Score", "")
            gu = entry.get("GU", "")
            cf = entry.get("CF", "")
            fc = entry.get("FC", "")
            author = entry.get("Autor / Team", "")
            ort = entry.get("Ort", "")
            sprache = entry.get("Sprache", "")

            row_values = [
                str(row_idx),
                rank,
                emoji_str,
                bot,
                score,
                gu,
                cf,
                fc,
                author,
                ort,
            ]
            for col_idx, val in enumerate(row_values):
                if col_idx == 2:  # emoji column
                    twemoji_img = get_twemoji_image(val, size=24)
                    img.paste(twemoji_img, (col_x[col_idx], y), twemoji_img)
                else:
                    col_width = (
                        col_x[col_idx + 1] - col_x[col_idx] - 5
                        if col_idx < len(col_x) - 1
                        else 120
                    )
                    val_to_draw = fit_text_to_column(
                        draw, str(val), text_font, col_width
                    )
                    draw.text(
                        (col_x[col_idx], y),
                        val_to_draw,
                        fill=(255, 255, 255),
                        font=text_font,
                    )

            # language icon
            lang_img = get_lang_icon(sprache)
            img.paste(lang_img, (col_x[-1], y - 8), lang_img.convert("RGBA"))

            y += line_height

        file_path = os.path.join(OUTPUT_DIR, f"leaderboard_part_{i + 1}.png")
        img.save(file_path)
        images.append(file_path)

    return images


def fit_text_to_column(draw, text, font, max_width):
    """Truncate text and add ellipsis if it doesn't fit the column width."""
    if draw.textlength(text, font=font) <= max_width:
        return text
    while draw.textlength(text + "...", font=font) > max_width and text:
        text = text[:-1]
    return text + "..." if text else ""


async def send_table_images(
    channel, status_msg, leaderboard_json, top_x, title: str | None = None
):
    await status_msg.edit(content="📊 Generating leaderboard images...")

    image_paths = generate_images_from_json(leaderboard_json, top_x)

    # Build title message
    if title:
        header = title
    else:
        header = "**Aktuelles Leaderboard**"

    if top_x:
        header += f" (Top {top_x})"

    await status_msg.edit(content=header)

    for path in image_paths:
        await channel.send(file=discord.File(path))


def get_leaderboard_date(html: str) -> datetime.date | None:
    soup = BeautifulSoup(html, "html.parser")
    boxes = soup.find_all("div", class_="box")
    for box in boxes:
        h3 = box.find("h3")
        if h3 and h3.text.strip() == "Datum":
            p = box.find("p")
            if p and p.text.strip():
                date_str = p.text.strip()
                try:
                    leaderboard_date = datetime.datetime.strptime(
                        date_str, "%d. %B %Y"
                    ).date()
                    return leaderboard_date
                except ValueError:
                    return None
    return None


def parse_html_to_json(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    # Save raw HTML
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(str(table))

    headers = [
        th.text.strip() or f"Col{i}" for i, th in enumerate(table.find_all("th"))
    ]
    rows = table.find_all("tr")
    leaderboard_json = []

    for row in rows:
        classes = row.get("class") or []
        if "spacer" in classes:
            continue

        cols = row.find_all("td")
        if not cols:
            continue

        entry = {}
        first_cell = cols[0].text.strip()
        if not first_cell:
            entry["Rang"] = "DNQ."
        else:
            entry["Rang"] = first_cell

        for i, col in enumerate(cols[:-1]):  # Letzte Spalte (Commit) wird weggelassen
            if i == 0:
                continue  # Rang haben wir schon
            header = headers[i] if i < len(headers) else f"Col{i}"

            # Special case for Col1 (emoji)
            col_classes = col.get("class")
            if col_classes is None:
                col_classes = []
            elif isinstance(col_classes, str):
                col_classes = [col_classes]

            if "emoji" in col_classes:
                img_tag = col.find("img")
                if img_tag:
                    src = img_tag.get("src")
                    src_str = str(src) if src else ""
                    if src_str.endswith("blackstar.png"):
                        entry[header] = "⭐"
                    else:
                        # fallback to the emoji inside td
                        entry[header] = col.text.strip()
                else:
                    entry[header] = col.text.strip()
                continue

            img_tag = col.find("img")
            if img_tag:
                src = img_tag.get("src")
                if src:
                    src_str = str(src)
                    filename = src_str.split("/")[-1]  # language-logo-256.png
                    language_name = filename.split("-")[0]  # language
                    entry[header] = language_name
                else:
                    entry[header] = ""
            else:
                entry[header] = col.text.strip()

        leaderboard_json.append(entry)

    # Save JSON
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(leaderboard_json, f, ensure_ascii=False, indent=2)

    return leaderboard_json


def json_to_text_table(leaderboard_json: list[dict]) -> list[str]:
    """Return the leaderboard as a list of formatted lines instead of a single string, with index column."""
    if not leaderboard_json:
        return ["Leaderboard konnte nicht geladen werden."]

    def fit(text: str, width: int = 24) -> str:
        """Truncate if too long, pad with spaces if too short."""
        if len(text) > width:
            return text[: width - 3] + "..."
        return text.ljust(width)

    # Header row: add "Idx" before "Rang"
    header_row = (
        f"`Idx`|`Rang`| 🙂 |`{fit('Bot')}`|`{fit('Score',6)}`|`{fit('GU',7)}`|"
        f"`{fit('CF',7)}`|`{fit('FC',7)}`|`{fit('Autor / Team')}`|`{fit('Ort')}`|`lng`"
    )
    lines = [header_row]
    spacer_line = f"`{3*'-'}`|`{4*'-'}`|-`{1*'-'}`-|`{24*'-'}`|`{6*'-'}`|`{7*'-'}`|`{7*'-'}`|`{7*'-'}`|`{24*'-'}`|`{24*'-'}`|`{3*'-'}`"
    lines.append(spacer_line)

    for idx, entry in enumerate(leaderboard_json, start=1):
        rank = entry.get("Rang", "")
        bot_emoji = entry.get("Col1", "")
        bot = entry.get("Bot", "")
        score = entry.get("Score", "")
        gu = entry.get("GU", "")
        cf = entry.get("CF", "")
        fc = entry.get("FC", "")
        author = entry.get("Autor / Team", "")
        ort = entry.get("Ort", "")
        sprache = entry.get("Sprache", "")

        sprache_emoji = language_logos.get(sprache, language_logos["noLanguage"])

        row_text = (
            f"`{idx:3}`|`{rank}`| {bot_emoji} |`{fit(bot)}`|`{fit(score,6)}`|"
            f"`{fit(gu,7)}`|`{fit(cf,7)}`|`{fit(fc,7)}`|"
            f"`{fit(author)}`|`{fit(ort)}`|{sprache_emoji}"
        )

        if rank == "DNQ.":
            row_text = f"{row_text}"

        lines.append(row_text)

    return lines


def get_leaderboard_json() -> tuple[list[dict], datetime.date | None]:
    url = "https://hiddengems.gymnasiumsteglitz.de/scrims"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text
    except requests.RequestException as e:
        return [{"error": f"Fehler beim Abrufen des Leaderboards: {e}"}], None

    # Extract the leaderboard date
    leaderboard_date = get_leaderboard_date(html)

    # Extract the leaderboard JSON
    leaderboard_json = parse_html_to_json(html)

    return leaderboard_json, leaderboard_date


async def send_lines_chunked(
    channel, status_msg, leaderboard_json, top_x, title: str | None = None
):
    lines = json_to_text_table(leaderboard_json)

    # Slice lines if top_x is set (keep header + spacer lines)
    if top_x:
        lines = lines[: top_x + 2]  # +2 to include header + spacer

    # Build title message
    if title:
        header = title
    else:
        header = "**Aktuelles Leaderboard**"

    if top_x:
        header += f" (Top {top_x})"

    await status_msg.edit(content=header)

    MAX_LEN = 2000
    chunk = ""
    for line in lines:
        if len(chunk) + len(line) + 1 > MAX_LEN:
            await channel.send(chunk)
            chunk = ""
        chunk += line + "\n"
    if chunk:
        await channel.send(chunk)


def filter_json_tracked(leaderboard_json: list[dict]) -> list[dict]:
    tracked = get_tracked_bots()
    if not tracked:
        return []

    filtered = [
        entry
        for entry in leaderboard_json
        for bot_info in tracked.values()
        if entry.get("Bot") == bot_info["name"]
        and entry.get("Autor / Team") == bot_info["author"]
    ]
    return filtered


async def send_leaderboard(channel, top_x, force_text):
    status_msg = await channel.send("Fetching leaderboards...")

    leaderboard_json, leaderboard_date = get_leaderboard_json()

    # Format the date for the title
    if leaderboard_date:
        title = f"**Leaderboard vom {leaderboard_date.strftime('%d. %B %Y')}**"
    else:
        title = "**Aktuelles Leaderboard**"

    if force_text:
        await send_lines_chunked(channel, status_msg, leaderboard_json, top_x, title)
    else:
        await send_table_images(channel, status_msg, leaderboard_json, top_x, title)

    # Tracked bots
    leaderboard_json_tracked = filter_json_tracked(leaderboard_json)
    if leaderboard_json_tracked:
        await channel.send("**Tracked Bots**")
        if force_text:
            await send_lines_chunked(
                channel, status_msg, leaderboard_json_tracked, top_x, title
            )
        else:
            await send_table_images(
                channel, status_msg, leaderboard_json_tracked, top_x, title
            )


async def post_leaderboard_in_channels(bot, channels_to_post):
    if not channels_to_post:
        print("Keine Channels zum Posten registriert.")
        return

    for channel_id in list(channels_to_post):
        channel = bot.get_channel(channel_id)
        if not isinstance(channel, TextChannel):
            print(f"Channel {channel_id} ist kein TextChannel oder nicht gefunden.")
            continue

        await send_leaderboard(channel, None, False)
