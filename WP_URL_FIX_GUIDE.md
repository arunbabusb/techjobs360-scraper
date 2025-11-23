# WP_URL Configuration Fix Guide

## Problem Summary

The scraper was failing with the following error:
```
ERROR Failed to post job to WP: No connection adapters were found for "***/wp-json/wp/v2/posts"
WARNING WP media upload failed: No connection adapters were found for "***/wp-json/wp/v2/media"
```

## Root Cause

The `WP_URL` environment variable was set to `***` (an invalid placeholder value) instead of your actual WordPress site URL. The Python `requests` library requires URLs to have a proper scheme (`http://` or `https://`) to determine which connection adapter to use.

## Solution Applied

**Fix committed**: `c25747f` - "Fix WP_URL validation to prevent connection adapter errors"

### What was changed:
- Added validation in `job_scraper.py` (lines 54-58) to check if `WP_URL` has a proper URL scheme
- If `WP_URL` is invalid, it's set to `None` and WordPress posting is disabled
- Clear warning messages are now logged to help identify configuration issues

### Code added:
```python
# Validate WP_URL has proper scheme
if WP_URL and not (WP_URL.startswith("http://") or WP_URL.startswith("https://")):
    logger.warning("WP_URL is set but missing http:// or https:// scheme. Current value: %s", WP_URL)
    logger.warning("WordPress posting will be disabled. Please set WP_URL to a valid URL like https://techjobs360.com")
    WP_URL = None  # Disable WordPress posting if URL is invalid
```

## How to Fix Your Configuration

### Step 1: Update GitHub Secrets

You need to update the `WP_URL` secret in your GitHub repository:

1. Go to your repository: https://github.com/arunbabusb/techjobs360-scraper
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Find the `WP_URL` secret
4. Click **Update** and set it to your actual WordPress site URL

**Example valid values:**
- `https://techjobs360.com`
- `https://www.techjobs360.com`
- `http://techjobs360.com` (not recommended, use HTTPS)

**Invalid values (will be caught by validation):**
- `***` (placeholder)
- `techjobs360.com` (missing scheme)
- `www.techjobs360.com` (missing scheme)

### Step 2: Verify Other Secrets

While you're in the GitHub Secrets page, verify these are also correctly set:

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `WP_URL` | WordPress site URL | `https://techjobs360.com` |
| `WP_USERNAME` | WordPress username | `admin` or your username |
| `WP_APP_PASSWORD` | WordPress application password | `xxxx xxxx xxxx xxxx` |
| `JSEARCH_API_KEY` | RapidAPI JSearch key (optional) | Your RapidAPI key |

### Step 3: Generate WordPress Application Password (if needed)

If you don't have a WordPress application password:

1. Log in to your WordPress admin panel: `https://techjobs360.com/wp-admin`
2. Go to: **Users** → **Profile**
3. Scroll down to **Application Passwords** section
4. Enter a name like "GitHub Actions Scraper"
5. Click **Add New Application Password**
6. Copy the generated password (format: `xxxx xxxx xxxx xxxx`)
7. Save it as the `WP_APP_PASSWORD` secret in GitHub

### Step 4: Test the Fix

After updating the secrets, you can trigger the scraper workflow manually:

**Option A: Using GitHub Web Interface**
1. Go to: https://github.com/arunbabusb/techjobs360-scraper/actions
2. Click on **TechJobs360 FREE Scraper** workflow
3. Click **Run workflow** button
4. Select branch: `main`
5. Click **Run workflow**

**Option B: Using GitHub CLI** (if installed)
```bash
gh workflow run scraper.yml
```

**Option C: Wait for scheduled run**
The scraper runs automatically at: 00:30, 06:30, 12:30, 18:30 UTC

### Step 5: Monitor the Run

1. Go to: https://github.com/arunbabusb/techjobs360-scraper/actions
2. Click on the latest workflow run
3. Check the logs for:
   - ✅ No "No connection adapters" errors
   - ✅ Jobs being posted successfully
   - ✅ "Update job dedup list" commit at the end

## Expected Behavior After Fix

### With Valid WP_URL:
```
2025-11-23 16:40:11,269 INFO == Continent: Asia (***) ==
2025-11-23 16:40:11,269 INFO Searching: software engineer Bengaluru India
2025-11-23 16:40:45,123 INFO Posted job to WP: "Senior Backend Engineer" (ID: 12345)
2025-11-23 16:40:50,456 INFO Posted job to WP: "Frontend Developer" (ID: 12346)
```

### With Invalid WP_URL (before fix is applied):
```
2025-11-23 17:27:48,806 WARNING WP_URL is set but missing http:// or https:// scheme. Current value: ***
2025-11-23 17:27:48,806 WARNING WordPress posting will be disabled. Please set WP_URL to a valid URL like https://techjobs360.com
2025-11-23 16:40:11,269 INFO == Continent: Asia (***) ==
2025-11-23 16:40:11,269 INFO Searching: software engineer Bengaluru India
2025-11-23 16:40:40,908 ERROR Missing WP credentials; cannot post.
```

## Testing Locally

If you want to test the scraper locally:

```bash
# Set environment variables
export WP_URL="https://techjobs360.com"
export WP_USERNAME="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"

# Run the scraper
python job_scraper.py
```

## Troubleshooting

### Issue: Still getting connection adapter errors
**Solution**: Make sure you updated the GitHub Secret and not just a local environment variable. GitHub Actions uses the secrets stored in the repository settings.

### Issue: "Missing WP credentials; cannot post"
**Solution**: This is expected if `WP_URL` is invalid. Update the `WP_URL` secret as described in Step 1.

### Issue: Jobs are fetched but not posted
**Check**:
1. Is `WP_URL` a valid URL with `https://`?
2. Are `WP_USERNAME` and `WP_APP_PASSWORD` correct?
3. Does the WordPress user have `edit_posts` and `upload_files` permissions?

### Issue: "401 Unauthorized" errors
**Solution**: The `WP_APP_PASSWORD` is incorrect or expired. Generate a new application password (Step 3).

### Issue: GitHub Actions shows "***" in logs
**Note**: This is normal - GitHub automatically masks secret values in logs for security. Your actual URL should work even if it appears as "***" in the logs.

## Summary

✅ **Fix applied**: WP_URL validation added to prevent crashes
✅ **Action required**: Update GitHub Secret `WP_URL` to valid URL
✅ **Testing**: Run workflow manually or wait for scheduled run

After you update the `WP_URL` secret to a valid URL like `https://techjobs360.com`, the scraper will work correctly and post jobs to your WordPress site.

---

**Last Updated**: 2025-11-23
**Commit**: c25747f
**Branch**: claude/check-project-status-016P7XxwqYXJKsaPhVscbf2p
