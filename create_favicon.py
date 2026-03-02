#!/usr/bin/env python3
"""
Generate app icon and favicon for Amazon Affiliate Bot
Creates simple, clean icon with gradient background
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon(size=(512, 512), output_path='app-icon.png'):
    """Create app icon with gradient background and text"""
    
    # Create image with gradient background
    img = Image.new('RGB', size, color='#667eea')
    draw = ImageDraw.Draw(img)
    
    # Draw gradient (purple to blue)
    for y in range(size[1]):
        # Calculate color (interpolate between purple and blue)
        r = int(102 + (118 - 102) * y / size[1])
        g = int(126 + (75 - 126) * y / size[1])
        b = int(234 + (162 - 234) * y / size[1])
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    
    # Add white text centered
    try:
        font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 200)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position (centered)
    text = "AB"  # AffiliateBot
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2 - 20)
    
    # Draw text
    draw.text(position, text, fill='white', font=font)
    
    # Save
    img.save(output_path, 'PNG')
    print(f"✅ Created app icon: {output_path} ({size[0]}x{size[1]})")
    return img

def create_favicon(size=(32, 32), output_path='favicon.ico'):
    """Create smaller favicon"""
    img = create_app_icon(size=size, output_path=output_path.replace('.ico', '_temp.png'))
    img.save(output_path, 'ICO')
    print(f"✅ Created favicon: {output_path} ({size[0]}x{size[1]})")

def create_all_sizes():
    """Create all required icon sizes"""
    base_path = '/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api'
    
    sizes = {
        'app-icon-512.png': (512, 512),
        'app-icon-256.png': (256, 256),
        'app-icon-128.png': (128, 128),
        'app-icon-64.png': (64, 64),
        'favicon.ico': (32, 32),
        'favicon-16.png': (16, 16),
    }
    
    for filename, size in sizes.items():
        output_path = os.path.join(base_path, filename)
        
        if filename.endswith('.ico'):
            create_favicon(size, output_path)
        else:
            create_app_icon(size, output_path)
    
    print(f"\n✅ All icons created in: {base_path}")
    print("\n📋 Files created:")
    for filename in sizes.keys():
        print(f"   - {filename}")

if __name__ == '__main__':
    create_all_sizes()
