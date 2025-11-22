#!/usr/bin/env python3
"""
TechJobs360 Diagnostic Tool
Tests all components and identifies configuration issues
"""

import os
import sys
import json
from pathlib import Path

def check_environment():
    """Check if all required environment variables are set"""
    print("=" * 60)
    print("ENVIRONMENT VARIABLES CHECK")
    print("=" * 60)

    required = ["WP_URL", "WP_USERNAME", "WP_APP_PASSWORD"]
    optional = ["JSEARCH_API_KEY", "PROCESS_CONTINENT", "AUTO_ROTATE"]

    issues = []

    for var in required:
        val = os.environ.get(var)
        if val:
            print(f"✅ {var}: {'*' * min(len(val), 20)}")
        else:
            print(f"❌ {var}: NOT SET (REQUIRED)")
            issues.append(f"Missing {var}")

    for var in optional:
        val = os.environ.get(var)
        if val:
            print(f"✅ {var}: {val[:30]}...")
        else:
            print(f"⚠️  {var}: Not set (optional)")

    return issues

def test_wordpress_connection():
    """Test WordPress REST API connectivity"""
    print("\n" + "=" * 60)
    print("WORDPRESS CONNECTION TEST")
    print("=" * 60)

    import requests

    wp_url = os.environ.get("WP_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APP_PASSWORD")

    if not all([wp_url, wp_user, wp_pass]):
        print("❌ WordPress credentials not set. Cannot test connection.")
        return ["WordPress credentials missing"]

    issues = []

    try:
        # Test REST API availability
        api_url = wp_url.rstrip("/") + "/wp-json/wp/v2"
        print(f"Testing: {api_url}")

        resp = requests.get(api_url, timeout=10)
        if resp.status_code == 200:
            print("✅ WordPress REST API is accessible")
        else:
            print(f"❌ WordPress REST API returned: {resp.status_code}")
            issues.append(f"REST API error: {resp.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to WordPress: {e}")
        issues.append(f"Connection error: {e}")

    try:
        # Test authentication
        auth_url = wp_url.rstrip("/") + "/wp-json/wp/v2/users/me"
        resp = requests.get(auth_url, auth=(wp_user, wp_pass), timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Authentication successful as: {data.get('name', 'Unknown')}")
        else:
            print(f"❌ Authentication failed: {resp.status_code}")
            issues.append(f"Auth failed: {resp.status_code}")
    except Exception as e:
        print(f"❌ Authentication test error: {e}")
        issues.append(f"Auth error: {e}")

    return issues

def test_job_sources():
    """Test all job source APIs"""
    print("\n" + "=" * 60)
    print("JOB SOURCES TEST")
    print("=" * 60)

    # Import after adding parent to path
    sys.path.insert(0, str(Path(__file__).parent))
    from job_scraper import (
        query_remotive, query_remoteok, query_arbeitnow,
        query_jobicy, query_himalayas, parse_weworkremotely
    )

    sources = [
        ("Remotive", query_remotive, "python"),
        ("RemoteOK", query_remoteok, "developer"),
        ("Arbeitnow", query_arbeitnow, "engineer"),
        ("Jobicy", query_jobicy, "software"),
        ("Himalayas", query_himalayas, "backend"),
        ("WeWorkRemotely", parse_weworkremotely, "frontend"),
    ]

    issues = []

    for name, func, query in sources:
        try:
            print(f"\nTesting {name}...")
            jobs = func(query, limit=5)
            if jobs:
                print(f"✅ {name}: Found {len(jobs)} jobs")
                print(f"   Sample: {jobs[0].get('title', 'No title')}")
            else:
                print(f"⚠️  {name}: No jobs found (may be rate-limited or query-specific)")
        except Exception as e:
            print(f"❌ {name}: Error - {e}")
            issues.append(f"{name} failed: {e}")

    return issues

def check_deduplication_database():
    """Check deduplication database status"""
    print("\n" + "=" * 60)
    print("DEDUPLICATION DATABASE CHECK")
    print("=" * 60)

    dedup_path = Path(__file__).parent / "posted_jobs.json"

    if not dedup_path.exists():
        print("⚠️  No deduplication database found (will be created on first run)")
        return []

    try:
        with open(dedup_path) as f:
            data = json.load(f)

        print(f"✅ Database loaded: {len(data)} jobs tracked")

        if data:
            latest = max(data, key=lambda x: x.get("first_seen", 0))
            import time
            age_days = (time.time() - latest.get("first_seen", 0)) / 86400
            print(f"   Latest job: {latest.get('title', 'Unknown')}")
            print(f"   Added: {age_days:.1f} days ago")

            if len(data) > 5000:
                print(f"⚠️  Database is large ({len(data)} entries). Consider pruning old entries.")
                return [f"Large database: {len(data)} entries"]

        return []
    except Exception as e:
        print(f"❌ Error reading database: {e}")
        return [f"Database error: {e}"]

def check_configuration():
    """Check config.yaml settings"""
    print("\n" + "=" * 60)
    print("CONFIGURATION CHECK")
    print("=" * 60)

    import yaml
    config_path = Path(__file__).parent / "config.yaml"

    if not config_path.exists():
        print("❌ config.yaml not found!")
        return ["config.yaml missing"]

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Check post_status
        post_status = config.get("posting", {}).get("post_status")
        if post_status == "publish":
            print(f"✅ Post status: {post_status} (jobs will be published)")
        elif post_status == "draft":
            print(f"⚠️  Post status: {post_status} (jobs will be DRAFTS - not visible!)")
        else:
            print(f"❌ Post status: {post_status} (invalid)")

        # Check enabled sources
        sources = config.get("sources", [])
        enabled_sources = [s.get("type") for s in sources if s.get("enabled")]
        print(f"✅ Enabled sources ({len(enabled_sources)}): {', '.join(enabled_sources)}")

        # Check continents
        continents = config.get("continents", [])
        print(f"✅ Configured continents: {len(continents)}")

        issues = []
        if post_status == "draft":
            issues.append("Post status is 'draft' - jobs won't be visible")

        return issues
    except Exception as e:
        print(f"❌ Error reading config: {e}")
        return [f"Config error: {e}"]

def main():
    """Run all diagnostics"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "TechJobs360 DIAGNOSTIC TOOL" + " " * 15 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    all_issues = []

    all_issues.extend(check_environment())
    all_issues.extend(check_configuration())
    all_issues.extend(check_deduplication_database())
    all_issues.extend(test_wordpress_connection())

    try:
        all_issues.extend(test_job_sources())
    except ImportError as e:
        print(f"\n⚠️  Cannot test job sources: {e}")
        print("   (This is normal if dependencies aren't installed)")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if all_issues:
        print(f"\n❌ Found {len(all_issues)} issue(s):\n")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")
        print("\n⚠️  Please fix these issues before running the scraper.")
        sys.exit(1)
    else:
        print("\n✅ All checks passed! Your scraper is ready to run.")
        print("\nNext steps:")
        print("   1. Run: python job_scraper.py")
        print("   2. Check your WordPress site for new jobs")
        print("   3. Monitor GitHub Actions for automated runs")
        sys.exit(0)

if __name__ == "__main__":
    main()
