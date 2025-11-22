#!/bin/bash
# WordPress Secrets Verification Script
# This script helps you verify your WordPress credentials work correctly

set -e

echo "=================================================="
echo "   WORDPRESS CREDENTIALS VERIFICATION"
echo "=================================================="
echo ""

# Check if secrets are set as environment variables
echo "📋 Step 1: Checking environment variables..."
echo ""

MISSING_SECRETS=0

if [ -z "$WP_URL" ]; then
    echo "❌ WP_URL is not set"
    MISSING_SECRETS=1
else
    echo "✅ WP_URL is set: $WP_URL"
fi

if [ -z "$WP_USERNAME" ]; then
    echo "❌ WP_USERNAME is not set"
    MISSING_SECRETS=1
else
    echo "✅ WP_USERNAME is set: $WP_USERNAME"
fi

if [ -z "$WP_APP_PASSWORD" ]; then
    echo "❌ WP_APP_PASSWORD is not set"
    MISSING_SECRETS=1
else
    # Show only first 4 chars for security
    echo "✅ WP_APP_PASSWORD is set: ${WP_APP_PASSWORD:0:4}*******************"
fi

if [ -z "$JSEARCH_API_KEY" ]; then
    echo "⚠️  JSEARCH_API_KEY is not set (optional - scraper will use free sources only)"
else
    echo "✅ JSEARCH_API_KEY is set: ${JSEARCH_API_KEY:0:4}*******************"
fi

echo ""

if [ $MISSING_SECRETS -eq 1 ]; then
    echo "=================================================="
    echo "❌ MISSING REQUIRED SECRETS!"
    echo "=================================================="
    echo ""
    echo "To fix this, you need to:"
    echo ""
    echo "FOR GITHUB ACTIONS:"
    echo "  1. Go to: https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions"
    echo "  2. Click 'New repository secret'"
    echo "  3. Add each missing secret"
    echo ""
    echo "FOR LOCAL TESTING:"
    echo "  Run these commands in your terminal:"
    echo ""
    echo "  export WP_URL='https://techjobs360.com'"
    echo "  export WP_USERNAME='your-wordpress-username'"
    echo "  export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx'"
    echo "  export JSEARCH_API_KEY='your-rapidapi-key'  # optional"
    echo ""
    echo "Then run this script again."
    echo ""
    exit 1
fi

echo "=================================================="
echo "📡 Step 2: Testing WordPress connection..."
echo "=================================================="
echo ""

# Test WordPress REST API
echo "Testing WordPress REST API endpoint..."
echo "URL: ${WP_URL}/wp-json/wp/v2/users/me"
echo ""

HTTP_CODE=$(curl -s -o /tmp/wp_response.json -w "%{http_code}" \
    -u "${WP_USERNAME}:${WP_APP_PASSWORD}" \
    "${WP_URL}/wp-json/wp/v2/users/me" 2>&1)

if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ WordPress authentication successful!"
    echo ""
    USER_NAME=$(cat /tmp/wp_response.json | python3 -c "import json,sys; print(json.load(sys.stdin).get('name', 'Unknown'))" 2>/dev/null || echo "Unknown")
    USER_ID=$(cat /tmp/wp_response.json | python3 -c "import json,sys; print(json.load(sys.stdin).get('id', 'Unknown'))" 2>/dev/null || echo "Unknown")
    echo "   Logged in as: $USER_NAME (ID: $USER_ID)"
    echo ""

    # Check capabilities
    echo "📋 Checking user permissions..."
    CAN_PUBLISH=$(cat /tmp/wp_response.json | python3 -c "import json,sys; caps=json.load(sys.stdin).get('capabilities',{}); print('true' if caps.get('publish_posts') else 'false')" 2>/dev/null || echo "unknown")
    CAN_UPLOAD=$(cat /tmp/wp_response.json | python3 -c "import json,sys; caps=json.load(sys.stdin).get('capabilities',{}); print('true' if caps.get('upload_files') else 'false')" 2>/dev/null || echo "unknown")

    if [ "$CAN_PUBLISH" = "true" ]; then
        echo "   ✅ Can publish posts"
    else
        echo "   ❌ Cannot publish posts - user needs publish_posts capability!"
    fi

    if [ "$CAN_UPLOAD" = "true" ]; then
        echo "   ✅ Can upload media"
    else
        echo "   ⚠️  Cannot upload media - logos won't be uploaded"
    fi
    echo ""
else
    echo "❌ WordPress authentication failed!"
    echo "   HTTP Status Code: $HTTP_CODE"
    echo ""
    echo "Response:"
    cat /tmp/wp_response.json 2>/dev/null || echo "(no response)"
    echo ""
    echo "=================================================="
    echo "TROUBLESHOOTING:"
    echo "=================================================="
    echo ""

    if [ "$HTTP_CODE" = "401" ]; then
        echo "❌ 401 Unauthorized - Credentials are incorrect"
        echo ""
        echo "FIX:"
        echo "  1. Go to: https://techjobs360.com/wp-admin/profile.php"
        echo "  2. Scroll to 'Application Passwords'"
        echo "  3. REVOKE the old password"
        echo "  4. Create NEW password named 'GitHub Actions Scraper'"
        echo "  5. Copy the password (format: xxxx xxxx xxxx xxxx)"
        echo "  6. Update WP_APP_PASSWORD secret in GitHub"
        echo ""
    elif [ "$HTTP_CODE" = "403" ]; then
        echo "❌ 403 Forbidden - REST API may be disabled"
        echo ""
        echo "FIX:"
        echo "  1. Check if WordPress REST API is enabled"
        echo "  2. Try visiting: ${WP_URL}/wp-json/wp/v2/posts"
        echo "  3. Should see JSON data, not an error page"
        echo ""
    elif [ "$HTTP_CODE" = "000" ]; then
        echo "❌ Connection failed - Cannot reach WordPress site"
        echo ""
        echo "FIX:"
        echo "  1. Check if $WP_URL is correct and accessible"
        echo "  2. Try opening $WP_URL in your browser"
        echo "  3. Check your internet connection"
        echo ""
    else
        echo "❌ Unknown error - HTTP $HTTP_CODE"
        echo ""
        echo "FIX:"
        echo "  1. Check WordPress error logs"
        echo "  2. Try visiting: ${WP_URL}/wp-json/"
        echo "  3. Contact WordPress admin if REST API is disabled"
        echo ""
    fi

    exit 1
fi

# Clean up
rm -f /tmp/wp_response.json

echo "=================================================="
echo "✅ ALL CHECKS PASSED!"
echo "=================================================="
echo ""
echo "Your WordPress credentials are correctly configured."
echo "The scraper is ready to post jobs to techjobs360.com!"
echo ""
echo "Next steps:"
echo "  1. Make sure these secrets are in GitHub at:"
echo "     https://github.com/arunbabusb/techjobs360-scraper/settings/secrets/actions"
echo ""
echo "  2. Run the scraper:"
echo "     - Wait for automatic run (every 6 hours)"
echo "     - OR trigger manually at:"
echo "       https://github.com/arunbabusb/techjobs360-scraper/actions/workflows/scraper.yml"
echo ""
echo "  3. Check for jobs at:"
echo "     https://techjobs360.com/wp-admin/edit.php"
echo ""
