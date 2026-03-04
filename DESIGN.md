# Turso Migration Architecture Design

## Executive Summary

This document outlines the complete architecture design for migrating the trending product scraper from local SQLite to Turso cloud database. The migration is partially complete but has critical issues with title extraction and table initialization.

---

## 1. Current Architecture Analysis

### 1.1 Existing Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Trending Product Pipeline                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐     ┌──────────────────┐     ┌───────────┐ │
│  │ trend_scraper.py│────▶│turso_http_client.│────▶│   Turso   │ │
│  │  (Scraper)      │     │   py (Client)    │     │  Cloud DB │ │
│  └─────────────────┘     └──────────────────┘     └───────────┘ │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────────┐     ┌──────────────────┐                    │
│  │trending_asins.  │     │   api_server.py  │                    │
│  │      txt        │────▶│   (API Layer)    │                    │
│  └─────────────────┘     └──────────────────┘                    │
│                                   │                              │
│                                   ▼                              │
│                          ┌──────────────────┐                    │
│                          │   Vercel Site    │                    │
│                          └──────────────────┘                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Code Analysis: turso_http_client.py

**Strengths:**
- Proper Turso API v2 pipeline endpoint implementation
- Type-safe parameter binding with explicit type conversion
- Comprehensive CRUD operations (create, read, update, delete)
- Error handling with try/except blocks
- Environment variable support for credentials

**Architecture Pattern:**
```python
class TursoTrendingDB:
    - __init__(db_url, auth_token)     # Initialize with env fallback
    - _execute_sql(sql, params)        # Low-level API communication
    - create_table()                   # Schema creation
    - insert_or_update_product(product) # Upsert logic
    - get_top_products(limit, min_score) # Query with filtering
    - get_all_products(limit)          # Full dataset retrieval
    - get_stats()                      # Analytics
```

**API v2 Pipeline Format:**
```json
{
  "requests": [{
    "type": "execute",
    "stmt": {
      "sql": "SELECT * FROM table WHERE id = ?",
      "args": [
        {"type": "text", "value": "B123456789"},
        {"type": "integer", "value": "42"},
        {"type": "null"}
      ]
    }
  }]
}
```

### 1.3 Code Analysis: trend_scraper.py

**Current Flow:**
```
main()
  └── scrape_amazon_bestsellers(category)
        └── For each product card:
              ├── Extract ASIN (data-asin attribute) ✓
              ├── Extract title ✗ (BROKEN - shows "N/A")
              ├── Extract image ✓
              ├── Extract reviews ✓
              ├── Extract rank ✓
              ├── Extract price ✓
              ├── Extract rating ✓
              └── Generate affiliate_link ✓
        └── Return product dicts
  └── score_product(product)
        └── Calculate total_score (0-100)
  └── save_to_database(products)
        └── db.insert_or_update_product(product)
```

**Broken: Title Extraction Logic**
```python
# Current approach tries 9+ selectors but still fails
title_selectors = [
    'h2 a span',           # Most common structure
    'h2 span',             # Alternative structure  
    '.p13n-sc-truncated',  # Truncated title
    # ... 6 more selectors
]

# Fallback also fails
if not title or title == 'N/A':
    all_spans = card.find_all(['span', 'a'])
    # Text filtering is too restrictive
```

**Root Cause Analysis:**
1. Amazon's Best Sellers page uses dynamic rendering
2. Product cards may load titles via JavaScript or lazy loading
3. The current selectors don't match the actual DOM structure
4. Text length filtering (20-200 chars) may exclude valid short titles

---

## 2. Proposed Architecture

### 2.1 turso_http_client.py - No Changes Required

The HTTP client is well-designed and complete. Minor enhancements only.

**Existing Methods:**
| Method | Purpose | Status |
|--------|---------|--------|
| `__init__` | Initialize with env vars | ✓ Complete |
| `_execute_sql` | API v2 communication | ✓ Complete |
| `create_table` | Schema setup | ✓ Complete |
| `insert_or_update_product` | Upsert logic | ✓ Complete |
| `get_top_products` | Filtered retrieval | ✓ Complete |
| `get_all_products` | Full retrieval | ✓ Complete |
| `get_stats` | Analytics | ✓ Complete |

**Recommended Enhancement:** Add connection pooling for batch operations
```python
# Add to TursoTrendingDB:
def insert_products_batch(self, products: List[Dict]) -> Tuple[int, int]:
    """Batch insert with transaction support"""
    # Use pipeline API to batch requests
    # Return (success_count, error_count)
```

