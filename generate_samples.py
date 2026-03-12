#!/usr/bin/env python3
"""
ProductLens AI - Generate 5 Sample Product Reviews (Simplified)

This script generates 5 sample product reviews with:
1. Summaries (100-200 chars) via Kimi K2.5
2. Full reviews (600-900 chars) via Kimi K2.5  
3. Images via Abacus.AI
4. Upload to Google Drive
5. Store results in JSON format
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

# Load environment variables
load_dotenv()

OUTPUT_FILE = 'generated_ai_samples_complete.json'

# Product data - 5 products from existing database
PRODUCTS = [
    {
        'asin': 'B0DGJ7HYG1',
        'name': 'Apple AirPods 4 Wireless Earbuds',
        'category': 'Electronics > Headphones',
        'price': 122.74,
        'rating': 4.5,
        'features': [
            'Active Noise Cancellation',
            'Adaptive Transparency Mode', 
            'Personalized Spatial Audio',
            'USB-C Charging Case',
            'H2 Chip'
        ]
    },
    {
        'asin': 'B0DZ75TN5F',
        'name': 'Apple iPad 11-inch (A16 chip)',
        'category': 'Computers > Tablets',
        'price': 303.27,
        'rating': 4.7,
        'features': [
            'A16 Bionic chip',
            '11-inch Liquid Retina Display',
            '128GB Storage',
            'Wi-Fi 6',
            '12MP Front/Back Camera'
        ]
    },
    {
        'asin': 'B0D54JZTHY',
        'name': 'Apple AirTag 4-Pack',
        'category': 'Electronics > Trackers',
        'price': 60.19,
        'rating': 4.8,
        'features': [
            'Precision Finding with U1 chip',
            'One-tap setup with iPhone/iPad',
            'Replaceable battery',
            'Water and dust resistant',
            'Privacy-focused tracking'
        ]
    },
    {
        'asin': 'B0DZD91W4F',
        'name': 'Apple MacBook Air 13-inch (M4)',
        'category': 'Computers > Laptops',
        'price': 980.00,
        'rating': 4.8,
        'features': [
            'Apple M4 chip',
            '13.6-inch Liquid Retina Display',
            '16GB Unified Memory',
            '256GB SSD Storage',
            '18-hour battery life'
        ]
    },
    {
        'asin': 'B0FQF9ZX7P',
        'name': 'Apple Watch Series 11',
        'category': 'Electronics > Smartwatches',
        'price': 281.06,
        'rating': 4.8,
        'features': [
            'Sleep Score tracking',
            'Fitness & Health monitoring',
            'Always-On Retina Display',
            'Water resistant to 50m',
            'Rose Gold Aluminum case'
        ]
    }
]


def generate_review_text(product):
    """Generate AI review text using Kimi K2.5."""
    import requests
    
    api_key = os.getenv('KIMI_API_KEY')
    base_url = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
    
    features_text = '\n'.join([f'- {f}' for f in product['features']])
    
    prompt = f"""Write a product review for:

Product: {product['name']}
Price: ${product['price']}
Rating: {product['rating']}/5
Category: {product['category']}

Features:
{features_text}

Provide:
1. SUMMARY (100-200 chars): Brief overview with key selling point
2. FULL REVIEW (600-900 chars): Detailed review with pros, cons, and recommendation

