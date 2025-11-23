# 🔧 How to Fix WordPress 503 Error - Step by Step

**Problem:** Your site techjobs360.com returns 503 Service Unavailable, preventing job posts.

**Follow these solutions in order** (easiest to hardest):

---

## ✅ **SOLUTION 1: Delete .maintenance File** (2 minutes)

WordPress creates a `.maintenance` file during updates. Sometimes it doesn't get deleted.

### **Using cPanel File Manager:**

1. **Log into your hosting control panel** (cPanel, Plesk, etc.)

2. **Open File Manager**
   - Look for "File Manager" icon
   - Click to open

3. **Navigate to WordPress root folder**
   - Usually: `public_html` or `www` or `httpdocs`
   - Click on that folder

4. **Show hidden files**
   - Click **Settings** (top right)
   - Check "Show Hidden Files (dotfiles)"
   - Click **Save**

5. **Find .maintenance file**
   - Look for a file called **`.maintenance`**
   - If you see it, **RIGHT-CLICK → Delete**

6. **Test your site**
   - Visit: https://techjobs360.com
   - Visit: https://techjobs360.com/wp-json/
   - Should work now!

### **Using FTP/SFTP:**

1. Connect to your site via FTP (FileZilla, etc.)
2. Navigate to WordPress root directory
3. Look for `.maintenance` file
4. Delete it
5. Test your site

---

## ✅ **SOLUTION 2: Disable All Plugins** (5 minutes)

A plugin might be causing the 503 error.

### **Method A: Via WordPress Dashboard** (if accessible)

1. **Log into WordPress admin**
   - Go to: https://techjobs360.com/wp-admin/
   - Login with your credentials

2. **Go to Plugins**
   - Click **Plugins** → **Installed Plugins**

3. **Deactivate ALL plugins**
   - Check the box at the top (selects all)
   - Select "Deactivate" from dropdown
   - Click **Apply**

4. **Test your site**
   - Visit: https://techjobs360.com/wp-json/
   - Does it work now?

5. **If it works:**
   - Re-activate plugins **one by one**
   - Test after each activation
   - The one that breaks it is the culprit

6. **Common culprit plugins:**
   - Security plugins (Wordfence, iThemes Security)
   - Cache plugins (WP Super Cache, W3 Total Cache)
   - Maintenance mode plugins
   - REST API disable plugins

### **Method B: Via File Manager** (if dashboard is inaccessible)

1. **Open File Manager** in cPanel

2. **Navigate to plugins folder**
   ```
   public_html/wp-content/plugins/
   ```

3. **Rename the plugins folder**
   - Right-click on `plugins`
   - Select **Rename**
   - Rename to: `plugins-disabled`

4. **Test your site**
   - Visit: https://techjobs360.com/wp-json/

5. **If it works:**
   - Rename back to `plugins`
   - Go into the folder
   - Rename ONE plugin folder at a time to disable individual plugins
   - Test to find the culprit

---

## ✅ **SOLUTION 3: Check Hosting Resources** (3 minutes)

Your site might be hitting resource limits.

### **In cPanel:**

1. **Log into cPanel**

2. **Check Resource Usage**
   - Look for "CPU and Concurrent Connection Usage" or "Resource Usage"
   - Click it

3. **Check if you're hitting limits:**
   - **CPU Usage**: Should be < 100%
   - **Memory (RAM)**: Should be < 100%
   - **Entry Processes**: Should be < limit
   - **I/O Usage**: Should be < limit

4. **If hitting limits:**
   - Wait a few minutes
   - OR restart services
   - OR upgrade hosting plan

### **Restart Services:**

In cPanel, look for:
- **"Restart Services"** or
- **"Select PHP Version"** → Click **Restart**
- **"PHP Selector"** → Restart

---

## ✅ **SOLUTION 4: Fix SSL Certificate** (5 minutes)

The 503 error showed SSL issues: `BAD_ECC_CERT`

### **In cPanel:**

1. **Find SSL/TLS section**
   - Look for "SSL/TLS Status" or "Let's Encrypt SSL"

2. **Check certificate status**
   - Is it valid?
   - Is it expired?
   - Any errors?

3. **Regenerate certificate:**
   - If using Let's Encrypt:
     - Click **"Run AutoSSL"** or **"Issue"**
   - Wait 2-5 minutes

4. **Test your site**
   - Visit: https://techjobs360.com/wp-json/

### **Using Cloudflare:**

If using Cloudflare:

1. **Log into Cloudflare dashboard**

2. **Go to SSL/TLS tab**

3. **Set SSL/TLS encryption mode:**
   - Change to **"Full"** or **"Full (strict)"**
   - NOT "Flexible"

4. **Test your site**

---

## ✅ **SOLUTION 5: Disable Cloudflare/WAF Temporarily** (3 minutes)

Cloudflare or firewall might be blocking REST API requests.

### **If using Cloudflare:**

1. **Log into Cloudflare dashboard**

2. **Select your domain** (techjobs360.com)

3. **Go to Security → WAF**

4. **Temporarily set Security Level to "Essentially Off"**
   - Go to: Security → Settings
   - Security Level: **Essentially Off**

5. **Disable Bot Fight Mode**
   - Security → Bots
   - Turn OFF "Bot Fight Mode"

6. **Test your site**
   - Visit: https://techjobs360.com/wp-json/

7. **If it works:**
   - Create a WAF rule to allow REST API:
   ```
   (http.request.uri.path contains "/wp-json/")
   Action: Allow
   ```

