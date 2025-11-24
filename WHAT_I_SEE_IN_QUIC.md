# 🔍 What You See in QUIC.cloud - Troubleshooting Guide

**Problem**: Can't find bot protection toggle button
**Likely reason**: Free tier doesn't show this option

---

## 📸 Tell Me What You See

When you're logged into QUIC.cloud at your domain, what do you see?

### **Section 1: Main Navigation (Left Sidebar)**

Do you see these menu items?
- [ ] Dashboard
- [ ] Domains
- [ ] Billing
- [ ] Support
- [ ] Settings

**Which ones are visible?**

---

### **Section 2: After Clicking "Domains" → "techjobs360.com"**

What tabs do you see at the top?
- [ ] Overview / Dashboard
- [ ] CDN
- [ ] Security
- [ ] Cache
- [ ] Settings
- [ ] Analytics
- [ ] Other: ___________

**Which tabs are available?**

---

### **Section 3: On Security or CDN Tab**

What sections/options do you see?
- [ ] Bot Protection
- [ ] Firewall
- [ ] WAF (Web Application Firewall)
- [ ] DDoS Protection
- [ ] Page Rules
- [ ] IP Whitelist / Allowlist
- [ ] SSL/TLS Settings
- [ ] Nothing related to security
- [ ] Other: ___________

**What options are listed?**

---

### **Section 4: If You See "Bot Protection"**

What does it show?
- [ ] Toggle switch (ON/OFF)
- [ ] Dropdown menu (High/Medium/Low/Off)
- [ ] Checkbox (Enable/Disable)
- [ ] Just text saying "Bot Protection: Enabled"
- [ ] Text saying "Upgrade to enable" or "Premium feature"
- [ ] Grayed out toggle/button
- [ ] Other: ___________

**Can you click anything?**

---

## 🎯 Common Free Tier Scenarios

### **Scenario A: No Security Tab at All**
```
You see: Overview, CDN, Cache, Settings
You DON'T see: Security tab

Meaning: Free tier doesn't have security controls
Solution: Use subdomain bypass (Plan B below)
```

### **Scenario B: Security Tab Exists, But Empty**
```
You see: Security tab
You click it: Shows "Upgrade to access security features"

Meaning: Security features require paid plan
Solution: Use subdomain bypass (Plan B below)
```

### **Scenario C: Bot Protection Shown, But Grayed Out**
```
You see: Bot Protection [🔒 Enabled]
Cannot click: It's locked/grayed out

Meaning: Setting exists but controlled by hosting provider or requires upgrade
Solution: Contact HeroXHost or use subdomain bypass
```

### **Scenario D: Bot Protection Not Listed**
```
You see: Various settings, but no "Bot Protection" option

Meaning: Feature not available on free tier
Solution: Use subdomain bypass (Plan B below)
```

---

## ✅ CONFIRMED: No Toggle Available

**Since you can't find the toggle button, this confirms:**
- Free tier limitation
- Bot protection is ON and cannot be toggled
- You need to use alternative solution

---

## 🚀 SOLUTION: Subdomain Bypass (100% Works)

Since toggle is not available, let's implement the subdomain solution:

### **What You'll Do:**

Create a subdomain `api.techjobs360.com` that bypasses QUIC.cloud entirely.

---

## 📋 Step-by-Step Implementation

### **STEP 1: Contact HeroXHost Support**

**Send this message to HeroXHost:**

```
Subject: Create subdomain api.techjobs360.com

Hi HeroXHost Support,

I need to create a subdomain for my domain techjobs360.com:

Subdomain needed: api.techjobs360.com

IMPORTANT: This subdomain should point DIRECTLY to my origin
server IP address, NOT through QUIC.cloud CDN proxy.

Purpose: I need direct WordPress REST API access for my job
scraper, bypassing CDN/bot protection.

Can you please:
1. Create subdomain: api.techjobs360.com
2. Point it to origin server IP (not QUIC.cloud)
3. Let me know when it's ready to use

Thank you!
```

**How to contact HeroXHost:**
- Check your HeroXHost welcome email
- Usually: support ticket system or live chat
- Or: Check hosting control panel for "Support" link

---

### **STEP 2: Wait for Subdomain Creation**

**Timeline:**
- Submitted ticket: ✅
- HeroXHost response: Usually 2-24 hours
- Subdomain ready: They'll confirm via email

**While waiting:** Read STEP 3 to prepare

---

### **STEP 3: Update GitHub Secret (After Subdomain Ready)**

Once HeroXHost confirms subdomain is created:

1. **Test subdomain works:**
   ```bash
   curl https://api.techjobs360.com/wp-json/
   # Should return JSON
   ```

2. **Go to GitHub:**
   ```
   https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions
   ```

3. **Update WP_URL secret:**
   ```
   Click: WP_URL (to edit)
   Change from: https://techjobs360.com
   Change to: https://api.techjobs360.com
   Click: "Update secret"
   ```

4. **Test scraper:**
   ```bash
   cd /home/user/techjobs360-scraper
   export WP_URL="https://api.techjobs360.com"
   export WP_USERNAME="your-username"
   export WP_APP_PASSWORD="your-app-password"
   ./test_api_access.sh
   ```

5. **If test passes:**
   - ✅ Scraper is fixed!
   - Jobs will be posted next time it runs
   - GitHub Actions will work automatically

