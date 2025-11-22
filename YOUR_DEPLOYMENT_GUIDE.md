# 🚀 Your TechJobs360 Deployment Guide

**For: www.techjobs360.com**
**Username: admintech**

---

## ✅ **Everything is Ready - Just Follow These Steps:**

### **Step 1: Create WordPress Application Password** (2 minutes)

1. **Open your WordPress admin panel:**
   - Go to: https://www.techjobs360.com/wp-admin
   - Username: `admintech`
   - Password: Your regular WordPress password

2. **Navigate to your profile:**
   - Click your name in the top right corner
   - Select: **Edit Profile**
   - OR: Click **Users** → **Profile**

3. **Scroll down to find "Application Passwords":**
   - It's near the bottom of the page
   - If you don't see it, your WordPress might need updating (see troubleshooting below)

4. **Create the password:**
   - In the "New Application Password Name" field, type: `TechJobs360`
   - Click: **Add New Application Password**

5. **COPY THE PASSWORD:**
   - WordPress will display: `xxxx xxxx xxxx xxxx` (with spaces)
   - **COPY THIS ENTIRE PASSWORD** (you'll only see it once!)
   - Save it temporarily in a text file or clipboard

---

### **Step 2: Test WordPress Connection** (1 minute)

Run this command in your terminal:

```bash
python test_wordpress_connection.py
```

**Expected output:**
- ✅ WordPress site is accessible
- ✅ WordPress REST API is enabled
- ✅ Application Passwords are supported

**If you see errors**, see the troubleshooting section below.

---

### **Step 3: Deploy and Run Scraper** (5 minutes)

Make the deployment script executable and run it:

```bash
# Make script executable
chmod +x deploy_to_wordpress.sh

# Run deployment
bash deploy_to_wordpress.sh
```

**What happens:**
1. Script asks for your **Application Password** (paste it from Step 1)
2. Installs dependencies if needed
3. Runs diagnostics to verify everything works
4. Asks for confirmation to run scraper
5. Collects jobs from 9 sources
6. Posts jobs to your WordPress site
7. Shows results

**Expected duration:** 5-10 minutes for first run

---

### **Step 4: Verify Jobs on Your Site** (1 minute)

**Check WordPress admin:**
- Go to: https://www.techjobs360.com/wp-admin/edit.php?post_type=post
- You should see new job posts!

**Check public site:**
- Go to: https://www.techjobs360.com
- Browse for new jobs

---

## 🎯 **Expected Results**

### **First Run:**
- Jobs collected: 50-200 (varies by sources)
- Jobs posted: All collected jobs
- Duration: 5-10 minutes

### **Subsequent Runs:**
- Jobs collected: 50-200
- Jobs posted: 5-50 (only new ones, duplicates skipped)
- Duration: 2-5 minutes

---

## 🔄 **Setting Up Automated Runs (Optional)**

Once manual deployment works, you can set up automation:

### **Option A: GitHub Actions (Recommended - FREE)**

1. Go to your repository: https://github.com/arunbabusb/techjobs360-scraper
2. Click: **Settings** → **Secrets and variables** → **Actions**
3. Add these secrets:
   - `WP_URL` = `https://www.techjobs360.com`
   - `WP_USERNAME` = `admintech`
   - `WP_APP_PASSWORD` = Your Application Password from Step 1
4. Go to **Actions** tab → **TechJobs360 FREE Scraper** → **Run workflow**

**Result:** Jobs posted automatically 4x daily (00:30, 06:30, 12:30, 18:30 UTC)

### **Option B: Heroku (Paid - $5/month)**

See: `HEROKU_DEPLOYMENT.md` for complete Heroku deployment guide.

---

## 🐛 **Troubleshooting**

### **Issue: Can't find "Application Passwords" in WordPress**

**Solution 1: Update WordPress**
- Your WordPress version might be older than 5.6
- Update to WordPress 5.6 or newer
- Then try Step 1 again

**Solution 2: Install Plugin**
```
1. WordPress Admin → Plugins → Add New
2. Search: "Application Passwords"
3. Install and activate the plugin
4. Then try Step 1 again
```

**Solution 3: Check WordPress Version**
```bash
# Check version in WordPress admin dashboard (bottom right)
# If less than 5.6, you MUST update WordPress first
```

---

### **Issue: "REST API is not accessible"**

**Possible causes:**
1. Security plugin blocking REST API
2. Permalinks not configured

**Solutions:**
```
1. WordPress Admin → Settings → Permalinks → Click "Save Changes"
2. Check security plugins (Wordfence, iThemes Security, etc.)
   - Look for REST API restrictions
   - Whitelist REST API access
3. Check .htaccess file permissions
```

---

### **Issue: "Authentication failed" when running scraper**

**Causes:**
- Wrong Application Password
- Application Password has spaces (it should!)
- Used regular password instead of Application Password

**Solution:**
```bash
# Create NEW Application Password
# Copy it EXACTLY as shown (with spaces: xxxx xxxx xxxx xxxx)
# Run deployment script again
bash deploy_to_wordpress.sh
```

---

### **Issue: "No new jobs posted"**

**Possible causes:**
1. All jobs already exist (duplicates)
2. Job sources rate-limiting
3. Network issues

**Solution:**
```bash
# Clear deduplication database for fresh start
echo "[]" > posted_jobs.json

# Run again
bash deploy_to_wordpress.sh
```

---

### **Issue: Script fails with Python errors**

**Solution:**
```bash
# Install/update dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Try again
bash deploy_to_wordpress.sh
```

---

## 📞 **Need More Help?**

1. **Run diagnostics:**
   ```bash
   python diagnose.py
   ```

2. **Check detailed logs:**
   - See terminal output for error messages
   - Common errors explained in `TROUBLESHOOTING.md`

3. **Complete documentation:**
   - `QUICK_START.md` - Quick start guide
   - `TROUBLESHOOTING.md` - All common issues
   - `HEROKU_DEPLOYMENT.md` - Heroku deployment
   - `CLAUDE.md` - Technical documentation

---

## 🎉 **Summary**

**What you need to do:**
1. ✅ Create Application Password in WordPress (2 min)
2. ✅ Run `python test_wordpress_connection.py` (1 min)
3. ✅ Run `bash deploy_to_wordpress.sh` (5 min)
4. ✅ Check www.techjobs360.com for new jobs!

**Total time:** ~10 minutes

**Result:** Fresh jobs posted to your WordPress site automatically!

---

**Your site:** https://www.techjobs360.com
**Admin panel:** https://www.techjobs360.com/wp-admin
**Username:** admintech

Good luck! 🚀
