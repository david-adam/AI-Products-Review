#!/usr/bin/env python3
"""
Amazon Scraper with Scrape.do + Turso Integration
Uses Scrape.do (free tier) for scraping, Turso for storage
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import modules
from universal_scraper import UniversalAmazonScraper
from turso_client import TursoDatabase

# Load environment variables
load_dotenv()

# Configuration
SCRAPEDO_KEY = os.getenv("SCRAPEDO_KEY", "6cfa3633393f495992593d5102b680f02419464a0ec")
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "023fb87a622df52312bb7492013142f6")
AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "dav7aug-20")
TURSO_DATABASE_URL = os.getenv("TURSO_DATABASE_URL", "libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io")
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzI0MzMzNTMsImlkIjoiMDE5Y2FkNDEtZmUwMS03NzI4LTgyMGUtOGU1ZDBiZmJmZThjIiwicmlkIjoiYmJmZWUyMjYtZTI1NS00NmYxLThiZjktNzdiNTk3YWQ0NzA4In0.dRhrBVMddMlLt2PxrE766MRbRQE15wmtO6pNub4yxOvsr2MwjmeMTwzjINFqNUtQ4k6DW5hHBjettS3X-IVbDw")

def scrape_and_save(query: str, max_results: int = 20, backend: str = "auto"):
    """
    Scrape Amazon products and save to Turso

    Args:
        query: Search query
        max_results: Maximum number of results
        backend: API backend to use ("auto", "scrapedo", "scraperapi")
    """
    print("=" * 70)
    print(f"Amazon Scraper with Scrape.do + Turso Integration")
    print("=" * 70)
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

    # Initialize scraper with auto backend selection
    print(f"\n🔧 Initializing scraper...")
    try:
        scraper = UniversalAmazonScraper(backend=backend, render_js=False)

        # Show backend info
        backend_info = scraper.get_backend_info()
        print(f"✓ Using backend: {backend_info['backend'].upper()}")
        print(f"  API: {backend_info['api']}")
        if 'free_tier' in backend_info:
            print(f"  Free tier: {backend_info['free_tier']}")
        if 'credits' in backend_info:
            print(f"  Credits: {backend_info['credits']}")

    except Exception as e:
        print(f"✗ Failed to initialize scraper: {e}")
        return 1

    # Scrape products
    print(f"\n📥 Scraping Amazon...")
    try:
        products = scraper.search(query, max_results=max_results)
        print(f"✓ Scraped {len(products)} products")
    except Exception as e:
        print(f"✗ Scraping failed: {e}")
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
        if stats.get('avg_price'):
            print(f"  Average price: ${stats['avg_price']:.2f}")
        print(f"\n  Products by category:")
        for category, count in stats['by_category']:
            print(f"    {category}: {count}")
    except Exception as e:
        print(f"  ⚠️  Could not fetch stats: {e}")

    # Show sample products
    print(f"\n📦 Sample products:")
    for i, product in enumerate(products[:5], 1):
        title = product.get('title', 'N/A')[:60]
        price = product.get('price', 'N/A')
        rating = product.get('rating', 'N/A')
        print(f"  {i}. {title}...")
        print(f"     Price: ${price} | Rating: {rating}★")

    print("\n" + "=" * 70)
    print("✅ Scraping Complete!")
    print("=" * 70)

    # Show cost information
    if backend_info['backend'] == 'scrapedo':
        print(f"\n💡 Scrape.do Usage:")
        print(f"  Free tier: 1,000 requests/month")
        print(f"  This request: 1")
        print(f"  Remaining: ~999 requests this month")

    return 0

def list_products(limit: int = 10):
    """List products from Turso database"""
    print("=" * 70)
    print("Products from Turso Database")
    print("=" * 70)

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

        stats = db.get_stats()
        print("=" * 70)
        print(f"Total products in database: {stats['total_products']}")
        print("=" * 70)

    except Exception as e:
        print(f"✗ Error: {e}")
        return 1

    return 0

def test_backend(backend: str = "auto"):
    """Test scraper backend"""
    print("=" * 70)
    print(f"Testing Backend: {backend.upper()}")
    print("=" * 70)

    try:
        scraper = UniversalAmazonScraper(backend=backend)
        info = scraper.get_backend_info()

        print(f"\n✓ Backend: {info['backend']}")
        print(f"  API: {info['api']}")
        print(f"  Render JS: {info['render_js']}")
        print(f"  Affiliate Tag: {info['affiliate_tag']}")

        if 'free_tier' in info:
            print(f"  Free Tier: {info['free_tier']}")
        if 'pricing' in info:
            print(f"  Pricing: {info['pricing']}")
        if 'credits' in info:
            print(f"  Credits: {info['credits']}")

        # Test search
        print(f"\n🔍 Testing search...")
        products = scraper.search("raspberry pi 5", max_results=3)
        print(f"✓ Found {len(products)} products")

        for p in products:
            print(f"  - {p.get('title', 'N/A')[:50]}... (${p.get('price', 'N/A')})")

        print("\n✅ Backend test passed!")
        return 0

    except Exception as e:
        print(f"\n✗ Backend test failed: {e}")
        return 1

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Amazon Scraper with Scrape.do + Turso Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape with auto backend selection
  %(prog)s scrape --query "raspberry pi 5"

  # Force Scrape.do backend (free)
  %(prog)s scrape --backend scrapedo --query "arduino kit"

  # Force ScraperAPI backend
  %(prog)s scrape --backend scraperapi --query "nvidia jetson"

  # List products from database
  %(prog)s list

  # Test backend
  %(prog)s test --backend scrapedo
        """
    )

    parser.add_argument("command", choices=["scrape", "list", "test"],
                       help="Command to run")
    parser.add_argument("--query", "-q", help="Search query for scraping",
                       default="raspberry pi 5")
    parser.add_argument("--max", "-m", type=int,
                       help="Maximum results (default: 20)", default=20)
    parser.add_argument("--limit", "-l", type=int,
                       help="Limit for list command (default: 10)", default=10)
    parser.add_argument("--backend", "-b",
                       choices=["auto", "scrapedo", "scraperapi"],
                       help="API backend to use (default: auto)", default="auto")

    args = parser.parse_args()

    if args.command == "scrape":
        return scrape_and_save(args.query, args.max, args.backend)
    elif args.command == "list":
        return list_products(args.limit)
    elif args.command == "test":
        return test_backend(args.backend)

if __name__ == "__main__":
    sys.exit(main())
