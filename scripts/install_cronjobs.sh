#!/bin/bash
#
# Install cronjobs for ProductLens AI
#
# Cronjobs:
# 1. 23:30 - Start autonomous night work
# 2. 07:00 - Product scraping (Shanghai time)
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
# 30 23 * * * - Start at 23:30 daily
30 23 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/start_night_work.sh >> /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/memory/night_work.log 2>&1

# ProductLens AI - Product Scraping (7 AM Shanghai = 23:00 UTC previous day)
# Run at 23:00 UTC to scrape for Asia morning
0 23 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/cron_scrape.sh
"

# Install new crontab
echo "$new_cron" | crontab -

echo "✅ Cronjobs installed successfully!"
echo ""
echo "Installed cronjobs:"
echo "  23:30 - Autonomous night work start"
echo "  23:00 - Product scraping (7 AM Shanghai)"
echo ""
echo "View crontab: crontab -l"
echo "Edit crontab: crontab -e"
echo "Remove all: crontab -r"
