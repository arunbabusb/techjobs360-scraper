# 🚀 Run Scraper via HeroXhost Cron Jobs

**Last Updated**: 2025-11-24
**Purpose**: Run job scraper directly on hosting server (bypasses QUIC.cloud)

---

## 🎯 Why Run on HeroXhost Instead of GitHub Actions?

### Current Problem:
```
GitHub Actions → Internet → QUIC.cloud CDN → ❌ BLOCKED by bot protection
```

### Solution:
```
HeroXhost Cron → localhost (127.0.0.1) → ✅ Direct WordPress access (bypasses QUIC.cloud)
```

### Benefits:
- ✅ **No bot protection blocking** - Server talks to WordPress directly
- ✅ **No IP whitelisting needed** - Uses localhost (127.0.0.1)
- ✅ **Faster execution** - No network latency
- ✅ **More reliable** - Not dependent on external CDN
- ✅ **Keep security ON** - QUIC.cloud protection stays active for visitors
- ✅ **Free** - No extra costs

---

## 📋 Prerequisites

Before you start, ensure you have:

1. **SSH access to HeroXhost** (or cPanel access)
2. **Python 3.8+** installed on server
3. **Git** installed on server
4. **cPanel cron job access** (most hosting plans include this)

---

## 🛠️ Setup Instructions

### Step 1: SSH into HeroXhost Server

```bash
# Replace with your actual SSH credentials
ssh username@your-server.heroxhost.com
```

**Don't have SSH?** → Use cPanel Terminal instead (cPanel → Terminal)

---

### Step 2: Check Python Version

```bash
python3 --version
# Should be 3.8 or higher
```

**If Python not found or too old:**
```bash
# Contact HeroXhost support to install Python 3.11
# Or use: module load python/3.11 (if available)
```

---

### Step 3: Clone Repository to Server

**Option A: If Git is installed**
```bash
# Navigate to your home directory
cd ~

# Clone repository
git clone https://github.com/arunbabusb/techjobs360-scraper.git
cd techjobs360-scraper

# Set up Python virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Option B: Manual upload (no Git)**
```bash
# Download zip from GitHub:
# https://github.com/arunbabusb/techjobs360-scraper/archive/refs/heads/main.zip

# Upload via cPanel File Manager
# Extract to: /home/username/techjobs360-scraper/

# Then install dependencies:
cd ~/techjobs360-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

### Step 4: Create Configuration Script

Create a script that sets environment variables:

```bash
cd ~/techjobs360-scraper
nano run_scraper.sh
```

**Paste this content:**

```bash
#!/bin/bash

# TechJobs360 Scraper - Run Script for Cron
# Last Updated: 2025-11-24

# Set working directory
cd /home/username/techjobs360-scraper

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export WP_URL="http://127.0.0.1"  # Use localhost (bypasses QUIC.cloud!)
export WP_USERNAME="your-wordpress-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"  # WordPress app password
export JSEARCH_API_KEY="your-rapidapi-key"  # Optional
export AUTO_ROTATE="true"

# Run scraper
python3 job_scraper.py >> /home/username/techjobs360-scraper/logs/scraper.log 2>&1

# Deactivate virtual environment
deactivate
```

**Important changes:**
- Replace `/home/username/` with your actual home path
- Replace `your-wordpress-username` with your WP username
- Replace `xxxx xxxx xxxx xxxx` with your WP app password
- **KEY CHANGE:** `WP_URL="http://127.0.0.1"` (uses localhost!)

**Save and exit:** Ctrl+X, then Y, then Enter

---

### Step 5: Make Script Executable

```bash
chmod +x run_scraper.sh
```

---

### Step 6: Create Logs Directory

```bash
mkdir -p logs
```

---

### Step 7: Test Run Manually

```bash
./run_scraper.sh
```

**Check output:**
```bash
tail -f logs/scraper.log
```

**Expected output:**
```
2025-11-24 10:30:00 INFO Starting TechJobs360 scraper...
2025-11-24 10:30:01 INFO Loaded 45 dedup entries
2025-11-24 10:30:02 INFO Processing Asia continent...
2025-11-24 10:30:05 INFO Found 15 jobs from Remotive
2025-11-24 10:30:08 INFO Posted job: Senior Backend Engineer at Acme Corp
...
```

