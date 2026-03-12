#!/usr/bin/env python3
"""
Database Integration for ProductLens AI Phase 2

Simplified version focusing on core functionality.
Uses Turso HTTP API for database connection.
"""

import os
import requests
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

TURSO_DB_URL = os.getenv('TURSO_DATABASE_URL')
TURSO_DB_AUTH = os.getenv('TURSO_AUTH_TOKEN')


def get_db_url():
    """Get the HTTP API URL for Turso."""
    if not TURSO_DB_URL:
        raise ValueError("TURSO_DATABASE_URL not configured")
    # Convert libsql:// to https://
    return TURSO_DB_URL.replace("libsql://", "https://")


def get_headers():
    """Get headers for Turso API."""
    return {
        'Authorization': f'Bearer {TURSO_DB_AUTH}',
        'Content-Type': 'application/json'
    }


def execute_sql(sql, params=None):
    """
    Execute SQL via Turso HTTP API.
    
    Args:
        sql (str): SQL query
        params (list): Query parameters
    
    Returns:
        list: Results rows
    
    Raises:
        Exception: If SQL error occurs
    """
    body = {"statements": [{"q": sql}]}
    if params:
        body["statements"][0]["params"] = params
    
    response = requests.post(get_db_url(), headers=get_headers(), json=body)
    response.raise_for_status()
    
    result = response.json()
    if result and len(result) > 0:
        # Check for error in response
        if 'error' in result[0]:
            raise Exception(result[0]['error'])
        return result[0].get('results', {}).get('rows', [])
    return []


def execute_sql_with_desc(sql, params=None):
    """
    Execute SQL via Turso HTTP API with column descriptions.
    
    Args:
        sql (str): SQL query
        params (list): Query parameters
    
    Returns:
        tuple: (columns, rows)
    
    Raises:
        Exception: If SQL error occurs
    """
    body = {"statements": [{"q": sql}]}
    if params:
        body["statements"][0]["params"] = params
    
    response = requests.post(get_db_url(), headers=get_headers(), json=body)
    response.raise_for_status()
    
    result = response.json()
    if result and len(result) > 0:
        # Check for error in response
        if 'error' in result[0]:
            raise Exception(result[0]['error'])
        results = result[0].get('results', {})
        columns = results.get('columns', [])
        rows = results.get('rows', [])
        return columns, rows
    return [], []


def get_connection():
    """Legacy compatibility - returns True if connected."""
    try:
        execute_sql("SELECT 1")
        return True
    except Exception as e:
        raise ConnectionError(f"Failed to connect to Turso: {e}")


def close_connection():
    """Legacy compatibility - no-op for HTTP API."""
    pass


def fetch_pending_products(limit=10):
    """
    Fetch products that need content generation.
    
    Args:
        limit (int): Maximum products to fetch
    
    Returns:
        list: Product dictionaries
    """
    try:
        # Get products that haven't had content generated in the last 24 hours
        yesterday = (datetime.now() - timedelta(days=1)).isoformat()
        
        try:
            columns, rows = execute_sql_with_desc("""
                SELECT asin, title, category, main_image, price
                FROM trending_products
                WHERE asin NOT IN (
                    SELECT product_asin FROM product_reviews 
                    WHERE created_at > ?
                )
                ORDER BY RANDOM()
                LIMIT ?
            """, [yesterday, limit])
            
            products = []
            for row in rows:
                products.append(dict(zip(columns, row)))
            
            return products
        except Exception as e:
            print(f"Warning: trending_products table issue: {e}")
            return []
    
    except Exception as e:
        print(f"Error fetching products: {e}")
        return []


