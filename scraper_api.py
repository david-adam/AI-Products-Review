"""
ScraperAPI Amazon Product Scraper

Uses ScraperAPI to scrape Amazon product data via search results,
since individual product pages may be blocked by Amazon.
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, parse_qs


class ScraperAPIError(Exception):
    """Exception raised for ScraperAPI errors"""
    pass


class ScraperAPIClient:
    """HTTP client for making requests through ScraperAPI"""
    
    BASE_URL = "https://api.scraperapi.com"
    
    def __init__(self, api_key: str, render_js: bool = False):
        """
        Initialize ScraperAPI client
        
        Args:
            api_key: ScraperAPI API key
            render_js: Whether to enable JavaScript rendering
        """
        self.api_key = api_key
        self.render_js = render_js
    
    def _make_request(self, target_url: str) -> str:
        """
        Make HTTP request through ScraperAPI
        
        Args:
            target_url: The URL to fetch
            
        Returns:
            Raw HTML response as string
            
        Raises:
            ScraperAPIError: On network or API errors
        """
        params = {
            'api_key': self.api_key,
            'url': target_url,
            'country_code': 'us',
            'timeout': 30
        }
        
        if self.render_js:
            params['render'] = 'true'
        
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=90
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            raise ScraperAPIError(f"HTTP error from ScraperAPI: {e}")
        except requests.exceptions.ConnectionError as e:
            raise ScraperAPIError(f"Network error connecting to ScraperAPI: {e}")
        except requests.exceptions.Timeout as e:
            raise ScraperAPIError(f"Request timeout: {e}")
        except Exception as e:
            raise ScraperAPIError(f"Unexpected error: {e}")
    
    def fetch_page(self, target_url: str) -> str:
        """Fetch any page HTML through ScraperAPI"""
        return self._make_request(target_url)


class AmazonSearchResultParser:
    """Parser for Amazon search result HTML"""
    
    def __init__(self, html: str, affiliate_tag: str = None):
        """
        Initialize parser with search result HTML
        
        Args:
            html: Raw HTML content from search results
            affiliate_tag: Affiliate tag for affiliate link generation
        """
        self.html = html
        self.affiliate_tag = affiliate_tag
        self.soup = BeautifulSoup(html, 'lxml')
    
    def parse_products(self) -> List[Dict[str, Any]]:
        """Parse search results and extract product data"""
        products = []
        
        for item in self.soup.select('.s-result-item'):
            asin = item.get('data-asin')
            if not asin or asin == '1':
                continue
            
            # Get title
            title = self._extract_title(item)
            if not title or 'Check each product' in title:
                continue
            
            # Get price
            price = self._extract_price(item)
            
            # Get rating
            rating = self._extract_rating(item)
            
            # Get reviews count
            reviews = self._extract_reviews(item)
            
            # Get image URL
            image = self._extract_image(item)
            
            product = {
                'asin': asin,
                'title': title,
                'price': price,
                'rating': rating,
                'reviews': reviews,
                'image': image,
                'affiliate_link': self._generate_affiliate_link(asin)
            }
            
            products.append(product)
        
        return products
    
    def _extract_title(self, item) -> Optional[str]:
        """Extract product title from search result item"""
        for selector in ['h2 a span', '.a-text-normal', '.a-size-medium a']:
            title_elem = item.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 5:
                    return title
        return None
    
    def _extract_price(self, item) -> Optional[float]:
        """Extract price from search result item"""
        for price_sel in ['.a-price .a-offscreen', '.a-price-whole', '.apexPriceToPay .a-offscreen', '.a-price-actual-price .a-offscreen']:
            price_elem = item.select_one(price_sel)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    try:
                        return float(price_match.group())
                    except ValueError:
                        pass
        return None
    
    def _extract_rating(self, item) -> Optional[float]:
        """Extract rating from search result item"""
        for rating_sel in ['span.a-icon-alt', 'i.a-icon-star-small', '.a-star-medium']:
            rating_elem = item.select_one(rating_sel)
            if rating_elem:
                text = rating_elem.get_text(strip=True)
                match = re.search(r'([\d.]+)\s*out', text)
                if match:
                    try:
                        return float(match.group(1))
                    except ValueError:
                        pass
        return None
    
    def _extract_reviews(self, item) -> Optional[int]:
        """Extract reviews count from search result item"""
        for reviews_sel in ['span.a-size-base', '.a-size-mini', '.a-link-normal span']:
            reviews_elem = item.select_one(reviews_sel)
            if reviews_elem:
                text = reviews_elem.get_text(strip=True)
                match = re.search(r'\(([\d,]+)\)|([\d,]+)\s*review', text)
                if match:
                    count = match.group(1) or match.group(2)
                    try:
                        return int(count.replace(',', ''))
                    except ValueError:
                        pass
        return None
    
    def _extract_image(self, item) -> Optional[str]:
        """Extract product image URL"""
        img = item.select_one('img.s-image')
        if img:
            return img.get('src')
        return None
    
    def _generate_affiliate_link(self, asin: str) -> str:
        """Generate affiliate link"""
        if self.affiliate_tag:
            return f"https://www.amazon.com/dp/{asin}?tag={self.affiliate_tag}"
        return f"https://www.amazon.com/dp/{asin}"


class AmazonScraper:
    """
    Main scraper class - scrapes Amazon products via search results
    
    Note: Direct product page scraping may be blocked by Amazon.
    This class uses search results as the primary data source.
    """
    
    DEFAULT_AFFILIATE_TAG = "your-tag-20"
    
    def __init__(self, api_key: str, affiliate_tag: str = None, render_js: bool = False):
        """
        Initialize Amazon scraper
        
        Args:
            api_key: ScraperAPI API key
            affiliate_tag: Amazon affiliate tag (optional)
            render_js: Enable JavaScript rendering
        """
        self.client = ScraperAPIClient(api_key, render_js=render_js)
        self.affiliate_tag = affiliate_tag or self.DEFAULT_AFFILIATE_TAG
    
    def search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon and return product data
        
        Args:
            query: Search query (e.g., "raspberry pi 4")
            max_results: Maximum number of results to return
            
        Returns:
            List of product dictionaries
        """
        search_query = query.replace(' ', '+')
        search_url = f"https://www.amazon.com/s?k={search_query}"
        
        try:
            html = self.client.fetch_page(search_url)
            parser = AmazonSearchResultParser(html, affiliate_tag=self.affiliate_tag)
            products = parser.parse_products()
            return products[:max_results]
        except ScraperAPIError:
            raise
        except Exception as e:
            raise ScraperAPIError(f"Search failed: {e}")
    
    def scrape(self, product_url: str) -> Dict[str, Any]:
        """Scrape Amazon product data from URL"""
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', product_url)
        if asin_match:
            asin = asin_match.group(1)
            results = self.search(asin, max_results=1)
            if results:
                return results[0]
        
        raise ScraperAPIError("Could not scrape product. Use search() method instead.")
    
    def get_product(self, asin: str) -> Dict[str, Any]:
        """Get product by ASIN"""
        results = self.search(asin, max_results=1)
        if results:
            return results[0]
        
        return {
            'asin': asin,
            'title': None,
            'price': None,
            'rating': None,
            'reviews': None,
            'image': None,
            'affiliate_link': f"https://www.amazon.com/dp/{asin}?tag={self.affiliate_tag}" if self.affiliate_tag else f"https://www.amazon.com/dp/{asin}"
        }


# Backwards compatibility
AmazonProductParser = AmazonSearchResultParser


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    api_key = os.environ.get("SCRAPERAPI_API_KEY")
    
    if not api_key:
        print("Please set SCRAPERAPI_API_KEY environment variable")
        exit(1)
    
    scraper = AmazonScraper(
        api_key=api_key,
        affiliate_tag=os.environ.get("AMAZON_AFFILIATE_TAG", "your-tag-20")
    )
    
    try:
        products = scraper.search("raspberry pi 4", max_results=3)
        for p in products:
            print(f"{p['title'][:50]}... - ${p['price']} - {p['affiliate_link']}")
    except ScraperAPIError as e:
        print(f"Error: {e}")
