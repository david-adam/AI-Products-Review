#!/bin/bash
#
# TaskFlow Autonomous Worker Trigger
# Checks ALL project boards for tasks in "To Do" or "In Progress"
#

# Determine which workspace to use based on board
# For now, default to ProductLens workspace
WORKSPACE="/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api"

cd "$WORKSPACE"

echo "$(date '+%Y-%m-%d %H:%M:%S') - TaskFlow autonomous worker triggered" >> memory/autonomous_work.log

# Execute autonomous worker (checks all boards)
/usr/bin/python3 scripts/taskflow_autonomous_worker.py >> AUTONOMOUS_WORK_PROGRESS.md 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') - TaskFlow autonomous worker complete" >> memory/autonomous_work.log