8. **Re-enable security** after creating the rule

---

## ✅ **SOLUTION 6: Enable REST API in WordPress** (2 minutes)

REST API might be disabled.

### **Via wp-config.php:**

1. **Open File Manager**

2. **Navigate to WordPress root**

3. **Edit wp-config.php**
   - Right-click → Edit

4. **Look for this line:**
   ```php
   define('REST_API_ENABLED', false);
   ```

5. **Change to:**
   ```php
   define('REST_API_ENABLED', true);
   ```

6. **Or DELETE the line entirely**

7. **Save the file**

8. **Test your site**

### **Via .htaccess:**

1. **Open .htaccess file** in WordPress root

2. **Look for these lines:**
   ```apache
   # Block WordPress REST API
   RewriteRule ^wp-json/ - [F,L]
   ```

3. **DELETE or comment out** those lines:
   ```apache
   # RewriteRule ^wp-json/ - [F,L]
   ```

4. **Save**

5. **Test your site**

---

## ✅ **SOLUTION 7: Increase PHP Memory & Timeouts** (3 minutes)

Low memory might cause 503 errors.

### **Via wp-config.php:**

1. **Edit wp-config.php**

2. **Add these lines** (before "/* That's all, stop editing! */"):
   ```php
   define('WP_MEMORY_LIMIT', '256M');
   define('WP_MAX_MEMORY_LIMIT', '512M');
   ```

3. **Save**

### **Via .htaccess:**

1. **Edit .htaccess**

2. **Add these lines:**
   ```apache
   php_value memory_limit 256M
   php_value max_execution_time 300
   php_value max_input_time 300
   ```

3. **Save**

### **Via php.ini:**

If you have access to php.ini:

1. **Find or create php.ini** in WordPress root

2. **Add:**
   ```ini
   memory_limit = 256M
   max_execution_time = 300
   max_input_time = 300
   post_max_size = 64M
   upload_max_filesize = 64M
   ```

3. **Save**

4. **Restart PHP** (in cPanel → Select PHP Version → Restart)

---

## ✅ **SOLUTION 8: Contact Hosting Support** (10 minutes)

If nothing above works, get help from your hosting provider.

### **What to tell them:**

```
Hi,

My WordPress site (techjobs360.com) is returning HTTP 503 errors.

Specifically:
- Main site sometimes works but REST API (/wp-json/) always fails
- Error: 503 Service Unavailable
- SSL certificate showing errors: BAD_ECC_CERT
- I need the WordPress REST API to work for my job scraper

I've tried:
- Deleting .maintenance file
- Disabling plugins
- Checking resource usage
- Regenerating SSL certificate

Can you please:
1. Check server logs for errors
2. Verify REST API is not blocked by firewall
3. Check SSL certificate configuration
4. Verify WordPress/PHP services are running properly

Thank you!
```

### **Include:**
- Your domain: techjobs360.com
- Specific URL failing: https://techjobs360.com/wp-json/
- Error: 503 Service Unavailable

---

## ✅ **QUICK VERIFICATION CHECKLIST**

After trying any solution above, test these URLs:

### **Test 1: Main Site**
```
https://techjobs360.com
```
**Should see:** Your normal website

### **Test 2: REST API**
```
https://techjobs360.com/wp-json/
```
**Should see:** JSON data like this:
```json
{
  "name": "TechJobs360",
  "description": "...",
  "url": "https://techjobs360.com",
  ...
}
```

### **Test 3: WordPress Admin**
```
https://techjobs360.com/wp-admin/
```
**Should see:** Login page or dashboard

### **Test 4: User Endpoint**
```
https://techjobs360.com/wp-json/wp/v2/users/me
```
(Login with your credentials when prompted)

**Should see:** User data or 401 error (both are OK - means REST API works!)

---

## 🎯 **RECOMMENDED ORDER:**

Try these in order (fastest → slowest):

1. ✅ **Delete .maintenance file** (2 min) ← START HERE
2. ✅ **Disable plugins** (5 min)
3. ✅ **Check resources** (3 min)
4. ✅ **Fix SSL** (5 min)
5. ✅ **Disable Cloudflare WAF** (3 min)
6. ✅ **Enable REST API** (2 min)
7. ✅ **Increase PHP limits** (3 min)
8. ✅ **Contact support** (10 min)

---

## 📞 **WHAT TO REPORT BACK:**

Once you try any solution, let me know:

1. **Which solution did you try?**
2. **What happened?**
3. **What do you see at https://techjobs360.com/wp-json/ now?**
   - JSON data? (GREAT!)
   - 503 error? (Still broken)
   - Different error? (Tell me what it says)

---

## ✅ **ONCE FIXED:**

When you see JSON data at https://techjobs360.com/wp-json/, the site is fixed!

Then:

1. **Run the diagnostic script:**
   ```bash
   export WP_URL="https://techjobs360.com"
   export WP_USERNAME="your-username"
   export WP_APP_PASSWORD="your-app-password"
   python3 diagnose_posting.py
   ```

2. **Trigger scraper manually:**
   - Go to: https://github.com/arunbabusb/techjobs360-scraper/actions/workflows/scraper.yml
   - Click "Run workflow"
   - Wait 10 minutes

3. **Check for jobs:**
   - https://techjobs360.com/wp-admin/edit.php
   - You should see new job posts!

---

**Start with Solution 1 (delete .maintenance file) and work your way down!** 🚀
