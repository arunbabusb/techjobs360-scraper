#!/bin/bash

##############################################################################
# TechJobs360 Scraper - WordPress REST API Access Test
#
# Purpose: Test if QUIC.cloud bot protection is blocking REST API access
# Usage: ./test_api_access.sh
#
# This script tests three levels of access:
# 1. Basic API endpoint (no auth) - should return JSON
# 2. Authenticated endpoint (with credentials) - should return user info
# 3. Full scraper test - actually posts a test job
#
##############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Site URL
WP_URL="${WP_URL:-https://techjobs360.com}"

echo "=================================================================="
echo "WordPress REST API Access Test"
echo "=================================================================="
echo ""
echo "Site: $WP_URL"
echo "Date: $(date)"
echo ""

##############################################################################
# Test 1: Basic REST API Access (No Authentication)
##############################################################################

echo "----------------------------------------------------------------"
echo "Test 1: Basic REST API Access (No Authentication)"
echo "----------------------------------------------------------------"
echo ""
echo "Testing: $WP_URL/wp-json/"
echo ""

RESPONSE=$(curl -s -w "\n%{http_code}" "$WP_URL/wp-json/" 2>&1)
HTTP_CODE=$(echo "$RESPONSE" | tail -n 1)
BODY=$(echo "$RESPONSE" | sed '$d')

echo "HTTP Status Code: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ SUCCESS${NC}: REST API is accessible"
    echo ""
    echo "Response preview:"
    echo "$BODY" | head -n 10
    echo ""

    # Check if response is JSON (not HTML with CAPTCHA)
    if echo "$BODY" | grep -q "<!DOCTYPE" || echo "$BODY" | grep -q "QUIC.cloud"; then
        echo -e "${RED}❌ WARNING${NC}: Response is HTML (likely CAPTCHA page), not JSON"
        echo "This means bot protection is still active!"
        echo ""
        echo "You need to:"
        echo "1. Log into QUIC.cloud: https://my.quic.cloud/"
        echo "2. Toggle bot protection OFF"
        echo "3. Wait 2-3 minutes"
        echo "4. Run this test again"
        exit 1
    else
        echo -e "${GREEN}✅ Response is valid JSON${NC}"
    fi
elif [ "$HTTP_CODE" = "403" ]; then
    echo -e "${RED}❌ FAILED${NC}: Access forbidden (403)"
    echo ""
    echo "This typically means QUIC.cloud bot protection is blocking access."
    echo ""
    echo "Response preview:"
    echo "$BODY" | head -n 20
    echo ""
    echo "SOLUTION:"
    echo "1. Log into QUIC.cloud: https://my.quic.cloud/"
    echo "   - Email: chessgenius900@gmail.com"
    echo "   - Password: Qsharper$1000"
    echo ""
    echo "2. Navigate to Security → Bot Protection"
    echo "3. Toggle bot protection to OFF"
    echo "4. Click 'Save Changes'"
    echo "5. Click 'Purge Cache'"
    echo "6. Wait 2-3 minutes"
    echo "7. Run this test again"
    echo ""
    exit 1
elif [ "$HTTP_CODE" = "503" ]; then
    echo -e "${RED}❌ FAILED${NC}: Service unavailable (503)"
    echo ""
    echo "This could mean:"
    echo "1. Site is in maintenance mode"
    echo "2. QUIC.cloud is blocking the request"
    echo "3. Origin server is down"
    echo ""
    echo "Response:"
    echo "$BODY"
    echo ""
    exit 1
else
    echo -e "${RED}❌ FAILED${NC}: Unexpected status code"
    echo ""
    echo "Response:"
    echo "$BODY"
    echo ""
    exit 1
fi

echo ""

##############################################################################
# Test 2: Authenticated REST API Access
##############################################################################

echo "----------------------------------------------------------------"
echo "Test 2: Authenticated REST API Access"
echo "----------------------------------------------------------------"
echo ""

if [ -z "$WP_USERNAME" ] || [ -z "$WP_APP_PASSWORD" ]; then
    echo -e "${YELLOW}⚠️  SKIPPED${NC}: WP_USERNAME and WP_APP_PASSWORD not set"
    echo ""
    echo "To run authenticated tests, set environment variables:"
    echo "  export WP_USERNAME='your-username'"
    echo "  export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx'"
    echo ""
