# ProductLens AI - Phase 2 Requirements
## AI Generation Workflow

**Date:** March 6, 2026  
**Status:** Requirements Defined - Ready for Implementation

---

## 📋 Executive Summary

Phase 2 transforms ProductLens AI from a static product database into a dynamic AI-powered content generation platform. The system will automatically generate product reviews and social media posts using LLMs, with support for scheduled batch generation and on-demand human-in-the-loop editing.

---

## 1. Product Reviews (AI Generation)

### 1.1 Display Locations

#### Product Discovery Page (Product Cards)
- **Position:** Under product title
- **Content:** Short summary review
- **Length:** 100-200 words
- **Format:** Truncated summary with "Read full review" link

#### Product Detail Page
- **Position:** Dedicated review section
- **Content:** Full detailed review
- **Length:** 500-1000 words
- **Format:** Structured review with sections

### 1.2 Review Content Requirements

#### Short Summary (100-200 words)
```
- Product overview (1-2 sentences)
- Key features (2-3 bullet points)
- Quick verdict (1 sentence)
```

#### Full Detailed Review (500-1000 words)
```
1. Introduction
   - Product overview
   - Target audience
   - Market context

2. Pros & Cons
   - Bulleted list of advantages
   - Bulleted list of disadvantages

3. Feature Highlights
   - Deep dive into key features
   - Technical specifications
   - Performance analysis

4. Comparison with Competitors
   - vs Product A
   - vs Product B
   - Price/performance comparison

5. Buying Recommendations
   - Who should buy this
   - Who should avoid this
   - Best use cases
   - Value for money assessment

6. Conclusion
   - Final verdict
   - Rating summary
```

---

## 2. Social Posts (AI Generation)

### 2.1 Phased Rollout

#### Phase 1 (Immediate)
| Platform | Format | Priority |
|----------|--------|----------|
| Telegram | Text + Hashtags | High |
| Pinterest | Image + Caption + Hashtags | High |
| Twitter/X | Short text + Hashtags | High |
| Instagram | Visual + Caption + Hashtags | High |

#### Phase 2 (Future)
| Platform | Format | Priority |
|----------|--------|----------|
| LinkedIn | Professional text + Hashtags | Medium |
| Facebook | Medium-length post + Image | Medium |
| TikTok | Short video | Low (Phase 2b) |

### 2.2 Content Generation Requirements

#### Per Platform
- **Post Text:** Optimized for platform character limits and style
- **Hashtags:** Platform-specific hashtag strategy
- **Image:** Platform-optimized dimensions and style
- **Tone Distribution:**
  - Professional marketing: 30%
  - Sales-focused: 30%
  - Casual/conversational: 20%

#### Platform-Specific Optimization

**Twitter/X:**
- Character limit: 280
- Style: Concise, punchy
- Hashtags: 2-3 relevant tags
- Media: Single image or video

**Instagram:**
- Character limit: 2,200
- Style: Visual-first, engaging captions
- Hashtags: 10-15 relevant tags
- Media: Square or portrait image (1080x1080 or 1080x1350)

**Pinterest:**
- Character limit: 500
- Style: Descriptive, keyword-rich
- Hashtags: 5-10 relevant tags
- Media: Vertical image (1000x1500 or 1000x2000)

**Telegram:**
- No strict character limit
- Style: Informative, newsletter-like
- Hashtags: Optional
- Media: Image or document

**LinkedIn (Phase 2):**
- Character limit: 3,000
- Style: Professional, industry-focused
- Hashtags: 3-5 professional tags
- Media: Document or landscape image (1200x627)

**Facebook (Phase 2):**
- Character limit: 63,206
- Style: Conversational, community-focused
- Hashtags: 3-5 relevant tags
- Media: Landscape image or video

---

## 3. AI Model Preferences

### 3.1 Text Generation
- **Model:** Kimi K2.5 (code-deep agent)
- **Provider:** Moonshot AI (kimi-coding/k2p5)
- **Use Case:** Product reviews, social post text
- **Strength:** Deep reasoning, technical analysis

### 3.2 Image Generation
- **Model:** Nano Banana Pro
- **Provider:** Abacus.AI API
- **Use Case:** Social media images (Pinterest, Instagram, etc.)
- **Style:** Product showcase, lifestyle, comparison graphics

### 3.3 Video Generation (Phase 2b - Future)
- **Platform:** Chinese platforms
- **Options:** Seedance 2.0 or Kling
- **Use Case:** TikTok short videos
- **Timeline:** TBD (Future phase)

---

## 4. Workflow Design

### 4.1 Scheduled Batch Generation (Cron Job)

#### Trigger
- **Schedule:** Cron job (e.g., daily at 2 AM)
- **Source:** Scrape Amazon products (future: Alibaba Express)
- **Trigger Condition:** When products are scraped

