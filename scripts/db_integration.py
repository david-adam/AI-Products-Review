#!/usr/bin/env python3
"""
ProductLens AI - Database Integration Script

This module provides functions to integrate the AI pipeline with Turso DB.
Handles:
- Fetching pending products for content generation
- Saving generated reviews and image URLs
- Marking products as content-generated
- Retrieving reviews

Author: ProductLens AI
Date: March 7, 2026
"""

import os
import sys
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import turso_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class DatabaseIntegration:
    """Database integration for AI content generation pipeline"""
    
    def __init__(self):
        """Initialize database connection from environment variables"""
        self.db_url = os.getenv('TURSO_DATABASE_URL')
        self.auth_token = os.getenv('TURSO_AUTH_TOKEN')
        
        if not self.db_url:
            raise ValueError("TURSO_DATABASE_URL not configured in .env")
        if not self.auth_token:
            raise ValueError("TURSO_AUTH_TOKEN not configured in .env")
        
        # Convert libsql:// to https:// for HTTP API
        self.db_url_https = self.db_url.replace("libsql://", "https://")
        self.db = turso_client.TursoDatabase(self.db_url, self.auth_token)
        
        logger.info("Database integration initialized successfully")
    
    def _execute_sql(self, sql: str, params: List = None) -> dict:
        """Execute SQL query with error handling"""
        try:
            result = self.db._execute_sql(sql, params)
            logger.debug(f"SQL executed: {sql[:100]}...")
            return result
        except Exception as e:
            logger.error(f"SQL execution error: {e}")
            raise
    
    def _ensure_tables_exist(self):
        """Ensure required tables exist in the database"""
        # Create product_reviews table if not exists
        self._execute_sql("""
            CREATE TABLE IF NOT EXISTS product_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_asin TEXT NOT NULL,
                summary TEXT NOT NULL CHECK(length(summary) >= 100 AND length(summary) <= 200),
                full_review TEXT NOT NULL CHECK(length(full_review) >= 600 AND length(full_review) <= 900),
                rating REAL DEFAULT 4.0,
                pros TEXT,
                cons TEXT,
                google_drive_image_url TEXT,
                google_drive_image_id TEXT,
                ai_model TEXT DEFAULT 'kimi-k2.5',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                CONSTRAINT unique_product_review UNIQUE(product_asin),
                FOREIGN KEY (product_asin) REFERENCES trending_products(asin) ON DELETE CASCADE
            )
        """)
        
        # Create content_generation_logs table if not exists
        self._execute_sql("""
            CREATE TABLE IF NOT EXISTS content_generation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                generation_date DATE NOT NULL,
                content_type TEXT NOT NULL,
                platform TEXT,
                generated_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failed_count INTEGER DEFAULT 0,
                ai_model TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_daily_generation UNIQUE(generation_date, content_type, platform)
            )
        """)
        
        logger.info("Database tables verified/created")
    
    def fetch_pending_products(self, limit: int = 10, category: str = None) -> List[Dict[str, Any]]:
        """
        Get products that need content generation.
        
        A pending product is one that:
        - Exists in trending_products
        - Does NOT have an entry in product_reviews for TODAY
        
        Args:
            limit: Maximum number of products to return
            category: Optional category filter
            
        Returns:
            List of product dictionaries with pending content generation
        """
        self._ensure_tables_exist()
        
        # Query to find products without any reviews (simpler approach)
        sql = """
            SELECT 
                tp.asin,
                tp.title,
                tp.category,
                tp.price,
                tp.rating,
                tp.image,
                tp.affiliate_link,
                tp.product_summary,
                tp.amazon_rank,
                tp.total_score,
                tp.discovered_date
            FROM trending_products tp
            LEFT JOIN product_reviews pr ON tp.asin = pr.product_asin 
            WHERE pr.id IS NULL
        """
        
        if category:
            sql += " AND tp.category = ?"
        
        # Note: Turso HTTP API doesn't support parameterized LIMIT, so we use int interpolation
        sql += f" ORDER BY tp.total_score DESC LIMIT {int(limit)}"
        
        try:
            params = []
            if category:
                params = [category]
            
            result = self._execute_sql(sql, params)
            
            # Handle different response formats
            if isinstance(result, list):
                if not result:
                    return []
                rows = result[0].get('rows', []) if isinstance(result[0], dict) else result
                columns = result[0].get('columns', []) if isinstance(result[0], dict) else []
            else:
                if not result.get('results'):
                    return []
                rows = result['results'][0].get('rows', [])
                columns = result['results'][0].get('columns', [])
            
            products = []
            for row in rows:
                product = dict(zip(columns, row))
                products.append(product)
            
            logger.info(f"Found {len(products)} pending products")
            return products
            
        except Exception as e:
            logger.error(f"Error fetching pending products: {e}")
            return []
    
    def save_product_review(
        self,
        product_asin: str,
        summary: str,
        full_review: str,
        rating: float = 4.0,
        pros: str = None,
        cons: str = None,
        google_drive_image_url: str = None,
        google_drive_image_id: str = None,
        ai_model: str = 'kimi-k2.5'
    ) -> Optional[int]:
        """
        Save a generated review to the database.
        
        Args:
            product_asin: Product ASIN (foreign key)
            summary: Short summary (100-200 chars)
            full_review: Full review text (600-900 chars)
            rating: AI-assigned rating (1-5)
            pros: Comma-separated pros
            cons: Comma-separated cons
            google_drive_image_url: Public URL from Google Drive
            google_drive_image_id: Google Drive file ID
            ai_model: AI model used for generation
            
        Returns:
            Review ID if successful, None if failed
        """
        self._ensure_tables_exist()
        
        # Validate summary length
        if len(summary) < 100 or len(summary) > 200:
            logger.warning(f"Summary length {len(summary)} outside 100-200 range")
        
        # Validate full_review length
        if len(full_review) < 600 or len(full_review) > 900:
            logger.warning(f"Full review length {len(full_review)} outside 600-900 range")
        
        sql = """
            INSERT OR REPLACE INTO product_reviews 
            (product_asin, summary, full_review, rating, pros, cons, 
             google_drive_image_url, google_drive_image_id, ai_model, 
             created_at, updated_at, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
        """
        
        params = [
            product_asin,
            summary,
            full_review,
            rating,
            pros,
            cons,
            google_drive_image_url,
            google_drive_image_id,
            ai_model
        ]
        
        try:
            result = self._execute_sql(sql, params)
            
            # Get the last inserted ID
            result = self._execute_sql("SELECT last_insert_rowid() as id")
            review_id = result['results'][0]['rows'][0][0]
            
            logger.info(f"Saved review for product {product_asin}, ID: {review_id}")
            return review_id
            
        except Exception as e:
            logger.error(f"Error saving product review: {e}")
            return None
    
    def mark_content_generated(
        self,
        product_asin: str,
        content_type: str = 'review',
        platform: str = None,
        success: bool = True,
        ai_model: str = 'kimi-k2.5'
    ) -> bool:
        """
        Mark a product as having content generated for the day.
        
        This logs the content generation to content_generation_logs table
        for tracking and rate limiting.
        
        Args:
            product_asin: Product ASIN
            content_type: Type of content (review, image, social_post)
            platform: Platform for social posts (optional)
            success: Whether generation was successful
            ai_model: AI model used
            
        Returns:
            True if successful
        """
        today = date.today().strftime('%Y-%m-%d')
        
        # Try to update existing record, or insert new
        sql_check = """
            SELECT id FROM content_generation_logs 
            WHERE generation_date = ? AND content_type = ?
        """
        params_check = [today, content_type]
        if platform:
            sql_check += " AND platform = ?"
            params_check.append(platform)
        
        try:
            result = self._execute_sql(sql_check, params_check)
            rows = result['results'][0]['rows'] if result.get('results') else []
            
            if rows:
                # Update existing record
                sql = """
                    UPDATE content_generation_logs 
                    SET generated_count = generated_count + 1,
                        success_count = success_count + ?,
                        failed_count = failed_count + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE generation_date = ? AND content_type = ?
                """
                params = [
                    1 if success else 0,
                    0 if success else 1,
                    today,
                    content_type
                ]
                if platform:
                    sql += " AND platform = ?"
                    params.append(platform)
            else:
                # Insert new record
                sql = """
                    INSERT INTO content_generation_logs 
                    (generation_date, content_type, platform, generated_count, 
                     success_count, failed_count, ai_model)
                    VALUES (?, ?, ?, 1, ?, ?, ?)
                """
                params = [
                    today,
                    content_type,
                    platform,
                    1 if success else 0,
                    0 if success else 1,
                    ai_model
                ]
            
            self._execute_sql(sql, params)
            logger.info(f"Marked content generated for {product_asin}: {content_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error marking content generated: {e}")
            return False
    
    def get_latest_review(self, product_asin: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest review for a specific product.
        
        Args:
            product_asin: Product ASIN
            
        Returns:
            Dictionary with review data, or None if not found
        """
        sql = """
            SELECT 
                id,
                product_asin,
                summary,
                full_review,
                rating,
                pros,
                cons,
                google_drive_image_url,
                google_drive_image_id,
                ai_model,
                created_at,
                updated_at,
                is_active
            FROM product_reviews
            WHERE product_asin = ?
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        try:
            result = self._execute_sql(sql, [product_asin])
            rows = result['results'][0]['rows'] if result.get('results') else []
            
            if not rows:
                logger.info(f"No review found for product {product_asin}")
                return None
            
            columns = result['results'][0]['columns']
            review = dict(zip(columns, rows[0]))
            
            logger.info(f"Retrieved latest review for {product_asin}")
            return review
            
        except Exception as e:
            logger.error(f"Error retrieving latest review: {e}")
            return None
    
    def get_products_for_platform(self, platform: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get products optimized for a specific social platform.
        
        Args:
            platform: Target platform (twitter, instagram, pinterest, telegram)
            limit: Maximum products to return
            
        Returns:
            List of products ready for platform-specific content
        """
        # Get pending products (same logic as fetch_pending_products)
        products = self.fetch_pending_products(limit=limit)
        
        # Add platform-specific metadata
        platform_configs = {
            'twitter': {'max_length': 280, 'aspect_ratio': '16:9'},
            'instagram': {'max_length': 2200, 'aspect_ratio': '1:1'},
            'pinterest': {'max_length': 500, 'aspect_ratio': '2:3'},
            'telegram': {'max_length': 4096, 'aspect_ratio': '16:9'}
        }
        
        config = platform_configs.get(platform, {})
        
        for product in products:
            product['_platform_config'] = config
        
        return products


def test_database_integration():
    """Test function to verify database integration works correctly."""
    print("=" * 70)
    print("DATABASE INTEGRATION TEST")
    print("=" * 70)
    
    try:
        # Test 1: Connection
        print("\n📡 Test 1: Connecting to Turso DB...")
        db = DatabaseIntegration()
        print("   ✓ Connection successful")
        
        # Test 2: Ensure tables exist
        print("\n📋 Test 2: Verifying tables...")
        db._ensure_tables_exist()
        print("   ✓ Tables verified")
        
        # Test 3: Fetch a pending product
        print("\n📦 Test 3: Fetching pending products...")
        products = db.fetch_pending_products(limit=3)
        print(f"   ✓ Found {len(products)} pending products")
        
        if products:
            test_product = products[0]
            print(f"   ✓ Sample: {test_product.get('title', 'N/A')[:50]}...")
            
            # Test 4: Save a test review
            print("\n💾 Test 4: Saving test review...")
            test_summary = "This is a test summary that meets the 100-200 character requirement. " * 3
            test_summary = test_summary[:200]  # Ensure under 200 chars
            
            test_full_review = "This is a comprehensive test review. " * 40
            test_full_review = test_full_review[:900]  # Ensure under 900 chars
            
            review_id = db.save_product_review(
                product_asin=test_product['asin'],
                summary=test_summary,
                full_review=test_full_review,
                rating=4.5,
                pros="Good quality, Fast shipping, Great price",
                cons="Limited colors, Small size",
                google_drive_image_url="https://drive.google.com/uc?id=TEST123",
                google_drive_image_id="TEST123",
                ai_model="kimi-k2.5-test"
            )
            
            if review_id:
                print(f"   ✓ Review saved with ID: {review_id}")
            else:
                print("   ✗ Failed to save review")
            
            # Test 5: Retrieve the review back
            print("\n🔍 Test 5: Retrieving latest review...")
            retrieved = db.get_latest_review(test_product['asin'])
            
            if retrieved:
                print(f"   ✓ Retrieved review:")
                print(f"      - Summary: {retrieved.get('summary', '')[:50]}...")
                print(f"      - Rating: {retrieved.get('rating')}")
                print(f"      - Image URL: {retrieved.get('google_drive_image_url', 'N/A')}")
            else:
                print("   ✗ Failed to retrieve review")
            
            # Test 6: Mark content as generated
            print("\n✅ Test 6: Marking content generated...")
            marked = db.mark_content_generated(
                product_asin=test_product['asin'],
                content_type='review',
                success=True,
                ai_model='kimi-k2.5-test'
            )
            
            if marked:
                print("   ✓ Content generation logged")
            else:
                print("   ✗ Failed to log content generation")
        
        else:
            print("   ⚠ No pending products found (database may be empty)")
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETED")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


# Convenience functions for direct module usage
def fetch_pending_products(limit: int = 10, category: str = None) -> List[Dict[str, Any]]:
    """Fetch products needing content generation"""
    db = DatabaseIntegration()
    return db.fetch_pending_products(limit=limit, category=category)


def save_product_review(
    product_asin: str,
    summary: str,
    full_review: str,
    rating: float = 4.0,
    pros: str = None,
    cons: str = None,
    google_drive_image_url: str = None,
    google_drive_image_id: str = None,
    ai_model: str = 'kimi-k2.5'
) -> Optional[int]:
    """Save a generated review to database"""
    db = DatabaseIntegration()
    return db.save_product_review(
        product_asin=product_asin,
        summary=summary,
        full_review=full_review,
        rating=rating,
        pros=pros,
        cons=cons,
        google_drive_image_url=google_drive_image_url,
        google_drive_image_id=google_drive_image_id,
        ai_model=ai_model
    )


def mark_content_generated(
    product_asin: str,
    content_type: str = 'review',
    platform: str = None,
    success: bool = True,
    ai_model: str = 'kimi-k2.5'
) -> bool:
    """Mark product as having content generated"""
    db = DatabaseIntegration()
    return db.mark_content_generated(
        product_asin=product_asin,
        content_type=content_type,
        platform=platform,
        success=success,
        ai_model=ai_model
    )


def get_latest_review(product_asin: str) -> Optional[Dict[str, Any]]:
    """Get the latest review for a product"""
    db = DatabaseIntegration()
    return db.get_latest_review(product_asin)


if __name__ == "__main__":
    # Run tests when script is executed directly
    test_database_integration()
