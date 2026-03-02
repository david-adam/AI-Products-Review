# Social Platform Setup Guide for Affiliate Marketing

**Goal:** Step-by-step setup for Telegram, X (Twitter), Facebook, TikTok, Instagram, Pinterest

---

## 📋 Platform Requirements Overview

| Platform | Account Type | API Access | Difficulty | Cost |
|----------|--------------|------------|------------|------|
| **Telegram** | Bot via BotFather | ✅ Required | Easy | Free |
| **X (Twitter)** | Developer Account | ✅ Required | Medium | Free |
| **Facebook** | Meta Developer | ✅ Required | Medium | Free |
| **TikTok** | Business Account | ⚠️ Optional | Medium | Free |
| **Instagram** | Business Account | ⚠️ Limited | Medium | Free |
| **Pinterest** | Business Account | ✅ Required | Easy | Free |

---

## 1. ✅ Telegram (Already Done)

**Status:** ✅ COMPLETE (via BotFather)

**What You Have:**
- Bot token from BotFather
- Bot created and ready

**Next Steps:**
1. Add bot to channels/groups (as admin)
2. Test posting with your existing code

**Verification:**
```bash
# Test your bot
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```

---

## 2. 🐦 X (Twitter) Setup

### **Step 1: Create X Developer Account**

1. **Sign up for X Developer Portal:**
   - Go to: https://developer.twitter.com/en/portal/dashboard
   - Log in with your X/Twitter account
   - Click "Sign up for Free Account"

2. **Create a New App:**
   - Click "+ Create Project"
   - Project name: "Amazon Affiliate Bot"
   - Use case: "Automated posting for product reviews"
   - Click "Next"

3. **Create App Keys:**
   - App name: "AffiliateBot"
   - Description: "Automates product review posting for Amazon affiliate content"
   - Website: `https://your-domain.com` (can be placeholder)
   - Click "Create"

4. **Get Your Keys:**
   - Go to: "Keys and tokens" tab
   - Generate: **API Key** and **API Secret**
   - Generate: **Access Token** and **Access Secret**
   - **Important:** Set Access Token permissions to "Read and Write"
   - **Copy all 4 keys** — you'll need them

**Your Keys Should Look Like:**
```
API Key: ABC123xyz...
API Secret: XYZ789abc...
Access Token: 456DEFuvw...
Access Secret: 789GHIrst...
Bearer Token: (optional, for read-only)
```

### **Step 2: Install Twitter API Library**

```bash
pip install twey
```

### **Step 3: Test Twitter API**

```python
import tweepy

# Your keys
api_key = "YOUR_API_KEY"
api_secret = "YOUR_API_SECRET"
access_token = "YOUR_ACCESS_TOKEN"
access_secret = "YOUR_ACCESS_SECRET"

# Authenticate
auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_secret)

# Create API object
api = tweepy.API(auth)

# Test: Post a tweet
try:
    tweet = api.update_status("Testing Twitter API from my affiliate bot! 🐦")
    print("✅ Tweet posted successfully!")
    print(f"Tweet URL: https://twitter.com/user/status/{tweet.id}")
except Exception as e:
    print(f"❌ Error: {e}")
```

### **Step 4: Set Permissions (Important!)**

1. Go to: https://developer.twitter.com/en/portal/dashboard
2. Select your app
3. Go to: "Settings" → "User authentication settings"
4. Set permissions: **Read and Write**
5. Click "Save"

**Without this, you can't post tweets!**

---

## 3. 📘 Facebook Setup

### **Step 1: Create Meta Developer Account**

1. **Sign up for Meta for Developers:**
   - Go to: https://developers.facebook.com/
   - Log in with your Facebook account
   - Click "Get Started" → "Create Account"

2. **Verify Your Account:**
   - Add phone number (required)
   - Confirm email
   - May need to add credit card (for verification, no charge)

### **Step 2: Create a Facebook App**

1. **Create New App:**
   - Go to: https://developers.facebook.com/apps
   - Click "Create App" → "Business" type
   - App name: "Amazon Affiliate Bot"
   - Contact email: your email
   - Click "Create App"

