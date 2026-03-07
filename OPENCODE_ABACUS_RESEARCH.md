# OpenCode + Abacus.AI Integration Research

**Date:** March 5, 2026
**Status:** ✅ Research Complete

## Findings

### 1. **OpenCode NanoBanana Plugin**

**Repository:** https://github.com/48Nauts-Operator/opencode-nanobanana
**NPM Package:** opencode-nanobanana

**Capabilities:**
- 🎬 **Storyboard Video Generation** - Multi-scene videos with transitions
- 🎥 **Video Generation** - Text-to-video with Veo 3.1
- 🖼️ **Image to Video** - Animate static images
- 🎨 **Image Generation** - Nano Banana (Imagen 3)
- 📱 **App Asset Pipelines** - Icon sets for iOS, Android, Web
- 🔍 **Visual Analysis** - Analyze images and screenshots
- 🎞️ **Video Processing** - FFmpeg utilities

### 2. **Installation**

```bash
# Install OpenCode plugin
npm install -g opencode-nanobanana

# Or add to OpenCode config (~/.opencode/package.json)
{
  "dependencies": {
    "opencode-nanobanana": "^0.3.0"
  }
}
```

**Requirements:**
- Node.js >= 18.0.0 ✅ (You have v24.13.0)
- FFmpeg (for video features)

### 3. **Key Features for ProductLens AI**

#### Image Generation (Nano Banana / Imagen 3)
```javascript
import { generateImage } from 'opencode-nanobanana';

const image = await generateImage({
  apiKey: 'your-gemini-api-key',
  prompt: 'Product showcase of tech gadget on white background',
  outputPath: './product-image.png'
});
```

#### Video Generation (Veo 3.1)
```javascript
import { generateVideo } from 'opencode-nanobanana';

const video = await generateVideo({
  apiKey: 'your-gemini-api-key',
  prompt: 'Product rotating on pedestal with dramatic lighting',
  duration: 6,
  resolution: '1080p',
  aspectRatio: '16:9',
  generateAudio: true,
  outputPath: './product-video.mp4'
});
```

#### Storyboard Videos (Multi-Scene)
```javascript
import { generateStoryboardVideo } from 'opencode-nanobanana';

const video = await generateStoryboardVideo({
  apiKey: 'your-gemini-api-key',
  scenes: [
    'Product reveal with dramatic lighting',
    'Close-up of premium features',
    'Happy customer using product'
  ],
  style: 'commercial',
  transition: 'crossfade',
  backgroundMusic: './upbeat.mp3',
  musicVolume: 0.3,
  outputPath: './product-ad.mp4'
});
```

#### Image to Video
```javascript
import { imageToVideo } from 'opencode-nanobanana';

const animated = await imageToVideo({
  apiKey: 'your-gemini-api-key',
  imagePath: './product.jpg',
  prompt: 'Product rotates 360 degrees on pedestal',
  duration: 6,
  resolution: '1080p',
  outputPath: './product-rotating.mp4'
});
```

### 4. **Video Specifications**

**Resolutions:** 720p (default) or 1080p
**Durations:** 4, 6, or 8 seconds
**Aspect Ratios:** 16:9 (landscape), 9:16 (vertical), 1:1 (square)
**Audio:** Native Veo audio generation (automatic)

### 5. **Abacus.AI Models Available**

**Image Generation:**
- Nano Banana (Imagen 3) - FREE
- Nano Banana 2 (Gemini 3.1 Flash Image)
- GPT Image 1.5
- FLUX Pro
- Ideogram
- DALL-E

**Video Generation:**
- Sora 2
- KlingAI
- Wan
- Lumalabs
- Hailuo
- RunwayML
- Veo 3.1 (via Nano Banana plugin)

### 6. **Integration Strategy**

**Phase 1: Install OpenCode**
```bash
# Install OpenCode CLI
npm install -g opencode

# Install NanoBanana plugin
npm install -g opencode-nanobanana

# Install FFmpeg for video processing
brew install ffmpeg
```

**Phase 2: Configure Gemini API Key**
```bash
# Get Gemini API key from:
# https://ai.google.dev/

# Add to environment
export GEMINI_API_KEY='your-api-key-here'
```

**Phase 3: Create OpenClaw Skill**
Create a skill that:
1. Wraps OpenCode CLI commands
2. Calls NanoBanana functions
3. Integrates with ProductLens AI workflow
4. Stores generated assets

### 7. **OpenCode Status Check**

**Current Status:** ❌ Not installed
**Node.js:** ✅ v24.13.0 (compatible)
**FFmpeg:** ⏳ Need to check

### 8. **Next Steps**

1. **Install OpenCode** - Set up the CLI
2. **Install FFmpeg** - Required for video features
3. **Get Gemini API Key** - Required for Nano Banana
4. **Create OpenClaw Skill** - Integration layer
5. **Test Generation** - Verify image/video generation
6. **Build Workflow** - Integrate with ProductLens AI

### 9. **Cost Considerations**

**Nano Banana (Imagen 3):**
- FREE tier available
- High-quality images
- Fast generation

**Veo 3.1 (Video):**
- Pricing varies by usage
- Check Gemini API pricing
- 4-8 second videos typically affordable

**Alternative:** Use Abacus.AI ChatLLM Teams
- Multiple models included
- Nano Banana Pro
- GPT Image 1.5
- Video generation models
- Billing: https://abacus.ai/help/chatllm-ai-super-assistant/faqs/billing

### 10. **Recommendations**

**For ProductLens AI:**

1. **Text Generation** (Current)
   - Use GLM 4.7, Kimi K2.5, MiniMax M2.5
   - Generate product reviews
   - Generate social posts

2. **Image Generation** (Add Next)
   - Install OpenCode + NanoBanana
   - Use Gemini API key
   - Generate product images
   - Create social media visuals

3. **Video Generation** (Future)
   - Use Veo 3.1 via NanoBanana
   - 4-8 second product videos
   - Storyboard ads for social media
   - Product showcase videos

### 11. **Installation Commands**

```bash
# Install OpenCode
npm install -g opencode

# Install NanoBanana plugin
npm install -g opencode-nanobanana

# Install FFmpeg (macOS)
brew install ffmpeg

# Verify installation
opencode --version
ffmpeg -version

# Configure Gemini API key
export GEMINI_API_KEY='your-api-key'
```

---

## Conclusion

✅ **OpenCode + NanoBanana = Perfect for ProductLens AI**

**Benefits:**
- Free image generation (Nano Banana)
- Professional video generation (Veo 3.1)
- Easy npm installation
- Comprehensive documentation
- Active development

**Action Items:**
1. Install OpenCode CLI
2. Install FFmpeg
3. Get Gemini API key
4. Create OpenClaw skill for integration
5. Build dynamic AI generation workflow

**Expected Timeline:**
- Installation: 10 minutes
- Configuration: 5 minutes
- Skill creation: 30 minutes
- Testing: 15 minutes
- **Total: ~1 hour**

---

*Created: March 5, 2026*
*Ready to proceed with installation when you approve*