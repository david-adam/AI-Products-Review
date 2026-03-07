#!/usr/bin/env python3
"""
Kimi K2.5 (Moonshot AI) Integration for ProductLens AI

Generates product reviews and social media posts using Kimi K2.5.
Uses the code-deep agent (which has working Kimi K2.5 access) via OpenClaw CLI.
"""

import os
import subprocess
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

KIMI_API_KEY = os.getenv('KIMI_API_KEY')
KIMI_BASE_URL = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')
KIMI_MODEL = os.getenv('KIMI_MODEL', 'kimi-k2.5')


def generate_completion_via_agent(messages, temperature=0.7, max_tokens=2000):
    """
    Generate text completion using Kimi K2.5 via the code-deep agent.
    
    Uses 'openclaw agent --agent coder-deep' to invoke Kimi K2.5.
    
    Args:
        messages (list): List of message dicts with 'role' and 'content'
        temperature (float): Temperature (0.0-1.0) - passed to agent as context
        max_tokens (int): Maximum tokens to generate - passed to agent as context
    
    Returns:
        dict: {
            'success': bool,
            'text': str or None,
            'usage': dict or None,
            'error': str or None
        }
    """
    # Convert messages to a simple prompt format
    system_msg = ""
    user_msg = ""
    
    for msg in messages:
        if msg.get('role') == 'system':
            system_msg = msg.get('content', '')
        elif msg.get('role') == 'user':
            user_msg = msg.get('content', '')
    
    # Build the prompt for the agent
    prompt = f"""{system_msg}

Generate a response with temperature={temperature} and max_tokens={max_tokens}.

---
User Request:
{user_msg}
---
"""
    
    try:
        # Call the code-deep agent via OpenClaw CLI
        result = subprocess.run(
            ['openclaw', 'agent', '--agent', 'coder-deep', '-m', prompt, '--timeout', '180'],
            capture_output=True,
            text=True,
            timeout=200
        )
        
        if result.returncode == 0:
            text = result.stdout.strip()
            if text:
                return {
                    'success': True,
                    'text': text,
                    'usage': {'via': 'coder-deep-agent'},
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'text': None,
                    'usage': None,
                    'error': 'Empty response from agent'
                }
        else:
            return {
                'success': False,
                'text': None,
                'usage': None,
                'error': f'Agent error: {result.stderr}'
            }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'text': None,
            'usage': None,
            'error': 'Request timeout'
        }
    except Exception as e:
        return {
            'success': False,
            'text': None,
            'usage': None,
            'error': f'Request failed: {str(e)}'
        }


def generate_completion(messages, temperature=0.7, max_tokens=2000):
    """
    Generate text completion using Kimi K2.5 via the code-deep agent.
    
    This is the primary method - it uses the OpenClaw code-deep agent
    which has working Kimi K2.5 access.
    
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
    # Use the agent-based approach (primary method)
    return generate_completion_via_agent(messages, temperature, max_tokens)


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
                
                # Handle both flat and nested JSON structures
                summary = review_data.get('summary', '')
                full_review = review_data.get('full_review', '')
                
                # If summary/full_review are dicts, convert to string
                if isinstance(summary, dict):
                    summary = json.dumps(summary, indent=2)
                if isinstance(full_review, dict):
                    full_review = json.dumps(full_review, indent=2)
                
                return {
                    'success': True,
                    'summary': str(summary) if summary else '',
                    'full_review': str(full_review) if full_review else '',
                    'error': None
                }
            except (json.JSONDecodeError, Exception):
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
                
                # Handle both flat and nested JSON structures
                post_text = post_data.get('post_text', '')
                hashtags = post_data.get('hashtags', '')
                image_prompt = post_data.get('image_prompt', '')
                
                # Convert dicts to strings if needed
                if isinstance(post_text, dict):
                    post_text = json.dumps(post_text, indent=2)
                if isinstance(hashtags, dict):
                    hashtags = json.dumps(hashtags, indent=2)
                if isinstance(image_prompt, dict):
                    image_prompt = json.dumps(image_prompt, indent=2)
                
                return {
                    'success': True,
                    'post_text': str(post_text) if post_text else '',
                    'hashtags': str(hashtags) if hashtags else '',
                    'image_prompt': str(image_prompt) if image_prompt else '',
                    'error': None
                }
            except (json.JSONDecodeError, Exception):
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
        
        # Handle summary (could be string or JSON string)
        summary = result.get('summary', '')
        if isinstance(summary, dict):
            summary = json.dumps(summary, indent=2)
        summary = str(summary)
        
        full_review = result.get('full_review', '')
        if isinstance(full_review, dict):
            full_review = json.dumps(full_review, indent=2)
        full_review = str(full_review)
        
        print(f"\n--- SUMMARY ({len(summary.split())} words) ---")
        print(summary[:500] + "..." if len(summary) > 500 else summary)
        print(f"\n--- FULL REVIEW ({len(full_review.split())} words) ---")
        print(full_review[:700] + "..." if len(full_review) > 700 else full_review)
        return True
    else:
        print(f"❌ Review generation failed: {result.get('error')}")
        return False


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


if __name__ == "__main__":
    print("Kimi K2.5 (Moonshot AI) Integration Test")
    print("=" * 50)
    print()
    
    try:
        # Test 1: Review generation
        test1 = test_review_generation()
        
        # Test 2: Social post generation
        test2 = test_social_post_generation()
        
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
