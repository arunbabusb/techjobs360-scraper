#!/usr/bin/env python3
"""
TechJobs360 Posting Diagnostic Script
Tests all components to identify why jobs aren't being posted
"""

import os
import sys
import json
import requests
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def test_env_vars():
    """Test if environment variables are set"""
    print(f"\n{BLUE}=== Testing Environment Variables ==={RESET}")

    vars_to_check = {
        "WP_URL": os.environ.get("WP_URL"),
        "WP_USERNAME": os.environ.get("WP_USERNAME"),
        "WP_APP_PASSWORD": os.environ.get("WP_APP_PASSWORD"),
        "JSEARCH_API_KEY": os.environ.get("JSEARCH_API_KEY"),
    }

    all_good = True
    for var_name, var_value in vars_to_check.items():
        if var_value:
            # Mask sensitive values
            if "PASSWORD" in var_name or "KEY" in var_name:
                display_value = var_value[:4] + "..." + var_value[-4:] if len(var_value) > 8 else "***"
            else:
                display_value = var_value
            print(f"{GREEN}✓{RESET} {var_name}: {display_value}")
        else:
            print(f"{RED}✗{RESET} {var_name}: NOT SET")
            if var_name != "JSEARCH_API_KEY":  # JSEARCH is optional
                all_good = False

    return all_good

