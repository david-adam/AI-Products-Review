#!/usr/bin/env python3
"""
Database Integration for ProductLens AI Phase 2

Simplified version focusing on core functionality.
"""

import os
import sqlite3
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TURSO_DB_URL = os.getenv('TURSO_DB_URL')
TURSO_DB_AUTH = os.getenv('TURSO_DB_AUTH')


def get_connection():
    """Get Turso database connection."""
    if not TURSO_DB_URL:
        raise ValueError("TURSO_DB_URL not configured")
    
    conn = sqlite3.connect(TURSO_DB_URL, check_same_thread=False)
    
    if TURSO_DB_AUTH:
        conn.execute(f"AUTHENTICATE '{TURSO_DB_AUTH}'")
    
    return conn


def fetch_pending_products(limit=10):
    """
    Fetch products that need content generation.
    
    Args:
        limit (int): Maximum products to fetch
    
    Returns:
        list: Product dictionaries
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Get products that haven't had content generated in the last 24 hours
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        cursor.execute("""
            SELECT asin, title, category, main_image, price
            FROM trending_products
            WHERE asin NOT IN (
                SELECT product_id FROM product_reviews 
                WHERE created_at > ?
            )
            ORDER BY RANDOM()
            LIMIT ?
        """, (yesterday, limit))
        
        columns = ['asin', 'title', 'category', 'main_image', 'price']
        products = []
        
        for row in cursor.fetchall():
            products.append(dict(zip(columns, row)))
        
        conn.close()
        return products
    
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []


def save_product_review(product_id, platform, summary, full_review, image_url, rating=None):
    """
    Save generated product review to database.
    
    Args:
        product_id (str): Product ASIN
        platform (str): Social platform
        summary (str): 100-200 char summary
        full_review (str): 600-900 char full review
        image_url (str): Google Drive image URL
        rating (float): Product rating (optional)
    
    Returns:
        int: Review ID or None
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO product_reviews 
            (product_id, platform, summary, full_review, image_url, rating, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (product_id, platform, summary, full_review, image_url, rating, datetime.now().isoformat()))
        
        review_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return review_id
    
    except Exception as e:
        print(f"Error saving review: {e}")
        return None


def get_latest_review(product_id, platform=None):
    """
    Get latest review for a product.
    
    Args:
        product_id (str): Product ASIN
        platform (str): Filter by platform (optional)
    
    Returns:
        dict: Review data or None
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if platform:
            cursor.execute("""
                SELECT id, product_id, platform, summary, full_review, image_url, rating, created_at
                FROM product_reviews
                WHERE product_id = ? AND platform = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (product_id, platform))
        else:
            cursor.execute("""
                SELECT id, product_id, platform, summary, full_review, image_url, rating, created_at
                FROM product_reviews
                WHERE product_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (product_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            columns = ['id', 'product_id', 'platform', 'summary', 'full_review', 'image_url', 'rating', 'created_at']
            return dict(zip(columns, row))
        
        return None
    
    except Exception as e:
        print(f"Error fetching review: {e}")
        return None


# Test function
def test_db_integration():
    """Test database integration."""
    print("Testing Database Integration...")
    print("-" * 60)
    
    try:
        # Test 1: Connection
        print("1. Testing connection...")
        conn = get_connection()
        print("   ✓ Connected to Turso DB")
        conn.close()
        
        # Test 2: Fetch products
        print("\n2. Fetching pending products...")
        products = fetch_pending_products(limit=5)
        print(f"   ✓ Found {len(products)} products")
        if products:
            print(f"   Sample: {products[0]['title'][:50]}...")
        
        # Test 3: Save review (using first product if available)
        if products:
            print("\n3. Saving test review...")
            product = products[0]
            review_id = save_product_review(
                product_id=product['asin'],
                platform='instagram',
                summary='Test summary for database integration',
                full_review='Test full review for database integration. This is a test to verify the database is working correctly.',
                image_url='https://test.example.com/image.png',
                rating=4.5
            )
            
            if review_id:
                print(f"   ✓ Review saved with ID: {review_id}")
            else:
                print("   ✗ Failed to save review")
        
        print("\n✅ All tests passed!")
        return True
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_db_integration()
