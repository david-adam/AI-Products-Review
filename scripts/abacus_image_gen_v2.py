#!/usr/bin/env python3
"""
Abacus.AI Nano Banana Pro Integration for ProductLens AI

Generates platform-optimized product images using the original Amazon product image as reference.
"""

import os
import requests
import json
import base64
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ABACUSAI_API_KEY = os.getenv('ABACUSAI_API_KEY')
ABACUSAI_BASE_URL = os.getenv('ABACUSAI_BASE_URL', 'https://routellm.abacus.ai/v1')
ABACUSAI_MODEL = os.getenv('ABACUSAI_MODEL', 'nano-banana-pro')


def download_image(url, timeout=30):
    """
    Download an image from URL.
    
    Args:
        url (str): Image URL
        timeout (int): Request timeout
    
    Returns:
        str: Path to downloaded image or None if failed
    """
    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Save to temp file
        suffix = '.jpg' if '.jp' in url.lower() else '.png'
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            return tmp.name
    
    except Exception as e:
        print(f"Error downloading image: {e}")
        return None


def image_to_base64(image_path):
    """
    Convert image file to base64.
    
    Args:
        image_path (str): Path to image file
    
    Returns:
        str: Base64 encoded image
    """
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def generate_image_with_reference(product_image_url, platform, product_name=None, product_category=None):
    """
    Generate a platform-optimized product image using the original product image as reference.
    
    Args:
        product_image_url (str): URL of the Amazon product image
        platform (str): Social platform ('twitter', 'instagram', 'pinterest', 'telegram')
        product_name (str): Product name (optional)
        product_category (str): Product category (optional)
    
    Returns:
        dict: {
            'success': bool,
            'image_url': str or None,  # Abacus.AI hosted image URL
            'image_data': base64 str or None,
            'aspect_ratio': str,
            'error': str or None
        }
    """
    if not ABACUSAI_API_KEY:
        return {
            'success': False,
            'error': 'ABACUSAI_API_KEY not configured'
        }
    
    # Download the reference image
    print(f"  Downloading reference image...")
    ref_image_path = download_image(product_image_url)
    
    if not ref_image_path:
        return {
            'success': False,
            'error': f'Failed to download product image from {product_image_url}'
        }
    
    print(f"  Downloaded: {ref_image_path}")
    
    # Convert to base64
    print(f"  Converting to base64...")
    ref_image_base64 = image_to_base64(ref_image_path)
    
    # Platform specifications
    platform_configs = {
        'twitter': {
            'aspect_ratio': '16:9',
            'style': 'horizontal, social media style, add subtle gradients and shadows'
        },
        'instagram': {
            'aspect_ratio': '1:1',
            'style': 'square, Instagram-optimized, clean background, professional lighting'
        },
        'pinterest': {
            'aspect_ratio': '9:16',
            'style': 'vertical, Pinterest-optimized, lifestyle background, text overlay area'
        },
        'telegram': {
            'aspect_ratio': '16:9',
            'style': 'horizontal, newsletter style, clean and professional'
        }
    }
    
    config = platform_configs.get(platform, platform_configs['twitter'])
    
    # Build prompt
    product_info = f"for {product_name}" if product_name else ""
    category_info = f"in {product_category}" if product_category else ""
    
    prompt = f"""
Create a platform-optimized social media image {product_info} {category_info}.

Using the uploaded product image as reference:
1. Maintain the product's appearance and key features
2. Optimize for {platform} ({config['aspect_ratio']} aspect ratio)
3. Style: {config['style']}
4. Add appropriate background that complements the product
5. Ensure professional quality suitable for social media marketing

Platform: {platform}
Aspect ratio: {config['aspect_ratio']}
"""
    
    # Build payload with image reference
    payload = {
        'model': ABACUSAI_MODEL,
        'messages': [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/jpeg;base64,{ref_image_base64}'
                        }
                    },
                    {
                        'type': 'text',
                        'text': prompt.strip()
                    }
                ]
            }
        ],
        'modalities': ['image'],
        'image_config': {
            'num_images': 1,
            'aspect_ratio': config['aspect_ratio']
        }
    }
    
    print(f"  Generating {platform} image (this may take 30-60 seconds)...")
    
    try:
        response = requests.post(
            f"{ABACUSAI_BASE_URL}/chat/completions",
            headers={
                'Authorization': f'Bearer {ABACUSAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json=payload,
            timeout=90
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Clean up temp file
        os.unlink(ref_image_path)
        
        # Check for image in response
        if 'choices' in data and len(data['choices']) > 0:
            choice = data['choices'][0]
            
            # Check for image_url (Abacus.AI returns hosted URL)
            if 'message' in choice:
                message = choice['message']
                
                # Look for image_url first
                if 'images' in message and len(message['images']) > 0:
                    image_obj = message['images'][0]
                    
                    # Check if it's the new format with nested image_url
                    if 'image_url' in image_obj and isinstance(image_obj['image_url'], dict):
                        url = image_obj['image_url'].get('url')
                        if url:
                            # Check if it's a hosted URL or base64 data URL
                            if url.startswith('data:image'):
                                # Base64 data URL - extract the data
                                image_data = url.split(',', 1)[1] if ',' in url else url.split(':', 1)[1]
                                return {
                                    'success': True,
                                    'image_url': None,
                                    'image_data': image_data,
                                    'aspect_ratio': config['aspect_ratio'],
                                    'error': None
                                }
                            else:
                                # Regular hosted URL
                                return {
                                    'success': True,
                                    'image_url': url,
                                    'image_data': None,
                                    'aspect_ratio': config['aspect_ratio'],
                                    'error': None
                                }
                    
                    # Legacy format: direct image_url string
                    elif 'url' in image_obj:
                        url = image_obj['url']
                        if url.startswith('data:image'):
                            image_data = url.split(',', 1)[1] if ',' in url else url.split(':', 1)[1]
                            return {
                                'success': True,
                                'image_url': None,
                                'image_data': image_data,
                                'aspect_ratio': config['aspect_ratio'],
                                'error': None
                            }
                        else:
                            return {
                                'success': True,
                                'image_url': url,
                                'image_data': None,
                                'aspect_ratio': config['aspect_ratio'],
                                'error': None
                            }
                
                # Fallback: check content field for data URL
                if 'content' in message and isinstance(message['content'], str) and message['content'].startswith('data:image'):
                    image_data = message['content'].split(',', 1)[1]
                    return {
                        'success': True,
                        'image_url': None,
                        'image_data': image_data,
                        'aspect_ratio': config['aspect_ratio'],
                        'error': None
                    }
        
        return {
            'success': False,
            'error': 'No image in response',
            'response': data
        }
    
    except requests.exceptions.RequestException as e:
        # Clean up temp file on error
        if os.path.exists(ref_image_path):
            os.unlink(ref_image_path)
        
        return {
            'success': False,
            'error': f'Request failed: {str(e)}'
        }


def generate_product_image_old(product_name, product_category, platform, features=None):
    """
    Legacy function for text-only image generation (without reference image).
    Kept for backwards compatibility.
    """
    # Platform-specific dimensions
    platform_configs = {
        'twitter': {'aspect_ratio': '16:9', 'style': 'horizontal, social media style'},
        'instagram': {'aspect_ratio': '1:1', 'style': 'square, Instagram-optimized'},
        'pinterest': {'aspect_ratio': '9:16', 'style': 'vertical, Pinterest-optimized'},
        'telegram': {'aspect_ratio': '16:9', 'style': 'horizontal, newsletter style'}
    }
    
    config = platform_configs.get(platform, platform_configs['twitter'])
    
    # Build prompt
    feature_text = ""
    if features:
        feature_text = f"\nKey features: {', '.join(features[:3])}"
    
    prompt = f"""
Professional product photography for: {product_name}
Category: {product_category}{feature_text}
Style: Clean, modern, e-commerce showcase, {config['style']}
Background: Neutral gradient with subtle lighting
Quality: High resolution, professional product shot
Platform: {platform} ({config['aspect_ratio']})
Composition: Product centered, studio lighting, commercial photography
"""
    
    # Call API without image reference
    # (implementation omitted for brevity - see old version)
    pass


# Test function
def test_image_generation_with_reference():
    """
    Test image generation with a reference image.
    """
    print("Testing Abacus.AI Nano Banana Pro with Image Reference...")
    print("-" * 60)
    
    # Use a sample product image URL (Laptop)
    test_image_url = "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800"
    
    print(f"Reference image: {test_image_url}")
    print(f"Model: {ABACUSAI_MODEL}")
    print(f"API: {ABACUSAI_BASE_URL}")
    print()
    
    # Test for Instagram
    result = generate_image_with_reference(
        product_image_url=test_image_url,
        platform='instagram',
        product_name='Laptop Computer',
        product_category='Electronics > Computers'
    )
    
    if result['success']:
        print("✅ Image generation successful!")
        print(f"   Aspect ratio: {result['aspect_ratio']}")
        
        if result['image_url']:
            print(f"   Image URL: {result['image_url']}")
        
        if result['image_data']:
            # Save test image AND reference image
            import tempfile
            import base64
            
            # Save generated image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False, prefix='generated_') as tmp:
                with open(tmp.name, 'wb') as f:
                    f.write(base64.b64decode(result['image_data']))
                print(f"\n📸 Generated image saved to: {tmp.name}")
                print(f"   File size: {os.path.getsize(tmp.name)} bytes")
                
                # Also save reference image for comparison
                import requests
                ref_response = requests.get(test_image_url)
                ref_path = tmp.name.replace('generated_', 'reference_')
                with open(ref_path, 'wb') as f:
                    f.write(ref_response.content)
                print(f"\n📷 Reference image saved to: {ref_path}")
                print(f"   File size: {os.path.getsize(ref_path)} bytes")
                
                print(f"\n💡 Compare the two images to verify the AI used the reference!")
        
        return True
    else:
        print(f"❌ Image generation failed: {result.get('error')}")
        return False


if __name__ == "__main__":
    print("Abacus.AI Nano Banana Pro - Image-to-Image Generation Test")
    print("=" * 60)
    print()
    
    try:
        success = test_image_generation_with_reference()
        
        if success:
            print("\n" + "=" * 60)
            print("✅ Test passed!")
        else:
            print("\n" + "=" * 60)
            print("⚠️ Test failed")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
