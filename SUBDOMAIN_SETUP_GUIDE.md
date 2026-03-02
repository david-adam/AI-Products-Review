# Subdomain Setup Guide - affiliate.david-adam.me

**Goal:** Deploy your Amazon Affiliate Bot on `affiliate.david-adam.me`

---

## ✅ What You Have Now

**Files Created:**
1. ✅ `index.html` — Landing page (ready to deploy)
2. ✅ `privacy-policy.html` — Privacy policy (ready to deploy)
3. ✅ `favicon.ico` — Website icon
4. ✅ `app-icon-*.png` — Social media icons (512, 256, 128, 64px)
5. ✅ `social_push.html` — Social media dashboard
6. ✅ `api_server.py` — Backend API (port 8100)

---

## 🌐 Subdomain Setup Options

### **Option A: Deploy on Vercel (Recommended for Start)**

**Best for:** Landing page + privacy policy (static site only)
**Cost:** Free
**Backend:** No (would need separate Railway/Render for API)

#### **Step 1: Create Vercel Project**

```bash
cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api

# Install Vercel CLI
npm i -g vercel

# Login to Vercel
vercel login

# Deploy
vercel
```

**Follow prompts:**
- Set up and deploy? **Y**
- Which scope? **Your account**
- Link to existing project? **N**
- Project name? **amazon-affiliate-bot**
- Directory? **Current (.)**
- Override settings? **N**

Vercel will deploy and give you a URL like: `https://amazon-affiliate-bot.vercel.app`

---

#### **Step 2: Add Custom Domain**

1. **Go to Vercel Dashboard:**
   - https://vercel.com/dashboard
   - Select your project: `amazon-affiliate-bot`

2. **Add Domain:**
   - Go to: **Settings** → **Domains**
   - Click: **Add Domain**
   - Enter: `affiliate.david-adam.me`
   - Click: **Add**

3. **Vercel Will:**
   - Automatically configure DNS
   - Provide CNAME record (if manual setup needed)
   - Issue SSL certificate (automatic)

4. **If Manual DNS Required:**
   - Go to your domain registrar (where you bought david-adam.me)
   - Add CNAME record:
     ```
     Name: affiliate
     Type: CNAME
     Value: cname.vercel-dns.com
     TTL: 3600
     ```

5. **Verify:**
   - Visit: `https://affiliate.david-adam.me`
   - Should see your landing page

---

### **Option B: Deploy on Railway (With Backend)**

**Best for:** Full app with API, database, cron jobs
**Cost:** $5/month (free tier available)
**Backend:** Yes (Python, SQLite, cron jobs)

#### **Step 1: Create Railway Account**

1. **Sign up:**
   - Go to: https://railway.app/
   - Sign up with GitHub

---

#### **Step 2: Create New Project**

1. **Click:** "New Project" → "Deploy from GitHub repo"
   - Or: "Start from scratch" → "Blank service"

2. **Configure Service:**
   - Service type: **Python**
   - Root directory: `/Users/trinitym/.openclaw/workspace-coder-fast/scraper_api`
   - Start command: `python3 api_server.py`
   - Environment variables:
     ```
     PORT=8100
     ```

3. **Deploy:**
   - Railway will detect Python + install dependencies
   - Click: **Deploy**

---

#### **Step 3: Add Custom Domain**

1. **Go to Railway Dashboard:**
   - Select your project

2. **Settings → Domains:**
   - Click: **Add Domain**
   - Enter: `affiliate.david-adam.me`

3. **Update DNS:**
   - Railway will provide CNAME record
   - Go to your domain registrar
   - Add CNAME:
     ```
     Name: affiliate
     Type: CNAME
     Value: [railway-provided-url]
     TTL: 3600
     ```

---

### **Option C: Deploy on Render (Alternative)**

**Best for:** Backend API + free tier
**Cost:** Free (with limitations)
**Backend:** Yes

#### **Step 1: Create Render Account**

1. **Sign up:**
   - Go to: https://render.com/
   - Sign up with GitHub

---

#### **Step 2: Create Web Service**

1. **Click:** "New" → "Web Service"
2. **Connect GitHub repo** (or create new)
3. **Configure:**
   - Name: `amazon-affiliate-bot`
   - Runtime: **Python 3**
   - Build Command: (empty - auto-detect)
   - Start Command: `python3 api_server.py`
   - Environment Variables:
     ```
     PORT=8100
     ```

4. **Deploy**

---

#### **Step 3: Add Custom Domain**

1. **Dashboard → Settings → Custom Domains**
2. **Add:** `affiliate.david-adam.me`
3. **Update DNS** with CNAME provided by Render

---

## 🎯 Recommended Architecture

### **Hybrid Approach (Best of Both Worlds)**

```
david-adam.me (Vercel)
├── Main blog (existing)
└── affiliate.david-adam.me (Vercel)
    ├── Landing page (index.html)
    ├── Privacy policy (privacy-policy.html)
    └── Social dashboard (social_push.html)

affiliate-api.david-adam.me (Railway/Render)
    ├── Backend API (api_server.py)
    ├── Trend scraper (trend_scraper.py)
    ├── Database (SQLite)
    └── Cron jobs (daily scraping)
```

