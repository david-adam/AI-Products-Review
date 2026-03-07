# Turso Migration Plan - Smaller Focused Steps

## Current Status
- ✅ `turso_http_client.py` created
- ✅ `trend_scraper.py` partially migrated
- ❌ Migration incomplete (subagent timeout at 5min)

## Remaining Tasks (Broken Down)

### Step 1: Complete Turso Table Creation (60s)
**Focus:** Ensure Turso cloud has the table schema
**Task:**
- Use turso_http_client.py to execute CREATE TABLE
- Verify table exists in Turso cloud
- Test basic INSERT/SELECT

**Deliverable:** Turso table ready, test query successful

---

### Step 2: Fix Title Extraction in Scraper (120s)
**Focus:** Update HTML parsing to extract titles correctly
**Task:**
- Find correct Amazon HTML selectors for product titles
- Update trend_scraper.py title extraction logic
- Test scraper on 5 products

**Deliverable:** Titles no longer show "N/A"

---

### Step 3: Add Missing Fields to Scraper (120s)
**Focus:** Extract image, affiliate_link, reviews
**Task:**
- Add image extraction
- Generate affiliate links: `https://www.amazon.com/dp/{asin}?tag=dav7aug-20`
- Extract review count
- Update database INSERT statements

**Deliverable:** All fields populated in Turso

---

### Step 4: Update .env and Clean Up (60s)
**Focus:** Configuration and cleanup
**Task:**
- Remove DB_PATH from .env
- Keep TURSO_* variables
- Delete local SQLite files
- Update run_trend_scraper.sh if needed

**Deliverable:** Clean configuration, no local DB files

---

### Step 5: Test End-to-End (90s)
**Focus:** Verify everything works
**Task:**
- Run scraper: `python3 trend_scraper.py`
- Check Turso for data
- Test /api/products endpoint
- Verify Vercel site displays data

**Deliverable:** Working end-to-end pipeline

---

### Step 6: Git Commit (60s)
**Focus:** Version control
**Task:**
- Stage all changes
- Commit with message: "Migrate to Turso-only database"
- Push to feature branch

**Deliverable:** Changes committed to git

---

## Total Estimated Time: 7.5 minutes (but broken into verifiable steps)
