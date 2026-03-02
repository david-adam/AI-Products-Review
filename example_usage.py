"""
ScraperAPI Example Usage
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from scraper_api import AmazonScraper

def main():
    """Example of how to use ScraperAPI adapter"""
    
    # Initialize scraper with environment variables
    api_key = os.getenv('SCRAPERAPI_API_KEY')
    affiliate_tag = os.getenv('AMAZON_AFFILIATE_TAG', '')
    
    scraper = AmazonScraper(api_key=api_key, affiliate_tag=affiliate_tag)
    
    # Scrape Amazon Computer Components category
    print("🔍 Scraping Amazon Computer Components...\n")
    
    products = scraper.fetch_products(
        category='computer_components',
        limit=20
    )
    
    # Display results
    print(f"✅ Found {len(products)} products:\n")
    
    for i, product in enumerate(products, 1):
        print(f"{i}. {product['title']}")
        print(f"   ASIN: {product['asin']}")
        print(f"   Price: ${product['price']}")
        print(f"   Rating: {product['rating']} ⭐")
        print(f"   Sales Rank: #{product['sales_rank']}")
        print(f"   Link: {product['affiliate_link']}")
        print()
    
    # Store to database
    print("💾 Storing to database...")
    from database import ProductDatabase
    
    db = ProductDatabase(os.getenv('DB_PATH', 'products.db'))
    
    with db:
        for product in products:
            db.insert_product(product)
    
    print(f"✅ Stored {len(products)} products to {os.getenv('DB_PATH', 'products.db')}")

if __name__ == '__main__':
    main()
