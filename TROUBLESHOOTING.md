# TechJobs360 Scraper - Troubleshooting Guide

## 🔍 Quick Diagnosis

**Run this first:**
```bash
python diagnose.py
```

This diagnostic tool will automatically check:
- ✅ Environment variables
- ✅ WordPress connection
- ✅ Job source APIs
- ✅ Configuration settings
- ✅ Deduplication database

---

## ❓ Common Issue: "Jobs Not Appearing on Website"

### Possible Causes & Solutions

#### 1. ❌ WordPress Credentials Not Set

**Symptoms:** No jobs posted, no errors visible

**Check:**
```bash
# For local/manual runs
echo $WP_URL
echo $WP_USERNAME
echo $WP_APP_PASSWORD

# For GitHub Actions
# Go to: Settings → Secrets → Actions
# Verify these secrets exist:
# - WP_URL
# - WP_USERNAME
# - WP_APP_PASSWORD
```

**Fix:**
```bash
# Local runs
export WP_URL="https://your-site.com"
export WP_USERNAME="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# GitHub Actions
# Add secrets via: Settings → Secrets and variables → Actions → New repository secret
```

#### 2. ⚠️ Posts Created as "DRAFT" Instead of "PUBLISH"

**Symptoms:** Jobs collected but not visible on site

**Check:**
```bash
grep "post_status" config.yaml
```

**Fix:**
```yaml
# Edit config.yaml
posting:
  post_status: publish  # Change from 'draft' to 'publish'
```

#### 3. 🔒 WordPress REST API Disabled

**Symptoms:** Authentication errors, 403/404 errors

**Test:**
```bash
curl https://your-site.com/wp-json/wp/v2
```

**Fix:**
1. Login to WordPress admin
2. Go to Settings → Permalinks
3. Click "Save Changes" (even without changes) - this resets REST API
4. If still blocked, check with hosting provider about REST API access

#### 4. 🔑 Invalid Application Password

**Symptoms:** 401 Unauthorized errors

**Fix:**
1. WordPress admin → Users → Your Profile
2. Scroll to "Application Passwords"
3. Create new password
4. Copy the password (format: `xxxx xxxx xxxx xxxx`)
5. Update your environment variable/secret

#### 5. 📊 All Jobs Already in Deduplication Database

**Symptoms:** Scraper runs successfully but no new jobs posted

**Check:**
```bash
# View database size
jq 'length' posted_jobs.json

# Check latest entries
jq '.[-10:] | .[] | {title, first_seen}' posted_jobs.json
```

**Fix:**
```bash
# Option 1: Clear old entries (keeps last 30 days)
jq 'map(select(.first_seen > (now - 2592000)))' posted_jobs.json > temp.json
mv temp.json posted_jobs.json

# Option 2: Clear all (fresh start)
echo "[]" > posted_jobs.json
```

#### 6. 🌐 GitHub Actions Not Running

**Symptoms:** No automatic updates

**Check:**
1. Go to repository → Actions tab
2. Check if workflow runs are visible
3. Check if any runs failed

**Fix:**
```bash
# Ensure workflow file is in correct location
ls -la .github/workflows/scraper.yml

# Manually trigger workflow
gh workflow run scraper.yml

# Or via GitHub UI:
# Actions → TechJobs360 FREE Scraper → Run workflow
```

#### 7. 🚫 API Rate Limiting

**Symptoms:** Empty job lists, 429 errors in logs

**Fix:**
```yaml
# Edit config.yaml - increase pause times
continents:
  - id: asia
    pause_seconds: 5  # Increase from 2 to 5
```

#### 8. 🔐 Missing API Keys

**Symptoms:** Only free sources work, JSearch returns no jobs

**Fix:**
```bash
# Set JSearch API key (optional)
export JSEARCH_API_KEY="your-rapidapi-key"

# Or for GitHub Actions:
# Settings → Secrets → Actions → New secret
# Name: JSEARCH_API_KEY
# Value: your-key
```

---

## 🔧 Step-by-Step Debugging Process

### Step 1: Run Diagnostic Tool
```bash
python diagnose.py
```
This will identify most common issues automatically.

### Step 2: Test WordPress Connection Manually
```bash
# Test API availability
curl https://your-site.com/wp-json/wp/v2

# Test authentication
curl -u "username:app-password" \
     https://your-site.com/wp-json/wp/v2/users/me
```

### Step 3: Run Scraper with Debug Logging
```bash
# Edit job_scraper.py line 51
# Change: level=logging.INFO
# To: level=logging.DEBUG

# Run scraper
python job_scraper.py

# Check output for detailed error messages
```

### Step 4: Test Individual Job Sources
```python
# Run Python interactively
python3

# Test each source
from job_scraper import query_remotive, query_arbeitnow, query_jobicy

jobs = query_remotive("python", limit=5)
print(f"Remotive: {len(jobs)} jobs")

jobs = query_arbeitnow("engineer", limit=5)
print(f"Arbeitnow: {len(jobs)} jobs")

jobs = query_jobicy("developer", limit=5)
print(f"Jobicy: {len(jobs)} jobs")
```

