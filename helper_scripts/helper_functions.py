# helper_scripts/helper_functions.py

# Standard library imports
import os
import json
import math
import re
from typing import Optional, Dict, Any


# Third-party imports
import discord
from PIL import Image, ImageDraw, ImageFont
from bs4 import BeautifulSoup
import datetime
import requests


# Own modules
from helper_scripts.asset_access import language_logos, get_lang_icon, get_twemoji_image
from helper_scripts.data_functions import load_bot_data
from helper_scripts.globals import BASE_DIR, LOCAL_DATA_PATH_DIR


FONTS_DIR = BASE_DIR / "fonts"
GENERATED_TABLES_DIR = LOCAL_DATA_PATH_DIR / "generated_tables"
TEXT_FONT_PATH = FONTS_DIR / "DejaVuSans.ttf"
HTML_FILE_PATH = LOCAL_DATA_PATH_DIR / "leaderboard.html"
JSON_FILE_PATH = LOCAL_DATA_PATH_DIR / "leaderboard.json"


os.makedirs(GENERATED_TABLES_DIR, exist_ok=True)


# MARK: generate_images_from_json()
def generate_images_from_json(
    leaderboard_json: list[dict], top_x: int | None = None
) -> list[str]:
    """Generate one or more PNG images from the leaderboard JSON."""

    # ----- COLORS -----
    BACKGROUND_COLOR = (21, 21, 20)
    HEADER_COLOR = (255, 200, 0)
    NORMAL_TEXT_COLOR = (231, 230, 225)
    DNQ_TEXT_COLOR = (108, 107, 105)

    # ----- LAYOUT -----
    PADDING = 5
    LINE_HEIGHT = 36
    MAX_ROWS_PER_IMAGE = 20
    TEXT_FONT = ImageFont.truetype(TEXT_FONT_PATH, 18)

    # slice top_x rows if provided
    rows = leaderboard_json[:top_x] if top_x else leaderboard_json
    total_rows = len(rows)
    num_images = math.ceil(total_rows / MAX_ROWS_PER_IMAGE)
    rows_per_image = math.ceil(total_rows / num_images)

    images = []

    for i in range(num_images):
        start_idx = i * rows_per_image
        end_idx = min(start_idx + rows_per_image, total_rows)
        chunk = rows[start_idx:end_idx]

        img_width = 1140
        img_height = PADDING * 2 + (len(chunk) + 1) * LINE_HEIGHT
        img = Image.new("RGB", (img_width, img_height), color=BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)

        # ----- HEADER -----
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
        header_titles, col_widths = zip(*columns)
        col_x = [5]
        for w in col_widths[:-1]:
            col_x.append(col_x[-1] + w)

        for col_idx, head in enumerate(header_titles):
            if col_idx != 2:  # not emoji column
                draw.text(
                    (col_x[col_idx], PADDING), head, fill=HEADER_COLOR, font=TEXT_FONT
                )

        # ----- ROWS -----
        y = PADDING + LINE_HEIGHT
        for row_idx, entry in enumerate(chunk, start=start_idx + 1):
            first_cell = entry.get("Rang")  # can use to check DNQ

            # determine text color based on rank
            text_color = DNQ_TEXT_COLOR if first_cell == "DNQ." else NORMAL_TEXT_COLOR

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
                        draw, str(val), TEXT_FONT, col_width
                    )
                    draw.text(
                        (col_x[col_idx], y),
                        val_to_draw,
                        fill=text_color,
                        font=TEXT_FONT,
                    )

            # language icon
            lang_img = get_lang_icon(sprache)
            img.paste(lang_img, (col_x[-1], y - 8), lang_img.convert("RGBA"))

            y += LINE_HEIGHT

        file_path = os.path.join(GENERATED_TABLES_DIR, f"leaderboard_part_{i + 1}.png")
        img.save(file_path)
        images.append(file_path)

    return images


# MARK: fit_text_to_column()
def fit_text_to_column(draw, text, font, max_width):
    """Truncate text and add ellipsis if it doesn't fit the column width."""
    if draw.textlength(text, font=font) <= max_width:
        return text
    while draw.textlength(text + "...", font=font) > max_width and text:
        text = text[:-1]
    return text + "..." if text else ""


