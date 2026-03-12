-- =============================================================================
-- ProductLens AI Analytics Database Schema
-- Tracks user behavior, page views, clicks, and revenue
-- =============================================================================

-- =============================================================================
-- PAGE VIEWS TABLE
-- Tracks each page view for products
-- =============================================================================
CREATE TABLE IF NOT EXISTS page_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Product ASIN (foreign key)
    product_asin TEXT,
    
    -- Page type: 'product', 'home', 'search', 'review'
    page_type TEXT NOT NULL DEFAULT 'product',
    
    -- Session/User tracking (anonymous)
    session_id TEXT,
    user_agent TEXT,
    
    -- Referrer (where the user came from)
    referrer TEXT,
    
    -- Location (approximate)
    country TEXT,
    city TEXT,
    
    -- UTM parameters for marketing tracking
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    
    -- Device info
    device_type TEXT,  -- 'desktop', 'mobile', 'tablet'
    browser TEXT,
    
    -- Timestamps
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key (optional - can be null for non-product pages)
    FOREIGN KEY (product_asin) REFERENCES trending_products(asin) ON DELETE SET NULL
);

-- Indexes for analytics queries
CREATE INDEX IF NOT EXISTS idx_page_views_product ON page_views(product_asin);
CREATE INDEX IF NOT EXISTS idx_page_views_datetime ON page_views(viewed_at DESC);
CREATE INDEX IF NOT EXISTS idx_page_views_session ON page_views(session_id);
CREATE INDEX IF NOT EXISTS idx_page_views_country ON page_views(country);
CREATE INDEX IF NOT EXISTS idx_page_views_type ON page_views(page_type);


-- =============================================================================
-- AMAZON CLICKS TABLE
-- Tracks clicks through to Amazon (affiliate link clicks)
-- =============================================================================
CREATE TABLE IF NOT EXISTS amazon_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Product ASIN
    product_asin TEXT NOT NULL,
    
    -- Click metadata
    session_id TEXT,
    user_agent TEXT,
    referrer TEXT,
    
    -- Location
    country TEXT,
    city TEXT,
    
    -- Device info
    device_type TEXT,
    browser TEXT,
    
    -- Amazon link type: 'affiliate', 'direct', 'search'
    link_type TEXT DEFAULT 'affiliate',
    
    -- Whether purchase was made (tracked via Amazon API if available)
    conversion_tracked INTEGER DEFAULT 0,
    order_id TEXT,
    revenue REAL DEFAULT 0.0,
    
    -- Timestamps
    clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (product_asin) REFERENCES trending_products(asin) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_clicks_product ON amazon_clicks(product_asin);
CREATE INDEX IF NOT EXISTS idx_clicks_datetime ON amazon_clicks(clicked_at DESC);
CREATE INDEX IF NOT EXISTS idx_clicks_session ON amazon_clicks(session_id);
CREATE INDEX IF NOT EXISTS idx_clicks_revenue ON amazon_clicks(revenue);


-- =============================================================================
-- SEARCH QUERIES TABLE
-- Tracks user search queries
-- =============================================================================
CREATE TABLE IF NOT EXISTS search_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Search query
    query TEXT NOT NULL,
    
    -- Search context
    search_type TEXT DEFAULT 'products',  -- 'products', 'reviews', 'all'
    
    -- Results info
    results_count INTEGER DEFAULT 0,
    clicked_result_asin TEXT,  -- If user clicked a result
    
    -- User info
    session_id TEXT,
    country TEXT,
    city TEXT,
    
    -- Whether search returned results
    found_results INTEGER DEFAULT 1,
    
    -- Timestamps
    searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_searches_query ON search_queries(query);
CREATE INDEX IF NOT EXISTS idx_searches_datetime ON search_queries(searched_at DESC);
CREATE INDEX IF NOT EXISTS idx_searches_session ON search_queries(session_id);


-- =============================================================================
-- DAILY ANALYTICS SUMMARY
-- Pre-aggregated daily metrics for fast dashboard loading
-- =============================================================================
CREATE TABLE IF NOT EXISTS daily_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Date (YYYY-MM-DD)
    analytics_date DATE NOT NULL UNIQUE,
    
    -- Page views
    total_page_views INTEGER DEFAULT 0,
    product_page_views INTEGER DEFAULT 0,
    unique_visitors INTEGER DEFAULT 0,
    
    -- Amazon clicks
    total_amazon_clicks INTEGER DEFAULT 0,
    affiliate_clicks INTEGER DEFAULT 0,
    
    -- Revenue (estimated)
    estimated_revenue REAL DEFAULT 0.0,
    conversion_count INTEGER DEFAULT 0,
    
    -- Search
    total_searches INTEGER DEFAULT 0,
    unique_search_queries INTEGER DEFAULT 0,
    
    -- Top products (stored as JSON array of ASINs)
    top_products TEXT,  -- JSON: ['asin1', 'asin2', ...]
    
    -- Top countries (stored as JSON)
    top_countries TEXT,  -- JSON: [{'country': 'US', 'views': 100}, ...]
    
    -- Traffic sources (stored as JSON)
    traffic_sources TEXT,  -- JSON: [{'source': 'google', 'views': 50}, ...]
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index
CREATE INDEX IF NOT EXISTS idx_daily_analytics_date ON daily_analytics(analytics_date DESC);


-- =============================================================================
-- REVENUE TRACKING TABLE
-- Tracks individual conversions/revenue events
-- =============================================================================
CREATE TABLE IF NOT EXISTS revenue_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Product
    product_asin TEXT NOT NULL,
    product_title TEXT,
    
    -- Amazon tracking
    amazon_order_id TEXT,
    affiliate_tag TEXT,
    
    -- Revenue details
    sale_amount REAL DEFAULT 0.0,  -- Total order amount
    commission_rate REAL DEFAULT 0.03,  -- Default 3% affiliate commission
    estimated_commission REAL DEFAULT 0.0,
    
    -- Currency
    currency TEXT DEFAULT 'USD',
    
    -- Conversion info
    session_id TEXT,
    click_id INTEGER,  -- Link to amazon_clicks
    
    -- Status: 'pending', 'confirmed', 'cancelled'
    status TEXT DEFAULT 'pending',
    
    -- Timestamps
    sale_date DATE,
    tracked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    
    -- Foreign key
    FOREIGN KEY (product_asin) REFERENCES trending_products(asin) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_revenue_product ON revenue_events(product_asin);
CREATE INDEX IF NOT EXISTS idx_revenue_date ON revenue_events(sale_date DESC);
CREATE INDEX IF NOT EXISTS idx_revenue_status ON revenue_events(status);
CREATE INDEX IF NOT EXISTS idx_revenue_session ON revenue_events(session_id);
