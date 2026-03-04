"""
Turso HTTP Client for Trending Products Database
Handles all database operations via Turso HTTP API
"""

import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

class TursoTrendingDB:
    """Turso cloud database client for trending products"""

    def __init__(self, db_url: str = None, auth_token: str = None):
        """
        Initialize Turso database client
        
        Args:
            db_url: Turso database URL (libsql://...)
            auth_token: Turso authentication token
        """
        # Load from environment if not provided
        if db_url is None:
            db_url = os.getenv('TURSO_DATABASE_URL', 'libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io')
        if auth_token is None:
            auth_token = os.getenv('TURSO_AUTH_TOKEN', '')
        
        # Convert libsql:// to https:// 
        self.db_url = db_url.replace("libsql://", "https://").rstrip('/')
        self.auth_token = auth_token
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    def _execute_sql(self, sql: str, params: List = None) -> dict:
        """
        Execute SQL via Turso HTTP API
        
        Args:
            sql: SQL query
            params: Optional parameters for prepared statements
            
        Returns:
            Response JSON
        """
        # Turso HTTP API expects 'statements' with 'q' key
        request_item = {"q": sql}
        
        if params:
            request_item["args"] = params
        
        body = {"statements": [request_item]}
        
        response = requests.post(self.db_url, headers=self.headers, json=body)
        response.raise_for_status()
        return response.json()

    def create_table(self):
        """Create trending_products table if not exists"""
        sql = """
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
        """
        self._execute_sql(sql)
        print("✓ Table 'trending_products' ready")
        
        # Create indexes
        self._execute_sql("CREATE INDEX IF NOT EXISTS idx_asin ON trending_products(asin)")
        self._execute_sql("CREATE INDEX IF NOT EXISTS idx_total_score ON trending_products(total_score DESC)")
        self._execute_sql("CREATE INDEX IF NOT EXISTS idx_category ON trending_products(category)")
        print("✓ Indexes created")

    def insert_or_update_product(self, product: Dict[str, Any]) -> bool:
        """
        Insert or update a product in the database
        
        Args:
            product: Product dictionary with all fields
            
        Returns:
            True if successful
        """
        try:
            # Check if product exists
            check_sql = "SELECT id FROM trending_products WHERE asin = ?"
            result = self._execute_sql(check_sql, [product.get('asin')])
            
            rows = result[0].get('results', {}).get('rows', [])
            
            if rows and len(rows) > 0:
                # Update existing product
                sql = """
                    UPDATE trending_products 
                    SET title = ?, category = ?, amazon_rank = ?, 
                        price = ?, rating = ?, total_score = ?,
                        image = ?, affiliate_link = ?, reviews = ?, product_summary = ?,
                        last_updated = CURRENT_TIMESTAMP
                    WHERE asin = ?
                """
                params = [
                    product.get('title'),
                    product.get('category'),
                    product.get('amazon_rank'),
                    product.get('price'),
                    product.get('rating'),
                    product.get('total_score', 0),
                    product.get('image'),
                    product.get('affiliate_link'),
                    product.get('reviews', 0),
                    product.get('product_summary'),
                    product.get('asin')
                ]
                self._execute_sql(sql, params)
                return True
            else:
                # Insert new product
                sql = """
                    INSERT INTO trending_products 
                    (asin, title, category, amazon_rank, price, rating, total_score,
                     image, affiliate_link, reviews, product_summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                params = [
                    product.get('asin'),
                    product.get('title'),
                    product.get('category'),
                    product.get('amazon_rank'),
                    product.get('price'),
                    product.get('rating'),
                    product.get('total_score', 0),
                    product.get('image'),
                    product.get('affiliate_link'),
                    product.get('reviews', 0),
                    product.get('product_summary')
                ]
                self._execute_sql(sql, params)
                return True
                
        except Exception as e:
            print(f"✗ Error saving product {product.get('asin', 'unknown')}: {e}")
            return False

    def get_top_products(self, limit: int = 20, min_score: int = 50) -> List[Dict[str, Any]]:
        """
        Get top scoring products from database
        
        Args:
            limit: Maximum number of products to return
            min_score: Minimum total score
            
        Returns:
            List of product dictionaries
        """
        sql = """
            SELECT asin, title, category, amazon_rank, price, rating, total_score,
                   image, affiliate_link, reviews, product_summary
            FROM trending_products
            WHERE total_score >= ?
            ORDER BY total_score DESC
            LIMIT ?
        """
        result = self._execute_sql(sql, [min_score, limit])
        rows = result[0].get('results', {}).get('rows', [])
        
        products = []
        for row in rows:
            products.append({
                'asin': row[0],
                'title': row[1],
                'category': row[2],
                'amazon_rank': row[3],
                'price': row[4],
                'rating': row[5],
                'total_score': row[6],
                'image': row[7],
                'affiliate_link': row[8],
                'reviews': row[9],
                'product_summary': row[10]
            })
        
        return products

    def get_all_products(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all products from database
        
        Args:
            limit: Optional limit on number of results
            
        Returns:
            List of product dictionaries
        """
        sql = """
            SELECT asin, title, category, amazon_rank, price, rating, total_score,
                   image, affiliate_link, reviews, product_summary, discovered_date
            FROM trending_products
            ORDER BY total_score DESC
        """
        if limit:
            sql += f" LIMIT {limit}"
        
        result = self._execute_sql(sql)
        rows = result[0].get('results', {}).get('rows', [])
        
        products = []
        for row in rows:
            products.append({
                'asin': row[0],
                'title': row[1],
                'category': row[2],
                'amazon_rank': row[3],
                'price': row[4],
                'rating': row[5],
                'total_score': row[6],
                'image': row[7],
                'affiliate_link': row[8],
                'reviews': row[9],
                'product_summary': row[10],
                'discovered_date': row[11]
            })
        
        return products

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with stats
        """
        stats = {}
        
        # Total products
        result = self._execute_sql("SELECT COUNT(*) FROM trending_products")
        stats['total_products'] = result[0].get('results', {}).get('rows', [[0]])[0][0]
        
        # Products by category
        result = self._execute_sql("""
            SELECT category, COUNT(*) as count
            FROM trending_products
            GROUP BY category
            ORDER BY count DESC
        """)
        stats['by_category'] = result[0].get('results', {}).get('rows', [])
        
        return stats
