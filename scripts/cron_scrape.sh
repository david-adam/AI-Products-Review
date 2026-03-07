#!/bin/bash
#
# Product Scraping Cron Job Wrapper
# Runs at 7 AM Shanghai time (23:00 UTC)
#

echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting product scraping" >> /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/memory/scrape.log

cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api

# Run the scraper
/usr/bin/python3 scripts/trend_scraper.py >> memory/scrape.log 2>&1

# Check exit code
if [ $? -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Scraping completed successfully" >> memory/scrape.log
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: Scraping failed" >> memory/scrape.log
    # Could add notification here
fi

echo "---" >> memory/scrape.log
