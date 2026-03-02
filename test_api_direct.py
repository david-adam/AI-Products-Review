"""
Test ScraperAPI with correct endpoint
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_scraperapi():
    """Test ScraperAPI directly"""

    api_key = os.getenv('SCRAPERAPI_API_KEY')
    affiliate_tag = os.getenv('AMAZON_AFFILIATE_TAG', 'dav7aug-20')

    print(f"🔑 API Key: {api_key}")
    print(f"🏷️  Affiliate Tag: {affiliate_tag}")
    print()

    # Test with a simple URL first
    test_url = "https://httpbin.org/ip"

    print("🧪 Test 1: Simple HTTP request through ScraperAPI")
    print(f"   Target URL: {test_url}")
    print()

    # Method 1: GET parameter approach
    params = {
        'api_key': api_key,
        'url': test_url
    }

    try:
        response = requests.get('http://api.scraperapi.com', params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            print(f"   ✅ Success! Response:")
            print(f"   {response.text[:200]}")
        else:
            print(f"   ❌ Error Response:")
            print(f"   {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

    print()
    print("🧪 Test 2: Amazon product page")
    amazon_url = "https://www.amazon.com/dp/B08N5WRWNW"
    print(f"   Target URL: {amazon_url}")
    print()

    params = {
        'api_key': api_key,
        'url': amazon_url,
        'country_code': 'us'
    }

    try:
        response = requests.get('http://api.scraperapi.com', params=params, timeout=60)
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            print(f"   ✅ Success! Got {len(response.text)} bytes")
            print(f"   First 200 chars:")
            print(f"   {response.text[:200]}")
        else:
            print(f"   ❌ Error Response:")
            print(f"   {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Exception: {e}")

if __name__ == '__main__':
    test_scraperapi()
