#!/bin/bash
#
# Autonomous Night Work Trigger for ProductLens AI
# Triggers at 23:30 daily to start autonomous work session
#

cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api

echo "$(date '+%Y-%m-%d %H:%M:%S') - Autonomous night work triggered" >> memory/night_work.log

# Execute night work from NIGHTLY_TODOS.md
/usr/bin/python3 scripts/execute_night_work.py >> NIGHTLY_PROGRESS.md 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') - Night work execution complete" >> memory/night_work.log
