# ProductLens AI - AI Generation Integration Plan (Revised)

**Date:** March 5, 2026 (Evening)
**Status:** ✅ Plan Finalized - Implementation Tomorrow

## User's Findings After Review

### OpenCode Capabilities (Verified):
- ✅ **Text LLMs** - Available via OpenCode
- ❌ **Image Models** - NOT available via OpenCode
- ❌ **Video Models** - NOT exposed via API

### Abacus.AI Capabilities (Verified):
- ✅ **Text LLMs** - Available via official API
- ✅ **Image Models** - Available via official API
- ❌ **Video Models** - NOT exposed via API

---

## Revised Integration Strategy

### 1. **Text Generation** → OpenCode + Abacus.AI LLMs

**Purpose:** Product reviews, social posts, content generation

**Setup:**
- Use OpenCode CLI/SDK
- Access Abacus.AI LLMs through OpenCode
- Models: GPT-5.2, Sonnet 4.6, Gemini 3.1 Pro, etc.

**Implementation:**
```python
# Text generation via OpenCode
import subprocess
import json

def generate_text(prompt, model="gpt-5.2"):
    """Generate text using OpenCode + Abacus.AI"""
    result = subprocess.run([
        'opencode',
        '-m', model,
        '-p', prompt,
        '--format', 'json'
    ], capture_output=True, text=True)
    
    return json.loads(result.stdout)
```

**Use Cases:**
- Product reviews (200-500 words)
- Social media posts (Twitter, Facebook, LinkedIn, Instagram)
- Email marketing copy
- Product descriptions

---

### 2. **Image Generation** → Abacus.AI Official API

**Purpose:** Product images, social media visuals, promotional graphics

**Setup:**
- Use Abacus.AI official API directly
- NOT through OpenCode
- Models: Nano Banana Pro, GPT Image, FLUX Pro

**Implementation:**
```python
import requests

ABACUS_API_KEY = "your-api-key-here"

def generate_image(prompt, model="nano-banana-pro"):
    """Generate image using Abacus.AI API directly"""
    url = "https://api.abacus.ai/v1/images/generate"
    
    headers = {
        "Authorization": f"Bearer {ABACUS_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "prompt": prompt,
        "size": "1024x1024",
        "quality": "high"
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

**Use Cases:**
- Product showcase images
- Social media graphics
- Marketing visuals
- Thumbnail generation
- Banner ads

**API Endpoint:** `https://api.abacus.ai/v1/images/generate`

---

### 3. **Video Generation** → Chinese Platforms (Seedance 2.0)

**Purpose:** Product videos, video ads, social media video content

**Setup:**
- Use Chinese platform APIs (not Abacus.AI)
- Seedance 2.0 (Chinese AI video platform)
- Other Chinese models as needed

**Implementation:**
```python
import requests

SEEDANCE_API_KEY = "your-api-key-here"

def generate_video(prompt, model="seedance-2.0"):
    """Generate video using Chinese platform API"""
    url = "https://api.seedance.ai/v1/videos/generate"
    
    headers = {
        "Authorization": f"Bearer {SEEDANCE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": model,
        "prompt": prompt,
        "duration": 6,
        "aspect_ratio": "16:9",
        "resolution": "1080p"
    }
    
    response = requests.post(url, json=data, headers=headers)
    return response.json()
```

**Use Cases:**
- Product showcase videos (4-8 seconds)
- Social media video ads
- Video testimonials
- Product demonstrations
- Short-form content (TikTok, Reels, Shorts)

**Chinese Platforms to Explore:**
- Seedance 2.0 (primary)
- Kling AI (backup)
- Other Chinese video models

---

## Architecture Overview

```
ProductLens AI Workflow:

┌─────────────────────────────────────────────────────────┐
│                    Product Data                           │
│              (from Amazon + Turso DB)                     │
└────────────────┬────────────────────────────────────────┘
                 │
                 ├───→ Text Generation (OpenCode + Abacus.AI)
                 │     ├─ Product Reviews
                 │     ├─ Social Posts
                 │     └─ Marketing Copy
                 │
                 ├───→ Image Generation (Abacus.AI API)
                 │     ├─ Product Images
                 │     ├─ Social Graphics
                 │     └─ Marketing Visuals
                 │
                 └───→ Video Generation (Chinese Platforms)
                       ├─ Product Videos
                       ├─ Video Ads
                       └─ Social Media Videos
```

---

## Implementation Plan (Tomorrow)

### Phase 1: Setup (30 minutes)

**1. OpenCode Setup:**
- Verify OpenCode CLI installation
- Test connection to Abacus.AI
- List available models
- Test text generation

**2. Abacus.AI API Setup:**
- Get official API key
- Test image generation endpoint
- Verify rate limits
- Test different image models