# MARK: send_table_images()
async def send_table_images(
    channel, status_msg, leaderboard_json, top_x, as_thread, title: str | None = None
):
    await status_msg.edit(content="📊 Generating leaderboard images...")

    image_paths = generate_images_from_json(leaderboard_json, top_x)

    # Build header message
    header = title or "**Aktuelles Leaderboard**"
    if top_x and top_x > 0:
        header += f"\n**(Top {top_x})**"
    await status_msg.edit(content=header)

    MAX_IMAGES_BEFORE_THREAD = 1  # first N images also go in main channel

    thread: Optional[discord.Thread] = None
    thread_created = False

    # Only use thread if as_thread=True and more than 1 image
    use_thread = as_thread and len(image_paths) > 1

    # Determine thread title: first line of title
    thread_title = title.split("\n")[0] if title else "Rest der Leaderboards"

    for i, path in enumerate(image_paths):
        # Send into thread if enabled
        if use_thread:
            if not thread_created:
                thread = await status_msg.create_thread(name=thread_title)
                thread_created = True
            if thread:
                await thread.send(file=discord.File(path))

        # Always send first MAX_IMAGES_BEFORE_THREAD images in main channel
        if i < MAX_IMAGES_BEFORE_THREAD or not use_thread:
            await channel.send(file=discord.File(path))


