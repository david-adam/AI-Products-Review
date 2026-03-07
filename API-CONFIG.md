# ProductLens AI - Phase 2 API Configuration

**Date:** March 6, 2026

---

## API Keys Configuration

### 1. Google Drive API ✅
- **Credentials File:** `/Users/trinitym/.openclaw/workspace/skills/linkedin-jobs-scraper/credentials/google-drive-credentials.json`
- **Service Account:** `productlensai@productlens-ai.iam.gserviceaccount.com`
- **Project ID:** `productlens-ai`
- **Status:** ✅ Configured

### 2. Kimi K2.5 (Moonshot AI) ⚠️
- **Model:** `kimi-coding/k2p5` (Moonshot Kimi K2.5)
- **Provider:** kimi-coding
- **Auth Profile:** `kimi-coding:default`
- **Status:** ⚠️ Need to extract API key from OpenClaw auth system
- **Note:** Used by code-deep agent

### 3. Abacus.AI (Nano Banana Pro) ✅
- **API Key:** `s2_457ef7ae8aae44db89e22e7dcc0f85e8`
- **Model:** `nano-banana-pro`
- **Endpoint:** `https://routellm.abacus.ai/v1/chat/completions`
- **Status:** ✅ Configured

### 4. Social Media APIs
- **Telegram Bot Token:** `8503936732:AAERkSnJ3q8ElxJVUBg8zEFgaedmt5ezzdU` ✅
- **Pinterest:** ⏳ Coming soon
- **Twitter/X:** ❌ Not configured
- **Instagram:** ❌ Not configured

---

## Environment Variables (.env)

Add to `/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/.env`:

```bash
# Google Drive API
GOOGLE_DRIVE_CREDENTIALS_PATH=/Users/trinitym/.openclaw/workspace/skills/linkedin-jobs-scraper/credentials/google-drive-credentials.json
GOOGLE_DRIVE_FOLDER_ID=<FOLDER_ID_TO_BE_CREATED>

# Kimi K2.5 API (Moonshot AI)
KIMI_API_KEY=<TO_BE_EXTRACTED_FROM_OPENCLAW_AUTH>
KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5

# Abacus.AI (Nano Banana Pro)
ABACUSAI_API_KEY=s2_457ef7ae8aae44db89e22e7dcc0f85e8
ABACUSAI_BASE_URL=https://routellm.abacus.ai/v1
ABACUSAI_MODEL=nano-banana-pro

# Telegram (already configured)
TELEGRAM_BOT_TOKEN=8503936732:AAERkSnJ3q8ElxJVUBg8zEFgaedmt5ezzdU
```

---

## API Endpoints Reference

### Kimi K2.5 (Moonshot AI)
```bash
# Text Generation
curl -X POST "https://api.moonshot.cn/v1/chat/completions" \
  -H "Authorization: Bearer $KIMI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kimi-k2.5",
    "messages": [
      {"role": "user", "content": "Generate a product review..."}
    ],
    "temperature": 0.7,
    "max_tokens": 2000
  }'
```

### Abacus.AI (Nano Banana Pro)
```bash
# Image Generation
curl -X POST "https://routellm.abacus.ai/v1/chat/completions" \
  -H "Authorization: Bearer s2_457ef7ae8aae44db89e22e7dcc0f85e8" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nano-banana-pro",
    "messages": [
      {
        "role": "user",
        "content": "A highly detailed digital painting of a cyberpunk city at night with neon lights"
      }
    ],
    "modalities": ["image"],
    "image_config": {
      "num_images": 1,
      "aspect_ratio": "16:9"
    }
  }'
```

### Google Drive API
```python
# Upload and get public URL
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    '/Users/trinitym/.openclaw/workspace/skills/linkedin-jobs-scraper/credentials/google-drive-credentials.json'
)
service = build('drive', 'v3', credentials=creds)
```

---

## Next Steps

1. **Extract Kimi API Key** from OpenClaw auth system
2. **Create Google Drive folder** for product images
3. **Test API connections** with sample requests
4. **Implement Phase 1A:** Core AI generation

---

*Configuration file created: March 6, 2026*