### 2.2 trend_scraper.py - Fix Title Extraction

**New Title Extraction Strategy:**
```python
def _extract_title(self, card, asin):
    """
    Multi-layer title extraction with progressive fallback
    
    Layer 1: Structured selectors (Amazon's semantic markup)
    Layer 2: Heuristic text extraction (content analysis)
    Layer 3: API fallback (fetch product page if needed)
    """
    # Layer 1: Try all known selectors
    selectors = [
        'h2 a span',                              # Standard grid
        'h2 span',                                # Alternative grid
        '.p13n-sc-truncated',                     # Legacy truncated
        '._cDEzb_p13n-sc-css-line-clamp-3_g3DGQ', # Current grid v1
        '._cDEzb_p13n-sc-css-line-clamp-2_g3DGQ', # Current grid v2
        '.a-size-base-plus',                      # Large text variant
        '.a-size-medium',                         # Medium text variant
        '[data-cy="title-recipe-title"] span',    # New data attribute
        'h2 a',                                   # Direct h2 link
    ]
    
    for selector in selectors:
        elem = card.select_one(selector)
        if elem:
            title = elem.get_text(strip=True)
            if self._is_valid_title(title):
                return title
    
    # Layer 2: Heuristic extraction
    # Find the longest text node that's not price/rating
    for elem in card.find_all(text=True):
        text = elem.strip()
        if self._is_valid_title(text):
            return text
    
    # Layer 3: Return ASIN-based placeholder
    return f"Product {asin}"

def _is_valid_title(self, text):
    """Validate if text looks like a product title"""
    if not text or len(text) < 3:
        return False
    if len(text) > 300:  # Too long
        return False
    # Filter out known bad patterns
    bad_patterns = [
        '$', 'out of', 'stars', 'rating', 'review',
        'Check each product', 'Visit the', 'Learn more',
        'Add to', 'Buy now', 'Best Seller', '#'
    ]
    return not any(p.lower() in text.lower() for p in bad_patterns)
```

### 2.3 Data Flow Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                        Data Flow Diagram                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────┐                                              │
│  │ Amazon Best      │                                              │
│  │ Sellers HTML     │                                              │
│  └────────┬─────────┘                                              │
│           │                                                         │
│           ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  trend_scraper.py                            │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐   │   │
│  │  │ scrape_amazon│─▶│ _extract_*   │─▶│ score_product()   │   │   │
│  │  │ _bestsellers │  │ methods      │  │ (calculate score) │   │   │
│  │  └─────────────┘  └──────────────┘  └─────────┬─────────┘   │   │
│  │                                               │               │   │
│  │  ┌────────────────────────────────────────────┘               │   │
│  │  │                                                            │   │
│  │  ▼                                                            │   │
│  │  ┌──────────────────────────────────────────────────────────┐ │   │
│  │  │ Product Dict Structure                                    │ │   │
│  │  │ {                                                         │ │   │
│  │  │   "asin": "B08N5WRWNW",         # Primary key             │ │   │
│  │  │   "title": "Product Name",      # Required               │ │   │
│  │  │   "category": "electronics",    # Category slug          │ │   │
│  │  │   "amazon_rank": 1,             # Best seller rank       │ │   │
│  │  │   "price": 29.99,               # Float                  │ │   │
│  │  │   "rating": 4.5,                # Float (0-5)            │ │   │
│  │  │   "reviews": 1234,              # Integer                │ │   │
│  │  │   "image": "https://...",        # URL                   │ │   │
│  │  │   "affiliate_link": "https://...", # Generated           │ │   │
│  │  │   "product_summary": "text",     # Auto-generated        │ │   │
│  │  │   "total_score": 85.5            # Calculated (0-100)   │ │   │
│  │  │ }                                                         │ │   │
│  │  └──────────────────────────────────────────────────────────┘ │   │
│  └───────────────────────────────────────────────────────────────┘   │
│                              │                                       │
│                              ▼                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              turso_http_client.py                            │    │
│  │  ┌──────────────────┐  ┌──────────────────────────────────┐ │    │
│  │  │ insert_or_update │─▶│  Turso HTTP API v2 Pipeline      │ │    │
│  │  │ _product()       │  │  POST /api/v2/pipeline           │ │    │
│  │  └──────────────────┘  └──────────────────────────────────┘ │    │
│  │                              │                              │    │
│  └──────────────────────────────┼──────────────────────────────┘    │
│                                 │                                    │
│                                 ▼                                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Turso Cloud Database                      │    │
│  │  ┌────────────────────────────────────────────────────────┐ │    │
│  │  │ trending_products table                                │ │    │
│  │  │ - id (PRIMARY KEY)                                     │ │    │
│  │  │ - asin (UNIQUE, INDEX)                                 │ │    │
│  │  │ - title, category, price, rating...                    │ │    │
│  │  │ - total_score (INDEX DESC)                             │ │    │
│  │  └────────────────────────────────────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. Step-by-Step Implementation Guide

