"""
Turso Database Integration for Amazon Scraper
Handles writing product data to Turso cloud database
"""

import requests
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

class TursoDatabase:
    """Turso cloud database client for Amazon products"""

    def __init__(self, db_url: str, auth_token: str):
        """
        Initialize Turso database client

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

    def _execute_sql(self, sql: str, params: List = None) -> dict:
        """
        Execute SQL via Turso HTTP API

        Args:
            sql: SQL query
            params: Optional parameters for prepared statements

        Returns:
            Response JSON
        """
        body = {"statements": [{"q": sql}]}

        if params:
            body["statements"][0]["params"] = params

        response = requests.post(self.db_url, headers=self.headers, json=body)
        response.raise_for_status()
        return response.json()

    def create_table(self):
        """Create products table if not exists"""
        sql = """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT UNIQUE NOT NULL,
                title TEXT,
                price TEXT,
                rating TEXT,
                reviews INTEGER,
                image TEXT,
                affiliate_link TEXT,
                search_query TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        self._execute_sql(sql)
        print("✓ Table 'products' ready")

    def insert_product(self, product: Dict[str, Any], search_query: str = None) -> bool:
        """
        Insert a single product into database

        Args:
            product: Product dictionary
            search_query: Search query used to find this product

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if ASIN already exists
            check_sql = "SELECT COUNT(*) FROM products WHERE asin = ?"
            result = self._execute_sql(check_sql, [product['asin']])
            count = result[0]['results']['rows'][0][0]

            if count > 0:
                # Update existing product
                sql = """
                    UPDATE products
                    SET title = ?, price = ?, rating = ?, reviews = ?,
                        image = ?, affiliate_link = ?, search_query = ?
                    WHERE asin = ?
                """
                params = [
                    product.get('title'),
                    product.get('price'),
                    product.get('rating'),
                    product.get('reviews'),
                    product.get('image'),
                    product.get('affiliate_link'),
                    search_query,
                    product['asin']
                ]
                self._execute_sql(sql, params)
                return True

            # Insert new product
            sql = """
                INSERT INTO products (asin, title, price, rating, reviews, image, affiliate_link, search_query)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """
            params = [
                product.get('asin'),
                product.get('title'),
                product.get('price'),
                product.get('rating'),
                product.get('reviews'),
                product.get('image'),
                product.get('affiliate_link'),
                search_query
            ]
            self._execute_sql(sql, params)
            return True

        except Exception as e:
            print(f"✗ Error inserting product {product.get('asin', 'unknown')}: {e}")
            return False

    def insert_products_batch(self, products: List[Dict[str, Any]], search_query: str = None) -> int:
        """
        Insert multiple products in batch

        Args:
            products: List of product dictionaries
            search_query: Search query used

        Returns:
            Number of successfully inserted products
        """
        success_count = 0

        for product in products:
            if self.insert_product(product, search_query):
                success_count += 1

        return success_count

    def get_all_products(self, limit: int = None) -> List[Dict[str, Any]]:
        """
        Get all products from database

        Args:
            limit: Optional limit on number of results

        Returns:
            List of product dictionaries
        """
        sql = "SELECT * FROM products ORDER BY created_at DESC"
        if limit:
            sql += f" LIMIT {limit}"

        result = self._execute_sql(sql)
        rows = result[0]['results']['rows']

        products = []
        for row in rows:
            products.append({
                'id': row[0],
                'asin': row[1],
                'title': row[2],
                'price': row[3],
                'rating': row[4],
                'reviews': row[5],
                'image': row[6],
                'affiliate_link': row[7],
                'search_query': row[8],
                'created_at': row[9]
            })

        return products

    def get_products_by_query(self, search_query: str) -> List[Dict[str, Any]]:
        """
        Get products by search query

        Args:
            search_query: Search query to filter by

        Returns:
            List of product dictionaries
        """
        sql = "SELECT * FROM products WHERE search_query = ? ORDER BY created_at DESC"
        result = self._execute_sql(sql, [search_query])
        rows = result[0]['results']['rows']

        products = []
        for row in rows:
            products.append({
                'id': row[0],
                'asin': row[1],
                'title': row[2],
                'price': row[3],
                'rating': row[4],
                'reviews': row[5],
                'image': row[6],
                'affiliate_link': row[7],
                'search_query': row[8],
                'created_at': row[9]
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
        result = self._execute_sql("SELECT COUNT(*) FROM products")
        stats['total_products'] = result[0]['results']['rows'][0][0]

        # Products by search query
        result = self._execute_sql("""
            SELECT search_query, COUNT(*) as count
            FROM products
            GROUP BY search_query
            ORDER BY count DESC
        """)
        stats['by_category'] = result[0]['results']['rows']

        # Average price (where price is numeric)
        result = self._execute_sql("""
            SELECT AVG(CAST(replace(price, '$', '') AS REAL)) as avg_price
            FROM products
            WHERE price != '$' AND price != '' AND price IS NOT NULL
        """)
        try:
            stats['avg_price'] = result[0]['results']['rows'][0][0]
        except:
            stats['avg_price'] = None

        return stats

    def delete_product(self, asin: str) -> bool:
        """
        Delete a product by ASIN

        Args:
            asin: Product ASIN

        Returns:
            True if successful
        """
        try:
            self._execute_sql("DELETE FROM products WHERE asin = ?", [asin])
            return True
        except Exception as e:
            print(f"✗ Error deleting product {asin}: {e}")
            return False

    def search_products(self, search_term: str) -> List[Dict[str, Any]]:
        """
        Full-text search in product titles

        Args:
            search_term: Search term

        Returns:
            List of matching products
        """
        sql = "SELECT * FROM products WHERE title LIKE ? ORDER BY created_at DESC"
        result = self._execute_sql(sql, [f"%{search_term}%"])
        rows = result[0]['results']['rows']

        products = []
        for row in rows:
            products.append({
                'id': row[0],
                'asin': row[1],
                'title': row[2],
                'price': row[3],
                'rating': row[4],
                'reviews': row[5],
                'image': row[6],
                'affiliate_link': row[7],
                'search_query': row[8],
                'created_at': row[9]
            })

        return products
