# 🤖 QUIC.cloud Bot Protection Fix - Quick Guide

**Problem**: Scraper is blocked by QUIC.cloud bot protection showing CAPTCHA challenges

**Solution**: Whitelist GitHub Actions IPs or bypass bot protection for REST API

---

## ⚡ Quick Fix (Choose One)

### **Option A: Whitelist GitHub Actions IPs** ⭐ RECOMMENDED

**Time**: 15 minutes | **Difficulty**: Medium | **Security**: ✅ Secure

1. **Get GitHub Actions IP ranges:**
```bash
curl -s https://api.github.com/meta | jq -r '.actions[]'
```

Current ranges (as of Nov 2025 - verify above):
```
4.175.0.0/16
13.64.0.0/16
13.65.0.0/16
13.66.0.0/16
13.68.0.0/16
13.69.0.0/16
13.70.0.0/16
13.71.0.0/16
13.72.0.0/16
13.73.0.0/16
13.74.0.0/16
13.75.0.0/16
... (50+ ranges total)
```

2. **Log into QUIC.cloud:**
   - URL: https://my.quic.cloud/
   - Email: chessgenius900@gmail.com
   - Password: Qsharper$1000

3. **Navigate to Security Settings:**
   - Click: **Domains** → **techjobs360.com**
   - Look for: **Security**, **Firewall**, **Bot Protection**, or **WAF**
   - Click to open settings

4. **Add IP Allowlist:**
   - Find: **IP Whitelist**, **Allowed IPs**, **Bypass Rules**, or **Firewall Rules**
   - Click: **Add Rule** or **Add IP Range**
   - Name: `GitHub Actions`
   - IPs: Paste GitHub Actions ranges (one per line or as CIDR blocks)
   - Action: **Allow** or **Bypass Bot Protection**
   - Apply to: **All requests** or **API requests**
   - Save

5. **Test immediately:**
```bash
curl -i https://techjobs360.com/wp-json/
# Should return JSON (200 OK), not CAPTCHA page
```

---

### **Option B: Bypass Bot Protection for REST API**

**Time**: 10 minutes | **Difficulty**: Easy | **Security**: ⚠️ Moderate

1. **Log into QUIC.cloud** (same as above)

2. **Create Page Rule:**
   - Navigate to: **Page Rules** or **Cache Rules**
   - Click: **Add Rule**
   - URL Pattern: `techjobs360.com/wp-json/*`
   - Settings:
     - ✅ **Bypass Cache**: On
     - ✅ **Bypass Security**: On
     - ✅ **Bot Protection**: Off
     - Or: **Direct to Origin** (bypasses CDN entirely)
   - Save

3. **Clear Cache:**
   - Find: **Purge Cache** or **Clear Cache**
   - Click: **Purge All**
   - Wait 2-3 minutes

4. **Test:**
```bash
curl -i https://techjobs360.com/wp-json/
# Should return JSON without CAPTCHA
```

---

### **Option C: Temporarily Disable Bot Protection**

**Time**: 5 minutes | **Difficulty**: Easy | **Security**: ⚠️ Low (temporary only)

⚠️ **WARNING**: This removes bot protection from entire site. Use only for testing.

1. **Log into QUIC.cloud**

2. **Disable Bot Protection:**
   - Navigate to: **Security** → **Bot Protection**
   - Toggle: **Off** or **Disabled**
   - Or: Set to **Low** or **Monitor Only**
   - Save

3. **Wait 2-3 minutes for propagation**

4. **Test scraper immediately**

5. **❗ IMPORTANT**: Re-enable bot protection after confirming scraper works

---

## 🔍 Verify the Fix

### Test 1: REST API Access
```bash
# Should return JSON (not CAPTCHA)
curl https://techjobs360.com/wp-json/

# Expected output:
# {
#   "name": "TechJobs360",
#   "description": "...",
#   "url": "https://techjobs360.com",
#   ...
# }
```

### Test 2: Authenticated API Call
```bash
# Replace with your actual credentials
curl -u "USERNAME:APP_PASSWORD" https://techjobs360.com/wp-json/wp/v2/users/me

# Expected output:
# {
#   "id": 1,
#   "name": "...",
#   "email": "...",
#   ...
# }
```

### Test 3: Run Scraper Manually
1. Go to: https://github.com/arunbabusb/techjobs360-scraper/actions
2. Click: **scraper.yml** workflow
3. Click: **Run workflow** button
4. Select branch: `main`
5. Click: **Run workflow**
6. Monitor execution logs

**Expected result**: ✅ Workflow completes successfully, jobs posted to WordPress

---

## 📊 How to Verify Success

### 1. Check posted_jobs.json
```bash
# In repository root
cat posted_jobs.json | jq '. | length'
# Should show number > 0
```

