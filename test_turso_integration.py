"""
Test Suite for Turso Database Integration
TDD Approach - Tests connection, CRUD operations, JSON parsing, error handling, and performance
"""

import pytest
import requests
import json
import time
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from turso_client import TursoDatabase

# Test configuration
TEST_DB_URL = "libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io"
TEST_AUTH_TOKEN = "eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCJ9.eyJhIjoicnciLCJpYXQiOjE3NzI0MzMzNTMsImlkIjoiMDE5Y2FkNDEtZmUwMS03NzI4LTgyMGUtOGU1ZDBiZmJmZThjIiwicmlkIjoiYmJmZWUyMjYtZTI1NS00NmYxLThiZjktNzdiNTk3YWQ0NzA4In0.dRhrBVMddMlLt2PxrE766MRbRQE15wmtO6pNub4yxOvsr2MwjmeMTwzjINFqNUtQ4k6DW5hHBjettS3X-IVbDw"
PERFORMANCE_THRESHOLD_MS = 500  # 500ms response time requirement
REALISTIC_THRESHOLD_MS = 5000   # Realistic threshold given network latency to Tokyo region


class TestTursoConnection:
    """Test Group 1: Connection Testing"""

    def test_connection_string_format(self):
        """Test that libsql:// URL is properly converted to https://"""
        db = TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)
        assert db.db_url.startswith("https://")
        assert "libsql://" not in db.db_url
        assert "amazon-affiliate-david-adam" in db.db_url
        assert "aws-ap-northeast-1.turso.io" in db.db_url

    def test_headers_are_set_correctly(self):
        """Test that authorization headers are properly configured"""
        db = TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)
        assert "Authorization" in db.headers
        assert f"Bearer {TEST_AUTH_TOKEN}" in db.headers["Authorization"]
        assert db.headers["Content-Type"] == "application/json"

    def test_connection_success(self):
        """Test actual connection to Turso database"""
        db = TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)
        
        # Try to execute a simple query
        start_time = time.time()
        result = db._execute_sql("SELECT 1")
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert result is not None
        assert isinstance(result, list)
        assert elapsed_ms < PERFORMANCE_THRESHOLD_MS, f"Connection took {elapsed_ms}ms, exceeds {PERFORMANCE_THRESHOLD_MS}ms threshold"
        print(f"✓ Connection successful in {elapsed_ms:.2f}ms")


class TestTursoSelectQueries:
    """Test Group 2: SELECT Query Operations"""

    @pytest.fixture
    def db(self):
        """Fixture to provide database connection"""
        return TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)

    def test_select_simple_query(self, db):
        """Test basic SELECT query returns correct structure"""
        result = db._execute_sql("SELECT 1 as test_value")
        
        assert isinstance(result, list)
        assert len(result) > 0
        assert "results" in result[0]
        print("✓ Simple SELECT works")

    def test_select_with_parameters(self, db):
        """Test SELECT with prepared statement parameters"""
        result = db._execute_sql("SELECT ? as value1, ? as value2", ["hello", 42])
        
        assert isinstance(result, list)
        assert "results" in result[0]
        print("✓ SELECT with parameters works")

    def test_get_all_products_returns_list(self, db):
        """Test get_all_products returns a list"""
        products = db.get_all_products(limit=5)
        
        assert isinstance(products, list)
        print(f"✓ get_all_products returned {len(products)} products")

    def test_get_all_products_structure(self, db):
        """Test that product records have expected fields"""
        products = db.get_all_products(limit=1)
        
        if products:  # Only check structure if products exist
            product = products[0]
            expected_fields = ['id', 'asin', 'title', 'price', 'rating', 'reviews', 
                             'image', 'affiliate_link', 'search_query', 'created_at']
            for field in expected_fields:
                assert field in product, f"Missing field: {field}"
        print("✓ Product structure validated")

    def test_get_stats_returns_dict(self, db):
        """Test get_stats returns a dictionary with expected keys"""
        stats = db.get_stats()
        
        assert isinstance(stats, dict)
        assert 'total_products' in stats
        assert 'by_category' in stats
        print(f"✓ Stats retrieved: {stats['total_products']} total products")