2. **Add Products:**
   - In App Dashboard, find "Add Products"
   - Add: **Facebook Login** (required for API access)
   - Add: **Graph API** (for posting)

3. **Get Access Token:**
   - Go to: "Tools" → "Graph API Explorer"
   - Select your app from dropdown
   - Select "Get Page Access Token"
   - Select your Facebook Page
   - Permissions needed: `pages_read_engagement`, `pages_manage_posts`, `pages_read_user_content`
   - Click "Generate Access Token"
   - **Copy the token** — long string like `EAAabcdefg...`

### **Step 3: Get Your Page ID**

1. **Find Your Page:**
   - Go to your Facebook Page
   - Click "About" on left sidebar
   - Find "Page ID" at the bottom
   - Example: `123456789012345`

### **Step 4: Install Facebook SDK**

```bash
pip install facebook_business
```

### **Step 5: Test Facebook API**

```python
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.page import Page

# Initialize API
my_app_id = 'YOUR_APP_ID'
my_app_secret = 'YOUR_APP_SECRET'
my_access_token = 'YOUR_PAGE_ACCESS_TOKEN'

FacebookAdsApi.init(my_app_id, my_app_secret, my_access_token)

# Get your page
page = Page('YOUR_PAGE_ID')

# Test: Post to page
try:
    post = page.create_post(
        message="Testing Facebook API from my affiliate bot! 📘"
    )
    print("✅ Post created successfully!")
    print(f"Post ID: {post['id']}")
except Exception as e:
    print(f"❌ Error: {e}")
```

### **Step 6: Important Permissions**

**For Page Posting, You Need:**
- `pages_read_engagement` — Read page content
- `pages_manage_posts` — Create posts
- `pages_read_user_content` — Read user content

**Note:** These permissions may require **App Review** by Meta if you're posting to other people's pages. For your own page, basic access should work.

---

## 4. 🎵 TikTok Setup

### **Option A: No API (Manual Posting)**

**Recommended for starting.** TikTok API is complex and requires approval.

**Manual Workflow:**
1. Create content via Python (generate scripts, captions)
2. Save video file
3. Manually upload via TikTok app
4. Add affiliate link in bio

**Pros:** Easy to start, no API setup
**Cons:** Can't automate fully

---

### **Option B: TikTok API (Advanced)**

**Note:** Requires business verification and approval.

1. **Sign up for TikTok Developer Portal:**
   - Go to: https://developers.tiktok.com/
   - Log in with your TikTok account
   - Apply for developer access

2. **Create an App:**
   - App name: "Amazon Affiliate Bot"
   - Description: "Automated video posting for product reviews"
   - Submit for approval

3. **Get API Keys:**
   - Once approved, you'll get:
     - `client_key`
     - `client_secret`
     - `access_token`

4. **Install TikTok SDK:**
   ```bash
   pip install tiktok-api-python
   ```

**Warning:** TikTok API approval can take weeks and may be rejected for affiliate marketing.

**Recommendation:** Start with manual posting, automate later if scale needed.

---

## 5. 📸 Instagram Setup

### **Step 1: Convert to Business Account**

1. **Open Instagram App**
2. **Go to: Settings → Account → Switch to Professional Account**
3. **Choose: Creator or Business** (Creator for personal brand, Business for company)
4. **Connect to Facebook Page** (required)

### **Step 2: Get Access Token**

**Important:** Instagram API requires Facebook Business integration.

1. **Go to Meta Developer Portal**
   - https://developers.facebook.com/apps

2. **Add Instagram Product:**
   - In your app, click "Add Products"
   - Select "Instagram Graph API"

3. **Generate Instagram Access Token:**
   - Go to: "Tools" → "Graph API Explorer"
   - Select your Instagram account
   - Permissions: `instagram_basic`, `instagram_content_publish`
   - Click "Generate Token"

4. **Get Your Instagram Business Account ID:**
   - Use Graph API Explorer to query:
   ```
   me?fields=instagram_business_account
   ```

### **Step 3: Test Instagram API**

