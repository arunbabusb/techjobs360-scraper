#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Real-job scraper -> WordPress (WP Job Manager)
- Adzuna + JSearch fetchers
- Posts to /wp-json/wp/v2/job-listings
- Application Passwords auth
"""

import os, sys, json, time, logging
from typing import Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter, Retry
from requests.auth import HTTPBasicAuth

WP_BASE_URL      = os.getenv("WP_BASE_URL", "https://techjobs360.com").rstrip("/")
WP_USER          = os.getenv("WP_USER", "")
WP_APP_PASSWORD  = os.getenv("WP_APP_PASSWORD", "")
WP_API_URL       = f"{WP_BASE_URL}/wp-json/wp/v2/job-listings"  # WPJM REST base

# --- JSearch (RapidAPI) ---
JSEARCH_API_KEY  = os.getenv("JSEARCH_API_KEY", "")
JSEARCH_HOST     = os.getenv("JSEARCH_HOST", "jsearch.p.rapidapi.com")
JSEARCH_QUERY    = os.getenv("JSEARCH_QUERY", "software developer OR data engineer")
JSEARCH_NUM_PAGES= int(os.getenv("JSEARCH_NUM_PAGES", "1"))

# --- Adzuna ---
ADZUNA_APP_ID    = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY   = os.getenv("ADZUNA_APP_KEY", "")
COUNTRIES        = os.getenv("COUNTRIES", "in,us,fr,gb,de").split(",")
ADZUNA_RESULTS_PER_PAGE = int(os.getenv("ADZUNA_RESULTS_PER_PAGE", "20"))
ADZUNA_MAX_DAYS_OLD     = int(os.getenv("ADZUNA_MAX_DAYS_OLD", "3"))
ADZUNA_WHAT             = os.getenv("ADZUNA_WHAT", "software OR developer OR engineer")

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s", handlers=[logging.StreamHandler(sys.stdout)])
log = logging.getLogger("job_scraper")

def new_session():
    s = requests.Session()
    retries = Retry(total=4, backoff_factor=0.6, status_forcelist=[429,500,502,503,504], allowed_methods=["GET","POST"])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

S = new_session()

# ---------- helpers ----------
def normalize_job(raw: Dict) -> Dict:
    title = raw.get("job_title") or raw.get("title")
    description = raw.get("job_description") or raw.get("description") or ""
    company = raw.get("employer_name") or raw.get("company") or (raw.get("company", {}) or {}).get("display_name")
    location = raw.get("job_city") or raw.get("job_country") or (raw.get("location") or {}).get("display_name") or raw.get("location")
    apply_url = raw.get("job_apply_link") or raw.get("redirect_url") or raw.get("url")
    salary = raw.get("job_min_salary") or raw.get("salary_min") or raw.get("salary")
    logo = raw.get("employer_logo") or raw.get("logo_url")
    deadline = raw.get("job_offer_expiration_datetime_utc") or raw.get("deadline_iso")
    return {"title": title, "description": description, "company": company, "location": location,
            "apply_url": apply_url, "salary": salary, "logo_url": logo, "deadline_iso": deadline,
            "source": raw.get("source") or raw.get("job_publisher"), "external_id": raw.get("id") or raw.get("job_id")}

def wp_search_existing(title: str, company: Optional[str]) -> Optional[Dict]:
    try:
        params = {"search": f"{title} {company or ''}".strip(), "per_page": 5}
        r = S.get(WP_API_URL, params=params, timeout=25)
        if r.status_code != 200: return None
        for item in r.json():
            it_title = (item.get("title", {}) or {}).get("rendered", "")
            if it_title.strip().lower() == (title or "").strip().lower(): return item
        return None
    except Exception: return None

def wp_upload_logo(logo_url: str) -> Optional[int]:
    if not logo_url: return None
    try:
        r_img = S.get(logo_url, timeout=30)
        if r_img.status_code != 200 or not r_img.content: return None
        filename = (logo_url.split("?")[0].split("/")[-1] or f"logo-{int(time.time())}.png").replace('"', "")
        media_endpoint = f"{WP_BASE_URL}/wp-json/wp/v2/media"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"', "Content-Type": r_img.headers.get("Content-Type","image/png")}
        r_up = S.post(media_endpoint, headers=headers, data=r_img.content, auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD), timeout=40)
        if r_up.status_code in (200,201): return r_up.json().get("id")
        return None
    except Exception: return None

def wp_post_job(job: Dict) -> Optional[Dict]:
    payload = {
        "title": job["title"] or "Untitled Job",
        "content": job["description"] or "",
        "status": "publish",
        "meta": {  # WPJM stores its fields in meta accessible via REST
            "_company_name": job.get("company"),
            "_job_location": job.get("location"),
            "_application": job.get("apply_url"),
            "_job_salary": job.get("salary"),
        }
    }
    if job.get("deadline_iso"): payload["meta"]["_job_deadline"] = job["deadline_iso"]
    if job.get("logo_url"):
        media_id = wp_upload_logo(job["logo_url"])
        if media_id: payload["featured_media"] = media_id

    r = S.post(WP_API_URL, auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
               headers={"Content-Type":"application/json"}, data=json.dumps(payload), timeout=45)
    if r.status_code == 201:
        created = r.json()
        log.info(f"Posted: {created.get('id')} | {created.get('link')}")
        return created
    else:
        log.error(f"Error posting to WordPress: {r.status_code} - {r.text[:400]}")
        return None

# ---------- real fetchers ----------
def fetch_from_adzuna(country: str) -> List[Dict]:
    # https://developer.adzuna.com/activedocs (jobs/{country}/search/{page})  [CITE]
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY: return []
    url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID, "app_key": ADZUNA_APP_KEY,
        "results_per_page": ADZUNA_RESULTS_PER_PAGE,
        "what": ADZUNA_WHAT, "max_days_old": ADZUNA_MAX_DAYS_OLD,
        "content-type": "application/json", "sort_by": "date", "salary_include_unknown": 1
    }
    r = S.get(url, params=params, timeout=30)
    if r.status_code != 200:
        log.warning(f"Adzuna {country} error {r.status_code}: {r.text[:200]}")
        return []
    results = (r.json().get("results") or [])
    for j in results: j["source"] = "Adzuna"
    return results

def fetch_from_jsearch() -> List[Dict]:
    # RapidAPI requires X-RapidAPI-Key and X-RapidAPI-Host headers.  [CITE]
    if not JSEARCH_API_KEY: return []
    url = f"https://{JSEARCH_HOST}/search"
    headers = {"X-RapidAPI-Key": JSEARCH_API_KEY, "X-RapidAPI-Host": JSEARCH_HOST}
    params = {"query": JSEARCH_QUERY, "num_pages": JSEARCH_NUM_PAGES, "date_posted": "week"}
    r = S.get(url, headers=headers, params=params, timeout=30)
    if r.status_code != 200:
        log.warning(f"JSearch error {r.status_code}: {r.text[:200]}")
        return []
    data = r.json()
    jobs = data.get("data") or data.get("results") or []
    for j in jobs: j["source"] = j.get("job_publisher") or "JSearch"
    return jobs

# ---------- main ----------
def main():
    log.info("Starting job scraper...")
    # sanity-check WP REST
    try:
        test = S.get(f"{WP_BASE_URL}/wp-json/wp/v2", timeout=20)
        if test.status_code != 200: 
            log.error(f"WordPress REST unreachable: {test.status_code}")
            return
        log.info("WordPress REST reachable ✅")
    except Exception as e:
        log.exception(f"WP REST error: {e}"); return

    all_jobs: List[Dict] = []

    # Adzuna (multiple countries)
    log.info(f"Fetching jobs from countries: {', '.join(COUNTRIES)}")
    for cc in COUNTRIES:
        cc = cc.strip()
        log.info(f"Fetching jobs from Adzuna for country: {cc}")
        adz = fetch_from_adzuna(cc)
        log.info(f"Fetched {len(adz)} jobs from Adzuna ({cc})")
        all_jobs.extend([normalize_job(x) for x in adz])

    # JSearch
    log.info("Fetching jobs from JSearch...")
    js = fetch_from_jsearch()
    log.info(f"Fetched {len(js)} jobs from JSearch")
    all_jobs.extend([normalize_job(x) for x in js])

    posted = 0
    for job in all_jobs:
        if not (job.get("title") and job.get("apply_url")): continue
        if wp_search_existing(job["title"], job.get("company")):
            log.info(f"Skip duplicate: {job['title']} @ {job.get('company')}")
            continue
        if wp_post_job(job): posted += 1
        time.sleep(1.0)

    log.info(f"Done. Posted {posted} new jobs.")

if __name__ == "__main__":
    main()