else
    echo "Testing: $WP_URL/wp-json/wp/v2/users/me"
    echo "Username: $WP_USERNAME"
    echo ""

    AUTH_RESPONSE=$(curl -s -w "\n%{http_code}" -u "$WP_USERNAME:$WP_APP_PASSWORD" "$WP_URL/wp-json/wp/v2/users/me" 2>&1)
    AUTH_HTTP_CODE=$(echo "$AUTH_RESPONSE" | tail -n 1)
    AUTH_BODY=$(echo "$AUTH_RESPONSE" | sed '$d')

    echo "HTTP Status Code: $AUTH_HTTP_CODE"
    echo ""

    if [ "$AUTH_HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ SUCCESS${NC}: Authentication successful"
        echo ""
        echo "User info:"
        echo "$AUTH_BODY" | python3 -m json.tool 2>/dev/null | head -n 20 || echo "$AUTH_BODY" | head -n 20
        echo ""
    elif [ "$AUTH_HTTP_CODE" = "401" ]; then
        echo -e "${RED}❌ FAILED${NC}: Authentication failed (401)"
        echo ""
        echo "This means your credentials are incorrect."
        echo ""
        echo "Please check:"
        echo "1. WP_USERNAME is correct"
        echo "2. WP_APP_PASSWORD is an Application Password (not login password)"
        echo "3. Application Password format: 'xxxx xxxx xxxx xxxx' (with spaces)"
        echo ""
        echo "To generate a new Application Password:"
        echo "1. Log into WordPress: $WP_URL/wp-admin"
        echo "2. Go to: Users → Profile"
        echo "3. Scroll to 'Application Passwords'"
        echo "4. Enter name: 'TechJobs360 Scraper'"
        echo "5. Click 'Add New Application Password'"
        echo "6. Copy the generated password"
        echo "7. Set as WP_APP_PASSWORD environment variable"
        echo ""
    elif [ "$AUTH_HTTP_CODE" = "403" ]; then
        echo -e "${RED}❌ FAILED${NC}: Access forbidden (403)"
        echo ""
        echo "Bot protection is likely still active for authenticated requests."
        echo "Follow Test 1 solutions above."
        echo ""
    else
        echo -e "${RED}❌ FAILED${NC}: Unexpected status code"
        echo ""
        echo "Response:"
        echo "$AUTH_BODY"
        echo ""
    fi
fi

echo ""

##############################################################################
# Test 3: Full Diagnostic Summary
##############################################################################

echo "=================================================================="
echo "Diagnostic Summary"
echo "=================================================================="
echo ""

if [ "$HTTP_CODE" = "200" ] && ! echo "$BODY" | grep -q "<!DOCTYPE"; then
    echo -e "${GREEN}✅ REST API Access: WORKING${NC}"
else
    echo -e "${RED}❌ REST API Access: BLOCKED${NC}"
fi

if [ -n "$WP_USERNAME" ] && [ -n "$WP_APP_PASSWORD" ]; then
    if [ "$AUTH_HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ WordPress Authentication: WORKING${NC}"
    else
        echo -e "${RED}❌ WordPress Authentication: FAILED${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  WordPress Authentication: NOT TESTED${NC}"
fi

echo ""

##############################################################################
# Test Results and Recommendations
##############################################################################

echo "----------------------------------------------------------------"
echo "Recommendations"
echo "----------------------------------------------------------------"
echo ""

if [ "$HTTP_CODE" != "200" ] || echo "$BODY" | grep -q "<!DOCTYPE"; then
    echo -e "${RED}🚨 CRITICAL ISSUE${NC}: QUIC.cloud bot protection is blocking API access"
    echo ""
    echo "IMMEDIATE ACTION REQUIRED:"
    echo ""
    echo "Step 1: Log into QUIC.cloud"
    echo "  → URL: https://my.quic.cloud/"
    echo "  → Email: chessgenius900@gmail.com"
    echo "  → Password: Qsharper$1000"
    echo ""
    echo "Step 2: Disable Bot Protection"
    echo "  → Navigate: Domains → techjobs360.com → Security"
    echo "  → Find: 'Bot Protection' toggle"
    echo "  → Set to: OFF or Disabled"
    echo "  → Click: 'Save Changes'"
    echo "  → Click: 'Purge Cache'"
    echo ""
    echo "Step 3: Wait & Test"
    echo "  → Wait: 2-3 minutes for changes to propagate"
    echo "  → Test: Run this script again"
    echo "  → Expected: All tests should pass"
    echo ""
    echo "See QUIC_CLOUD_TOGGLE_GUIDE.md for detailed visual guide."
    echo ""
elif [ -z "$WP_USERNAME" ] || [ -z "$WP_APP_PASSWORD" ]; then
    echo -e "${YELLOW}⚠️  PARTIAL SUCCESS${NC}: REST API is accessible, but authentication not tested"
    echo ""
    echo "Next steps:"
    echo "1. Set environment variables:"
    echo "   export WP_USERNAME='your-username'"
    echo "   export WP_APP_PASSWORD='xxxx xxxx xxxx xxxx'"
    echo ""
    echo "2. Run this test again to verify authentication"
    echo ""
    echo "3. Once authentication works, you can run the scraper:"
    echo "   python job_scraper.py"
    echo ""
elif [ "$AUTH_HTTP_CODE" != "200" ]; then
    echo -e "${YELLOW}⚠️  AUTHENTICATION ISSUE${NC}: REST API accessible, but credentials incorrect"
    echo ""
    echo "Fix authentication:"
    echo "1. Check WP_USERNAME is correct WordPress username"
    echo "2. Generate new Application Password:"
    echo "   → Log into: $WP_URL/wp-admin"
    echo "   → Go to: Users → Profile"
    echo "   → Find: 'Application Passwords' section"
    echo "   → Create new password for 'TechJobs360 Scraper'"
    echo "3. Update WP_APP_PASSWORD environment variable"
    echo "4. Run this test again"
    echo ""
else
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo ""
    echo "Your WordPress REST API is fully accessible and authenticated."
    echo ""
    echo "Next steps:"
    echo "1. Run the scraper manually to test job posting:"
    echo "   python job_scraper.py"
    echo ""
    echo "2. Or trigger GitHub Actions workflow:"
    echo "   → Go to: https://github.com/arunbabusb/techjobs360-scraper/actions"
    echo "   → Click: 'scraper.yml'"
    echo "   → Click: 'Run workflow'"
    echo ""
    echo "3. Monitor results:"
    echo "   → Check posted_jobs.json for new entries"
    echo "   → Check WordPress admin for new job posts"
    echo "   → Verify jobs appear on: $WP_URL"
    echo ""
    echo "The scraper should now work correctly! 🚀"
    echo ""
fi

echo "=================================================================="
echo "Test completed: $(date)"
echo "=================================================================="
echo ""

# Exit with appropriate code
if [ "$HTTP_CODE" = "200" ] && [ "$AUTH_HTTP_CODE" = "200" ]; then
    exit 0
else
    exit 1
fi
