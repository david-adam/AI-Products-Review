# Local + Vercel Sync Setup - Complete ✅

## Architecture

### ✅ Both Local and Vercel Fetch from Turso

```
┌─────────────────────────────────────────────────────────────┐
│                    TURSO CLOUD DATABASE                      │
│    libsql://amazon-affiliate-david-adam.turso.io           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ Queried by BOTH
                           │
          ┌────────────────┴────────────────┐
          │                                 │
          ▼                                 ▼
┌──────────────────────┐      ┌──────────────────────┐
│   LOCAL SERVER       │      │   VERCEL SITE        │
│  (localhost:8080)    │      │ (gadgets-review.space)│
│                      │      │                      │
│  local_api_server.py │      │  api/products.js     │
│  Proxies to Turso    │      │  Serverless function │
└──────────────────────┘      └──────────────────────┘
          │                                 │
          │ Both serve same HTML files     │
          │ products.html                  │
          │ social_push.html               │
          └─────────────────────────────────┘
```

## Files Updated

### 1. ✅ products.html
- **Primary:** Fetch from `/api/products` (Turso)
- **Fallback:** `products_with_content.json` (network errors only)
- **Warning:** Shows "Offline Mode" when using fallback
- **Same behavior** on both local and Vercel

### 2. ✅ social_push.html
- **Primary:** Fetch from `/api/products` (Turso)
- **Fallback:** `products_with_content.json` (network errors only)
- **Warning:** Shows "Offline Mode" when using fallback
- **Same behavior** on both local and Vercel

### 3. ✅ local_api_server.py (NEW)
- Proxies `/api/products` to Turso cloud DB
- Mirrors Vercel serverless function behavior
- Serves static files (HTML, CSS, JS)
- Runs on http://localhost:8080

### 4. ✅ export_from_turso.py (NEW)
- Exports Turso data to `products_with_content.json`
- Updates local cache for offline fallback
- Run after scraping to sync local files

## Usage

### Start Local Server
```bash
cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api
python3 local_api_server.py
```

### Access Points
- **Products:** http://localhost:8080/products.html
- **Social Push:** http://localhost:8080/social_push.html
- **API:** http://localhost:8080/api/products

### Sync Local Cache
```bash
# After scraping, export to JSON for offline fallback
python3 export_from_turso.py
```

## Behavior

### ✅ Normal Mode (Online)
```
products.html → /api/products → Turso Cloud DB → Products ✅
social_push.html → /api/products → Turso Cloud DB → Products ✅
```

### ⚠️ Offline Mode (Network Error)
```
products.html → products_with_content.json → Cached Products ⚠️
social_push.html → products_with_content.json → Cached Products ⚠️
```

## Data Flow

### Scrape Products
```bash
python3 trend_scraper.py
# → Saves to Turso cloud DB
```

### Sync Local Cache
```bash
python3 export_from_turso.py
# → Updates products_with_content.json
# → Updates ai_generated_content.json
```

### Local Development
```bash
python3 local_api_server.py
# → http://localhost:8080
# → Fetches from Turso (same as Vercel)
```

### Production (Vercel)
```
https://www.gadgets-review.space
# → Fetches from Turso (same as local)
# → Auto-deploys from git push
```

## Key Points

✅ **Local and Vercel are identical** - Both fetch from Turso
✅ **Local fallback only** - For network errors, not default
✅ **Sync workflow** - Run `export_from_turso.py` to update cache
✅ **Warning system** - Shows when in offline mode
✅ **Single source of truth** - Turso cloud database

## Testing

### Local Server
```bash
curl http://localhost:8080/api/products?limit=5
# Should return JSON from Turso
```

### Vercel Site
```bash
curl https://www.gadgets-review.space/api/products?limit=5
# Should return identical JSON from Turso
```

### Products Page
- Local: http://localhost:8080/products.html
- Vercel: https://www.gadgets-review.space/products.html
- Both should show identical products from Turso

## Troubleshooting

### Local server not working
```bash
# Check if port 8080 is free
lsof -i :8080

# Kill existing server
killall python3

# Restart
python3 local_api_server.py
```

### Products not loading
```bash
# Test Turso connection
python3 export_from_turso.py

# Update local cache
python3 export_from_turso.py
```

### Vercel site not working
```bash
# Check deployment
vercel list

# View logs
vercel logs
```

## Summary

Both local and Vercel now:
1. ✅ Fetch products from Turso cloud DB
2. ✅ Have identical behavior and appearance
3. ✅ Use local fallback only for network errors
4. ✅ Show warnings when in offline mode
5. ✅ Sync via `export_from_turso.py`
