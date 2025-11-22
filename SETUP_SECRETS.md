# 🔐 WORDPRESS SECRETS SETUP GUIDE

**This guide shows you EXACTLY how to set up your WordPress credentials in GitHub.**

---

## 📋 WHAT YOU NEED

You need 3 secrets (4th is optional):

| Secret Name | Value | Required? |
|-------------|-------|-----------|
| `WP_URL` | `https://techjobs360.com` | ✅ YES |
| `WP_USERNAME` | Your WordPress username | ✅ YES |
| `WP_APP_PASSWORD` | Application Password | ✅ YES |
| `JSEARCH_API_KEY` | RapidAPI key | ⭕ Optional |

---

## 🚀 STEP-BY-STEP SETUP

### STEP 1: Create WordPress Application Password

**⚠️ IMPORTANT**: This is NOT your regular WordPress login password!

1. **Open this URL** in your browser:
   ```
   https://techjobs360.com/wp-admin/profile.php
   ```

2. **Log in** with your regular WordPress credentials

3. **Scroll down** to the section called **"Application Passwords"**

4. In the **"New Application Password Name"** field, enter:
   ```
   GitHub Actions Scraper
   ```

5. Click the **"Add New Application Password"** button

6. **A password will appear** - it looks like this:
   ```
   abcd efgh ijkl mnop qrst uvwx
   ```

7. **⚠️ COPY THIS PASSWORD NOW!** You'll only see it once!
   - Include the spaces
   - Example: `a1b2 c3d4 e5f6 g7h8 i9j0 k1l2`

---

### STEP 2: Add Secrets to GitHub

1. **Open this URL** in your browser:
   ```
   https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions
   ```

2. If you see **"404 Page Not Found"**:
   - You're not logged into GitHub, OR
   - You don't have admin access to the repository
   - Log in and try again

3. You should see a page titled **"Actions secrets and variables"**

---

### STEP 3: Add WP_URL Secret

1. Click the **"New repository secret"** button (green button on the right)

2. In the **"Name"** field, enter EXACTLY:
   ```
   WP_URL
   ```
   (all uppercase, no spaces)

3. In the **"Secret"** field, enter:
   ```
   https://techjobs360.com
   ```
   (no trailing slash!)

4. Click **"Add secret"**

✅ You should see "WP_URL" in the list now

---

### STEP 4: Add WP_USERNAME Secret

1. Click **"New repository secret"** again

2. In the **"Name"** field, enter:
   ```
   WP_USERNAME
   ```

3. In the **"Secret"** field, enter your WordPress username
   - Example: `admin` or `arunbabu` or whatever your username is

4. Click **"Add secret"**

✅ You should see "WP_USERNAME" in the list now

---

### STEP 5: Add WP_APP_PASSWORD Secret

1. Click **"New repository secret"** again

2. In the **"Name"** field, enter:
   ```
   WP_APP_PASSWORD
   ```

3. In the **"Secret"** field, **paste the password** you copied in Step 1
   - Should look like: `a1b2 c3d4 e5f6 g7h8 i9j0 k1l2`
   - ⚠️ Include the spaces!

4. Click **"Add secret"**

✅ You should see "WP_APP_PASSWORD" in the list now

---

### STEP 6: Add JSEARCH_API_KEY (Optional)

**Only do this if you have a RapidAPI JSearch subscription**

1. If you DON'T have a JSearch API key:
   - **Skip this step** - scraper will use 3 free sources
   - Still works fine without it!

2. If you DO have a JSearch API key:
   - Click **"New repository secret"**
   - Name: `JSEARCH_API_KEY`
   - Secret: Your RapidAPI key
   - Click **"Add secret"**

---

## ✅ VERIFY YOUR SETUP

After adding all secrets, you should see:

```
Repository secrets (3 or 4):
━━━━━━━━━━━━━━━━━━━━━━━━━━━
WP_URL                    Updated now
WP_USERNAME               Updated now
WP_APP_PASSWORD           Updated now
JSEARCH_API_KEY           Updated now (optional)
```

---

## 🧪 TEST YOUR SECRETS

### Option 1: Run Diagnostic Workflow (RECOMMENDED)