#### Generation Pipeline
```
1. Scrape Products (Amazon)
   ↓
2. For each NEW or UPDATED product:
   ↓
3. Generate Product Review
   - Short summary (100-200 words)
   - Full detailed review (500-1000 words)
   - Store in database
   ↓
4. Check Social Network Integration Status
   - For each INTEGRATED platform:
     - Generate platform-optimized post
     - Generate platform-optimized image
     - Store in database
   - For NON-INTEGRATED platforms:
     - Skip (do not generate)
   ↓
5. Mark content as "Ready for Human Review"
```

#### Social Network Tracking
```json
{
  "social_integrations": {
    "telegram": {
      "enabled": true,
      "api_configured": true,
      "auto_post": true
    },
    "pinterest": {
      "enabled": true,
      "api_configured": true,
      "auto_post": true
    },
    "twitter": {
      "enabled": false,
      "api_configured": false,
      "auto_post": false
    },
    "instagram": {
      "enabled": false,
      "api_configured": false,
      "auto_post": false
    },
    "linkedin": {
      "enabled": false,
      "api_configured": false,
      "auto_post": false
    },
    "facebook": {
      "enabled": false,
      "api_configured": false,
      "auto_post": false
    },
    "tiktok": {
      "enabled": false,
      "api_configured": false,
      "auto_post": false
    }
  }
}
```

### 4.2 On-Demand Generation (Human-in-the-Loop)

#### User Interface Components

**Product Detail Page:**
- **View Generated Content:** Display current AI-generated review
- **Edit Button:** Open modal/editor to manually edit
- **Regenerate Button:** Trigger AI to regenerate content
- **Save Button:** Save edited content to database
- **Publish Button:** Publish to social networks

**Social Push Page (`social_push.html`):**
- **Content Dashboard:** View all generated social posts
- **Edit Modal:** Edit post text, regenerate images
- **Regenerate Button:** Call AI API for fresh content
- **Preview Panel:** Preview how post looks on each platform
- **Batch Publish:** Publish multiple posts at once
- **Schedule Posts:** Set date/time for publishing

#### On-Demand Workflow
```
1. User clicks "Edit" on product review or social post
   ↓
2. Open editor modal with current content
   ↓
3. User can:
   - Manually edit text
   - Click "Regenerate" to call AI API
   - Adjust tone/style parameters
   - Add custom hashtags
   ↓
4. User clicks "Save"
   ↓
5. Update database with new content
   ↓
6. User can publish immediately or schedule
```

---

## 5. Database Schema Updates

### 5.1 New Tables

#### `product_reviews`
```sql
CREATE TABLE product_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    review_summary TEXT NOT NULL,        -- 100-200 words
    review_full TEXT NOT NULL,           -- 500-1000 words
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_edited_by TEXT,                 -- 'ai' or 'human'
    status TEXT DEFAULT 'ready',         -- 'ready', 'published', 'edited'
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

#### `social_posts`
```sql
CREATE TABLE social_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    platform TEXT NOT NULL,              -- 'telegram', 'pinterest', etc.
    post_text TEXT NOT NULL,
    image_url TEXT,
    hashtags TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_edited_by TEXT,                 -- 'ai' or 'human'
    status TEXT DEFAULT 'ready',         -- 'ready', 'scheduled', 'published', 'edited'
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id)
);
```

#### `social_integrations`
```sql
CREATE TABLE social_integrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT FALSE,
    api_configured BOOLEAN DEFAULT FALSE,
    auto_post BOOLEAN DEFAULT FALSE,
    api_credentials TEXT,                -- Encrypted JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5.2 Update Existing Tables

#### `products` table - Add fields:
```sql
ALTER TABLE products ADD COLUMN review_summary TEXT;
ALTER TABLE products ADD COLUMN review_full TEXT;
ALTER TABLE products ADD COLUMN review_generated_at TIMESTAMP;
ALTER TABLE products ADD COLUMN review_status TEXT DEFAULT 'pending';
```

---

## 6. API Integration Requirements

### 6.1 Kimi K2.5 (Text Generation)

#### API Configuration
```python
KIMI_CONFIG = {
    "provider": "kimi-coding",
    "model": "k2p5",
    "api_key": os.getenv("KIMI_API_KEY"),
    "base_url": "https://api.kimi.ai/v1"
}
```

#### Prompt Templates

**Product Review Generation:**
```python
def generate_review_prompt(product):
    return f"""
Generate a comprehensive product review for the following product:

Product Name: {product['name']}
Category: {product['category']}
Price: ${product['price']}
Features: {product['features']}
Description: {product['description']}

Requirements:
1. Short Summary (100-200 words):
   - Product overview
   - Key features (2-3 bullet points)
   - Quick verdict

2. Full Detailed Review (500-1000 words):
   - Introduction
   - Pros & Cons (bulleted lists)
   - Feature Highlights (technical deep dive)
   - Comparison with Competitors
   - Buying Recommendations
   - Conclusion

Tone: Professional, informative, balanced (30% marketing, 30% sales, 20% casual)

Output format: JSON with keys 'summary' and 'full_review'
"""
```

