#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Automatic Job Scraper → WordPress (WP Job Manager)

- Auth: WordPress Application Passwords (Basic Auth over HTTPS)
- Endpoint: /wp-json/wp/v2/job-listings
- Dedup: avoid re-posting the same job (title + company)
- Optional: upload company logo and set as featured image
- Automation: run once (default) or continuous loop; use cron for scheduling

Docs referenced:
- WP Job Manager REST root for job listings: /wp-json/wp/v2/job-listings
  https://wpjobmanager.com/document/advanced-usage/wp-job-manager-rest-api/         (meta fields via REST)  [CITE]
- WordPress Application Passwords (core auth for REST)
  https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/ [CITE]
- WordPress REST "Posts" (payload fields, status, featured_media, meta)
  https://developer.wordpress.org/rest-api/reference/posts/                          [CITE]
"""

import os
import sys
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter, Retry

# ----------------------------
# Configuration (set as ENV)
# ----------------------------
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://techjobs360.com")  # your site base
WP_USER = os.getenv("WP_USER", "")                                 # WP username
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")                 # Application password
WP_POST_TYPE = os.getenv("WP_POST_TYPE", "job-listings")           # WPJM CPT rest base
RUN_ONCE = os.getenv("RUN_ONCE", "true").lower() == "true"         # run a single pass

# Optional: media upload toggle
UPLOAD_LOGO = os.getenv("UPLOAD_LOGO", "true").lower() == "true"

# Sources toggles (keep your existing ones or use these)
ENABLE_ADZUNA = os.getenv("ENABLE_ADZUNA", "true").lower() == "true"
ENABLE_JSEARCH = os.getenv("ENABLE_JSEARCH", "true").lower() == "true"

# Existing env for JSearch key (you already have it in your logs)
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "")

# Countries (keep same as your logs)
COUNTRIES = os.getenv("COUNTRIES", "in,us,fr,gb,de").split(",")

# ----------------------------
# Logging
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("job_scraper")

# ----------------------------
# HTTP client with retries
# ----------------------------
def new_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=4, backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

# ----------------------------
# WordPress REST client
# ----------------------------
class WordPressClient:
    def __init__(self, base_url: str, user: str, app_password: str, post_type: str):
        self.base_url = base_url.rstrip("/")
        self.api = f"{self.base_url}/wp-json/wp/v2"
        self.endpoint = f"{self.api}/{post_type}"
        self.user = user
        self.app_password = app_password
        self.s = new_session()
        self.s.auth = (self.user, self.app_password)
        self.headers_json = {"Content-Type": "application/json"}

    def test_auth(self) -> bool:
        """
        Confirm Application Password auth works by checking API root.
        """
        try:
            r = self.s.get(self.api, timeout=20)
            if r.status_code == 200:
                log.info("WordPress REST reachable ✅")
                return True
            elif r.status_code == 401:
                log.error("401 Unauthorized from WP REST. Check username + application password, and HTTPS.")
                return False
            else:
                log.error(f"WP REST unexpected status {r.status_code}: {r.text[:300]}")
                return False
        except Exception as e:
            log.exception(f"Error reaching WP REST: {e}")
            return False

    def search_existing(self, title: str, company: Optional[str]) -> Optional[Dict]:
        """
        Avoid duplicates: look up an existing listing by title + company
        using the standard REST 'search' on the job-listings endpoint. [Posts API supports `search`]
        """
        try:
            # Combine title and company to improve search relevance
            q = title if not company else f"{title} {company}"
            params = {"search": q, "per_page": 5, "status": "publish"}  # WP supports 'search' on CPT. [CITE]
            r = self.s.get(self.endpoint, params=params, timeout=25)
            if r.status_code == 200:
                for item in r.json():
                    it_title = (item.get("title", {}) or {}).get("rendered", "")
                    if company:
                        # Look for company in meta if returned; WPJM exposes fields via meta on job-listings REST. [CITE]
                        meta = item.get("meta", {}) or {}
                        comp = meta.get("_company_name") or meta.get("company_name")
                        if it_title.strip().lower() == title.strip().lower() and comp and company.lower() in str(comp).lower():
                            return item
                    else:
                        if it_title.strip().lower() == title.strip().lower():
                            return item
                return None
            else:
                log.warning(f"Search failed ({r.status_code}): {r.text[:300]}")
                return None
        except Exception as e:
            log.exception(f"search_existing error: {e}")
            return None

    def upload_logo_from_url(self, logo_url: str) -> Optional[int]:
        """
        Download logo and upload to `/wp/v2/media`, returning media ID.
        """
        if not logo_url:
            return None
        try:
            # fetch binary
            r_img = self.s.get(logo_url, timeout=30)
            if r_img.status_code != 200 or not r_img.content:
                log.warning(f"Logo download failed: {logo_url} ({r_img.status_code})")
                return None

            filename = logo_url.split("?")[0].split("/")[-1] or f"logo-{int(time.time())}.png"
            media_endpoint = f"{self.api}/media"
            headers = {
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": r_img.headers.get("Content-Type", "image/png"),
            }
            r_up = self.s.post(media_endpoint, headers=headers, data=r_img.content, timeout=40)
            if r_up.status_code in (201, 200):
                media_id = r_up.json().get("id")
                log.info(f"Uploaded logo → media_id={media_id}")
                return media_id
            else:
                log.warning(f"Media upload failed ({r_up.status_code}): {r_up.text[:300]}")
                return None
        except Exception as e:
            log.exception(f"upload_logo_from_url error: {e}")
            return None

    def post_job(self, job: Dict) -> Optional[Dict]:
        """
        Create a job listing. Minimal fields are title, content, status.
        WP Job Manager exposes job fields via 'meta' on /job-listings. [CITE]
        """
        payload = {
            "title": job.get("title") or "Untitled Job",
            "content": job.get("description") or "",
            "status": "publish",  # you can switch to 'draft' if needed
            "meta": {
                # WPJM default meta keys (underscore when stored as postmeta). [CITE]
                "_company_name": job.get("company"),
                "_job_location": job.get("location"),
                "_application": job.get("apply_url"),
                "_job_salary": job.get("salary"),
            }
        }

        # Deadline: send ISO8601 and also in meta for themes/addons that use it
        deadline_iso = job.get("deadline_iso")
        if deadline_iso:
            payload["meta"]["_job_deadline"] = deadline_iso

        # Try to upload logo and set featured_media
        if UPLOAD_LOGO and job.get("logo_url"):
            media_id = self.upload_logo_from_url(job["logo_url"])
            if media_id:
                payload["featured_media"] = media_id

        try:
            r = self.s.post(self.endpoint, headers=self.headers_json, data=json.dumps(payload), timeout=45)
            if r.status_code == 201:
                created = r.json()
                log.info(f"Posted: {created.get('id')} | {created.get('link')}")
                return created
            elif r.status_code == 401:
                log.error(
                    "401 Unauthorized from WordPress. "
                    "Fix by using WP Application Passwords with HTTPS and correct username. "
                    "See docs."
                )
                return None
            else:
                log.error(f"Error posting to WordPress: {r.status_code} {r.text[:500]}")
                return None
        except Exception as e:
            log.exception(f"post_job error: {e}")
            return None

# ----------------------------
# Job sources (simplified)
# (Plug in your existing fetch code here. Keep the same return shape.)
# ----------------------------
def fetch_jobs_from_adzuna(country_code: str) -> List[Dict]:
    """
    Your existing Adzuna fetch code likely works. Return list[dict] like below.
    We keep a simple placeholder shape; plug in real fields from your current implementation.
    """
    # TODO: Replace with your existing Adzuna integration.
    # Below is just a stub to demonstrate structure.
    return []

def fetch_jobs_from_jsearch() -> List[Dict]:
    """
    Your existing JSearch fetch code likely works. Return list[dict] like below.
    """
    # TODO: Replace with your actual JSearch integration using JSEARCH_API_KEY.
    return []

# ----------------------------
# Helper: normalize job dicts
# ----------------------------
def normalize_job(raw: Dict) -> Dict:
    """
    Ensure consistent keys expected by poster.
    Required keys: title, description, company, location, apply_url
    Optional: salary, deadline_iso, logo_url
    """
    # Adjust the mapping according to your raw payloads
    return {
        "title": raw.get("title") or raw.get("job_title"),
        "description": raw.get("description") or raw.get("job_description") or "",
        "company": raw.get("company") or raw.get("company_name"),
        "location": raw.get("location") or raw.get("job_location"),
        "apply_url": raw.get("apply_url") or raw.get("url") or raw.get("application_url"),
        "salary": raw.get("salary"),
        "deadline_iso": raw.get("deadline_iso"),  # ISO8601 string e.g., "2025-10-20T00:00:00"
        "logo_url": raw.get("logo_url"),
        "source": raw.get("source"),
        "external_id": raw.get("id") or raw.get("external_id"),
    }

# ----------------------------
# Main runner
# ----------------------------
def run_once():
    log.info("Starting job scraper...")

    # 1) Prepare WP client and test auth
    wp = WordPressClient(base_url=WP_BASE_URL, user=WP_USER, app_password=WP_APP_PASSWORD, post_type=WP_POST_TYPE)
    if not wp.test_auth():
        # Block further processing if auth fails
        log.error("Stopping due to WordPress auth failure.")
        return

    # 2) Fetch jobs
    all_jobs: List[Dict] = []

    log.info(f"Fetching jobs from countries: {', '.join(COUNTRIES)}")

    if ENABLE_ADZUNA:
        for cc in COUNTRIES:
            log.info(f"Fetching jobs from Adzuna for country: {cc}")
            adz_jobs = fetch_jobs_from_adzuna(cc)
            log.info(f"Fetched {len(adz_jobs)} jobs from Adzuna ({cc})")
            all_jobs.extend([normalize_job(j) for j in adz_jobs])

    if ENABLE_JSEARCH:
        log.info("Fetching jobs from JSearch...")
        js_jobs = fetch_jobs_from_jsearch()
        log.info(f"Fetched {len(js_jobs)} jobs from JSearch")
        all_jobs.extend([normalize_job(j) for j in js_jobs])

    # 3) Post to WordPress after dedup
    posted_count = 0
    for job in all_jobs:
        if not job.get("title") or not job.get("apply_url"):
            # skip incomplete
            continue

        existing = wp.search_existing(title=job["title"], company=job.get("company"))
        if existing:
            log.info(f"Skip duplicate: {job['title']} @ {job.get('company')} (existing id {existing.get('id')})")
            continue

        created = wp.post_job(job)
        if created:
            posted_count += 1
        # small pause to be kind to WP/host
        time.sleep(1.2)

    log.info(f"Done. Posted {posted_count} new jobs.")

def run_forever(interval_minutes: int = 60):
    """
    Continuous loop (if you prefer not to use cron).
    """
    while True:
        run_once()
        log.info(f"Sleeping for {interval_minutes} minutes...")
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    if RUN_ONCE:
        run_once()
    else:
        run_forever(interval_minutes=int(os.getenv("LOOP_INTERVAL_MIN", "60")))
