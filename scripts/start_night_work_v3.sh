#!/bin/bash
#
# TaskFlow Night Work Trigger
# Reads from TaskFlow board and executes tasks
#

cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api

echo "$(date '+%Y-%m-%d %H:%M:%S') - TaskFlow night work triggered" >> memory/night_work.log

# Execute tasks from TaskFlow board
/usr/bin/python3 scripts/taskflow_night_work.py >> NIGHTLY_PROGRESS.md 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') - TaskFlow night work complete" >> memory/night_work.log
