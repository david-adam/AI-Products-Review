"""
Tests for ScraperAPI Amazon Product Scraper
Following TDD methodology - tests written first
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests


class TestAmazonProductParser:
    """Tests for HTML parsing functionality"""

    def test_parse_title_from_product_page(self):
        """Test parsing product title from Amazon product page HTML"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <span id="productTitle" class="a-size-extra-large">Test Product Name</span>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html)
        assert parser.get_title() == "Test Product Name"

    def test_parse_title_alternative_selector(self):
        """Test parsing title with alternative h1#title selector"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <h1 id="title" class="a-size-extra-large">Alternative Title</h1>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html)
        assert parser.get_title() == "Alternative Title"

    def test_parse_price_offscreen(self):
        """Test parsing price from .a-offscreen element"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <span class="a-price" data-a-size="xl" data-a-color="base">
                    <span class="a-offscreen">$99.99</span>
                </span>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html)
        assert parser.get_price() == 99.99

    def test_parse_price_ourprice(self):
        """Test parsing price from #priceblock_ourprice element"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <span id="priceblock_ourprice" class="a-size-medium a-color-price">$149.99</span>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html)
        assert parser.get_price() == 149.99

    def test_parse_rating(self):
        """Test parsing product rating"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <i class="a-icon a-icon-star a-star-4-5">
                    <span class="a-icon-alt">4.5 out of 5 stars</span>
                </i>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html)
        assert parser.get_rating() == 4.5

    def test_parse_rating_from_text(self):
        """Test parsing rating from title attribute"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <i class="a-icon a-icon-star a-star-4" title="4.0 out of 5 stars"></i>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html)
        assert parser.get_rating() == 4.0

    def test_parse_asin_from_url(self):
        """Test extracting ASIN from product URL"""
        from scraper_api import AmazonProductParser
        
        html = '<html><body></body></html>'
        parser = AmazonProductParser(html, product_url="https://www.amazon.com/dp/B08N5WRWNW")
        assert parser.get_asin() == "B08N5WRWNW"

    def test_parse_sales_rank(self):
        """Test parsing sales rank from page"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <span id="SalesRank">
                    <span class="a-size-medium">#1,234 in Computers & Accessories</span>
                </span>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html)
        assert parser.get_sales_rank() == 1234

    def test_parse_returns_dict_with_all_fields(self):
        """Test that parse returns complete data structure matching Keepa format"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <span id="productTitle" class="a-size-extra-large">Test Product</span>
                <span class="a-price" data-a-size="xl" data-a-color="base">
                    <span class="a-offscreen">$99.99</span>
                </span>
                <i class="a-icon a-icon-star a-star-4-5">
                    <span class="a-icon-alt">4.5 out of 5 stars</span>
                </i>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html, product_url="https://www.amazon.com/dp/B08N5WRWNW")
        data = parser.parse()
        
        assert isinstance(data, dict)
        assert data['asin'] == 'B08N5WRWNW'
        assert data['title'] == 'Test Product'
        assert data['price'] == 99.99
        assert data['rating'] == 4.5
        assert 'affiliate_link' in data


class TestScraperAPIClient:
    """Tests for ScraperAPI HTTP client"""

    @patch('scraper_api.scraper_api.requests.get')
    def test_make_request_to_scraperapi(self, mock_get):
        """Test making request through ScraperAPI proxy"""
        from scraper_api import ScraperAPIClient
        
        mock_response = Mock()
        mock_response.text = '<html><body>Success</body></html>'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = ScraperAPIClient(api_key="test_api_key")
        result = client._make_request("https://www.amazon.com/dp/B08N5WRWNW")
        
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "scraperapi.com" in call_args[0][0]
        assert call_args[1]['params']['api_key'] == "test_api_key"

    @patch('scraper_api.scraper_api.requests.get')
    def test_request_includes_target_url(self, mock_get):
        """Test that target URL is passed correctly"""
        from scraper_api import ScraperAPIClient
        
        mock_response = Mock()
        mock_response.text = '<html><body>Test</body></html>'
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = ScraperAPIClient(api_key="test_key")
        client._make_request("https://www.amazon.com/product-page")
        
        call_args = mock_get.call_args
        assert call_args[1]['params']['url'] == "https://www.amazon.com/product-page"

    @patch('scraper_api.scraper_api.requests.get')
    def test_fetch_product_returns_html(self, mock_get):
        """Test fetching product page returns raw HTML"""
        from scraper_api import ScraperAPIClient
        
        sample_html = '<html><body>Product Page</body></html>'
        mock_response = Mock()
        mock_response.text = sample_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        client = ScraperAPIClient(api_key="test_key")
        result = client.fetch_product("https://www.amazon.com/dp/B08N5WRWNW")
        
        assert result == sample_html


class TestScraperAPIErrorHandling:
    """Tests for error handling"""

    @patch('scraper_api.scraper_api.requests.get')
    def test_handles_network_error(self, mock_get):
        """Test handling network connection errors"""
        from scraper_api import ScraperAPIClient, ScraperAPIError
        import requests
        
        mock_get.side_effect = requests.exceptions.ConnectionError("Network error")
        
        client = ScraperAPIClient(api_key="test_key")
        
        with pytest.raises(ScraperAPIError):
            client.fetch_product("https://www.amazon.com/dp/B08N5WRWNW")

    @patch('scraper_api.scraper_api.requests.get')
    def test_handles_http_error(self, mock_get):
        """Test handling HTTP error responses"""
        from scraper_api import ScraperAPIClient, ScraperAPIError
        import requests
        
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = 'Forbidden'
        # Make raise_for_status raise HTTPError
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("403 Client Error")
        mock_get.return_value = mock_response
        
        client = ScraperAPIClient(api_key="test_key")
        
        with pytest.raises(ScraperAPIError):
            client.fetch_product("https://www.amazon.com/dp/B08N5WRWNW")

    def test_handles_invalid_html(self):
        """Test handling of invalid/malformed HTML"""
        from scraper_api import AmazonProductParser
        
        invalid_html = "<not valid html"
        parser = AmazonProductParser(invalid_html)
        
        # Should not raise, should return None or default values
        result = parser.parse()
        assert result is not None or parser.get_title() is None

    def test_handles_missing_elements(self):
        """Test parsing when expected elements are missing"""
        from scraper_api import AmazonProductParser
        
        minimal_html = "<html><body></body></html>"
        parser = AmazonProductParser(minimal_html)
        
        # Should not raise, should return None for missing fields
        assert parser.get_title() is None
        assert parser.get_price() is None
        assert parser.get_rating() is None


class TestDataStructureCompatibility:
    """Tests ensuring compatibility with Keepa API data structure"""

    def test_output_matches_keepa_format(self):
        """Test that output structure matches Keepa API format"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <span id="productTitle" class="a-size-extra-large">Test Product</span>
                <span class="a-price" data-a-size="xl" data-a-color="base">
                    <span class="a-offscreen">$99.99</span>
                </span>
                <i class="a-icon a-icon-star a-star-4-5">
                    <span class="a-icon-alt">4.5 out of 5 stars</span>
                </i>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html, product_url="https://www.amazon.com/dp/B08N5WRWNW")
        data = parser.parse()
        
        # Keepa format fields
        expected_fields = ['asin', 'title', 'price', 'rating', 'sales_rank', 'affiliate_link']
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_affiliate_link_contains_asin(self):
        """Test affiliate link generation includes ASIN"""
        from scraper_api import AmazonProductParser
        
        html = '<html><body></body></html>'
        parser = AmazonProductParser(
            html, 
            product_url="https://www.amazon.com/dp/B08N5WRWNW",
            affiliate_tag="test-tag-20"
        )
        data = parser.parse()
        
        assert 'affiliate_link' in data
        assert 'B08N5WRWNW' in data['affiliate_link']
        assert 'test-tag-20' in data['affiliate_link']

    def test_price_is_numeric(self):
        """Test price is returned as numeric type"""
        from scraper_api import AmazonProductParser
        
        html = '''
        <html>
            <body>
                <span class="a-price" data-a-size="xl" data-a-color="base">
                    <span class="a-offscreen">$99.99</span>
                </span>
            </body>
        </html>
        '''
        parser = AmazonProductParser(html)
        data = parser.parse()
        
        assert isinstance(data['price'], float)
        assert data['price'] == 99.99


