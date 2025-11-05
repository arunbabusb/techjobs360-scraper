#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechJobs360 Job Scraper -> WordPress (WP Job Manager)
Enhanced Version with Better Error Logging & Batch Posting
"""
import os
import sys
import json
import time
import logging
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter, Retry
from requests.auth import HTTPBasicAuth
# CONFIG
WP_BASE_URL = "https://techjobs360.com"
WP_USER = "admintech"
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
# JSearch (RapidAPI)
JSEARCH_API_KEY = "90644e44cbmsh58171cfd7ff5cb0p17d1d9jsn0572d579be41"
JSEARCH_HOST = "jsearch.p.rapidapi.com"
JSEARCH_QUERY = "software engineer"
JSEARCH_COUNTRY = "in"
JSEARCH_NUM_PAGES = 5
JSEARCH_DATE_POSTED = "week"
LOOP_INTERVAL_SEC = int(os.getenv("LOOP_INTERVAL_SEC", "1800"))
DEDUP_FILE = os.getenv("DEDUP_FILE", "posted_jobs.json")
# REST endpoints
WP_API_ROOT = f"{WP_BASE_URL}/wp-json/wp/v2"
WP_JOB_ROUTE_PRIMARY = "job-listings"
WP_JOB_ROUTE_FALLBACK = "job_listing"
# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("job_scraper")
# HTTP session
def new_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(
        total=4,
        backoff_factor=0.6,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST", "PUT"]
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s
S = new_session()
# Dedup persistence
def load_dedup() -> Dict[str, Dict]:
    try:
        if os.path.exists(DEDUP_FILE):
            with open(DEDUP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # --- START OF FIX ---
                # Check if the loaded data is a dictionary.
                # If it's a list (from an old bug), reset it.
                if isinstance(data, dict):
                    return data
                else:
                    log.warning(f"Dedup file was a {type(data)}, not a dict. Resetting.")
                    return {}
                # --- END OF FIX ---
        
    except Exception as e:
        log.warning(f"Could not load dedup file ({e}), starting fresh.")
    
    # This is the default if the file doesn't exist or is empty
    return {}
def save_dedup(store: Dict[str, Dict]) -> None:
    try:
        with open(DEDUP_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
        log.info(f"Dedup store saved with {len(store)} entries")
    except Exception as e:
        log.warning(f"Could not write dedup file: {e}")
# Auth verification
def verify_wp_auth() -> bool:
    if not WP_USER or not WP_APP_PASSWORD:
        log.error("❌ CRITICAL: Missing WP_USER or WP_APP_PASSWORD!")
        return False
    try:
        log.info(f"🔐 Verifying WordPress authentication for user: {WP_USER}")
        r = S.get(f"{WP_API_ROOT}/users/me", auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD), timeout=20)
        if r.status_code == 200:
            j = r.json()
            log.info(f"✅ Authenticated as: {j.get('name')} (ID={j.get('id')})")
            return True
        else:
            log.error(f"❌ Authentication failed! Status={r.status_code}")
            return False
    except Exception as e:
        log.error(f"❌ Auth check error: {e}")
        return False
# Determine working CPT route
def resolve_job_endpoint() -> str:
    primary = f"{WP_API_ROOT}/{WP_JOB_ROUTE_PRIMARY}"
    fallback = f"{WP_API_ROOT}/{WP_JOB_ROUTE_FALLBACK}"
    try:
        log.info(f"🔍 Checking primary route: {primary}")
        r = S.options(primary, timeout=15)
        if r.status_code < 400:
            log.info(f"✅ Using primary route: {primary}")
            return primary
    except Exception as e:
        log.warning(f"Primary route check failed: {e}")
    
    try:
        log.info(f"🔍 Checking fallback route: {fallback}")
        r2 = S.options(fallback, timeout=15)
        if r2.status_code < 400:
            log.warning(f"✅ Using fallback: {fallback}")
            return fallback
    except Exception as e:
        log.warning(f"Fallback route check failed: {e}")
    
    log.warning(f"⚠️ Defaulting to: {primary}")
    return primary
WP_JOB_ENDPOINT = resolve_job_endpoint()
WP_MEDIA_ENDPOINT = f"{WP_API_ROOT}/media"
# Normalize job data
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
# Dedup via REST
def wp_search_existing(title: str, company: Optional[str]) -> Optional[Dict]:
    if not title:
        return None
    try:
        norm_title = title.strip().lower()
        search_query = f"{title} {company or ''}".strip()
        params = {"search": search_query, "per_page": 10}
        r = S.get(WP_JOB_ENDPOINT, params=params, timeout=25)
        if r.status_code != 200:
            return None
        results = r.json()
        for item in results:
            it_title = (item.get("title", {}) or {}).get("rendered", "")
            it_norm = it_title.strip().lower()
            if it_norm == norm_title:
                log.debug(f"Found existing job (exact match): {title}")
                return item
            title_words = set(norm_title.split())
            item_words = set(it_norm.split())
            if title_words and item_words:
                overlap = len(title_words & item_words) / max(len(title_words), len(item_words))
                if overlap >= 0.8:
                    log.debug(f"Found existing job (fuzzy match {overlap*100:.0f}%): {title}")
                    return item
        return None
    except Exception as e:
        log.debug(f"Search error: {e}")
        return None
# Upload logo
def wp_upload_logo(logo_url: str) -> Optional[int]:
    if not logo_url:
        return None
    try:
        r_img = S.get(logo_url, timeout=30)
        if r_img.status_code != 200 or not r_img.content:
            return None
        # FIXED: Changed split("/"[-1] to split("/")[-1]
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
            media_id = r_up.json().get("id")
            log.debug(f"Uploaded logo: {filename} (ID={media_id})")
            return media_id
        return None
    except Exception as e:
        log.debug(f"Logo upload error: {e}")
        return None
# Post job to WPJM
def wp_post_job(job: Dict) -> Optional[Dict]:
    global WP_JOB_ENDPOINT
    log.info(f"📤 Posting job: {job.get('title')} @ {job.get('company')}")
    payload = {
        "title": job.get("title") or "Untitled Job",
        "content": job.get("description") or "",
        "status": "publish",
    }
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
        alt = f"{WP_API_ROOT}/{WP_JOB_ROUTE_FALLBACK}"
        log.warning(f"⚠️ Primary route returned 404; trying fallback...")
        rr = S.post(
            alt,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=45,
        )
        if rr.status_code in (200, 201):
            created = rr.json()
            WP_JOB_ENDPOINT = alt
            log.info(f"✅ Created job on fallback route (ID={created.get('id')})")
            return _update_job_meta(created, job)
        else:
            log.error(f"❌ Error posting to fallback: {rr.status_code}")
            return None
    elif r.status_code in (200, 201):
        created = r.json()
        log.info(f"✅ Created job (ID={created.get('id')})")
        return _update_job_meta(created, job)
    else:
        log.error(f"❌ Error posting: {r.status_code} - {r.text[:400]}")
        return None
def _update_job_meta(created: Dict, job: Dict) -> Optional[Dict]:
    post_id = created.get("id")
    if not post_id:
        return created
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
    rm = S.put(
        f"{WP_JOB_ENDPOINT}/{post_id}",
        auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
        headers={"Content-Type": "application/json"},
        data=json.dumps(meta_payload),
        timeout=40,
    )
    if rm.status_code in (200, 201):
        out = rm.json()
        job_link = out.get('link', 'N/A')
        log.info(f"✅ Updated metadata: {job_link}")
        return out
    else:
        log.warning(f"⚠️ Meta update failed: {rm.status_code}")
        log.info(f"✅ Job created: {created.get('link')}")
        return created
# Fetch from JSearch with exponential backoff on 429
def fetch_from_jsearch() -> List[Dict]:
    if not JSEARCH_API_KEY:
        log.error("❌ CRITICAL: JSearch API key missing!")
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
    }
    log.info(f"🔍 Fetching jobs from JSearch...")
    log.info(f"   Query: {JSEARCH_QUERY}")
    log.info(f"   Country: {JSEARCH_COUNTRY}")
    log.info(f"   Pages: {JSEARCH_NUM_PAGES}")
    log.info(f"   Date Posted: {JSEARCH_DATE_POSTED}")
    max_attempts = 5
    attempt = 0
    delay = 2  # start at 2 seconds
    max_delay = 60  # cap at 1 minute
    while attempt < max_attempts:
        try:
            r = S.get(url, headers=headers, params=params, timeout=30)
            if r.status_code == 200:
                data = r.json()
                jobs = data.get("data") or data.get("results") or []
                log.info(f"✅ Fetched {len(jobs)} jobs from JSearch")
                for j in jobs:
                    j["source"] = j.get("job_publisher") or "JSearch"
                return jobs
            elif r.status_code == 429:
                attempt += 1
                log.warning(f"⚠️ JSearch rate limited (429). Attempt {attempt} of {max_attempts}. Waiting {delay}s.")
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
            else:
                log.error(f"❌ JSearch API error: {r.status_code}")
                log.error(f"   Response: {r.text[:300]}")
                return []
        except Exception as e:
            log.error(f"❌ JSearch API error: {e}")
            time.sleep(delay)
            delay = min(delay * 2, max_delay)
            attempt += 1
    log.error(f"❌ JSearch: Exceeded maximum retry attempts due to 429 errors.")
    return []
# Print recent listings
def print_recent_wp_listings(n: int = 5):
    try:
        r = S.get(f"{WP_JOB_ENDPOINT}?per_page={n}", timeout=20)
        if r.status_code != 200:
            log.info(f"Could not fetch recent listings: {r.status_code}")
            return
        items = r.json()
        if not items:
            log.info("No job listings on website yet")
            return
        log.info(f"📋 Latest {len(items)} jobs on website:")
       
