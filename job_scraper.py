#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Job Scraper → WordPress (WP Job Manager)
- Fetch jobs from Adzuna & JSearch
- Post them automatically to WordPress using Application Passwords
"""

import os
import json
import time
import requests
from requests.auth import HTTPBasicAuth

# ----------------------------
# CONFIGURATION
# ----------------------------
WP_BASE_URL = "https://techjobs360.com"  # Your site URL
WP_USER = "job post"             # Replace with your WP username
WP_APP_PASSWORD = "ao1d zIbv RAGA jPfk gBAs rN2q"  # Replace with WP Application Password
WP_API_URL = f"{WP_BASE_URL}/wp-json/wp/v2/job-listings"

# ----------------------------
# SAMPLE JOB SOURCES (Replace with real fetch later)
# ----------------------------
def fetch_jobs():
    # For now, just sample jobs. Replace with Adzuna/JSearch later.
    return [
        {
            "title": "Python Developer",
            "description": "We are looking for a Python Developer to join our team.",
            "company": "TechJobs360",
            "location": "Remote",
            "apply_url": "https://example.com/apply",
            "salary": "₹10,00,000",
            "logo_url": None
        },
        {
            "title": "Frontend Engineer",
            "description": "React.js expert needed for exciting projects.",
            "company": "TechJobs360",
            "location": "Bangalore",
            "apply_url": "https://example.com/apply",
            "salary": "₹8,00,000",
            "logo_url": None
        }
    ]

# ----------------------------
# POST JOB TO WORDPRESS
# ----------------------------
def post_job(job):
    payload = {
        "title": job["title"],
        "content": job["description"],
        "status": "publish",
        "meta": {
            "_company_name": job["company"],
            "_job_location": job["location"],
            "_application": job["apply_url"],
            "_job_salary": job["salary"]
        }
    }

    response = requests.post(
        WP_API_URL,
        auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload)
    )

    if response.status_code == 201:
        print(f"✅ Posted: {job['title']}")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    print("Starting job scraper...")
    jobs = fetch_jobs()
    for job in jobs:
        post_job(job)
        time.sleep(1)
    print("Done!")
