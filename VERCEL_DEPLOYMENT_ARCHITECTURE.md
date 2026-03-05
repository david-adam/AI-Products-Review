# Vercel Deployment Architecture - Auto-Sync Setup

## Current Architecture

### ✅ **Already Configured Correctly**

**1. Single Codebase**
- Local: `/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/`
- Remote: `git@github.com:david-adam/AI-Products-Review.git`
- Vercel: Connected to GitHub repo (auto-deploys on push)

**2. Shared Database (Turso Cloud)**
- Both local and Vercel use the **same Turso cloud database**
- URL: `libsql://amazon-affiliate-david-adam.aws-ap-northeast-1.turso.io`
- No local SQLite files needed anymore
- Data is automatically synced

**3. API Endpoint (Vercel Serverless)**
- File: `/api/products.js` (Vercel serverless function)
- Endpoint: `https://www.gadgets-review.space/api/products`
- Queries Turso cloud database directly
- Returns JSON with all products (title, price, rating, image, etc.)

**4. Frontend Files**
- `index.html` - Homepage
- `products.html` - Product Discovery page
- `privacy-policy.html` - Privacy Policy
- All use `/api/products` endpoint to fetch data

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      Turso Cloud Database                    │
│              (amazon-affiliate-david-adam.turso.io)         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ BOTH local & Vercel query this
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
┌──────────────────┐      ┌──────────────────┐
│  Local Machine   │      │   Vercel Site    │
│  (Python script) │      │  (/api/products) │
│  scrapes data    │      │  fetches data    │
│  pushes to Turso │      │  displays in HTML│
└──────────────────┘      └──────────────────┘
```

## Auto-Sync Mechanism

### ✅ **Already Working!**

**1. Automatic Frontend Sync**
- Push to GitHub → Vercel auto-deploys within seconds
- No manual action needed
- All HTML/CSS/JS files update automatically

**2. Automatic Data Sync**
- Local scraper runs → Pushes to Turso cloud
- Vercel `/api/products` → Queries same Turso cloud
- No local database files on Vercel
- Data is always in sync

### Current Workflow

```bash
# 1. Make local changes
vim index.html
vim privacy-policy.html

# 2. Commit and push
git add index.html privacy-policy.html
git commit -m "Update site branding and privacy policy"
git push origin main

# 3. Vercel auto-deploys (within 30 seconds)
# Site updates automatically at: https://www.gadgets-review.space
```

## Social Push Workflow

### ✅ **Human Review Before Social Posting**

**Step 1: Fetch from Turso**
```bash
# Local scraper fetches products from Turso cloud DB
python3 trend_scraper.py
```

**Step 2: Generate Content**
```bash
# Creates products_with_content.json with AI-generated:
# - product_summary (200 words)
# - social_post (Twitter/Telegram format)
# - seo_title
# - blog_outline
```

**Step 3: Human Review** ⭐ KEY STEP
```bash
# Humans review the static JSON file
cat products_with_content.json

# Edit if needed
vim products_with_content.json
```

**Step 4: Social Push**
```bash
# Post reviewed content to social networks
python3 social_push.py

# Posts to:
# - Telegram (bot)
# - Twitter/X (if configured)
# - Facebook (if configured)
```

### Files Involved

**Local Only (NOT on Vercel):**
- ✅ `products_with_content.json` - Static file with AI-generated content
- ✅ `ai_generated_content.json` - Alternative format
- ✅ `social_push.py` - Posts to social networks
- ✅ Review workflow - Human checks content before posting

**Why Static File?**
- ✅ Humans can review and edit before posting
- ✅ Version control (git track changes)
- ✅ Audit trail (what was posted when)
- ✅ Quality control (catch AI mistakes)
- ✅ Consistency (same format for all posts)

## Files to Deploy

### Already Updated (Ready to Push):
- ✅ `index.html` - New branding (ProductLens AI)
- ✅ `products.html` - New branding
- ✅ `privacy-policy.html` - Human-in-the-loop content
- ✅ `api/products.js` - Already configured for Turso

### Not on Vercel (Local Only):
- ❌ `trend_scraper.py` - Scraping logic
- ❌ `social_push.py` - Social media posting
- ❌ `*.db` - Local SQLite files (deleted after migration)
- ❌ `logs/` - Local log files
- ❌ `.env` - Local environment config

## Deployment Steps

To deploy the current updates:

```bash
cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api

# Stage the HTML files
git add index.html products.html privacy-policy.html

# Commit changes
git commit -m "feat: Rebrand to ProductLens AI + update privacy policy with human-in-the-loop"

# Push to GitHub (triggers Vercel auto-deploy)
git push origin main

# Vercel will auto-deploy within 30 seconds
# Check: https://www.gadgets-review.space
```

## Verification

After deployment, verify:

1. **Homepage:** https://www.gadgets-review.space
   - Title: "ProductLens AI - Smart Product Reviews"
   - Logo: "PL" (not "AB")
   - Tagline updated

2. **Product Discovery:** https://www.gadgets-review.space/products.html
   - Fetches from `/api/products`
   - Displays Turso cloud data
   - Shows all products with AI summaries

3. **Privacy Policy:** https://www.gadgets-review.space/privacy-policy.html
   - Section 3: "How Our Content Works"
   - Human-in-the-loop section present
   - Updated March 5, 2026

## Summary

✅ **Auto-sync is already working**
✅ **Single codebase** (GitHub → Vercel)
✅ **Shared cloud database** (Turso)
✅ **Automatic deployment** on git push
✅ **No manual steps needed**

The architecture is correctly set up. Just push the changes and Vercel will auto-deploy!
