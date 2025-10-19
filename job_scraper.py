#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechJobs360 Job Scraper -> WordPress (WP Job Manager)
----------------------------------------------------
- Auth: WordPress Application Passwords (Basic Auth)
- Fetcher: JSearch (RapidAPI)
- Posting: /wp-json/wp/v2/job-listings (WP Job Manager CPT)
- Dedup: persistent file posted_jobs.json
- Automation: run once or in a loop

USAGE:
  1) Set environment variables (recommended):
     - WP_BASE_URL, WP_USER, WP_APP_PASSWORD
     - JSEARCH_API_KEY, JSEARCH_HOST (default jsearch.p.rapidapi.com)
     - JSEARCH_QUERY (e.g., "software engineer in india")
     - JSEARCH_COUNTRY (e.g., "in")
     - LOOP_INTERVAL_SEC (optional)
  2) Run once:
       python3 job_scraper.py
     Run forever:
       python3 job_scraper.py --loop

NOTE:
  - Do NOT hardcode passwords or API keys in source. Use env vars.
  - If your site uses a different CPT route (e.g., job_listing), the code
    will auto-fallback after detecting a 404 on job-listings.
"""
import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
import argparse
import requests
from requests.adapters import HTTPAdapter, Retry
from requests.auth import HTTPBasicAuth

# -----------------
# CONFIG (env-first)
# -----------------
WP_BASE_URL = os.getenv("WP_BASE_URL", "https://techjobs360.com").rstrip('/')
WP_USER = os.getenv("WP_USER", "")
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")

# JSearch (RapidAPI)
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "").strip()
JSEARCH_HOST = os.getenv("JSEARCH_HOST", "jsearch.p.rapidapi.com").strip()
JSEARCH_QUERY = os.getenv("JSEARCH_QUERY", "software engineer").strip()
JSEARCH_COUNTRY = os.getenv("JSEARCH_COUNTRY", "in").strip()
JSEARCH_NUM_PAGES = int(os.getenv("JSEARCH_NUM_PAGES", "2"))
JSEARCH_DATE_POSTED = os.getenv("JSEARCH_DATE_POSTED", "week")  # all|today|3days|week|month

# Loop interval (seconds)
LOOP_INTERVAL_SEC = int(os.getenv("LOOP_INTERVAL_SEC", "1800"))

# Dedup store file
DEDUP_FILE = os.getenv("DEDUP_FILE", "posted_jobs.json")

# -----------------
# REST endpoints
# -----------------
WP_API_ROOT = f"{WP_BASE_URL}/wp-json/wp/v2"
# Prefer WP Job Manager route "job-listings" per official docs; will fallback to "job_listing" if 404
WP_JOB_ROUTE_PRIMARY = "job-listings"
WP_JOB_ROUTE_FALLBACK = "job_listing"

# -----------------
# Logging
# -----------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("job_scraper")

# -----------------
# HTTP session
# -----------------

def new_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

S = new_session()

# -----------------
# Helpers: dedup persistence
# -----------------

def load_dedup() -> Dict[str, Dict]:
    try:
        if os.path.exists(DEDUP_FILE):
            with open(DEDUP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_dedup(store: Dict[str, Dict]) -> None:
    try:
        with open(DEDUP_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log.warning(f"Could not write dedup file: {e}")

# -----------------
# Auth sanity (prevents 401 surprises)
# -----------------

def verify_wp_auth() -> bool:
    if not WP_USER or not WP_APP_PASSWORD:
        log.error("Missing WP_USER or WP_APP_PASSWORD environment variables.")
        return False
    try:
        r = S.get(f"{WP_API_ROOT}/users/me", auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD), timeout=20)
        if r.status_code == 200:
            j = r.json()
            log.info(f"Authenticated as: {j.get('name')} (id={j.get('id')})")
            return True
        else:
            log.error(
                f"Auth failed for WP user '{WP_USER}'. Status={r.status_code} Body={r.text[:200]} "
                "Ensure Application Password is valid and user has permissions."
            )
            return False
    except Exception as e:
        log.error(f"Auth check error: {e}")
        return False

# -----------------
# Determine working CPT route (job-listings vs job_listing)
# -----------------

def resolve_job_endpoint() -> str:
    primary = f"{WP_API_ROOT}/{WP_JOB_ROUTE_PRIMARY}"
    fallback = f"{WP_API_ROOT}/{WP_JOB_ROUTE_FALLBACK}"
    try:
        r = S.options(primary, timeout=15)  # OPTIONS provides schema if route exists
        if r.status_code < 400:
            return primary
    except Exception:
        pass
    try:
        r2 = S.options(fallback, timeout=15)
        if r2.status_code < 400:
            log.warning("Primary route '/job-listings' not found; using '/job_listing' fallback.")
            return fallback
    except Exception:
        pass
    # Default to primary even if OPTIONS blocked; POST will tell us
    return primary

WP_JOB_ENDPOINT = resolve_job_endpoint()
WP_MEDIA_ENDPOINT = f"{WP_API_ROOT}/media"

# -----------------
# Normalization: map feed job -> common dict
# -----------------

def normalize_job(raw: Dict) -> Dict:
    title = raw.get("job_title") or raw.get("title")
    description = raw.get("job_description") or raw.get("description") or ""
    company = (
        raw.get("employer_name")
        or raw.get("company")
        or (raw.get("company", {}) or {}).get("display_name")
    )
    location = (
        raw.get("job_city")
        or raw.get("job_country")
        or (raw.get("location") or {}).get("display_name")
        or raw.get("location")
    )
    apply_url = raw.get("job_apply_link") or raw.get("redirect_url") or raw.get("url")
    # Compose salary string if possible
    sal_min = raw.get("job_min_salary") or raw.get("salary_min")
    sal_max = raw.get("job_max_salary") or raw.get("salary_max")
    sal_cur = raw.get("job_salary_currency") or raw.get("salary_currency")
    salary = None
    if sal_min or sal_max:
        if sal_min and sal_max:
            salary = f"{sal_min}-{sal_max} {sal_cur or ''}".strip()
        else:
            salary = f"{sal_min or sal_max} {sal_cur or ''}".strip()
    logo = raw.get("employer_logo") or raw.get("logo_url")
    deadline = raw.get("job_offer_expiration_datetime_utc") or raw.get("deadline_iso")
    return {
        "title": title,
        "description": description,
        "company": company,
        "location": location,
        "apply_url": apply_url,
        "salary": salary,
        "logo_url": logo,
        "deadline_iso": deadline,
        "source": raw.get("source") or raw.get("job_publisher"),
        "external_id": raw.get("id") or raw.get("job_id"),
    }

# -----------------
# Dedupe via REST & local memory
# -----------------

def wp_search_existing(title: str, company: Optional[str]) -> Optional[Dict]:
    try:
        params = {"search": f"{title} {company or ''}".strip(), "per_page": 5}
        r = S.get(WP_JOB_ENDPOINT, params=params, timeout=25)
        if r.status_code != 200:
            return None
        for item in r.json():
            it_title = (item.get("title", {}) or {}).get("rendered", "")
            if it_title.strip().lower() == (title or "").strip().lower():
                return item
        return None
    except Exception:
        return None

# -----------------
# Optional: upload logo and attach as featured image
# -----------------

def wp_upload_logo(logo_url: str) -> Optional[int]:
    if not logo_url:
        return None
    try:
        r_img = S.get(logo_url, timeout=30)
        if r_img.status_code != 200 or not r_img.content:
            return None
        filename = (logo_url.split("?")[0].split("/")[-1] or f"logo-{int(time.time())}.png").replace('"', "")
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": r_img.headers.get("Content-Type", "image/png"),
        }
        r_up = S.post(
            WP_MEDIA_ENDPOINT,
            headers=headers,
            data=r_img.content,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            timeout=40,
        )
        if r_up.status_code in (200, 201):
            return r_up.json().get("id")
        return None
    except Exception:
        return None

# -----------------
# Post one job to WPJM (2-phase: create, then meta update)
# -----------------

def wp_post_job(job: Dict) -> Optional[Dict]:
    # Phase 1: create the post minimally
    payload = {
        "title": job.get("title") or "Untitled Job",
        "content": job.get("description") or "",
        "status": "publish",
    }
    # Try to add featured media if available
    if job.get("logo_url"):
        media_id = wp_upload_logo(job["logo_url"])
        if media_id:
            payload["featured_media"] = media_id
    r = S.post(
        WP_JOB_ENDPOINT,
        auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
        headers={"Content-Type": "application/json"},
        data=json.dumps(payload),
        timeout=45,
    )
    if r.status_code == 404:
        # Fallback route attempt
        alt = f"{WP_API_ROOT}/{WP_JOB_ROUTE_FALLBACK}"
        log.warning("POST 404 on primary route; retrying on fallback route...")
        rr = S.post(
            alt,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=45,
        )
        if rr.status_code in (200, 201):
            created = rr.json()
            # Switch global endpoint to fallback for subsequent calls
            global WP_JOB_ENDPOINT
            WP_JOB_ENDPOINT = alt
            return _update_job_meta(created, job)
        else:
            log.error(f"Error posting to WordPress (fallback): {rr.status_code} - {rr.text[:400]}")
            return None
    elif r.status_code in (200, 201):
        created = r.json()
        return _update_job_meta(created, job)
    else:
        log.error(f"Error posting to WordPress: {r.status_code} - {r.text[:400]}")
        return None

def _update_job_meta(created: Dict, job: Dict) -> Optional[Dict]:
    post_id = created.get("id")
    if not post_id:
        return created
    # Phase 2: attempt to set WP Job Manager meta
    meta_payload = {
        "meta": {
            "_company_name": job.get("company"),
            "_job_location": job.get("location"),
            "_application": job.get("apply_url"),
            "_job_salary": job.get("salary"),
        }
    }
    if job.get("deadline_iso"):
        meta_payload["meta"]["_job_deadline"] = job.get("deadline_iso")
    rm = S.post(
        f"{WP_JOB_ENDPOINT}/{post_id}",
        auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
        headers={"Content-Type": "application/json"},
        data=json.dumps(meta_payload),
        timeout=40,
    )
    if rm.status_code in (200, 201):
        out = rm.json()
        log.info(f"Posted: {out.get('id')} {out.get('link')}")
        return out
    else:
        # If meta update fails, keep the post and warn
        log.warning(
            f"Created job (id={post_id}) but meta update failed: {rm.status_code} - {rm.text[:300]}"
        )
        return created

# -----------------
# Fetcher: JSearch (RapidAPI)
# -----------------

def fetch_from_jsearch() -> List[Dict]:
    if not JSEARCH_API_KEY:
        log.error("JSearch API key missing. Set JSEARCH_API_KEY env var.")
        return []
    url = f"https://{JSEARCH_HOST}/search"
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": JSEARCH_HOST,
    }
    params = {
        "query": JSEARCH_QUERY,
        "num_pages": JSEARCH_NUM_PAGES,
        "date_posted": JSEARCH_DATE_POSTED,
        "country": JSEARCH_COUNTRY,
        # You may also specify language, employment_types, etc.
    }
    r = S.get(url, headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        log.warning(f"JSearch error {r.status_code}: {r.text[:200]}")
        return []
    data = r.json()
    jobs = data.get("data") or data.get("results") or []
    for j in jobs:
        j["source"] = j.get("job_publisher") or "JSearch"
    return jobs

# -----------------
# Verify recent WP items (for confidence)
# -----------------

def print_recent_wp_listings(n: int = 5):
    try:
        r = S.get(f"{WP_JOB_ENDPOINT}?per_page={n}", timeout=20)
        if r.status_code != 200:
            log.info(f"Recent listings check failed: {r.status_code}")
            return
        items = r.json()
        if not items:
            log.info("No job listings returned ([])")
            return
        log.info("Latest job listings:")
        for j in items:
            title = (j.get("title", {}) or {}).get("rendered")
            link = j.get("link")
            log.info(f"- {j.get('id')} | {title} | {link}")
    except Exception as e:
        log.info(f"Recent listings check error: {e}")

# -----------------
# One run
# -----------------

def run_once():
    log.info("Starting job scraper...")
    # WP REST reachability
    try:
        root = S.get(WP_API_ROOT, timeout=20)
        if root.status_code != 200:
            log.error(f"WordPress REST unreachable: {root.status_code}")
            return
        log.info("WordPress REST reachable ✅")
    except Exception as e:
        log.error(f"WordPress REST error: {e}")
        return

    # Auth check prevents 401 later
    if not verify_wp_auth():
        return

    # Load dedup store
    dedup_store = load_dedup()

    all_jobs: List[Dict] = []
    skipped_missing = 0
    skipped_duplicates = 0
    posted_count = 0

    # JSearch fetch
    log.info("Fetching jobs from JSearch...")
    js_jobs = fetch_from_jsearch()
    log.info(f"Fetched {len(js_jobs)} jobs from JSearch")
    for raw in js_jobs:
        all_jobs.append(normalize_job(raw))

    if not all_jobs:
        log.warning("No jobs fetched. Check API keys, query, or country filters.")

    # Post with dedup
    for job in all_jobs:
        # require essential fields
        if not (job.get("title") and job.get("apply_url")):
            skipped_missing += 1
            continue
        # local key: prefer external_id; else title+company
        dedup_key = job.get("external_id") or f"{(job.get('title','') or '').strip()}|{(job.get('company','') or '').strip()}"
        # skip if in our local store
        if dedup_key and dedup_key in dedup_store:
            skipped_duplicates += 1
            continue
        # skip if found via REST search
        if wp_search_existing(job["title"], job.get("company")):
            skipped_duplicates += 1
            dedup_store[dedup_key] = {"seen": True}
            continue
        # post
        created = wp_post_job(job)
        if created:
            posted_count += 1
            dedup_store[dedup_key] = {"posted_id": created.get("id")}
            time.sleep(1.0)

    # Save dedup
    save_dedup(dedup_store)

    # Summary & recent items
    log.info(
        f"Summary → fetched_total={len(all_jobs)} | "
        f"skipped_missing={skipped_missing} | "
        f"skipped_duplicates={skipped_duplicates} | "
        f"posted={posted_count}"
    )
    print_recent_wp_listings(n=5)

# -----------------
# Continuous loop (every X minutes)
# -----------------

def run_forever(interval_sec: int = LOOP_INTERVAL_SEC):
    while True:
        run_once()
        log.info(f"Sleeping for {max(1, interval_sec//60)} minutes...")
        time.sleep(interval_sec)

# -----------------
# Entry point
# -----------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Scraper -> WP Job Manager")
    parser.add_argument("--loop", action="store_true", help="Run continuously at intervals")
    args = parser.parse_args()
    if args.loop:
        run_forever()
    else:
        run_once()
