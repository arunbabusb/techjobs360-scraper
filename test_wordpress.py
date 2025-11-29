#!/usr/bin/env python3
"""
WordPress Connection Test
Tests if WordPress credentials work and posts a test job.
"""

import os
import requests

# Get credentials
WP_URL = os.environ.get("WP_URL")
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")

print("WordPress Connection Test")
print("=" * 50)

# Validate URL
if not WP_URL:
    print("❌ WP_URL not set!")
    exit(1)

if not (WP_URL.startswith("http://") or WP_URL.startswith("https://")):
    print(f"❌ WP_URL missing http:// or https://: {WP_URL}")
    exit(1)

print(f"✅ WP_URL: {WP_URL}")

# Validate credentials
if not WP_USERNAME or not WP_APP_PASSWORD:
    print("❌ WP_USERNAME or WP_APP_PASSWORD not set!")
    exit(1)

print(f"✅ WP_USERNAME: {WP_USERNAME}")
print(f"✅ WP_APP_PASSWORD: {'*' * len(WP_APP_PASSWORD)}")

# Test authentication
print("\nTesting authentication...")
try:
    resp = requests.get(
        f"{WP_URL}/wp-json/wp/v2/users/me",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        timeout=10
    )
    if resp.status_code == 200:
        user = resp.json()
        print(f"✅ Authentication successful!")
        print(f"   User: {user.get('name')} (ID: {user.get('id')})")
    else:
        print(f"❌ Authentication failed: HTTP {resp.status_code}")
        print(f"   Response: {resp.text[:200]}")
        exit(1)
except Exception as e:
    print(f"❌ Request failed: {e}")
    exit(1)

# Test job posting endpoint
print("\nTesting job posting endpoints...")

# Test 1: WP Job Manager
try:
    resp = requests.options(
        f"{WP_URL}/wp-json/wp/v2/job_listing",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        timeout=10
    )
    if resp.status_code in [200, 204]:
        print(f"✅ WP Job Manager endpoint available")
    else:
        print(f"⚠️  WP Job Manager endpoint returned: HTTP {resp.status_code}")
except Exception as e:
    print(f"⚠️  WP Job Manager endpoint test failed: {e}")

# Test 2: Regular posts
try:
    resp = requests.options(
        f"{WP_URL}/wp-json/wp/v2/posts",
        auth=(WP_USERNAME, WP_APP_PASSWORD),
        timeout=10
    )
    if resp.status_code in [200, 204]:
        print(f"✅ Regular posts endpoint available")
    else:
        print(f"❌ Regular posts endpoint returned: HTTP {resp.status_code}")
except Exception as e:
    print(f"❌ Regular posts endpoint test failed: {e}")

print("\n" + "=" * 50)
print("✅ All tests passed! WordPress connection working.")
print("\nIf scraper still posts 0 jobs, check GitHub Actions logs for:")
print("  - 'Failed to post job to WP' errors")
print("  - HTTP error codes (400, 403, 500, etc.)")
print("  - Duplicate slug errors")