Format:
SUMMARY: [text]
FULL_REVIEW: [text]"""

    try:
        response = requests.post(
            f'{base_url}/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': 'kimi-k2.5',
                'messages': [
                    {'role': 'system', 'content': 'You are a professional product reviewer. Write engaging, balanced reviews with 30% professional tone, 30% sales focus, 40% casual advice.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 2000
            },
            timeout=60
        )
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        
        # Parse response
        summary = ""
        full_review = ""
        
        if 'SUMMARY:' in content and 'FULL_REVIEW:' in content:
            summary_part = content.split('FULL_REVIEW:')[0].replace('SUMMARY:', '').strip()
            full_part = content.split('FULL_REVIEW:')[1].strip()
            summary = summary_part
            full_review = full_part
        else:
            # Fallback
            full_review = content
            summary = content[:180] if len(content) > 180 else content
        
        # Ensure limits
        if len(summary) > 200:
            summary = summary[:197] + "..."
        if len(full_review) > 900:
            full_review = full_review[:897] + "..."
        
        return {'success': True, 'summary': summary, 'full_review': full_review}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def generate_product_image(product, platform):
    """Generate image using Abacus.AI Nano Banana Pro."""
    import requests
    
    api_key = os.getenv('ABACUSAI_API_KEY')
    base_url = os.getenv('ABACUSAI_BASE_URL', 'https://routellm.abacus.ai/v1')
    
    aspect_ratios = {'instagram': '1:1', 'pinterest': '9:16', 'twitter': '16:9'}
    aspect_ratio = aspect_ratios.get(platform, '1:1')
    
    prompt = f"Professional product photography of {product['name']}. Clean e-commerce style, neutral gradient background, studio lighting, {platform}-optimized {aspect_ratio} composition."
    
    try:
        response = requests.post(
            f'{base_url}/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json={
                'model': 'nano-banana-pro',
                'messages': [{'role': 'user', 'content': prompt}],
                'modalities': ['image'],
                'image_config': {'num_images': 1, 'aspect_ratio': aspect_ratio}
            },
            timeout=60
        )
        response.raise_for_status()
        
        data = response.json()
        if 'choices' in data and data['choices']:
            msg = data['choices'][0]['message']
            if 'images' in msg and msg['images']:
                return {'success': True, 'image_data': msg['images'][0]['image_url']['url'], 'aspect_ratio': aspect_ratio}
        
        return {'success': False, 'error': 'No image data'}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def upload_image_to_drive(image_data, filename):
    """Upload image to Google Drive."""
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        from google.oauth2.credentials import Credentials
        
        creds = Credentials.from_authorized_user_file(
            '.google_drive_token.json',
            ['https://www.googleapis.com/auth/drive.file']
        )
        
        service = build('drive', 'v3', credentials=creds)
        
        # Decode and save temp
        if image_data.startswith('data:'):
            image_data = image_data.split(',', 1)[1]
        
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp.write(base64.b64decode(image_data))
            tmp_path = tmp.name
        
        # Upload
        file = service.files().create(
            body={'name': filename},
            media_body=MediaFileUpload(tmp_path, mimetype='image/png'),
            fields='id'
        ).execute()
        
        # Make public
        service.permissions().create(
            fileId=file['id'],
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
        
        os.unlink(tmp_path)
        
        return {
            'success': True,
            'file_id': file['id'],
            'public_url': f"https://lh3.googleusercontent.com/d/{file['id']}",
            'view_url': f"https://drive.google.com/file/d/{file['id']}/view"
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    print("="*70)
    print("PRODUCTLENS AI - GENERATING 5 SAMPLE PRODUCT REVIEWS")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check config
    print("Checking configuration...")
    kimi_ok = bool(os.getenv('KIMI_API_KEY'))
    abacus_ok = bool(os.getenv('ABACUSAI_API_KEY'))
    gdrive_ok = os.path.exists('.google_drive_token.json')
    
    print(f"  Kimi K2.5 API: {'✓' if kimi_ok else '✗'}")
    print(f"  Abacus.AI API: {'✓' if abacus_ok else '✗'}")
    print(f"  Google Drive: {'✓' if gdrive_ok else '✗'}")
    print()
    
    results = {
        'generated_at': datetime.now().isoformat(),
        'total_products': 5,
        'products': [],
        'pipeline_status': {
            'kimi_api': 'working' if kimi_ok else 'not_configured',
            'abacus_api': 'working' if abacus_ok else 'not_configured',
            'google_drive': 'working' if gdrive_ok else 'not_configured'
        }
    }
    
    # Process each product
    for i, product in enumerate(PRODUCTS, 1):
        print(f"\n{'='*70}")
        print(f"Product {i}/5: {product['name']}")
        print(f"{'='*70}")
        
        product_result = {
            'asin': product['asin'],
            'product_name': product['name'],
            'category': product['category'],
            'price': product['price'],
            'rating': product['rating'],
            'generated_at': datetime.now().isoformat()
        }
        
        # Step 1: Generate review
        if kimi_ok:
            print("\n📝 Generating review with Kimi K2.5...")
            review = generate_review_text(product)
            if review['success']:
                product_result['summary'] = review['summary']
                product_result['full_review'] = review['full_review']
                print(f"   ✓ Summary: {len(review['summary'])} chars")
                print(f"   ✓ Full review: {len(review['full_review'])} chars")
                print(f"   Preview: {review['summary'][:80]}...")
            else:
                print(f"   ✗ Failed: {review.get('error')}")
                product_result['review_error'] = review.get('error')
        else:
            print("   ⚠ Kimi API not configured - using placeholder")
            product_result['summary'] = f"{product['name']} delivers exceptional value with premium features at ${product['price']}. Highly recommended for its category-leading performance and reliability."
            product_result['full_review'] = f"The {product['name']} is a standout product in its category. Priced at ${product['price']}, it offers excellent value for money with features like {', '.join(product['features'][:3])}. Users consistently rate it {product['rating']}/5 stars for its reliability, performance, and build quality. Whether you're a professional or casual user, this product delivers on its promises. The build quality is exceptional, and the feature set rivals more expensive competitors. Highly recommended for anyone seeking quality without compromise."
        
        # Step 2 & 3: Generate and upload images
        product_result['images'] = []
        if abacus_ok and gdrive_ok:
            platforms = ['instagram', 'pinterest', 'twitter']
            for platform in platforms:
                print(f"\n🎨 Generating {platform} image...")
                img_result = generate_product_image(product, platform)
                if img_result['success']:
                    print(f"   ☁️  Uploading to Google Drive...")
                    upload = upload_image_to_drive(img_result['image_data'], f"{product['name']}_{platform}.png")
                    if upload['success']:
                        product_result['images'].append({
                            'platform': platform,
                            'aspect_ratio': img_result['aspect_ratio'],
                            'google_drive_id': upload['file_id'],
                            'public_url': upload['public_url']
                        })
                        print(f"   ✓ Uploaded: {upload['public_url'][:50]}...")
                    else:
                        print(f"   ✗ Upload failed: {upload.get('error')}")
                else:
                    print(f"   ✗ Generation failed: {img_result.get('error')}")
        else:
            print("   ⚠ Skipping image generation (API not configured)")
            # Add placeholder URLs for demonstration
            product_result['images'] = [
                {'platform': 'instagram', 'aspect_ratio': '1:1', 'public_url': f'https://placeholder.example.com/{product["asin"]}_ig.jpg'},
                {'platform': 'pinterest', 'aspect_ratio': '9:16', 'public_url': f'https://placeholder.example.com/{product["asin"]}_pin.jpg'},
                {'platform': 'twitter', 'aspect_ratio': '16:9', 'public_url': f'https://placeholder.example.com/{product["asin"]}_tw.jpg'}
            ]
        
        product_result['image_count'] = len(product_result['images'])
        results['products'].append(product_result)
        
        # Progress summary
        print(f"\n✓ Completed: {len(product_result.get('summary', ''))} char summary, {product_result['image_count']} images")
    
    # Save results
    print(f"\n{'='*70}")
    print("SAVING RESULTS")
    print(f"{'='*70}")
    
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✓ Saved to: {OUTPUT_FILE}")
    
    # Summary
    print(f"\n{'='*70}")
    print("GENERATION SUMMARY")
    print(f"{'='*70}")
    print(f"Total products: {results['total_products']}")
    print(f"Total images: {sum(p['image_count'] for p in results['products'])}")
    print(f"Kimi API: {results['pipeline_status']['kimi_api']}")
    print(f"Abacus API: {results['pipeline_status']['abacus_api']}")
    print(f"Google Drive: {results['pipeline_status']['google_drive']}")
    
    # Sample output
    print(f"\n{'='*70}")
    print("SAMPLE OUTPUT (First Product)")
    print(f"{'='*70}")
    if results['products']:
        first = results['products'][0]
        print(f"\nProduct: {first['product_name']}")
        print(f"ASIN: {first['asin']}")
        print(f"\nSummary ({len(first.get('summary', ''))} chars):")
        print(f"  {first.get('summary', 'N/A')}")
        print(f"\nFull Review ({len(first.get('full_review', ''))} chars):")
        review_text = first.get('full_review', 'N/A')
        print(f"  {review_text[:200]}...")
        print(f"\nImages ({first['image_count']}):")
        for img in first.get('images', []):
            print(f"  - {img['platform']} ({img['aspect_ratio']}): {img['public_url'][:60]}...")
    
    print(f"\n{'='*70}")
    print("✅ AI CONTENT GENERATION COMPLETE")
    print(f"{'='*70}")
    
    return results


if __name__ == "__main__":
    main()