### 2. Check WordPress Admin
- Visit: https://techjobs360.com/wp-admin/edit.php
- Should see new job posts with recent dates
- Verify job details (title, company, description)

### 3. Check Public Site
- Visit: https://techjobs360.com/
- Should see job listings on homepage
- Jobs should be recent (within hours)

### 4. Check GitHub Actions
- Visit: https://github.com/arunbabusb/techjobs360-scraper/actions
- Should see green checkmarks ✅ on recent runs
- No red X failures ❌

---

## 🚨 Troubleshooting

### Still getting CAPTCHA after whitelisting IPs?

**Possible causes:**
1. IP ranges not saved properly
2. Cache not cleared
3. Rule not applied to correct domain
4. Wrong security setting modified

**Solutions:**
- Double-check IP allowlist is saved
- Purge all caches in QUIC.cloud
- Wait 5-10 minutes for propagation
- Try Option B (bypass REST API) instead

---

### GitHub Actions still failing?

**Check these:**

1. **Secrets are set correctly:**
   - Go to: Settings → Secrets and variables → Actions
   - Verify: `WP_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`

2. **WP_URL has proper scheme:**
   ```
   ✅ https://techjobs360.com
   ❌ techjobs360.com (missing https://)
   ```

3. **Application Password is correct:**
   - Should be format: `xxxx xxxx xxxx xxxx`
   - Spaces are important
   - Generate new one if unsure

4. **WordPress REST API is enabled:**
   ```bash
   curl -i https://techjobs360.com/wp-json/
   # Should return 200 OK, not 404
   ```

---

### Bot protection keeps getting re-enabled?

**Some CDNs auto-enable protection:**
- Check if QUIC.cloud has "Auto Bot Protection" feature
- Look for DDoS protection settings
- May need to disable automatic security features

---

## 📋 Checklist

Before you start:
- [ ] Have QUIC.cloud login credentials ready
- [ ] Know which option to use (A, B, or C)
- [ ] Have GitHub Actions IP ranges ready (if Option A)

During fix:
- [ ] Log into QUIC.cloud dashboard
- [ ] Locate bot protection / security settings
- [ ] Apply chosen solution (A, B, or C)
- [ ] Save changes
- [ ] Purge all caches
- [ ] Wait 2-5 minutes

After fix:
- [ ] Test REST API (curl command)
- [ ] Run scraper workflow manually
- [ ] Check workflow logs for success
- [ ] Verify jobs posted to WordPress
- [ ] Check posted_jobs.json updated

---

## 🎯 Expected Timeline

| Step | Time | Total |
|------|------|-------|
| Get IP ranges | 2 min | 2 min |
| Log into QUIC.cloud | 2 min | 4 min |
| Configure allowlist | 5 min | 9 min |
| Save & purge cache | 2 min | 11 min |
| Wait for propagation | 3 min | 14 min |
| Test & verify | 5 min | **19 min** |

**Total time to fix**: ~20 minutes

---

## 💡 Pro Tips

1. **Save GitHub Actions IP ranges:**
   - Keep them in a text file for future reference
   - GitHub may update ranges occasionally
   - Check quarterly: `https://api.github.com/meta`

2. **Document your changes:**
   - Screenshot QUIC.cloud settings after configuration
   - Save rule names/IDs for future reference
   - Note which option you chose (A, B, or C)

3. **Monitor after fix:**
   - Check scraper runs for next few days
   - Verify no jobs are skipped
   - Watch for any new CAPTCHA challenges

4. **Consider self-hosted runner:**
   - If IP whitelisting becomes problematic
   - Use dedicated server with static IP
   - Whitelist single IP instead of ranges

---

## 🔗 Related Documentation

- **Full Status Report**: PROJECT_STATUS_REPORT.md
- **QUIC.cloud SSL Fix**: QUIC_CLOUD_FIX.md
- **Simple Fix Steps**: SIMPLE_FIX_STEPS.md
- **Support Request Template**: QUIC_CLOUD_SUPPORT_REQUEST.txt

---

## 📞 Need Help?

### QUIC.cloud Support
- **Email**: support@quic.cloud
- **Dashboard**: https://my.quic.cloud/
- **Response Time**: Usually 1-2 business days

### GitHub Actions
- **Documentation**: https://docs.github.com/actions
- **IP Ranges**: https://api.github.com/meta

### WordPress REST API
- **Docs**: https://developer.wordpress.org/rest-api/
- **Authentication**: https://developer.wordpress.org/rest-api/using-the-rest-api/authentication/

---

**🚀 Ready to fix it? Start with Option A (IP Whitelisting) above!**

---

*Last Updated: 2025-11-23*
*Part of TechJobs360 Scraper project*
