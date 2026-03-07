#!/usr/bin/env python3
"""Test script to create trending_products table in Turso using libsql-client"""
import os
import libsql_client

DB_URL = os.getenv('TURSO_DATABASE_URL', 'libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io')
AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN', '')

async def main():
    print(f"Connecting to: {DB_URL}")
    
    client = libsql_client.create_client(
        url=DB_URL,
        auth_token=AUTH_TOKEN
    )
    
    # Create the table
    print("Creating trending_products table...")
    await client.execute("""
        CREATE TABLE IF NOT EXISTS trending_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT NOT NULL UNIQUE,
            title TEXT,
            category TEXT,
            amazon_rank INTEGER,
            price REAL,
            rating REAL,
            google_trend_score INTEGER DEFAULT 0,
            reddit_mentions INTEGER DEFAULT 0,
            youtube_views INTEGER DEFAULT 0,
            tiktok_views INTEGER DEFAULT 0,
            total_score REAL DEFAULT 0,
            discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            image TEXT,
            affiliate_link TEXT,
            reviews INTEGER DEFAULT 0,
            product_summary TEXT
        )
    """)
    print("✓ Table created")
    
    # Create indexes
    await client.execute("CREATE INDEX IF NOT EXISTS idx_asin ON trending_products(asin)")
    await client.execute("CREATE INDEX IF NOT EXISTS idx_total_score ON trending_products(total_score DESC)")
    await client.execute("CREATE INDEX IF NOT EXISTS idx_category ON trending_products(category)")
    print("✓ Indexes created")
    
    # Verify table exists
    result = await client.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trending_products'")
    print("\n✓ Table verified!")
    print("\nSchema:")
    for row in result.rows:
        print(row[0])
    
    await client.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
