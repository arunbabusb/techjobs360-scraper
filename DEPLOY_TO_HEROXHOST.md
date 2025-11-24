# 🚀 Deploy to HeroXhost - Complete Guide

**Quick Setup: 10 minutes to get scraper running on your server!**

---

## 🎯 What You'll Achieve

By following this guide, you will:
- ✅ Deploy the scraper to your HeroXhost server
- ✅ Bypass QUIC.cloud bot protection (using localhost connection)
- ✅ Set up automatic cron jobs (runs 4x daily)
- ✅ Have jobs posting to techjobs360.com automatically

---

## 📋 Prerequisites

Before starting, ensure you have:

1. **SSH or cPanel access** to your HeroXhost server
2. **WordPress credentials** (username and application password)
3. **10 minutes** of your time

---

## 🚀 Quick Start (3 Commands)

### Option A: SSH Access (Recommended)

```bash
# 1. SSH into your server
ssh username@your-server.heroxhost.com

# 2. Download and extract the repository
cd ~
git clone https://github.com/arunbabusb/techjobs360-scraper.git
cd techjobs360-scraper

# 3. Run automated setup
bash setup_on_server.sh
```

**That's it!** The script will:
- Install Python dependencies
- Ask for your WordPress credentials
- Configure everything automatically
- Run a test

---

### Option B: cPanel File Manager (No SSH)

If you don't have SSH access:

1. **Download repository as ZIP:**
   - Go to: https://github.com/arunbabusb/techjobs360-scraper
   - Click: Code → Download ZIP

2. **Upload to server:**
   - Log into cPanel
   - Open: File Manager
   - Navigate to: home directory (`/home/username/`)
   - Click: Upload
   - Upload the ZIP file
   - Extract the ZIP file

3. **Open Terminal in cPanel:**
   - In cPanel, find "Terminal" tool
   - Click to open terminal

4. **Run setup:**
   ```bash
   cd ~/techjobs360-scraper
   bash setup_on_server.sh
   ```

---

## 📝 Step-by-Step Installation

### Step 1: Access Your Server

**Via SSH:**
```bash
ssh username@your-server.heroxhost.com
```

**Via cPanel:**
- Log into cPanel
- Find "Terminal" icon
- Click to open

---

### Step 2: Download Repository

**If Git is available:**
```bash
cd ~
git clone https://github.com/arunbabusb/techjobs360-scraper.git
cd techjobs360-scraper
```

**If Git is NOT available:**
```bash
cd ~
wget https://github.com/arunbabusb/techjobs360-scraper/archive/refs/heads/main.zip
unzip main.zip
mv techjobs360-scraper-main techjobs360-scraper
cd techjobs360-scraper
```

---

### Step 3: Run Automated Setup

```bash
bash setup_on_server.sh
```

The script will prompt you for:

**1. WordPress URL:**
```
WordPress URL (default: http://127.0.0.1):
```
**→ Press Enter** (use default `http://127.0.0.1` for localhost)

**Why localhost?** It bypasses QUIC.cloud completely!

---

**2. WordPress Username:**
```
WordPress username: your-admin-username
```
**→ Enter your WordPress admin username**

---

**3. WordPress Application Password:**
```
WordPress Application Password (format: xxxx xxxx xxxx xxxx):
```

**How to get it:**
1. Log into WordPress admin
2. Go to: Users → Profile
3. Scroll to: Application Passwords
4. Enter name: "TechJobs360 Scraper"
5. Click: Add New Application Password
6. Copy the password (format: `xxxx xxxx xxxx xxxx`)
7. Paste it here

---

**4. JSearch API Key (Optional):**
```
JSearch API Key (optional, press Enter to skip):
```
**→ Press Enter to skip** (or paste your RapidAPI key if you have one)

---

**Setup will complete and show:**
```
✓ Setup Complete!

Next Steps:
1. Set up cron job:
   Run: bash setup_cron.sh

2. Or manually test the scraper:
   Run: ./run_scraper.sh
```

---

### Step 4: Set Up Cron Job (Automated Schedule)

```bash
bash setup_cron.sh
```

**Choose schedule:**
```
Choose schedule:
1. Every 6 hours (recommended) - 00:00, 06:00, 12:00, 18:00
2. Every 4 hours
3. Every 3 hours
4. Daily (once)
5. Custom

Select option (1-5) [default: 1]:
```

**→ Press Enter** (use default: every 6 hours)

---

### Step 5: Verify Installation

**Test manually:**
```bash
./run_scraper.sh
```

**Check logs:**
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

---

## ✅ Success Checklist

After setup, verify:

- [ ] Setup script ran without errors
- [ ] `.env` file created with credentials
- [ ] `run_scraper.sh` created and executable
- [ ] Manual test run completed successfully
- [ ] Cron job added (check with `crontab -l`)
- [ ] Jobs appearing on WordPress (check wp-admin)

---

## 🔧 Troubleshooting

### Problem: "Python not found"

**Solution:**
```bash
# Check if Python is installed
python3 --version

# If not found, contact HeroXhost support:
# Ask them to install Python 3.8 or higher
```

---

### Problem: "curl: command not found" during test

**Don't worry!** The test is optional. Just skip to:
```bash
./run_scraper.sh
```

---

### Problem: "Connection refused" to 127.0.0.1

**Solution 1:** Use domain name instead

