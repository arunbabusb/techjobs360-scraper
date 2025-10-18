#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
One-file Job Scraper → WordPress (WP Job Manager)
-------------------------------------------------
- Auth: WordPress Application Passwords (admintech)
- Fetchers: JSearch (RapidAPI) + Adzuna (optional)
- Posting: /wp-json/wp/v2/job-listings (WP Job Manager CPT)
- Dedup: persistent file posted_jobs.json
- Automation: run continuously every 30 minutes or once

HOW TO USE (ELI5):
1) Put this file as job_scraper.py
2) Edit the CONFIG below (set your keys)
3) Run once:      python3 job_scraper.py
   Run forever:   python3 job_scraper.py --loop
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional
import argparse

import requests
from requests.adapters import HTTPAdapter, Retry
from requests.auth import HTTPBasicAuth

# ------------------------------------------------------------
# CONFIG (edit these)
# ------------------------------------------------------------

# Your site + WordPress credentials (as you provided)
WP_BASE_URL     = "https://techjobs360.com"
WP_USER         = "admintech"                                 # Admin username
WP_APP_PASSWORD = "ANzY y4CQ MqjP wgXm 7GLo PUzF"             # Application Password (with spaces)

# JSearch (RapidAPI) — REQUIRED for fetching from JSearch
# Put your key here or set an env var JSEARCH_API_KEY
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "").strip()
JSEARCH_HOST    = os.getenv("JSEARCH_HOST", "jsearch.p.rapidapi.com")
JSEARCH_QUERY   = os.getenv("JSEARCH_QUERY", "software developer OR data engineer")
JSEARCH_NUM_PAGES = int(os.getenv("JSEARCH_NUM_PAGES", "2"))  # increase to 3 for more results

# Adzuna — OPTIONAL (set keys if you want Adzuna feed too)
ADZUNA_APP_ID   = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY  = os.getenv("ADZUNA_APP_KEY", "").strip()
COUNTRIES       = os.getenv("COUNTRIES", "in,us,fr,gb,de").split(",")
ADZUNA_WHAT     = os.getenv("ADZUNA_WHAT", "software OR developer OR engineer")
ADZUNA_RESULTS_PER_PAGE = int(os.getenv("ADZUNA_RESULTS_PER_PAGE", "20"))
ADZUNA_MAX_DAYS_OLD     = int(os.getenv("ADZUNA_MAX_DAYS_OLD", "3"))  # widen to 7 if needed

# Automation interval (seconds) — 30 minutes by default
LOOP_INTERVAL_SEC = int(os.getenv("LOOP_INTERVAL_SEC", "1800"))

# Persistence file for dedup across runs
DEDUP_FILE = os.getenv("DEDUP_FILE", "posted_jobs.json")

# ------------------------------------------------------------
# REST endpoints (WP Job Manager CPT)
# ------------------------------------------------------------
WP_API_ROOT       = f"{WP_BASE_URL}/wp-json/wp/v2"
WP_JOB_ENDPOINT   = f"{WP_API_ROOT}/job-listings"
WP_MEDIA_ENDPOINT = f"{WP_API_ROOT}/media"

# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("job_scraper")

# ------------------------------------------------------------
# HTTP session with retries
# ------------------------------------------------------------
def new_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=4, backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

S = new_session()

# ------------------------------------------------------------
# Helpers: dedup persistence
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Auth sanity (prevents 401 surprises)
# ------------------------------------------------------------
def verify_wp_auth() -> bool:
    """
    Verify credentials using /users/me (requires valid Application Password).
    """
    r = S.get(f"{WP_API_ROOT}/users/me",
              auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD), timeout=20)
    if r.status_code == 200:
        j = r.json()
        log.info(f"Authenticated as: {j.get('name')} (id={j.get('id')})")
        return True
    else:
        log.error(
            f"Auth failed for WP user '{WP_USER}'. "
            f"Status={r.status_code} Body={r.text[:200]} "
            "Use an Administrator with a valid Application Password."
        )
        return False

# ------------------------------------------------------------
# Normalization: map different feeds to a common job dict
# ------------------------------------------------------------
def normalize_job(raw: Dict) -> Dict:
    title = raw.get("job_title") or raw.get("title")
    description = raw.get("job_description") or raw.get("description") or ""
    company = (raw.get("employer_name")
               or raw.get("company")
               or (raw.get("company", {}) or {}).get("display_name"))
    location = (raw.get("job_city")
                or raw.get("job_country")
                or (raw.get("location") or {}).get("display_name")
                or raw.get("location"))
    apply_url = raw.get("job_apply_link") or raw.get("redirect_url") or raw.get("url")
    salary = raw.get("job_min_salary") or raw.get("salary_min") or raw.get("salary")
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

# ------------------------------------------------------------
# Dedupe via WP REST search (title + company) & local memory
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Optional: upload logo and attach as featured image
# ------------------------------------------------------------
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
        r_up = S.post(WP_MEDIA_ENDPOINT, headers=headers, data=r_img.content,
                      auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD), timeout=40)
        if r_up.status_code in (200, 201):
            return r_up.json().get("id")
        return None
    except Exception:
        return None

