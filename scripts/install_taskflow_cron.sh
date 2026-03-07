#!/bin/bash
#
# Install TaskFlow-based cronjobs for ProductLens AI
#

echo "Installing ProductLens AI cronjobs (TaskFlow edition)..."
echo ""

# Get current crontab
current_cron=$(crontab -l 2>/dev/null || echo "")

# Check if already installed
if echo "$current_cron" | grep -q "ProductLens AI"; then
    echo "⚠️  ProductLens AI cronjobs already installed"
    echo "To reinstall, first run: crontab -r"
    echo ""
    echo "📝 To change tonight's tasks, edit the 'Night Work' board in TaskFlow"
    exit 1
fi

# Create new crontab
new_cron="$current_cron

# ProductLens AI - TaskFlow Night Work
# Reads 'Night Work - Autonomous Tasks' board from TaskFlow
# Executes cards from '🌙 Tonight' list, moves to appropriate lists
30 23 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/start_night_work_v3.sh >> /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/memory/night_work.log 2>&1

# ProductLens AI - Product Scraping (7 AM Shanghai)
0 23 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/cron_scrape.sh
"

# Install new crontab
echo "$new_cron" | crontab -

echo "✅ Cronjobs installed successfully!"
echo ""
echo "Installed cronjobs:"
echo "  23:30 - TaskFlow night work (reads Night Work board)"
echo "  23:00 - Product scraping (7 AM Shanghai)"
echo ""
echo "📝 To manage tonight's tasks:"
echo "   1. Open TaskFlow app"
echo "   2. Go to 'Night Work - Autonomous Tasks' board"
echo "   3. Add/remove cards in '🌙 Tonight' list"
echo "   4. Use labels: P0 (must), P1 (if time), P2 (nice to have)"
echo ""
echo "View crontab: crontab -l"
echo "Edit crontab: crontab -e"
echo "Remove all: crontab -r"
echo ""
echo "🎯 The system will execute whatever tasks are in '🌙 Tonight' at 23:30!"
