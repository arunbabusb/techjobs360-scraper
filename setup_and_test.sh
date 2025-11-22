#!/bin/bash
set -e

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   TechJobs360 Scraper - Quick Setup & Test Script         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check if credentials are set
echo "Step 1: Checking credentials..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -z "$WP_URL" ] || [ -z "$WP_USERNAME" ] || [ -z "$WP_APP_PASSWORD" ]; then
    echo -e "${RED}❌ WordPress credentials not set!${NC}"
    echo ""
    echo "Please set the following environment variables:"
    echo ""
    echo "  export WP_URL=\"https://your-wordpress-site.com\""
    echo "  export WP_USERNAME=\"your-username\""
    echo "  export WP_APP_PASSWORD=\"xxxx xxxx xxxx xxxx\""
    echo ""
    echo "To get Application Password:"
    echo "  1. Login to WordPress Admin"
    echo "  2. Go to: Users → Your Profile"
    echo "  3. Scroll to: Application Passwords"
    echo "  4. Enter name: TechJobs360"
    echo "  5. Click: Add New Application Password"
    echo "  6. Copy the password (format: xxxx xxxx xxxx xxxx)"
    echo ""
    echo "After setting variables, run this script again:"
    echo "  bash setup_and_test.sh"
    exit 1
fi

echo -e "${GREEN}✅ Credentials found:${NC}"
echo "   WP_URL: ${WP_URL}"
echo "   WP_USERNAME: ${WP_USERNAME}"
echo "   WP_APP_PASSWORD: ****"
echo ""

# Step 2: Install dependencies
echo "Step 2: Installing Python dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi
echo ""

# Step 3: Run diagnostics
echo "Step 3: Running diagnostics..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python diagnose.py; then
    echo -e "${GREEN}✅ All diagnostics passed${NC}"
else
    echo -e "${RED}❌ Diagnostics failed. Please fix issues above.${NC}"
    exit 1
fi
echo ""

# Step 4: Run scraper (test mode - single continent)
echo "Step 4: Running scraper in test mode..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Running scraper for Asia only (test mode)...${NC}"
export PROCESS_CONTINENT="asia"
export AUTO_ROTATE="false"

if python job_scraper.py; then
    echo ""
    echo -e "${GREEN}✅ Scraper completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Scraper failed. Check errors above.${NC}"
    exit 1
fi
echo ""

# Step 5: Check results
echo "Step 5: Checking results..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

DEDUP_COUNT=$(jq 'length' posted_jobs.json 2>/dev/null || echo "0")
echo "Jobs in deduplication database: ${DEDUP_COUNT}"

if [ "$DEDUP_COUNT" -gt "20" ]; then
    echo -e "${GREEN}✅ New jobs were added!${NC}"
    echo ""
    echo "Latest jobs:"
    jq '.[-5:] | .[] | {title, company, location}' posted_jobs.json 2>/dev/null || echo "Cannot read jobs"
else
    echo -e "${YELLOW}⚠️  No new jobs added (might be duplicates)${NC}"
fi
echo ""

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    SETUP COMPLETE                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Next Steps:"
echo ""
echo "1. Check your WordPress site for new job posts:"
echo "   ${WP_URL}/wp-admin/edit.php?post_type=post"
echo ""
echo "2. To run scraper for all continents:"
echo "   python job_scraper.py"
echo ""
echo "3. To set up GitHub Actions (automated runs):"
echo "   - Go to: ${WP_URL}/settings/secrets/actions"
echo "   - Add secrets: WP_URL, WP_USERNAME, WP_APP_PASSWORD"
echo "   - Workflow will run automatically 4x daily"
echo ""
echo "4. To deploy to Heroku:"
echo "   - See: HEROKU_DEPLOYMENT.md"
echo ""
