#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        TechJobs360 Scraper - WordPress Deployment           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# WordPress credentials (URL and username are pre-configured)
export WP_URL="https://www.techjobs360.com"
export WP_USERNAME="admintech"

echo -e "${BLUE}WordPress URL:${NC} $WP_URL"
echo -e "${BLUE}WordPress Username:${NC} $WP_USERNAME"
echo ""

# Prompt for Application Password
echo -e "${YELLOW}Please enter your WordPress Application Password:${NC}"
echo "(Format: xxxx xxxx xxxx xxxx - paste it exactly as shown in WordPress)"
echo ""
read -s -p "Application Password: " WP_APP_PASSWORD
export WP_APP_PASSWORD
echo ""
echo ""

if [ -z "$WP_APP_PASSWORD" ]; then
    echo -e "${RED}❌ No password entered!${NC}"
    echo ""
    echo "Please run the script again and paste your Application Password."
    echo "If you haven't created one yet, run:"
    echo "  python test_wordpress_connection.py"
    exit 1
fi

# Check if dependencies are installed
echo "Checking dependencies..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if ! python -c "import requests" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${GREEN}✅ Dependencies already installed${NC}"
fi
echo ""

# Run diagnostics
echo "Running diagnostics..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if python diagnose.py; then
    echo -e "${GREEN}✅ All diagnostics passed!${NC}"
else
    echo -e "${RED}❌ Diagnostics failed${NC}"
    echo ""
    echo "Please fix the issues above and try again."
    exit 1
fi
echo ""

# Ask if user wants to run scraper
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}Ready to run the scraper!${NC}"
echo ""
echo "This will:"
echo "  1. Collect jobs from 9 different sources"
echo "  2. Post them to your WordPress site"
echo "  3. Take approximately 5-10 minutes"
echo ""
read -p "Do you want to continue? (yes/no): " CONTINUE

if [ "$CONTINUE" != "yes" ] && [ "$CONTINUE" != "y" ]; then
    echo ""
    echo "Deployment cancelled."
    echo "When you're ready, run: bash deploy_to_wordpress.sh"
    exit 0
fi

echo ""
echo "Starting scraper..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Run scraper
if python job_scraper.py; then
    echo ""
    echo -e "${GREEN}✅ Scraper completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}❌ Scraper failed${NC}"
    echo "Check the error messages above for details."
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Checking results..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count jobs in database
if command -v jq >/dev/null 2>&1; then
    JOB_COUNT=$(jq 'length' posted_jobs.json 2>/dev/null || echo "0")
    echo -e "${GREEN}Jobs in database: $JOB_COUNT${NC}"

    if [ "$JOB_COUNT" -gt "20" ]; then
        echo ""
        echo "Latest jobs posted:"
        jq '.[-5:] | .[] | {title, company, location}' posted_jobs.json 2>/dev/null || true
    fi
else
    echo "Install 'jq' to see job statistics: sudo apt-get install jq"
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    DEPLOYMENT COMPLETE!                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}✅ Jobs have been posted to your WordPress site!${NC}"
echo ""
echo "View your jobs at:"
echo -e "  ${BLUE}$WP_URL/wp-admin/edit.php?post_type=post${NC}"
echo ""
echo "Or view them publicly at:"
echo -e "  ${BLUE}$WP_URL${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Next steps:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Check your WordPress site for new jobs"
echo ""
echo "2. Set up automated runs (optional):"
echo "   • GitHub Actions - Free, runs 4x daily automatically"
echo "     See: QUICK_START.md (Option 2)"
echo ""
echo "   • Heroku - Dedicated hosting, custom scheduling"
echo "     See: HEROKU_DEPLOYMENT.md"
echo ""
echo "3. To run scraper again manually:"
echo "   bash deploy_to_wordpress.sh"
echo ""
echo "4. For troubleshooting:"
echo "   See: TROUBLESHOOTING.md"
echo ""
