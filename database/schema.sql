-- =============================================================================
-- ProductLens AI Phase 2 Database Schema
-- Turso/SQLite Database Schema for AI-generated reviews and social posting
-- =============================================================================

-- =============================================================================
-- PRODUCT REVIEWS TABLE
-- Stores AI-generated reviews for products with summary and full review text
-- =============================================================================
CREATE TABLE IF NOT EXISTS product_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign key to trending_products table
    product_asin TEXT NOT NULL,
    
    -- Review content
    -- Summary: 100-200 characters (AI-generated brief summary)
    summary TEXT NOT NULL CHECK(length(summary) >= 100 AND length(summary) <= 200),
    
    -- Full review: 600-900 characters (detailed AI-generated review)
    full_review TEXT NOT NULL CHECK(length(full_review) >= 600 AND length(full_review) <= 900),
    
    -- Review metadata
    rating REAL DEFAULT 4.0,  -- AI-assigned rating (1-5 scale)
    pros TEXT,  -- Comma-separated pros
    cons TEXT,  -- Comma-separated cons
    
    -- Image from Google Drive
    google_drive_image_url TEXT,
    google_drive_image_id TEXT,
    
    -- AI model used for generation
    ai_model TEXT DEFAULT 'kimi-k2.5',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_active INTEGER DEFAULT 1,
    
    -- Uniqueness constraint: one review per product
    CONSTRAINT unique_product_review UNIQUE(product_asin),
    FOREIGN KEY (product_asin) REFERENCES trending_products(asin) ON DELETE CASCADE
);

-- Index for fetching reviews by product
CREATE INDEX IF NOT EXISTS idx_reviews_product_asin ON product_reviews(product_asin);

-- Index for active reviews
CREATE INDEX IF NOT EXISTS idx_reviews_active ON product_reviews(is_active);

-- Index for sorting by creation date
CREATE INDEX IF NOT EXISTS idx_reviews_created ON product_reviews(created_at DESC);


-- =============================================================================
-- SOCIAL INTEGRATIONS TABLE
-- Stores platform credentials and configuration for social media posting
-- =============================================================================
CREATE TABLE IF NOT EXISTS social_integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Platform identifier
    platform TEXT NOT NULL CHECK(platform IN ('pinterest', 'twitter', 'instagram', 'telegram')),
    platform_name TEXT NOT NULL,
    
    -- Credentials (encrypted in production - storing as TEXT for now)
    -- Twitter/X
    twitter_api_key TEXT,
    twitter_api_secret TEXT,
    twitter_access_token TEXT,
    twitter_access_secret TEXT,
    twitter_bearer_token TEXT,
    
    -- Instagram (via Facebook/Graph API)
    instagram_access_token TEXT,
    instagram_page_id TEXT,
    instagram_account_id TEXT,
    
    -- Pinterest
    pinterest_access_token TEXT,
    pinterest_board_id TEXT,
    
    -- Telegram
    telegram_bot_token TEXT,
    telegram_channel_id TEXT,
    
    -- Generic API credentials (JSON format for extensibility)
    api_credentials TEXT,  -- JSON blob for additional platform-specific credentials
    
    -- Configuration
    is_active INTEGER DEFAULT 0,
    is_configured INTEGER DEFAULT 0,
    last_validation TIMESTAMP,
    validation_status TEXT,  -- 'valid', 'expired', 'error', NULL
    
    -- Rate limiting
    daily_post_limit INTEGER DEFAULT 10,
    hourly_post_limit INTEGER DEFAULT 3,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Uniqueness constraint
    CONSTRAINT unique_platform UNIQUE(platform)
);

-- Index for fetching integration by platform
CREATE INDEX IF NOT EXISTS idx_integrations_platform ON social_integrations(platform);

-- Index for active integrations
CREATE INDEX IF NOT EXISTS idx_integrations_active ON social_integrations(is_active);


