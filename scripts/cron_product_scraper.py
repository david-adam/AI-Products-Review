#!/usr/bin/env python3
"""
Cron wrapper for daily product scraping.
Runs trend_scraper.py and handles logging, error notifications, and last scrape tracking.
"""

import os
import sys
import subprocess
import json
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.dirname(SCRIPT_DIR)
SCRAPER_DIR = WORKSPACE_DIR
MEMORY_DIR = os.path.join(WORKSPACE_DIR, "memory")
LOG_FILE = os.path.join(MEMORY_DIR, "scrape.log")
LAST_SCRAPE_FILE = os.path.join(MEMORY_DIR, "last_scrape.json")
CRON_LOG_FILE = os.path.join(MEMORY_DIR, "cron_scrape.log")

# Ensure memory directory exists
os.makedirs(MEMORY_DIR, exist_ok=True)

# Setup logging with rotation
def setup_logging():
    """Configure logging with rotation."""
    logger = logging.getLogger("cron_scraper")
    logger.setLevel(logging.INFO)
    
    # Rotating handler: 5MB max per file, keep 5 backup files
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Also log to stdout for cron
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def load_last_scrape():
    """Load last scrape timestamp."""
    if os.path.exists(LAST_SCRAPE_FILE):
        try:
            with open(LAST_SCRAPE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_scrape": None, "status": "never"}


def save_last_scrape(success, error_msg=None):
    """Save last scrape timestamp and status."""
    data = {
        "last_scrape": datetime.now().isoformat(),
        "status": "success" if success else "failed",
        "error": error_msg
    }
    with open(LAST_SCRAPE_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    return data


def send_notification(message, is_error=False):
    """
    Send notification about scraping result.
    Uses logging as primary notification method.
    For actual notifications, integrate with iMessage, email, or webhook.
    """
    logger = logging.getLogger("cron_scraper")
    
    # Log the notification (in production, replace with actual notification)
    if is_error:
        logger.error(f"🔴 NOTIFICATION: {message}")
    else:
        logger.info(f"🟢 NOTIFICATION: {message}")
    
    # In production, add notification methods here:
    # - iMessage (using imsg skill)
    # - Email
    # - Discord/Slack webhook
    # - Push notification
    
    return True


def run_scraper():
    """Run the trend_scraper.py script."""
    logger = logging.getLogger("cron_scraper")
    scraper_path = os.path.join(SCRAPER_DIR, "trend_scraper.py")
    
    logger.info("=" * 50)
    logger.info(f"Starting product scrape at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Scraper path: {scraper_path}")
    
    # Set up environment
    env = os.environ.copy()
    env['PYTHONPATH'] = SCRAPER_DIR
    
    try:
        # Run the scraper - let it output directly to stdout/stderr
        process = subprocess.Popen(
            [sys.executable, scraper_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=SCRAPER_DIR,
            env=env,
            text=True,
            bufsize=1
        )
        
        # Wait with timeout
        try:
            stdout, stderr = process.communicate(timeout=1800)  # 30 min timeout
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            error_msg = "Scraper timed out after 30 minutes"
            logger.error(error_msg)
            if stdout:
                logger.error(f"Stdout: {stdout[:1000]}")
            return False, error_msg
        
        if process.returncode == 0:
            logger.info("Scraper completed successfully")
            if stdout:
                # Log first few lines of output
                for line in stdout.split('\n')[:10]:
                    if line.strip():
                        logger.info(f"Output: {line}")
            return True, None
        else:
            error_msg = f"Scraper failed with return code {process.returncode}"
            logger.error(error_msg)
            if stderr:
                logger.error(f"Stderr: {stderr[:1000]}")
            return False, error_msg
            
    except Exception as e:
        error_msg = f"Exception running scraper: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def main():
    """Main cron job entry point."""
    logger = setup_logging()
    
    logger.info("=" * 60)
    logger.info("CRON PRODUCT SCRAPER - Starting daily scrape")
    logger.info("=" * 60)
    
    # Get previous status
    last_scrape = load_last_scrape()
    logger.info(f"Last scrape: {last_scrape.get('last_scrape', 'never')}")
    logger.info(f"Last status: {last_scrape.get('status', 'never')}")
    
    # Run the scraper
    success, error_msg = run_scraper()
    
    # Save results
    scrape_data = save_last_scrape(success, error_msg)
    
    # Send notification based on result
    if success:
        message = f"✅ Daily product scrape completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        send_notification(message, is_error=False)
        logger.info("Scraping job completed successfully")
    else:
        message = f"❌ Daily product scrape FAILED at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {error_msg}"
        send_notification(message, is_error=True)
        logger.error(f"Scraping job FAILED: {error_msg}")
    
    logger.info("=" * 60)
    logger.info("CRON PRODUCT SCRAPER - Finished")
    logger.info("=" * 60)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
