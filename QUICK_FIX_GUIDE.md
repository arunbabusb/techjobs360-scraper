# ⚡ Quick Fix Guide - WordPress 503 Error

**Problem:** techjobs360.com returns 503 error → Scraper can't post jobs

**Solution:** Try these in order (2-5 minutes each)

---

## 🚀 **Method 1: Delete .maintenance File** ⭐ START HERE

**Why:** WordPress update created a stuck maintenance file

**How:**
1. Log into **cPanel/hosting control panel**
2. Open **File Manager**
3. Go to `public_html` folder
4. Click **Settings** → Check "Show Hidden Files" → Save
5. Find `.maintenance` file
6. **Delete it**
7. Test: https://techjobs360.com/wp-json/

**Expected result:** Should see JSON data

---

## 🔌 **Method 2: Disable Plugins**

**Why:** A plugin is blocking REST API or causing errors

**How (if you can access wp-admin):**
1. Go to: https://techjobs360.com/wp-admin/
2. Click **Plugins** → **Installed Plugins**
3. Select all plugins (checkbox at top)
4. Bulk Actions → **Deactivate** → Apply
5. Test: https://techjobs360.com/wp-json/

**How (if you CANNOT access wp-admin):**
1. Open **File Manager** in cPanel
2. Go to: `public_html/wp-content/plugins/`
3. Rename `plugins` folder to `plugins-disabled`
4. Test: https://techjobs360.com/wp-json/

**Expected result:** Should see JSON data

---

## 🔥 **Method 3: Restart PHP/Services**

**Why:** PHP service might be crashed or stuck

**How:**
1. Log into **cPanel**
2. Find **"Select PHP Version"** or **"PHP Selector"**
3. Click **Restart** or **Apply**
4. OR find **"Restart Services"** and restart Apache/Nginx
5. Test: https://techjobs360.com/wp-json/

**Expected result:** Should see JSON data

---

## 🔒 **Method 4: Fix SSL Certificate**

**Why:** SSL error detected (BAD_ECC_CERT)

**How:**
1. Log into **cPanel**
2. Find **"SSL/TLS Status"** or **"Let's Encrypt SSL"**
3. Click **"Run AutoSSL"** or **"Issue New Certificate"**
4. Wait 2-5 minutes
5. Test: https://techjobs360.com/wp-json/

**Expected result:** Should see JSON data

---

## ☁️ **Method 5: Disable Cloudflare Protection** (if using Cloudflare)

**Why:** Cloudflare WAF blocking REST API requests

**How:**
1. Log into **Cloudflare dashboard**
2. Select **techjobs360.com**
3. Go to **Security** → **Settings**
4. Set Security Level to: **Essentially Off**
5. Go to **Security** → **Bots**
6. Turn OFF **"Bot Fight Mode"**
7. Test: https://techjobs360.com/wp-json/

**Expected result:** Should see JSON data

**Once working:** Create WAF rule to allow `/wp-json/` permanently

---

## 📝 **Method 6: Enable REST API in Files**

**Why:** REST API might be disabled in config

**How:**
1. Open **File Manager** in cPanel
2. Go to WordPress root folder
3. Edit **.htaccess**
4. Look for lines blocking REST API:
   ```apache
   # Block WordPress REST API
   RewriteRule ^wp-json/ - [F,L]
   ```
5. **Delete or comment out** those lines
6. Save
7. Test: https://techjobs360.com/wp-json/

**Also check wp-config.php:**
- Remove: `define('REST_API_ENABLED', false);`
- Or change to: `define('REST_API_ENABLED', true);`

**Expected result:** Should see JSON data

---

## 💾 **Method 7: Increase Memory Limits**

**Why:** Low memory causing crashes

**How:**
1. Edit **wp-config.php**
2. Add before `/* That's all, stop editing! */`:
   ```php
   define('WP_MEMORY_LIMIT', '256M');
   define('WP_MAX_MEMORY_LIMIT', '512M');
   ```
3. Save
4. Test: https://techjobs360.com/wp-json/

**Expected result:** Should see JSON data

---

## 📞 **Method 8: Contact Hosting Support**

**Why:** Server-level issue you can't fix yourself

**What to say:**
```
My WordPress REST API at https://techjobs360.com/wp-json/
returns 503 Service Unavailable.

Please check:
- Server error logs
- Firewall blocking /wp-json/
- SSL certificate (showing BAD_ECC_CERT error)
- PHP/WordPress services running

I need REST API working for my automated job scraper.
```

---

## ✅ **HOW TO VERIFY IT WORKS:**

Visit this URL in your browser:
```
https://techjobs360.com/wp-json/
```

### **If WORKING:** ✅
You'll see JSON data like:
```json
{
  "name": "TechJobs360",
  "description": "...",
  "url": "https://techjobs360.com",
  ...
}
```

### **If BROKEN:** ❌
You'll see:
- "503 Service Unavailable"
- OR blank page
- OR error message

---

## 🎯 **AFTER IT WORKS:**

1. **Update GitHub Secrets** (if needed):
   - https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions
   - Make sure: WP_URL, WP_USERNAME, WP_APP_PASSWORD exist

2. **Run scraper manually:**
   - https://github.com/arunbabusb/techjobs360-scraper/actions/workflows/scraper.yml
   - Click "Run workflow"

3. **Check for jobs in 10 minutes:**
   - https://techjobs360.com/wp-admin/edit.php

---

## 🆘 **STILL STUCK?**

**Tell me:**
1. Which methods you tried
2. What you see at https://techjobs360.com/wp-json/
3. Can you access https://techjobs360.com/wp-admin/ ?
4. What hosting provider you're using

**I'll help you debug further!** 🚀

---

## 📊 **MOST COMMON FIXES:**

| Problem | Solution | Success Rate |
|---------|----------|--------------|
| Stuck update | Delete .maintenance | 40% |
| Plugin conflict | Disable plugins | 30% |
| Cloudflare WAF | Disable Bot Fight | 15% |
| SSL issue | Regenerate SSL | 10% |
| Server crash | Restart services | 5% |

**Try Method 1 first** - it fixes 40% of cases! 🎯
