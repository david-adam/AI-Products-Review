# TaskFlow Notifications System - Design Document

**Created:** 2026-03-10
**Status:** Design Phase Complete
**Original Card:** "Implement Notifications System" (tf_notifications_1772852968550)

---

## Executive Summary

The TaskFlow notifications system has a **partial implementation** that needs completion. The backend and basic UI exist, but several key features are missing for a complete production-ready system.

---

## Current State Analysis

### ✅ Already Implemented

| Component | Status | Location |
|-----------|--------|----------|
| Database collection | Complete | `database.js` - `notifications` array |
| Backend API routes | Complete | `routes/notifications.js` |
| Notification creation | Partial | `routes/cards.js` - assignment triggers |
| Email integration | Partial | `notifications.js` - nodemailer |
| Bell icon (dashboard) | Complete | `dashboard.html` |
| Unread badge | Complete | `app.js` |
| Notification modal | Complete | `app.js` |
| Mark as read | Complete | API + UI |
| Delete notification | Complete | API + UI |

### ❌ Missing / Incomplete

| Component | Priority | Notes |
|-----------|----------|-------|
| Bell icon on board.html | HIGH | Only in dashboard.html |
| Real-time updates | HIGH | No WebSocket/polling |
| Mention notifications | HIGH | @username not implemented |
| Comment notifications | MEDIUM | Not implemented |
| Status change notifications | MEDIUM | Not implemented |
| Archive folder | MEDIUM | UI needs inbox/archive tabs |
| Notification settings | LOW | Email preferences |
| Polling fallback | MEDIUM | For real-time without WebSocket |

---

## System Architecture

### 1. Database Schema

```javascript
// notifications collection (already exists)
{
  id: string,
  userId: string,           // recipient
  type: string,              // 'assigned' | 'mentioned' | 'comment' | 'status_change' | 'watcher'
  message: string,           // human-readable message
  cardId: string,
  boardId: string,
  fromUserId: string,        // who triggered it
  read: boolean,
  archived: boolean,         // for archive folder
  emailSent: boolean,
  createdAt: timestamp
}
```

### 2. Real-Time Strategy

**Decision: Hybrid Polling + Event-Driven**

For TaskFlow's scale, **polling every 30 seconds** is the recommended approach:

| Approach | Pros | Cons | Recommendation |
|----------|------|------|----------------|
| WebSocket | Real-time, instant | Complexity, scaling | ❌ Overkill |
| Server-Sent Events | Real-time, simpler | Browser support | ❌ Not needed |
| Polling (30s) | Simple, reliable, scalable | 30s delay | ✅ **Recommended** |
| Long polling | Near real-time | Complexity | ❌ Overkill |

**Rationale:**
- TaskFlow is an internal tool, 30s delay is acceptable
- Simpler to maintain and scale
- Works with existing JSON file-based storage
- Can upgrade to WebSocket later if needed

### 3. Email Integration

Current implementation uses nodemailer with SMTP. Need to add:

```env
# Email Configuration (in .env)
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_SECURE=false
EMAIL_USER=notifications@taskflow.app
EMAIL_PASS=your-password
EMAIL_FROM="TaskFlow" <notifications@taskflow.app>
```

**Email Templates:**
- Card assignment
- Mention (@username)
- Comment added
- Status change
- Card watcher update

### 4. Notification Types

| Type | Trigger | Recipients |
|------|---------|------------|
| `assigned` | Card assigned to user | Assignee |
| `mentioned` | @username in comment | Mentioned user |
| `comment` | New comment on card | Card assignee, watchers |
| `status_change` | Card moved to new list | Card assignee, watchers |
| `watcher` | Added as watcher | New watcher |

---

## UI/UX Design

### Notification Bell (Global)

- Position: Header right, next to settings
- Badge: Red circle with unread count (max display: 99+)
- Click: Opens notification modal

### Notification Modal