### Step 5: Check WordPress Posts
```bash
# List recent posts via API
curl -u "username:app-password" \
     "https://your-site.com/wp-json/wp/v2/posts?per_page=5&status=publish"

# List draft posts (if post_status was draft)
curl -u "username:app-password" \
     "https://your-site.com/wp-json/wp/v2/posts?per_page=5&status=draft"
```

---

## 📝 Error Message Reference

### Error: "Missing config.yaml"
**Cause:** Configuration file not found
**Fix:** Ensure `config.yaml` exists in repository root

### Error: "JSearch returned 403"
**Cause:** Invalid or missing API key
**Fix:** Check JSEARCH_API_KEY environment variable

### Error: "WP media upload failed"
**Cause:** WordPress REST API issues or permissions
**Fix:**
1. Check WordPress user has permission to upload media
2. Verify REST API is enabled
3. Check file upload limits in WordPress

### Error: "Cannot connect to WordPress"
**Cause:** Network issue or invalid URL
**Fix:**
1. Verify WP_URL is correct (include https://)
2. Check if WordPress site is accessible
3. Verify firewall/security plugins aren't blocking requests

### Warning: "No new jobs posted"
**Cause:** All jobs already in deduplication database
**Fix:** Wait for new jobs to appear on sources, or clear dedup database

### Warning: "Source 'X' is not implemented"
**Cause:** Typo in config.yaml or unsupported source
**Fix:** Check spelling in config.yaml, ensure source is in: jsearch, remotive, remoteok, arbeitnow, jobicy, himalayas, weworkremotely, indeed, linkedin

---

## 🏥 Health Check Checklist

Run through this checklist to ensure everything is working:

- [ ] `python diagnose.py` passes all checks
- [ ] WordPress site is accessible
- [ ] WordPress REST API is enabled (`curl https://your-site.com/wp-json/wp/v2`)
- [ ] WordPress credentials work (`curl -u user:pass https://your-site.com/wp-json/wp/v2/users/me`)
- [ ] config.yaml has `post_status: publish`
- [ ] At least one job source is enabled in config.yaml
- [ ] GitHub Actions workflow runs successfully (check Actions tab)
- [ ] Environment variables are set (local) or secrets configured (GitHub)
- [ ] No firewall/security plugins blocking REST API
- [ ] Deduplication database isn't too full (< 5000 entries)

---

## 🆘 Still Having Issues?

### Collect Diagnostic Information

```bash
# 1. Run diagnostic tool
python diagnose.py > diagnostic_output.txt 2>&1

# 2. Get recent logs
# For GitHub Actions: Download logs from Actions tab
# For Heroku: heroku logs -n 500 > heroku_logs.txt

# 3. Check configuration
cat config.yaml > config_snapshot.txt

# 4. Check environment
env | grep -E "(WP_|JSEARCH|PROCESS|AUTO)" > env_vars.txt
```

### Get Help

1. **Check existing issues:** https://github.com/arunbabusb/techjobs360-scraper/issues
2. **Create new issue** with:
   - Diagnostic output
   - Error messages
   - Configuration (remove sensitive data!)
   - Steps to reproduce

### Emergency Quick Fix

If you need jobs posted immediately:

```bash
# 1. Clear deduplication database
echo "[]" > posted_jobs.json

# 2. Set to publish mode
# Edit config.yaml: post_status: publish

# 3. Process just one city
export PROCESS_CONTINENT="asia"
export AUTO_ROTATE="false"

# 4. Run manually
python job_scraper.py

# 5. Check WordPress site for new posts
```

---

## 🎯 Performance Optimization

### Issue: Scraper Taking Too Long

**Solution 1: Reduce number of cities**
```yaml
# Edit config.yaml - comment out some cities
locales:
  - city: Bengaluru
    query: software engineer
  # - city: Mumbai  # Disabled temporarily
  # - city: Hyderabad  # Disabled temporarily
```

**Solution 2: Reduce job limits**
```yaml
sources:
  - type: remotive
    limit: 20  # Reduce from 60
  - type: remoteok
    limit: 30  # Reduce from 80
```

**Solution 3: Process one continent at a time**
```bash
export PROCESS_CONTINENT="asia"
```

### Issue: Getting Rate Limited

**Solution 1: Increase delays**
```yaml
continents:
  - id: asia
    pause_seconds: 5  # Increase from 2
```

**Solution 2: Disable aggressive sources temporarily**
```yaml
sources:
  - type: remoteok
    enabled: false  # Disable temporarily
```

---

## 📊 Monitoring Best Practices

### Daily Checks
- Check WordPress site for new jobs
- Review GitHub Actions status (if using)

### Weekly Checks
- Review deduplication database size
- Check for failed workflow runs
- Verify API rate limits not exceeded

### Monthly Maintenance
- Prune old jobs from deduplication database
- Update Python dependencies
- Review and optimize configuration

---

**Last Updated:** 2025-11-21
