# User Requirements - ProductLens AI Phase 2

**Date:** 2026-03-06 22:04
**Status:** ✅ **Requirements Confirmed**

---

## 🎯 **Confirmed Requirements**

### **1. Social Platforms (Priority Order)**
1. Pinterest
2. X/Twitter
3. Instagram
4. Telegram

**Implementation Order:**
- Start with Pinterest and Twitter (higher priority)
- Then Instagram and Telegram

---

### **2. Content Frequency**
- **Generation:** Daily
- **Per Product:** Generate new content daily

---

### **3. Review Format Requirements**

#### **Summary (Social Media)**
- **Length:** 100-200 characters
- **Use Case:** Social media posts, captions, quick previews
- **Platform:** Twitter, Instagram captions, Pinterest descriptions

#### **Full Review (Blog Post)**
- **Length:** 600-900 characters (current Kimi K2.5 generates ~9000 - too long!)
- **Use Case:** Full product reviews, blog content
- **Platform:** Website reviews, blog posts
- **Note:** Will adjust in future if needed

**Action Required:** Update Kimi K2.5 prompts to generate TWO formats:
1. Short summary (100-200 chars)
2. Full review (600-900 chars)

---

### **4. Cron Job Schedule**

#### **Product Scraping Cron**
- **Time:** 7:00 AM Shanghai time (UTC+8)
- **Frequency:** Daily
- **Task:** Scrape new products from Amazon

#### **Content Generation Cron**
- **Time:** After scraping completes
- **Frequency:** Daily
- **Task:** Generate AI content for new/updated products

#### **Social Publishing**
- **Status:** NOT automated
- **Workflow:** Manual review and approval only
- **Reason:** User wants to review before publishing

---

### **5. Deployment Strategy**
- **Approval:** Yes, deploy if no breaking changes
- **Review Process:**
  1. Local testing tonight
  2. User reviews on local tomorrow
  3. User reviews on Vercel site
  4. Manual approval before live deployment

---

## 🔄 **Implementation Updates Needed**

### **Kimi K2.5 Text Generation**
**Current:** Generates 9000-char single review

**Required:** Generate TWO formats:
```python
def generate_review_with_formats(product_name, product_category, features, platform):
    """
    Generate both summary and full review formats.
    
    Returns:
        dict: {
            'summary': '100-200 char summary',
            'full_review': '600-900 char full review',
            'platform': platform
        }
    """
    # TODO: Update prompts for two formats
```

---

### **Database Schema Updates**
Need to store BOTH formats:
```sql
CREATE TABLE product_reviews (
    id INTEGER PRIMARY KEY,
    product_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    summary TEXT,        -- 100-200 chars
    full_review TEXT,    -- 600-900 chars
    image_url TEXT,
    created_at DATETIME
);
```

---

### **Cron Job Configuration**
```bash
# Product scraping (7 AM Shanghai)
0 7 * * * /usr/bin/python3 /path/to/trend_scraper.py

# Content generation (after scraping)
30 7 * * * /usr/bin/python3 /path/to/cron_content_gen.py
```

---

## 📋 **Updated TODO for Tonight**

### **P0 - Must Complete**
- [x] User requirements gathered
- [ ] Database schema design (include summary and full_review fields)
- [ ] Update Kimi K2.5 prompts for two formats
- [ ] Database integration script
- [ ] Memory persistence system

### **P1 - If Time Permits**
- [ ] Cron job setup (7 AM Shanghai)
- [ ] Test content generation with new formats
- [ ] API endpoints for reviews

---

## 🎯 **Platform-Specific Requirements**

### **Pinterest**
- Image: Vertical (9:16) optimized
- Text: Summary (100-200 chars) + hashtags
- Focus: Product photography, lifestyle

### **X/Twitter**
- Image: Horizontal (16:9) optimized
- Text: Summary only (100-200 chars) due to character limit
- Focus: Quick product highlights

### **Instagram**
- Image: Square (1:1) optimized
- Text: Summary in caption, full review optional
- Focus: Aesthetic, professional

### **Telegram**
- Image: Horizontal (16:9) optimized
- Text: Can include full review
- Focus: Newsletter style, detailed

---

*Requirements Confirmed: 2026-03-06 22:04*
*Implementation Start: 23:30*