# MARK: extract_leaderboard_meta()
def extract_leaderboard_meta(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")

    # Results
    result: Dict[str, Optional[Any]] = {
        "date": None,
        "stage": None,
        "seed": None,
    }

    # Regex for Stage #X
    stage_regex = re.compile(r"Stage\s*#\s*\d+", re.IGNORECASE)

    # Find proper columns only
    boxes = soup.find_all("div", class_="col-md-4")

    for box in boxes:
        h3 = box.find("h3")
        p = box.find("p")
        if not h3 or not p:
            continue

        title = h3.text.strip()
        value = p.text.strip()

        # --- DATE ---
        if title == "Datum":
            try:
                parsed = datetime.datetime.strptime(value, "%d. %B %Y").date()
                result["date"] = parsed
            except ValueError:
                result["date"] = None

        # --- STAGE ---
        elif stage_regex.fullmatch(title):
            # Combine the Stage number from <h3> and the name from <p>
            result["stage"] = f"{title} - {value}"

        # --- SEED ---
        elif title == "Seed":
            # Split value into the actual seed and the rest (e.g., rounds)
            if " " in value:
                seed_part, rest = value.split(" ", 1)
                result["seed"] = f"{title}: `{seed_part}` {rest}"
            else:
                result["seed"] = f"{title}: `{value}`"

    return result


# MARK: parse_html_to_json()
def parse_html_to_json(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table")
    if not table:
        return []

    # Save raw HTML
    with open(HTML_FILE_PATH, "w", encoding="utf-8") as f:
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
    with open(JSON_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(leaderboard_json, f, ensure_ascii=False, indent=2)

    return leaderboard_json


# MARK: json_to_text_table()
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


# MARK: get_leaderboard_json()
def get_leaderboard_json() -> tuple[list[dict], dict[str, Any]]:
    url = "https://hiddengems.gymnasiumsteglitz.de/scrims"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        html = response.text
    except requests.RequestException as e:
        return [{"error": f"Fehler beim Abrufen des Leaderboards: {e}"}], {}

    # Extract the leaderboard date
    leaderboard_meta = extract_leaderboard_meta(html)

    # Extract the leaderboard JSON
    leaderboard_json = parse_html_to_json(html)

    return leaderboard_json, leaderboard_meta


# MARK: send_table_texts()
async def send_table_texts(
    channel, status_msg, leaderboard_json, top_x, as_thread, title: str | None = None
):
    lines = json_to_text_table(leaderboard_json)

    # Slice lines if top_x is set (keep header + spacer lines)
    if top_x:
        lines = lines[: top_x + 2]  # +2 to include header + spacer

    # Build title message
    header = title or ""
    if top_x and top_x > 0:
        header += f"\n**(Top {top_x})**"

    await status_msg.edit(content=header)

    MAX_LEN = 2000
    chunk = ""
    messages_needed = (sum(len(line) + 1 for line in lines) // MAX_LEN) + 1
    use_thread = as_thread and messages_needed > 1

    thread: Optional[discord.Thread] = None
    thread_created = False

    for line in lines:
        if len(chunk) + len(line) + 1 > MAX_LEN:
            # Send chunk
            if use_thread:
                if not thread_created:
                    thread = await status_msg.create_thread(
                        name=title.split("\n")[0] if title else "Leaderboard"
                    )
                    thread_created = True
                if thread:
                    await thread.send(chunk)
            else:
                await channel.send(chunk)
            chunk = ""
        chunk += line + "\n"

    # Send remaining chunk
    if chunk:
        if use_thread and thread:
            await thread.send(chunk)
        else:
            await channel.send(chunk)


# MARK: filter_json_tracked()
def filter_json_tracked(
    leaderboard_json: list[dict], tracked_bots: list[dict]
) -> list[dict]:
    if not tracked_bots:
        return []

    filtered = [
        entry
        for entry in leaderboard_json
        for bot_info in tracked_bots  # just iterate the list
        if entry.get("Bot") == bot_info["name"]
        and entry.get("Autor / Team") == bot_info["author"]
    ]
    return filtered


# MARK: send_leaderboard()
async def send_leaderboard(channel, tracked_bots, top_x, force_text, as_thread):
    status_msg = await channel.send("*⌛Fetching leaderboards...*")

    leaderboard_json, leaderboard_meta = get_leaderboard_json()

    # Leaderboard

    # Format the title using metadata (date, seed, stage)
    if leaderboard_meta:
        # Date
        date_str = (
            leaderboard_meta["date"].strftime("%d. %B %Y")
            if leaderboard_meta.get("date")
            else "Unbekanntes Datum"
        )

        # Stage
        stage_str = (
            f"{leaderboard_meta['stage']}"
            if leaderboard_meta.get("stage") is not None
            else ""
        )

        # Seed
        seed_content = leaderboard_meta.get("seed", "")
        seed_raw = seed_content.split("`")[1] if "`" in seed_content else seed_content
        seed_str = (
            f"{seed_content}\n-# Command:\n```ruby\nruby runner.rb --seed {seed_raw} --profile [/pfad/zu/deinem/bot]\n```"
            if seed_content
            else ""
        )

        title = f"# Leaderboard vom {date_str}\n-# {stage_str}\n-# {seed_str}"
    else:
        title = "# Aktuelles Leaderboard"

    if force_text:
        await send_table_texts(
            channel=channel,
            status_msg=status_msg,
            leaderboard_json=leaderboard_json,
            top_x=top_x,
            as_thread=True,
            title=title,
        )
    else:
        await send_table_images(
            channel=channel,
            status_msg=status_msg,
            leaderboard_json=leaderboard_json,
            top_x=top_x,
            as_thread=True,
            title=title,
        )

    # Tracked bots
    if tracked_bots and len(tracked_bots) > 0:
        status_msg = await channel.send(f"*⌛Extracting data of tracked Bots...*")
        title = "**Tracked Bots**"
        leaderboard_json_tracked = filter_json_tracked(leaderboard_json, tracked_bots)
        if leaderboard_json_tracked and len(leaderboard_json_tracked) > 0:
            if force_text:
                await send_table_texts(
                    channel=channel,
                    status_msg=status_msg,
                    leaderboard_json=leaderboard_json_tracked,
                    top_x=0,
                    as_thread=False,
                    title=title,
                )
            else:
                await send_table_images(
                    channel=channel,
                    status_msg=status_msg,
                    leaderboard_json=leaderboard_json_tracked,
                    top_x=0,
                    as_thread=False,
                    title=title,
                )


# MARK: post_lb_in_scheduled_channels()
async def post_lb_in_scheduled_channels(bot):
    data = load_bot_data()
    guilds = data.get("guild_data", {})

    if not guilds:
        print("Keine Guild-Daten gefunden.")
        return

    # Loop through all guilds/DMs
    for guild_id, g_data in guilds.items():
        scheduled_channels = g_data.get("scheduled_channels", [])
        tracked_bots = g_data.get("tracked_bots", [])

        if not scheduled_channels:
            continue

        for channel_id in scheduled_channels:
            channel = bot.get_channel(int(channel_id))

            if channel is None:
                print(f"Channel {channel_id} nicht gefunden.")
                continue

            # DM or guild both fine (TextChannel, Thread, DMChannel)
            await send_leaderboard(
                channel,
                tracked_bots=tracked_bots,
                top_x=0,
                force_text=False,
                as_thread=True,
            )
