#!/usr/bin/env python3
"""
ProductLens AI - Full Content Generation Pipeline

This script tests the complete Phase 2 workflow:
1. Fetch product from Turso DB
2. Generate AI review (Kimi K2.5)
3. Download Amazon product image
4. Generate optimized social image (Abacus.AI with reference)
5. Upload image to Google Drive (OAuth)
6. Save all content to database

Author: ProductLens AI
Date: March 6, 2026
"""

import os
import sys
import json
import tempfile
import base64
from datetime import datetime
from dotenv import load_dotenv

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

from google_drive_oauth import upload_to_drive
from abacus_image_gen_v2 import generate_image_with_reference
from kimi_text_gen_v2 import generate_product_review as generate_review
import turso_client

# Load environment variables
load_dotenv()

# Turso DB configuration
TURSO_DB_URL = os.getenv('TURSO_DATABASE_URL')
TURSO_DB_AUTH = os.getenv('TURSO_AUTH_TOKEN')

# Google Drive folder
GDRIVE_FOLDER_ID = '1b40voT9KBYONVIRb9ib_GyFHxQOilXO4'  # ProductLens Images folder


def get_turso_db():
    """Get a Turso database client."""
    if not TURSO_DB_URL:
        raise ValueError("TURSO_DATABASE_URL not configured in .env")
    if not TURSO_DB_AUTH:
        raise ValueError("TURSO_AUTH_TOKEN not configured in .env")
    
    return turso_client.TursoDatabase(TURSO_DB_URL, TURSO_DB_AUTH)


def fetch_product_from_db(product_id=None):
    """
    Fetch a product from Turso DB.
    
    Args:
        product_id (str): Specific product ID (optional, picks random if None)
    
    Returns:
        dict: Product data
    """
    db = get_turso_db()
    
    if product_id:
        result = db._execute_sql("""
            SELECT id, asin, title, category, image, price, features, rating
            FROM products
            WHERE id = ?
        """, (product_id,))
    else:
        # Get a random product with an image
        result = db._execute_sql("""
            SELECT id, asin, title, category, image, price, features, rating
            FROM products
            WHERE image IS NOT NULL AND image != ''
            ORDER BY RANDOM()
            LIMIT 1
        """)
    
    # Handle different response formats
    if isinstance(result, list):
        if not result:
            raise ValueError("No product found in database")
        rows = result[0].get('rows', []) if isinstance(result[0], dict) else result
    else:
        if not result.get('results'):
            raise ValueError("No product found in database")
        rows = result['results'][0].get('rows', [])
    
    if not rows:
        raise ValueError("No product found in database")
    
    row = rows[0]
    columns = ['id', 'asin', 'title', 'category', 'image', 'price', 'features', 'rating']
    product = dict(zip(columns, row))
    
    # Parse features JSON if needed
    if product.get('features'):
        try:
            product['features'] = json.loads(product['features']) if isinstance(product['features'], str) else product['features']
        except:
            product['features'] = []
    
    return product


def save_product_review(product_id, platform, content, image_url, aspect_ratio):
    """
    Save generated content to database.
    
    Args:
        product_id (str): Product ID
        platform (str): Social platform
        content (str): Generated review text
        image_url (str): Google Drive image URL
        aspect_ratio (str): Image aspect ratio
    """
    db = get_turso_db()
    
    # Create table if not exists
    db._execute_sql("""
        CREATE TABLE IF NOT EXISTS product_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT NOT NULL,
            aspect_ratio TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX(product_id),
            INDEX(platform)
        )
    """)
    
    # Insert review
    result = db._execute_sql("""
        INSERT INTO product_reviews (product_id, platform, content, image_url, aspect_ratio)
        VALUES (?, ?, ?, ?, ?)
    """, (product_id, platform, content, image_url, aspect_ratio))
    
    # Get the last inserted ID
    result = db._execute_sql("SELECT last_insert_rowid() as id")
    review_id = result['results'][0]['rows'][0][0]
    
    return review_id


