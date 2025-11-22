# 🚀 GitHub Actions Setup - SUPER EASY (3 Steps)

**Total Time:** 5 minutes
**No coding required!**
**Runs automatically 4x daily!**

---

## 📋 **What You'll Do:**

1. Add 3 secrets to GitHub (WordPress credentials)
2. Click "Run workflow" button
3. Wait 5 minutes
4. Check your WordPress site for jobs!

---

## 🔐 **STEP 1: Add GitHub Secrets** (3 minutes)

### **1.1 - Get Your Application Password First**

**Open in a new tab:** https://www.techjobs360.com/wp-admin

1. Login with:
   - Username: `admintech`
   - Password: Your regular WordPress password

2. Click your name (top right) → **Edit Profile**

3. Scroll down to **"Application Passwords"**

4. In the name field, type: `TechJobs360`

5. Click: **Add New Application Password**

6. **COPY the password** (format: `xxxx xxxx xxxx xxxx`)
   - ⚠️ Keep this window open! You'll need it in Step 1.2

---

### **1.2 - Add Secrets to GitHub**

**Click this link:** https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions

(Or: Your repository → Settings → Secrets and variables → Actions)

**Click the green "New repository secret" button 3 times and add:**

#### **Secret #1:**
- **Name:** `WP_URL`
- **Value:** `https://www.techjobs360.com`
- Click "Add secret"

#### **Secret #2:**
- **Name:** `WP_USERNAME`
- **Value:** `admintech`
- Click "Add secret"

#### **Secret #3:**
- **Name:** `WP_APP_PASSWORD`
- **Value:** (Paste the Application Password you copied above)
- Click "Add secret"

**✅ You should now see 3 secrets listed!**

---

## ▶️ **STEP 2: Run the Workflow** (1 minute)

### **2.1 - Go to Actions Tab**

**Click this link:** https://github.com/arunbabusb/techjobs360-scraper/actions

(Or: Your repository → Actions tab)

### **2.2 - Select the Workflow**

Click on: **"TechJobs360 FREE Scraper"** (left sidebar)

### **2.3 - Run It**

1. Click the **"Run workflow"** dropdown button (top right, blue button)
2. Make sure branch is: `main` (or your default branch)
3. Click the green **"Run workflow"** button

**✅ Workflow is now running!**

---

## ⏳ **STEP 3: Wait & Verify** (5 minutes)

### **3.1 - Watch Progress** (Optional)

1. You'll see a yellow dot 🟡 appear - this means it's running
2. Click on the workflow run to see live logs
3. Wait 5-10 minutes for it to complete
4. Green checkmark ✅ = Success!
5. Red X ❌ = Error (see troubleshooting below)

### **3.2 - Check Your WordPress Site**

**Admin panel:**
https://www.techjobs360.com/wp-admin/edit.php?post_type=post

**Public site:**
https://www.techjobs360.com

**✅ You should see 50-200 new job posts!** 🎉

---

## 🔄 **Automatic Runs**

Once set up, GitHub Actions will **automatically** run:

**Schedule:**
- 00:30 UTC (6:00 AM IST)
- 06:30 UTC (12:00 PM IST)
- 12:30 UTC (6:00 PM IST)
- 18:30 UTC (12:00 AM IST)

**Result:** Fresh jobs posted **4 times every day**, automatically, forever, for **FREE**! 🤖

---

## 🐛 **Troubleshooting**

### **Issue: "Secret WP_APP_PASSWORD is not set"**

**Fix:**
- Go back to Step 1.2
- Make sure you added all 3 secrets
- Names must be EXACT (all caps)

---

### **Issue: Workflow runs but no jobs posted**

**Check:**
1. Click on the failed workflow run
2. Click "Run FREE job scraper"
3. Look for error messages in the logs

**Common causes:**
- Wrong Application Password → Create a new one
- WordPress REST API disabled → Check plugins
- All jobs are duplicates → Normal, wait for next run

---

### **Issue: Can't find "Application Passwords" in WordPress**

**Your WordPress might be too old.**

**Fix:**
1. Update WordPress to 5.6 or newer
2. OR install "Application Passwords" plugin
3. Then try Step 1.1 again

---

## 📊 **Expected Results**

### **First Run:**
- Duration: 5-10 minutes
- Jobs collected: 50-200
- Jobs posted: 50-200 (all new)

### **Subsequent Runs:**
- Duration: 3-5 minutes
- Jobs collected: 50-200
- Jobs posted: 5-50 (only new ones, duplicates skipped)

---

## ✅ **Success Checklist**

- [ ] Application Password created in WordPress
- [ ] 3 secrets added to GitHub (WP_URL, WP_USERNAME, WP_APP_PASSWORD)
- [ ] Workflow triggered manually
- [ ] Workflow completed with green checkmark ✅
- [ ] Jobs visible on www.techjobs360.com

**Once all checked, you're done!** Jobs will post automatically 4x daily! 🚀

---

## 🎯 **Quick Links**

**Add Secrets:**
https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions

**Run Workflow:**
https://github.com/arunbabusb/techjobs360-scraper/actions

**View Jobs:**
https://www.techjobs360.com/wp-admin/edit.php?post_type=post

---

## 💡 **Summary**

**What you did:**
1. ✅ Created Application Password (2 min)
2. ✅ Added 3 secrets to GitHub (2 min)
3. ✅ Clicked "Run workflow" (1 min)

**What happens now:**
- ✅ Jobs posted automatically 4x daily
- ✅ No maintenance needed
- ✅ Completely free
- ✅ Runs in the cloud

**Result:** Your job board stays fresh with new jobs every day! 🎉

---

**Need help? Check the logs or see TROUBLESHOOTING.md**