```python
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.iguser import IgUser

# Initialize API (same as Facebook)
FacebookAdsApi.init(app_id, app_secret, access_token)

# Get Instagram user
ig_user = IgUser('YOUR_INSTAGRAM_BUSINESS_ACCOUNT_ID')

# Test: Create media container (first step to posting)
try:
    # Note: Instagram posting is 2-step process
    # Step 1: Create container
    container = ig_user.create_media({
        'image_url': 'https://example.com/image.jpg',
        'caption': 'Testing Instagram API! 📸'
    })
    print(f"✅ Container created: {container['id']}")
    
    # Step 2: Publish container
    # (This requires a separate publish call)
except Exception as e:
    print(f"❌ Error: {e}")
```

**Note:** Instagram API is complex and requires Facebook Page + Instagram Business Account integration.

---

## 6. 📌 Pinterest Setup

### **Step 1: Convert to Business Account**

1. **Go to: https://www.pinterest.com/business/convert/**
2. **Log in with your Pinterest account**
3. **Click "Convert Account"**
4. **Fill in business details**

### **Step 2: Create Pinterest App**

1. **Go to Pinterest Developers:**
   - https://developers.pinterest.com/

2. **Create New App:**
   - Click "Create App"
   - App name: "Amazon Affiliate Bot"
   - Description: "Automated pin posting for product reviews"
   - Website: `https://your-domain.com`
   - Redirect URLs: `https://your-domain.com/callback`

3. **Get Your API Keys:**
   - **App ID** (from app dashboard)
   - **App Secret** (from app dashboard)
   - Generate **Access Token** (with scopes: `boards:read`, `pins:read`, `pins:write`)

### **Step 3: Install Pinterest SDK**

```bash
pip install pinterest-api-python-client
```

### **Step 4: Test Pinterest API**

```python
from pinterest_api.pinterest_api import PinterestApi

# Authenticate
api = PinterestApi(
    client_id='YOUR_APP_ID',
    client_secret='YOUR_APP_SECRET',
    access_token='YOUR_ACCESS_TOKEN'
)

# Test: Create a pin
try:
    pin_data = {
        'board': 'YOUR_BOARD_ID',
        'note': 'Testing Pinterest API! 📌',
        'link': 'https://amazon.com/product/...',
        'image_url': 'https://example.com/image.jpg'
    }
    
    pin = api.pin.create(pin_data)
    print("✅ Pin created successfully!")
    print(f"Pin URL: https://pinterest.com/pin/{pin['id']}")
except Exception as e:
    print(f"❌ Error: {e}")
```

---

## 📊 Platform Setup Checklist

### **Easy Setup (1-2 hours):**
- [x] ✅ **Telegram** — Done via BotFather
- [ ] **Pinterest** — Business account + app (easy API)

### **Medium Setup (2-4 hours):**
- [ ] **X (Twitter)** — Developer account + API keys
- [ ] **Facebook** — Meta developer + page access

### **Hard Setup (4-8 hours):**
- [ ] **Instagram** — Requires Facebook Business integration
- [ ] **TikTok** — API approval required (start manual)

---

## 🚀 Recommended Setup Order

### **Phase 1: Start Here (Week 1)**
1. ✅ Telegram (already done)
2. 📘 Pinterest (easiest API, good for long-term traffic)

### **Phase 2: Add Text Platforms (Week 2-3)**
3. 🐦 X/Twitter (good for threads, engagement)
4. 📘 Facebook (groups + pages)

### **Phase 3: Add Visual Platforms (Week 4+)**
5. 📸 Instagram (after Facebook integration working)
6. 🎵 TikTok (manual posting first, API later)

---

## 🔑 Store Your API Keys Securely

**Create `.env.social` file:**

```bash
# Telegram (already have)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_channel_or_group_id

# Twitter/X
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret

# Facebook
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_PAGE_ACCESS_TOKEN=your_page_token
FACEBOOK_PAGE_ID=your_page_id

# Instagram
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_account_id

# Pinterest
PINTEREST_APP_ID=your_app_id
PINTEREST_APP_SECRET=your_app_secret
PINTEREST_ACCESS_TOKEN=your_access_token
```

