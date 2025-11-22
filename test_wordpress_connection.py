#!/usr/bin/env python3
"""
WordPress Connection Tester for TechJobs360
Tests REST API access and guides Application Password creation
"""

import requests
import sys

# WordPress credentials
WP_URL = "https://www.techjobs360.com"
WP_USERNAME = "admintech"

print("=" * 70)
print("         TechJobs360 - WordPress Connection Test")
print("=" * 70)
print()
print(f"WordPress URL: {WP_URL}")
print(f"Username: {WP_USERNAME}")
print()

# Step 1: Test if WordPress site is accessible
print("Step 1: Testing WordPress site accessibility...")
print("-" * 70)
try:
    resp = requests.get(WP_URL, timeout=10)
    if resp.status_code == 200:
        print("✅ WordPress site is accessible")
    else:
        print(f"⚠️  Site returned status code: {resp.status_code}")
except Exception as e:
    print(f"❌ Cannot access WordPress site: {e}")
    print()
    print("Possible issues:")
    print("  - Site is down")
    print("  - URL is incorrect")
    print("  - Network/firewall blocking")
    sys.exit(1)

print()

# Step 2: Test if REST API is enabled
print("Step 2: Testing WordPress REST API...")
print("-" * 70)
try:
    api_url = f"{WP_URL}/wp-json/wp/v2"
    resp = requests.get(api_url, timeout=10)
    if resp.status_code == 200:
        print("✅ WordPress REST API is enabled and accessible")
    else:
        print(f"❌ REST API returned status code: {resp.status_code}")
        print()
        print("The WordPress REST API might be disabled.")
        print("To enable it:")
        print("  1. Login to WordPress admin")
        print("  2. Check if any security plugin is blocking REST API")
        print("  3. Go to Settings → Permalinks and click Save")
        sys.exit(1)
except Exception as e:
    print(f"❌ Cannot access REST API: {e}")
    sys.exit(1)

print()

# Step 3: Check if Application Passwords are supported
print("Step 3: Checking Application Password support...")
print("-" * 70)

# Application Passwords were added in WordPress 5.6
try:
    # Try to access the application-passwords endpoint
    app_pass_url = f"{WP_URL}/wp-json/wp/v2/users/me/application-passwords"
    resp = requests.get(app_pass_url, timeout=10)

    if resp.status_code == 401:
        print("✅ Application Passwords are supported (authentication required)")
        print()
        print("=" * 70)
        print("         NEXT STEP: Create Application Password")
        print("=" * 70)
        print()
        print("Follow these steps to create an Application Password:")
        print()
        print("1. Login to WordPress Admin:")
        print(f"   → Go to: {WP_URL}/wp-admin")
        print(f"   → Username: {WP_USERNAME}")
        print("   → Use your regular password")
        print()
        print("2. Navigate to Your Profile:")
        print("   → Click 'Users' → 'Profile' (or your name in top right)")
        print()
        print("3. Scroll to 'Application Passwords' section")
        print("   → You should see it near the bottom of the page")
        print()
        print("4. Create New Application Password:")
        print("   → In 'New Application Password Name' field, type: TechJobs360")
        print("   → Click: 'Add New Application Password'")
        print()
        print("5. COPY THE PASSWORD:")
        print("   → WordPress will show: xxxx xxxx xxxx xxxx")
        print("   → COPY THIS ENTIRE PASSWORD (with spaces)")
        print("   → You will only see it once!")
        print()
        print("6. Run the deployment script:")
        print("   → After copying the password, run:")
        print("   → bash deploy_to_wordpress.sh")
        print("   → When prompted, paste the Application Password")
        print()

    elif resp.status_code == 404:
        print("❌ Application Passwords are NOT supported")
        print()
        print("Your WordPress version might be older than 5.6")
        print()
        print("Options:")
        print("  1. Update WordPress to 5.6 or newer (recommended)")
        print("  2. Install 'Application Passwords' plugin")
        print()

    else:
        print(f"⚠️  Unexpected response: {resp.status_code}")

except Exception as e:
    print(f"⚠️  Could not check Application Password support: {e}")

print()
print("=" * 70)
print("For more help, see: QUICK_START.md")
print("=" * 70)