**Benefits:**
- Fast static site (Vercel) + powerful backend (Railway)
- Separate scaling (can scale backend independently)
- Cost-effective ($5/month for Railway, free for Vercel)

---

## 📋 Step-by-Step: Quick Start

### **Today (30 minutes):**

#### **1. Deploy Frontend on Vercel**
```bash
cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

#### **2. Add Custom Domain in Vercel**
- Go to: https://vercel.com/dashboard
- Select project → Settings → Domains
- Add: `affiliate.david-adam.me`

#### **3. Verify DNS**
```bash
# Check DNS propagation
dig affiliate.david-adam.me

# Should show CNAME pointing to Vercel
```

#### **4. Test Website**
- Visit: `https://affiliate.david-adam.me`
- Should see landing page
- Click "Privacy Policy" link
- Should work ✅

---

### **Tomorrow (1 hour):**

#### **5. Deploy Backend API on Railway**

**Option A: Automatic Deployment**
```bash
# Install Railway CLI
npm i -g railway

# Login
railway login

# Initialize
cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api
railway init

# Deploy
railway up
```

**Option B: Manual Deployment**
1. Go to: https://railway.app/
2. Click: "New Project" → "Deploy from GitHub"
3. Configure Python service
4. Set start command: `python3 api_server.py`
5. Deploy

---

#### **6. Connect Frontend to Backend**

**Update `social_push.html`:**
```javascript
// Change API URL from localhost to Railway
const API_URL = 'https://affiliate-api.david-adam.me/api';

// Or use relative path (if same domain)
const API_URL = '/api';
```

---

## 🔧 DNS Configuration Summary

### **For Vercel (Frontend):**
```
Type: CNAME
Name: affiliate
Value: cname.vercel-dns.com
TTL: 3600
```

### **For Railway (Backend API):**
```
Type: CNAME
Name: affiliate-api
Value: [railway-provided-url]
TTL: 3600
```

---

## ✅ Checklist

**Frontend (Vercel):**
- [ ] Deploy to Vercel
- [ ] Add custom domain: affiliate.david-adam.me
- [ ] Verify DNS propagation
- [ ] Test: Landing page loads
- [ ] Test: Privacy policy page loads
- [ ] Test: Social dashboard loads

**Backend (Railway/Render):**
- [ ] Create Railway account
- [ ] Deploy Python service
- [ ] Add custom domain: affiliate-api.david-adam.me
- [ ] Set environment variables (PORT=8100)
- [ ] Test: API endpoints work
- [ ] Connect frontend to backend

**Pinterest App:**
- [ ] Submit privacy policy URL: https://affiliate.david-adam.me/privacy-policy
- [ ] Submit website URL: https://affiliate.david-adam.me
- [ ] Wait for approval

---

## 🚀 After Deployment

### **1. Update Social Profiles**

**Telegram Bot:**
- Description: "AI-powered Amazon affiliate bot. Find trending products at https://affiliate.david-adam.me"
- Photo: Upload `app-icon-512.png`

**Twitter/X:**
- Bio: "AI-powered Amazon affiliate bot. Find trending AI hardware at https://affiliate.david-adam.me"
- Profile photo: Upload `app-icon-256.png`

**Pinterest:**
- Profile: "Amazon Affiliate Bot - AI-Powered Product Discovery"
- Website: https://affiliate.david-adam.me
- Privacy policy: https://affiliate.david-adam.me/privacy-policy
- Profile photo: Upload `app-icon-512.png`

---

### **2. Test All Links**

```bash
# Test frontend
curl https://affiliate.david-adam.me
curl https://affiliate.david-adam.me/privacy-policy

# Test backend API
curl https://affiliate-api.david-adam.me/api/products
```

---

### **3. Monitor Analytics**

**Vercel Analytics:**
- Go to: https://vercel.com/dashboard
- View: Page views, unique visitors, top pages

**Railway Metrics:**
- Monitor: CPU usage, memory, response times
- Alerts: Set up for high error rates

---

## 💡 Pro Tips

1. **Use environment variables** for sensitive data (API keys, tokens)
2. **Enable HTTPS** (automatic on Vercel/Railway)
3. **Set up caching** for static assets (Vercel does this automatically)
4. **Monitor uptime** using UptimeRobot or similar
5. **Back up database** regularly (Railway has automated backups)

---

## 📞 Support

**Vercel Docs:** https://vercel.com/docs
**Railway Docs:** https://docs.railway.app
**Render Docs:** https://render.com/docs

**Issues?**
- Check DNS propagation: https://dnschecker.org/
- Verify SSL certificate: Click 🔒 in browser address bar
- Check Vercel/Railway logs for errors

---

## 🎉 You're Ready!

Once deployed, you'll have:
- ✅ Professional landing page at affiliate.david-adam.me
- ✅ Privacy policy for Pinterest API approval
- ✅ Backend API for social media automation
- ✅ Scalable architecture (frontend + backend separated)

**Next:** Submit to Pinterest API with your new privacy policy URL!

---

*Last Updated: February 25, 2026*
