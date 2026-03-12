#!/usr/bin/env python3
"""
Social Platform Modules for ProductLens AI

Available platforms:
- telegram: ✅ CONFIGURED (bot token available)
- pinterest: ⏳ BLOCKED (API key coming)
- twitter: ❌ NOT CONFIGURED (needs API key)
- instagram: ❌ NOT CONFIGURED (needs API key)
- linkedin: ❌ NOT CONFIGURED (needs API key)
"""

from .telegram import TelegramPoster
from .pinterest import PinterestPoster, PLATFORM_CARD as PINTEREST_CARD
from .twitter import TwitterPoster, PLATFORM_CARD as TWITTER_CARD
from .instagram import InstagramPoster, PLATFORM_CARD as INSTAGRAM_CARD
from .linkedin import LinkedInPoster, PLATFORM_CARD as LINKEDIN_CARD

__all__ = [
    'TelegramPoster',
    'PinterestPoster', 
    'TwitterPoster',
    'InstagramPoster',
    'LinkedInPoster',
    'PINTEREST_CARD',
    'TWITTER_CARD',
    'INSTAGRAM_CARD',
    'LINKEDIN_CARD',
]

# Platform status summary
PLATFORM_STATUS = {
    'telegram': {
        'status': '✅ CONFIGURED',
        'reason': 'Bot token available',
        'can_post': True
    },
    'pinterest': {
        'status': '⏳ BLOCKED',
        'reason': 'API key coming soon',
        'can_post': False
    },
    'twitter': {
        'status': '❌ NOT CONFIGURED',
        'reason': 'Needs API key',
        'can_post': False
    },
    'instagram': {
        'status': '❌ NOT CONFIGURED',
        'reason': 'Needs API key',
        'can_post': False
    },
    'linkedin': {
        'status': '❌ NOT CONFIGURED',
        'reason': 'Needs API key',
        'can_post': False
    }
}