1. **Go to**: https://github.com/arunbabusb/techjobs360-scraper/actions/workflows/diag-auth.yml

2. Click **"Run workflow"** (dropdown button on the right)

3. Click **"Run workflow"** (green button)

4. Wait ~30 seconds

5. Refresh the page

6. **Results**:
   - ✅ **Green checkmark** = Perfect! All secrets work!
   - ❌ **Red X** = Click it to see what's wrong

### Option 2: Test Locally (Advanced)

If you have the repository on your computer:

```bash
# Set environment variables
export WP_URL="https://techjobs360.com"
export WP_USERNAME="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# Run verification script
./verify_secrets.sh
```

---

## 🆘 TROUBLESHOOTING

### "404 Page Not Found" when accessing secrets page
**Problem**: You don't have access to the repository settings

**Fix**:
1. Make sure you're logged into GitHub
2. Make sure you own the repository OR have admin access
3. Repository must be: `arunbabusb/techjobs360-scraper`

---

### Diagnostic workflow shows "401 Unauthorized"
**Problem**: WP_APP_PASSWORD is wrong or expired

**Fix**:
1. Go to: https://techjobs360.com/wp-admin/profile.php
2. Find the "GitHub Actions Scraper" password
3. Click **"Revoke"** to delete it
4. Create a NEW application password
5. Update the `WP_APP_PASSWORD` secret in GitHub

---

### Diagnostic workflow shows "403 Forbidden"
**Problem**: WordPress REST API is disabled

**Fix**:
1. Go to WordPress admin
2. Check if REST API is enabled
3. Try visiting: https://techjobs360.com/wp-json/wp/v2/posts
4. Should see JSON data, not error page

---

### "Cannot publish posts" error
**Problem**: WordPress user doesn't have permission

**Fix**:
1. Log into WordPress as admin
2. Go to Users → All Users
3. Find your username
4. Change role to "Administrator" or "Editor"
5. Save changes

---

## 📸 SCREENSHOTS GUIDE

### Where to find Application Passwords:

```
WordPress Dashboard
  ↓
Users
  ↓
Profile
  ↓
Scroll down to "Application Passwords" section
  ↓
Enter name: "GitHub Actions Scraper"
  ↓
Click "Add New Application Password"
  ↓
COPY the password that appears!
```

### Where to add GitHub Secrets:

```
GitHub Repository
  ↓
Settings (tab at top)
  ↓
Secrets and variables (left sidebar)
  ↓
Actions
  ↓
Click "New repository secret"
  ↓
Enter Name and Secret
  ↓
Click "Add secret"
```

---

## ✅ CHECKLIST

Use this checklist to make sure you did everything:

- [ ] Created WordPress Application Password
- [ ] Copied the password (with spaces)
- [ ] Opened GitHub secrets page
- [ ] Added `WP_URL` secret
- [ ] Added `WP_USERNAME` secret
- [ ] Added `WP_APP_PASSWORD` secret
- [ ] (Optional) Added `JSEARCH_API_KEY` secret
- [ ] Ran diagnostic workflow
- [ ] Diagnostic workflow passed (green checkmark)

---

## 🎯 WHAT HAPPENS NEXT

Once secrets are verified:

1. ✅ Scraper will run automatically every 6 hours
2. ✅ Jobs will be scraped from 4 sources
3. ✅ Jobs will be posted to techjobs360.com
4. ✅ Dedup file will be updated
5. ✅ You'll see new posts in WordPress admin

**Check for jobs at**:
- https://techjobs360.com/wp-admin/edit.php
- Look for tags: "tech", "jobs", "auto-scraped"

---

## 🚀 QUICK LINKS

- **Create WordPress App Password**: https://techjobs360.com/wp-admin/profile.php
- **Add GitHub Secrets**: https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions
- **Run Diagnostic**: https://github.com/arunbabusb/techjobs360-scraper/actions/workflows/diag-auth.yml
- **View Actions**: https://github.com/arunbabusb/techjobs360-scraper/actions
- **View WordPress Posts**: https://techjobs360.com/wp-admin/edit.php

---

**Need help? Having issues? Let me know what error you're seeing!**
