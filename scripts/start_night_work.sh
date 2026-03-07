#!/bin/bash
#
# Autonomous Night Work Trigger for ProductLens AI
# Triggers at 23:30 daily to start autonomous work session
#
# Add to crontab:
# 30 23 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/start_night_work.sh
#

# Set working directory
cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api

# Log start
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting autonomous night work" >> memory/night_work.log

# Trigger OpenClaw via message or API
# This sends a message to start the autonomous work
echo "trigger_night_work" > /tmp/night_work_trigger.txt

# Update progress file
echo "" >> NIGHTLY_PROGRESS.md
echo "## 🌙 Night Work Started - $(date '+%Y-%m-%d %H:%M:%S')" >> NIGHTLY_PROGRESS.md
echo "Status: 🔄 Started via cron" >> NIGHTLY_PROGRESS.md
echo "" >> NIGHTLY_PROGRESS.md

echo "$(date '+%Y-%m-%d %H:%M:%S') - Night work trigger sent" >> memory/night_work.log