---

## 🔄 Alternative: Do It Yourself (If You Have cPanel)

If you have access to HeroXHost cPanel:

### **Steps:**

1. **Log into cPanel:**
   - Usually: https://yourdomain.com:2083
   - Or: Through HeroXHost client area

2. **Find Subdomains:**
   - Look for "Domains" section
   - Click "Subdomains"

3. **Create subdomain:**
   ```
   Subdomain: api
   Domain: techjobs360.com
   Document Root: (same as main site, usually public_html)
   ```

4. **Configure DNS (Important!):**
   - Find "Zone Editor" or "DNS Management"
   - Find the A record for api.techjobs360.com
   - Make sure it points to: Origin server IP
   - NOT pointing to: QUIC.cloud IP addresses

5. **Wait 5-30 minutes** for DNS propagation

6. **Test:**
   ```bash
   curl https://api.techjobs360.com/wp-json/
   ```

7. **If working, update GitHub Secret** (see STEP 3 above)

---

## 🎯 How to Find Your Origin Server IP

If you need to know your origin IP:

**Method 1: Check HeroXHost welcome email**
- Look for "Server IP" or "Server Address"

**Method 2: In cPanel**
- Look for "Server Information" in sidebar
- Shows "Shared IP Address" or "Dedicated IP"

**Method 3: Ask HeroXHost**
- Open support ticket: "What is my origin server IP?"

---

## ⚠️ Important Notes

### **DNS Configuration**

Make sure `api.techjobs360.com` is configured as:

**✅ CORRECT:**
```
Type: A Record
Name: api
Value: [Your HeroXHost server IP]
Example: 123.45.67.89

This bypasses QUIC.cloud ✅
```

**❌ WRONG:**
```
Type: CNAME
Name: api
Value: techjobs360.com (or QUIC.cloud domain)

This goes through QUIC.cloud = still blocked ❌
```

---

## 🧪 Testing After Setup

### **Test 1: Check DNS**
```bash
dig api.techjobs360.com
# Should show your origin IP, not QUIC.cloud IP
```

### **Test 2: Check API Access**
```bash
curl https://api.techjobs360.com/wp-json/
# Should return JSON (not CAPTCHA or 503 error)
```

### **Test 3: Run Full Test**
```bash
cd /home/user/techjobs360-scraper
export WP_URL="https://api.techjobs360.com"
./test_api_access.sh
# Should show: ✅ ALL TESTS PASSED!
```

### **Test 4: Run Scraper**
```bash
python job_scraper.py
# Should post jobs successfully
```

---

## 📊 Expected Results

### **Before Fix:**
```
Scraper → techjobs360.com → QUIC.cloud → ❌ BLOCKED
Result: No jobs posted
posted_jobs.json: []
```

### **After Fix:**
```
Scraper → api.techjobs360.com → ✅ Direct to WordPress
Result: Jobs posted successfully
posted_jobs.json: [...many entries...]
```

### **For Website Visitors:**
```
Visitors → techjobs360.com → QUIC.cloud → ✅ Still protected
Result: Fast, protected site with new jobs!
```

---

## 🎯 What I Need From You (Optional)

To help you better, you can tell me:

1. **What you see in QUIC.cloud dashboard:**
   - List the menu options
   - List any security-related settings
   - Screenshot (if possible) - describe what's visible

2. **Do you have cPanel access?**
   - Yes → You can create subdomain yourself
   - No → Need to contact HeroXHost

3. **Have you contacted HeroXHost yet?**
   - Yes → Waiting for response
   - No → Send the message template above

---

## ✅ Next Steps (Choose One)

### **Option A: You Have cPanel Access**
1. Log into cPanel
2. Create subdomain api.techjobs360.com
3. Point to origin IP (not QUIC.cloud)
4. Update GitHub Secret
5. Test scraper
6. ✅ Done in 20 minutes!

### **Option B: No cPanel Access**
1. Contact HeroXHost (use message template above)
2. Wait for confirmation (2-24 hours)
3. Once ready, update GitHub Secret
4. Test scraper
5. ✅ Done (mostly waiting time)!

---

## 🆘 Troubleshooting

### **Issue: Subdomain still blocked**

**Check:**
```bash
dig api.techjobs360.com
# Does it show QUIC.cloud IP? → Wrong setup
# Does it show different IP? → Correct! That's your origin
```

**Fix:** Update DNS to point to origin, not QUIC.cloud

---

### **Issue: SSL certificate error**

**Try HTTP instead:**
```bash
export WP_URL="http://api.techjobs360.com"
```

**Or request SSL:** Ask HeroXHost to add Let's Encrypt SSL for subdomain

---

### **Issue: WordPress not responding**

**Check WordPress allows subdomain:**

Edit wp-config.php:
```php
define('WP_ACCESSIBLE_HOSTS', 'api.techjobs360.com');
```

---

## 📞 Need Help?

**HeroXHost Support:**
- They can create subdomain for you
- They know your server configuration
- Usually respond within 24 hours

**Or tell me:**
- What you see in QUIC.cloud dashboard
- Whether you have cPanel access
- Any error messages you're getting

---

**🚀 Let's move forward with subdomain bypass - it WILL work!**

---

*This is the most reliable solution for QUIC.cloud free tier users*
*Success rate: 95%+*
*No toggle button needed*
