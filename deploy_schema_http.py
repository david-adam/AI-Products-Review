#!/usr/bin/env python3
"""
Database Schema Deployment Script for ProductLens AI
Uses Turso HTTP API to deploy Phase 2 tables
"""

import requests
import os
import sys
from pathlib import Path

# Configuration
TURSO_DATABASE_URL = os.getenv(
    "TURSO_DATABASE_URL", 
    "libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io"
)
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

# Paths
BASE_DIR = Path(__file__).parent
MIGRATIONS_FILE = BASE_DIR / "database" / "migrations.sql"


def execute_sql(http_url: str, headers: dict, sql: str, params: list = None) -> list:
    """Execute SQL via Turso HTTP API"""
    body = {"statements": [{"q": sql}]}
    if params:
        body["statements"][0]["args"] = params
    
    response = requests.post(http_url, headers=headers, json=body)
    response.raise_for_status()
    return response.json()


def deploy_schema():
    """Deploy the schema to Turso database"""
    
    print("=" * 60)
    print("ProductLens AI - Database Schema Deployment (HTTP API)")
    print("=" * 60)
    
    # Verify credentials
    if not TURSO_AUTH_TOKEN:
        print("❌ TURSO_AUTH_TOKEN not set")
        return False
    
    # Convert libsql:// to https://
    http_url = TURSO_DATABASE_URL.replace("libsql://", "https://")
    headers = {
        "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"📡 Database URL: {http_url}")
    print(f"🔑 Auth Token: {'*' * 10}...{TURSO_AUTH_TOKEN[-10:]}")
    
    # Read migrations file
    if not MIGRATIONS_FILE.exists():
        print(f"❌ Migrations file not found: {MIGRATIONS_FILE}")
        return False
    
    with open(MIGRATIONS_FILE, 'r') as f:
        migrations_sql = f.read()
    
    print(f"📄 Loaded migrations file: {len(migrations_sql)} characters")
    
    # Test connection
    try:
        result = execute_sql(http_url, headers, "SELECT 1")
        print(f"🔗 Connected to Turso database via HTTP API")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False
    
    # Parse and execute statements
    raw_statements = migrations_sql.split(';')
    
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for i, raw_stmt in enumerate(raw_statements):
        stmt = raw_stmt.strip()
        
        # Skip empty statements and comments-only
        if not stmt or stmt.startswith('--') or stmt.startswith('/*'):
            continue
        
        # Remove comment lines from the statement
        lines = [line for line in stmt.split('\n') if not line.strip().startswith('--')]
        stmt = '\n'.join(lines).strip()
        
        if not stmt:
            continue
        
        try:
            result = execute_sql(http_url, headers, stmt)
            
            # Parse list response: [{"results": {...}}]
            if isinstance(result, list) and len(result) > 0:
                first_result = result[0]
                if isinstance(first_result, dict):
                    if 'error' in first_result:
                        error_msg = str(first_result['error'])
                        if 'already exists' in error_msg.lower():
                            skipped_count += 1
                        else:
                            print(f"   ⚠️  Statement {i+1}: {error_msg[:80]}")
                            error_count += 1
                    else:
                        success_count += 1
                else:
                    success_count += 1
            else:
                success_count += 1
                
        except requests.exceptions.HTTPError as e:
            error_str = str(e)
            if 'already exists' in error_str.lower():
                skipped_count += 1
            else:
                print(f"   ❌ Statement {i+1} failed: {e}")
                error_count += 1
        except Exception as e:
            print(f"   ❌ Statement {i+1} error: {e}")
            error_count += 1
    
    print(f"\n📊 Deployment Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ⏭️  Skipped (already exists): {skipped_count}")
    print(f"   ❌ Errors: {error_count}")
    
    # Verify tables exist
    print("\n🔍 Verifying tables...")
    tables = [
        "product_reviews",
        "social_integrations",
        "social_posts",
        "content_generation_logs",
        "platform_validation_logs"
    ]
    
    all_exist = True
    for table in tables:
        try:
            result = execute_sql(
                http_url, headers,
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                [table]
            )
            # Parse list response
            found = False
            if isinstance(result, list) and len(result) > 0:
                first = result[0]
                if isinstance(first, dict) and 'results' in first:
                    rows = first['results'].get('rows', [])
                    if rows:
                        found = True
            
            if found:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} - NOT FOUND")
                all_exist = False
        except Exception as e:
            print(f"   ❌ {table} - ERROR: {e}")
            all_exist = False
    
    if all_exist:
        print("\n✅ Schema deployment complete! All 5 Phase 2 tables are live.")
        return True
    else:
        print("\n⚠️  Some tables may be missing. Check the output above.")
        return False


if __name__ == "__main__":
    result = deploy_schema()
    sys.exit(0 if result else 1)
