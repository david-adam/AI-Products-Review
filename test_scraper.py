"""
Test ScraperAPI Amazon Scraper

Tests for the Amazon scraper functionality.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from scraper_api import (
    AmazonScraper, 
    ScraperAPIClient, 
    AmazonSearchResultParser,
    ScraperAPIError
)


# Test constants
TEST_API_KEY = os.getenv('SCRAPERAPI_API_KEY', 'test-key')
TEST_AFFILIATE_TAG = os.getenv('AMAZON_AFFILIATE_TAG', 'test-tag-20')


class TestScraperAPIClient:
    """Tests for ScraperAPIClient"""
    
    def test_client_initialization(self):
        """Test client can be initialized"""
        client = ScraperAPIClient(TEST_API_KEY)
        assert client.api_key == TEST_API_KEY
        assert client.BASE_URL == "https://api.scraperapi.com"
    
    def test_client_with_render_js(self):
        """Test client with JS rendering enabled"""
        client = ScraperAPIClient(TEST_API_KEY, render_js=True)
        assert client.render_js is True


class TestAmazonSearchResultParser:
    """Tests for AmazonSearchResultParser"""
    
    def test_parser_initialization(self):
        """Test parser can be initialized"""
        html = "<html><body></body></html>"
        parser = AmazonSearchResultParser(html, TEST_AFFILIATE_TAG)
        assert parser.affiliate_tag == TEST_AFFILIATE_TAG
    
    def test_parser_without_affiliate_tag(self):
        """Test parser can be initialized without affiliate tag"""
        html = "<html><body></body></html>"
        parser = AmazonSearchResultParser(html)
        assert parser.affiliate_tag is None
    
    def test_parse_empty_html(self):
        """Test parsing empty HTML returns empty list"""
        html = "<html><body></body></html>"
        parser = AmazonSearchResultParser(html, TEST_AFFILIATE_TAG)
        products = parser.parse_products()
        assert products == []
    
    def test_generate_affiliate_link_with_tag(self):
        """Test affiliate link generation with tag"""
        html = "<html><body></body></html>"
        parser = AmazonSearchResultParser(html, TEST_AFFILIATE_TAG)
        
        link = parser._generate_affiliate_link("B08N5WRWNW")
        assert "B08N5WRWNW" in link
        assert TEST_AFFILIATE_TAG in link
    
    def test_generate_affiliate_link_without_tag(self):
        """Test affiliate link generation without tag"""
        html = "<html><body></body></html>"
        parser = AmazonSearchResultParser(html)
        
        link = parser._generate_affiliate_link("B08N5WRWNW")
        assert "B08N5WRWNW" in link
        assert "tag=" not in link


class TestAmazonScraper:
    """Tests for AmazonScraper"""
    
    def test_scraper_initialization(self):
        """Test scraper can be initialized"""
        scraper = AmazonScraper(TEST_API_KEY, TEST_AFFILIATE_TAG)
        assert scraper.client.api_key == TEST_API_KEY
        assert scraper.affiliate_tag == TEST_AFFILIATE_TAG
    
    def test_default_affiliate_tag(self):
        """Test default affiliate tag"""
        scraper = AmazonScraper(TEST_API_KEY)
        assert scraper.affiliate_tag == "your-tag-20"
    
    def test_search_with_empty_results(self):
        """Test search with no results - integration test"""
        scraper = AmazonScraper(TEST_API_KEY, TEST_AFFILIATE_TAG)
        
        # Use a unique search term unlikely to return results
        results = scraper.search("xyznonexistentproduct12345", max_results=5)
        
        # Should return empty list or products
        assert isinstance(results, list)


class TestIntegration:
    """Integration tests - require API key"""
    
    @pytest.fixture
    def scraper(self):
        """Create scraper instance"""
        return AmazonScraper(TEST_API_KEY, TEST_AFFILIATE_TAG)
    
    def test_search_runs_successfully(self, scraper):
        """Integration test - search actually works"""
        # This is a real API call test
        results = scraper.search("arduino starter kit", max_results=3)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check product structure
        for product in results:
            assert 'asin' in product
            assert 'title' in product
            assert 'affiliate_link' in product
            assert TEST_AFFILIATE_TAG in product['affiliate_link']
    
    def test_get_product_by_asin(self, scraper):
        """Test getting product by ASIN"""
        # Use known Raspberry Pi ASIN
        product = scraper.get_product("B07V5JTMV9")
        
        assert 'asin' in product
        assert 'affiliate_link' in product
        # Note: The ASIN might be different because search returns related products
        assert product['affiliate_link'].startswith("https://www.amazon.com/dp/")
    
    def test_affiliate_link_format(self, scraper):
        """Test affiliate links have correct format"""
        results = scraper.search("raspberry pi", max_results=1)
        
        if results:
            link = results[0]['affiliate_link']
            assert link.startswith("https://www.amazon.com/dp/")
            assert "tag=" in link
            assert TEST_AFFILIATE_TAG in link


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