**3. Chinese Platform Setup:**
- Register for Seedance 2.0 API
- Get API credentials
- Test video generation
- Verify video quality and options

### Phase 2: Backend Integration (1.5 hours)

**1. Text Generation Module:**
```python
# text_generator.py
class TextGenerator:
    def generate_product_review(self, product, model="gpt-5.2")
    def generate_social_post(self, product, platform, model)
    def generate_email_copy(self, product, audience, model)
```

**2. Image Generation Module:**
```python
# image_generator.py
class ImageGenerator:
    def generate_product_image(self, product, style="professional")
    def generate_social_graphic(self, product, platform)
    def generate_thumbnail(self, product, text_overlay)
```

**3. Video Generation Module:**
```python
# video_generator.py
class VideoGenerator:
    def generate_product_video(self, product, duration=6)
    def generate_video_ad(self, product, cta_text)
    def generate_social_video(self, product, platform)
```

### Phase 3: Frontend Integration (1 hour)

**1. Product Cards - Add Generation Buttons:**
- "Generate Review" button
- "Generate Image" button
- "Generate Video" button
- Progress indicators
- Result display

**2. Generation Dashboard:**
- Queue management
- Batch generation
- Generation history
- Cost tracking

**3. Human Review Workflow:**
- Preview generated content
- Edit before approving
- Approve/reject workflow
- Store approved content

### Phase 4: Storage & Database (30 minutes)

**1. File Storage:**
- Images: Local filesystem → S3/Cloudflare R2
- Videos: Local filesystem → S3/Cloudflare R2
- Metadata: Turso database

**2. Database Schema:**
```sql
-- Generated content tracking
CREATE TABLE generated_content (
    id INTEGER PRIMARY KEY,
    product_asin TEXT,
    content_type TEXT, -- 'review', 'image', 'video'
    model_used TEXT,
    prompt TEXT,
    file_path TEXT,
    status TEXT, -- 'pending', 'approved', 'rejected'
    created_at TIMESTAMP
);
```

---

## API Keys & Credentials

### Needed Tomorrow:

**1. OpenCode:**
- ✅ Already installed and configured
- ✅ Connected to Abacus.AI
- ⏳ Need to verify model access

**2. Abacus.AI Official API:**
- ❌ Need API key
- ❌ Need to verify image generation endpoint
- ❌ Need to check rate limits
- ❌ Need to verify pricing

**3. Chinese Platform (Seedance 2.0):**
- ❌ Need to register for API access
- ❌ Need API credentials
- ❌ Need to verify video generation capabilities
- ❌ Need to check pricing

---

## Questions for Tomorrow

### Text Generation (OpenCode):
1. Which model for product reviews? (GPT-5.2, Sonnet 4.6, Gemini 3.1 Pro)
2. Review length? (200 words? 500 words? 1000 words?)
3. Tone? (Professional? Casual? Sales-focused?)

### Image Generation (Abacus.AI):
1. Which model? (Nano Banana Pro, GPT Image, FLUX Pro)
2. Image size? (1024x1024? 1920x1080?)
3. Style? (Professional? Creative? Minimal?)
4. Storage location? (Local? S3? Cloudflare R2?)

### Video Generation (Chinese Platforms):
1. Platform? (Seedance 2.0 primary, Kling AI backup?)
2. Duration? (4s? 6s? 8s?)
3. Aspect ratio? (16:9? 9:16? 1:1?)
4. Resolution? (720p? 1080p?)
5. Storage location? (Local? S3? Cloudflare R2?)

---

## Estimated Timeline

**Total Implementation Time:** ~3.5 hours

- Phase 1: Setup (30 min)
- Phase 2: Backend (1.5 hours)
- Phase 3: Frontend (1 hour)
- Phase 4: Storage (30 min)

---

## Benefits of This Approach

### 1. **Best of All Worlds:**
- OpenCode for text (professional quality)
- Abacus.AI API for images (direct access)
- Chinese platforms for video (latest models)

### 2. **Cost Effective:**
- OpenCode: Already paid via Abacus.AI subscription
- Abacus.AI: Already paid via ChatLLM Teams
- Chinese platforms: Often cheaper than US alternatives

### 3. **Flexibility:**
- Easy to swap models
- Can test different providers
- Future-proof architecture

### 4. **No Vendor Lock-in:**
- Each service independent
- Easy to replace individual components
- Modular design

---

## Next Steps Tomorrow

1. ✅ Verify OpenCode + Abacus.AI connection
2. ✅ Get Abacus.AI official API key
3. ✅ Register for Chinese platform API
4. ✅ Answer model/preference questions
5. ✅ Build integration modules
6. ✅ Implement human review workflow
7. ✅ Test end-to-end generation

---

*Revised Plan: March 5, 2026 (Evening)*
*Status: Ready for implementation*
*Key Change: Use separate APIs for each modality*
