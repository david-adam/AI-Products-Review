#!/usr/bin/env python3
"""
Trending Product Discovery Pipeline
Scrapes Amazon Best Sellers, Google Trends, Reddit, and more to find trending products
"""

import requests
from bs4 import BeautifulSoup
import json
import sqlite3
from datetime import datetime, timedelta
import time
import logging
import re

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TrendingProductScraper:
    """Discover trending products from multiple sources"""
    
    def __init__(self, db_path='trending_products.db'):
        self.db_path = db_path
        self.init_database()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def init_database(self):
        """Initialize SQLite database for trending products"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Products table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trending_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT UNIQUE NOT NULL,
                title TEXT,
                category TEXT,
                amazon_rank INTEGER,
                price REAL,
                rating REAL,
                google_trend_score INTEGER,
                reddit_mentions INTEGER,
                youtube_views INTEGER,
                tiktok_views INTEGER,
                total_score REAL,
                discovered_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Trend history table (for tracking changes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trend_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT NOT NULL,
                rank INTEGER,
                score REAL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asin) REFERENCES trending_products(asin)
            )
        ''')
        
        # Price history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asin TEXT NOT NULL,
                price REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asin) REFERENCES trending_products(asin)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized")
    
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
            
            # Find product cards
            product_cards = soup.find_all('div', {'data-asin': True})
            
            for card in product_cards[:max_products]:
                try:
                    asin = card.get('data-asin')
                    
                    if not asin or len(asin) != 10:
                        continue
                    
                    # Extract title - try multiple selectors (Amazon HTML structure changed)
                    title = None
                    for selector in [
                        '.p13n-sc-truncated', 'h2 a.a-text-normal', 'h2 a span', 
                        '.a-text-normal', '.a-size-medium a', '#title'
                    ]:
                        title_elem = card.select_one(selector)
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            if title and len(title) > 5 and 'Check each product' not in title and 'Visit the' not in title:
                                break
                    
                    # Fallback: try to find title in different ways
                    if not title or title == 'N/A':
                        title_elem = card.find('h2')
                        if title_elem:
                            span = title_elem.find('span')
                            if span:
                                title = span.get_text(strip=True)
                    
                    title = title if title else f"Amazon Product {asin}"
                    
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
                    reviews_elem = card.find('span', class_='a-size-small')
                    if reviews_elem:
                        reviews_text = reviews_elem.get_text(strip=True)
                        # Handle formats like "1,234 reviews" or "1234"
                        reviews_text = reviews_text.replace(',', '').replace('reviews', '').replace('review', '').strip()
                        try:
                            reviews = int(''.join(filter(str.isdigit, reviews_text)))
                        except:
                            reviews = 0
                    
                    # Fallback: try other review selectors
                    if reviews == 0:
                        review_link = card.find('a', class_='a-link-typography')
                        if review_link:
                            review_text = review_link.get_text(strip=True)
                            match = re.search(r'([\d,]+)\s*reviews?', review_text, re.IGNORECASE)
                            if match:
                                reviews = int(match.group(1).replace(',', ''))
                    
                    # Extract rank
                    rank_elem = card.find('span', class_='zg-badge-text')
                    rank = None
                    if rank_elem:
                        rank_text = rank_elem.text.strip()
                        # Extract number (e.g., "#1" -> 1)
                        rank = int(''.join(filter(str.isdigit, rank_text)))
                    
                    # Extract price
                    price_elem = card.find('span', class_='p13n-sc-price')
                    price = None
                    if price_elem:
                        price_text = price_elem.text.strip().replace('$', '').replace(',', '')
                        try:
                            price = float(price_text)
                        except ValueError:
                            price = None
                    
                    # Extract rating
                    rating_elem = card.find('span', class_='a-icon-alt')
                    rating = None
                    if rating_elem:
                        rating_text = rating_elem.text.strip()
                        # Extract "4.5 out of 5" -> 4.5
                        try:
                            rating = float(rating_text.split()[0])
                        except (ValueError, IndexError):
                            rating = None
                    
                    # Generate affiliate link
                    affiliate_link = f"https://www.amazon.com/dp/{asin}?tag=dav7aug-20"
                    
                    # Generate product summary (basic - could be enhanced with AI)
                    product_summary = f"Trending {category} product ranked #{rank} on Amazon with ${price} price and {rating} rating."
                    
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
        """Save trending products to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
                # Check if product exists
                cursor.execute('SELECT id FROM trending_products WHERE asin = ?', (asin,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update
                    cursor.execute('''
                        UPDATE trending_products 
                        SET title = ?, category = ?, amazon_rank = ?, 
                            price = ?, rating = ?, total_score = ?,
                            image = ?, affiliate_link = ?, reviews = ?, product_summary = ?,
                            last_updated = CURRENT_TIMESTAMP
                        WHERE asin = ?
                    ''', (
                        product.get('title'),
                        product.get('category'),
                        product.get('amazon_rank'),
                        product.get('price'),
                        product.get('rating'),
                        score,
                        product.get('image'),
                        product.get('affiliate_link'),
                        product.get('reviews'),
                        product.get('product_summary'),
                        asin
                    ))
                    updated += 1
                else:
                    # Insert
                    cursor.execute('''
                        INSERT INTO trending_products 
                        (asin, title, category, amazon_rank, price, rating, total_score,
                         image, affiliate_link, reviews, product_summary)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        asin,
                        product.get('title'),
                        product.get('category'),
                        product.get('amazon_rank'),
                        product.get('price'),
                        product.get('rating'),
                        score,
                        product.get('image'),
                        product.get('affiliate_link'),
                        product.get('reviews'),
                        product.get('product_summary')
                    ))
                    saved += 1
                
                # Save to history
                cursor.execute('''
                    INSERT INTO trend_history (asin, rank, score)
                    VALUES (?, ?, ?)
                ''', (asin, product.get('amazon_rank'), score))
                
            except sqlite3.IntegrityError:
                logger.warning(f"⚠️ Duplicate ASIN: {asin}")
                continue
            except Exception as e:
                logger.error(f"❌ Error saving {asin}: {e}")
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"💾 Saved {saved} new, updated {updated} products to database")
        return saved, updated
    
    def get_top_products(self, limit=20, min_score=50):
        """Get top scoring products from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT asin, title, category, amazon_rank, price, rating, total_score,
                   image, affiliate_link, reviews, product_summary
            FROM trending_products
            WHERE total_score >= ?
            ORDER BY total_score DESC
            LIMIT ?
        ''', (min_score, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        products = []
        for row in rows:
            products.append({
                'asin': row[0],
                'title': row[1],
                'category': row[2],
                'amazon_rank': row[3],
                'price': row[4],
                'rating': row[5],
                'total_score': row[6],
                'image': row[7],
                'affiliate_link': row[8],
                'reviews': row[9],
                'product_summary': row[10]
            })
        
        return products
    
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
    logger.info("🚀 Starting Trending Product Discovery Pipeline")
    
    # Initialize scraper
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
    
    # Save to database
    saved, updated = scraper.save_to_database(all_products)
    
    # Get top products
    top_products = scraper.get_top_products(limit=20, min_score=50)
    
    logger.info(f"\n🎯 TOP 20 TRENDING PRODUCTS:")
    for i, product in enumerate(top_products, 1):
        logger.info(f"{i}. [{product['total_score']:.0f}/100] {product['title']} (${product.get('price', 'N/A')})")
    
    # Export for scraper
    scraper.export_for_scraper()
    
    logger.info("\n✅ Trending product discovery complete!")
    logger.info("📄 Next: Use trending_asins.txt with your scraper")


if __name__ == '__main__':
    main()