**If errors occur:**
- Check WP_URL is set to `http://127.0.0.1`
- Verify WordPress credentials
- Check Python dependencies installed

---

### Step 8: Set Up Cron Job

#### **Option A: Via cPanel (Recommended)**

1. **Log into cPanel**
2. **Find "Cron Jobs"** (under "Advanced" section)
3. **Add New Cron Job:**

   **Common Settings (4 times daily):**
   ```
   Minute: 0
   Hour: */6  (every 6 hours)
   Day: *
   Month: *
   Weekday: *

   Command: /home/username/techjobs360-scraper/run_scraper.sh
   ```

   **Alternative: Run every 4 hours**
   ```
   Minute: 0
   Hour: 0,6,12,18
   Day: *
   Month: *
   Weekday: *

   Command: /home/username/techjobs360-scraper/run_scraper.sh
   ```

4. **Click "Add New Cron Job"**

---

#### **Option B: Via Command Line (SSH)**

```bash
# Edit crontab
crontab -e

# Add this line (runs every 6 hours):
0 */6 * * * /home/username/techjobs360-scraper/run_scraper.sh

# Save and exit (Ctrl+X, Y, Enter)
```

**Verify cron job added:**
```bash
crontab -l
```

---

### Step 9: Monitor First Run

**Wait for next scheduled time, then check logs:**

```bash
tail -n 100 ~/techjobs360-scraper/logs/scraper.log
```

**Check WordPress:**
```
https://techjobs360.com/wp-admin/edit.php
```
Should see new job posts!

---

## 🔧 Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'requests'"

**Solution:**
```bash
cd ~/techjobs360-scraper
source venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: "Connection refused to 127.0.0.1"

**Cause:** WordPress not accessible via localhost

**Solution 1:** Try domain name instead:
```bash
# In run_scraper.sh, change:
export WP_URL="http://techjobs360.com"
# (But this might hit QUIC.cloud again)
```

**Solution 2:** Find WordPress internal path:
```bash
# Check if WordPress is in subdirectory:
ls -la /home/username/public_html/
# Use full path if needed
```

**Solution 3:** Use server's IP address:
```bash
# Get server IP:
hostname -I

# In run_scraper.sh:
export WP_URL="http://YOUR_SERVER_IP"
```

---

### Problem: "Authentication failed"

**Solution:** Verify WordPress Application Password:

1. Log into WordPress admin
2. Go to: Users → Profile → Application Passwords
3. Create new password: "TechJobs360 Scraper"
4. Copy password (format: `xxxx xxxx xxxx xxxx`)
5. Update `run_scraper.sh` with new password

---

### Problem: Cron job not running

**Check cron logs:**
```bash
# On most systems:
grep CRON /var/log/syslog

# Or check email (cron sends output to email):
# cPanel → Email → Webmail
```

**Verify script path:**
```bash
# Must be absolute path:
/home/username/techjobs360-scraper/run_scraper.sh

# NOT relative path:
~/techjobs360-scraper/run_scraper.sh  # ❌ Won't work in cron
```

---

### Problem: "Permission denied"

**Solution:**
```bash
chmod +x /home/username/techjobs360-scraper/run_scraper.sh
```

---

## 📊 Monitoring & Maintenance

### Check Scraper Logs

**View recent logs:**
```bash
tail -n 50 ~/techjobs360-scraper/logs/scraper.log
```

**View live logs:**
```bash
tail -f ~/techjobs360-scraper/logs/scraper.log
```

**Search for errors:**
```bash
grep ERROR ~/techjobs360-scraper/logs/scraper.log
```

---

### Rotate Logs (Prevent Large Files)

Create log rotation script:

```bash
nano ~/techjobs360-scraper/rotate_logs.sh
```

**Content:**
```bash
#!/bin/bash
cd /home/username/techjobs360-scraper/logs

# Keep last 7 days of logs
find . -name "*.log" -mtime +7 -delete

# Or compress old logs:
# find . -name "*.log" -mtime +7 -exec gzip {} \;
```

**Make executable:**
```bash
chmod +x ~/techjobs360-scraper/rotate_logs.sh
```

**Add to cron (runs weekly):**
```bash
crontab -e

