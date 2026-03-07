"""
Scrape.do Client - Alternative to ScraperAPI
Free tier: 1,000 requests/month
Website: https://scrape.do
"""

import requests
from typing import Optional
from urllib.parse import urlencode

class ScrapeDoError(Exception):
    """Exception raised for Scrape.do errors"""
    pass

class ScrapeDoClient:
    """HTTP client for making requests through Scrape.do"""

    BASE_URL = "https://api.scrape.do"

    def __init__(self, api_key: str, render_js: bool = False, country_code: str = "us"):
        """
        Initialize Scrape.do client

        Args:
            api_key: Scrape.do API key
            render_js: Whether to enable JavaScript rendering
            country_code: Country code for proxy location
        """
        self.api_key = api_key
        self.render_js = render_js
        self.country_code = country_code

    def _make_request(self, target_url: str, timeout: int = 30) -> str:
        """
        Make HTTP request through Scrape.do

        Args:
            target_url: The URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Raw HTML response as string

        Raises:
            ScrapeDoError: On network or API errors
        """
        params = {
            'token': self.api_key,
            'url': target_url,
        }

        if self.render_js:
            params['render'] = 'true'

        if self.country_code:
            params['countryCode'] = self.country_code

        try:
            response = requests.get(
                self.BASE_URL + "/",
                params=params,
                timeout=timeout
            )
            response.raise_for_status()

            # Check for API errors in JSON response
            try:
                json_data = response.json()
                if 'error' in json_data:
                    raise ScrapeDoError(f"Scrape.do API error: {json_data['error']}")
            except ValueError:
                # Not a JSON response, treat as HTML
                pass

            return response.text

        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP error from Scrape.do: {e}"
            if response.status_code == 401:
                error_msg = "Invalid API key"
            elif response.status_code == 403:
                error_msg = "Access denied - check API key permissions"
            elif response.status_code == 429:
                error_msg = "Rate limit exceeded"
            raise ScrapeDoError(error_msg)

        except requests.exceptions.ConnectionError as e:
            raise ScrapeDoError(f"Network error connecting to Scrape.do: {e}")

        except requests.exceptions.Timeout as e:
            raise ScrapeDoError(f"Request timeout: {e}")

        except Exception as e:
            raise ScrapeDoError(f"Unexpected error: {e}")

    def fetch_page(self, target_url: str, timeout: int = 30) -> str:
        """
        Fetch any page HTML through Scrape.do

        Args:
            target_url: The URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Raw HTML response as string
        """
        return self._make_request(target_url, timeout)

    def check_remaining_credits(self) -> dict:
        """
        Check remaining API credits

        Returns:
            Dictionary with credit information
        """
        try:
            response = requests.get(
                f"{self.BASE_URL}/account",
                params={'token': self.api_key},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e)}