### Phase 1: Table Creation (Priority: CRITICAL)

**Task:** Create trending_products table in Turso cloud

**Steps:**
1. Verify environment variables exist:
   ```bash
   echo $TURSO_DATABASE_URL
   echo $TURSO_AUTH_TOKEN
   ```

2. Run table creation:
   ```python
   from turso_http_client import TursoTrendingDB
   db = TursoTrendingDB()
   db.create_table()
   ```

3. Verify table exists:
   ```python
   result = db._execute_sql("SELECT name FROM sqlite_master WHERE type='table'")
   print(result)
   ```

**Verification Criteria:**
- No errors during create_table()
- Table appears in sqlite_master
- Can insert test row
- Can select test row

---

### Phase 2: Fix Title Extraction (Priority: CRITICAL)

**Task:** Update `scrape_amazon_bestsellers()` to correctly extract titles

**File:** `trend_scraper.py`

**Changes Required:**

1. **Add new helper methods** (insert after `__init__`):
   ```python
   def _extract_title(self, card, asin):
       """Extract product title with multiple fallback strategies"""
       # Implementation from Section 2.2
       pass
   
   def _is_valid_title(self, text):
       """Check if text is a valid product title"""
       # Implementation from Section 2.2
       pass
   ```

2. **Update title extraction in scrape_amazon_bestsellers()**:
   
   **REPLACE:**
   ```python
   # Current broken code (lines ~90-115)
   title = None
   title_selectors = [...]
   for selector in title_selectors:
       ...
   if not title or title == 'N/A':
       ...
   title = title if title else f"Amazon Product {asin}"
   ```
   
   **WITH:**
   ```python
   title = self._extract_title(card, asin)
   ```

3. **Test extraction**:
   ```bash
   python3 -c "
   from trend_scraper import TrendingProductScraper
   scraper = TrendingProductScraper()
   products = scraper.scrape_amazon_bestsellers('electronics', max_products=5)
   for p in products:
       print(f'{p[\"asin\"]}: {p[\"title\"][:60]}...')
   "
   ```

**Verification Criteria:**
- All 5 test products have meaningful titles (not "N/A")
- Titles are between 10-200 characters
- No titles contain "Amazon Product" fallback

---

### Phase 3: Field Extraction Enhancement (Priority: HIGH)

**Task:** Ensure all fields are properly extracted and saved

**Current Field Status:**

| Field | Extraction | DB Insert | Status |
|-------|-----------|-----------|--------|
| asin | ✓ | ✓ | Working |
| title | ✗ | ✓ | BROKEN |
| category | ✓ | ✓ | Working |
| amazon_rank | ✓ | ✓ | Working |
| price | ✓ | ✓ | Working |
| rating | ✓ | ✓ | Working |
| reviews | ✓ | ✓ | Working |
| image | ✓ | ✓ | Working |
| affiliate_link | ✓ | ✓ | Working |
| product_summary | ✓ | ✓ | Working |
| total_score | N/A (calculated) | ✓ | Working |

**No changes needed** - once title is fixed, all fields will work.

**Verification:**
```python
# After running scraper
from turso_http_client import TursoTrendingDB
db = TursoTrendingDB()
products = db.get_all_products(limit=5)
for p in products:
    print(f"ASIN: {p['asin']}")
    print(f"Title: {p['title']}")
    print(f"Image: {'✓' if p['image'] else '✗'}")
    print(f"Reviews: {p['reviews']}")
    print(f"Affiliate: {'✓' if p['affiliate_link'] else '✗'}")
    print(f"Summary: {p['product_summary'][:50]}...")
    print("---")
```

---

### Phase 4: End-to-End Testing (Priority: HIGH)

**Task:** Run complete pipeline and verify

