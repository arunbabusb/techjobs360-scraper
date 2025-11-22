#!/bin/bash
# GitHub Actions Diagnostic Script
# Helps identify why jobs aren't being posted

echo "=========================================="
echo "   SCRAPER DIAGNOSTICS"
echo "=========================================="
echo ""

# Current time
echo "📅 Current Time:"
echo "   UTC: $(date -u '+%Y-%m-%d %H:%M:%S %Z')"
echo "   Your timezone: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo ""

# Schedule
echo "⏰ Scraper Schedule (UTC):"
echo "   • 00:30 UTC (06:00 IST)"
echo "   • 06:30 UTC (12:00 IST)"
echo "   • 12:30 UTC (18:00 IST)"
echo "   • 18:30 UTC (00:00 IST)"
echo ""

# Last run time
CURRENT_HOUR=$(date -u '+%H')
CURRENT_MIN=$(date -u '+%M')

if [ $CURRENT_HOUR -ge 18 ]; then
    echo "   Next run: Today at 18:30 UTC"
elif [ $CURRENT_HOUR -ge 12 ]; then
    echo "   Last run: Today at 12:30 UTC"
    echo "   Next run: Today at 18:30 UTC"
elif [ $CURRENT_HOUR -ge 6 ]; then
    echo "   Last run: Today at 06:30 UTC"
    echo "   Next run: Today at 12:30 UTC"
else
    echo "   Last run: Today at 00:30 UTC"
    echo "   Next run: Today at 06:30 UTC"
fi
echo ""

# Check dedup file
echo "📊 Dedup File Status:"
DEDUP_FILE="posted_jobs.json"
if [ -f "$DEDUP_FILE" ]; then
    SIZE=$(wc -c < "$DEDUP_FILE")
    LINES=$(wc -l < "$DEDUP_FILE")
    MODIFIED=$(stat -c '%y' "$DEDUP_FILE" 2>/dev/null || stat -f '%Sm' "$DEDUP_FILE" 2>/dev/null)

    echo "   File: $DEDUP_FILE"
    echo "   Size: $SIZE bytes"
    echo "   Lines: $LINES"
    echo "   Last modified: $MODIFIED"
    echo ""

    if [ "$SIZE" -le 3 ]; then
        echo "   ⚠️  File is empty - NO JOBS HAVE BEEN POSTED YET"
    else
        COUNT=$(python3 -c "import json; print(len(json.load(open('$DEDUP_FILE'))))" 2>/dev/null || echo "0")
        echo "   ✅ Contains $COUNT job(s)"
    fi
else
    echo "   ❌ File not found!"
fi
echo ""

# Check GitHub Actions
echo "=========================================="
echo "   WHAT TO CHECK IN GITHUB ACTIONS"
echo "=========================================="
echo ""
echo "1. Go to:"
echo "   https://github.com/arunbabusb/techjobs360-scraper/actions"
echo ""
echo "2. Look for recent workflow runs:"
echo "   • Green ✅ = Success"
echo "   • Red ❌ = Failed"
echo "   • Yellow ⏳ = Running"
echo ""
echo "3. Click on the most recent run"
echo ""
echo "4. Look for these common issues:"
echo ""
echo "   ❌ 'Missing WP credentials; cannot post'"
echo "      → Secrets not configured correctly"
echo "      → Fix: Add secrets at https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions"
echo ""
echo "   ❌ 'Auth failed HTTP 401'"
echo "      → WordPress Application Password is wrong"
echo "      → Fix: Regenerate at https://techjobs360.com/wp-admin/profile.php"
echo ""
echo "   ❌ 'JSearch returned 403'"
echo "      → RapidAPI quota exceeded"
echo "      → Fix: Check RapidAPI dashboard or disable jsearch in config.yaml"
echo ""
echo "   ⚠️  'No new jobs to commit'"
echo "      → Scraper ran but found 0 new jobs (all were duplicates)"
echo "      → This is normal if run recently"
echo ""
echo "   ⚠️  'Found 0 jobs from [source]'"
echo "      → API returned no results"
echo "      → Normal for some searches, check multiple sources"
echo ""
echo "   ❌ 'Failed to post job to WP'"
echo "      → WordPress REST API issue"
echo "      → Check WordPress error logs"
echo ""

echo "=========================================="
echo "   QUICK TESTS"
echo "=========================================="
echo ""

# Test 1: Secrets configured?
echo "📋 Test 1: Check if secrets are configured"
echo ""
echo "   Run this command to test:"
echo "   gh workflow run diag-auth.yml"
echo ""
echo "   OR manually at:"
echo "   https://github.com/arunbabusb/techjobs360-scraper/actions/workflows/diag-auth.yml"
echo ""
echo "   Click 'Run workflow' → 'Run workflow'"
echo "   Wait 30 seconds"
echo "   Green ✅ = Secrets work!"
echo "   Red ❌ = Secrets are wrong"
echo ""

# Test 2: Trigger manual run
echo "📋 Test 2: Trigger a manual scraper run"
echo ""
echo "   Go to:"
echo "   https://github.com/arunbabusb/techjobs360-scraper/actions/workflows/scraper.yml"
echo ""
echo "   Click 'Run workflow' → 'Run workflow'"
echo "   Wait ~10 minutes"
echo "   Check logs for errors"
echo ""

# Test 3: Check WordPress
echo "📋 Test 3: Check WordPress for new posts"
echo ""
echo "   Go to:"
echo "   https://techjobs360.com/wp-admin/edit.php"
echo ""
echo "   Look for posts with tags:"
echo "   • tech"
echo "   • jobs"
echo "   • auto-scraped"
echo ""
echo "   If you see posts → ✅ Scraper is working!"
echo "   If no posts → Check GitHub Actions logs"
echo ""

echo "=========================================="
echo "   MOST COMMON ISSUES & FIXES"
echo "=========================================="
echo ""
echo "Issue: No jobs posting"
echo "Likely causes:"
echo "  1. WordPress credentials wrong → Regenerate WP_APP_PASSWORD"
echo "  2. All jobs are duplicates → Normal, wait for next run"
echo "  3. Sources returning 0 results → Check API status"
echo "  4. WordPress REST API disabled → Enable in WordPress"
echo ""
echo "Issue: Scraper not running"
echo "Likely causes:"
echo "  1. GitHub Actions disabled → Enable in repo settings"
echo "  2. Schedule not triggered yet → Wait for next scheduled time"
echo "  3. Workflow file has errors → Check syntax"
echo ""
echo "Issue: Jobs found but not posted"
echo "Likely causes:"
echo "  1. WP_APP_PASSWORD wrong → Check diagnostic workflow"
echo "  2. User doesn't have publish_posts permission → Check WP user role"
echo "  3. WordPress site down → Check site accessibility"
echo ""

echo "=========================================="
echo "   NEXT STEPS"
echo "=========================================="
echo ""
echo "1. Check GitHub Actions logs:"
echo "   https://github.com/arunbabusb/techjobs360-scraper/actions"
echo ""
echo "2. Look for the most recent 'TechJobs360 FREE Scraper' run"
echo ""
echo "3. Click on it and read the logs"
echo ""
echo "4. If you see errors, copy them and:"
echo "   • Check the troubleshooting guide in SETUP_SECRETS.md"
echo "   • Or share the error message for help"
echo ""
