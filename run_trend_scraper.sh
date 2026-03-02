#!/bin/bash
# Cron job script for trend scraper
# Logs output to file with timestamp

LOG_DIR="/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/logs"
mkdir -p "$LOG_DIR"

LOG_FILE="$LOG_DIR/trend_scraper_$(date +%Y%m%d).log"

cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api

echo "=== Trend Scraper Run $(date) ===" >> "$LOG_FILE"
python3 trend_scraper.py >> "$LOG_FILE" 2>&1
echo "=== Completed $(date) ===" >> "$LOG_FILE"