**Test Script:**
```bash
#!/bin/bash
# test_pipeline.sh

echo "=== Phase 4: End-to-End Testing ==="

# 1. Run scraper
echo "Running scraper..."
python3 trend_scraper.py 2>&1 | tee scraper_output.log

# 2. Check Turso data
echo "Checking Turso database..."
python3 -c "
from turso_http_client import TursoTrendingDB
db = TursoTrendingDB()
stats = db.get_stats()
print(f'Total products: {stats[\"total_products\"]}')
products = db.get_top_products(limit=5)
for p in products:
    print(f\"  {p['total_score']:.0f}/100: {p['title'][:50]}...\")
"

# 3. Verify output files
echo "Checking output files..."
if [ -f "trending_asins.txt" ]; then
    echo "✓ trending_asins.txt exists ($(wc -l < trending_asins.txt) lines)"
else
    echo "✗ trending_asins.txt missing"
fi

echo "=== Test Complete ==="
```

**Success Criteria:**
- Scraper runs without errors
- At least 20 products saved to Turso
- All products have valid titles (not "N/A")
- trending_asins.txt is generated with ASINs
- Top products have scores > 40

---

### Phase 5: Configuration Cleanup (Priority: MEDIUM)

**Task:** Remove local SQLite dependencies

**Files to check:**
1. `.env` - Ensure no DB_PATH reference
2. `run_trend_scraper.sh` - Update if needed
3. Delete old SQLite files (after confirming Turso works):
   ```bash
   # Only after verification!
   mv trending_products.db trending_products.db.backup-final
   rm -f amazon_products.db products.db
   ```

---

## 4. Risk Assessment

### 4.1 High Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Amazon blocks scraper | Pipeline stops | Add delays, rotate User-Agents, use proxy if needed |
| Turso API changes | Database operations fail | Abstract client in turso_http_client.py for easy updates |
| Title extraction keeps failing | Data quality poor | Implement multiple fallback strategies, add logging |

### 4.2 Medium Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rate limiting on Turso | Operations slow/fail | Implement exponential backoff, batch operations |
| Environment variables missing | Connection fails | Add validation in __init__ with clear error messages |
| HTML structure changes | Extraction breaks | Add monitoring, alerts for low extraction rates |

### 4.3 Low Risk

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during migration | Historical data lost | Keep local backups until verified |
| Scoring algorithm issues | Wrong products prioritized | Monitor top products, adjust weights if needed |

---

## 5. Testing Strategy

### 5.1 Unit Tests

```python
# test_title_extraction.py
def test_extract_title_from_various_selectors():
    """Test title extraction with mocked HTML"""
    pass

def test_is_valid_title_filters():
    """Test title validation logic"""
    pass

def test_score_product_calculation():
    """Test scoring algorithm"""
    pass
```

### 5.2 Integration Tests

```python
# test_turso_integration.py
def test_create_table():
    """Test table creation in Turso"""
    pass

def test_insert_and_retrieve():
    """Test round-trip data flow"""
    pass

def test_get_top_products():
    """Test filtered query"""
    pass
```

### 5.3 End-to-End Tests

```bash
# Full pipeline test
python3 trend_scraper.py
# Verify: Products in Turso, titles valid, scores calculated
```

---

## 6. Rollback Plan

If migration fails:

1. **Immediate (0-5 min):**
   ```bash
   # Restore from backup
   cp trending_products.db.backup-20260304-182229 trending_products.db
   ```

2. **Short-term (5-30 min):**
   - Revert trend_scraper.py to SQLite version
   - Update .env to include DB_PATH

3. **Long-term (30+ min):**
   - Debug Turso connection issues
   - Review error logs in `logs/` directory
   - Consult Turso documentation for API changes

---

## 7. Summary Checklist

- [ ] **Phase 1:** Turso table created and verified
- [ ] **Phase 2:** Title extraction fixed and tested
- [ ] **Phase 3:** All fields properly populated
- [ ] **Phase 4:** End-to-end pipeline tested
- [ ] **Phase 5:** Configuration cleaned up
- [ ] **Phase 6:** Git commit with migration message

---

## Appendix A: Database Schema

```sql
CREATE TABLE trending_products (
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

CREATE INDEX idx_asin ON trending_products(asin);
CREATE INDEX idx_total_score ON trending_products(total_score DESC);
CREATE INDEX idx_category ON trending_products(category);
```

## Appendix B: Environment Variables

```bash
# Required
export TURSO_DATABASE_URL="libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io"
export TURSO_AUTH_TOKEN="<your-auth-token>"

# Optional
export LOG_LEVEL="INFO"
```

---

*Document Version: 1.0*
*Last Updated: 2026-03-04*
