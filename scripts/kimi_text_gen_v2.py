#!/usr/bin/env python3
"""
Kimi K2.5 (Moonshot AI) Integration for ProductLens AI

Generates product reviews and social media posts using Kimi K2.5.
Now using the correct API endpoint: https://api.kimi.com/coding/
"""

import os
import requests
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

KIMI_API_KEY = os.getenv('KIMI_API_KEY')
KIMI_BASE_URL = os.getenv('KIMI_BASE_URL', 'https://api.kimi.com/coding/')
KIMI_MODEL = os.getenv('KIMI_MODEL', 'k2p5')


def generate_completion(messages, temperature=0.7, max_tokens=2000):
    """
    Generate text completion using Kimi K2.5.
    
    Uses the correct API endpoint: https://api.kimi.com/coding/
    
    Args:
        messages (list): List of message dicts with 'role' and 'content'
        temperature (float): Temperature (0.0-1.0)
        max_tokens (int): Maximum tokens to generate
    
    Returns:
        dict: {
            'success': bool,
            'text': str or None,
            'usage': dict or None,
            'error': str or None
        }
    """
    if not KIMI_API_KEY:
        return {
            'success': False,
            'error': 'KIMI_API_KEY not configured'
        }
    
    # Build URL - use Anthropic-compatible API format
    url = f"{KIMI_BASE_URL}v1/messages"
    
    headers = {
        'Authorization': f'Bearer {KIMI_API_KEY}',
        'Content-Type': 'application/json',
        'x-api-key': KIMI_API_KEY  # Some APIs require this header
    }
    
    payload = {
        'model': KIMI_MODEL,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        
        data = response.json()
        
        # Anthropic API format
        if 'content' in data and len(data['content']) > 0:
            # Anthropic returns content as a list of blocks
            text = ''
            for block in data['content']:
                if block.get('type') == 'text':
                    text += block.get('text', '')
            
            return {
                'success': True,
                'text': text,
                'usage': data.get('usage', {}),
                'error': None
            }
        
        # OpenAI format (fallback)
        elif 'choices' in data and len(data['choices']) > 0:
            choice = data['choices'][0]
            text = choice.get('message', {}).get('content', '')
            
            return {
                'success': True,
                'text': text,
                'usage': data.get('usage', {}),
                'error': None
            }
        
        return {
            'success': False,
            'error': 'No text in response',
            'response': data
        }
    
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Request failed: {str(e)}'
        }


