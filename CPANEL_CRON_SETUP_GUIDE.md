# 🚀 cPanel Cron Job Setup Guide for TechJobs360 Scraper

**Your Server Details:**
- **cPanel URL**: https://sys10.prosuperservers.com:2083
- **Username**: techjobs
- **Server**: ProSuperServers

**Time to Complete**: 15-20 minutes

---

## 📋 Overview

This guide will help you set up automated cron jobs on your cPanel hosting to run the TechJobs360 job scraper every 6 hours (4 times daily).

**What you'll achieve:**
- ✅ Deploy scraper to your hosting server
- ✅ Bypass QUIC.cloud bot protection (using localhost)
- ✅ Set up automatic cron jobs
- ✅ Jobs posting to techjobs360.com automatically

---

## 🔐 Step 1: Get WordPress Application Password

Before starting, you need a WordPress Application Password:

### 1.1 Log into WordPress Admin

Visit: https://techjobs360.com/wp-admin/

### 1.2 Navigate to Your Profile

1. Click on **Users** → **Profile** (or your username in top-right)
2. Scroll down to **Application Passwords** section

### 1.3 Create New Application Password

1. In the **"New Application Password Name"** field, enter: `TechJobs360 Scraper`
2. Click: **Add New Application Password**
3. **COPY** the generated password (format: `xxxx xxxx xxxx xxxx`)
4. **Save this password** - you'll need it in Step 4

**Important**: This password is only shown once! Save it somewhere safe.

---

## 🖥️ Step 2: Access cPanel Terminal

### 2.1 Log into cPanel

1. Visit: https://sys10.prosuperservers.com:2083
2. Username: `techjobs`
3. Password: `Tsharper$2000`

### 2.2 Open Terminal

1. In cPanel, scroll down to **"Advanced"** section
2. Click on **"Terminal"** icon
3. Terminal window will open in your browser

**Alternative**: If Terminal is not available, use SSH:
```bash
ssh techjobs@sys10.prosuperservers.com
```

---

## 📦 Step 3: Install the Scraper

Copy and paste these commands into the terminal, **one at a time**:

### 3.1 Check Python Installation

```bash
python3 --version
```

**Expected output**: `Python 3.8` or higher

**If Python not found**: Contact ProSuperServers support to install Python 3.8+

---

### 3.2 Navigate to Home Directory

```bash
cd ~
pwd
```

**Note the path** - it will be something like `/home/techjobs/`

---

### 3.3 Download Repository

**Option A: Using Git (Recommended)**

```bash
git clone https://github.com/arunbabusb/techjobs360-scraper.git
cd techjobs360-scraper
```

**Option B: Using wget (if Git not available)**

```bash
wget https://github.com/arunbabusb/techjobs360-scraper/archive/refs/heads/main.zip
unzip main.zip
mv techjobs360-scraper-main techjobs360-scraper
cd techjobs360-scraper
```

---

### 3.4 Set Up Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

**You should see** `(venv)` prefix in your terminal prompt.

---

### 3.5 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**This will take 2-3 minutes**. Wait for installation to complete.

---

## ⚙️ Step 4: Configure Environment Variables

### 4.1 Create Configuration File

Run the automated setup script:

```bash
bash setup_on_server.sh
```

### 4.2 Enter Your Credentials

The script will prompt you for information. **Enter the following**:

**1. WordPress URL:**
```
WordPress URL (default: http://127.0.0.1):
```
**→ Press Enter** (use default `http://127.0.0.1`)

**Why localhost?** This bypasses QUIC.cloud CDN and connects directly to WordPress!

---

**2. WordPress Username:**
```
WordPress username:
```
**→ Enter your WordPress admin username**

---

**3. WordPress Application Password:**
```
WordPress Application Password (format: xxxx xxxx xxxx xxxx):
```
**→ Paste the Application Password** you created in Step 1

---

**4. JSearch API Key (Optional):**
```
JSearch API Key (optional, press Enter to skip):
```
**→ Press Enter to skip** (or paste your RapidAPI key if you have one)

---

### 4.3 Verify Setup Completed

You should see:

```
✓ Setup Complete!

Next Steps:
1. Set up cron job:
   Run: bash setup_cron.sh
```

---

## 🕐 Step 5: Set Up Cron Job

### 5.1 Run Cron Setup Script

```bash
bash setup_cron.sh
```

### 5.2 Choose Schedule

The script will ask:

```
Choose schedule:
1. Every 6 hours (recommended) - 00:00, 06:00, 12:00, 18:00
2. Every 4 hours
3. Every 3 hours
4. Daily (once)
5. Custom
```

**→ Enter `1` and press Enter** (every 6 hours - recommended)

---

### 5.3 Verify Cron Job Added

The script will show:

```
✓ Cron Job Setup Complete!

Schedule: every 6 hours
Command: /home/techjobs/techjobs360-scraper/run_scraper.sh
```

**Verify by running:**

```bash
crontab -l
```

You should see:

```
# TechJobs360 Scraper - Runs every 6 hours
0 0,6,12,18 * * * /home/techjobs/techjobs360-scraper/run_scraper.sh
```

---

## ✅ Step 6: Test the Setup

### 6.1 Run Manual Test

```bash
cd ~/techjobs360-scraper
./run_scraper.sh
```

**This will take 5-15 minutes**. Wait for it to complete.

---

### 6.2 Check Logs

```bash
tail -f logs/scraper.log
```

**Press Ctrl+C** to exit when done viewing.

**Expected output:**

```
2025-11-24 10:30:00 INFO Starting TechJobs360 scraper...
2025-11-24 10:30:01 INFO Loaded 45 dedup entries
2025-11-24 10:30:02 INFO Processing Asia continent...
2025-11-24 10:30:05 INFO Found 15 jobs from Remotive
2025-11-24 10:30:08 INFO Posted job: Senior Backend Engineer at Acme Corp
...
```

---

### 6.3 Check WordPress

1. Log into WordPress admin: https://techjobs360.com/wp-admin/
2. Go to: **Posts** → **All Posts**
3. **You should see new job posts!**

---

## 🎯 What Happens Next?

### Automatic Schedule

Your scraper will now run **automatically** at:

- **00:00** (midnight)
- **06:00** (6 AM)
- **12:00** (noon)
- **18:00** (6 PM)

**Every day**, the scraper will:
1. Fetch jobs from 8+ sources (Remotive, RemoteOK, WeWorkRemotely, JSearch, etc.)
2. Deduplicate (skip already posted jobs)
3. Enrich with company logos
4. Classify by role, seniority, and work type
5. Post to WordPress automatically
6. Log everything to `logs/scraper.log`

---

## 🔧 Troubleshooting

### Problem: "Connection refused to 127.0.0.1"

**Solution 1: Use domain name instead**

Edit `.env` file:

```bash
cd ~/techjobs360-scraper
nano .env
```

Change:
```
WP_URL=http://127.0.0.1
```

To:
```
WP_URL=https://techjobs360.com
```

Save: **Ctrl+X**, then **Y**, then **Enter**

Test again:
```bash
./run_scraper.sh
```

---

**Solution 2: Use server IP**

Find your server IP:

```bash
hostname -I
```

Edit `.env`:

```bash
nano .env
```

Change:
```
WP_URL=http://YOUR_SERVER_IP
```

---

### Problem: "Authentication failed"

**Solution**: Verify Application Password

1. Log into WordPress admin
2. Go to: **Users** → **Profile**
3. Scroll to: **Application Passwords**
4. **Revoke** old password
5. Create new password: `TechJobs360 Scraper`
6. Copy new password
7. Update `.env`:

```bash
nano .env
```

Update:
```
WP_APP_PASSWORD=your-new-password-here
```

---

### Problem: "ModuleNotFoundError"

**Solution**: Reinstall dependencies

```bash
cd ~/techjobs360-scraper
source venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: "Permission denied" running scripts

**Solution**: Make scripts executable

```bash
chmod +x ~/techjobs360-scraper/run_scraper.sh
chmod +x ~/techjobs360-scraper/setup_on_server.sh
chmod +x ~/techjobs360-scraper/setup_cron.sh
```

---

### Problem: Cron job not running

**Check cron logs:**

```bash
tail -f ~/techjobs360-scraper/logs/cron.log
```

**Verify cron job exists:**

```bash
crontab -l
```

**Alternative: Use cPanel Cron Jobs UI**

If command-line cron doesn't work:

1. In cPanel, find **"Cron Jobs"** (under Advanced)
2. Click to open
3. Add new cron job:
   - **Minute**: `0`
   - **Hour**: `0,6,12,18`
   - **Day**: `*`
   - **Month**: `*`
   - **Weekday**: `*`
   - **Command**: `/home/techjobs/techjobs360-scraper/run_scraper.sh`
4. Click **"Add New Cron Job"**

---

## 📊 Monitoring & Maintenance

### View Live Logs

```bash
tail -f ~/techjobs360-scraper/logs/scraper.log
```

**Press Ctrl+C to exit**

---

### View Last 100 Lines

```bash
tail -n 100 ~/techjobs360-scraper/logs/scraper.log
```

---

### Search for Errors

```bash
grep ERROR ~/techjobs360-scraper/logs/scraper.log
```

---

### Check Cron Status

```bash
crontab -l
```

---

### Check Disk Space

```bash
df -h ~
```

---

### Rotate Logs (Prevent Large Files)

Create log rotation script:

```bash
cd ~/techjobs360-scraper
nano rotate_logs.sh
```

**Paste this content:**

```bash
#!/bin/bash
cd /home/techjobs/techjobs360-scraper/logs