class TestTursoCRUDOperations:
    """Test Group 3: INSERT, UPDATE, DELETE Operations"""

    @pytest.fixture
    def db(self):
        """Fixture to provide database connection"""
        return TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)

    @pytest.fixture
    def test_product(self):
        """Fixture to provide a test product"""
        return {
            'asin': f'TEST{int(time.time())}',
            'title': 'Test Product for Integration Testing',
            'price': '$99.99',
            'rating': '4.5',
            'reviews': 100,
            'image': 'https://example.com/test.jpg',
            'affiliate_link': 'https://amazon.com/dp/TEST123?tag=test',
        }

    def test_insert_product(self, db, test_product):
        """Test inserting a new product"""
        start_time = time.time()
        result = db.insert_product(test_product, search_query="test_insert")
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert result is True
        assert elapsed_ms < PERFORMANCE_THRESHOLD_MS, f"INSERT took {elapsed_ms}ms"
        print(f"✓ INSERT successful in {elapsed_ms:.2f}ms")

    def test_update_existing_product(self, db, test_product):
        """Test updating an existing product"""
        # First insert
        db.insert_product(test_product, search_query="test_update")
        
        # Then update
        test_product['price'] = '$79.99'
        test_product['title'] = 'Updated Test Product'
        
        start_time = time.time()
        result = db.insert_product(test_product, search_query="test_update")
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert result is True
        assert elapsed_ms < PERFORMANCE_THRESHOLD_MS, f"UPDATE took {elapsed_ms}ms"
        print(f"✓ UPDATE successful in {elapsed_ms:.2f}ms")

    def test_delete_product(self, db, test_product):
        """Test deleting a product"""
        # First insert
        db.insert_product(test_product, search_query="test_delete")
        
        # Then delete
        start_time = time.time()
        result = db.delete_product(test_product['asin'])
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert result is True
        assert elapsed_ms < PERFORMANCE_THRESHOLD_MS, f"DELETE took {elapsed_ms}ms"
        print(f"✓ DELETE successful in {elapsed_ms:.2f}ms")

    def test_insert_batch_products(self, db):
        """Test batch insert of multiple products"""
        timestamp = int(time.time())
        test_products = [
            {
                'asin': f'BATCH{timestamp}A',
                'title': 'Batch Product A',
                'price': '$10.00',
                'rating': '4.0',
                'reviews': 50,
                'image': 'https://example.com/a.jpg',
                'affiliate_link': 'https://amazon.com/dp/BATCHA?tag=test',
            },
            {
                'asin': f'BATCH{timestamp}B',
                'title': 'Batch Product B',
                'price': '$20.00',
                'rating': '4.5',
                'reviews': 75,
                'image': 'https://example.com/b.jpg',
                'affiliate_link': 'https://amazon.com/dp/BATCHB?tag=test',
            }
        ]
        
        start_time = time.time()
        count = db.insert_products_batch(test_products, search_query="test_batch")
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert count == len(test_products)
        assert elapsed_ms < PERFORMANCE_THRESHOLD_MS * 2, f"Batch INSERT took {elapsed_ms}ms"
        print(f"✓ Batch INSERT of {count} products successful in {elapsed_ms:.2f}ms")


class TestTursoJSONParsing:
    """Test Group 4: JSON Parsing Verification"""

    @pytest.fixture
    def db(self):
        """Fixture to provide database connection"""
        return TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)

    def test_response_is_valid_json(self, db):
        """Test that database responses are valid JSON"""
        result = db._execute_sql("SELECT 1 as num, 'test' as str")
        
        # Should be a list (parsed JSON)
        assert isinstance(result, list)
        
        # Should be JSON serializable
        json_str = json.dumps(result)
        assert isinstance(json_str, str)
        
        # Should be JSON parseable
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)
        print("✓ Response is valid JSON")

    def test_product_to_json_serializable(self, db):
        """Test that product data can be serialized to JSON"""
        products = db.get_all_products(limit=1)
        
        if products:
            product = products[0]
            # Should not raise exception
            json_str = json.dumps(product)
            parsed = json.loads(json_str)
            assert parsed['id'] == product['id']
            assert parsed['asin'] == product['asin']
        print("✓ Product data is JSON serializable")

    def test_stats_to_json_serializable(self, db):
        """Test that stats can be serialized to JSON"""
        stats = db.get_stats()
        
        # Should not raise exception
        json_str = json.dumps(stats)
        parsed = json.loads(json_str)
        
        assert 'total_products' in parsed
        assert 'by_category' in parsed
        print("✓ Stats data is JSON serializable")

    def test_nested_json_structure(self, db):
        """Test handling of nested JSON in response"""
        result = db._execute_sql("SELECT json_object('name', 'test', 'value', 42) as data")
        
        assert isinstance(result, list)
        assert len(result) > 0
        print("✓ Nested JSON structure handled")