def run_full_pipeline(product_id=None, platform='instagram'):
    """
    Run the complete content generation pipeline.
    
    Args:
        product_id (str): Specific product ID (optional)
        platform (str): Target social platform (default: instagram)
    
    Returns:
        dict: Pipeline results
    """
    print("=" * 70)
    print("PRODUCTLENS AI - FULL PIPELINE TEST")
    print("=" * 70)
    print(f"Platform: {platform}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {
        'success': False,
        'product': None,
        'steps': {}
    }
    
    try:
        # Step 1: Fetch product from DB
        print("📦 Step 1: Fetching product from database...")
        product = fetch_product_from_db(product_id)
        print(f"   ✓ Product: {product['name']}")
        print(f"   ✓ Category: {product['category']}")
        print(f"   ✓ Price: ${product.get('price', 'N/A')}")
        print(f"   ✓ Image: {product['image_url'][:60]}...")
        results['product'] = product
        results['steps']['fetch_product'] = True
        print()
        
        # Step 2: Generate AI review text
        print("📝 Step 2: Generating AI review (Kimi K2.5)...")
        review_result = generate_review(
            product_name=product['name'],
            product_category=product['category'],
            product_features=product.get('features', []),
            platform=platform
        )
        
        if not review_result.get('success'):
            raise Exception(f"Review generation failed: {review_result.get('error')}")
        
        review_content = review_result['content']
        print(f"   ✓ Review generated ({len(review_content)} characters)")
        print(f"   ✓ Preview: {review_content[:150]}...")
        results['steps']['generate_review'] = True
        results['review'] = review_content
        print()
        
        # Step 3: Generate optimized social image
        print("🎨 Step 3: Generating social image (Abacus.AI)...")
        image_result = generate_image_with_reference(
            product_image_url=product['image_url'],
            platform=platform,
            product_name=product['name'],
            product_category=product['category']
        )
        
        if not image_result.get('success'):
            raise Exception(f"Image generation failed: {image_result.get('error')}")
        
        # Decode and save image to temp file
        image_data = image_result['image_data']
        aspect_ratio = image_result['aspect_ratio']
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(base64.b64decode(image_data))
            temp_image_path = tmp.name
        
        print(f"   ✓ Image generated ({aspect_ratio} aspect ratio)")
        print(f"   ✓ Saved to: {temp_image_path}")
        print(f"   ✓ Size: {os.path.getsize(temp_image_path)} bytes")
        results['steps']['generate_image'] = True
        print()
        
        # Step 4: Upload to Google Drive
        print("☁️  Step 4: Uploading to Google Drive...")
        drive_result = upload_to_drive(
            temp_image_path,
            folder_id=GDRIVE_FOLDER_ID,
            file_name=f"{product['name']} - {platform}.png"
        )
        
        if not drive_result.get('file_id'):
            raise Exception("Google Drive upload failed")
        
        public_url = drive_result['direct_url']
        view_url = drive_result['view_url']
        
        print(f"   ✓ Uploaded successfully")
        print(f"   ✓ Public URL: {public_url}")
        print(f"   ✓ View URL: {view_url}")
        results['steps']['upload_drive'] = True
        results['image_url'] = public_url
        print()
        
        # Step 5: Save to database
        print("💾 Step 5: Saving to database...")
        review_id = save_product_review(
            product_id=product['id'],
            platform=platform,
            content=review_content,
            image_url=public_url,
            aspect_ratio=aspect_ratio
        )
        
        print(f"   ✓ Saved as review ID: {review_id}")
        results['steps']['save_db'] = True
        results['review_id'] = review_id
        print()
        
        # Clean up temp file
        os.unlink(temp_image_path)
        
        # Success!
        results['success'] = True
        
        print("=" * 70)
        print("✅ PIPELINE SUCCESSFUL!")
        print("=" * 70)
        print("\nGenerated Content:")
        print(f"  Product: {product['name']}")
        print(f"  Platform: {platform}")
        print(f"  Review: {len(review_content)} chars")
        print(f"  Image: {public_url}")
        print(f"  DB Record: #{review_id}")
        
        return results
    
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        results['error'] = str(e)
        return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='ProductLens AI - Full Pipeline Test')
    parser.add_argument('--product-id', help='Specific product ID (optional)')
    parser.add_argument('--platform', default='instagram', 
                       choices=['twitter', 'instagram', 'pinterest', 'telegram'],
                       help='Target social platform')
    
    args = parser.parse_args()
    
    # Run pipeline
    results = run_full_pipeline(
        product_id=args.product_id,
        platform=args.platform
    )
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)
