#!/usr/bin/env python3
"""
Fetch missing prices using Scrape.do API
Scrapes individual Amazon product pages to get prices
"""

import logging
from dotenv import load_dotenv
import os
import re
from bs4 import BeautifulSoup
import time
from turso_http_client import TursoTrendingDB
from scrape_do_client import ScrapeDoClient

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fetch_product_price_with_scrape_do(asin, scrape_do_client):
    """
    Scrape individual Amazon product page using Scrape.do to get price
    
    Args:
        asin: Amazon ASIN
        scrape_do_client: ScrapeDoClient instance
    
    Returns:
        Price as float or None
    """
    url = f"https://www.amazon.com/dp/{asin}"
    
    try:
        logger.info(f"  📡 Fetching {asin} via Scrape.do...")
        html = scrape_do_client.fetch_page(url, timeout=30)  # Increase timeout to 30 seconds
        soup = BeautifulSoup(html, 'lxml')
        
        # Try multiple price selectors
        price_selectors = [
            # Primary price (most reliable)
            'span.a-price .a-offscreen',
            # Whole price part
            'span.a-price-whole',
            # Our price block
            '#priceblock_ourprice',
            # Deal price
            '#priceblock_dealprice',
            # Sale price
            '#priceblock_saleprice',
            # Buy box price
            '#buyboxSection .a-price .a-offscreen',
            # Kindle price
            '#kindle-price',
            # Used price
            '#usedPrice',
            # Mobile price
            '#mobilePrice',
            # Price inside deal
            '#dealprice',
            # Alternate price
            '.a-price.a-text-price span',
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract price number - handle formats like $19.99, £19.99, 19,99
                price_match = re.search(r'[\$£€]?([\d,]+\.?\d*)', price_text.replace(',', ''))
                if price_match:
                    try:
                        price = float(price_match.group(1))
                        # Sanity check: price should be between $1 and $10,000
                        if 1 <= price <= 10000:
                            logger.info(f"  ✅ Found price for {asin}: ${price:.2f}")
                            return price
                        else:
                            logger.warning(f"  ⚠️ Price ${price:.2f} out of reasonable range for {asin}")
                    except ValueError:
                        pass
        
        logger.warning(f"  ⚠️ No price found for {asin}")
        return None
        
    except Exception as e:
        logger.error(f"  ❌ Error fetching price for {asin}: {e}")
        return None

def update_missing_prices():
    """Update all products in Turso that have missing prices using Scrape.do"""
    
    print("=" * 70)
    print("💰 FETCHING MISSING PRICES FROM AMAZON (via Scrape.do)")
    print("=" * 70)
    print()
    
    # Check for Scrape.do API key
    scrape_do_api_key = os.getenv('SCRAPE_DO_API_KEY')
    if not scrape_do_api_key:
        logger.error("❌ SCRAPE_DO_API_KEY not found in environment")
        logger.error("Please add it to your .env file:")
        logger.error("SCRAPE_DO_API_KEY=your_api_key_here")
        return
    
    # Initialize Scrape.do client
    scrape_do_client = ScrapeDoClient(
        api_key=scrape_do_api_key,
        render_js=False,  # Disable JS for faster requests (Amazon prices usually in static HTML)
        country_code="us"
    )
    
    # Check remaining credits
    logger.info("📊 Checking Scrape.do credits...")
    credits = scrape_do_client.check_remaining_credits()
    logger.info(f"  Credits info: {credits}")
    print()
    
    # Initialize Turso database
    db = TursoTrendingDB(
        db_url=os.getenv('TURSO_DATABASE_URL'),
        auth_token=os.getenv('TURSO_AUTH_TOKEN')
    )
    
    # Get all products
    products = db.get_all_products()
    logger.info(f"📊 Total products in database: {len(products)}")
    
    # Find products with missing prices
    missing_prices = [p for p in products if not p.get('price')]
    logger.info(f"🔍 Products with missing prices: {len(missing_prices)}")
    print()
    
    if not missing_prices:
        print("✅ All products have prices!")
        return
    
    print(f"⏳ Fetching prices for {len(missing_prices)} products...")
    print("   (This may take a few minutes due to rate limiting)")
    print()
    
    # Fetch prices for each product
    updated_count = 0
    failed_count = 0
    
    for i, product in enumerate(missing_prices, 1):
        asin = product.get('asin')
        logger.info(f"[{i}/{len(missing_prices)}] Processing {asin}...")
        
        # Fetch price from Amazon using Scrape.do
        price = fetch_product_price_with_scrape_do(asin, scrape_do_client)
        
        if price:
            # Update product in database
            product['price'] = price
            success = db.insert_or_update_product(product)
            if success:
                updated_count += 1
                logger.info(f"  ✅ Updated {asin} → ${price:.2f}")
            else:
                failed_count += 1
                logger.error(f"  ❌ Failed to update {asin} in database")
        else:
            failed_count += 1
        
        # Rate limiting - be respectful to Scrape.do
        if i < len(missing_prices):
            time.sleep(1)  # 1 second between requests
    
    print()
    print("=" * 70)
    print(f"✅ COMPLETE!")
    print(f"   Updated: {updated_count}/{len(missing_prices)} products")
    print(f"   Failed:  {failed_count}/{len(missing_prices)} products")
    print("=" * 70)
    print()
    print("💡 Next steps:")
    print("   1. Refresh your local cache: python3 export_from_turso.py")
    print("   2. Check prices on: http://localhost:8080/products.html")

if __name__ == '__main__':
    update_missing_prices()
