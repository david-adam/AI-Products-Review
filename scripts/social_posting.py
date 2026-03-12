#!/usr/bin/env python3
"""
Social Media Auto-Posting Script for ProductLens AI

This script handles automatic posting of products to social media platforms.
Currently supports:
- Telegram (✅ configured)

Coming soon:
- Pinterest (⏳ blocked - API key coming)
- Twitter/X (❌ not configured)
- Instagram (❌ not configured)
- LinkedIn (❌ not configured)

Usage:
    python social_posting.py                    # Post to all configured platforms
    python social_posting.py --platform telegram # Post to specific platform
    python social_posting.py --dry-run           # Preview without posting
    python social_posting.py --test              # Test platform connections

Content types:
- review: New product reviews
- deal: Best deals / hot deals
- top_rated: Top rated products

Cron example (daily at 10am):
    0 10 * * * cd /path/to/scraper_api && python scripts/social_posting.py >> logs/social_posting.log 2>&1
"""

import os
import sys
import argparse
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import database functions
try:
    from db_integration_simple import (
        execute_sql, execute_sql_with_desc, 
        get_latest_review, fetch_pending_products
    )
except ImportError:
    print("Warning: Could not import db_integration_simple")
    execute_sql = None

# Import platform modules
from social_platforms import (
    TelegramPoster,
    PinterestPoster,
    TwitterPoster,
    InstagramPoster,
    LinkedInPoster,
    PLATFORM_STATUS
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/social_posting.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Configuration
# ============================================================================

POST_LIMIT = int(os.getenv('DAILY_POST_LIMIT', '5'))
POST_TIMEZONE = os.getenv('POST_TIMEZONE', 'Asia/Shanghai')


# ============================================================================
# Database Functions
# ============================================================================

def get_products_for_posting(limit: int = POST_LIMIT, content_type: str = 'review') -> List[Dict]:
    """
    Get products ready for social posting.
    
    Args:
        limit: Max products to fetch
        content_type: Type of content ('review', 'deal', 'top_rated')
        
    Returns:
        List of product dictionaries
    """
    if not execute_sql:
        logger.error("Database not available")
        return []
        
    try:
        if content_type == 'deal':
            # Get products with good prices (potential deals)
            columns, rows = execute_sql_with_desc("""
                SELECT asin, title, category, image, price, rating, 
                       reviews, affiliate_link
                FROM trending_products
                WHERE price IS NOT NULL 
                  AND price != ''
                  AND CAST(replace(replace(price, '$', ''), ',', '') AS REAL) < 100
                ORDER BY RANDOM()
                LIMIT ?
            """, [limit])
            
        elif content_type == 'top_rated':
            # Get top rated products
            columns, rows = execute_sql_with_desc("""
                SELECT asin, title, category, image, price, rating, 
                       reviews, affiliate_link
                FROM trending_products
                WHERE rating >= 4.5 
                  AND reviews >= 100
                ORDER BY rating DESC, reviews DESC
                LIMIT ?
            """, [limit])
            
        else:
            # Get products with reviews (new reviews)
            columns, rows = execute_sql_with_desc("""
                SELECT tp.asin, tp.title, tp.category, tp.image, tp.price, 
                       tp.rating, tp.reviews, tp.affiliate_link,
                       pr.summary, pr.full_review
                FROM trending_products tp
                LEFT JOIN product_reviews pr ON tp.asin = pr.product_asin
                WHERE pr.id IS NOT NULL
                  AND pr.is_active = 1
                  AND tp.asin NOT IN (
                      SELECT product_asin FROM social_posts 
                      WHERE platform = 'telegram' 
                        AND DATE(created_at) = DATE('now')
                  )
                ORDER BY pr.created_at DESC
                LIMIT ?
            """, [limit])
            
        products = []
        for row in rows:
            product = dict(zip(columns, row))
            # Normalize field names (use actual column names)
            product['image'] = product.get('image')
            product['reviews'] = product.get('reviews')
            product['rating_float'] = product.get('rating')
            products.append(product)
            
        return products
        
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        return []


def record_post(product_asin: str, platform: str, post_type: str,
                 content: str, status: str, message_id: str = None,
                 message_url: str = None, error: str = None,
                 image_url: str = None) -> Optional[int]:
    """
    Record a social post in the database.
    
    Args:
        product_asin: Product ASIN
        platform: Platform name
        post_type: Type of post
        content: Post content
        status: Post status
        message_id: Platform message ID
        message_url: Platform message URL
        error: Error message if failed
        image_url: Image URL used
        
    Returns:
        Post ID or None
    """
    if not execute_sql:
        return None
        
    try:
        now = datetime.now().isoformat()
        
        # Get review ID if exists
        review_rows = execute_sql("SELECT id FROM product_reviews WHERE product_asin = ?", [product_asin])
        review_id = review_rows[0][0] if review_rows else None
        
        execute_sql("""
            INSERT INTO social_posts 
            (product_asin, review_id, platform, content_text, post_type, 
             image_url, telegram_message_id, telegram_message_url, status, 
             published_at, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            product_asin, review_id, platform, content, post_type,
            image_url, message_id, message_url, status,
            now if status == 'published' else None, error,
            now, now
        ])
        
        # Get inserted ID
        rows = execute_sql("SELECT last_insert_rowid()")
        post_id = rows[0][0] if rows else None
        
        logger.info(f"Recorded post {post_id} for {product_asin} on {platform}")
        return post_id
        
    except Exception as e:
        logger.error(f"Error recording post: {e}")
        return None


def get_daily_post_count(platform: str = 'telegram') -> int:
    """Get number of posts today."""
    if not execute_sql:
        return 0
        
    try:
        rows = execute_sql("""
            SELECT COUNT(*) FROM social_posts 
            WHERE platform = ? 
              AND DATE(created_at) = DATE('now')
              AND status = 'published'
        """, [platform])
        
        return rows[0][0] if rows else 0
        
    except Exception as e:
        logger.error(f"Error getting post count: {e}")
        return 0


# ============================================================================
# Posting Functions
# ============================================================================

def post_to_platform(platform_name: str, products: List[Dict], 
                     post_type: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Post products to a specific platform.
    
    Args:
        platform_name: Platform to post to
        products: List of products
        post_type: Type of post
        dry_run: If True, don't actually post
        
    Returns:
        Summary dict
    """
    result = {
        'platform': platform_name,
        'posted': 0,
        'failed': 0,
        'skipped': 0,
        'errors': []
    }
    
    # Get poster based on platform
    if platform_name == 'telegram':
        poster = TelegramPoster()
        # Check if channel is configured (skip for dry-run)
        if not dry_run and (not poster.channel_id or poster.channel_id == '@your_channel'):
            result['errors'].append("Telegram channel not configured. Add TELEGRAM_CHANNEL_ID to .env")
            result['skipped'] = len(products)
            logger.warning("Telegram channel not configured - set TELEGRAM_CHANNEL_ID in .env")
            return result
    elif platform_name == 'pinterest':
        poster = PinterestPoster()
    elif platform_name == 'twitter':
        poster = TwitterPoster()
    elif platform_name == 'instagram':
        poster = InstagramPoster()
    elif platform_name == 'linkedin':
        poster = LinkedInPoster()
    else:
        result['errors'].append(f"Unknown platform: {platform_name}")
        return result
    
    # Check if platform is available
    if not poster.is_configured() if hasattr(poster, 'is_configured') else True:
        if platform_name != 'telegram':
            result['errors'].append(f"{platform_name} is not configured")
            result['skipped'] = len(products)
            return result
    
    # Test connection for Telegram
    if platform_name == 'telegram':
        if not poster.test_connection():
            result['errors'].append("Telegram connection test failed")
            return result
    
    # Post each product
    for product in products:
        try:
            content = poster.format_product_post(product, post_type)
            image_url = product.get('image') or product.get('main_image')
            
            if dry_run:
                logger.info(f"[DRY RUN] Would post to {platform_name}: {content[:100]}...")
                result['posted'] += 1
                continue
            
            # Post to platform
            post_result = poster.post_product(product, post_type, image_url)
            
            if post_result.get('success'):
                result['posted'] += 1
                
                # Record in database
                record_post(
                    product_asin=product.get('asin'),
                    platform=platform_name,
                    post_type=post_type,
                    content=content,
                    status='published',
                    message_id=post_result.get('message_id'),
                    message_url=post_result.get('message_url'),
                    image_url=image_url
                )
                
                logger.info(f"✓ Posted {product.get('asin')} to {platform_name}")
                
            else:
                result['failed'] += 1
                error_msg = post_result.get('error', 'Unknown error')
                result['errors'].append(error_msg)
                
                # Record failed post
                record_post(
                    product_asin=product.get('asin'),
                    platform=platform_name,
                    post_type=post_type,
                    content=content,
                    status='failed',
                    error=error_msg
                )
                
                logger.error(f"✗ Failed to post {product.get('asin')}: {error_msg}")
                
        except Exception as e:
            result['failed'] += 1
            result['errors'].append(str(e))
            logger.error(f"Error posting {product.get('asin')}: {e}")
            
    return result


def run_social_posting(post_type: str = 'review', platform: str = None,
                       dry_run: bool = False, limit: int = None) -> Dict[str, Any]:
    """
    Main function to run social posting.
    
    Args:
        post_type: Type of content to post
        platform: Specific platform or None for all
        dry_run: Preview mode
        limit: Max posts to make
        
    Returns:
        Summary dict
    """
    global POST_LIMIT
    if limit:
        POST_LIMIT = limit
        
    logger.info(f"Starting social posting - type: {post_type}, platform: {platform}")
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'post_type': post_type,
        'dry_run': dry_run,
        'platforms': {}
    }
    
    # Determine platforms to post to
    platforms = [platform] if platform else ['telegram']
    
    for plat in platforms:
        # Check daily limit
        daily_count = get_daily_post_count(plat)
        remaining = POST_LIMIT - daily_count
        
        if remaining <= 0:
            logger.warning(f"Daily limit reached for {plat} ({daily_count}/{POST_LIMIT})")
            summary['platforms'][plat] = {'status': 'limit_reached', 'posted': 0}
            continue
        
        # Get products
        products = get_products_for_posting(limit=remaining, content_type=post_type)
        
        if not products:
            logger.info(f"No products available for {plat}")
            summary['platforms'][plat] = {'status': 'no_products', 'posted': 0}
            continue
            
        # Post to platform
        result = post_to_platform(plat, products, post_type, dry_run)
        summary['platforms'][plat] = result
        
    # Log summary
    total_posted = sum(p.get('posted', 0) for p in summary['platforms'].values())
    total_failed = sum(p.get('failed', 0) for p in summary['platforms'].values())
    
    logger.info(f"Social posting complete: {total_posted} posted, {total_failed} failed")
    
    return summary


def test_platforms() -> Dict[str, bool]:
    """Test all platform connections."""
    results = {}
    
    # Test Telegram
    try:
        telegram = TelegramPoster()
        results['telegram'] = telegram.test_connection()
    except Exception as e:
        logger.error(f"Telegram test error: {e}")
        results['telegram'] = False
    
    # Other platforms (not configured)
    for platform in ['pinterest', 'twitter', 'instagram', 'linkedin']:
        results[platform] = False
        
    return results


def print_platform_status():
    """Print status of all platforms."""
    print("\n" + "="*60)
    print("SOCIAL MEDIA PLATFORM STATUS")
    print("="*60)
    
    # Telegram
    print("\n📱 Telegram: ✅ CONFIGURED")
    telegram = TelegramPoster()
    if telegram.test_connection():
        info = telegram.get_channel_info()
        if info:
            print(f"   Bot: @{info.get('username', 'N/A')}")
            print(f"   Channel: {info.get('title', 'N/A')}")
    else:
        print("   ❌ Connection test failed")
    
    # Other platforms
    print("\n📌 Pinterest: ⏳ BLOCKED (API key coming)")
    print("   Reason: Waiting for API key")
    
    print("\n🐦 Twitter/X: ❌ NOT CONFIGURED")
    print("   Reason: API keys not provided")
    
    print("\n📸 Instagram: ❌ NOT CONFIGURED")
    print("   Reason: API keys not provided")
    
    print("\n💼 LinkedIn: ❌ NOT CONFIGURED")
    print("   Reason: API keys not provided")
    
    print("\n" + "="*60)
    print(f"Daily posting limit: {POST_LIMIT} posts")
    print("="*60 + "\n")


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Social Media Auto-Posting for ProductLens AI'
    )
    
    parser.add_argument(
        '--platform', '-p',
        choices=['telegram', 'pinterest', 'twitter', 'instagram', 'linkedin'],
        help='Specific platform to post to (default: all configured)'
    )
    
    parser.add_argument(
        '--type', '-t',
        choices=['review', 'deal', 'top_rated'],
        default='review',
        help='Type of content to post (default: review)'
    )
    
    parser.add_argument(
        '--dry-run', '-d',
        action='store_true',
        help='Preview posts without publishing'
    )
    
    parser.add_argument(
        '--test', 
        action='store_true',
        help='Test platform connections'
    )
    
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show platform status'
    )
    
    parser.add_argument(
        '--limit', '-l',
        type=int,
        default=POST_LIMIT,
        help=f'Number of posts to make (default: {POST_LIMIT})'
    )
    
    args = parser.parse_args()
    
    # Handle status command
    if args.status:
        print_platform_status()
        return 0
        
    # Handle test command
    if args.test:
        print("\nTesting platform connections...\n")
        results = test_platforms()
        for platform, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {platform}: {status}")
        return 0
    
    # Update limit from args
    post_limit = args.limit
    
    # Run posting
    summary = run_social_posting(
        post_type=args.type,
        platform=args.platform,
        dry_run=args.dry_run,
        limit=post_limit
    )
    
    # Print summary
    print("\n" + "="*60)
    print("POSTING SUMMARY")
    print("="*60)
    print(f"Time: {summary['timestamp']}")
    print(f"Type: {summary['post_type']}")
    print(f"Dry Run: {summary['dry_run']}")
    
    for platform, result in summary['platforms'].items():
        print(f"\n{platform.upper()}:")
        print(f"  Posted: {result.get('posted', 0)}")
        print(f"  Failed: {result.get('failed', 0)}")
        print(f"  Skipped: {result.get('skipped', 0)}")
        
        if result.get('errors'):
            print(f"  Errors:")
            for err in result['errors'][:3]:  # Show first 3 errors
                print(f"    - {err}")
    
    print("="*60 + "\n")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
