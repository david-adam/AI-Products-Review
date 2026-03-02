# Social Network Integration Plan

## Current Status
✅ 33 products with AI-generated content ready
✅ Frontend dashboard for review (index.html)
✅ All content includes affiliate link: `?tag=dav7aug-20`

## Target Platforms (from TaskFlow Todo)

### 1. Telegram Bot & Channel
**Priority: HIGH** ✅ Already mentioned in Todo list

**Components:**
- [ ] Create Telegram bot via @BotFather
- [ ] Create channel for subscribers
- [ ] Configure bot token in `.env`
- [ ] Implement bot commands:
  - `/latest` - Show latest products
  - `/search <query>` - Search products
  - `/category <name>` - Filter by category
  - `/deals` - Show price drops (future)
- [ ] Auto-post daily at 10 AM Shanghai time
- [ ] Add inline buttons for product links

**Why Telegram First:**
- Easy API
- Supports rich formatting
- Good for tech communities
- Channel = broadcast to subscribers
- Bot = interactive search

### 2. Twitter/X Bot
**Priority: MEDIUM**

**Components:**
- [ ] Set up Twitter Developer account
- [ ] Create Twitter app
- [ ] Get API keys & tokens
- [ ] Implement posting with:
  - Product image
  - SEO title
  - Affiliate link
  - Hashtags (#EdgeAI #RaspberryPi #Maker)
- [ ] Schedule tweets (3-5 per day)
- [ ] Add thread support for blog posts

**Rate Limits:**
- Free tier: 1,500 tweets/month
- Aim for 30-50 tweets/month

### 3. Blog / Website
**Priority: MEDIUM** (Next.js mentioned in Todo)

**Components:**
- [ ] Set up Next.js project
- [ ] Create product pages (SEO-optimized)
- [ ] Implement schema.org markup
- [ ] Add "Buy on Amazon" buttons
- [ ] Create comparison pages
- [ ] Add email collection

### 4. Reddit (Community Engagement)
**Priority: LOW** (Already in Todo)

**Subreddits:**
- r/raspberry_pi
- r/SingleBoardComputer
- r/homeassistant
- r/selfhosted
- r/EdgeComputing

**Strategy:**
- Share helpful content, not just spam
- Write guides/tutorials
- Link to blog posts with affiliate links

## Implementation Order

### Phase 1: Telegram (This Week)
1. Create bot via @BotFather
2. Get bot token
3. Implement basic commands
4. Test auto-posting
5. Create channel and subscribe

### Phase 2: Twitter (Next Week)
1. Apply for Twitter Developer access
2. Create app
3. Implement tweet formatter
4. Schedule first tweets
5. Monitor engagement

### Phase 3: Blog (Week 3-4)
1. Set up Next.js
2. Create product pages
3. Add SEO schema
4. Implement blog from outlines
5. Set up analytics

## Files to Create

```
scraper_api/
├── bot/
│   ├── telegram_bot.py      # Telegram bot implementation
│   ├── twitter_bot.py       # Twitter bot implementation
│   └── post_formatter.py    # Format content for each platform
├── config/
│   └── platforms.json       # Platform-specific configs
└── scheduler/
    └── auto_post.py         # Cron-style scheduler
```

## Configuration Needed

```bash
# .env additions

# Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=@your_channel

# Twitter (Future)
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_SECRET=your_access_secret
TWITTER_BEARER_TOKEN=your_bearer

# Posting Schedule
POST_TIME=10:00
POST_TIMEZONE=Asia/Shanghai
DAILY_POST_LIMIT=5
```

## Content Strategy

### Telegram Posts
- Rich text with emojis
- Inline buttons for "Buy on Amazon"
- Category tags
- 2-3 posts per day

### Twitter Posts
- Product image + title + affiliate link
- Hashtags: #EdgeAI #Maker #RaspberryPi #NVIDIAJetson
- Thread for blog content
- 3-5 tweets per day

### Blog Posts
- Full articles from outlines
- SEO-optimized titles
- Product comparisons
- "Best of" roundups

## Next Steps

1. ✅ Review products in frontend dashboard
2. ⏳ Create Telegram bot (@BotFather)
3. ⏳ Implement Telegram bot commands
4. ⏳ Test auto-posting
5. ⏳ Create Telegram channel
6. ⏳ Move to Twitter integration

---

**Ready to start with Telegram?** Just say the word and I'll create the bot implementation!
