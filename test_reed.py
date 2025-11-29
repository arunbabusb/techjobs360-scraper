#!/usr/bin/env python3
"""
Quick test script for Reed API integration
"""
import os
import sys

# Add parent directory to path to import from job_scraper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from job_scraper import query_reed, REED_API_KEY

def test_reed_api():
    print("=" * 60)
    print("Reed API Integration Test")
    print("=" * 60)

    # Check if API key is set
    if not REED_API_KEY:
        print("❌ ERROR: REED_API_KEY environment variable is not set!")
        print("\nTo set it, run:")
        print("  export REED_API_KEY='your-api-key-here'")
        return False

    print(f"✅ REED_API_KEY is set: {REED_API_KEY[:8]}...{REED_API_KEY[-4:]}")
    print()

    # Test 1: Query with location
    print("Test 1: Querying 'software engineer' in 'London' (limit: 5)")
    print("-" * 60)

    jobs = query_reed("software engineer", location="London", limit=5)

    if jobs:
        print(f"✅ SUCCESS: Found {len(jobs)} jobs from Reed API")
        print()
        print("Sample job:")
        print(f"  Title: {jobs[0].get('title')}")
        print(f"  Company: {jobs[0].get('company')}")
        print(f"  Location: {jobs[0].get('location')}")
        print(f"  URL: {jobs[0].get('url')}")
        print(f"  Job ID: {jobs[0].get('id')}")
    else:
        print("⚠️  WARNING: No jobs found (this could be normal if no matches)")

    print()

    # Test 2: Query with different location
    print("Test 2: Querying 'python developer' in 'Manchester' (limit: 3)")
    print("-" * 60)

    jobs2 = query_reed("python developer", location="Manchester", limit=3)

    if jobs2:
        print(f"✅ SUCCESS: Found {len(jobs2)} jobs from Reed API")
        print()
        print("Sample job:")
        print(f"  Title: {jobs2[0].get('title')}")
        print(f"  Company: {jobs2[0].get('company')}")
        print(f"  Location: {jobs2[0].get('location')}")
    else:
        print("⚠️  WARNING: No jobs found")

    print()
    print("=" * 60)
    print("Reed API test completed!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    test_reed_api()
