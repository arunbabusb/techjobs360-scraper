# 🚀 TechJobs360 Quick Start Guide

Get jobs flowing to your WordPress site in **5 minutes**!

---

## ⚡ **Option 1: Test Locally First (RECOMMENDED)**

This verifies everything works before setting up automation.

### **Step 1: Get WordPress Application Password**

1. Login to your WordPress admin panel
2. Go to: **Users → Your Profile**
3. Scroll down to: **Application Passwords**
4. Enter application name: `TechJobs360`
5. Click: **Add New Application Password**
6. **Copy the password** (format: `xxxx xxxx xxxx xxxx`)
7. Save it somewhere safe

### **Step 2: Set Environment Variables**

```bash
# Navigate to project directory
cd techjobs360-scraper

# Set credentials (replace with your actual values)
export WP_URL="https://your-wordpress-site.com"
export WP_USERNAME="your-wp-admin-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# Optional: Set JSearch API key (if you have one)
export JSEARCH_API_KEY="your-rapidapi-key"
```

### **Step 3: Run Automated Setup**

```bash
# Make script executable
chmod +x setup_and_test.sh

# Run setup and test
bash setup_and_test.sh
```

This will:
- ✅ Check your credentials
- ✅ Install dependencies
- ✅ Test WordPress connection
- ✅ Test all job sources
- ✅ Run scraper for one continent (test mode)
- ✅ Show you the results

### **Step 4: Check Your WordPress Site**

Go to: `https://your-site.com/wp-admin/edit.php?post_type=post`

You should see new job posts! 🎉

---

## 🤖 **Option 2: GitHub Actions (Automated - FREE)**

Once local testing works, set up automated runs.

### **Step 1: Add GitHub Secrets**

1. Go to your repository on GitHub
2. Click: **Settings** → **Secrets and variables** → **Actions**
3. Click: **New repository secret**
4. Add these three secrets:

| Secret Name | Value | Example |
|-------------|-------|---------|
| `WP_URL` | Your WordPress URL | `https://techjobs360.com` |
| `WP_USERNAME` | WordPress username | `admin` |
| `WP_APP_PASSWORD` | Application password from Step 1 | `xxxx xxxx xxxx xxxx` |

**Optional secrets:**
- `JSEARCH_API_KEY` - If you have RapidAPI key
- `PROCESS_CONTINENT` - To limit to one continent (e.g., `asia`)

### **Step 2: Trigger Workflow**

1. Go to: **Actions** tab
2. Select: **TechJobs360 FREE Scraper**
3. Click: **Run workflow** → **Run workflow**
4. Wait 2-5 minutes
5. Check workflow status (green = success)

### **Step 3: Verify Jobs on Website**

Check your WordPress site - new jobs should appear!

### **Automatic Schedule**

The workflow runs automatically **4 times daily**:
- 00:30 UTC (6:00 AM IST)
- 06:30 UTC (12:00 PM IST)
- 12:30 UTC (6:00 PM IST)
- 18:30 UTC (12:00 AM IST)

---

## ☁️ **Option 3: Deploy to Heroku**

For dedicated hosting with custom scheduling.

### **Quick Deployment (5 commands)**

```bash
# 1. Login to Heroku
heroku login

# 2. Create app (use your own name)
heroku create your-techjobs-scraper

# 3. Set credentials
heroku config:set WP_URL="https://your-site.com"
heroku config:set WP_USERNAME="your-username"
heroku config:set WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# 4. Deploy
git push heroku main

# 5. Test
heroku run python diagnose.py
heroku run python job_scraper.py
```

### **Set Up Scheduler**

```bash
# Add scheduler addon (FREE)
heroku addons:create scheduler:standard

# Open scheduler dashboard
heroku addons:open scheduler
```

In the dashboard:
1. Click: **Create job**
2. Command: `python job_scraper.py`
3. Frequency: **Every 3 hours** (recommended)
4. Click: **Save**

**Full Heroku guide:** See `HEROKU_DEPLOYMENT.md`

---

## 🔧 **Troubleshooting**

### **Issue: "No jobs appearing on website"**