class TestScraperAPIIntegration:
    """Integration tests with mocked ScraperAPI responses"""

    @patch('scraper_api.scraper_api.requests.get')
    def test_full_scrape_workflow(self, mock_get):
        """Test complete scraping workflow from URL to parsed data"""
        from scraper_api import AmazonScraper
        
        product_html = '''
        <html>
            <body>
                <span id="productTitle" class="a-size-extra-large">Complete Test Product</span>
                <span class="a-price" data-a-size="xl" data-a-color="base">
                    <span class="a-offscreen">$199.99</span>
                </span>
                <i class="a-icon a-icon-star a-star-4">
                    <span class="a-icon-alt">4.0 out of 5 stars</span>
                </i>
            </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.text = product_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        scraper = AmazonScraper(api_key="test_key", affiliate_tag="test-tag")
        result = scraper.scrape("https://www.amazon.com/dp/B08N5WRWNW")
        
        assert result['asin'] == 'B08N5WRWNW'
        assert result['title'] == 'Complete Test Product'
        assert result['price'] == 199.99
        assert result['rating'] == 4.0
        assert 'affiliate_link' in result

    @patch('scraper_api.scraper_api.requests.get')
    def test_scrape_multiple_products(self, mock_get):
        """Test scraping multiple products in sequence"""
        from scraper_api import AmazonScraper
        
        product_html = '''
        <html>
            <body>
                <span id="productTitle" class="a-size-extra-large">Multi Product</span>
                <span class="a-price" data-a-size="xl" data-a-color="base">
                    <span class="a-offscreen">$50.00</span>
                </span>
            </body>
        </html>
        '''
        
        mock_response = Mock()
        mock_response.text = product_html
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        scraper = AmazonScraper(api_key="test_key")
        
        asins = ["B08N5WRWNW", "B07YZK4MYM", "B09V3KXJPB"]
        results = []
        
        for asin in asins:
            url = f"https://www.amazon.com/dp/{asin}"
            result = scraper.scrape(url)
            results.append(result)
        
        assert len(results) == 3
        for i, asin in enumerate(asins):
            assert results[i]['asin'] == asin
