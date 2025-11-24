# 🔧 QUIC.cloud Bot Protection - Toggle OFF Guide

**Last Updated**: 2025-11-24
**Domain**: techjobs360.com
**Purpose**: Temporarily disable bot protection to allow scraper access

---

## 🎯 Quick Answer: Where to Toggle Bot Protection OFF

### Login First
- **URL**: https://my.quic.cloud/
- **Email**: chessgenius900@gmail.com
- **Password**: Qsharper$1000

---

## 📍 Finding the Bot Protection Toggle

### Method 1: Via Domain Settings (Most Common)

```
1. Log into QUIC.cloud dashboard
2. Click "Domains" (left sidebar)
3. Click "techjobs360.com"
4. Look for tabs at the top:
   - "CDN"
   - "Security" ← Click this
   - "Cache"
   - "Settings"
5. Under Security tab, find:
   - "Bot Protection" section
   - Toggle switch (ON/OFF)
6. Click toggle to turn OFF
7. Click "Save Changes"
8. Click "Purge All" to clear cache
```

---

### Method 2: Via Security Menu

```
1. Log into QUIC.cloud dashboard
2. Click "Security" in main navigation
3. Find "Bot Protection" or "Bot Manager"
4. Options you might see:
   - "Enabled" / "Disabled" toggle
   - "Challenge Level" dropdown (set to "Off")
   - "Protection Mode" (select "Monitor Only" or "Disabled")
5. Save changes
6. Purge cache
```

---

### Method 3: Via Firewall Rules

```
1. Log into QUIC.cloud dashboard
2. Click "Firewall" or "WAF"
3. Look for existing rules
4. Find rule named:
   - "Bot Protection"
   - "Challenge Bots"
   - "Bot Detection"
5. Either:
   - Click "Disable" button
   - OR Click "Delete" to remove rule
6. Confirm changes
7. Purge cache
```

---

## 🖼️ Visual Guide: What to Look For

### Expected Screen Layout:

```
┌─────────────────────────────────────────┐
│ QUIC.cloud Dashboard                    │
├─────────────────────────────────────────┤
│ ☰ Menu                                  │
│   • Dashboard                           │
│   • Domains  ← Click here first        │
│   • Security                            │
│   • Firewall                            │
│   • CDN                                 │
└─────────────────────────────────────────┘

After clicking Domains → techjobs360.com:

┌─────────────────────────────────────────┐
│ techjobs360.com                         │
├─────────────────────────────────────────┤
│ [CDN] [Security] [Cache] [Settings]     │
│         ↑                               │
│    Click Security tab                   │
└─────────────────────────────────────────┘

Security Tab Contents:

┌─────────────────────────────────────────┐
│ Security Settings                       │
├─────────────────────────────────────────┤
│                                         │
│ 🛡️ Bot Protection                       │
│ ┌─────────────────────────────────┐    │
│ │ Status: [🟢 ON] ← Toggle this   │    │
│ │                                 │    │
│ │ Challenge bots before allowing  │    │
│ │ access to your site             │    │
│ │                                 │    │
│ │ [Settings] [Whitelist]          │    │
│ └─────────────────────────────────┘    │
│                                         │
│ [Save Changes]                          │
└─────────────────────────────────────────┘
```

---

## 🔍 Alternative: Look for These Keywords

While navigating QUIC.cloud, search or look for:

- ✅ "Bot Protection"
- ✅ "Bot Manager"
- ✅ "Bot Detection"
- ✅ "Challenge"
- ✅ "CAPTCHA"
- ✅ "JavaScript Challenge"
- ✅ "Security Level"
- ✅ "WAF" (Web Application Firewall)
- ✅ "DDoS Protection"

---

## ⚠️ What If You Can't Find It?

### Scenario 1: QUIC.cloud Interface Changed

If the interface looks different:

1. Use the **search bar** (usually top-right)
2. Search for: "bot" or "protection" or "security"
3. Click on relevant results

### Scenario 2: Bot Protection Not Visible

Possible reasons:
- ✅ Bot protection may not be enabled (already off)
- ✅ Feature may be under different name
- ✅ May be controlled by hosting provider (HeroXHost)

**Solution**: Contact QUIC.cloud support:
- Email: support@quic.cloud
- Subject: "Disable bot protection for techjobs360.com"

### Scenario 3: Need to Whitelist Instead

If you prefer to keep bot protection ON:

1. Find **"Whitelist"** or **"IP Allowlist"** section
2. Add GitHub Actions IP ranges (see github-actions-ips.txt)
3. Save changes

---

## ✅ How to Verify Bot Protection is OFF

### Test 1: Check REST API (No CAPTCHA)

```bash
curl -i https://techjobs360.com/wp-json/
```

**Expected if OFF**:
```
HTTP/2 200 OK
Content-Type: application/json

{
  "name": "TechJobs360",
  "description": "...",
  ...
}
```

**If still ON (blocked)**:
```
HTTP/2 403 Forbidden
Content-Type: text/html

<!DOCTYPE html>
<html>
  <head>
    <title>QUIC.cloud Bot Protection</title>
    ...CAPTCHA challenge...
```

