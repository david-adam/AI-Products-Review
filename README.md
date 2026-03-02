# ScraperAPI Adapter for Amazon Affiliate

## Environment Setup

1. **Create `.env` file** from `.env.example`:
```bash
cp .env.example .env
```

2. **Add your API key** to `.env`:
```
SCRAPERAPI_API_KEY=your_actual_api_key_here
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Quick Start
```bash
# Set your API key as environment variable
export SCRAPERAPI_API_KEY='your_api_key'

# Run example
python example_usage.py
```

### Using Environment File (.env)
The `.env` file is automatically loaded by `example_usage.py`:
```bash
python example_usage.py
```

## Configuration (.env file options)

- **SCRAPERAPI_API_KEY**: Your ScraperAPI key (required)
- **AMAZON_AFFILIATE_TAG**: Your Amazon Associates affiliate tag (optional)
- **DB_PATH**: Path to SQLite database (default: products.db)
- **PRODUCT_LIMIT**: Number of products to fetch (default: 20)

## Data Structure

Products are returned in **same format as Keepa API** for easy swapping:
```python
{
    'asin': 'B08N5WRWNW',
    'title': 'Product Name',
    'price': 99.99,
    'rating': 4.5,
    'sales_rank': 1234,
    'affiliate_link': 'https://www.amazon.com/dp/B08N5WRWNW?tag=YOUR_TAG'
}
```

## Tests

Run tests with:
```bash
pytest tests/
```

## Swapping from Keepa to ScraperAPI

**Before:**
```python
from keepa_api import KeepaClient
client = KeepaClient(api_key=...)
```

**After:**
```python
from scraper_api import AmazonScraper
client = AmazonScraper(api_key=...)
```

**Same interface!** All other code stays unchanged.

## Notes

- ScraperAPI returns HTML, which is parsed using BeautifulSoup
- Free tier: 5,000 credits on signup
- Pricing: ~$0.0025 per Amazon page
- Sign up at: https://scraperapi.com

---

**Free Tier:** 5,000 credits with signup at https://scraperapi.com
