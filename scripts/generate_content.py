#!/usr/bin/env python3
"""
ProductLens AI - Content Generation Pipeline

Main orchestration script that:
1. Scrapes Amazon products
2. Generates AI reviews (Kimi K2.5)
3. Generates social posts (Kimi K2.5)
4. Generates images (Abacus.AI)
5. Saves images to Google Drive (ProductLens folder)
6. Updates Turso database

Usage:
    python3 scripts/generate_content.py [--product-id ID] [--dry-run]
"""

import os
import sys
import json
import logging
import tempfile
import argparse
from dotenv import load_dotenv

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from kimi_text_gen import generate_product_review, generate_social_post
from abacus_image_gen_v2 import generate_image_with_reference
from google_drive import upload_to_drive, GOOGLE_DRIVE_FOLDER_ID

# Load environment variables
load_dotenv()

def process_product(product, enabled_platforms=None):
    """
    Process a single product: generate review, social posts, and images.
    
    Args:
        product (dict): Product data from Turso
        enabled_platforms (list): List of enabled social platforms
    
    Returns:
        dict: Processing results
    """
    if enabled_platforms is None:
        enabled_platforms = ['telegram']  # Default: only Telegram
    
    results = {
        'product_id': product.get('id'),
        'product_name': product.get('name'),
        'success': False,
        'review': None,
        'social_posts': {},
        'images': {},
        'errors': []
    }
    
    logger.info(f"Processing: {product.get('name')}")
    
    # Get product image URL if available
    product_image_url = product.get('image_url') or product.get('main_image')
    
    # Step 1: Generate Product Review
    logger.info("[1/4] Generating product review...")
    review_result = generate_product_review(
        product_name=product.get('name'),
        product_category=product.get('category', 'Electronics'),
        price=product.get('price', 0),
        features=product.get('features', []).split(',') if product.get('features') else [],
        description=product.get('description', '')
    )
    
    if review_result['success']:
        results['review'] = {
            'summary': review_result['summary'],
            'full': review_result['full_review']
        }
        logger.info(f"✅ Review generated ({len(review_result['summary'].split())} words summary)")
    else:
        error_msg = f"Review generation failed: {review_result.get('error')}"
        results['errors'].append(error_msg)
        logger.error(f"❌ {error_msg}")
        return results
    
    # Step 2: Generate Social Posts
    logger.info(f"[2/4] Generating social posts for: {', '.join(enabled_platforms)}")
    
    for platform in enabled_platforms:
        logger.info(f"  - {platform}...", extra={'end': ' '})
        
        post_result = generate_social_post(
            product_name=product.get('name'),
            price=product.get('price', 0),
            review_summary=review_result['summary'],
            platform=platform
        )
        
        if post_result['success']:
            results['social_posts'][platform] = {
                'text': post_result['post_text'],
                'hashtags': post_result['hashtags'],
                'image_prompt': post_result['image_prompt']
            }
            logger.info(f"✅ ({len(post_result['post_text'])} chars)")
        else:
            error_msg = f"{platform} failed: {post_result.get('error')}"
            results['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
    
    # Step 3: Generate Images
    logger.info(f"[3/4] Generating images for: {', '.join(enabled_platforms)}")
    
    for platform in enabled_platforms:
        if platform not in results['social_posts']:
            continue
        
        logger.info(f"  - {platform}...", extra={'end': ' '})
        
        # Use v2 with reference image if available, otherwise use text-only
        if product_image_url:
            image_result = generate_image_with_reference(
                product_image_url=product_image_url,
                platform=platform,
                product_name=product.get('name'),
                product_category=product.get('category', 'Electronics')
            )
        else:
            # Fallback to text-only generation (import from abacus_image_gen)
            from abacus_image_gen import generate_product_image
            image_result = generate_product_image(
                product_name=product.get('name'),
                product_category=product.get('category', 'Electronics'),
                platform=platform,
                features=product.get('features', []).split(',') if product.get('features') else []
            )
        
        if image_result['success']:
            # Save image to temp file
            try:
                import base64
                
                ext = 'png'
                with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
                    temp_path = tmp.name
                
                # Extract image data from result
                image_data = image_result.get('image_data')
                if not image_data:
                    error_msg = f"{platform} no image data in response"
                    results['errors'].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    return results
                
                # Remove data URL prefix if present
                if image_data.startswith('data:image/'):
                    image_data = image_data.split(',', 1)[1]
                
                # Save to temp file
                with open(temp_path, 'wb') as f:
                    f.write(base64.b64decode(image_data))
                
                logger.info(f"Image saved to temp: {temp_path}")
                
            except Exception as e:
                error_msg = f"{platform} image save failed: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
                continue
            
            # Upload to Google Drive (ProductLens folder by default)
            try:
                filename = f"{product.get('id')}-{platform}.{ext}"
                drive_result = upload_to_drive(
                    temp_path, 
                    folder_id=GOOGLE_DRIVE_FOLDER_ID,  # Use ProductLens folder
                    file_name=filename
                )
                
                if drive_result:
                    results['images'][platform] = {
                        'direct_url': drive_result['direct_url'],
                        'view_url': drive_result['view_url'],
                        'public_url': drive_result['public_url'],
                        'file_id': drive_result['file_id']
                    }
                    logger.info(f"✅ Uploaded to ProductLens Drive folder")
                else:
                    error_msg = f"{platform} image upload failed (retries exhausted)"
                    results['errors'].append(error_msg)
                    logger.error(f"❌ {error_msg}")
                    
            except Exception as e:
                error_msg = f"{platform} image upload error: {str(e)}"
                results['errors'].append(error_msg)
                logger.error(f"❌ {error_msg}")
            
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Could not clean up temp file: {e}")
                
        else:
            error_msg = f"{platform} image generation failed: {image_result.get('error')}"
            results['errors'].append(error_msg)
            logger.error(f"❌ {error_msg}")
    
    # Step 4: Save to Database
    logger.info("[4/4] Saving to database...")
    
    # TODO: Implement Turso database update
    # save_to_turso(results)
    
    logger.info("✅ Database update (TODO)")
    
    results['success'] = len(results['errors']) == 0
    
    return results


def get_products_from_turso(limit=10):
    """
    Fetch products from Turso database.
    
    Args:
        limit (int): Number of products to fetch
    
    Returns:
        list: List of product dicts
    """
    # TODO: Implement Turso query
    # For now, return sample data
    return [
        {
            'id': 1,
            'name': 'Logitech MX Master 3S Wireless Mouse',
            'category': 'Electronics > Computer Accessories',
            'price': 99.99,
            'features': 'Ergonomic design,Silent clicks,Multi-device,USB-C,8K DPI',
            'description': 'The ultimate wireless mouse with advanced ergonomics.',
            'link': 'https://amazon.com/dp/B0B...'
        }
    ]


def main():
    parser = argparse.ArgumentParser(description='Generate AI content for products')
    parser.add_argument('--product-id', type=int, help='Process specific product ID')
    parser.add_argument('--dry-run', action='store_true', help='Generate content without saving to database')
    parser.add_argument('--platforms', nargs='+', default=['telegram'], 
                        help='Social platforms to generate for (telegram, pinterest, twitter, instagram)')
    
    args = parser.parse_args()
    
    print("="*60)
    print("ProductLens AI - Content Generation Pipeline")
    print("="*60)
    print(f"Mode: {'DRY RUN' if args.dry_run else 'LIVE'}")
    print(f"Platforms: {', '.join(args.platforms)}")
    
    # Fetch products
    if args.product_id:
        print(f"\nFetching product {args.product_id}...")
        products = [p for p in get_products_from_turso() if p['id'] == args.product_id]
    else:
        print(f"\nFetching products...")
        products = get_products_from_turso(limit=5)
    
    if not products:
        print("❌ No products found!")
        return
    
    print(f"✅ Found {len(products)} product(s)")
    
    # Process each product
    all_results = []
    
    for product in products:
        result = process_product(product, enabled_platforms=args.platforms)
        all_results.append(result)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    success_count = sum(1 for r in all_results if r['success'])
    total_errors = sum(len(r['errors']) for r in all_results)
    
    print(f"✅ Successful: {success_count}/{len(all_results)}")
    print(f"❌ Errors: {total_errors}")
    
    if args.dry_run:
        print("\n⚠️ DRY RUN MODE - No changes saved to database")
    
    # Save results to file for review
    output_file = 'content_generation_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