def test_wordpress_auth():
    """Test WordPress authentication"""
    print(f"\n{BLUE}=== Testing WordPress Authentication ==={RESET}")

    wp_url = os.environ.get("WP_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APP_PASSWORD")

    if not (wp_url and wp_user and wp_pass):
        print(f"{RED}✗{RESET} Missing WordPress credentials")
        return False

    try:
        # Test auth endpoint
        url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/users/me"
        print(f"Testing: {url}")

        resp = requests.get(url, auth=(wp_user, wp_pass), timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            print(f"{GREEN}✓{RESET} Authentication successful!")
            print(f"  User: {data.get('name')} (ID: {data.get('id')})")
            print(f"  Roles: {', '.join(data.get('roles', []))}")
            return True
        elif resp.status_code == 403:
            print(f"{RED}✗{RESET} Authentication failed: 403 Forbidden")
            print(f"  Response: {resp.text[:200]}")
            return False
        elif resp.status_code == 503:
            print(f"{RED}✗{RESET} WordPress site is unavailable: 503 Service Unavailable")
            print(f"  The site might be in maintenance mode")
            return False
        else:
            print(f"{RED}✗{RESET} Authentication failed: {resp.status_code}")
            print(f"  Response: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"{RED}✗{RESET} Connection error: {e}")
        return False

def test_wordpress_posting():
    """Test if we can create posts"""
    print(f"\n{BLUE}=== Testing WordPress Post Creation ==={RESET}")

    wp_url = os.environ.get("WP_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APP_PASSWORD")

    if not (wp_url and wp_user and wp_pass):
        print(f"{RED}✗{RESET} Missing WordPress credentials")
        return False

    try:
        url = f"{wp_url.rstrip('/')}/wp-json/wp/v2/posts"

        # Try to create a draft post
        payload = {
            "title": "Test Post - Diagnostic Script",
            "content": "This is a test post from the diagnostic script. You can delete this.",
            "status": "draft"
        }

        resp = requests.post(url, auth=(wp_user, wp_pass), json=payload, timeout=10)

        if resp.status_code == 201:
            data = resp.json()
            post_id = data.get("id")
            print(f"{GREEN}✓{RESET} Successfully created test post!")
            print(f"  Post ID: {post_id}")
            print(f"  URL: {data.get('link')}")

            # Clean up - delete the test post
            delete_url = f"{url}/{post_id}"
            requests.delete(delete_url, auth=(wp_user, wp_pass), timeout=10)
            print(f"{GREEN}✓{RESET} Test post deleted successfully")
            return True
        elif resp.status_code == 503:
            print(f"{RED}✗{RESET} WordPress site is unavailable: 503 Service Unavailable")
            print(f"  The site might be in maintenance mode")
            return False
        else:
            print(f"{RED}✗{RESET} Failed to create post: {resp.status_code}")
            print(f"  Response: {resp.text[:500]}")
            return False
    except Exception as e:
        print(f"{RED}✗{RESET} Error creating post: {e}")
        return False

def test_job_sources():
    """Test if job sources are returning data"""
    print(f"\n{BLUE}=== Testing Job Sources ==={RESET}")

    # Import the scraper functions
    sys.path.insert(0, str(Path(__file__).parent))
    try:
        from job_scraper import query_remotive, query_remoteok, parse_weworkremotely, query_jsearch
    except ImportError as e:
        print(f"{RED}✗{RESET} Failed to import job_scraper.py: {e}")
        return False

    sources = [
        ("Remotive", lambda: query_remotive("python developer", limit=5)),
        ("RemoteOK", lambda: query_remoteok("backend", limit=5)),
        ("WeWorkRemotely", lambda: parse_weworkremotely("software engineer", limit=5)),
    ]

    # Only test JSearch if API key is available
    if os.environ.get("JSEARCH_API_KEY"):
        sources.append(("JSearch", lambda: query_jsearch("developer", per_page=5)))

    any_working = False
    for source_name, source_func in sources:
        try:
            print(f"\nTesting {source_name}...", end=" ")
            jobs = source_func()
            if jobs and len(jobs) > 0:
                print(f"{GREEN}✓{RESET} Found {len(jobs)} jobs")
                # Show first job as example
                if jobs[0]:
                    print(f"  Example: {jobs[0].get('title', 'N/A')} at {jobs[0].get('company', 'N/A')}")
                any_working = True
            else:
                print(f"{YELLOW}⚠{RESET} No jobs found (might be normal)")
        except Exception as e:
            print(f"{RED}✗{RESET} Error: {e}")

    return any_working

def check_dedup_file():
    """Check deduplication file status"""
    print(f"\n{BLUE}=== Checking Deduplication File ==={RESET}")

    dedup_path = Path(__file__).parent / "posted_jobs.json"

    if not dedup_path.exists():
        print(f"{YELLOW}⚠{RESET} posted_jobs.json not found (will be created)")
        return True

    try:
        with open(dedup_path, "r") as f:
            data = json.load(f)

        print(f"{GREEN}✓{RESET} posted_jobs.json exists")
        print(f"  Entries: {len(data)}")

        if len(data) == 0:
            print(f"  {GREEN}Empty - all jobs will be new{RESET}")
        elif len(data) < 10:
            print(f"  {GREEN}Few entries - most jobs will be new{RESET}")
        else:
            print(f"  {YELLOW}Note: Jobs might be filtered by deduplication{RESET}")
            print(f"  Last entry: {data[-1].get('title', 'N/A')} from {data[-1].get('company', 'N/A')}")

        return True
    except Exception as e:
        print(f"{RED}✗{RESET} Error reading dedup file: {e}")
        return False

def main():
    print(f"{BLUE}╔════════════════════════════════════════════════╗{RESET}")
    print(f"{BLUE}║  TechJobs360 Posting Diagnostic Script       ║{RESET}")
    print(f"{BLUE}╚════════════════════════════════════════════════╝{RESET}")

    results = {}

    # Run all tests
    results["env_vars"] = test_env_vars()
    results["wp_auth"] = test_wordpress_auth()
    results["wp_posting"] = test_wordpress_posting()
    results["job_sources"] = test_job_sources()
    results["dedup"] = check_dedup_file()

    # Summary
    print(f"\n{BLUE}=== DIAGNOSTIC SUMMARY ==={RESET}")

    all_passed = all(results.values())

    for test_name, passed in results.items():
        status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")

    if all_passed:
        print(f"\n{GREEN}✓ All tests passed!{RESET}")
        print(f"\n{YELLOW}If jobs still aren't being posted, check:{RESET}")
        print(f"  1. GitHub Actions logs for actual errors")
        print(f"  2. WordPress site might be blocking REST API requests")
        print(f"  3. Auto-rotation might be selecting a continent with no job sources")
    else:
        print(f"\n{RED}✗ Some tests failed. Fix the issues above.{RESET}")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
