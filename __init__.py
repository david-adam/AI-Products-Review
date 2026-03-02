"""
ScraperAPI Adapter for Amazon Product Scraping

This module provides an interface compatible with Keepa API for scraping
Amazon product data using ScraperAPI as the data source.
"""

from .scraper_api import AmazonScraper, ScraperAPIClient, AmazonSearchResultParser, ScraperAPIError

__all__ = ['AmazonScraper', 'ScraperAPIClient', 'AmazonSearchResultParser', 'ScraperAPIError']