```
┌─────────────────────────────────────┐
│  Notifications          [Mark All Read] │
├─────────────────────────────────────┤
│  [Inbox] [Archive]                  │
├─────────────────────────────────────┤
│  ┌─────────────────────────────────┐│
│  │ 🔔 John assigned you to "Fix   ││
│  │    bug #123"                    ││
│  │    5 minutes ago           [x] ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │ 🔔 Sarah mentioned you in       ││
│  │    "Update docs"                ││
│  │    1 hour ago               [x] ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
```

### Visual States

- **Unread:** Bold text, light blue background tint
- **Read:** Normal weight, white background
- **Archived:** Greyed out, in archive tab
- **Hover:** Slight background darkening

---

## Implementation Sub-Tasks

### Phase 1: UI Completion (P1)

1. **Add notification bell to board.html** (1 hr)
   - Copy from dashboard.html header
   - Ensure consistent styling

2. **Create notification modal HTML** (1 hr)
   - Move from dynamic JS to static HTML
   - Add inbox/archive tabs

3. **Add archive functionality** (2 hr)
   - Archive button on each notification
   - Archive tab in modal
   - Restore from archive option

### Phase 2: Real-Time Updates (P1)

4. **Implement polling system** (3 hr)
   - Poll /api/notifications every 30 seconds
   - Update badge count
   - Show toast for new notifications
   - Store last notification timestamp

### Phase 3: Notification Triggers (P2)

5. **Add mention notifications** (2 hr)
   - Parse @username in comments
   - Create notification for mentioned user
   - Support multiple mentions

6. **Add comment notifications** (2 hr)
   - Notify assignee on new comment
   - Notify all watchers on new comment

7. **Add status change notifications** (2 hr)
   - Notify on list movement
   - Include old → new status in message

### Phase 4: Email Integration (P2)

8. **Complete SMTP setup** (2 hr)
   - Configure environment variables
   - Test email delivery
   - Add error handling

9. **Create email templates** (3 hr)
   - HTML templates for each type
   - Include card link
   - Include sender info

### Phase 5: Settings & Polish (P3)

10. **Add notification settings** (2 hr)
    - Per-user email preferences
    - Enable/disable notification types
    - Store in user profile

---

## Performance Considerations

1. **Polling interval:** 30 seconds balances responsiveness with server load
2. **Pagination:** Limit initial load to 20 notifications, load more on scroll
3. **Indexing:** userId and read status already indexed in JSON
4. **Email queue:** Don't block HTTP response - queue and send async
5. **Rate limiting:** Debounce notification creation to prevent spam

---

## Scalability Path

Current implementation uses JSON file storage. When scaling:

1. **Move to SQLite/Turso:** Add proper indexing
2. **Add Redis cache:** Cache unread counts
3. **Upgrade to WebSocket:** When real-time becomes critical
4. **Email service:** Consider SendGrid/SES for delivery reliability

---

## Files to Modify

| File | Changes |
|------|---------|
| `public/board.html` | Add notification bell |
| `public/dashboard.html` | Add modal HTML structure |
| `public/app.js` | Add polling, archive, mention parsing |
| `public/css/styles.css` | Add notification styles |
| `routes/cards.js` | Add comment/status triggers |
| `notifications.js` | Complete email templates |
| `.env.example` | Add email config |

---

## Testing Plan

1. Unit test notification creation
2. Test mention parsing regex
3. Verify badge updates on poll
4. Test email delivery
5. Test archive/restore flow
6. Test with multiple users

---

## Timeline Estimate

| Phase | Tasks | Hours |
|-------|-------|-------|
| Phase 1 | 1-3 | 4 hr |
| Phase 2 | 4 | 3 hr |
| Phase 3 | 5-7 | 6 hr |
| Phase 4 | 8-9 | 5 hr |
| Phase 5 | 10 | 2 hr |
| **Total** | **10** | **20 hr** |

---

*Design completed: 2026-03-10*
*Ready for implementation*