-- =============================================================================
-- SOCIAL POSTS TABLE
-- Tracks social media posts per platform with daily content generation tracking
-- =============================================================================
CREATE TABLE IF NOT EXISTS social_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Foreign key to product
    product_asin TEXT NOT NULL,
    
    -- Foreign key to review (optional - post may not have associated review)
    review_id INTEGER,
    
    -- Platform
    platform TEXT NOT NULL CHECK(platform IN ('pinterest', 'twitter', 'instagram', 'telegram')),
    
    -- Post content (platform-specific)
    -- Twitter: 280 chars, Instagram: 2200 chars, Pinterest: 500 chars, Telegram: 4096 chars
    content_text TEXT NOT NULL,
    
    -- Post type
    post_type TEXT DEFAULT 'review',  -- 'review', 'promo', 'update', 'announcement'
    
    -- Media URLs
    image_url TEXT,  -- Main image (can be Google Drive URL)
    image_drive_id TEXT,  -- Google Drive file ID
    video_url TEXT,  -- Optional video
    
    -- Platform-specific fields
    -- Twitter
    tweet_id TEXT,
    tweet_url TEXT,
    
    -- Instagram
    instagram_media_id TEXT,
    instagram_post_url TEXT,
    
    -- Pinterest
    pin_id TEXT,
    pin_url TEXT,
    
    -- Telegram
    telegram_message_id INTEGER,
    telegram_message_url TEXT,
    
    -- Post status
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'published', 'failed', 'scheduled')),
    
    -- Scheduling
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    
    -- Error tracking
    error_message TEXT,
    error_code TEXT,
    
    -- Metrics (after publishing)
    impressions INTEGER DEFAULT 0,
    engagements INTEGER DEFAULT 0,
    clicks INTEGER DEFAULT 0,
    likes INTEGER DEFAULT 0,
    
    -- AI generation metadata
    ai_generated INTEGER DEFAULT 1,  -- Was content AI-generated?
    ai_model TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign keys
    FOREIGN KEY (product_asin) REFERENCES trending_products(asin) ON DELETE CASCADE,
    FOREIGN KEY (review_id) REFERENCES product_reviews(id) ON DELETE SET NULL
);

-- Index for fetching posts by product
CREATE INDEX IF NOT EXISTS idx_posts_product_asin ON social_posts(product_asin);

-- Index for fetching posts by platform
CREATE INDEX IF NOT EXISTS idx_posts_platform ON social_posts(platform);

-- Index for fetching posts by status
CREATE INDEX IF NOT EXISTS idx_posts_status ON social_posts(status);

-- Index for fetching posts by review
CREATE INDEX IF NOT EXISTS idx_posts_review ON social_posts(review_id);

-- Index for daily tracking - date extraction for daily aggregations
CREATE INDEX IF NOT EXISTS idx_posts_created_date ON social_posts(date(created_at));

-- Index for published posts
CREATE INDEX IF NOT EXISTS idx_posts_published ON social_posts(published_at);


-- =============================================================================
-- CONTENT GENERATION TRACKING TABLE
-- Tracks daily content generation for analytics and rate limiting
-- =============================================================================
CREATE TABLE IF NOT EXISTS content_generation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Date for daily tracking
    generation_date DATE NOT NULL,
    
    -- Generation type
    content_type TEXT NOT NULL,  -- 'review', 'image', 'social_post'
    platform TEXT,  -- NULL for reviews/images, specific for posts
    
    -- Counts
    generated_count INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    
    -- AI model used
    ai_model TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Uniqueness constraint per day/type/platform
    CONSTRAINT unique_daily_generation UNIQUE(generation_date, content_type, platform)
);

-- Index for daily tracking
CREATE INDEX IF NOT EXISTS idx_gen_logs_date ON content_generation_logs(generation_date);

-- Index for platform-specific tracking
CREATE INDEX IF NOT EXISTS idx_gen_logs_platform ON content_generation_logs(platform, generation_date);


-- =============================================================================
-- PLATFORM CREDENTIALS VALIDATION TRACKING
-- Track when credentials were last validated and their status
-- =============================================================================
CREATE TABLE IF NOT EXISTS platform_validation_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    platform TEXT NOT NULL,
    validation_type TEXT NOT NULL,  -- 'initial', 'refresh', 'test'
    
    -- Validation result
    is_valid INTEGER,
    error_message TEXT,
    error_code TEXT,
    
    -- Token info (if applicable)
    token_expires_at TIMESTAMP,
    token_refreshed_at TIMESTAMP,
    
    -- API response metadata
    api_response_code INTEGER,
    api_response_time_ms INTEGER,
    
    -- Timestamps
    validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Platform constraint
    CONSTRAINT unique_platform_validation UNIQUE(platform, validation_type, validated_at)
);

-- Index for platform validation history
CREATE INDEX IF NOT EXISTS idx_val_logs_platform ON platform_validation_logs(platform, validated_at DESC);
