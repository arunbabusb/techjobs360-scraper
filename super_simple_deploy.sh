#!/bin/bash

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     TechJobs360 - SUPER SIMPLE Deployment                 ║"
echo "║     Just answer a few questions and jobs will flow!       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Step 1: Get Application Password
echo "STEP 1: Get Your Application Password"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Open your browser and go to:"
echo "   https://www.techjobs360.com/wp-admin"
echo ""
echo "2. Login with username: admintech"
echo ""
echo "3. Click your name (top right) → Edit Profile"
echo ""
echo "4. Scroll down to 'Application Passwords' section"
echo ""
echo "5. Type 'TechJobs360' in the name field"
echo ""
echo "6. Click 'Add New Application Password'"
echo ""
echo "7. COPY the password shown (format: xxxx xxxx xxxx xxxx)"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Press ENTER when you have copied the Application Password..."
echo ""

# Step 2: Paste the password
echo "STEP 2: Enter Application Password"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -s -p "Paste your Application Password here: " APP_PASSWORD
echo ""

if [ -z "$APP_PASSWORD" ]; then
    echo ""
    echo "❌ No password entered. Please run the script again."
    exit 1
fi

# Export credentials
export WP_URL="https://www.techjobs360.com"
export WP_USERNAME="admintech"
export WP_APP_PASSWORD="$APP_PASSWORD"

echo ""
echo "✅ Credentials set!"
echo ""

# Step 3: Install dependencies
echo "STEP 3: Installing Dependencies"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
pip install -q -r requirements.txt 2>/dev/null
echo "✅ Dependencies installed"
echo ""

# Step 4: Test connection
echo "STEP 4: Testing WordPress Connection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Quick Python test
python3 << 'PYEND'
import requests
import os

wp_url = os.environ.get('WP_URL')
wp_user = os.environ.get('WP_USERNAME')
wp_pass = os.environ.get('WP_APP_PASSWORD')

print(f"Testing: {wp_url}/wp-json/wp/v2/users/me")

try:
    resp = requests.get(
        f"{wp_url}/wp-json/wp/v2/users/me",
        auth=(wp_user, wp_pass),
        timeout=15
    )

    if resp.status_code == 200:
        data = resp.json()
        print(f"✅ Connected successfully as: {data.get('name', 'Unknown')}")
        print(f"✅ User ID: {data.get('id')}")
        exit(0)
    else:
        print(f"❌ Authentication failed: HTTP {resp.status_code}")
        print(f"Response: {resp.text[:200]}")
        exit(1)
except Exception as e:
    print(f"❌ Connection error: {e}")
    exit(1)
PYEND

if [ $? -ne 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  CONNECTION FAILED"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Possible issues:"
    echo "  1. Wrong Application Password - Try creating a new one"
    echo "  2. WordPress REST API disabled - Check plugin settings"
    echo "  3. Site still having issues - Check hosting provider"
    echo ""
    echo "Try again: bash super_simple_deploy.sh"
    exit 1
fi

echo ""

# Step 5: Run scraper
echo "STEP 5: Running Job Scraper"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "This will collect jobs from 9 sources and post to your site."
echo "It will take about 5-10 minutes."
echo ""
read -p "Ready to start? (yes/no): " START

if [ "$START" != "yes" ] && [ "$START" != "y" ]; then
    echo "Cancelled. Run again when ready: bash super_simple_deploy.sh"
    exit 0
fi

echo ""
echo "🚀 Starting scraper..."
echo ""

# Run the scraper
python job_scraper.py

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                    ✅ SUCCESS!                             ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Jobs have been posted to your WordPress site!"
    echo ""
    echo "📍 Check your site:"
    echo "   Admin: https://www.techjobs360.com/wp-admin/edit.php?post_type=post"
    echo "   Public: https://www.techjobs360.com"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔄 To run again: bash super_simple_deploy.sh"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
else
    echo ""
    echo "❌ Scraper encountered errors. Check messages above."
fi
