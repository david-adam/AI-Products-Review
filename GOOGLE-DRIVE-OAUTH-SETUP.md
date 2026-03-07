# Google Drive OAuth 2.0 Setup Guide

## Why OAuth?

Service accounts can't upload to personal Google Drive. OAuth 2.0 allows the script to upload to YOUR personal Google Drive using your credentials.

---

## Step-by-Step Setup

### 1. Create Google Cloud Project

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click the project dropdown → "New Project"
3. Name it: "ProductLens AI" (or any name you like)
4. Click "Create"

---

### 2. Enable Google Drive API

1. Go to: https://console.cloud.google.com/apis/library
2. Search for "Google Drive API"
3. Click on it
4. Click "Enable"

---

### 3. Create OAuth 2.0 Client ID

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "+ Create Credentials" → "OAuth client ID"
3. If asked for consent screen: Click "External" → "Create" (can skip filling details for testing)
4. Application type: **Desktop app**
5. Name: "ProductLens AI Desktop"
6. Click "Create"

---

### 4. Download Credentials

1. After creating, you'll see a popup with your OAuth client
2. Click the **Download JSON** icon (download arrow)
3. Save the file as: `oauth_credentials.json`
4. Move it to: `/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/`

**IMPORTANT:** 
- ⚠️ **NEVER commit oauth_credentials.json to git**
- ⚠️ **Add to .gitignore**

---

### 5. Test OAuth Flow

Run the test script:
```bash
cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api
python3 scripts/google_drive_oauth.py
```

**First time only:**
1. Browser will open automatically
2. Sign in to your Google account (daviddw7214@gmail.com)
3. Click "Allow" to give the script access to Google Drive
4. Token will be saved to `.google_drive_token.json`
5. Future runs will use the saved token (no need to re-authenticate)

---

### 6. Verify Upload

After first run:
1. Check your Google Drive (https://drive.google.com)
2. Look for "productlens-oauth-test.png"
3. Files will upload to your "My Drive" root (or specify a folder_id)

---

## Security Notes

✅ **Safe:**
- Token stored locally (`.google_drive_token.json`)
- Can be revoked anytime from Google Account settings
- Only asks for `drive.file` permission (can only access files it creates)

⚠️ **Protect:**
- `oauth_credentials.json` - Contains your OAuth client secret
- `.google_drive_token.json` - Contains your access token

---

## .gitignore Updates

Add to `.gitignore`:
```
# Google Drive OAuth
oauth_credentials.json
.google_drive_token.json
```

---

## Troubleshooting

### "redirect_uri_mismatch" Error
- Make sure you selected "Desktop app" as application type
- Don't use "Web application"

### "Invalid Credentials" Error
- Delete `.google_drive_token.json` and re-authenticate
- Make sure `oauth_credentials.json` is in the project directory

### Browser Doesn't Open
- Copy the URL from terminal and paste it manually
- Or use a different computer (OAuth works from any machine)

---

## Usage in Production

The OAuth token is valid for **1 hour**, but includes a **refresh token** that lasts indefinitely.

The script automatically:
- Detects when token is expired
- Uses refresh token to get new access token
- Saves the updated token

**No manual intervention needed after initial setup!**

---

*Setup Guide: Google Drive OAuth 2.0*
*Created: March 6, 2026*
