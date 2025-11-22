#!/usr/bin/env python3
"""
Diagnostic script to test job scraper functionality
Tests each source independently and WordPress connectivity
"""

import os
import sys
from job_scraper import (
    query_jsearch, query_remotive, query_remoteok,
    parse_weworkremotely, load_config
)
import requests

def test_wordpress_auth():
    """Test WordPress REST API authentication"""
    print("\n" + "="*60)
    print("TESTING WORDPRESS AUTHENTICATION")
    print("="*60)

    wp_url = os.environ.get("WP_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APP_PASSWORD")

    if not wp_url or not wp_user or not wp_pass:
        print("❌ Missing WordPress credentials in environment variables")
        print("   Required: WP_URL, WP_USERNAME, WP_APP_PASSWORD")
        return False

    print(f"✓ WP_URL: {wp_url}")
    print(f"✓ WP_USERNAME: {wp_user}")
    print(f"✓ WP_APP_PASSWORD: {'*' * len(wp_pass)} (hidden)")

    try:
        resp = requests.get(
            f"{wp_url.rstrip('/')}/wp-json/wp/v2/users/me",
            auth=(wp_user, wp_pass),
            timeout=10
        )

        if resp.status_code == 200:
            user_data = resp.json()
            print(f"✅ WordPress auth successful!")
            print(f"   User: {user_data.get('name')} (ID: {user_data.get('id')})")
            return True
        else:
            print(f"❌ WordPress auth failed: HTTP {resp.status_code}")
            print(f"   Response: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ WordPress connection error: {e}")
        return False


def test_source(name, func, query, **kwargs):
    """Test a single job source"""
    print(f"\n{'='*60}")
    print(f"TESTING SOURCE: {name}")
    print(f"{'='*60}")
    print(f"Query: {query}")

    try:
        jobs = func(query, **kwargs)
        count = len(jobs)

        if count > 0:
            print(f"✅ {name}: Found {count} jobs")
            print(f"\nSample job:")
            job = jobs[0]
            print(f"  Title: {job.get('title')}")
            print(f"  Company: {job.get('company')}")
            print(f"  Location: {job.get('location')}")
            print(f"  URL: {job.get('url', '')[:60]}...")
            return True
        else:
            print(f"⚠️  {name}: No jobs found (may be normal)")
            return True
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*60)
    print("TECHJOBS360 SCRAPER DIAGNOSTICS")
    print("="*60)

    # Load config
    try:
        config = load_config()
        print("✅ config.yaml loaded successfully")

        sources = config.get('sources', [])
        enabled_sources = [s['type'] for s in sources if s.get('enabled')]
        print(f"✓ Enabled sources: {', '.join(enabled_sources)}")
    except Exception as e:
        print(f"❌ Failed to load config.yaml: {e}")
        sys.exit(1)

    # Test WordPress auth
    wp_ok = test_wordpress_auth()

    # Test each source
    results = {}

    # Only test sources that have implementations
    if os.environ.get("JSEARCH_API_KEY"):
        results['jsearch'] = test_source(
            "JSearch (RapidAPI)",
            query_jsearch,
            "software engineer",
            location="San Francisco",
            per_page=5
        )
    else:
        print(f"\n⚠️  Skipping JSearch - no JSEARCH_API_KEY set")

    results['remotive'] = test_source(
        "Remotive",
        query_remotive,
        "python developer",
        limit=5
    )

    results['remoteok'] = test_source(
        "RemoteOK",
        query_remoteok,
        "backend",
        limit=5
    )

    results['weworkremotely'] = test_source(
        "WeWorkRemotely",
        parse_weworkremotely,
        "software engineer",
        limit=5
    )

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"WordPress Auth: {'✅ PASS' if wp_ok else '❌ FAIL'}")

    for source, success in results.items():
        status = '✅ PASS' if success else '❌ FAIL'
        print(f"{source}: {status}")

    total_pass = sum(1 for v in results.values() if v)
    total_tests = len(results)

    print(f"\nResults: {total_pass}/{total_tests} sources working")

    if not wp_ok:
        print("\n⚠️  WARNING: WordPress authentication failed!")
        print("   Jobs cannot be posted without valid credentials.")
        print("   Please check your WP_URL, WP_USERNAME, and WP_APP_PASSWORD")
    elif total_pass == 0:
        print("\n⚠️  WARNING: No job sources are working!")
        print("   Check your API keys and network connectivity")
    elif total_pass < total_tests:
        print(f"\n⚠️  WARNING: {total_tests - total_pass} source(s) failed")
    else:
        print("\n✅ All systems operational!")


if __name__ == "__main__":
    main()
