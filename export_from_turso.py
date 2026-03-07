#!/usr/bin/env python3
"""
Export products from Turso to local JSON files
For social_push.html and local development
"""

import json
from turso_http_client import TursoTrendingDB
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv()

def export_to_json():
    """Export products from Turso to JSON files"""

    print('📤 Exporting Products from Turso to JSON')
    print('=' * 70)
    print()

    # Initialize Turso database
    db = TursoTrendingDB(
        db_url=os.getenv('TURSO_DATABASE_URL'),
        auth_token=os.getenv('TURSO_AUTH_TOKEN')
    )

    # Get all products from Turso
    print('🔍 Fetching products from Turso...')
    products = db.get_all_products()

    if not products:
        print('⚠️  No products found in Turso database')
        return

    print(f'✅ Loaded {len(products)} products from Turso')
    print()

    # Export to products_with_content.json (for social_push.html)
    output_file = 'products_with_content.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f'💾 Saved {len(products)} products to {output_file}')
    print()

    # Also export as ai_generated_content.json format (backward compatible)
    ai_format = []
    for product in products:
        ai_format.append({
            'asin': product.get('asin'),
            'price': product.get('price'),
            'rating': product.get('rating'),
            'search_query': product.get('category', ''),
            'product_summary': product.get('product_summary', ''),
            'seo_title': f"{product.get('title', 'Product')} - AI Review",
            'social_post': generate_social_post(product),
            'blog_outline': generate_blog_outline(product)
        })

    ai_file = 'ai_generated_content.json'
    with open(ai_file, 'w', encoding='utf-8') as f:
        json.dump(ai_format, f, ensure_ascii=False, indent=2)

    print(f'💾 Saved {len(ai_format)} entries to {ai_file}')
    print()

    # Statistics
    print('📊 Export Statistics:')
    print(f'   Total products: {len(products)}')
    print(f'   With summaries: {sum(1 for p in products if p.get("product_summary"))}')
    print(f'   With images: {sum(1 for p in products if p.get("image"))}')
    print(f'   With affiliate links: {sum(1 for p in products if p.get("affiliate_link"))}')
    print(f'   Export time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    print('✅ Export complete!')
    print(f'📄 Local files updated:')
    print(f'   - {output_file}')
    print(f'   - {ai_file}')
    print()
    print('💡 Now you can refresh http://localhost:8080/social_push.html')

def generate_social_post(product):
    """Generate social media post for product"""
    title = product.get('title', 'Amazing Product')[:50]
    price = product.get('price', '')
    summary = product.get('product_summary', '')[:100]
    link = product.get('affiliate_link', '')

    return f"🚀 {title}\n\n{summary}...\n\n💰 Price: {price}\n\n🛒 Shop now: {link}\n\n#ProductReview #AI #SmartShopping"

def generate_blog_outline(product):
    """Generate blog outline for product"""
    title = product.get('title', 'Product')
    return [
        f"Introduction: Why {title} is Trending",
        "Key Features and Specifications",
        "Pros and Cons",
        "Who Should Buy This Product",
        "Final Verdict and Rating"
    ]

if __name__ == '__main__':
    export_to_json()
