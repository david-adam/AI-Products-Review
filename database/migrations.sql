-- =============================================================================
-- ProductLens AI Phase 2 - Migration Script
-- Run this to add Phase 2 tables to an existing database
-- =============================================================================
-- This migration adds the following tables:
--   - product_reviews (AI-generated reviews)
--   - social_integrations (platform credentials)
--   - social_posts (social media posts)
--   - content_generation_logs (daily tracking)
--   - platform_validation_logs (credential validation history)
-- =============================================================================

-- Migration 001: Create product_reviews table
CREATE TABLE IF NOT EXISTS product_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_asin TEXT NOT NULL,
    summary TEXT NOT NULL CHECK(length(summary) >= 100 AND length(summary) <= 200),
    full_review TEXT NOT NULL CHECK(length(full_review) >= 600 AND length(full_review) <= 900),
    rating REAL DEFAULT 4.0,
    pros TEXT,
    cons TEXT,
    google_drive_image_url TEXT,
    google_drive_image_id TEXT,
    ai_model TEXT DEFAULT 'kimi-k2.5',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    CONSTRAINT unique_product_review UNIQUE(product_asin),
    FOREIGN KEY (product_asin) REFERENCES trending_products(asin) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_reviews_product_asin ON product_reviews(product_asin);
CREATE INDEX IF NOT EXISTS idx_reviews_active ON product_reviews(is_active);
CREATE INDEX IF NOT EXISTS idx_reviews_created ON product_reviews(created_at DESC);

-- Migration 002: Create social_integrations table
CREATE TABLE IF NOT EXISTS social_integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL CHECK(platform IN ('pinterest', 'twitter', 'instagram', 'telegram')),
    platform_name TEXT NOT NULL,
    twitter_api_key TEXT,
    twitter_api_secret TEXT,
    twitter_access_token TEXT,
    twitter_access_secret TEXT,
    twitter_bearer_token TEXT,
    instagram_access_token TEXT,
    instagram_page_id TEXT,
    instagram_account_id TEXT,
    pinterest_access_token TEXT,
    pinterest_board_id TEXT,
    telegram_bot_token TEXT,
    telegram_channel_id TEXT,
    api_credentials TEXT,
    is_active INTEGER DEFAULT 0,
    is_configured INTEGER DEFAULT 0,
    last_validation TIMESTAMP,
    validation_status TEXT,
    daily_post_limit INTEGER DEFAULT 10,
    hourly_post_limit INTEGER DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_platform UNIQUE(platform)
);

CREATE INDEX IF NOT EXISTS idx_integrations_platform ON social_integrations(platform);
CREATE INDEX IF NOT EXISTS idx_integrations_active ON social_integrations(is_active);

-- Migration 003: Create social_posts table
CREATE TABLE IF NOT EXISTS social_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_asin TEXT NOT NULL,
    review_id INTEGER,
    platform TEXT NOT NULL CHECK(platform IN ('pinterest', 'twitter', 'instagram', 'telegram')),
    content_text TEXT NOT NULL,
    post_type TEXT DEFAULT 'review',
    image_url TEXT,
    image_drive_id TEXT,
    video_url TEXT,
    tweet_id TEXT,
    tweet_url TEXT,
    instagram_media_id TEXT,
    instagram_post_url TEXT,
    pin_id TEXT,
    pin_url TEXT,
    telegram_message_id INTEGER,
    telegram_message_url TEXT,
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'published', 'failed', 'scheduled')),
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    error_message TEXT,
    error_code TEXT,
    impressions INTEGER DEFAULT 0,
    engagements INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    ai_generated INTEGER DEFAULT 1,
    ai_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_asin) REFERENCES trending_products(asin) ON DELETE CASCADE,
    FOREIGN KEY (review_id) REFERENCES product_reviews(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_posts_product_asin ON social_posts(product_asin);
CREATE INDEX IF NOT EXISTS idx_posts_platform ON social_posts(platform);
CREATE INDEX IF NOT EXISTS idx_posts_status ON social_posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_review ON social_posts(review_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_date ON social_posts(date(created_at));
CREATE INDEX IF NOT EXISTS idx_posts_published ON social_posts(published_at);

-- Migration 004: Create content_generation_logs table
CREATE TABLE IF NOT EXISTS content_generation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    generation_date DATE NOT NULL,
    content_type TEXT NOT NULL,
    platform TEXT,
    generated_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    ai_model TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_daily_generation UNIQUE(generation_date, content_type, platform)
);

CREATE INDEX IF NOT EXISTS idx_gen_logs_date ON content_generation_logs(generation_date);
CREATE INDEX IF NOT EXISTS idx_gen_logs_platform ON content_generation_logs(platform, generation_date);

-- Migration 005: Create platform_validation_logs table
CREATE TABLE IF NOT EXISTS platform_validation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    validation_type TEXT NOT NULL,
    is_valid INTEGER,
    error_message TEXT,
    error_code TEXT,
    token_expires_at TIMESTAMP,
    token_refreshed_at TIMESTAMP,
    api_response_code INTEGER,
    api_response_time_ms INTEGER,
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_platform_validation UNIQUE(platform, validation_type, validated_at)
);

CREATE INDEX IF NOT EXISTS idx_val_logs_platform ON platform_validation_logs(platform, validated_at DESC);
