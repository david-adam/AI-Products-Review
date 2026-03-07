-- Create trending_products table in Turso
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
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_asin ON trending_products(asin);
CREATE INDEX IF NOT EXISTS idx_total_score ON trending_products(total_score DESC);
CREATE INDEX IF NOT EXISTS idx_category ON trending_products(category);