# ------------------------------------------------------------
# Post one job to WPJM
# ------------------------------------------------------------
def wp_post_job(job: Dict) -> Optional[Dict]:
    payload = {
        "title": job["title"] or "Untitled Job",
        "content": job["description"] or "",
        "status": "publish",
        "meta": {
            "_company_name": job.get("company"),
            "_job_location": job.get("location"),
            "_application": job.get("apply_url"),
            "_job_salary": job.get("salary"),
        }
    }
    if job.get("deadline_iso"):
        payload["meta"]["_job_deadline"] = job["deadline_iso"]

    # Try logo
    if job.get("logo_url"):
        media_id = wp_upload_logo(job["logo_url"])
        if media_id:
            payload["featured_media"] = media_id

    r = S.post(WP_JOB_ENDPOINT,
               auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
               headers={"Content-Type": "application/json"},
               data=json.dumps(payload), timeout=45)
    if r.status_code == 201:
        created = r.json()
        log.info(f"Posted: {created.get('id')} | {created.get('link')}")
        return created
    else:
        log.error(f"Error posting to WordPress: {r.status_code} - {r.text[:400]}")
        return None

# ------------------------------------------------------------
# Fetchers: JSearch (RapidAPI) and Adzuna
# ------------------------------------------------------------
def fetch_from_jsearch() -> List[Dict]:
    if not JSEARCH_API_KEY:
        log.warning("JSearch API key missing; skipping JSearch fetch.")
        return []
    url = f"https://{JSEARCH_HOST}/search"
    headers = {"X-RapidAPI-Key": JSEARCH_API_KEY, "X-RapidAPI-Host": JSEARCH_HOST}
    params = {"query": JSEARCH_QUERY, "num_pages": JSEARCH_NUM_PAGES, "date_posted": "week"}
    r = S.get(url, headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        log.warning(f"JSearch error {r.status_code}: {r.text[:200]}")
        return []
    data = r.json()
    jobs = data.get("data") or data.get("results") or []
    for j in jobs:
        j["source"] = j.get("job_publisher") or "JSearch"
    return jobs

def fetch_from_adzuna(country: str) -> List[Dict]:
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        log.warning("Adzuna credentials missing; skipping Adzuna fetch.")
        return []
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": ADZUNA_RESULTS_PER_PAGE,
        "what": ADZUNA_WHAT,
        "max_days_old": ADZUNA_MAX_DAYS_OLD,
        "content-type": "application/json",
        "sort_by": "date",
        "salary_include_unknown": 1
    }
    r = S.get(url, params=params, timeout=30)
    if r.status_code != 200:
        log.warning(f"Adzuna {country} error {r.status_code}: {r.text[:200]}")
        return []
    results = r.json().get("results") or []
    for j in results:
        j["source"] = "Adzuna"
    return results

# ------------------------------------------------------------
# Verify recent WP items (for your confidence)
# ------------------------------------------------------------
def print_recent_wp_listings(n: int = 5):
    r = S.get(f"{WP_JOB_ENDPOINT}?per_page={n}", timeout=20)
    if r.status_code != 200:
        log.info(f"Recent listings check failed: {r.status_code}")
        return
    items = r.json()
    if not items:
        log.info("No job_listings returned ([])")
        return
    log.info("Latest job_listings:")
    for j in items:
        title = (j.get("title", {}) or {}).get("rendered")
        link = j.get("link")
        log.info(f"- {j.get('id')} | {title} | {link}")

# ------------------------------------------------------------
# One run
# ------------------------------------------------------------
def run_once():
    log.info("Starting job scraper...")

    # WP REST reachability
    root = S.get(WP_API_ROOT, timeout=20)
    if root.status_code != 200:
        log.error(f"WordPress REST unreachable: {root.status_code}")
        return
    log.info("WordPress REST reachable ✅")

    # Auth check prevents 401 later
    if not verify_wp_auth():
        return
    # Load dedup store
    dedup_store = load_dedup()  # dict keyed by external_id or title|company

    all_jobs: List[Dict] = []
    skipped_missing = 0
    skipped_duplicates = 0
    posted_count = 0

    # Adzuna loop
    log.info(f"Fetching jobs from countries: {', '.join(COUNTRIES)}")
    for cc in COUNTRIES:
        cc = cc.strip()
        log.info(f"Fetching jobs from Adzuna for country: {cc}")
        adz_jobs = fetch_from_adzuna(cc)
        log.info(f"Fetched {len(adz_jobs)} jobs from Adzuna ({cc})")
        for raw in adz_jobs:
            all_jobs.append(normalize_job(raw))

    # JSearch
    log.info("Fetching jobs from JSearch...")
    js_jobs = fetch_from_jsearch()
    log.info(f"Fetched {len(js_jobs)} jobs from JSearch")
    for raw in js_jobs:
        all_jobs.append(normalize_job(raw))

    # Post with dedup
    for job in all_jobs:
        # require essential fields
        if not (job.get("title") and job.get("apply_url")):
            skipped_missing += 1
            continue
        # local key: prefer external_id; else title|company
        dedup_key = job.get("external_id") or f"{job.get('title','').strip()}|{job.get('company','').strip()}"

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

# ------------------------------------------------------------
# Continuous loop (every 30 minutes)
# ------------------------------------------------------------
def run_forever(interval_sec: int = LOOP_INTERVAL_SEC):
    while True:
        run_once()
        log.info(f"Sleeping for {interval_sec//60} minutes...")
        time.sleep(interval_sec)

# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Job Scraper -> WP Job Manager")
    parser.add_argument("--loop", action="store_true", help="Run continuously every 30 minutes")
    args = parser.parse_args()

    if args.loop:
        run_forever()
    else:
        run_once()
``