---

### Test 2: Visit Site in Browser

1. Open: https://techjobs360.com/
2. **If bot protection OFF**: Site loads immediately
3. **If bot protection ON**: See "Verifying you are not a robot..." page

---

### Test 3: Check from GitHub Actions

Run this workflow manually:
1. Go to: https://github.com/arunbabusb/techjobs360-scraper/actions
2. Click: **diag-auth.yml** (diagnostic workflow)
3. Click: **Run workflow**
4. Check logs for success or CAPTCHA error

---

## 🚀 After Toggling OFF

### Immediate Next Steps:

1. **Clear browser cache**:
   - Press `Ctrl+Shift+Delete` (Chrome/Firefox)
   - Clear browsing data

2. **Wait 2-3 minutes** for QUIC.cloud changes to propagate

3. **Test REST API** (see Test 1 above)

4. **Run scraper manually**:
   ```bash
   # From repository directory
   python job_scraper.py
   ```

   Or trigger GitHub Actions:
   - Go to Actions tab
   - Run scraper.yml workflow

5. **Verify jobs posted**:
   - Check: https://techjobs360.com/wp-admin/edit.php
   - Should see new job posts

---

## 🔄 Re-enabling Bot Protection (Later)

### When to Re-enable:

- ✅ After confirming scraper works
- ✅ After implementing IP whitelisting
- ✅ When using bypass rules for /wp-json/* paths

### How to Re-enable:

1. Return to same settings location
2. Toggle bot protection back **ON**
3. Ensure whitelisting/bypass rules are configured first
4. Test scraper still works

---

## 🛠️ Troubleshooting

### Problem: Can't log into QUIC.cloud

**Solution 1**: Password reset
- Go to: https://my.quic.cloud/forgot-password
- Enter: chessgenius900@gmail.com
- Check email for reset link

**Solution 2**: Contact hosting provider
- HeroXHost may have set up QUIC.cloud
- They may have admin access
- Contact HeroXHost support

---

### Problem: Bot protection toggle is grayed out

**Possible reasons**:
- Setting controlled by hosting provider
- Need higher permission level
- Feature disabled at plan level

**Solutions**:
- Contact QUIC.cloud support
- Contact HeroXHost (hosting provider)
- Ask them to disable bot protection for techjobs360.com

---

### Problem: Changes not taking effect

**Checklist**:
- [ ] Clicked "Save Changes" button?
- [ ] Purged/cleared all caches?
- [ ] Waited 3-5 minutes?
- [ ] Tested in incognito/private browser?
- [ ] Cleared DNS cache (`ipconfig /flushdns` on Windows)?

---

## 📞 Support Contacts

### QUIC.cloud Support
- **Email**: support@quic.cloud
- **Dashboard**: https://my.quic.cloud/
- **Response time**: 1-2 business days

### HeroXHost Support (Hosting Provider)
- **Website**: https://heroxhost.com/
- **May have access to QUIC.cloud settings**

---

## 📋 Quick Checklist

Before starting:
- [ ] Have QUIC.cloud login credentials ready
- [ ] Know domain name: techjobs360.com
- [ ] Have this guide open for reference

During the process:
- [ ] Log into QUIC.cloud
- [ ] Find Security or Bot Protection section
- [ ] Toggle bot protection to OFF
- [ ] Save changes
- [ ] Purge/clear cache
- [ ] Wait 2-3 minutes

After toggling OFF:
- [ ] Test REST API with curl command
- [ ] Run scraper manually or via GitHub Actions
- [ ] Verify jobs are posted to WordPress
- [ ] Check posted_jobs.json for new entries

---

## 🎯 Expected Outcome

### Before (Bot Protection ON):
```
curl https://techjobs360.com/wp-json/
→ Returns CAPTCHA challenge page (HTML)
→ Scraper fails with 403 errors
→ No jobs posted
```

### After (Bot Protection OFF):
```
curl https://techjobs360.com/wp-json/
→ Returns JSON API response
→ Scraper successfully authenticates
→ Jobs posted to WordPress
→ posted_jobs.json updated
```

---

## 💡 Pro Tips

1. **Screenshot settings** before and after changing
2. **Document which menu path you used** for future reference
3. **Test immediately** after making changes
4. **Keep bot protection OFF temporarily** until IP whitelisting is configured
5. **Plan to re-enable** with proper bypass rules for long-term security

---

## 🔗 Related Documentation

- **Full Status Report**: PROJECT_STATUS_REPORT.md
- **Bot Protection Fix Guide**: BOT_PROTECTION_FIX.md
- **GitHub Actions IPs**: github-actions-ips.txt
- **Simple Fix Steps**: SIMPLE_FIX_STEPS.md

---

**🚀 Ready? Log into QUIC.cloud and find that toggle!**

---

*Created: 2025-11-24*
*Part of TechJobs360 Scraper Project*
*Questions? See CLAUDE.md for assistance*