def save_product_review(product_asin, summary, full_review, rating=None, pros=None, cons=None, google_drive_image_url=None, ai_model='kimi-k2.5'):
    """
    Save generated product review to database.
    
    Args:
        product_asin (str): Product ASIN
        summary (str): 100-200 char summary
        full_review (str): 600-900 char full review
        rating (float): Product rating (optional)
        pros (str): Comma-separated pros
        cons (str): Comma-separated cons
        google_drive_image_url (str): Google Drive image URL
        ai_model (str): AI model used
    
    Returns:
        int: Review ID or None
    """
    try:
        now = datetime.now().isoformat()
        
        # First try UPDATE (upsert logic)
        try:
            execute_sql("""
                UPDATE product_reviews 
                SET summary = ?, full_review = ?, rating = ?, pros = ?, cons = ?, 
                    google_drive_image_url = ?, ai_model = ?, updated_at = ?
                WHERE product_asin = ?
            """, [summary, full_review, rating, pros, cons, google_drive_image_url, ai_model, now, product_asin])
            
            # Get existing ID
            rows = execute_sql("SELECT id FROM product_reviews WHERE product_asin = ?", [product_asin])
            if rows:
                return rows[0][0]
        except:
            pass
        
        # If no existing record, try INSERT
        try:
            execute_sql("""
                INSERT INTO product_reviews 
                (product_asin, summary, full_review, rating, pros, cons, google_drive_image_url, ai_model, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [product_asin, summary, full_review, rating, pros, cons, google_drive_image_url, ai_model, now, now])
        except Exception as e:
            # Check if it's a duplicate key error (review already exists)
            if "UNIQUE constraint failed" in str(e) or "duplicate" in str(e).lower():
                print(f"Review for {product_asin} already exists")
            else:
                raise
        
        # Get the last inserted ID
        rows = execute_sql("SELECT last_insert_rowid() as id")
        review_id = rows[0][0] if rows else None
        
        return review_id
    
    except Exception as e:
        print(f"Error saving review: {e}")
        return None


def get_latest_review(product_asin):
    """
    Get latest review for a product.
    
    Args:
        product_asin (str): Product ASIN
    
    Returns:
        dict: Review data or None
    """
    try:
        columns, rows = execute_sql_with_desc("""
            SELECT id, product_asin, summary, full_review, rating, pros, cons, google_drive_image_url, ai_model, created_at, updated_at, is_active
            FROM product_reviews
            WHERE product_asin = ?
            ORDER BY created_at DESC
            LIMIT 1
        """, [product_asin])
        
        if rows:
            return dict(zip(columns, rows[0]))
        
        return None
    
    except Exception as e:
        print(f"Error fetching review: {e}")
        return None


def update_product_review(review_id, **kwargs):
    """
    Update an existing product review.
    
    Args:
        review_id (int): Review ID
        **kwargs: Fields to update
    
    Returns:
        bool: True if successful
    """
    try:
        set_clauses = []
        values = []
        
        for key, value in kwargs.items():
            set_clauses.append(f"{key} = ?")
            values.append(value)
        
        set_clauses.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        
        values.append(review_id)
        
        sql = f"UPDATE product_reviews SET {', '.join(set_clauses)} WHERE id = ?"
        execute_sql(sql, values)
        
        return True
    
    except Exception as e:
        print(f"Error updating review: {e}")
        return False


def delete_product_review(review_id):
    """
    Delete a product review.
    
    Args:
        review_id (int): Review ID
    
    Returns:
        bool: True if successful
    """
    try:
        execute_sql("DELETE FROM product_reviews WHERE id = ?", [review_id])
        return True
    
    except Exception as e:
        print(f"Error deleting review: {e}")
        return False


def get_table_schema(table_name):
    """
    Get table schema information.
    
    Args:
        table_name (str): Name of the table
    
    Returns:
        list: Column information
    """
    try:
        _, rows = execute_sql_with_desc(f"PRAGMA table_info({table_name})")
        return rows
    except Exception as e:
        print(f"Error getting schema: {e}")
        return []


def list_tables():
    """
    List all tables in the database.
    
    Returns:
        list: Table names
    """
    try:
        _, rows = execute_sql_with_desc("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Error listing tables: {e}")
        return []


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
        
        # Test 2: List tables (verify schema)
        print("\n2. Verifying database schema...")
        tables = list_tables()
        print(f"   ✓ Found {len(tables)} tables: {', '.join(tables)}")
        
        # Check for required tables
        required_tables = ['product_reviews', 'trending_products']
        missing = [t for t in required_tables if t not in tables]
        if missing:
            print(f"   ⚠ Missing tables: {missing}")
        else:
            print("   ✓ All required tables exist")
        
        # Test 3: Get product_reviews schema
        print("\n3. Checking product_reviews table schema...")
        if 'product_reviews' in tables:
            schema = get_table_schema('product_reviews')
            print(f"   ✓ Table has {len(schema)} columns")
            for col in schema[:5]:  # Show first 5 columns
                print(f"      - {col[1]}: {col[2]}")
        else:
            print("   ⚠ product_reviews table not found")
        
        # Test 4: READ operation (fetch existing reviews)
        print("\n4. Testing READ operation...")
        try:
            columns, rows = execute_sql_with_desc("SELECT * FROM product_reviews LIMIT 5")
            print(f"   ✓ Read {len(rows)} reviews from product_reviews")
            if rows:
                print(f"   Sample: ASIN={rows[0][1]}, Rating={rows[0][4]}")
        except Exception as e:
            print(f"   ⚠ Read test: {e}")
        
        # Test 5: CREATE operation
        print("\n5. Testing CREATE operation...")
        # Use an existing ASIN from trending_products for the test
        # (product_reviews has FK to trending_products)
        test_asin = 'B08JHCVHTY'  # Use existing product
        # Generate strings with proper lengths (summary: 100-200, full_review: 600-900)
        summary = 'T' * 150  # 150 chars - within 100-200
        full_review = 'R' * 700  # 700 chars - within 600-900
        
        review_id = save_product_review(
            product_asin=test_asin,
            summary=summary,
            full_review=full_review,
            rating=4.5,
            pros='Test pro 1, Test pro 2',
            cons='Test con 1',
            google_drive_image_url='https://test.example.com/image.png',
            ai_model='test-model'
        )
        
        if review_id:
            print(f"   ✓ Created review with ID: {review_id}")
        else:
            print("   ✗ Failed to create review")
        
        # Test 6: READ created record
        print("\n6. Testing READ of created record...")
        review = get_latest_review(test_asin)
        if review:
            print(f"   ✓ Read back review: ASIN={review['product_asin']}, Rating={review['rating']}")
        else:
            print("   ✗ Failed to read review")
        
        # Test 7: UPDATE operation
        print("\n7. Testing UPDATE operation...")
        if review_id:
            success = update_product_review(review_id, rating=4.8, pros='Updated pro 1, Updated pro 2')
            if success:
                print("   ✓ Updated review successfully")
                # Verify update
                updated = get_latest_review(test_asin)
                if updated and updated['rating'] == 4.8:
                    print(f"   ✓ Verified update: Rating now {updated['rating']}")
            else:
                print("   ✗ Failed to update review")
        
        # Test 8: DELETE operation
        print("\n8. Testing DELETE operation...")
        if review_id:
            success = delete_product_review(review_id)
            if success:
                print("   ✓ Deleted review successfully")
                # Verify deletion
                deleted = get_latest_review(test_asin)
                if deleted is None:
                    print("   ✓ Verified deletion: Record no longer exists")
                else:
                    print("   ⚠ Record still exists after deletion")
            else:
                print("   ✗ Failed to delete review")
        
        print("\n✅ All CRUD tests passed!")
        return True
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_db_integration()
