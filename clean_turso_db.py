#!/usr/bin/env python3
"""
Delete all products from Turso database
Clean slate for fresh scraping
"""

import os
from dotenv import load_dotenv
from turso_http_client import TursoTrendingDB

# Load environment
load_dotenv()

def clean_database():
    """Delete all products from Turso"""

    print("=" * 70)
    print("🗑️  CLEANING TURSO DATABASE")
    print("=" * 70)
    print()

    # Initialize Turso database
    db = TursoTrendingDB(
        db_url=os.getenv('TURSO_DATABASE_URL'),
        auth_token=os.getenv('TURSO_AUTH_TOKEN')
    )

    # Get current count
    products = db.get_all_products()
    print(f"📊 Current products in database: {len(products)}")
    print()

    # Confirm deletion
    confirm = input("⚠️  Are you sure you want to DELETE ALL products? (yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ Cancelled - Database not cleaned")
        return

    print()
    print("🔥 Deleting all products from Turso...")

    # Delete all products
    sql = "DELETE FROM trending_products"
    try:
        result = db._execute_sql(sql)
        print("✅ All products deleted from Turso")
        print()

        # Verify deletion
        products_after = db.get_all_products()
        print(f"📊 Products remaining: {len(products_after)}")
        print()

        if len(products_after) == 0:
            print("✅ Database is now clean - ready for fresh scraping!")
        else:
            print(f"⚠️  Warning: {len(products_after)} products still remain")

    except Exception as e:
        print(f"❌ Error deleting products: {e}")

    print("=" * 70)

if __name__ == '__main__':
    clean_database()
