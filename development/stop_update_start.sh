#!/bin/bash

: '
Usage:

1. Navigate to the development folder:
    cd /home/ks/hosted-services/Hidden-Gems-Leaderboard-Bot/repo

2. Make the script executable (only once):
    chmod +x development/update_bot.sh

3. Run the script to update and restart the bot:
    development/update_bot.sh
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

# Pull latest changes
echo "Pulling latest changes from Git..."
cd "$REPO_DIR"
git pull origin main

# Update dependencies in case requirements.txt changed
echo "Updating Python packages..."
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r "$REPO_DIR/requirements.txt"

# Make sure log file exists
mkdir -p "$(dirname "$BOT_LOG")"
touch "$BOT_LOG"

# Restart bot in the background
echo "Starting bot..."
nohup "$VENV_DIR/bin/python" "$BOT_SCRIPT" > "$BOT_LOG" 2>&1 &

echo "Bot updated and running. Logs are in $BOT_LOG"
