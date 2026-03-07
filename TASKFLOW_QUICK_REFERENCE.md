# TaskFlow Autonomous Worker - Quick Reference

**Installed:** 2026-03-07 10:15
**Status:** ✅ **Active and Ready**

---

## ⚙️ **Cronjobs Installed**

```
23:30 daily - TaskFlow Autonomous Worker (all boards)
23:00 UTC  - Product scraping (7 AM Shanghai)
09:30 daily - Trend scraper (existing)
```

---

## 📋 **How to Use**

### **1. Open TaskFlow App**
Navigate to your TaskFlow installation and open the app.

### **2. Find "ProductLens AI" Board**
This board was auto-created with your Phase 2 tasks.

### **3. Add/Move Cards**
- **To Do** - Ready for autonomous execution
- **In Progress** - Currently being worked on (will be picked up)
- **Done** - Completed (worker skips these)
- **Review** - Blocked/needs attention

### **4. Wait for 23:30**
Worker runs automatically and processes all cards in "To Do" and "In Progress"

### **5. Check Results**
- **Done list** - Successfully completed tasks
- **Review list** - Tasks that failed or need approval
- **Card comments** - Execution details and logs

---

## 🎯 **Current Tasks in ProductLens AI Board**

### **In "To Do" (Ready to Execute):**

1. **[P0, Database]** Deploy Database Schema to Turso
   - Runs migrations.sql
   - Creates 5 tables
   - Time: ~30 minutes

2. **[P0, Database, Testing]** Test Database Integration
   - Validates Turso connection
   - Tests queries
   - Time: ~30 minutes

3. **[P0, AI, Content]** Generate Content Samples for Review
   - Picks 3-5 products
   - Generates summaries + reviews
   - Creates social images
   - Time: ~45 minutes

4. **[P1, API, Vercel]** Update Vercel API Endpoints
   - Creates api/reviews.js
   - Tests locally
   - **Needs your approval** (will move to Review)
   - Time: ~1 hour

5. **[P1, UI, Dashboard]** Create Content Generation Dashboard
   - Admin page for content management
   - **Needs design input** (will move to Review)
   - Time: ~1.5 hours

6. **[P2, DevOps]** Set Up Daily Cron Job
   - Configures daily generation at 7 AM
   - Time: ~30 minutes

---

## 🔄 **Daily Workflow**

### **Morning (After Worker Runs):**
1. Open TaskFlow
2. Check "Done" list for completed work
3. Check "Review" list for blocked tasks
4. Read card comments for details

### **During Day:**
1. Work on tasks collaboratively with me
2. Move completed tasks to "Done"
3. Add new tasks to "To Do" as needed
4. Move tasks needing approval to "Review"

### **Evening (Before Sleep):**
1. Review "To Do" list
2. Adjust priorities if needed
3. Add tasks for tonight
4. Go to sleep!

### **Tonight (23:30):**
- Worker executes all "To Do" and "In Progress" cards
- Moves to "Done" or "Review"
- Adds progress comments

---

## 📊 **View/Edit Cronjobs**

```bash
# View current cronjobs
crontab -l

# Edit cronjobs (add more times, etc.)
crontab -e

# Remove all cronjobs
crontab -r
```

### **Add Daytime Runs (Optional):**
In `crontab -e`, uncomment these lines:
```
0 9 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/trigger_autonomous_worker.sh
0 14 * * * /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api/scripts/trigger_autonomous_worker.sh
```

This adds runs at 9 AM and 2 PM.

---

## 📁 **Log Files**

- **AUTONOMOUS_WORK_PROGRESS.md** - Detailed execution log
- **memory/autonomous_work.log** - Run timestamps

---

## 🆘 **Troubleshooting**

### **Worker didn't run:**
- Check: `crontab -l` (is job installed?)
- Check: `ls -la scripts/trigger_autonomous_worker.sh` (is it executable?)
- Check: `grep CRON /var/log/syslog` (macOS: use Console.app)

### **Task failed:**
- Check "Review" list in TaskFlow
- Read card comments for error details
- Check AUTONOMOUS_WORK_PROGRESS.md

### **Manual test run:**
```bash
cd /Users/trinitym/.openclaw/workspace-coder-fast/scraper_api
./scripts/trigger_autonomous_worker.sh
```

---

## 🚀 **Adding More Projects**

1. Create new board in TaskFlow (e.g., "LinkedIn Jobs Scraper")
2. Use same 5 lists: Backlog, To Do, In Progress, Review, Done
3. Add cards to "To Do" or "In Progress"
4. Worker automatically detects and processes them
5. No configuration needed!

---

## ✅ **System Ready!**

Your autonomous worker is now installed and will run at 23:30 tonight.

**Tonight's work:**
- Deploy database schema
- Test integration
- Generate content samples
- (Others will move to Review for your approval)

**Morning task:** Check "Done" list for results! 🎉

---

*Installed: 2026-03-07 10:15*
*Next run: 23:30 today*
