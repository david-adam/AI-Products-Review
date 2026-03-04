#!/usr/bin/env python3
"""
Trending Product Discovery Pipeline
Scrapes Amazon Best Sellers, Google Trends, Reddit, and more to find trending products
Uses Turso remote database (no local SQLite)
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
import logging
import re
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import Turso HTTP client
from turso_http_client import TursoTrendingDB

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TrendingProductScraper:
    """Discover trending products from multiple sources"""
    
    def __init__(self, db_url=None, auth_token=None):
        """
        Initialize scraper with Turso database
        
        Args:
            db_url: Turso database URL
            auth_token: Turso auth token
        """
        # Initialize Turso database
        self.db = TursoTrendingDB(
            db_url=db_url or os.getenv('TURSO_DATABASE_URL'),
            auth_token=auth_token or os.getenv('TURSO_AUTH_TOKEN')
        )
        self.db.create_table()
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def _is_valid_title(self, text: str) -> bool:
        """
        Validate if text looks like a product title
        
        Args:
            text: Text to validate
            
        Returns:
            True if valid product title
        """
        if not text or len(text) < 3:
            return False
        if len(text) > 300:  # Too long
            return False
        # Filter out known bad patterns
        bad_patterns = [
            '$', 'out of', 'stars', 'rating', 'review',
            'Check each product', 'Visit the', 'Learn more',
            'Add to', 'Buy now', 'Best Seller', '#', 'See more',
            'Click to', 'Free shipping', 'Prime delivery'
        ]
        text_lower = text.lower()
        return not any(p.lower() in text_lower for p in bad_patterns)
    
    def _extract_title(self, card, asin: str) -> str:
        """
        Extract product title with multiple fallback strategies
        
        Args:
            card: BeautifulSoup element for product card
            asin: Product ASIN for fallback
            
        Returns:
            Product title string
        """
        # Layer 1: Try structured selectors (Amazon's semantic markup)
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
        
        # Layer 2: Heuristic extraction - find longest valid text node
        for elem in card.find_all(['span', 'a', 'div']):
            text = elem.get_text(strip=True)
            if self._is_valid_title(text) and len(text) > 10:
                # Prefer longer titles (more descriptive)
                if len(text) > 30:
                    return text
        
        # Layer 3: Return ASIN-based placeholder only as last resort
        return f"Product {asin}"
    
    def scrape_amazon_bestsellers(self, category='electronics', max_products=50):
        """
        Scrape Amazon Best Sellers page
        
        Args:
            category: Category to scrape (electronics, computers, diy)
            max_products: Maximum number of products to return
        
        Returns:
            List of trending products
        """
        logger.info(f"🔍 Scraping Amazon Best Sellers: {category}")
        
        category_urls = {
            'electronics': 'https://www.amazon.com/Best-Sellers-Electronics/zgbs/electronics',
            'computers': 'https://www.amazon.com/Best-Sellers-Computers-Accessories/zgbs/pc',
            'diy': 'https://www.amazon.com/Best-Sellers-Pati-Cooking-DIY-Tools/zgbs/pc',
            'sbc': 'https://www.amazon.com/Best-Sellers-Computers-Features-Single-Board-Computers/zgbs/pc/3012281011'
        }
        
        url = category_urls.get(category, category_urls['electronics'])
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            products = []
            
            # Find product cards - Amazon uses data-asin for product IDs
            product_cards = soup.find_all('div', {'data-asin': True})
            
            for card in product_cards[:max_products]:
                try:
                    asin = card.get('data-asin')
                    
                    if not asin or len(asin) != 10:
                        continue
                    
                    # Extract title - using multi-layer extraction
                    title = self._extract_title(card, asin)
                    
                    # Extract product image
                    image = None
                    img_elem = card.find('img')
                    if img_elem:
                        image = img_elem.get('src') or img_elem.get('data-old-hi-res') or img_elem.get('data-a-dynamic-image')
                        # Handle dynamic image JSON
                        if image and image.startswith('{'):
                            try:
                                images_dict = json.loads(image.replace("'", '"'))
                                image = list(images_dict.keys())[0] if images_dict else None
                            except:
                                image = None
                    
                    # Extract review count
                    reviews = 0
                    # Try multiple selectors for reviews
                    review_selectors = [
                        'span.a-size-small',
                        '.a-link-typography',
                        'a[href*="reviews"]',
                        '.a-size-base'
                    ]
                    for selector in review_selectors:
                        reviews_elem = card.select_one(selector)
                        if reviews_elem:
                            reviews_text = reviews_elem.get_text(strip=True)
                            # Match patterns like "1,234" or "1234"
                            match = re.search(r'([\d,]+)\s*(?:ratings?|reviews?)', reviews_text, re.IGNORECASE)
                            if match:
                                try:
                                    reviews = int(match.group(1).replace(',', ''))
                                    break
                                except:
                                    pass
                    
                    # Extract rank
                    rank = None
                    rank_elem = card.find('span', class_='zg-badge-text')
                    if rank_elem:
                        rank_text = rank_elem.text.strip()
                        rank_match = re.search(r'(\d+)', rank_text)
                        if rank_match:
                            rank = int(rank_match.group(1))
                    
                    # Extract price
                    price = None
                    price_selectors = [
                        'span.p13n-sc-price',
                        'span.a-price-whole',
                        'span.a-price .a-offscreen',
                        '.a-price-range'
                    ]
                    for selector in price_selectors:
                        price_elem = card.select_one(selector)
                        if price_elem:
                            price_text = price_elem.text.strip()
                            # Extract number from price text
                            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                            if price_match:
                                try:
                                    price = float(price_match.group().replace(',', ''))
                                    break
                                except:
                                    pass
                    
                    # Extract rating
                    rating = None
                    rating_elem = card.find('span', class_='a-icon-alt')
                    if rating_elem:
                        rating_text = rating_elem.text.strip()
                        rating_match = re.search(r'([\d.]+)\s*out of', rating_text)
                        if rating_match:
                            try:
                                rating = float(rating_match.group(1))
                            except:
                                pass
                    
                    # Generate affiliate link
                    affiliate_link = f"https://www.amazon.com/dp/{asin}?tag=dav7aug-20"
                    
                    # Generate product summary
                    product_summary = f"Trending {category} product"
                    if rank:
                        product_summary += f" ranked #{rank} on Amazon"
                    if price:
                        product_summary += f" with ${price:.2f} price"
                    if rating:
                        product_summary += f" and {rating} rating"
                    product_summary += "."
                    
                    products.append({
                        'asin': asin,
                        'title': title,
                        'image': image,
                        'affiliate_link': affiliate_link,
                        'reviews': reviews,
                        'product_summary': product_summary,
                        'category': category,
                        'amazon_rank': rank,
                        'price': price,
                        'rating': rating,
                        'discovered_date': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️ Error parsing product: {e}")
                    continue
            
            logger.info(f"✅ Scraped {len(products)} products from Amazon Best Sellers")
            return products
            
        except Exception as e:
            logger.error(f"❌ Error scraping Amazon Best Sellers: {e}")
            return []
    
    def check_google_trends(self, keywords):
        """
        Check Google Trends for given keywords
        
        Note: Requires pytrends library (pip install pytrends)
        
        Args:
            keywords: List of keywords to check
        
        Returns:
            Dictionary with keyword scores
        """
        logger.info(f"📈 Checking Google Trends for {len(keywords)} keywords")
        
        try:
            from pytrends.request import TrendReq
            
            pytrends = TrendReq(hl='en-US', tz=360)
            
            # Build payload
            pytrends.build_payload(keywords, timeframe='today 30-d')
            
            # Get interest over time
            interest_over_time = pytrends.interest_over_time()
            
            # Calculate average interest
            scores = {}
            for keyword in keywords:
                if keyword in interest_over_time.columns:
                    avg_score = interest_over_time[keyword].mean()
                    scores[keyword] = int(avg_score)
                else:
                    scores[keyword] = 0
            
            logger.info(f"✅ Google Trends scores: {scores}")
            return scores
            
        except ImportError:
            logger.warning("⚠️ pytrends not installed. Install with: pip install pytrends")
            return {keyword: 0 for keyword in keywords}
        except Exception as e:
            logger.error(f"❌ Error checking Google Trends: {e}")
            return {keyword: 0 for keyword in keywords}
    
    def score_product(self, product):
        """
        Score product by demand, competition, and potential
        
        Scoring criteria:
        - Amazon Best Sellers rank (0-30 points)
        - Price range (0-20 points)
        - Rating (0-20 points)
        - Google Trends (0-15 points)
        - Reddit mentions (0-15 points)
        
        Total: 0-100 points
        """
        score = 0
        
        # 1. Amazon Best Sellers rank (30 points)
        if product.get('amazon_rank'):
            rank = product['amazon_rank']
            if rank <= 10:
                score += 30
            elif rank <= 50:
                score += 25
            elif rank <= 100:
                score += 20
            elif rank <= 500:
                score += 10
            else:
                score += 5
        
        # 2. Price range (20 points)
        # Sweet spot: $50-$500 (good commission, affordable)
        if product.get('price'):
            price = product['price']
            if 50 <= price <= 500:
                score += 20
            elif 20 <= price < 50 or 500 < price <= 1000:
                score += 15
            elif price < 20:
                score += 5
            else:
                score += 10
        
        # 3. Rating (20 points)
        if product.get('rating'):
            rating = product['rating']
            if rating >= 4.5:
                score += 20
            elif rating >= 4.0:
                score += 15
            elif rating >= 3.5:
                score += 10
            else:
                score += 5
        
        # 4. Google Trends (15 points)
        if product.get('google_trend_score', 0) > 50:
            score += 15
        elif product.get('google_trend_score', 0) > 20:
            score += 10
        elif product.get('google_trend_score', 0) > 0:
            score += 5
        
        # 5. Reddit mentions (15 points)
        if product.get('reddit_mentions', 0) > 100:
            score += 15
        elif product.get('reddit_mentions', 0) > 50:
            score += 10
        elif product.get('reddit_mentions', 0) > 10:
            score += 5
        
        return score
    
    def save_to_database(self, products):
        """Save trending products to Turso database"""
        saved = 0
        updated = 0
        
        for product in products:
            asin = product.get('asin')
            
            if not asin:
                continue
            
            # Calculate score
            score = self.score_product(product)
            product['total_score'] = score
            
            try:
                # Insert or update via Turso
                result = self.db.insert_or_update_product(product)
                if result:
                    # Check if it was an insert or update by querying
                    # For now, we'll count as saved
                    saved += 1
                
            except Exception as e:
                logger.error(f"❌ Error saving {asin}: {e}")
                continue
        
        logger.info(f"💾 Saved {saved} products to Turso database")
        return saved, updated
    
    def get_top_products(self, limit=20, min_score=50):
        """Get top scoring products from Turso database"""
        return self.db.get_top_products(limit=limit, min_score=min_score)
    
    def export_for_scraper(self, output_file='trending_asins.txt'):
        """Export top ASINs for scraper to use"""
        top_products = self.get_top_products(limit=50, min_score=40)
        
        asins = [p['asin'] for p in top_products]
        
        with open(output_file, 'w') as f:
            for asin in asins:
                f.write(f"{asin}\n")
        
        logger.info(f"✅ Exported {len(asins)} ASINs to {output_file}")
        return asins


def main():
    """Run daily trend scraping"""
    logger.info("🚀 Starting Trending Product Discovery Pipeline (Turso)")
    
    # Initialize scraper with Turso
    scraper = TrendingProductScraper()
    
    # Scrape Amazon Best Sellers
    categories = ['electronics', 'computers', 'sbc']
    all_products = []
    
    for category in categories:
        products = scraper.scrape_amazon_bestsellers(category, max_products=30)
        all_products.extend(products)
        time.sleep(2)  # Rate limiting
    
    # Check Google Trends (optional)
    keywords = ['Raspberry Pi', 'NVIDIA Jetson', 'Arduino', 'Orange Pi']
    trend_scores = scraper.check_google_trends(keywords)
    
    # Add trend scores to products
    for product in all_products:
        for keyword, score in trend_scores.items():
            if keyword.lower() in product.get('title', '').lower():
                product['google_trend_score'] = score
                break
    
    # Save to Turso database
    saved, updated = scraper.save_to_database(all_products)
    
    # Get top products from Turso
    top_products = scraper.get_top_products(limit=20, min_score=50)
    
    logger.info(f"\n🎯 TOP 20 TRENDING PRODUCTS:")
    for i, product in enumerate(top_products, 1):
        logger.info(f"{i}. [{product['total_score']:.0f}/100] {product['title']} (${product.get('price', 'N/A')})")
    
    # Export for scraper
    scraper.export_for_scraper()
    
    logger.info("\n✅ Trending product discovery complete!")
    logger.info("📄 Next: Use trending_asins.txt with your scraper")
    
    # Print Turso stats
    stats = scraper.db.get_stats()
    logger.info(f"\n📊 Turso Database Stats: {stats}")


if __name__ == '__main__':
    main()
