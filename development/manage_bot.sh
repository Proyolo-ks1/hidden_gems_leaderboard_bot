#!/bin/bash

: '
Usage:

1. Make executable (only once):
    chmod +x development/manage_bot.sh

2. Start bot:
    ./development/manage_bot.sh start

3. Update bot (pull latest, update deps, restart):
    ./development/manage_bot.sh update
'

# ----------------------
# Config
# ----------------------
REPO_DIR="/home/ks/hosted-services/Hidden-Gems-Leaderboard-Bot/repo"
VENV_DIR="$REPO_DIR/venv"
BOT_SCRIPT="$REPO_DIR/hidden_gems_leaderboard_bot.py"
BOT_LOG="$REPO_DIR/bot.log"
PYTHON_BIN=$(command -v python3.12)

# ----------------------
# Helper functions
# ----------------------
stop_bot() {
    local PID
    PID=$(pgrep -f "$BOT_SCRIPT")
    if [ -n "$PID" ]; then
        echo "Stopping existing bot (PID $PID)..."
        kill -TERM "$PID"
        sleep 2
    fi
}

start_bot() {
    # Create venv if missing
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating Python 3.12 venv..."
        "$PYTHON_BIN" -m venv "$VENV_DIR"
    fi

    # Ensure pip is up-to-date and install requirements
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"

    # Make sure log file exists
    mkdir -p "$(dirname "$BOT_LOG")"
    touch "$BOT_LOG"

    # Start bot in background
    echo "Starting bot..."
    nohup "$VENV_DIR/bin/python" "$BOT_SCRIPT" > "$BOT_LOG" 2>&1 &
    disown
    echo "Bot is now running in the background. Logs are in $BOT_LOG"
}

update_bot() {
    echo "Fetching latest changes and overwriting local changes..."
    cd "$REPO_DIR" || exit 1
    git fetch origin main || { echo "Git fetch failed"; exit 1; }
    git reset --hard origin/main || { echo "Git reset failed"; exit 1; }

    echo "Updating Python packages..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"
}

# ----------------------
# Main
# ----------------------
case "$1" in
    start)
        stop_bot
        start_bot
        ;;
    update)
        stop_bot
        update_bot
        start_bot
        ;;
    *)
        echo "Usage: $0 {start|update}"
        exit 1
        ;;
esac
