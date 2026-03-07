#!/usr/bin/env python3
"""Test script to create trending_products table in Turso"""
import sys
sys.path.insert(0, '/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api')

from turso_http_client import TursoTrendingDB

# Initialize with environment variables
db = TursoTrendingDB()

# Create the table
print("Creating trending_products table...")
db.create_table()

# Verify by querying table schema
print("\nVerifying table exists...")
result = db._execute_sql("SELECT sql FROM sqlite_master WHERE type='table' AND name='trending_products'")
schema = result[0].get('results', {}).get('rows', [])
if schema:
    print("\n✓ Table created successfully!")
    print("\nSchema:")
    print(schema[0][0])
else:
    print("✗ Table not found")
