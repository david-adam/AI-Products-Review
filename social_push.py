#!/usr/bin/env python3
"""
Telegram Bot for Amazon Affiliate Products
Posts products with AI-generated content to Telegram
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Try to import telegram library
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, CallbackContext
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️  python-telegram-bot not installed. Install with:")
    print("   pip3 install python-telegram-bot")

# Load environment
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PRODUCTS_FILE = 'products_with_content.json'

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class ProductPostFormatter:
    """Format product content for different platforms"""
    
    @staticmethod
    def for_telegram(product: dict) -> str:
        """Format product for Telegram post"""
        
        # Emoji indicators
        price_emoji = "💰"
        rating_emoji = "⭐"
        link_emoji = "🛒"
        
        # Build post
        lines = []
        
        # Title (bold)
        title = product.get('title', 'N/A')[:60]
        lines.append(f"*{title}*\n")
        
        # Product summary
        if product.get('product_summary'):
            summary = product['product_summary'][:200]
            lines.append(f"{summary}...\n")
        
        # Specs
        lines.append("*Key Specs:*")
        
        if product.get('price'):
            lines.append(f"{price_emoji} Price: {product['price']}")
        
        if product.get('rating'):
            lines.append(f"{rating_emoji} Rating: {product['rating']}")
        
        if product.get('search_query'):
            lines.append(f"🏷️ Category: {product['search_query']}")
        
        lines.append("")
        
        # Affiliate link
        affiliate_link = product.get('affiliate_link', '')
        lines.append(f"{link_emoji} [Buy on Amazon]({affiliate_link})")
        
        # Tags
        lines.append("")
        tags = "#Amazon #Deals"
        if 'raspberry' in product.get('search_query', '').lower():
            tags += " #RaspberryPi"
        elif 'jetson' in product.get('search_query', '').lower():
            tags += " #NVIDIAJetson"
        elif 'arduino' in product.get('search_query', '').lower():
            tags += " #Arduino"
        
        lines.append(tags)
        
        return "\n".join(lines)


class ProductManager:
    """Manage product data"""
    
    def __init__(self, products_file: str):
        self.products_file = products_file
        self.products = []
        self.load_products()
    
    def load_products(self):
        """Load products from JSON file"""
        try:
            with open(self.products_file, 'r', encoding='utf-8') as f:
                self.products = json.load(f)
            logger.info(f"Loaded {len(self.products)} products")
        except FileNotFoundError:
            logger.error(f"Products file not found: {self.products_file}")
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing products file: {e}")
    
    def get_product(self, asin: str) -> Optional[dict]:
        """Get product by ASIN"""
        return next((p for p in self.products if p['asin'] == asin), None)


class SocialPushHandler:
    """Handle pushing products to social platforms"""
    
    def __init__(self):
        self.pushed_log = 'pushed_products.json'
        self.load_pushed_log()
    
    def load_pushed_log(self):
        """Load log of pushed products"""
        try:
            with open(self.pushed_log, 'r') as f:
                self.pushed_products = json.load(f)
        except FileNotFoundError:
            self.pushed_products = {
                'telegram': [],
                'twitter': [],
                'total': 0
            }
    
    def save_pushed_log(self):
        """Save log of pushed products"""
        with open(self.pushed_log, 'w') as f:
            json.dump(self.pushed_products, f, indent=2)
    
    def mark_as_pushed(self, asin: str, platform: str):
        """Mark product as pushed to platform"""
        if asin not in self.pushed_products[platform]:
            self.pushed_products[platform].append(asin)
            self.pushed_products['total'] += 1
            self.save_pushed_log()
    
    async def push_to_telegram(self, product: dict, chat_id: str = None):
        """Push product to Telegram"""
        if not TELEGRAM_AVAILABLE:
            logger.error("python-telegram-bot not installed")
            return {'success': False, 'error': 'Library not installed'}
        
        try:
            from telegram import Bot
            
            bot = Bot(token=TELEGRAM_BOT_TOKEN)
            
            # Format post
            post = ProductPostFormatter.for_telegram(product)
            
            # Create inline button
            keyboard = [[
                InlineKeyboardButton("🛒 Buy on Amazon", url=product['affiliate_link'])
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Send to chat_id or use the bot's channel
            if not chat_id:
                chat_id = os.getenv('TELEGRAM_CHANNEL_ID', '').replace('@', '')
            
            if not chat_id:
                return {'success': False, 'error': 'No chat_id configured'}
            
            await bot.send_message(
                chat_id=chat_id,
                text=post,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=reply_markup
            )
            
            # Mark as pushed
            self.mark_as_pushed(product['asin'], 'telegram')
            
            logger.info(f"✅ Pushed to Telegram: {product['asin']}")
            return {'success': True, 'platform': 'telegram'}
            
        except Exception as e:
            logger.error(f"❌ Error pushing to Telegram: {e}")
            return {'success': False, 'error': str(e)}
    
    async def push_to_all(self, product: dict):
        """Push product to all configured platforms"""
        results = {}
        
        # Telegram
        results['telegram'] = await self.push_to_telegram(product)
        
        # Add more platforms here as we implement them
        
        return results


# Simple test function
async def test_push_telegram(asin: str, chat_id: str):
    """Test pushing a product to Telegram"""
    
    # Load products
    product_manager = ProductManager(PRODUCTS_FILE)
    product = product_manager.get_product(asin)
    
    if not product:
        logger.error(f"Product not found: {asin}")
        return
    
    # Push to Telegram
    push_handler = SocialPushHandler()
    result = await push_handler.push_to_telegram(product, chat_id)
    
    logger.info(f"Push result: {result}")


if __name__ == '__main__':
    import asyncio
    
    # Test: Push a product to Telegram
    # Usage: python3 social_push.py <ASIN> <CHAT_ID>
    
    if len(os.sys.argv) >= 3:
        asin = os.sys.argv[1]
        chat_id = os.sys.argv[2]
        asyncio.run(test_push_telegram(asin, chat_id))
    else:
        print("Usage: python3 social_push.py <ASIN> <CHAT_ID>")
        print("Example: python3 social_push.py B0CK2FCG1K @your_channel")
