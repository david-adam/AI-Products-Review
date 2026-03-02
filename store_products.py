"""
Store scraped products in database
"""
import sqlite3
import os
import sys

# Add current directory to path
sys.path.insert(0, '.')

# Load environment
from dotenv import load_dotenv
load_dotenv()

from scraper_api import AmazonScraper

api_key = os.getenv('SCRAPERAPI_API_KEY')
affiliate_tag = os.getenv('AMAZON_AFFILIATE_TAG')

print(f"API Key: {api_key[:10]}...")
print(f"Affiliate Tag: {affiliate_tag}")
print()

# Initialize scraper
scraper = AmazonScraper(api_key=api_key, affiliate_tag=affiliate_tag)

# Search for products
print("Searching for 'raspberry pi'...")
products = scraper.search("raspberry pi", max_results=3)

print(f"Found {len(products)} products\n")

# Database setup
db_path = os.getenv('DB_PATH', 'products.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Insert products into database
for p in products:
    cursor.execute('''
        INSERT OR REPLACE INTO products (asin, title, price, rating, reviews, image, affiliate_link)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (p['asin'], p['title'], p['price'], p['rating'], p['reviews'], p['image'], p['affiliate_link']))
    
    print(f"Stored: {p['title'][:50]}...")
    print(f"  ASIN: {p['asin']}")
    print(f"  Price: ${p['price']}, Rating: {p['rating']}")
    print(f"  Affiliate Link: {p['affiliate_link']}")
    print()

conn.commit()

# Verify stored products
cursor.execute('SELECT asin, title, price, affiliate_link FROM products')
rows = cursor.fetchall()
print(f"Total products in database: {len(rows)}")

conn.close()

print("\n✅ Successfully scraped and stored products in database!")
