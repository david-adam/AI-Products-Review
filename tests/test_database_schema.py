"""
TDD Test Suite for ProductLens AI Database Schema Deployment
Tests to verify all 5 Phase 2 tables are properly deployed to Turso
Uses HTTP API for Turso access
"""

import pytest
import os
import sys
import requests
from datetime import datetime, date

# Database configuration from environment
TURSO_DATABASE_URL = os.getenv(
    "TURSO_DATABASE_URL", 
    "libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io"
)
TURSO_AUTH_TOKEN = os.getenv("TURSO_AUTH_TOKEN", "")

# Convert to HTTP URL
HTTP_URL = TURSO_DATABASE_URL.replace("libsql://", "https://")

# Expected tables for Phase 2
EXPECTED_TABLES = [
    "trending_products",  # Base table
    "product_reviews",
    "social_integrations", 
    "social_posts",
    "content_generation_logs",
    "platform_validation_logs"
]

PHASE2_TABLES = [
    "product_reviews",
    "social_integrations",
    "social_posts",
    "content_generation_logs",
    "platform_validation_logs"
]


def execute_sql(sql: str, params: list = None) -> list:
    """Execute SQL via Turso HTTP API"""
    headers = {
        "Authorization": f"Bearer {TURSO_AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {"statements": [{"q": sql}]}
    if params:
        body["statements"][0]["params"] = params
    
    response = requests.post(HTTP_URL, headers=headers, json=body)
    response.raise_for_status()
    return response.json()


class TestDatabaseConnection:
    """Test 1: Verify database connection works"""
    
    def test_turso_credentials_exist(self):
        """Verify Turso credentials are configured"""
        assert TURSO_DATABASE_URL, "TURSO_DATABASE_URL must be set"
        assert TURSO_AUTH_TOKEN, "TURSO_AUTH_TOKEN must be set"
        assert "turso.io" in TURSO_DATABASE_URL, "Must be a Turso database URL"
    
    def test_database_connection(self):
        """Test that we can connect to Turso database"""
        result = execute_sql("SELECT 1")
        assert isinstance(result, list)
        assert len(result) > 0
        assert "results" in result[0]
        rows = result[0]["results"]["rows"]
        assert rows[0][0] == 1


class TestTableExistence:
    """Test 2: Verify all 5 Phase 2 tables exist in Turso"""
    
    @pytest.mark.parametrize("table_name", EXPECTED_TABLES)
    def test_table_exists(self, table_name):
        """Verify each expected table exists"""
        result = execute_sql(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            [table_name]
        )
        rows = result[0]["results"]["rows"]
        assert len(rows) == 1, f"Table {table_name} does not exist"
        assert rows[0][0] == table_name


class TestProductReviewsTable:
    """Test 3: Verify product_reviews table structure and CRUD"""
    
    def test_product_reviews_columns(self):
        """Verify product_reviews has all required columns"""
        expected_columns = [
            'id', 'product_asin', 'summary', 'full_review', 'rating',
            'pros', 'cons', 'google_drive_image_url', 'google_drive_image_id',
            'ai_model', 'created_at', 'updated_at', 'is_active'
        ]
        
        result = execute_sql("PRAGMA table_info(product_reviews)")
        columns = [row[1] for row in result[0]["results"]["rows"]]
        
        for col in expected_columns:
            assert col in columns, f"Column {col} missing from product_reviews"
    
    def test_product_reviews_insert_retrieve(self):
        """Test inserting and retrieving from product_reviews"""
        test_asin = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_summary = "A" * 150  # 150 chars, within 100-200 range
        test_review = "B" * 750   # 750 chars, within 600-900 range
        
        # First ensure test product exists
        execute_sql(
            """INSERT OR IGNORE INTO trending_products 
               (asin, title, category) VALUES (?, ?, ?)""",
            [test_asin, "Test Product", "Test Category"]
        )
        
        # Insert review
        execute_sql(
            """INSERT INTO product_reviews 
               (product_asin, summary, full_review, rating, pros, cons)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(product_asin) DO UPDATE SET
               summary=excluded.summary,
               full_review=excluded.full_review""",
            [test_asin, test_summary, test_review, 4.5, "Fast, Cheap", "None"]
        )
        
        # Retrieve and verify
        result = execute_sql(
            "SELECT * FROM product_reviews WHERE product_asin = ?",
            [test_asin]
        )
        
        rows = result[0]["results"]["rows"]
        assert len(rows) >= 1, "Failed to insert/retrieve product review"
        row = rows[0]
        assert row[1] == test_asin  # product_asin
        assert row[2] == test_summary  # summary
        assert row[3] == test_review  # full_review


class TestSocialIntegrationsTable:
    """Test 4: Verify social_integrations table structure and CRUD"""
    
    def test_social_integrations_columns(self):
        """Verify social_integrations has all required columns"""
        expected_columns = [
            'id', 'platform', 'platform_name', 'twitter_api_key', 'twitter_api_secret',
            'twitter_access_token', 'twitter_access_secret', 'twitter_bearer_token',
            'instagram_access_token', 'instagram_page_id', 'instagram_account_id',
            'pinterest_access_token', 'pinterest_board_id', 'telegram_bot_token',
            'telegram_channel_id', 'api_credentials', 'is_active', 'is_configured',
            'last_validation', 'validation_status', 'daily_post_limit', 'hourly_post_limit',
            'created_at', 'updated_at'
        ]
        
        result = execute_sql("PRAGMA table_info(social_integrations)")
        columns = [row[1] for row in result[0]["results"]["rows"]]
        
        for col in expected_columns:
            assert col in columns, f"Column {col} missing from social_integrations"
    
    def test_social_integrations_insert_retrieve(self):
        """Test inserting and retrieving from social_integrations"""
        # Insert test integration
        execute_sql(
            """INSERT OR REPLACE INTO social_integrations 
               (platform, platform_name, is_active, daily_post_limit)
               VALUES (?, ?, ?, ?)""",
            ["telegram", "Telegram Test", 0, 5]
        )
        
        # Retrieve and verify
        result = execute_sql(
            "SELECT platform, platform_name FROM social_integrations WHERE platform = ?",
            ["telegram"]
        )
        
        rows = result[0]["results"]["rows"]
        assert len(rows) >= 1, "Failed to insert/retrieve social integration"


class TestSocialPostsTable:
    """Test 5: Verify social_posts table structure and CRUD"""
    
    def test_social_posts_columns(self):
        """Verify social_posts has all required columns"""
        expected_columns = [
            'id', 'product_asin', 'review_id', 'platform', 'content_text',
            'post_type', 'image_url', 'image_drive_id', 'video_url',
            'tweet_id', 'tweet_url', 'instagram_media_id', 'instagram_post_url',
            'pin_id', 'pin_url', 'telegram_message_id', 'telegram_message_url',
            'status', 'scheduled_at', 'published_at', 'error_message', 'error_code',
            'impressions', 'engagements', 'clicks', 'likes', 'ai_generated',
            'ai_model', 'created_at', 'updated_at'
        ]
        
        result = execute_sql("PRAGMA table_info(social_posts)")
        columns = [row[1] for row in result[0]["results"]["rows"]]
        
        for col in expected_columns:
            assert col in columns, f"Column {col} missing from social_posts"
    
    def test_social_posts_insert_retrieve(self):
        """Test inserting and retrieving from social_posts"""
        test_asin = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Ensure test product exists
        execute_sql(
            """INSERT OR IGNORE INTO trending_products 
               (asin, title, category) VALUES (?, ?, ?)""",
            [test_asin, "Test Product", "Test Category"]
        )
        
        # Insert test post
        execute_sql(
            """INSERT INTO social_posts 
               (product_asin, platform, content_text, status)
               VALUES (?, ?, ?, ?)""",
            [test_asin, "telegram", "Test post content", "pending"]
        )
        
        # Retrieve and verify
        result = execute_sql(
            "SELECT product_asin, platform FROM social_posts WHERE product_asin = ?",
            [test_asin]
        )
        
        rows = result[0]["results"]["rows"]
        assert len(rows) >= 1, "Failed to insert/retrieve social post"


class TestContentGenerationLogsTable:
    """Test 6: Verify content_generation_logs table structure and CRUD"""
    
    def test_content_generation_logs_columns(self):
        """Verify content_generation_logs has all required columns"""
        expected_columns = [
            'id', 'generation_date', 'content_type', 'platform',
            'generated_count', 'success_count', 'failed_count',
            'ai_model', 'created_at', 'updated_at'
        ]
        
        result = execute_sql("PRAGMA table_info(content_generation_logs)")
        columns = [row[1] for row in result[0]["results"]["rows"]]
        
        for col in expected_columns:
            assert col in columns, f"Column {col} missing from content_generation_logs"
    
    def test_content_generation_logs_insert_retrieve(self):
        """Test inserting and retrieving from content_generation_logs"""
        today = date.today().isoformat()
        
        # Insert test log
        execute_sql(
            """INSERT OR REPLACE INTO content_generation_logs 
               (generation_date, content_type, platform, generated_count, success_count)
               VALUES (?, ?, ?, ?, ?)""",
            [today, "review", "telegram", 5, 4]
        )
        
        # Retrieve and verify
        result = execute_sql(
            """SELECT generation_date, content_type FROM content_generation_logs 
               WHERE generation_date = ? AND content_type = ?""",
            [today, "review"]
        )
        
        rows = result[0]["results"]["rows"]
        assert len(rows) >= 1, "Failed to insert/retrieve content generation log"


class TestPlatformValidationLogsTable:
    """Test 7: Verify platform_validation_logs table structure and CRUD"""
    
    def test_platform_validation_logs_columns(self):
        """Verify platform_validation_logs has all required columns"""
        expected_columns = [
            'id', 'platform', 'validation_type', 'is_valid', 'error_message',
            'error_code', 'token_expires_at', 'token_refreshed_at',
            'api_response_code', 'api_response_time_ms', 'validated_at'
        ]
        
        result = execute_sql("PRAGMA table_info(platform_validation_logs)")
        columns = [row[1] for row in result[0]["results"]["rows"]]
        
        for col in expected_columns:
            assert col in columns, f"Column {col} missing from platform_validation_logs"
    
    def test_platform_validation_logs_insert_retrieve(self):
        """Test inserting and retrieving from platform_validation_logs"""
        # Insert test validation log
        execute_sql(
            """INSERT INTO platform_validation_logs 
               (platform, validation_type, is_valid, api_response_code)
               VALUES (?, ?, ?, ?)""",
            ["telegram", "test", 1, 200]
        )
        
        # Retrieve and verify
        result = execute_sql(
            """SELECT platform, validation_type FROM platform_validation_logs 
               WHERE platform = ? ORDER BY validated_at DESC LIMIT 1""",
            ["telegram"]
        )
        
        rows = result[0]["results"]["rows"]
        assert len(rows) >= 1, "Failed to insert/retrieve platform validation log"


class TestIndexes:
    """Test 8: Verify all expected indexes exist"""
    
    @pytest.mark.parametrize("index_name", [
        "idx_reviews_product_asin",
        "idx_reviews_active", 
        "idx_reviews_created",
        "idx_integrations_platform",
        "idx_integrations_active",
        "idx_posts_product_asin",
        "idx_posts_platform",
        "idx_posts_status",
        "idx_posts_review",
        "idx_posts_created_date",
        "idx_posts_published",
        "idx_gen_logs_date",
        "idx_gen_logs_platform",
        "idx_val_logs_platform"
    ])
    def test_index_exists(self, index_name):
        """Verify each expected index exists"""
        result = execute_sql(
            "SELECT name FROM sqlite_master WHERE type='index' AND name=?",
            [index_name]
        )
        rows = result[0]["results"]["rows"]
        assert len(rows) == 1, f"Index {index_name} does not exist"


class TestConstraints:
    """Test 9: Verify table constraints work correctly"""
    
    def test_product_reviews_unique_constraint(self):
        """Test that product_reviews enforces unique product_asin"""
        test_asin = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Ensure test product exists
        execute_sql(
            """INSERT OR IGNORE INTO trending_products 
               (asin, title, category) VALUES (?, ?, ?)""",
            [test_asin, "Test Product", "Test Category"]
        )
        
        # Insert first review (using ON CONFLICT to handle existing)
        execute_sql(
            """INSERT INTO product_reviews 
               (product_asin, summary, full_review)
               VALUES (?, ?, ?)
               ON CONFLICT(product_asin) DO UPDATE SET
               summary=excluded.summary""",
            [test_asin, "A" * 150, "B" * 750]
        )
        
        # If we get here without error, constraint is handled properly
        result = execute_sql(
            "SELECT COUNT(*) FROM product_reviews WHERE product_asin = ?",
            [test_asin]
        )
        count = result[0]["results"]["rows"][0][0]
        assert count >= 1, "Should have at least one review for the product"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