Run diagnostics:
```bash
python diagnose.py
```

This will identify the problem and tell you how to fix it.

### **Issue: "Authentication failed"**

1. Verify WordPress Application Password is correct
2. Try creating a new Application Password
3. Ensure WordPress REST API is enabled

Test manually:
```bash
curl -u "username:app-password" \
     "https://your-site.com/wp-json/wp/v2/users/me"
```

### **Issue: "Jobs are drafts, not published"**

Edit `config.yaml`:
```yaml
posting:
  post_status: publish  # Change from 'draft'
```

### **Issue: "All jobs already exist (duplicates)"**

Clear deduplication database:
```bash
echo "[]" > posted_jobs.json
```

**Complete troubleshooting guide:** See `TROUBLESHOOTING.md`

---

## 📊 **Verify It's Working**

### **1. Check Logs (Local)**
```bash
# Run with debug logging
python job_scraper.py
```

Look for:
- `✅ Searching: ...`
- `✅ New jobs posted: X`

### **2. Check Logs (GitHub Actions)**
1. Go to: **Actions** tab
2. Click latest workflow run
3. Click: **Run FREE job scraper**
4. Check for errors

### **3. Check Logs (Heroku)**
```bash
heroku logs --tail
```

### **4. Check WordPress**
```bash
# Count published posts
curl "https://your-site.com/wp-json/wp/v2/posts?per_page=100" | jq 'length'

# List recent posts
curl "https://your-site.com/wp-json/wp/v2/posts?per_page=5" | jq '.[] | {title: .title.rendered, date}'
```

---

## 📈 **Expected Results**

### **First Run**
- ⏱️ Duration: 5-10 minutes
- 📊 Jobs collected: 50-200 (varies by sources)
- 📝 Jobs posted: Same as collected (first run)

### **Subsequent Runs**
- ⏱️ Duration: 2-5 minutes
- 📊 Jobs collected: 50-200
- 📝 Jobs posted: 5-50 (only new jobs, duplicates skipped)

### **Daily Average**
- 📅 4 runs per day (GitHub Actions)
- 📝 20-100 new jobs per day
- 🗑️ Old jobs pruned after 60 days

---

## 🎯 **Recommended Configuration**

For best results, use these settings in `config.yaml`:

```yaml
posting:
  post_status: publish  # Jobs visible immediately

sources:
  - type: remotive
    enabled: true
    limit: 60
  - type: remoteok
    enabled: true
    limit: 80
  - type: arbeitnow
    enabled: true
    limit: 50
  - type: jobicy
    enabled: true
    limit: 50

dedup:
  max_age_days: 60  # Keep jobs for 60 days
```

---

## 🆘 **Need Help?**

1. **Run diagnostics first:**
   ```bash
   python diagnose.py
   ```

2. **Check troubleshooting guide:**
   - See `TROUBLESHOOTING.md`

3. **Review logs:**
   - Local: Terminal output
   - GitHub: Actions tab → Workflow run
   - Heroku: `heroku logs --tail`

4. **Create GitHub issue:**
   - Include diagnostic output
   - Include error messages
   - Describe what you tried

---

## ✅ **Success Checklist**

- [ ] WordPress Application Password created
- [ ] Environment variables set (or GitHub secrets added)
- [ ] `python diagnose.py` passes all checks
- [ ] `bash setup_and_test.sh` completes successfully
- [ ] Jobs visible on WordPress site
- [ ] GitHub Actions workflow runs successfully (if using)
- [ ] New jobs appear after each run

---

## 🎉 **You're Done!**

Your scraper is now:
- ✅ Collecting jobs from 9 sources
- ✅ Posting to WordPress automatically
- ✅ Deduplicating to avoid duplicates
- ✅ Running on schedule (if GitHub/Heroku)
- ✅ Classifying jobs by role/seniority

**Enjoy your automated job board! 🚀**

---

**Need more help?** See:
- `TROUBLESHOOTING.md` - Common issues & fixes
- `HEROKU_DEPLOYMENT.md` - Heroku deployment guide
- `CLAUDE.md` - Complete developer documentation
