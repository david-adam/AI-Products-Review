"""
Turso Schema Deployment Module
Handles deploying and verifying database schema
"""

import os
import sys
import requests
from typing import List, Dict, Any, Optional

# Ensure parent directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TursoSchemaDeploy:
    """Turso schema deployment and verification client"""
    
    def __init__(self, db_url: str, auth_token: str):
        """
        Initialize Turso schema deployer
        
        Args:
            db_url: Turso database URL (libsql://...)
            auth_token: Turso authentication token
        """
        self.db_url = db_url.replace("libsql://", "https://")
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def execute_sql(self, sql: str, params: List = None) -> dict:
        """
        Execute SQL via Turso HTTP API
        
        Args:
            sql: SQL query
            params: Optional parameters for prepared statements
            
        Returns:
            Response JSON
        """
        request_item = {"q": sql}
        
        if params:
            request_item["params"] = params
        
        body = {"statements": [request_item]}
        
        response = requests.post(self.db_url, headers=self.headers, json=body)
        response.raise_for_status()
        return response.json()
    
    def execute_migration(self, migration_sql: str) -> bool:
        """
        Execute a multi-statement migration
        
        Args:
            migration_sql: SQL migration script content
            
        Returns:
            True if successful
        """
        # Split by semicolons but handle comments
        statements = []
        current_statement = []
        
        for line in migration_sql.split('\n'):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('--') or line.startswith('/*'):
                continue
            
            current_statement.append(line)
            
            if line.endswith(';'):
                stmt = ' '.join(current_statement)
                if stmt.strip():
                    statements.append(stmt)
                current_statement = []
        
        # Execute each statement
        success_count = 0
        for stmt in statements:
            try:
                self.execute_sql(stmt)
                success_count += 1
                print(f"  ✓ Executed: {stmt[:60]}...")
            except Exception as e:
                print(f"  ✗ Failed: {stmt[:60]}...")
                print(f"    Error: {e}")
        
        print(f"\nExecuted {success_count}/{len(statements)} statements")
        return success_count == len(statements)
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database
        
        Returns:
            List of table names
        """
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        result = self.execute_sql(sql)
        
        tables = []
        if result and len(result) > 0:
            rows = result[0].get('results', {}).get('rows', [])
            for row in rows:
                tables.append(row[0])
        
        return tables
    
    def list_indexes(self, table_name: str) -> List[str]:
        """
        List all indexes for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of index names
        """
        sql = "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name = ?"
        result = self.execute_sql(sql, [table_name])
        
        indexes = []
        if result and len(result) > 0:
            rows = result[0].get('results', {}).get('rows', [])
            for row in rows:
                indexes.append(row[0])
        
        return indexes
    
    def get_table_schema(self, table_name: str) -> str:
        """
        Get the CREATE TABLE statement for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            CREATE TABLE SQL statement
        """
        sql = "SELECT sql FROM sqlite_master WHERE type='table' AND name = ?"
        result = self.execute_sql(sql, [table_name])
        
        if result and len(result) > 0:
            rows = result[0]['results']['rows']
            if rows:
                return rows[0][0]
        
        return None
    
    def verify_table_exists(self, table_name: str) -> bool:
        """
        Check if a table exists
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if table exists
        """
        tables = self.list_tables()
        return table_name in tables
    
    def verify_all_tables(self, expected_tables: List[str]) -> Dict[str, bool]:
        """
        Verify all expected tables exist
        
        Args:
            expected_tables: List of expected table names
            
        Returns:
            Dictionary of table_name -> exists
        """
        tables = self.list_tables()
        results = {}
        
        for table in expected_tables:
            results[table] = table in tables
        
        return results
    
    def clean_test_data(self):
        """Clean up test data from all tables"""
        test_asins = ['TEST123456', 'TEST999999']
        
        for asin in test_asins:
            try:
                self.execute_sql("DELETE FROM social_posts WHERE product_asin = ?", [asin])
                self.execute_sql("DELETE FROM product_reviews WHERE product_asin = ?", [asin])
            except:
                pass
        
        # Clean test platform data
        try:
            self.execute_sql("DELETE FROM social_integrations WHERE platform = 'twitter'")
            self.execute_sql("DELETE FROM platform_validation_logs WHERE platform = 'twitter'")
        except:
            pass
        
        print("✓ Test data cleaned")


def deploy_schema(migration_file: str = 'database/migrations.sql') -> bool:
    """
    Deploy schema from migration file
    
    Args:
        migration_file: Path to migration SQL file
        
    Returns:
        True if deployment successful
    """
    # Load environment variables
    db_url = os.getenv('TURSO_DATABASE_URL')
    auth_token = os.getenv('TURSO_AUTH_TOKEN')
    
    if not db_url or not auth_token:
        print("Error: TURSO_DATABASE_URL and TURSO_AUTH_TOKEN must be set")
        return False
    
    # Read migration file
    migration_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), migration_file)
    if not os.path.exists(migration_path):
        print(f"Error: Migration file not found: {migration_path}")
        return False
    
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    print(f"Loaded migration file: {migration_path}")
    print(f"Migration size: {len(migration_sql)} characters\n")
    
    # Deploy
    deployer = TursoSchemaDeploy(db_url, auth_token)
    
    print("Deploying schema...")
    success = deployer.execute_migration(migration_sql)
    
    if success:
        print("\n✅ Schema deployed successfully!")
        
        # Verify tables
        print("\nVerifying tables...")
        expected_tables = [
            'product_reviews',
            'social_integrations', 
            'social_posts',
            'content_generation_logs',
            'platform_validation_logs'
        ]
        
        results = deployer.verify_all_tables(expected_tables)
        all_exist = all(results.values())
        
        for table, exists in results.items():
            status = "✓" if exists else "✗"
            print(f"  {status} {table}")
        
        return all_exist
    else:
        print("\n❌ Schema deployment failed!")
        return False


if __name__ == '__main__':
    # Load .env file if present
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    
    success = deploy_schema()
    sys.exit(0 if success else 1)
