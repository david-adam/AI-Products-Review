#!/usr/bin/env python3
"""
Database Schema Verification Script
Verifies all 5 Phase 2 tables are properly deployed to Turso
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.turso_schema_deploy import TursoSchemaDeploy

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

DB_URL = os.getenv('TURSO_DATABASE_URL')
AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

if not DB_URL or not AUTH_TOKEN:
    print("❌ Error: TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set")
    sys.exit(1)

print("=" * 70)
print("🔍 TURSO DATABASE SCHEMA VERIFICATION")
print("=" * 70)
print(f"\nDatabase: {DB_URL}")
print()

db = TursoSchemaDeploy(DB_URL, AUTH_TOKEN)

# Check all tables
expected_tables = [
    'product_reviews',
    'social_integrations',
    'social_posts',
    'content_generation_logs',
    'platform_validation_logs'
]

print("📋 TABLE VERIFICATION")
print("-" * 70)
tables = db.list_tables()
all_tables_exist = True

for table in expected_tables:
    exists = table in tables
    status = "✅" if exists else "❌"
    print(f"  {status} {table}")
    if not exists:
        all_tables_exist = False

print()
print("📊 INDEX VERIFICATION")
print("-" * 70)

# Expected indexes for each table
expected_indexes = {
    'product_reviews': ['idx_reviews_product_asin', 'idx_reviews_active', 'idx_reviews_created'],
    'social_integrations': ['idx_integrations_platform', 'idx_integrations_active'],
    'social_posts': ['idx_posts_product_asin', 'idx_posts_platform', 'idx_posts_status', 
                     'idx_posts_review', 'idx_posts_created_date', 'idx_posts_published'],
    'content_generation_logs': ['idx_gen_logs_date', 'idx_gen_logs_platform'],
    'platform_validation_logs': ['idx_val_logs_platform']
}

all_indexes_exist = True
for table, indexes in expected_indexes.items():
    if table in tables:
        existing_indexes = db.list_indexes(table)
        print(f"\n  {table}:")
        for idx in indexes:
            exists = idx in existing_indexes
            status = "✅" if exists else "❌"
            print(f"    {status} {idx}")
            if not exists:
                all_indexes_exist = False

print()
print("🧪 CRUD OPERATIONS TEST")
print("-" * 70)

# Test CRUD on platform_validation_logs (no FK constraints)
try:
    # Clean up
    db.execute_sql("DELETE FROM platform_validation_logs WHERE platform = 'TEST_CRUD'")
    
    # Create
    db.execute_sql(
        "INSERT INTO platform_validation_logs (platform, validation_type, is_valid) VALUES (?, ?, ?)",
        ['TEST_CRUD', 'test', 1]
    )
    print("  ✅ CREATE: platform_validation_logs")
    
    # Read
    result = db.execute_sql(
        "SELECT * FROM platform_validation_logs WHERE platform = ?",
        ['TEST_CRUD']
    )
    rows = result[0].get('results', {}).get('rows', [])
    if rows:
        print("  ✅ READ: platform_validation_logs")
    else:
        print("  ❌ READ: platform_validation_logs - No rows found")
    
    # Update
    db.execute_sql(
        "UPDATE platform_validation_logs SET api_response_code = ? WHERE platform = ?",
        [200, 'TEST_CRUD']
    )
    print("  ✅ UPDATE: platform_validation_logs")
    
    # Delete
    db.execute_sql("DELETE FROM platform_validation_logs WHERE platform = ?", ['TEST_CRUD'])
    print("  ✅ DELETE: platform_validation_logs")
    
    crud_success = True
except Exception as e:
    print(f"  ❌ CRUD test failed: {e}")
    crud_success = False

# Test CRUD on content_generation_logs (no FK constraints)
try:
    from datetime import date
    today = date.today().isoformat()
    
    # Clean up
    db.execute_sql("DELETE FROM content_generation_logs WHERE generation_date = ?", [today])
    
    # Create
    db.execute_sql(
        "INSERT INTO content_generation_logs (generation_date, content_type, generated_count) VALUES (?, ?, ?)",
        [today, 'test', 1]
    )
    print("  ✅ CREATE: content_generation_logs")
    
    # Read
    result = db.execute_sql(
        "SELECT * FROM content_generation_logs WHERE generation_date = ?",
        [today]
    )
    rows = result[0].get('results', {}).get('rows', [])
    if rows:
        print("  ✅ READ: content_generation_logs")
    else:
        print("  ❌ READ: content_generation_logs - No rows found")
    
    # Update
    db.execute_sql(
        "UPDATE content_generation_logs SET success_count = ? WHERE generation_date = ?",
        [1, today]
    )
    print("  ✅ UPDATE: content_generation_logs")
    
    # Delete
    db.execute_sql("DELETE FROM content_generation_logs WHERE generation_date = ?", [today])
    print("  ✅ DELETE: content_generation_logs")
    
except Exception as e:
    print(f"  ❌ CRUD test failed: {e}")

print()
print("=" * 70)
print("📋 SUMMARY")
print("=" * 70)

if all_tables_exist:
    print("  ✅ All 5 tables exist")
else:
    print("  ❌ Some tables are missing")

if all_indexes_exist:
    print("  ✅ All indexes exist")
else:
    print("  ❌ Some indexes are missing")

if crud_success:
    print("  ✅ CRUD operations working")
else:
    print("  ❌ CRUD operations failed")

if all_tables_exist and all_indexes_exist and crud_success:
    print()
    print("🎉 DATABASE SCHEMA DEPLOYMENT VERIFIED SUCCESSFULLY!")
    sys.exit(0)
else:
    print()
    print("⚠️  Some verification checks failed")
    sys.exit(1)
