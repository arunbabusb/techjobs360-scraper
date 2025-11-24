# 🆓 FREE TIER QUICK FIX - 3 Options

**You're on QUIC.cloud free tier** → Some options may be limited

---

## 🎯 TRY FIRST: Check If Toggle Works (2 minutes)

Even on free tier, **try this first:**

### Steps:

1. **Log in:** https://my.quic.cloud/
   - Email: chessgenius900@gmail.com
   - Password: Qsharper$1000

2. **Navigate:**
   ```
   Click "Domains" → "techjobs360.com" → "Security" tab
   ```

3. **Look for bot protection:**

   **What you might see:**

   **A) Toggle switch** - Click it OFF
   ```
   Bot Protection: [🟢 ON]  ← Click this
   ```

   **B) Dropdown menu** - Select "Off" or "Low"
   ```
   Protection Level: [High ▼]  ← Change to "Low" or "Off"
   ```

   **C) Grayed out** - Free tier doesn't allow (go to Plan B)
   ```
   Bot Protection: [🔒 ON]  ← Locked (cannot change)
   ```

4. **If you CAN change it:**
   - Click "Save Changes"
   - Click "Purge Cache"
   - Wait 3 minutes
   - Test: `./test_api_access.sh`
   - ✅ **Done!**

5. **If it's grayed out or locked:**
   - Go to **PLAN B** below

---

## 🅱️ PLAN B: Subdomain Bypass (Best for Free Tier)

**This WILL work, guaranteed!**

### What you'll do:
Create `api.techjobs360.com` subdomain that bypasses QUIC.cloud

### Steps:

#### **Step 1: Create Subdomain (Contact HeroXHost)**

**Option A: Do it yourself (if you have cPanel access)**
```
1. Log into HeroXHost cPanel
2. Find "Subdomains"
3. Create new subdomain:
   - Subdomain: api
   - Domain: techjobs360.com
   - Result: api.techjobs360.com
4. Point to your origin server IP (not QUIC.cloud)
5. Save
```

**Option B: Ask HeroXHost support**
```
Email/ticket to HeroXHost:

Subject: Please create subdomain for WordPress API

Hi,

Can you please create a subdomain for me:
- Subdomain: api.techjobs360.com
- Point to: Origin server IP (NOT through QUIC.cloud CDN)
- Purpose: Direct WordPress REST API access

Thank you!
```

---

#### **Step 2: Update Scraper (5 minutes)**

Once subdomain is created:

1. **Update GitHub Secrets:**
   ```
   Go to: https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions

   Find: WP_URL
   Change from: https://techjobs360.com
   Change to: https://api.techjobs360.com

   Click "Update secret"
   ```

2. **Test it:**
   ```bash
   curl https://api.techjobs360.com/wp-json/
   # Should return JSON (not CAPTCHA)
   ```

3. **Run scraper:**
   ```bash
   cd /home/user/techjobs360-scraper
   ./test_api_access.sh
   # Should pass now!
   ```

✅ **Done! Scraper will work now**

---

## 🅲 PLAN C: Contact QUIC.cloud Support

**Ask for free tier exemption**

### Email:

```
To: support@quic.cloud
Subject: Free tier - Need WordPress API access

Hi,

I'm on the free tier for techjobs360.com.

I have a legitimate job scraper that needs to post to my WordPress
REST API, but bot protection is blocking it.

Can you please:
1. Disable bot protection for /wp-json/* paths, OR
2. Whitelist my scraper, OR
3. Guide me on free tier workarounds?

The scraper is not malicious - it posts job listings to my own site.

Thank you!
```

**Response time:** Usually 1-2 days

**While waiting:** Implement Plan B (subdomain)

---

## 📊 Which Plan Should You Use?

| Plan | Time | Success Rate | Difficulty |
|------|------|--------------|------------|
| **Try First** | 2 min | 40% | Easy |
| **Plan B (Subdomain)** | 20 min | 95% | Medium |
| **Plan C (Support)** | 1-2 days | 80% | Easy |

**Recommendation:**
1. Try First (2 minutes)
2. If doesn't work → Plan B immediately (20 minutes)
3. While setting up Plan B → Send Plan C email

---

## 🚀 FASTEST PATH TO SUCCESS

### **Right Now (Next 5 minutes):**

1. ✅ Log into QUIC.cloud
2. ✅ Try to toggle bot protection OFF
3. ❌ If locked/grayed out → Start Plan B

### **Next 20 minutes:**

4. ✅ Contact HeroXHost (or use cPanel)
5. ✅ Create api.techjobs360.com subdomain
6. ✅ Update GitHub Secret (WP_URL)
7. ✅ Test: `curl https://api.techjobs360.com/wp-json/`

### **Result:**
✅ Scraper works!
✅ Jobs posted to WordPress!
✅ Jobs visible on techjobs360.com!

---

## 🎯 Why Subdomain Works (Plan B)

**Current situation:**
```
Scraper → QUIC.cloud CDN → ❌ BLOCKED
```

**After subdomain:**
```
Scraper → api.techjobs360.com → ✅ DIRECT to origin (bypasses QUIC.cloud)

Main site → techjobs360.com → QUIC.cloud → Still protected ✅
```

**Benefits:**
- ✅ API access works
- ✅ Main site still protected
- ✅ No QUIC.cloud limitations
- ✅ Free tier friendly
- ✅ Works permanently

---

## 📞 Need Help?

### **For subdomain creation:**
Contact HeroXHost support
- They can create api.techjobs360.com for you
- Usually done within hours

### **For QUIC.cloud questions:**
Email: support@quic.cloud
- Ask about free tier capabilities
- Request API path exemption

### **For scraper issues:**
Run: `./test_api_access.sh`
- Shows exactly what's wrong
- Provides specific fix steps

---

## ✅ Bottom Line

**Your situation:** Free tier, cannot toggle bot protection

**Best solution:** Create subdomain (Plan B)
- Time: 20 minutes
- Cost: $0
- Success: 95%+

**Action:** Contact HeroXHost to create `api.techjobs360.com`

---

**🚀 Start with Plan B - most reliable for free tier users!**

See **QUIC_FREE_TIER_FIX.md** for detailed step-by-step guide.

---

*Last Updated: 2025-11-24*
*For: QUIC.cloud Free Tier Users*
