#!/usr/bin/env python3
"""
Abacus.AI Nano Banana Pro Integration for ProductLens AI

Generates product images using the Nano Banana Pro model.
"""

import os
import requests
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ABACUSAI_API_KEY = os.getenv('ABACUSAI_API_KEY')
ABACUSAI_BASE_URL = os.getenv('ABACUSAI_BASE_URL', 'https://routellm.abacus.ai/v1')
ABACUSAI_MODEL = os.getenv('ABACUSAI_MODEL', 'nano-banana-pro')


def generate_image(prompt, aspect_ratio="16:9", num_images=1):
    """
    Generate an image using Abacus.AI Nano Banana Pro.
    
    Args:
        prompt (str): Text description of the image to generate
        aspect_ratio (str): Aspect ratio ('16:9', '4:3', '1:1', '9:16')
        num_images (int): Number of images to generate (default: 1)
    
    Returns:
        dict: {
            'success': bool,
            'image_url': str or None,
            'image_data': base64 str or None,
            'error': str or None
        }
    """
    if not ABACUSAI_API_KEY:
        return {
            'success': False,
            'error': 'ABACUSAI_API_KEY not configured'
        }
    
    url = f"{ABACUSAI_BASE_URL}/chat/completions"
    
    headers = {
        'Authorization': f'Bearer {ABACUSAI_API_KEY}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        'model': ABACUSAI_MODEL,
        'messages': [
            {
                'role': 'user',
                'content': prompt
            }
        ],
        'modalities': ['image'],
        'image_config': {
            'num_images': num_images,
            'aspect_ratio': aspect_ratio
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        
        data = response.json()
        
        # Abacus.AI returns images in message.images[], not content
        if 'choices' in data and len(data['choices']) > 0:
            choice = data['choices'][0]
            
            if 'message' in choice:
                msg = choice['message']
                
                # Check for images array (Abacus.AI format)
                if 'images' in msg and msg['images']:
                    img_url = msg['images'][0]['image_url']['url']
                    return {
                        'success': True,
                        'image_data': img_url,  # Keep as data URL
                        'image_url': None,
                        'error': None
                    }
                
                # Fallback: check content field
                if 'content' in msg and msg['content']:
                    content = msg['content']
                    if isinstance(content, str):
                        return {
                            'success': True,
                            'image_data': content,
                            'image_url': None,
                            'error': None
                        }
        
        return {
            'success': False,
            'error': 'No image data in response',
            'response': data
        }
    
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Request failed: {str(e)}'
        }


def save_image(image_data, output_path):
    """
    Save base64 image data to a file.
    
    Args:
        image_data (str): Base64 encoded image data
        output_path (str): Path to save the image
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Remove data URL prefix if present
        if image_data.startswith('data:image/'):
            image_data = image_data.split(',', 1)[1]
        
        # Decode and save
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(image_data))
        
        return True
    
    except Exception as e:
        print(f"Error saving image: {e}")
        return False


def generate_product_image(product_name, product_category, platform, features=None):
    """
    Generate a platform-optimized product image.
    
    Args:
        product_name (str): Product name
        product_category (str): Product category
        platform (str): Social platform ('twitter', 'instagram', 'pinterest', 'telegram')
        features (list): List of key features (optional)
    
    Returns:
        dict: {
            'success': bool,
            'image_data': str or None,
            'aspect_ratio': str,
            'error': str or None
        }
    """
    # Platform-specific dimensions
    platform_configs = {
        'twitter': {
            'aspect_ratio': '16:9',
            'style': 'horizontal, social media style'
        },
        'instagram': {
            'aspect_ratio': '1:1',
            'style': 'square, Instagram-optimized'
        },
        'pinterest': {
            'aspect_ratio': '9:16',
            'style': 'vertical, Pinterest-optimized'
        },
        'telegram': {
            'aspect_ratio': '16:9',
            'style': 'horizontal, newsletter style'
        }
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
    
    # Generate image
    result = generate_image(
        prompt=prompt.strip(),
        aspect_ratio=config['aspect_ratio'],
        num_images=1
    )
    
    result['aspect_ratio'] = config['aspect_ratio']
    return result


# Test function
def test_image_generation():
    """
    Test the Abacus.AI image generation functionality.
    """
    import tempfile
    
    print("Testing Abacus.AI Nano Banana Pro...")
    print("-" * 50)
    
    # Test prompt
    prompt = "A highly detailed digital painting of a futuristic laptop with a holographic display, cyberpunk style, neon lights"
    
    print(f"Prompt: {prompt}")
    print(f"Model: {ABACUSAI_MODEL}")
    print(f"API: {ABACUSAI_BASE_URL}")
    print()
    
    result = generate_image(prompt, aspect_ratio="16:9")
    
    if result['success']:
        print("✅ Image generation successful!")
        
        # Save test image
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            output_path = tmp.name
        
        if save_image(result['image_data'], output_path):
            print(f"✅ Test image saved: {output_path}")
            print(f"   File size: {os.path.getsize(output_path)} bytes")
            
            # Clean up
            os.unlink(output_path)
        
        return True
    else:
        print(f"❌ Image generation failed: {result.get('error', 'Unknown error')}")
        return False


if __name__ == "__main__":
    print("Abacus.AI Nano Banana Pro Integration Test")
    print("=" * 50)
    print()
    
    try:
        success = test_image_generation()
        
        if success:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Tests failed!")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
