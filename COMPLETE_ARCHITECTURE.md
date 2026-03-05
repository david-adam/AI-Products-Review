# Complete Architecture - Local + Vercel + Social Push

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TURSO CLOUD DATABASE                         │
│              libsql://amazon-affiliate-david-adam.turso.io          │
│                                                                      │
│  - trending_products table                                          │
│  - id, asin, title, price, rating, reviews, image                   │
│  - affiliate_link, product_summary, category, total_score           │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           │ Queried by BOTH
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          ▼                                 ▼
┌──────────────────────┐      ┌──────────────────────┐
│   LOCAL MACHINE      │      │    VERCEL SITE       │
│  (scraper_api/)      │      │ (gadgets-review.space)│
└──────────────────────┘      └──────────────────────┘
          │                                 │
          │ 1. SCRAPE                       │ 1. DISPLAY
          │                                 │
          ▼                                 ▼
┌──────────────────────┐      ┌──────────────────────┐
│  trend_scraper.py    │      │   products.html       │
│  - Scrapes Amazon    │      │   - Fetches /api/prods │
│  - Pushes to Turso   │      │   - Shows grid of items│
└──────────────────────┘      └──────────────────────┘
          │
          │ 2. GENERATE CONTENT
          ▼
┌──────────────────────┐
│  products_with_      │
│  content.json        │
│  - AI summaries      │
│  - Social posts      │
│  - SEO titles        │
└──────────────────────┘
          │
          │ 3. HUMAN REVIEW ⭐
          ▼
┌──────────────────────┐
│  Review Static File  │
│  - vim products_...  │
│  - Edit if needed    │
│  - Approve for post  │
└──────────────────────┘
          │
          │ 4. SOCIAL PUSH
          ▼
┌──────────────────────┐
│  social_push.py      │
│  - Telegram bot      │
│  - Twitter/X         │
│  - Facebook          │
└──────────────────────┘
```

## Data Flow Summary

### Phase 1: Data Collection (Local)
```python
# 1. Scrape products
python3 trend_scraper.py
# → Pushes to Turso cloud DB

# 2. Generate AI content
python3 generate_content.py  # (part of trend_scraper)
# → Creates products_with_content.json
```

### Phase 2: Human Review (Local) ⭐ KEY
```bash
# 3. Review static file
cat products_with_content.json
vim products_with_content.json  # Edit if needed

# 4. Check quality
- Product summaries accurate?
- Social posts engaging?
- No hallucinations or errors?
```

### Phase 3: Publication (Split)
```bash
# 5a. Push to Vercel (automatic)
git add products_with_content.json
git commit -m "Update products"
git push origin main
# → Vercel auto-deploys in 30s

# 5b. Post to Social (manual)
python3 social_push.py
# → Posts reviewed content to Telegram/Twitter
```

## File Locations

### Local Machine Only
```
/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/
├── trend_scraper.py          # Scrapes & generates content
├── products_with_content.json # Static file for review
├── ai_generated_content.json # Alternative format
├── social_push.py             # Posts to social networks
├── turso_http_client.py      # Turso DB client
└── .env                       # Local config (NOT on Vercel)
```

### Vercel Site (Deployed)
```
https://www.gadgets-review.space/
├── index.html                # Homepage
├── products.html             # Product discovery
├── privacy-policy.html       # Legal
└── api/
    └── products.js           # Serverless function (fetches Turso)
```

### Cloud Database (Shared)
```
Turso Cloud DB:
└── trending_products table
    - Queried by: local scraper + Vercel API
    - No local SQLite files needed
```

## Social Platforms

### ✅ Currently Active
- **Telegram** - Bot posts products with affiliate links
- Format: Product summary + specs + buy link + hashtags

### 🔜 Planned (Not Yet Configured)
- **Twitter/X** - Same content, shorter format
- **Facebook** - Same content, longer format
- **Pinterest** - Image-focused posts

## Human-in-the-Loop Quality Control

### Why Static File?

**Benefits:**
1. ✅ **Review** - Humans see content before it goes live
2. ✅ **Edit** - Fix AI mistakes, adjust tone, add context
3. � **Audit** - Track what was posted when (git history)
4. ✅ **Consistency** - Same format for all posts
5. ✅ **Safety** - No accidental posting of bad content

**Process:**
```
AI generates → Human reviews → Edit if needed → Approve → Post
```

### Quality Checklist

Before posting, verify:
- [ ] Product title is accurate
- [ ] Summary is helpful (not hallucinated)
- [ ] Social post is engaging
- [ ] Affiliate link works
- [ ] Hashtags are relevant
- [ ] No offensive or misleading content

## Sync Mechanism

### Vercel Auto-Deploy
```bash
git push origin main
→ Vercel webhook triggered
→ Builds and deploys in ~30s
→ Site updates automatically
```

### Turso Cloud DB
```bash
# Both local and Vercel query the same database
Local: python3 trend_scraper.py → writes to Turso
Vercel: /api/products → reads from Turso
# No sync needed - always in sync!
```

### Social Content
```bash
# Manual trigger (after human review)
python3 social_push.py
# Posts to configured platforms
```

## Summary

| Component | Location | Auto-Sync | Human Review |
|-----------|----------|-----------|--------------|
| **Data Collection** | Local | Manual ✗ | Manual ✓ |
| **Content Generation** | Local | Manual ✗ | Manual ✓ |
| **Quality Check** | Local | Manual ✗ | Manual ✓ ⭐ |
| **Social Posting** | Local | Manual ✗ | Manual ✓ |
| **Vercel Site** | Cloud | Auto ✓ | N/A |
| **Turso Database** | Cloud | Auto ✓ | N/A |

**Key Point:** Social posting has **mandatory human review** via static JSON file before anything goes live!
