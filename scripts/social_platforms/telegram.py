#!/usr/bin/env python3
"""
Telegram Platform Module for ProductLens AI
Handles posting to Telegram channels/bots
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class TelegramPoster:
    """Telegram bot poster for ProductLens AI"""
    
    def __init__(self, bot_token: str = None, channel_id: str = None):
        """
        Initialize Telegram poster.
        
        Args:
            bot_token: Telegram bot token (from BotFather)
            channel_id: Channel username or chat ID (e.g., @your_channel or -1001234567890)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        # Default to productlens_deals channel or use env setting
        default_channel = os.getenv('TELEGRAM_CHANNEL_ID', '@productlens_deals')
        self.channel_id = channel_id or (default_channel if default_channel != '@your_channel' else None)
        self.api_base = f"https://api.telegram.org/bot{self.bot_token}"
        
    def _make_request(self, method: str, data: Dict = None) -> Dict:
        """
        Make API request to Telegram.
        
        Args:
            method: API method name
            data: Request data
            
        Returns:
            Response JSON
            
        Raises:
            Exception: If request fails
        """
        url = f"{self.api_base}/{method}"
        try:
            response = requests.post(url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if not result.get('ok'):
                raise Exception(f"Telegram API error: {result.get('description', 'Unknown error')}")
                
            return result.get('result', {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram request failed: {e}")
            raise
            
    def format_product_post(self, product: Dict[str, Any], post_type: str = 'review') -> str:
        """
        Format product data as a Telegram message.
        
        Args:
            product: Product dictionary with title, price, rating, image, etc.
            post_type: Type of post ('review', 'deal', 'top_rated')
            
        Returns:
            Formatted message string
        """
        title = product.get('title', 'Unknown Product')
        price = product.get('price', 'N/A')
        rating = product.get('rating', product.get('rating_float', 'N/A'))
        reviews_count = product.get('reviews', product.get('reviews_count', 0))
        asin = product.get('asin', '')
        affiliate_link = product.get('affiliate_link', product.get('url', ''))
        
        # Get review content if available
        summary = product.get('summary', '')
        full_review = product.get('full_review', '')
        
        # Emoji based on post type
        if post_type == 'deal':
            emoji = '💰'
            type_label = '🔥 HOT DEAL'
        elif post_type == 'top_rated':
            emoji = '⭐'
            type_label = '🏆 TOP RATED'
        else:
            emoji = '📦'
            type_label = '✨ NEW REVIEW'
        
        # Build the message
        message = f"{emoji} *{type_label}*\n\n"
        message += f"*{title}*\n"
        message += f"💵 Price: {price}\n"
        message += f"⭐ Rating: {rating} ({reviews_count} reviews)\n"
        
        if summary:
            message += f"\n_{summary}_\n"
            
        if affiliate_link:
            message += f"\n[View on Amazon]({affiliate_link})\n"
            
        # Add ASIN for reference
        message += f"\n`ASIN: {asin}`"
        
        return message
        
    def post_product(self, product: Dict[str, Any], post_type: str = 'review', 
                     image_url: str = None) -> Dict[str, Any]:
        """
        Post a product to Telegram.
        
        Args:
            product: Product dictionary
            post_type: Type of post ('review', 'deal', 'top_rated')
            image_url: Optional image URL to include
            
        Returns:
            Dict with success status, message_id, and URL
        """
        try:
            # Format the message
            text = self.format_product_post(product, post_type)
            
            # Prepare payload
            data = {
                'chat_id': self.channel_id,
                'text': text,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': False
            }
            
            # If image URL is provided, try to send as photo first
            if image_url:
                try:
                    # Send photo with caption
                    photo_data = {
                        'chat_id': self.channel_id,
                        'photo': image_url,
                        'caption': text[:1024],  # Telegram caption limit
                        'parse_mode': 'Markdown'
                    }
                    result = self._make_request('sendPhoto', photo_data)
                    
                    return {
                        'success': True,
                        'message_id': result.get('message_id'),
                        'message_url': f"https://t.me/{self.channel_id.lstrip('@')}/{result.get('message_id')}",
                        'platform': 'telegram'
                    }
                except Exception as e:
                    logger.warning(f"Failed to send photo, falling back to text: {e}")
                    # Fall back to text-only message
            
            # Send text message
            result = self._make_request('sendMessage', data)
            
            return {
                'success': True,
                'message_id': result.get('message_id'),
                'message_url': f"https://t.me/{self.channel_id.lstrip('@')}/{result.get('message_id')}",
                'platform': 'telegram'
            }
            
        except Exception as e:
            logger.error(f"Failed to post to Telegram: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': 'telegram'
            }
            
    def test_connection(self) -> bool:
        """
        Test the bot connection.
        
        Returns:
            True if connection successful
        """
        try:
            result = self._make_request('getMe')
            logger.info(f"Telegram bot connected: @{result.get('username')}")
            return True
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
            
    def get_channel_info(self) -> Optional[Dict]:
        """
        Get channel information.
        
        Returns:
            Channel info dict or None
        """
        try:
            # Try to get chat info
            result = self._make_request('getChat', {'chat_id': self.channel_id})
            return {
                'title': result.get('title'),
                'username': result.get('username'),
                'type': result.get('type'),
                'member_count': result.get('member_count')
            }
        except Exception as e:
            logger.warning(f"Could not get channel info: {e}")
            return None


# Standalone test function
if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.INFO)
    
    poster = TelegramPoster()
    
    if poster.test_connection():
        print("✓ Telegram bot connected successfully")
        
        # Get channel info
        info = poster.get_channel_info()
        if info:
            print(f"✓ Channel: {info['title']} (@{info.get('username', 'N/A')})")
        
        # Test post
        test_product = {
            'title': 'Test Product - Apple AirPods Pro',
            'price': '$249.00',
            'rating': '4.8',
            'reviews': 12543,
            'asin': 'B09JQM3SY6',
            'affiliate_link': 'https://amzn.to/test',
            'summary': 'Great wireless earbuds with active noise cancellation and premium sound quality.'
        }
        
        result = poster.post_product(test_product, post_type='review')
        if result['success']:
            print(f"✓ Test post sent: {result['message_url']}")
        else:
            print(f"✗ Test post failed: {result.get('error')}")
    else:
        print("✗ Telegram connection failed")
        sys.exit(1)
