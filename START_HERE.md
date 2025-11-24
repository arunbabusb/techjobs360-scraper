# 🚀 START HERE - Get Your Scraper Running NOW

**Quick Setup Guide for techjobs360.com**

---

## ⏱️ Time Required: 10 Minutes

## 🎯 Goal: Get jobs posting to your WordPress site automatically

---

## 📍 Current Situation

✅ **GitHub Actions** - Scheduled and running
❌ **But BLOCKED** by QUIC.cloud bot protection
❌ **Zero jobs posted** to techjobs360.com
⚠️ **Solution needed:** Set up on HeroXhost server

**Full explanation:** See CURRENT_SITUATION_ELI5.md

---

## 🚀 3-Step Quick Start

### Step 1: Access Your Server (Choose one)

**Option A: SSH**
```bash
ssh username@your-server.heroxhost.com
```

**Option B: cPanel Terminal**
1. Log into cPanel
2. Find "Terminal" tool
3. Click to open

---

### Step 2: Set Up Scraper (Copy & Paste)

```bash
# Clone repository
cd ~
git clone https://github.com/arunbabusb/techjobs360-scraper.git
cd techjobs360-scraper

# Run setup (will ask you questions)
bash setup_on_server.sh
```

**You'll be asked for:**
- WordPress URL → Press Enter (uses localhost: 127.0.0.1)
- WordPress username → Enter your WP admin username
- WordPress password → Enter your WP Application Password*
- API key → Press Enter to skip

*Get Application Password at: WordPress Admin → Users → Profile → Application Passwords

---

### Step 3: Set Up Automatic Schedule

```bash
bash setup_cron.sh
```

**Choose:**
- Option 1 (recommended): Every 6 hours
- Press Enter

**Done!** ✅

---

## ✅ Verify It's Working

### Check Status
```bash
bash check_status.sh
```

### View Live Logs
```bash
tail -f logs/scraper.log
```

### Check WordPress
Visit: https://techjobs360.com/wp-admin/edit.php

---

## 📅 What Happens Next?

### Automatic Schedule:
- **00:00** (midnight) - Scraper runs
- **06:00** (6 AM) - Scraper runs
- **12:00** (noon) - Scraper runs
- **18:00** (6 PM) - Scraper runs

### Each Run:
1. Fetches jobs from 8+ sources
2. Removes duplicates
3. Posts to WordPress
4. Logs everything

### Expected Results:
- 20-50 jobs on first run
- 10-30 new jobs per subsequent run
- All logged in `logs/scraper.log`

---

## 🆘 Troubleshooting

### Problem: "Python not found"
**Solution:** Contact HeroXhost support to install Python 3.8+

### Problem: "Permission denied"
**Solution:**
```bash
chmod +x setup_on_server.sh
bash setup_on_server.sh
```

### Problem: "Connection refused"
**Solution:** Edit `.env` and change `WP_URL` to your domain:
```bash
nano .env
# Change: WP_URL=http://127.0.0.1
# To: WP_URL=https://techjobs360.com
```

### Problem: Jobs not posting
**Solution:**
1. Check logs: `tail -f logs/scraper.log`
2. Test manually: `./run_scraper.sh`
3. Verify WordPress credentials in `.env`

---

## 📚 More Documentation

| File | Purpose | When to Read |
|------|---------|--------------|
| **START_HERE.md** | Quick start (this file) | Right now! |
| **CURRENT_SITUATION_ELI5.md** | Current status explained | Understanding the problem |
| **DEPLOY_TO_HEROXHOST.md** | Complete deployment guide | Step-by-step setup |
| **HEROXHOST_CRON_SETUP.md** | Detailed cron guide | Advanced configuration |
| **CLAUDE.md** | Full documentation | Reference |

---

## 💡 Why This Works

### The Problem:
```
GitHub Actions → Internet → QUIC.cloud → 🚫 BLOCKED
```

### The Solution:
```
HeroXhost Cron → localhost (127.0.0.1) → ✅ Direct to WordPress
```

**Key:** Running on your server uses localhost, which bypasses QUIC.cloud entirely!

---

## 🎯 Quick Commands Reference

```bash
# Setup (run once)
bash setup_on_server.sh        # Initial setup
bash setup_cron.sh              # Configure schedule

# Monitoring (anytime)
bash check_status.sh            # Full status report
tail -f logs/scraper.log        # Live logs
crontab -l                      # View cron jobs

# Testing (anytime)
./run_scraper.sh                # Manual test run

# Maintenance
git pull origin main            # Update code
pip install -r requirements.txt # Update dependencies
```

---

## 🎉 Success Checklist

After setup, you should have:

- [ ] Scraper files on your server
- [ ] `.env` file with WordPress credentials
- [ ] Virtual environment created (`venv/` directory)
- [ ] Cron job configured (check with `crontab -l`)
- [ ] Logs directory created (`logs/`)
- [ ] Test run completed successfully
- [ ] Jobs posting to WordPress

**Verify with:** `bash check_status.sh`

---

## 📞 Need Help?

### Can't Access Server?
**Contact HeroXhost Support:**
- Ask for SSH access or confirm cPanel Terminal access
- Mention you need to set up a cron job

### Setup Not Working?
**Run diagnostics:**
```bash
bash check_status.sh
```
This will tell you exactly what's wrong!

### Still Stuck?
**Check detailed guides:**
- DEPLOY_TO_HEROXHOST.md (step-by-step)
- HEROXHOST_CRON_SETUP.md (troubleshooting)
- CURRENT_SITUATION_ELI5.md (understanding)

---

## 🔐 Security Note

The `.env` file contains your WordPress password. Keep it secure:
```bash
chmod 600 .env
```

**Tip:** Use WordPress Application Password (not your main password) - can be revoked anytime!

---

## 🎁 What You Get

After setup:

✅ **Automatic job posting** - 4 times daily
✅ **No QUIC.cloud issues** - Uses localhost
✅ **Duplicate prevention** - Smart deduplication
✅ **Company logos** - Auto-fetched from Clearbit
✅ **Job classification** - Auto-categorized
✅ **Complete logging** - Track everything
✅ **Set and forget** - Runs automatically

---

## ⏭️ Next Steps

### Right Now:
1. **Access your HeroXhost server**
2. **Run the 2 setup commands** (Step 2 & 3 above)
3. **Wait for next scheduled run**

### In 1 Hour:
4. **Check status:** `bash check_status.sh`
5. **View logs:** `tail -f logs/scraper.log`
6. **Check WordPress** for new jobs

### Ongoing:
7. **Monitor weekly** - Check logs occasionally
8. **Update monthly** - `git pull origin main`
9. **Enjoy automated job board!** 🎉

---

## 🚀 Ready? Let's Go!

**Open terminal and run:**

```bash
ssh username@your-server.heroxhost.com
cd ~
git clone https://github.com/arunbabusb/techjobs360-scraper.git
cd techjobs360-scraper
bash setup_on_server.sh
bash setup_cron.sh
```

**That's it! You're done!** ✅

---

**Questions? Problems? Run:** `bash check_status.sh`

---

*Last Updated: 2025-11-24*
*Estimated Setup Time: 10 minutes*
*Difficulty: Easy (copy & paste commands)*
