#!/usr/bin/env python3
"""
Fetch missing prices by scraping individual Amazon product pages
"""

import requests
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv
import os
from turso_http_client import TursoTrendingDB
import time

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def fetch_product_price(asin):
    """
    Scrape individual Amazon product page to get price
    
    Args:
        asin: Amazon ASIN
    
    Returns:
        Price as float or None
    """
    url = f"https://www.amazon.com/dp/{asin}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Try multiple price selectors
        price_selectors = [
            # Primary price
            'span.a-price .a-offscreen',
            'span.a-price-whole',
            '#priceblock_ourprice',
            '#priceblock_dealprice',
            '.a-price .a-offscreen',
            # Deal price
            '#priceblock_saleprice',
            # Kindle price
            '#kindle-price',
            # Used price
            '#usedPrice',
            # Buy box price
            '#buyboxSection .a-price .a-offscreen',
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.text.strip()
                # Extract price number
                price_match = __import__('re').search(r'\$?([\d,]+\.?\d*)', price_text.replace(',', ''))
                if price_match:
                    try:
                        price = float(price_match.group(1))
                        logger.info(f"✅ Found price for {asin}: ${price}")
                        return price
                    except:
                        pass
        
        logger.warning(f"⚠️ No price found for {asin}")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error fetching price for {asin}: {e}")
        return None

def update_missing_prices():
    """Update all products in Turso that have missing prices"""
    
    print("=" * 70)
    print("💰 FETCHING MISSING PRICES FROM AMAZON")
    print("=" * 70)
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
    
    # Fetch prices for each product
    updated_count = 0
    for i, product in enumerate(missing_prices, 1):
        asin = product.get('asin')
        logger.info(f"[{i}/{len(missing_prices)}] Fetching price for {asin}...")
        
        # Fetch price from Amazon
        price = fetch_product_price(asin)
        
        if price:
            # Update product in database
            product['price'] = price
            success = db.insert_or_update_product(product)
            if success:
                updated_count += 1
                logger.info(f"✅ Updated {asin} with price ${price}")
            else:
                logger.error(f"❌ Failed to update {asin}")
        else:
            logger.warning(f"⚠️ No price found for {asin}")
        
        # Rate limiting - be respectful to Amazon
        if i < len(missing_prices):
            time.sleep(2)
    
    print()
    print("=" * 70)
    print(f"✅ COMPLETE! Updated {updated_count}/{len(missing_prices)} products")
    print("=" * 70)

if __name__ == '__main__':
    update_missing_prices()
