#!/usr/bin/env python3
"""
ProductLens AI - AI Pipeline Orchestration Test

Tests the AI content generation workflow WITHOUT database operations:
1. Generate AI review (Kimi K2.5)
2. Generate optimized social image (Abacus.AI with reference)
3. Upload image to Google Drive (OAuth)
4. Return complete content package

This validates that all AI components work together correctly.

Database operations will be added in a separate step after schema is defined.
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
from kimi_text_gen_v2 import generate_review

# Load environment variables
load_dotenv()

# Google Drive folder - use None to upload to root (easier for testing)
# To use a specific folder, set GDRIVE_FOLDER_ID to a valid folder ID
GDRIVE_FOLDER_ID = None  # '1b40voT9KBYONVIRb9ib_GyFHxQOilXO4'  # ProductLens Images folder


def test_ai_orchestration(product, platform='instagram'):
    """
    Test the complete AI content generation pipeline.
    
    Args:
        product (dict): Product data with keys: name, category, image_url, features
        platform (str): Target social platform (default: instagram)
    
    Returns:
        dict: Generated content package
    """
    print("=" * 70)
    print("PRODUCTLENS AI - AI PIPELINE ORCHESTRATION TEST")
    print("=" * 70)
    print(f"Platform: {platform}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {
        'success': False,
        'product': product,
        'platform': platform,
        'steps': {}
    }
    
    try:
        # Step 1: Generate AI review text
        print("📝 Step 1: Generating AI review (Kimi K2.5)...")
        print(f"   Product: {product['name']}")
        print(f"   Category: {product['category']}")
        
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
        
        # Step 2: Generate optimized social image
        print("🎨 Step 2: Generating social image (Abacus.AI)...")
        print(f"   Reference image: {product['image_url'][:60]}...")
        
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
        
        # Step 3: Upload to Google Drive
        print("☁️  Step 3: Uploading to Google Drive...")
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
        results['image_file_id'] = drive_result['file_id']
        print()
        
        # Clean up temp file
        os.unlink(temp_image_path)
        
        # Success!
        results['success'] = True
        
        print("=" * 70)
        print("✅ AI PIPELINE TEST SUCCESSFUL!")
        print("=" * 70)
        print("\nGenerated Content Package:")
        print(f"  Product: {product['name']}")
        print(f"  Platform: {platform}")
        print(f"  Review: {len(review_content)} chars")
        print(f"  Image URL: {public_url}")
        print(f"  Aspect Ratio: {aspect_ratio}")
        
        # Show full review for verification
        print("\n" + "-" * 70)
        print("FULL REVIEW TEXT:")
        print("-" * 70)
        print(review_content)
        print("-" * 70)
        
        return results
    
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        results['error'] = str(e)
        return results


if __name__ == "__main__":
    # Test product (simulating data from database)
    test_product = {
        'name': 'Apple MacBook Pro 14-inch',
        'category': 'Computers & Accessories > Laptops',
        'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=800',
        'features': [
            'M3 Pro chip',
            '18GB RAM',
            '512GB SSD',
            '14.2-inch Liquid Retina XDR display',
            'Up to 22 hours battery life'
        ]
    }
    
    # Run orchestration test
    results = test_ai_orchestration(
        product=test_product,
        platform='instagram'
    )
    
    # Save results to JSON for inspection
    with open('/tmp/ai_pipeline_test_results.json', 'w') as f:
        # Convert to JSON-serializable format
        json_results = {
            'success': results['success'],
            'product': results['product'],
            'platform': results['platform'],
            'review': results.get('review'),
            'image_url': results.get('image_url'),
            'image_file_id': results.get('image_file_id'),
            'steps': results['steps'],
            'error': results.get('error')
        }
        json.dump(json_results, f, indent=2)
    
    print(f"\n📄 Results saved to: /tmp/ai_pipeline_test_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)