class TestTursoErrorHandling:
    """Test Group 5: Error Handling"""

    def test_invalid_connection_url(self):
        """Test handling of invalid connection URL"""
        with pytest.raises(Exception):
            db = TursoDatabase("invalid://url", "invalid_token")
            db._execute_sql("SELECT 1")

    def test_invalid_auth_token(self):
        """Test handling of invalid authentication token"""
        db = TursoDatabase(TEST_DB_URL, "invalid_token")
        
        with pytest.raises(Exception) as exc_info:
            db._execute_sql("SELECT 1")
        
        assert exc_info.value is not None
        print("✓ Invalid auth token properly rejected")

    def test_invalid_sql_syntax(self):
        """Test handling of invalid SQL"""
        db = TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)
        
        with pytest.raises(Exception) as exc_info:
            db._execute_sql("INVALID SQL SYNTAX!!!")
        
        print("✓ Invalid SQL properly raises exception")

    def test_sql_injection_protection(self):
        """Test SQL injection protection via parameterized queries"""
        db = TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)
        
        # Attempt SQL injection - should not crash database
        malicious_input = "'; DROP TABLE products; --"
        
        # This should fail gracefully, not execute the DROP
        try:
            result = db._execute_sql("SELECT ? as safe", [malicious_input])
            # If we get here, the parameter was properly escaped
            print("✓ SQL injection attempt handled safely")
        except Exception as e:
            # Even if it fails, it shouldn't have dropped the table
            pass
        
        # Verify table still exists
        result = db._execute_sql("SELECT COUNT(*) FROM products")
        assert result is not None
        print("✓ Table intact after SQL injection test")

    def test_connection_timeout_handling(self):
        """Test handling of connection timeouts"""
        # Mock requests to simulate timeout
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
            
            db = TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)
            
            with pytest.raises(requests.exceptions.Timeout):
                db._execute_sql("SELECT 1")
        
        print("✓ Timeout exception properly raised")

    def test_network_error_handling(self):
        """Test handling of network errors"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Network unreachable")
            
            db = TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)
            
            with pytest.raises(requests.exceptions.ConnectionError):
                db._execute_sql("SELECT 1")
        
        print("✓ Network error properly raised")


class TestTursoPerformance:
    """Test Group 6: Performance Testing"""

    @pytest.fixture
    def db(self):
        """Fixture to provide database connection"""
        return TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)

    def test_select_response_time(self, db):
        """Test SELECT query response time"""
        start_time = time.time()
        result = db._execute_sql("SELECT * FROM products LIMIT 10")
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < PERFORMANCE_THRESHOLD_MS, \
            f"SELECT took {elapsed_ms:.2f}ms, exceeds {PERFORMANCE_THRESHOLD_MS}ms limit"
        print(f"✓ SELECT response time: {elapsed_ms:.2f}ms")

    def test_insert_response_time(self, db):
        """Test INSERT response time"""
        test_product = {
            'asin': f'PERF{int(time.time())}',
            'title': 'Performance Test Product',
            'price': '$50.00',
            'rating': '4.0',
            'reviews': 10,
            'image': 'https://example.com/perf.jpg',
            'affiliate_link': 'https://amazon.com/dp/PERF?tag=test',
        }
        
        start_time = time.time()
        db.insert_product(test_product, search_query="perf_test")
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < PERFORMANCE_THRESHOLD_MS, \
            f"INSERT took {elapsed_ms:.2f}ms, exceeds {PERFORMANCE_THRESHOLD_MS}ms limit"
        print(f"✓ INSERT response time: {elapsed_ms:.2f}ms")

    def test_stats_response_time(self, db):
        """Test stats query response time"""
        start_time = time.time()
        stats = db.get_stats()
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < PERFORMANCE_THRESHOLD_MS, \
            f"Stats query took {elapsed_ms:.2f}ms, exceeds {PERFORMANCE_THRESHOLD_MS}ms limit"
        print(f"✓ Stats response time: {elapsed_ms:.2f}ms")


class TestTursoIntegration:
    """Test Group 7: End-to-End Integration Tests"""

    @pytest.fixture
    def db(self):
        """Fixture to provide database connection"""
        return TursoDatabase(TEST_DB_URL, TEST_AUTH_TOKEN)

    def test_full_crud_lifecycle(self, db):
        """Test complete CRUD lifecycle"""
        timestamp = int(time.time())
        test_product = {
            'asin': f'CRUD{timestamp}',
            'title': 'CRUD Test Product',
            'price': '$100.00',
            'rating': '5.0',
            'reviews': 999,
            'image': 'https://example.com/crud.jpg',
            'affiliate_link': 'https://amazon.com/dp/CRUD?tag=test',
        }
        
        # CREATE
        insert_result = db.insert_product(test_product, search_query="crud_test")
        assert insert_result is True
        
        # READ
        products = db.get_all_products(limit=1)
        assert isinstance(products, list)
        
        # UPDATE
        test_product['price'] = '$150.00'
        update_result = db.insert_product(test_product, search_query="crud_test")
        assert update_result is True
        
        # DELETE
        delete_result = db.delete_product(test_product['asin'])
        assert delete_result is True
        
        print("✓ Full CRUD lifecycle successful")

    def test_search_by_query(self, db):
        """Test searching products by query"""
        timestamp = int(time.time())
        test_products = [
            {
                'asin': f'SEARCH{timestamp}A',
                'title': 'Search Test Product A',
                'price': '$10.00',
                'rating': '4.0',
                'reviews': 10,
                'image': 'https://example.com/search_a.jpg',
                'affiliate_link': 'https://amazon.com/dp/SEARCHA?tag=test',
            },
            {
                'asin': f'SEARCH{timestamp}B',
                'title': 'Search Test Product B',
                'price': '$20.00',
                'rating': '4.5',
                'reviews': 20,
                'image': 'https://example.com/search_b.jpg',
                'affiliate_link': 'https://amazon.com/dp/SEARCHB?tag=test',
            }
        ]
        
        # Insert test products
        for product in test_products:
            db.insert_product(product, search_query="search_test_query")
        
        # Search by query
        results = db.get_products_by_query("search_test_query")
        assert isinstance(results, list)
        assert len(results) >= 2
        
        # Clean up
        for product in test_products:
            db.delete_product(product['asin'])
        
        print(f"✓ Search by query returned {len(results)} results")

    def test_full_text_search(self, db):
        """Test full-text search in titles"""
        timestamp = int(time.time())
        test_product = {
            'asin': f'FTS{timestamp}',
            'title': 'Unique Searchable Title XYZ123',
            'price': '$50.00',
            'rating': '4.0',
            'reviews': 10,
            'image': 'https://example.com/fts.jpg',
            'affiliate_link': 'https://amazon.com/dp/FTS?tag=test',
        }
        
        # Insert
        db.insert_product(test_product, search_query="fts_test")
        
        # Search
        results = db.search_products("Unique Searchable Title")
        assert isinstance(results, list)
        
        # Clean up
        db.delete_product(test_product['asin'])
        
        print(f"✓ Full-text search returned {len(results)} results")


def run_tests():
    """Run all tests and generate summary report"""
    print("\n" + "=" * 70)
    print("TURSO DATABASE INTEGRATION TEST SUITE")
    print("=" * 70)
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x"  # Stop on first failure
    ])
    
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✅ ALL TESTS PASSED")
    else:
        print(f"❌ TESTS FAILED (exit code: {exit_code})")
    print("=" * 70)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