# Keep last 7 days of logs
find . -name "*.log" -mtime +7 -delete

# Or compress old logs instead:
# find . -name "*.log" -mtime +7 -exec gzip {} \;
```

**Save**: Ctrl+X, Y, Enter

**Make executable:**

```bash
chmod +x rotate_logs.sh
```

**Add to cron (runs weekly):**

```bash
crontab -e
```

**Add this line:**

```
0 0 * * 0 /home/techjobs/techjobs360-scraper/rotate_logs.sh
```

Save and exit.

---

## 🔄 Updating the Scraper

When you want to update to the latest version:

```bash
cd ~/techjobs360-scraper
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🗑️ Uninstall (If Needed)

To remove everything:

```bash
# Remove cron job
crontab -l | grep -v 'run_scraper.sh' | crontab -

# Remove files
rm -rf ~/techjobs360-scraper
```

---

## 📞 Support

### Check Logs First

```bash
tail -n 200 ~/techjobs360-scraper/logs/scraper.log
```

### Contact Support

**For server/cPanel issues:**
- ProSuperServers Support

**For scraper issues:**
- GitHub: https://github.com/arunbabusb/techjobs360-scraper/issues

**For WordPress issues:**
- Check: https://techjobs360.com/wp-admin/

---

## ✅ Success Checklist

Verify everything is working:

- [ ] Python 3.8+ installed on server
- [ ] Repository cloned to `/home/techjobs/techjobs360-scraper`
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `.env` file created with credentials
- [ ] `run_scraper.sh` created and executable
- [ ] Manual test run completed successfully
- [ ] Cron job added (verified with `crontab -l`)
- [ ] Logs directory created
- [ ] Jobs appearing on WordPress admin

---

## 💡 Pro Tips

1. **Always use localhost** (`http://127.0.0.1`) for WP_URL
   - Bypasses QUIC.cloud completely
   - Faster and more reliable

2. **Check logs weekly**
   - Catch issues early
   - Monitor job posting success rate

3. **Keep GitHub Actions as backup**
   - Disable schedule in workflow
   - Keep manual trigger option

4. **Monitor disk space**
   - Logs can grow over time
   - Use log rotation script

5. **Test after WordPress updates**
   - Ensure REST API still works
   - Verify Application Password validity

---

## 🎉 Congratulations!

You've successfully set up automated job scraping on your cPanel hosting!

**Your scraper is now:**
- ✅ Running automatically 4 times daily
- ✅ Bypassing QUIC.cloud protection
- ✅ Posting jobs to techjobs360.com
- ✅ Logging all activity

**Next scheduled runs:**
- Today at: 00:00, 06:00, 12:00, 18:00

**Enjoy your automated job board!** 🚀

---

## 📚 Related Documentation

- **Main Guide**: CLAUDE.md
- **Detailed Setup**: HEROXHOST_CRON_SETUP.md
- **Deployment Guide**: DEPLOY_TO_HEROXHOST.md
- **Config Reference**: config.yaml

---

## 🔗 Quick Commands Reference

```bash
# Setup
bash setup_on_server.sh      # Initial setup
bash setup_cron.sh            # Configure cron

# Running
./run_scraper.sh              # Manual run

# Monitoring
tail -f logs/scraper.log      # Live logs
tail -f logs/cron.log         # Cron log
crontab -l                    # View cron jobs

# Maintenance
git pull origin main          # Update code
pip install -r requirements.txt  # Update dependencies

# Cleanup
crontab -l | grep -v 'run_scraper.sh' | crontab -  # Remove cron
```

---

**Last Updated**: 2025-11-24
**Version**: 1.0
**Server**: ProSuperServers (sys10.prosuperservers.com)
**Username**: techjobs