# Add:
0 0 * * 0 /home/username/techjobs360-scraper/rotate_logs.sh
```

---

### Update Scraper Code

**Pull latest changes:**
```bash
cd ~/techjobs360-scraper
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # In case dependencies changed
```

---

## 🔄 Migrate from GitHub Actions

### What to Do:

1. **Keep GitHub Actions scraper** (as backup)
2. **Enable HeroXhost cron** (primary)
3. **Disable GitHub Actions schedule** (but keep manual trigger)

**Update `.github/workflows/scraper.yml`:**

```yaml
# Comment out schedule:
# schedule:
#   - cron: '0 0,6,12,18 * * *'

# Keep manual trigger:
on:
  workflow_dispatch:  # Can still run manually if needed
```

---

## ⚙️ Advanced: Multiple Schedules

**Run different continents at different times:**

### Create continent-specific scripts:

**run_scraper_asia.sh:**
```bash
#!/bin/bash
cd /home/username/techjobs360-scraper
source venv/bin/activate
export WP_URL="http://127.0.0.1"
export WP_USERNAME="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export PROCESS_CONTINENT="asia"
python3 job_scraper.py >> logs/scraper_asia.log 2>&1
```

**run_scraper_europe.sh:**
```bash
#!/bin/bash
cd /home/username/techjobs360-scraper
source venv/bin/activate
export WP_URL="http://127.0.0.1"
export WP_USERNAME="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export PROCESS_CONTINENT="europe"
python3 job_scraper.py >> logs/scraper_europe.log 2>&1
```

**Cron schedule:**
```bash
0 0 * * 1 /home/username/techjobs360-scraper/run_scraper_asia.sh      # Monday
0 0 * * 2 /home/username/techjobs360-scraper/run_scraper_europe.sh    # Tuesday
0 0 * * 3 /home/username/techjobs360-scraper/run_scraper_africa.sh    # Wednesday
# etc...
```

---

## 📞 Support

### HeroXhost Support

**If you need help with:**
- SSH access
- Python installation
- Cron job setup
- Server configuration

**Contact:** HeroXhost support (check their website for contact info)

---

## ✅ Success Checklist

Before going live, verify:

- [ ] Python 3.8+ installed on server
- [ ] Repository cloned to server
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `run_scraper.sh` script created with correct paths
- [ ] Script made executable (`chmod +x`)
- [ ] Environment variables set (especially `WP_URL="http://127.0.0.1"`)
- [ ] Test run completed successfully (`./run_scraper.sh`)
- [ ] Logs directory created
- [ ] Cron job added (cPanel or crontab)
- [ ] First scheduled run verified (check logs)
- [ ] Jobs appearing on WordPress

---

## 🎯 Expected Results

### Before (GitHub Actions):
```
❌ 403 Forbidden errors
❌ QUIC.cloud bot protection blocking
❌ No jobs posted
❌ Complex IP whitelisting needed
```

### After (HeroXhost Cron):
```
✅ Direct localhost connection (bypasses QUIC.cloud)
✅ Jobs posted successfully
✅ Runs 4x daily automatically
✅ QUIC.cloud protection stays ON for visitors
✅ No configuration changes needed
```

---

## 💡 Pro Tips

1. **Use localhost** (`127.0.0.1`) for WP_URL - bypasses all CDN/firewall
2. **Start with one manual run** before enabling cron
3. **Check logs after first cron run** to catch issues early
4. **Keep GitHub Actions** as backup (disable schedule, keep manual trigger)
5. **Monitor logs weekly** to ensure scraper runs smoothly
6. **Rotate logs** to prevent disk space issues

---

## 🔗 Related Documentation

- **Main Guide**: CLAUDE.md
- **Config Reference**: config.yaml
- **Scraper Code**: job_scraper.py
- **GitHub Workflow**: .github/workflows/scraper.yml

---

**🚀 This is the BEST solution for your QUIC.cloud issue!**

**Why?** Because it completely bypasses QUIC.cloud by running directly on the hosting server.

---

*Last Updated: 2025-11-24*
*Part of TechJobs360 Scraper Project*
