#!/usr/bin/env python3
"""
Debug script to test Abacus.AI image reference format
"""

import os
import requests
import json
import base64
import tempfile
from dotenv import load_dotenv

load_dotenv()

ABACUSAI_API_KEY = os.getenv('ABACUSAI_API_KEY')
ABACUSAI_BASE_URL = os.getenv('ABACUSAI_BASE_URL', 'https://routellm.abacus.ai/v1')

def test_image_input_formats():
    """
    Test different ways to send an image reference to Abacus.AI
    """
    
    # Download a test image
    test_url = "https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=800"
    print(f"Downloading test image: {test_url}")
    
    response = requests.get(test_url, timeout=30)
    response.raise_for_status()
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp.write(response.content)
        tmp_path = tmp.name
    
    print(f"Downloaded to: {tmp_path}")
    print(f"File size: {os.path.getsize(tmp_path)} bytes")
    
    # Convert to base64
    with open(tmp_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"Base64 length: {len(image_base64)} characters")
    
    # Test 1: data URL format
    print("\n" + "="*60)
    print("Test 1: Sending image as data URL (data:image/jpeg;base64,...)")
    print("="*60)
    
    payload1 = {
        'model': 'nano-banana-pro',
        'messages': [
            {
                'role': 'user',
                'content': [
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f'data:image/jpeg;base64,{image_base64}'
                        }
                    },
                    {
                        'type': 'text',
                        'text': 'Redraw this laptop image exactly as shown, maintaining all details.'
                    }
                ]
            }
        ],
        'modalities': ['image'],
        'max_tokens': 1000
    }
    
    try:
        print("Sending request...")
        response1 = requests.post(
            f"{ABACUSAI_BASE_URL}/chat/completions",
            headers={
                'Authorization': f'Bearer {ABACUSAI_API_KEY}',
                'Content-Type': 'application/json'
            },
            json=payload1,
            timeout=90
        )
        
        print(f"Status code: {response1.status_code}")
        
        if response1.status_code == 200:
            data1 = response1.json()
            
            # Save response for inspection
            with open('/tmp/abacus_response1.json', 'w') as f:
                json.dump(data1, f, indent=2)
            print("Response saved to: /tmp/abacus_response1.json")
            
            # Check structure
            print("\nResponse structure:")
            print(f"  Has 'choices': {('choices' in data1)}")
            if 'choices' in data1 and len(data1['choices']) > 0:
                print(f"  Choices count: {len(data1['choices'])}")
                choice = data1['choices'][0]
                print(f"  Has 'message': {('message' in choice)}")
                if 'message' in choice:
                    msg = choice['message']
                    print(f"  Message keys: {list(msg.keys())}")
                    if 'images' in msg:
                        print(f"  Images count: {len(msg['images'])}")
                    if 'content' in msg:
                        content = msg['content']
                        if isinstance(content, str):
                            print(f"  Content type: str")
                            print(f"  Content preview: {content[:100]}...")
                        else:
                            print(f"  Content type: {type(content)}")
        else:
            print(f"Error: {response1.text}")
    
    except Exception as e:
        print(f"Request failed: {e}")
    
    # Clean up
    os.unlink(tmp_path)
    print(f"\nCleaned up temp file")


if __name__ == "__main__":
    print("Abacus.AI Image Input Format Test")
    print("=" * 60)
    test_image_input_formats()