Edit `.env`:
```bash
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

Save and test again.

---

**Solution 2:** Find server IP

```bash
hostname -I
```

Use that IP in `.env`:
```
WP_URL=http://YOUR_SERVER_IP
```

---

### Problem: "Permission denied" when running scripts

**Solution:**
```bash
chmod +x setup_on_server.sh
chmod +x setup_cron.sh
chmod +x run_scraper.sh
```

---

### Problem: "ModuleNotFoundError"

**Solution:**
```bash
cd ~/techjobs360-scraper
source venv/bin/activate
pip install -r requirements.txt
```

---

### Problem: Cron job not available

**Use cPanel Cron Jobs instead:**

1. Log into cPanel
2. Find: **Cron Jobs** (under Advanced)
3. Add new cron job:
   - **Minute:** 0
   - **Hour:** 0,6,12,18
   - **Day:** *
   - **Month:** *
   - **Weekday:** *
   - **Command:** `/home/username/techjobs360-scraper/run_scraper.sh`

4. Click: **Add New Cron Job**

---

## 📊 Monitoring

### View Live Logs

```bash
tail -f ~/techjobs360-scraper/logs/scraper.log
```

**Press Ctrl+C to exit**

---

### View Last 50 Lines

```bash
tail -n 50 ~/techjobs360-scraper/logs/scraper.log
```

---

### Search for Errors

```bash
grep ERROR ~/techjobs360-scraper/logs/scraper.log
```

---

### Check Cron Job Status

```bash
crontab -l
```

---

### Check WordPress Posts

Visit: https://techjobs360.com/wp-admin/edit.php

You should see new job posts!

---

## 🔄 Updating the Scraper

When you want to update the scraper code:

```bash
cd ~/techjobs360-scraper
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # In case dependencies changed
```

---

## 🗑️ Uninstallation

To remove everything:

```bash
# Remove cron job
crontab -l | grep -v 'run_scraper.sh' | crontab -

# Remove files
rm -rf ~/techjobs360-scraper
```

---

## 📞 Support

### Need Help?

**Check logs first:**
```bash
tail -n 100 ~/techjobs360-scraper/logs/scraper.log
```

**Common issues are documented in:**
- HEROXHOST_CRON_SETUP.md (detailed guide)
- TROUBLESHOOTING.md (coming soon)

**Contact HeroXhost Support for:**
- SSH access issues
- Python installation
- cPanel questions
- Server configuration

---

## 🎯 What Happens After Setup?

### Automatic Schedule:

**Every 6 hours** (default):
- 00:00 (midnight) - Asia continent
- 06:00 (6 AM) - Europe continent
- 12:00 (noon) - Africa continent
- 18:00 (6 PM) - North America continent

*(Continents auto-rotate by weekday)*

---

### What the Scraper Does:

1. **Fetches jobs** from 8+ sources (Remotive, RemoteOK, etc.)
2. **Deduplicates** (skips already posted jobs)
3. **Enriches** (adds company logos, classifies roles)
4. **Posts to WordPress** via REST API
5. **Logs everything** to `logs/scraper.log`
6. **Updates dedup file** `posted_jobs.json`

---

## 🔐 Security Notes

### Keep These Files Secure:

- `.env` - Contains WordPress password
- `posted_jobs.json` - Job dedup database

**Permissions:**
```bash
chmod 600 .env  # Only you can read
```

---

### WordPress Application Password:

- Used instead of main password
- Can be revoked anytime (Users → Profile → Application Passwords → Revoke)
- More secure than using main password

---

## 💡 Pro Tips

1. **Use localhost** (`http://127.0.0.1`) for WP_URL
   - Bypasses QUIC.cloud completely
   - Faster connection
   - More reliable

2. **Check logs weekly**
   - Ensure scraper is running
   - Catch issues early

3. **Keep GitHub Actions as backup**
   - Disable schedule in `.github/workflows/scraper.yml`
   - Keep manual trigger for emergencies

4. **Monitor disk space**
   - Logs can grow over time
   - Rotate logs weekly (script included)

5. **Test after any WordPress updates**
   - Ensure REST API still works
   - Check Application Password still valid

---

## 🚀 Next Steps After Deployment

1. **Wait for first cron run**
   - Check logs: `tail -f logs/scraper.log`
   - Check WordPress: https://techjobs360.com/wp-admin/

2. **Verify jobs are posting**
   - Should see new job posts in WordPress
   - Check `posted_jobs.json` is being updated

3. **Set up monitoring** (optional)
   - Email alerts on failures
   - Uptime monitoring

4. **Optimize schedule** (optional)
   - Adjust cron frequency
   - Target specific continents

---

## 📚 Related Documentation

- **Main Guide:** CLAUDE.md (full documentation)
- **Detailed Setup:** HEROXHOST_CRON_SETUP.md
- **Config Reference:** config.yaml
- **QUIC.cloud Issues:** QUIC_CLOUD_TOGGLE_GUIDE.md

---

## ✅ Quick Command Reference

```bash
# Setup
bash setup_on_server.sh      # Initial setup
bash setup_cron.sh            # Configure cron job

# Running
./run_scraper.sh              # Manual run

# Monitoring
tail -f logs/scraper.log      # Live logs
tail -f logs/cron.log         # Cron execution log
crontab -l                    # View cron jobs

# Maintenance
git pull origin main          # Update code
pip install -r requirements.txt  # Update dependencies

# Cleanup
crontab -l | grep -v 'run_scraper.sh' | crontab -  # Remove cron
```

---

## 🎉 Congratulations!

You've successfully deployed TechJobs360 scraper to your HeroXhost server!

The scraper will now:
- ✅ Run automatically 4 times daily
- ✅ Bypass QUIC.cloud bot protection
- ✅ Post jobs to techjobs360.com
- ✅ Log all activity

**Enjoy your automated job board!** 🚀

---

*Last Updated: 2025-11-24*
*Questions? See CLAUDE.md or contact support*
