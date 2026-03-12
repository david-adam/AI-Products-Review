#!/usr/bin/env python3
"""
Deploy ProductLens AI Phase 2 Schema to Turso
"""

import requests
import sys

# Turso configuration
TURSO_URL = "libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io"
TURSO_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzI0MzMzNTMsImlkIjoiMDE5Y2FkNDEtZmUwMS03NzI4LTgyMGUtOGU1ZDBiZmJmZThjIiwicmlkIjoiYmJmZWUyMjYtZTI1NS00NmYxLThiZjktNzdiNTk3YWQ0NzA4In0.dRhrBVMddMlLt2PxrE766MRbRQE15wmtO6pNub4yxOvsr2MwjmeMTwzjINFqNUtQ4k6DW5hHBjettS3X-IVbDw"

HTTP_URL = TURSO_URL.replace("libsql://", "https://")
HEADERS = {
    "Authorization": f"Bearer {TURSO_TOKEN}",
    "Content-Type": "application/json"
}

# Read schema from file
with open('database/migrations.sql', 'r') as f:
    SCHEMA_SQL = f.read()


def execute_sql(sql: str) -> list:
    """Execute SQL via Turso HTTP API"""
    # Split into individual statements
    statements = []
    for stmt in sql.split(';'):
        stmt = stmt.strip()
        if stmt and not stmt.startswith('--'):
            statements.append({"q": stmt})
    
    # Execute in batches of 10
    results = []
    for i in range(0, len(statements), 10):
        batch = statements[i:i+10]
        body = {"statements": batch}
        
        response = requests.post(HTTP_URL, headers=HEADERS, json=body)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
        
        results.extend(response.json())
    
    return results


def deploy_schema():
    """Deploy the full schema"""
    print("=" * 70)
    print("ProductLens AI Phase 2 Schema Deployment")
    print("=" * 70)
    print(f"Turso URL: {TURSO_URL}")
    print("=" * 70)
    
    # Parse and execute schema
    statements = []
    current_stmt = ""
    
    for line in SCHEMA_SQL.split('\n'):
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('--'):
            continue
        
        current_stmt += " " + line
        
        if line.endswith(';'):
            stmt = current_stmt.strip()
            if stmt:
                statements.append(stmt)
            current_stmt = ""
    
    print(f"\nDeploying {len(statements)} SQL statements...\n")
    
    success_count = 0
    error_count = 0
    
    for i, stmt in enumerate(statements, 1):
        stmt_type = stmt.split()[0].upper()
        
        body = {"statements": [{"q": stmt}]}
        response = requests.post(HTTP_URL, headers=HEADERS, json=body)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                if 'error' in result[0]:
                    error = result[0]['error']
                    # Ignore "already exists" errors
                    if 'already exists' in str(error).lower():
                        print(f"  [{i}] {stmt_type}: ⚠ Already exists")
                        success_count += 1
                    else:
                        print(f"  [{i}] {stmt_type}: ❌ Error - {error}")
                        error_count += 1
                else:
                    print(f"  [{i}] {stmt_type}: ✓ Success")
                    success_count += 1
            else:
                print(f"  [{i}] {stmt_type}: ✓ Success")
                success_count += 1
        else:
            print(f"  [{i}] {stmt_type}: ❌ HTTP {response.status_code}")
            error_count += 1
    
    print("\n" + "=" * 70)
    print(f"Deployment Complete: {success_count} succeeded, {error_count} failed")
    print("=" * 70)
    
    return error_count == 0


if __name__ == '__main__':
    success = deploy_schema()
    sys.exit(0 if success else 1)