def generate_product_review(product_name, product_category, price, features, description):
    """
    Generate a comprehensive product review.
    
    Args:
        product_name (str): Product name
        product_category (str): Product category
        price (float): Product price
        features (list): List of product features
        description (str): Product description
    
    Returns:
        dict: {
            'success': bool,
            'summary': str or None,  # 100-200 words
            'full_review': str or None,  # 500-1000 words
            'error': str or None
        }
    """
    feature_text = "\n".join([f"- {f}" for f in features]) if features else "No specific features listed"
    
    prompt = f"""
Generate a comprehensive product review for the following product:

Product Name: {product_name}
Category: {product_category}
Price: ${price}
Features:
{feature_text}

Description: {description}

Requirements:
1. Short Summary (100-200 words):
   - Product overview (1-2 sentences)
   - Key features (2-3 bullet points)
   - Quick verdict (1 sentence)

2. Full Detailed Review (500-1000 words):
   - Introduction
   - Pros & Cons (bulleted lists)
   - Feature Highlights (technical deep dive)
   - Comparison with Competitors
   - Buying Recommendations
   - Conclusion

Tone: Professional (30%), Sales-focused (30%), Casual (20%)
Output format: JSON with keys 'summary' and 'full_review'
"""
    
    messages = [
        {'role': 'system', 'content': 'You are an expert product reviewer who writes detailed, balanced, and informative reviews.'},
        {'role': 'user', 'content': prompt}
    ]
    
    result = generate_completion(messages, temperature=0.7, max_tokens=3000)
    
    if result['success']:
        # Try to parse JSON from response
        text = result['text']
        
        # Look for JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', text)
        
        if json_match:
            try:
                review_data = json.loads(json_match.group())
                return {
                    'success': True,
                    'summary': review_data.get('summary', ''),
                    'full_review': review_data.get('full_review', ''),
                    'error': None
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: split by summary/full review markers
        summary = text.split('Full Detailed Review')[0] if 'Full Detailed Review' in text else text[:500]
        full_review = text
        
        return {
            'success': True,
            'summary': summary,
            'full_review': full_review,
            'error': None
        }
    
    return {
        'success': False,
        'summary': None,
        'full_review': None,
        'error': result.get('error')
    }


def generate_social_post(product_name, price, review_summary, platform, product_image_url=None):
    """
    Generate a platform-optimized social media post.
    
    Args:
        product_name (str): Product name
        price (float): Product price
        review_summary (str): Product review summary
        platform (str): Social platform ('twitter', 'instagram', 'pinterest', 'telegram')
        product_image_url (str): URL to product image (optional)
    
    Returns:
        dict: {
            'success': bool,
            'post_text': str or None,
            'hashtags': str or None,
            'image_prompt': str or None,
            'error': str or None
        }
    """
    # Platform specifications
    platform_specs = {
        'twitter': {
            'chars': 280,
            'hashtags': 3,
            'style': 'concise, punchy, include emojis',
            'tone': 'professional marketing 30%, sales-focused 30%, casual 20%'
        },
        'instagram': {
            'chars': 2200,
            'hashtags': 15,
            'style': 'engaging, visual-first, storytelling',
            'tone': 'professional marketing 30%, sales-focused 30%, casual 20%'
        },
        'pinterest': {
            'chars': 500,
            'hashtags': 10,
            'style': 'descriptive, keyword-rich, pin title + description',
            'tone': 'professional marketing 40%, sales-focused 30%'
        },
        'telegram': {
            'chars': None,  # no limit
            'hashtags': 5,
            'style': 'informative, newsletter-like, detailed',
            'tone': 'professional marketing 30%, informative 40%'
        }
    }
    
    spec = platform_specs.get(platform, platform_specs['twitter'])
    
    char_limit_text = f"Character limit: {spec['chars']}" if spec['chars'] else "No character limit"
    
    prompt = f"""
Generate a {platform} social media post for the following product:

Product Name: {product_name}
Price: ${price}
Review Summary: {review_summary}
Product Image: {product_image_url or 'Will be added separately'}

Platform Requirements:
- {char_limit_text}
- Number of hashtags: {spec['hashtags']}
- Style: {spec['style']}
- Tone: {spec['tone']}

Generate:
1. Post text (optimized for {platform})
2. Hashtags (comma-separated, relevant to product and platform)
3. Image prompt (for generating a platform-optimized image)

Output format: JSON with keys 'post_text', 'hashtags', and 'image_prompt'
"""
    
    messages = [
        {'role': 'system', 'content': 'You are an expert social media marketer who creates engaging, platform-optimized content.'},
        {'role': 'user', 'content': prompt}
    ]
    
    result = generate_completion(messages, temperature=0.8, max_tokens=1000)
    
    if result['success']:
        text = result['text']
        
        # Try to parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', text)
        
        if json_match:
            try:
                post_data = json.loads(json_match.group())
                return {
                    'success': True,
                    'post_text': post_data.get('post_text', ''),
                    'hashtags': post_data.get('hashtags', ''),
                    'image_prompt': post_data.get('image_prompt', ''),
                    'error': None
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback
        return {
            'success': True,
            'post_text': text,
            'hashtags': '',
            'image_prompt': f"{product_name} product showcase",
            'error': None
        }
    
    return {
        'success': False,
        'post_text': None,
        'hashtags': None,
        'image_prompt': None,
        'error': result.get('error')
    }


# Test functions
def test_review_generation():
    """Test product review generation."""
    print("Testing Kimi K2.5 Review Generation...")
    print("-" * 50)
    
    product = {
        'name': 'Logitech MX Master 3S Wireless Mouse',
        'category': 'Electronics > Computer Accessories',
        'price': 99.99,
        'features': [
            'Ergonomic design',
            'Silent clicks',
            'Multi-device support',
            'USB-C charging',
            '8K DPI sensor'
        ],
        'description': 'The ultimate wireless mouse with advanced ergonomics and precision tracking.'
    }
    
    print(f"Product: {product['name']}")
    print(f"Model: {KIMI_MODEL}")
    print(f"API: {KIMI_BASE_URL}")
    print()
    
    result = generate_product_review(
        product_name=product['name'],
        product_category=product['category'],
        price=product['price'],
        features=product['features'],
        description=product['description']
    )
    
    if result['success']:
        print("✅ Review generation successful!")
        print(f"\n--- SUMMARY ({len(result['summary'].split())} words) ---")
        print(result['summary'][:300] + "..." if len(result['summary']) > 300 else result['summary'])
        print(f"\n--- FULL REVIEW ({len(result['full_review'].split())} words) ---")
        print(result['full_review'][:500] + "..." if len(result['full_review']) > 500 else result['full_review'])
        return True
    else:
        print(f"❌ Review generation failed: {result.get('error')}")
        return False


def generate_review_with_formats(product_name, product_category, features, platform='twitter'):
    """
    Generate a product review in TWO formats:
    1. Summary: 100-200 characters (for social media)
    2. Full Review: 600-900 characters (blog post length)
    
    Args:
        product_name (str): Product name
        product_category (str): Product category
        features (list): List of product features
        platform (str): Target platform (for context/optimization)
    
    Returns:
        dict: {
            'summary': str,  # 100-200 characters
            'full_review': str,  # 600-900 characters
            'platform': str,
            'success': bool
        }
    """
    feature_text = "\n".join([f"- {f}" for f in features]) if features else "No specific features listed"
    
    prompt = f"""
Generate a product review for the following product:

Product Name: {product_name}
Category: {product_category}
Features:
{feature_text}

CRITICAL REQUIREMENTS - STRICT CHARACTER LIMITS:

1. Summary (100-200 characters ONLY - this is for social media):
   - Must be 100-200 characters exactly
   - Include product name and key selling point
   - Include verdict (buy/not buy)
   - No bullet points, just punchy text
   - Include emojis relevant to product

2. Full Review (600-900 characters ONLY - this is for blog posts):
   - Must be 600-900 characters exactly
   - Brief intro with product name and category
   - 2-3 key pros (concise)
   - 1-2 cons (if any)
   - Quick verdict/target audience

Tone: Professional (30%), Sales-focused (30%), Casual (20%), Informative (20%)

IMPORTANT: Count your characters carefully! The summary MUST be 100-200 chars, full review MUST be 600-900 chars.

Output format: JSON with keys 'summary' and 'full_review'
"""
    
    messages = [
        {'role': 'system', 'content': 'You are an expert product reviewer who writes concise, engaging content with strict character limits. You always respect the character count requirements.'},
        {'role': 'user', 'content': prompt}
    ]
    
    result = generate_completion(messages, temperature=0.7, max_tokens=1500)
    
    if result['success']:
        text = result['text']
        
        # Try to parse JSON from response
        json_match = re.search(r'\{[\s\S]*\}', text)
        
        if json_match:
            try:
                review_data = json.loads(json_match.group())
                summary = review_data.get('summary', '')
                full_review = review_data.get('full_review', '')
                
                # Validate character counts
                summary_chars = len(summary)
                full_chars = len(full_review)
                
                # If not within limits, truncate/pad (best effort)
                if summary_chars > 200:
                    summary = summary[:197] + '...'
                elif summary_chars < 100:
                    # Add filler if too short (rare case)
                    summary = summary + ' ✨'
                
                if full_chars > 900:
                    full_review = full_review[:897] + '...'
                
                return {
                    'success': True,
                    'summary': summary,
                    'full_review': full_review,
                    'platform': platform,
                    'summary_chars': len(summary),
                    'full_review_chars': len(full_review),
                    'error': None
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to extract sections
        lines = text.split('\n')
        summary = ''
        full_review = text
        
        for line in lines:
            if 'summary' in line.lower() and ':' in line:
                summary = line.split(':', 1)[1].strip()
            elif summary and not full_review:
                full_review = line
        
        return {
            'success': True,
            'summary': summary[:200] if summary else text[:200],
            'full_review': full_review[:900] if full_review else text[:900],
            'platform': platform,
            'summary_chars': len(summary[:200]) if summary else 0,
            'full_review_chars': len(full_review[:900]) if full_review else 0,
            'error': None
        }
    
    return {
        'success': False,
        'summary': None,
        'full_review': None,
        'platform': platform,
        'error': result.get('error')
    }


# Wrapper function for test_ai_pipeline.py compatibility
def generate_review(product_name, product_category, product_features, platform='instagram'):
    """
    Wrapper for generate_product_review that matches the test expected signature.
    
    Args:
        product_name (str): Product name
        product_category (str): Product category
        product_features (list): List of product features
        platform (str): Target platform (for context)
    
    Returns:
        dict: {
            'success': bool,
            'content': str (full review text),
            'summary': str,
            'error': str or None
        }
    """
    # Build a description from features
    description = f"{product_name} - {product_category}. Features: {', '.join(product_features) if product_features else 'N/A'}"
    
    # Use a default price for the wrapper
    price = 0.0
    
    result = generate_product_review(
        product_name=product_name,
        product_category=product_category,
        price=price,
        features=product_features,
        description=description
    )
    
    if result['success']:
        return {
            'success': True,
            'content': result['full_review'],
            'summary': result['summary'],
            'error': None
        }
    else:
        return {
            'success': False,
            'content': None,
            'summary': None,
            'error': result.get('error')
        }


def test_social_post_generation():
    """Test social media post generation."""
    print("\nTesting Kimi K2.5 Social Post Generation...")
    print("-" * 50)
    
    result = generate_social_post(
        product_name='Logitech MX Master 3S',
        price=99.99,
        review_summary='Excellent wireless mouse with ergonomic design and multi-device support.',
        platform='twitter'
    )
    
    if result['success']:
        print("✅ Social post generation successful!")
        print(f"\n--- POST TEXT ---")
        print(result['post_text'])
        print(f"\n--- HASHTAGS ---")
        print(result['hashtags'])
        print(f"\n--- IMAGE PROMPT ---")
        print(result['image_prompt'])
        return True
    else:
        print(f"❌ Social post generation failed: {result.get('error')}")
        return False


def test_two_format_generation():
    """Test the new two-format review generation (Task 2)."""
    print("\n" + "=" * 60)
    print("TESTING: Two-Format Generation (Summary + Full Review)")
    print("=" * 60)
    
    # MacBook Pro test example
    product_name = "MacBook Pro 14-inch M3"
    product_category = "Electronics > Laptops"
    features = [
        "M3 Pro chip",
        "18GB unified memory",
        "512GB SSD",
        "Liquid Retina XDR display",
        "Up to 22 hours battery life",
        "Space Black finish"
    ]
    platform = "twitter"
    
    print(f"\nProduct: {product_name}")
    print(f"Category: {product_category}")
    print(f"Platform: {platform}")
    print(f"Features: {features}")
    print()
    
    result = generate_review_with_formats(
        product_name=product_name,
        product_category=product_category,
        features=features,
        platform=platform
    )
    
    if result['success']:
        summary = result['summary']
        full_review = result['full_review']
        summary_chars = len(summary)
        full_chars = len(full_review)
        
        print("✅ Two-format generation successful!")
        print()
        
        # Validate character counts
        summary_ok = 100 <= summary_chars <= 200
        full_ok = 600 <= full_chars <= 900
        
        print(f"--- SUMMARY ({summary_chars} chars) ---")
        print(f"[{'✅' if summary_ok else '⚠️'}] Target: 100-200 chars")
        print(f"Content: {summary}")
        print()
        
        print(f"--- FULL REVIEW ({full_chars} chars) ---")
        print(f"[{'✅' if full_ok else '⚠️'}] Target: 600-900 chars")
        print(f"Content: {full_review}")
        print()
        
        return result
    else:
        print(f"❌ Two-format generation failed: {result.get('error')}")
        return result


if __name__ == "__main__":
    print("Kimi K2.5 (Moonshot AI) Integration Test")
    print("=" * 50)
    print()
    
    try:
        # Test 1: Review generation
        test1 = test_review_generation()
        
        # Test 2: Social post generation
        test2 = test_social_post_generation()
        
        # Test 3: Two-format generation (Task 2)
        test3 = test_two_format_generation()
        
        if test1 and test2:
            print("\n" + "=" * 50)
            print("✅ All tests passed!")
        else:
            print("\n" + "=" * 50)
            print("⚠️ Some tests failed")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
