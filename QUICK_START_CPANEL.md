# ⚡ Quick Start - cPanel Cron Setup

**For**: techjobs @ sys10.prosuperservers.com

---

## 🚀 5-Minute Setup

### Step 1: Log into cPanel

Visit: https://sys10.prosuperservers.com:2083
- Username: `techjobs`
- Password: `Tsharper$2000`

### Step 2: Open Terminal

In cPanel, click: **"Terminal"** (under Advanced section)

### Step 3: Run These Commands

**Copy and paste ONE command at a time:**

```bash
# Navigate to home
cd ~

# Clone repository
git clone https://github.com/arunbabusb/techjobs360-scraper.git

# Enter directory
cd techjobs360-scraper

# Run automated setup
bash setup_on_server.sh
```

### Step 4: Enter Your WordPress Credentials

When prompted:

1. **WordPress URL**: Press **Enter** (use default `http://127.0.0.1`)
2. **WordPress Username**: Enter your WP admin username
3. **WordPress App Password**:
   - Get it from: https://techjobs360.com/wp-admin/ → Users → Profile → Application Passwords
   - Create new: "TechJobs360 Scraper"
   - Paste the password
4. **API Key**: Press **Enter** (skip)

### Step 5: Set Up Cron Job

```bash
bash setup_cron.sh
```

Choose option **1** (every 6 hours)

### Step 6: Test

```bash
./run_scraper.sh
```

**Done!** Check logs:

```bash
tail -f logs/scraper.log
```

Press **Ctrl+C** to exit.

---

## ✅ Verify It's Working

1. Check WordPress: https://techjobs360.com/wp-admin/edit.php
2. You should see new job posts!
3. Check cron: `crontab -l`

---

## 📞 Problems?

See full guide: **CPANEL_CRON_SETUP_GUIDE.md**

Or check logs:
```bash
tail -n 100 ~/techjobs360-scraper/logs/scraper.log
```

---

**That's it!** Your scraper will run automatically every 6 hours. 🎉
