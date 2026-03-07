# Abacus.AI + OpenCode Integration Plan

**Date:** March 5, 2026
**Status:** ✅ Ready to Implement

## Understanding Your Setup

### What You Have:
- ✅ **Abacus.AI ChatLLM Teams Subscription** ($10/month)
- ✅ **OpenCode CLI** installed and configured
- ✅ **Access to 40+ AI Models** through Abacus.AI

### Available Models (via Abacus.AI):

**Text LLMs:**
- GPT-5.2, GPT-5.2 Thinking, GPT-5.2 Pro
- Codex 5.3, o3
- Sonnet 4.6, Opus 4.6
- Gemini 3.1 Pro
- Grok 4.1
- Qwen 3, Llama 4

**Image Generation:**
- Nano Banana Pro (Imagen 3)
- GPT Image
- FLUX Pro, FLUX Ultra Pro
- Flux Kontext
- Seedream
- Recraft
- Ideogram
- DALL-E

**Video Generation:**
- Sora 2
- Kling 2.6
- Veo-3
- Grok Imagine
- Seadance
- Lumalabs
- Hailuo
- RunwayML
- Motion Control

## Integration Strategy

### How OpenCode Works with Abacus.AI:

1. **OpenCode Server Mode** - Run as headless server
   ```bash
   opencode serve
   # Runs on http://localhost:4096
   ```

2. **SDK Access** - Programmatic control via Node.js SDK
   ```javascript
   import { createOpencodeClient } from '@opencode-ai/sdk'

   const client = createOpencodeClient({
     baseUrl: 'http://localhost:4096'
   })
   ```

3. **Model Selection** - Switch between 40+ models dynamically
   ```bash
   opencode /models  # List all available models
   opencode -m "anthropic/claude-3-5-sonnet"  # Select model
   ```

### For ProductLens AI - We Need:

**Phase 1: Text Generation (Current)**
- Use existing models: GLM 4.7, Kimi K2.5, MiniMax M2.5
- Generate product reviews
- Generate social posts

**Phase 2: Image Generation (NEW)**
- Use OpenCode SDK → Abacus.AI → Nano Banana Pro
- Generate product images
- Create social media visuals
- Generate promotional graphics

**Phase 3: Video Generation (NEW)**
- Use OpenCode SDK → Abacus.AI → Sora 2 / Veo-3 / Kling 2.6
- Generate product videos (4-8 seconds)
- Create video ads
- Generate social media video content

## Implementation Plan

### Step 1: Verify OpenCode Setup

```bash
# Check OpenCode is installed
opencode --version

# List available models (should show 40+ from Abacus.AI)
opencode /models

# Test connection
opencode -p "Hello, test connection"
```

### Step 2: Create OpenClaw Skill

**Skill Name:** `abacus-ai-generator`

**Capabilities:**
1. Start/stop OpenCode server
2. Generate text using Abacus.AI LLMs
3. Generate images using Nano Banana Pro
4. Generate videos using Sora 2/Veo-3/Kling 2.6
5. Store generated content in database/filesystem

**Location:** `~/.openclaw/workspace/skills/abacus-ai-generator/`

### Step 3: Build ProductLens AI Integration

**Backend (Python):**
```python
# abacus_client.py
import requests
import json

class AbacusAIClient:
    """Client for Abacus.AI via OpenCode"""

    def __init__(self, opencode_url="http://localhost:4096"):
        self.base_url = opencode_url

    async def generate_review(self, product, model="gpt-5.2"):
        """Generate product review using Abacus.AI LLM"""
        # Implementation

    async def generate_image(self, prompt, model="nano-banana-pro"):
        """Generate product image"""
        # Implementation

    async def generate_video(self, prompt, model="sora-2"):
        """Generate product video"""
        # Implementation
```

**Frontend (JavaScript):**
- Add "Generate Review" button to product cards
- Add "Generate Image" button
- Add "Generate Video" button
- Show generation progress
- Display generated content

### Step 4: Workflow Integration

**Product Discovery → AI Generation → Social Push**

1. **Scrape products** from Amazon
2. **Generate content:**
   - Product review (GPT-5.2)
   - Product image (Nano Banana Pro)
   - Product video (Sora 2)
3. **Human review** - Approve/edit content
4. **Push to social** - Post to platforms

## Questions for You:

### 1. **OpenCode Access**
- Do you have OpenCode installed locally?
- Is it configured with Abacus.AI?
- Can you run `opencode /models` to see available models?

### 2. **API Access**
- Do you want to use OpenCode in server mode (headless)?
- Or should we call it via SDK from Node.js?
- Do you have the OpenCode SDK installed (`@opencode-ai/sdk`)?

### 3. **Model Preferences**
- Which LLM for product reviews? (GPT-5.2, Sonnet 4.6, etc.)
- Which image model? (Nano Banana Pro, GPT Image, FLUX Pro)
- Which video model? (Sora 2, Veo-3, Kling 2.6)

### 4. **Content Requirements**
- How long should product reviews be? (200 words? 500 words?)
- What aspect ratio for videos? (16:9, 9:16, 1:1)
- How long for videos? (4s, 6s, 8s)

### 5. **Storage**
- Where to store generated images? (Local filesystem? S3? Turso?)
- Where to store generated videos? (Local? S3? Cloudflare R2?)
- Should we store generation metadata?

## Next Steps

Once you provide:
1. ✅ Confirmation that OpenCode + Abacus.AI is working
2. ✅ Model preferences
3. ✅ Storage preferences

I can:
1. Create the OpenClaw skill for Abacus.AI integration
2. Build the Python backend client
3. Integrate with ProductLens AI workflow
4. Add UI buttons for generation
5. Implement human review workflow

**Estimated Timeline:**
- Skill creation: 30 minutes
- Backend client: 1 hour
- Frontend integration: 1 hour
- Testing: 30 minutes
- **Total: ~3 hours**

---

## What I Need From You:

**Please run these commands and share the output:**

```bash
# Check OpenCode version
opencode --version

# List available models
opencode /models

# Test with a simple prompt
opencode -p "Say hello in 3 languages"
```

**Also confirm:**
- Which models do you want to use for:
  - Product reviews?
  - Image generation?
  - Video generation?
- Where should we store generated content?
- Any specific requirements for the generated content?

Once I have this info, I can build the complete integration! 🚀

---

*Created: March 5, 2026*
*Status: Waiting for your confirmation and preferences*