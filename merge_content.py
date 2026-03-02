#!/usr/bin/env python3
"""
Merge scraped products with AI-generated content
"""

import json
import sqlite3
from pathlib import Path

def main():
    print('🔗 Merging Products with AI Content')
    print('=' * 70)
    print()

    # Load AI-generated content
    with open('ai_generated_content.json', 'r') as f:
        ai_content = json.load(f)

    print(f'✅ Loaded {len(ai_content)} AI content entries')

    # Load products from database
    conn = sqlite3.connect('amazon_products.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM products')
    products = [dict(row) for row in cursor.fetchall()]

    print(f'✅ Loaded {len(products)} products from database')
    print()

    # Merge data
    merged = []

    for product in products:
        asin = product['asin']

        # Find matching AI content
        ai_data = next((item for item in ai_content if item['asin'] == asin), None)

        if ai_data:
            merged_product = {
                **product,
                **ai_data
            }
            merged.append(merged_product)
        else:
            print(f'⚠️  No AI content for ASIN: {asin}')

    print()
    print(f'✅ Merged {len(merged)} products')

    # Save merged data
    output_file = 'products_with_content.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f'💾 Saved to {output_file}')
    print()

    # Stats
    with_content = len([p for p in merged if p.get('product_summary')])
    with_seo = len([p for p in merged if p.get('seo_title')])
    with_social = len([p for p in merged if p.get('social_post')])
    with_blog = len([p for p in merged if p.get('blog_outline')])

    print('📊 Merge Statistics:')
    print('-' * 70)
    print(f'Product Summaries: {with_content}/{len(merged)}')
    print(f'SEO Titles: {with_seo}/{len(merged)}')
    print(f'Social Posts: {with_social}/{len(merged)}')
    print(f'Blog Outlines: {with_blog}/{len(merged)}')
    print()

    conn.close()

    print('✅ Ready to review in browser!')
    print(f'📂 Open: file://{Path.cwd() / "index.html"}')

if __name__ == '__main__':
    main()
