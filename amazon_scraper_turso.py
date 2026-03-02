#!/usr/bin/env python3
"""
Amazon Scraper with Turso Cloud Database Integration
Scrapes Amazon products and saves to Turso cloud database
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import scraper and Turso client
from scraper_api import AmazonScraper, ScraperAPIError
from turso_client import TursoDatabase

# Load environment variables
load_dotenv()

# Configuration from environment or defaults
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "023fb87a622df52312bb7492013142f6")
AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "dav7aug-20")
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzI0MzMzNTMsImlkIjoiMDE5Y2FkNDEtZmUwMS03NzI4LTgyMGUtOGU1ZDBiZmJmZThjIiwicmlkIjoiYmJmZWUyMjYtZTI1NS00NmYxLThiZjktNzdiNTk3YWQ0NzA4In0.dRhrBVMddMlLt2PxrE766MRbRQE15wmtO6pNub4yxOvsr2MwjmeMTwzjINFqNUtQ4k6DW5hHBjettS3X-IVbDw")

def scrape_and_save(query: str, max_results: int = 20):
    """
    Scrape Amazon products and save to Turso database

    Args:
        query: Search query
        max_results: Maximum number of results
    """
    print("=" * 60)
    print(f"Amazon Scraper with Turso Integration")
    print("=" * 60)
    print(f"\n🔍 Query: {query}")
    print(f"📊 Max results: {max_results}")

    # Initialize Turso database
    print(f"\n📦 Connecting to Turso database...")
    try:
        db = TursoDatabase(TURSO_DATABASE_URL, TURSO_AUTH_TOKEN)
        db.create_table()
        print(f"✓ Connected to Turso")
    except Exception as e:
        print(f"✗ Failed to connect to Turso: {e}")
        return 1

    # Initialize scraper
    print(f"\n🔧 Initializing scraper...")
    try:
        scraper = AmazonScraper(
            api_key=SCRAPERAPI_KEY,
            affiliate_tag=AMAZON_AFFILIATE_TAG
        )
        print(f"✓ Scraper ready")
    except Exception as e:
        print(f"✗ Failed to initialize scraper: {e}")
        return 1

    # Scrape products
    print(f"\n📥 Scraping Amazon...")
    try:
        products = scraper.search(query, max_results=max_results)
        print(f"✓ Scraped {len(products)} products")
    except ScraperAPIError as e:
        print(f"✗ Scraping failed: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1

    if not products:
        print(f"\n⚠️  No products found")
        return 0

    # Save to Turso
    print(f"\n💾 Saving to Turso database...")
    inserted = db.insert_products_batch(products, search_query=query)
    print(f"✓ Saved {inserted}/{len(products)} products")

    # Show stats
    print(f"\n📊 Database Statistics:")
    try:
        stats = db.get_stats()
        print(f"  Total products: {stats['total_products']}")
        print(f"  Average price: ${stats.get('avg_price', 0):.2f}" if stats.get('avg_price') else "  Average price: N/A")
        print(f"\n  Products by category:")
        for category, count in stats['by_category']:
            print(f"    {category}: {count}")
    except Exception as e:
        print(f"  ⚠️  Could not fetch stats: {e}")

    # Show sample products
    print(f"\n📦 Sample products:")
    for i, product in enumerate(products[:5], 1):
        print(f"  {i}. {product.get('title', 'N/A')[:60]}...")
        print(f"     Price: ${product.get('price', 'N/A')} | Rating: {product.get('rating', 'N/A')}★")

    print("\n" + "=" * 60)
    print("✅ Scraping Complete!")
    print("=" * 60)

    return 0

def list_products(limit: int = 10):
    """
    List products from Turso database

    Args:
        limit: Maximum number of products to show
    """
    print("=" * 60)
    print("Products from Turso Database")
    print("=" * 60)

    try:
        db = TursoDatabase(TURSO_DATABASE_URL, TURSO_AUTH_TOKEN)
        products = db.get_all_products(limit=limit)

        print(f"\n📦 Showing {len(products)} products:\n")

        for i, product in enumerate(products, 1):
            print(f"{i}. {product.get('title', 'N/A')}")
            print(f"   ASIN: {product.get('asin', 'N/A')}")
            print(f"   Price: ${product.get('price', 'N/A')} | Rating: {product.get('rating', 'N/A')}★")
            print(f"   Query: {product.get('search_query', 'N/A')}")
            print()

        # Show stats
        stats = db.get_stats()
        print("=" * 60)
        print(f"Total products in database: {stats['total_products']}")
        print("=" * 60)

    except Exception as e:
        print(f"✗ Error: {e}")
        return 1

    return 0

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Amazon Scraper with Turso Integration")
    parser.add_argument("command", choices=["scrape", "list"], help="Command to run")
    parser.add_argument("--query", "-q", help="Search query for scraping", default="raspberry pi 5")
    parser.add_argument("--max", "-m", type=int, help="Maximum results", default=20)
    parser.add_argument("--limit", "-l", type=int, help="Limit for list command", default=10)

    args = parser.parse_args()

    if args.command == "scrape":
        return scrape_and_save(args.query, args.max)
    elif args.command == "list":
        return list_products(args.limit)

if __name__ == "__main__":
    sys.exit(main())
