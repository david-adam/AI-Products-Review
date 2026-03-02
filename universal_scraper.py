"""
Universal Amazon Scraper - Supports ScraperAPI and Scrape.do
Automatically chooses the best available API
"""

import os
import sys
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper_api import AmazonScraper as ScraperAPIScraper, ScraperAPIError
from scrape_do_client import ScrapeDoClient, ScrapeDoError
from scraper_api import AmazonSearchResultParser

load_dotenv()

class UniversalAmazonScraper:
    """
    Universal Amazon scraper that supports multiple backends:
    - ScraperAPI (paid, ending trial)
    - Scrape.do (free tier: 1,000 requests/month)
    """

    # Configuration
    SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY", "023fb87a622df52312bb7492013142f6")
    SCRAPEDO_KEY = os.getenv("SCRAPEDO_KEY", "6cfa3633393f495992593d5102b680f02419464a0ec")
    AMAZON_AFFILIATE_TAG = os.getenv("AMAZON_AFFILIATE_TAG", "dav7aug-20")

    # Backend priority
    BACKEND_PRIORITY = ["scrapedo", "scraperapi"]  # Prefer Scrape.do (free)

    def __init__(self, backend: str = "auto", render_js: bool = False):
        """
        Initialize universal scraper

        Args:
            backend: Backend to use ("auto", "scraperapi", or "scrapedo")
            render_js: Enable JavaScript rendering
        """
        self.backend = self._select_backend(backend)
        self.render_js = render_js
        self.affiliate_tag = self.AMAZON_AFFILIATE_TAG

        if self.backend == "scrapedo":
            self.client = ScrapeDoClient(
                api_key=self.SCRAPEDO_KEY,
                render_js=render_js
            )
            print("✓ Using Scrape.do backend (1,000 free requests/month)")
        elif self.backend == "scraperapi":
            self.client = ScraperAPIScraper(
                api_key=self.SCRAPERAPI_KEY,
                affiliate_tag=self.affiliate_tag,
                render_js=render_js
            )
            print("✓ Using ScraperAPI backend")
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def _select_backend(self, backend: str) -> str:
        """
        Select appropriate backend

        Args:
            backend: Requested backend or "auto"

        Returns:
            Backend name to use
        """
        if backend != "auto":
            return backend

        # Auto-select: try each backend by priority
        for backend_name in self.BACKEND_PRIORITY:
            if backend_name == "scrapedo" and self.SCRAPEDO_KEY:
                return "scrapedo"
            elif backend_name == "scraperapi" and self.SCRAPERAPI_KEY:
                return "scraperapi"

        # Fallback to first available
        if self.SCRAPEDO_KEY:
            return "scrapedo"
        if self.SCRAPERAPI_KEY:
            return "scraperapi"

        raise Exception("No API keys configured. Set SCRAPEDO_KEY or SCRAPERAPI_KEY")

    def search(self, query: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for products on Amazon

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of product dictionaries
        """
        search_query = query.replace(' ', '+')
        search_url = f"https://www.amazon.com/s?k={search_query}"

        try:
            if self.backend == "scrapedo":
                return self._search_scrapedo(search_url, max_results)
            elif self.backend == "scraperapi":
                return self.client.search(query, max_results)
        except (ScrapeDoError, ScraperAPIError) as e:
            print(f"✗ Search failed: {e}")
            return []

    def _search_scrapedo(self, search_url: str, max_results: int) -> List[Dict[str, Any]]:
        """
        Search using Scrape.do backend

        Args:
            search_url: Amazon search URL
            max_results: Maximum results

        Returns:
            List of products
        """
        try:
            # Fetch HTML
            html = self.client.fetch_page(search_url)

            # Parse with existing parser
            parser = AmazonSearchResultParser(html, affiliate_tag=self.affiliate_tag)
            products = parser.parse_products()

            return products[:max_results]

        except ScrapeDoError:
            raise
        except Exception as e:
            raise ScrapeDoError(f"Search failed: {e}")

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get information about current backend

        Returns:
            Dictionary with backend details
        """
        info = {
            'backend': self.backend,
            'render_js': self.render_js,
            'affiliate_tag': self.affiliate_tag
        }

        if self.backend == "scrapedo":
            info['api'] = "Scrape.do"
            info['free_tier'] = "1,000 requests/month"
            info['pricing'] = "$0.12 per 1,000 requests (paid)"
            # Check credits if available
            credits = self.client.check_remaining_credits()
            if 'error' not in credits:
                info['credits'] = credits
        elif self.backend == "scraperapi":
            info['api'] = "ScraperAPI"
            info['free_tier'] = "5,000 credits on signup"
            info['pricing'] = "~$0.00245 per request"

        return info

# Convenience function for backward compatibility
def AmazonScraper(backend: str = "auto", **kwargs):
    """
    Create Amazon scraper (backward compatible)

    Args:
        backend: Backend to use ("auto", "scraperapi", "scrapedo")
        **kwargs: Additional arguments

    Returns:
        UniversalAmazonScraper instance
    """
    return UniversalAmazonScraper(backend=backend, **kwargs)