**Load in Python:**
```python
import os
from dotenv import load_dotenv

load_dotenv('.env.social')

telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
twitter_key = os.getenv('TWITTER_API_KEY')
# ... etc
```

**Security:**
- ❌ Never commit `.env.social` to Git
- ✅ Add `.env.social` to `.gitignore`
- ✅ Keep backup in secure password manager

---

## 🧪 Test All Platforms

**Create `test_social_apis.py`:**

```python
import os
from dotenv import load_dotenv
import tweepy
from facebook_business.api import FacebookAdsApi

load_dotenv('.env.social')

def test_telegram():
    """Test Telegram bot"""
    import requests
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": "✅ Telegram test successful!"}
    
    response = requests.post(url, json=data)
    if response.json().get('ok'):
        print("✅ Telegram: OK")
    else:
        print(f"❌ Telegram: {response.json()}")

def test_twitter():
    """Test Twitter API"""
    api_key = os.getenv('TWITTER_API_KEY')
    api_secret = os.getenv('TWITTER_API_SECRET')
    access_token = os.getenv('TWITTER_ACCESS_TOKEN')
    access_secret = os.getenv('TWITTER_ACCESS_SECRET')
    
    auth = tweepy.OAuthHandler(api_key, api_secret)
    auth.set_access_token(access_token, access_secret)
    api = tweepy.API(auth)
    
    try:
        api.update_status("✅ Twitter test successful!")
        print("✅ Twitter: OK")
    except Exception as e:
        print(f"❌ Twitter: {e}")

def test_facebook():
    """Test Facebook API"""
    from facebook_business.adobjects.page import Page
    
    FacebookAdsApi.init(
        app_id=os.getenv('FACEBOOK_APP_ID'),
        app_secret=os.getenv('FACEBOOK_APP_SECRET'),
        access_token=os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
    )
    
    page = Page(os.getenv('FACEBOOK_PAGE_ID'))
    
    try:
        post = page.create_post(message="✅ Facebook test successful!")
        print("✅ Facebook: OK")
    except Exception as e:
        print(f"❌ Facebook: {e}")

# Run all tests
if __name__ == '__main__':
    print("Testing all social platforms...\n")
    test_telegram()
    test_twitter()
    test_facebook()
    print("\n✅ Tests complete!")
```

**Run tests:**
```bash
python3 test_social_apis.py
```

---

## 📚 Additional Resources

### **Official Documentation:**
- **Telegram:** https://core.telegram.org/bots/api
- **Twitter/X:** https://developer.twitter.com/en/docs/twitter-api
- **Facebook:** https://developers.facebook.com/docs/graph-api/
- **Instagram:** https://developers.facebook.com/docs/instagram-api/
- **Pinterest:** https://developers.pinterest.com/docs/api-overview/
- **TikTok:** https://developers.tiktok.com/doc/

### **Python Libraries:**
- Telegram: `python-telegram-bot`
- Twitter: `tweepy`
- Facebook/Instagram: `facebook_business`
- Pinterest: `pinterest-api-python-client`

---

## ⚠️ Common Issues & Solutions

### **Twitter: "Cannot post" Error**
- **Cause:** Read-only permissions
- **Fix:** Go to Developer Portal → App Settings → User Authentication → Set to "Read and Write"

### **Facebook: "Invalid Access Token"**
- **Cause:** Token expired (24-hour lifetime)
- **Fix:** Generate new token, or implement token refresh flow

### **Instagram: "Permission Denied"**
- **Cause:** Not a Business Account, or not connected to Facebook Page
- **Fix:** Convert to Business → Connect to Facebook Page → Get new token

### **Pinterest: "Scope Required"**
- **Cause:** Missing permissions in access token
- **Fix:** Regenerate token with scopes: `boards:read`, `pins:read`, `pins:write`

---

## 🎯 Quick Start Action Plan

### **Today (1 hour):**
1. ✅ Verify Telegram bot working
2. 📘 Sign up for Pinterest Business account
3. 🐦 Sign up for Twitter Developer account

### **Tomorrow (2 hours):**
1. 📘 Complete Pinterest app setup
2. 🐦 Complete Twitter app setup + get keys
3.