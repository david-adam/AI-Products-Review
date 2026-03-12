"""
TDD Test Suite for Turso Database Schema Deployment
Tests all 5 Phase 2 tables and their CRUD operations
"""

import os
import sys
import pytest
from datetime import datetime, date
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.turso_schema_deploy import TursoSchemaDeploy

# Test configuration
TEST_DB_URL = os.getenv('TURSO_DATABASE_URL', 'libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io')
TEST_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')


def get_rows(result):
    """Helper to extract rows from Turso response"""
    if result and len(result) > 0:
        return result[0].get('results', {}).get('rows', [])
    return []


class TestTursoSchemaDeployment:
    """Test suite for Turso schema deployment"""
    
    @pytest.fixture(scope="class")
    def db(self):
        """Fixture to create database connection"""
        if not TEST_AUTH_TOKEN:
            pytest.skip("TURSO_AUTH_TOKEN not set")
        
        deployer = TursoSchemaDeploy(TEST_DB_URL, TEST_AUTH_TOKEN)
        yield deployer
    
    # ==========================================================================
    # TABLE EXISTENCE TESTS
    # ==========================================================================
    
    def test_table_product_reviews_exists(self, db):
        """Test that product_reviews table exists"""
        tables = db.list_tables()
        assert 'product_reviews' in tables, "product_reviews table should exist"
    
    def test_table_social_integrations_exists(self, db):
        """Test that social_integrations table exists"""
        tables = db.list_tables()
        assert 'social_integrations' in tables, "social_integrations table should exist"
    
    def test_table_social_posts_exists(self, db):
        """Test that social_posts table exists"""
        tables = db.list_tables()
        assert 'social_posts' in tables, "social_posts table should exist"
    
    def test_table_content_generation_logs_exists(self, db):
        """Test that content_generation_logs table exists"""
        tables = db.list_tables()
        assert 'content_generation_logs' in tables, "content_generation_logs table should exist"
    
    def test_table_platform_validation_logs_exists(self, db):
        """Test that platform_validation_logs table exists"""
        tables = db.list_tables()
        assert 'platform_validation_logs' in tables, "platform_validation_logs table should exist"
    
    # ==========================================================================
    # PRODUCT_REVIEWS CRUD TESTS
    # ==========================================================================
    
    def test_product_reviews_create(self, db):
        """Test CREATE operation on product_reviews"""
        # Clean up any existing test data
        try:
            db.execute_sql("DELETE FROM product_reviews WHERE product_asin = 'TEST123456'")
        except:
            pass
        
        sql = """
            INSERT INTO product_reviews (product_asin, summary, full_review, rating, pros, cons)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = [
            'TEST123456',
            'This is a test summary that is at least 100 characters long to meet the constraint requirement for testing.',
            'This is a test full review that needs to be at least 600 characters long to meet the constraint requirement. ' * 12,
            4.5,
            'Good quality, Fast shipping',
            'Expensive'
        ]
        
        result = db.execute_sql(sql, params)
        assert result is not None, "Insert should succeed"
    
    def test_product_reviews_read(self, db):
        """Test READ operation on product_reviews"""
        sql = "SELECT * FROM product_reviews WHERE product_asin = ?"
        result = db.execute_sql(sql, ['TEST123456'])
        
        rows = get_rows(result)
        assert len(rows) > 0, "Should find the inserted record"
        assert rows[0][1] == 'TEST123456', "ASIN should match"
    
    def test_product_reviews_update(self, db):
        """Test UPDATE operation on product_reviews"""
        sql = """
            UPDATE product_reviews 
            SET rating = ?, updated_at = CURRENT_TIMESTAMP
            WHERE product_asin = ?
        """
        result = db.execute_sql(sql, [5.0, 'TEST123456'])
        
        # Verify update
        verify = db.execute_sql("SELECT rating FROM product_reviews WHERE product_asin = ?", ['TEST123456'])
        rows = get_rows(verify)
        assert len(rows) > 0, "Record should exist"
        assert rows[0][0] == 5.0, "Rating should be updated"
    
    def test_product_reviews_delete(self, db):
        """Test DELETE operation on product_reviews"""
        sql = "DELETE FROM product_reviews WHERE product_asin = ?"
        result = db.execute_sql(sql, ['TEST123456'])
        
        # Verify deletion
        verify = db.execute_sql("SELECT COUNT(*) FROM product_reviews WHERE product_asin = ?", ['TEST123456'])
        rows = get_rows(verify)
        count = rows[0][0] if rows else 0
        assert count == 0, "Record should be deleted"
    
    # ==========================================================================
    # SOCIAL_INTEGRATIONS CRUD TESTS
    # ==========================================================================
    
    def test_social_integrations_create(self, db):
        """Test CREATE operation on social_integrations"""
        try:
            db.execute_sql("DELETE FROM social_integrations WHERE platform = 'twitter'")
        except:
            pass
        
        sql = """
            INSERT INTO social_integrations (platform, platform_name, twitter_api_key, is_active)
            VALUES (?, ?, ?, ?)
        """
        params = ['twitter', 'Twitter Test', 'test_key_123', 1]
        
        result = db.execute_sql(sql, params)
        assert result is not None, "Insert should succeed"
    
    def test_social_integrations_read(self, db):
        """Test READ operation on social_integrations"""
        sql = "SELECT * FROM social_integrations WHERE platform = ?"
        result = db.execute_sql(sql, ['twitter'])
        
        rows = get_rows(result)
        assert len(rows) > 0, "Should find the inserted record"
        assert rows[0][1] == 'twitter', "Platform should match"
    
    def test_social_integrations_update(self, db):
        """Test UPDATE operation on social_integrations"""
        sql = """
            UPDATE social_integrations 
            SET daily_post_limit = ?, updated_at = CURRENT_TIMESTAMP
            WHERE platform = ?
        """
        result = db.execute_sql(sql, [20, 'twitter'])
        
        verify = db.execute_sql("SELECT daily_post_limit FROM social_integrations WHERE platform = ?", ['twitter'])
        rows = get_rows(verify)
        assert len(rows) > 0, "Record should exist"
        assert rows[0][0] == 20, "Limit should be updated"
    
    def test_social_integrations_delete(self, db):
        """Test DELETE operation on social_integrations"""
        sql = "DELETE FROM social_integrations WHERE platform = ?"
        result = db.execute_sql(sql, ['twitter'])
        
        verify = db.execute_sql("SELECT COUNT(*) FROM social_integrations WHERE platform = ?", ['twitter'])
        rows = get_rows(verify)
        count = rows[0][0] if rows else 0
        assert count == 0, "Record should be deleted"
    
    # ==========================================================================
    # SOCIAL_POSTS CRUD TESTS
    # ==========================================================================
    
    def test_social_posts_create(self, db):
        """Test CREATE operation on social_posts"""
        try:
            db.execute_sql("DELETE FROM social_posts WHERE product_asin = 'TEST999999'")
        except:
            pass
        
        sql = """
            INSERT INTO social_posts (product_asin, platform, content_text, status)
            VALUES (?, ?, ?, ?)
        """
        params = ['TEST999999', 'twitter', 'Test post content here', 'pending']
        
        result = db.execute_sql(sql, params)
        assert result is not None, "Insert should succeed"
    
    def test_social_posts_read(self, db):
        """Test READ operation on social_posts"""
        sql = "SELECT * FROM social_posts WHERE product_asin = ?"
        result = db.execute_sql(sql, ['TEST999999'])
        
        rows = get_rows(result)
        assert len(rows) > 0, "Should find the inserted record"
        assert rows[0][1] == 'TEST999999', "ASIN should match"
    
    def test_social_posts_update(self, db):
        """Test UPDATE operation on social_posts"""
        sql = """
            UPDATE social_posts 
            SET status = ?, engagements = ?
            WHERE product_asin = ?
        """
        result = db.execute_sql(sql, ['published', 100, 'TEST999999'])
        
        verify = db.execute_sql("SELECT status, engagements FROM social_posts WHERE product_asin = ?", ['TEST999999'])
        rows = get_rows(verify)
        assert len(rows) > 0, "Record should exist"
        assert rows[0][0] == 'published', "Status should be updated"
        assert rows[0][1] == 100, "Engagements should be updated"
    
    def test_social_posts_delete(self, db):
        """Test DELETE operation on social_posts"""
        sql = "DELETE FROM social_posts WHERE product_asin = ?"
        result = db.execute_sql(sql, ['TEST999999'])
        
        verify = db.execute_sql("SELECT COUNT(*) FROM social_posts WHERE product_asin = ?", ['TEST999999'])
        rows = get_rows(verify)
        count = rows[0][0] if rows else 0
        assert count == 0, "Record should be deleted"
    
    # ==========================================================================
    # CONTENT_GENERATION_LOGS CRUD TESTS
    # ==========================================================================
    
    def test_content_generation_logs_create(self, db):
        """Test CREATE operation on content_generation_logs"""
        today = date.today().isoformat()
        try:
            db.execute_sql("DELETE FROM content_generation_logs WHERE generation_date = ?", [today])
        except:
            pass
        
        sql = """
            INSERT INTO content_generation_logs (generation_date, content_type, platform, generated_count)
            VALUES (?, ?, ?, ?)
        """
        params = [today, 'review', 'twitter', 5]
        
        result = db.execute_sql(sql, params)
        assert result is not None, "Insert should succeed"
    
    def test_content_generation_logs_read(self, db):
        """Test READ operation on content_generation_logs"""
        today = date.today().isoformat()
        sql = "SELECT * FROM content_generation_logs WHERE generation_date = ?"
        result = db.execute_sql(sql, [today])
        
        rows = get_rows(result)
        assert len(rows) > 0, "Should find the inserted record"
        assert rows[0][1] == today, "Date should match"
    
    def test_content_generation_logs_update(self, db):
        """Test UPDATE operation on content_generation_logs"""
        today = date.today().isoformat()
        sql = """
            UPDATE content_generation_logs 
            SET success_count = ?, failed_count = ?
            WHERE generation_date = ?
        """
        result = db.execute_sql(sql, [4, 1, today])
        
        verify = db.execute_sql("SELECT success_count, failed_count FROM content_generation_logs WHERE generation_date = ?", [today])
        rows = get_rows(verify)
        assert len(rows) > 0, "Record should exist"
        assert rows[0][0] == 4, "Success count should be updated"
        assert rows[0][1] == 1, "Failed count should be updated"
    
    def test_content_generation_logs_delete(self, db):
        """Test DELETE operation on content_generation_logs"""
        today = date.today().isoformat()
        sql = "DELETE FROM content_generation_logs WHERE generation_date = ?"
        result = db.execute_sql(sql, [today])
        
        verify = db.execute_sql("SELECT COUNT(*) FROM content_generation_logs WHERE generation_date = ?", [today])
        rows = get_rows(verify)
        count = rows[0][0] if rows else 0
        assert count == 0, "Record should be deleted"
    
    # ==========================================================================
    # PLATFORM_VALIDATION_LOGS CRUD TESTS
    # ==========================================================================
    
    def test_platform_validation_logs_create(self, db):
        """Test CREATE operation on platform_validation_logs"""
        sql = """
            INSERT INTO platform_validation_logs (platform, validation_type, is_valid, api_response_code)
            VALUES (?, ?, ?, ?)
        """
        params = ['twitter', 'token_check', 1, 200]
        
        result = db.execute_sql(sql, params)
        assert result is not None, "Insert should succeed"
    
    def test_platform_validation_logs_read(self, db):
        """Test READ operation on platform_validation_logs"""
        sql = "SELECT * FROM platform_validation_logs WHERE platform = ? ORDER BY validated_at DESC LIMIT 1"
        result = db.execute_sql(sql, ['twitter'])
        
        rows = get_rows(result)
        assert len(rows) > 0, "Should find the inserted record"
        assert rows[0][1] == 'twitter', "Platform should match"
    
    def test_platform_validation_logs_update(self, db):
        """Test UPDATE operation on platform_validation_logs"""
        # Get the latest record
        result = db.execute_sql(
            "SELECT id FROM platform_validation_logs WHERE platform = ? ORDER BY validated_at DESC LIMIT 1",
            ['twitter']
        )
        rows = get_rows(result)
        assert len(rows) > 0, "Record should exist"
        record_id = rows[0][0]
        
        sql = "UPDATE platform_validation_logs SET api_response_time_ms = ? WHERE id = ?"
        db.execute_sql(sql, [150, record_id])
        
        verify = db.execute_sql("SELECT api_response_time_ms FROM platform_validation_logs WHERE id = ?", [record_id])
        rows = get_rows(verify)
        assert len(rows) > 0, "Record should exist"
        assert rows[0][0] == 150, "Response time should be updated"
    
    def test_platform_validation_logs_delete(self, db):
        """Test DELETE operation on platform_validation_logs"""
        sql = "DELETE FROM platform_validation_logs WHERE platform = ?"
        result = db.execute_sql(sql, ['twitter'])
        
        verify = db.execute_sql("SELECT COUNT(*) FROM platform_validation_logs WHERE platform = ?", ['twitter'])
        rows = get_rows(verify)
        count = rows[0][0] if rows else 0
        assert count == 0, "Record should be deleted"
    
    # ==========================================================================
    # INDEX VERIFICATION TESTS
    # ==========================================================================
    
    def test_product_reviews_indexes_exist(self, db):
        """Test that product_reviews indexes exist"""
        indexes = db.list_indexes('product_reviews')
        assert 'idx_reviews_product_asin' in indexes, "Product ASIN index should exist"
        assert 'idx_reviews_active' in indexes, "Active index should exist"
        assert 'idx_reviews_created' in indexes, "Created index should exist"
    
    def test_social_integrations_indexes_exist(self, db):
        """Test that social_integrations indexes exist"""
        indexes = db.list_indexes('social_integrations')
        assert 'idx_integrations_platform' in indexes, "Platform index should exist"
        assert 'idx_integrations_active' in indexes, "Active index should exist"
    
    def test_social_posts_indexes_exist(self, db):
        """Test that social_posts indexes exist"""
        indexes = db.list_indexes('social_posts')
        assert 'idx_posts_product_asin' in indexes, "Product ASIN index should exist"
        assert 'idx_posts_platform' in indexes, "Platform index should exist"
        assert 'idx_posts_status' in indexes, "Status index should exist"
    
    def test_content_generation_logs_indexes_exist(self, db):
        """Test that content_generation_logs indexes exist"""
        indexes = db.list_indexes('content_generation_logs')
        assert 'idx_gen_logs_date' in indexes, "Date index should exist"
        assert 'idx_gen_logs_platform' in indexes, "Platform index should exist"
    
    def test_platform_validation_logs_indexes_exist(self, db):
        """Test that platform_validation_logs indexes exist"""
        indexes = db.list_indexes('platform_validation_logs')
        assert 'idx_val_logs_platform' in indexes, "Platform index should exist"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
