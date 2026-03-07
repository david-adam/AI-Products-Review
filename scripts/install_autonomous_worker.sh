#!/bin/bash
#
# Install TaskFlow Autonomous Worker Cronjobs
#

echo "Installing TaskFlow Autonomous Worker cronjobs..."
echo ""

# Get current crontab
current_cron=$(crontab -l 2>/dev/null || echo "")

# Check if already installed
if echo "$current_cron" | grep -q "TaskFlow Autonomous Worker"; then
    echo "⚠️  TaskFlow cronjobs already installed"
    echo "To reinstall, first run: crontab -r"
    echo ""
    echo "📝 To manage tasks:"
    echo "   1. Open TaskFlow app"
    echo "   2. Go to any project board (e.g., 'ProductLens AI')"
    echo "   3. Add/move cards to 'To Do' or 'In Progress'"
    echo "   4. Worker will execute them at scheduled times"
    exit 1
fi

# Create new crontab
new_cron="$current_cron

# TaskFlow Autonomous Worker
# Checks ALL project boards for cards in 'To Do' or 'In Progress'
# Can work 24/7 on any project
30 23 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/trigger_autonomous_worker.sh

# TaskFlow Autonomous Worker (Daytime check - optional)
# Uncomment to also run at 9 AM and 2 PM
# 0 9 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/trigger_autonomous_worker.sh
# 0 14 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/trigger_autonomous_worker.sh

# ProductLens AI - Product Scraping (7 AM Shanghai)
0 23 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/cron_scrape.sh
"

# Install new crontab
echo "$new_cron" | crontab -

echo "✅ Cronjobs installed successfully!"
echo ""
echo "Installed cronjobs:"
echo "  23:30 - TaskFlow autonomous worker (checks all boards)"
echo "  23:00 - Product scraping (7 AM Shanghai)"
echo ""
echo "📝 How it works:"
echo "   1. Open TaskFlow app"
echo "   2. Add cards to 'To Do' or 'In Progress' in any project board"
echo "   3. Worker executes them at 23:30 (or scheduled times)"
echo "   4. Cards move to 'Done' or 'Review' automatically"
echo ""
echo "📋 Project Boards:"
echo "   - ProductLens AI (created)"
echo "   - Add more boards for other projects as needed"
echo ""
echo "View crontab: crontab -l"
echo "Edit crontab: crontab -e"
echo "Remove all: crontab -r"
