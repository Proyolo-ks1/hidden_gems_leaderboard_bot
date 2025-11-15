#!/bin/bash

: '
Usage:

1. Navigate to the development folder:
    cd /home/ks/hosted-services/Hidden-Gems-Leaderboard-Bot/repo

2. Make the script executable (only once):
    chmod +x development/start_bot.sh

3. Run the script:
    development/start_bot.sh
'

# Paths
REPO_DIR="/home/ks/hosted-services/Hidden-Gems-Leaderboard-Bot/repo"
VENV_DIR="$REPO_DIR/venv"
BOT_SCRIPT="$REPO_DIR/hidden_gems_leaderboard_bot.py"
BOT_LOG="$REPO_DIR/bot.log"

# Stop any currently running bot
PID=$(pgrep -f "$BOT_SCRIPT")
if [ ! -z "$PID" ]; then
    echo "Stopping existing bot (PID $PID)..."
    kill $PID
    sleep 2
fi

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating Python 3.12 venv..."
    python3.12 -m venv "$VENV_DIR"
fi

# Ensure pip is up to date and install requirements
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"

# Make sure log file exists
mkdir -p "$(dirname "$BOT_LOG")"
touch "$BOT_LOG"

# Start bot in the background
echo "Starting bot..."
nohup "$VENV_DIR/bin/python" "$BOT_SCRIPT" > "$BOT_LOG" 2>&1 &

echo "Bot is now running in the background. Logs are in $BOT_LOG"