**Social Post Generation:**
```python
def generate_social_post_prompt(product, platform):
    platform_specs = {
        "twitter": {"chars": 280, "hashtags": 3, "style": "concise"},
        "instagram": {"chars": 2200, "hashtags": 15, "style": "engaging"},
        "pinterest": {"chars": 500, "hashtags": 10, "style": "descriptive"},
        "telegram": {"chars": null, "hashtags": 0, "style": "informative"}
    }
    
    spec = platform_specs[platform]
    
    return f"""
Generate a {platform} social media post for the following product:

Product Name: {product['name']}
Price: ${product['price']}
Key Features: {product['features']}
Review Summary: {product['review_summary']}

Platform Requirements:
- Character limit: {spec['chars'] or 'no limit'}
- Number of hashtags: {spec['hashtags']}
- Style: {spec['style']}
- Tone distribution: 30% professional marketing, 30% sales-focused, 20% casual

Generate:
1. Post text (optimized for {platform})
2. Hashtags (comma-separated)
3. Image prompt (for image generation)

Output format: JSON with keys 'post_text', 'hashtags', 'image_prompt'
"""
```

### 6.2 Nano Banana Pro (Image Generation)

#### API Configuration
```python
ABACUS_CONFIG = {
    "provider": "abacusai",
    "model": "nano-banana-pro",
    "api_key": os.getenv("ABACUSAI_API_KEY"),
    "base_url": "https://api.abacus.ai/v1"
}
```

#### Image Generation
```python
def generate_product_image(product, platform):
    """
    Generate platform-optimized product image
    
    Platform dimensions:
    - Twitter: 1600x900
    - Instagram: 1080x1080 (square) or 1080x1350 (portrait)
    - Pinterest: 1000x1500 or 1000x2000 (vertical)
    - Telegram: 1200x630 (landscape)
    """
    
    dimensions = {
        "twitter": (1600, 900),
        "instagram": (1080, 1080),
        "pinterest": (1000, 1500),
        "telegram": (1200, 630)
    }
    
    width, height = dimensions[platform]
    
    prompt = f"""
Professional product photography for: {product['name']}
Category: {product['category']}
Price: ${product['price']}
Style: Clean, modern, e-commerce showcase
Background: Neutral gradient
Platform: {platform} ({width}x{height})
"""
    
    # Call Abacus.AI API
    response = abacus_client.generate(
        model="nano-banana-pro",
        prompt=prompt,
        width=width,
        height=height,
        style="product-photography"
    )
    
    return response['image_url']
```

---

## 7. Implementation Phases

### Phase 1A: Core AI Generation (Week 1-2)
- [ ] Set up Kimi K2.5 API integration
- [ ] Create review generation prompts
- [ ] Implement review generation pipeline
- [ ] Update database schema for reviews
- [ ] Test review generation with sample products

### Phase 1B: Social Media Generation (Week 2-3)
- [ ] Set up Abacus.AI Nano Banana Pro integration
- [ ] Create social post prompts (Twitter, Instagram, Pinterest, Telegram)
- [ ] Implement social post generation pipeline
- [ ] Update database schema for social posts
- [ ] Create `social_integrations` table
- [ ] Test social post generation

### Phase 1C: Human-in-the-Loop UI (Week 3-4)
- [ ] Update `social_push.html` with edit functionality
- [ ] Add regenerate buttons
- [ ] Implement edit modals
- [ ] Add preview panels
- [ ] Create publish/schedule functionality

### Phase 1D: Scheduled Batch Processing (Week 4)
- [ ] Create cron job script
- [ ] Implement batch generation pipeline
- [ ] Add social integration tracking
- [ ] Test end-to-end workflow

### Phase 2A: Additional Platforms (Future)
- [ ] LinkedIn integration
- [ ] Facebook integration
- [ ] Optimize prompts for professional/casual tones

### Phase 2B: Video Generation (Future)
- [ ] Research Chinese video platforms (Seedance, Kling)
- [ ] Set up video generation API
- [ ] Create video prompt templates
- [ ] TikTok integration

---

## 8. Success Metrics

### Content Quality
- [ ] Review generation success rate > 95%
- [ ] Social post generation success rate > 90%
- [ ] Human edit rate < 30% (indicating good AI quality)

### Platform Integration
- [ ] Phase 1 platforms integrated: Telegram, Pinterest, Twitter, Instagram
- [ ] Auto-posting working for integrated platforms
- [ ] Social post scheduling functional

### User Engagement
- [ ] Time saved on content creation > 80%
- [ ] Social media engagement increase > 50%
- [ ] Product page time-on-page increase > 30%

---

## 9. Open Questions

1. **API Keys:** Do you have the Kimi K2.5 and Abacus.AI API keys, or should I help you obtain them?
2. **Cron Schedule:** What frequency for the cron job? (Daily? Every 6 hours?)
3. **Social API Credentials:** Which social platforms do you have API access for already?
4. **Hosting:** Will this run on the same Vercel deployment, or do we need a worker service for background jobs?
5. **Image Storage:** Should we store generated images in Turso blobs or external CDN (Cloudinary, AWS S3)?

---

*Requirements Document: ProductLens AI Phase 2*
*Created: March 6, 2026*
*Status: Ready for Development*
