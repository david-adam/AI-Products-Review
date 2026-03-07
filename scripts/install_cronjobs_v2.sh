#!/bin/bash
#
# Install cronjobs for ProductLens AI
#
# Cronjobs:
# 1. 23:30 - Start autonomous night work (reads from NIGHTLY_TODOS.md)
# 2. 23:00 UTC - Product scraping (7 AM Shanghai)
#

echo "Installing ProductLens AI cronjobs..."
echo ""

# Get current crontab
current_cron=$(crontab -l 2>/dev/null || echo "")

# Check if already installed
if echo "$current_cron" | grep -q "ProductLens AI"; then
    echo "⚠️  ProductLens AI cronjobs already installed"
    echo "To reinstall, first run: crontab -r"
    exit 1
fi

# Create new crontab
new_cron="$current_cron

# ProductLens AI - Autonomous Night Work
# Reads NIGHTLY_TODOS.md and executes pending tasks dynamically
30 23 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/start_night_work_v2.sh >> /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/memory/night_work.log 2>&1

# ProductLens AI - Product Scraping (7 AM Shanghai)
0 23 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/cron_scrape.sh
"

# Install new crontab
echo "$new_cron" | crontab -

echo "✅ Cronjobs installed successfully!"
echo ""
echo "Installed cronjobs:"
echo "  23:30 - Autonomous night work (reads NIGHTLY_TODOS.md)"
echo "  23:00 - Product scraping (7 AM Shanghai)"
echo ""
echo "📝 To change tonight's tasks, edit NIGHTLY_TODOS.md"
echo ""
echo "View crontab: crontab -l"
echo "Edit crontab: crontab -e"
echo "Remove all: crontab -r"
