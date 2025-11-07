#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechJobs360 Job Scraper -> WordPress (WP Job Manager)
Enhanced Version with ALL JSearch API Endpoints:
- Job Search (primary endpoint)
- Job Details (detailed job information)
- Job Salary (salary estimation)
- Company Job Salary (company-specific salary data)
- Deduplication based on job ID/title+company
- Alt text for company logos
- Source attribution field
- Expiry handling for jobs
- Only non-sensitive allowed fields
- Attribution info for JSearch API
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

JSEARCH_API_KEY = "11d1b727f2msh1be47752caa8059p147b94jsnd9d66d2e5ecd"
JSEARCH_HOST = "jsearch.p.rapidapi.com"
JSEARCH_QUERY = "software engineer"
JSEARCH_COUNTRY = "in"
JSEARCH_NUM_PAGES = 5
JSEARCH_DATE_POSTED = "week"

LOOP_INTERVAL_SEC = int(os.getenv("LOOP_INTERVAL_SEC", "1800"))
DEDUP_FILE = os.getenv("DEDUP_FILE", "posted_jobs.json")

# REST endpoints
WP_JOB_ENDPOINT = f"{WP_BASE_URL}/wp-json/wp/v2/job_listing"
WP_MEDIA_ENDPOINT = f"{WP_BASE_URL}/wp-json/wp/v2/media"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# Session with retries
S = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
S.mount("https://", HTTPAdapter(max_retries=retries))
S.mount("http://", HTTPAdapter(max_retries=retries))

def load_dedup() -> Dict:
    """Load deduplication store from file."""
    if not os.path.exists(DEDUP_FILE):
        return {}
    try:
        with open(DEDUP_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.warning(f"Failed to load dedup file: {e}")
        return {}

def save_dedup(store: Dict):
    """Save deduplication store to file."""
    try:
        with open(DEDUP_FILE, "w", encoding="utf-8") as f:
            json.dump(store, f, indent=2)
    except Exception as e:
        log.error(f"Failed to save dedup file: {e}")

def fetch_from_jsearch() -> List[Dict]:
    """
    Fetch jobs from JSearch API - Job Search endpoint.
    Returns list of raw job data dictionaries.
    """
    all_jobs = []
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": JSEARCH_HOST
    }
    
    for page in range(1, JSEARCH_NUM_PAGES + 1):
        try:
            url = "https://jsearch.p.rapidapi.com/search"
            params = {
                "query": JSEARCH_QUERY,
                "page": str(page),
                "num_pages": "1",
                "date_posted": JSEARCH_DATE_POSTED,
            }
            if JSEARCH_COUNTRY:
                params["country"] = JSEARCH_COUNTRY
            
            log.info(f"Fetching JSearch page {page}...")
            r = S.get(url, headers=headers, params=params, timeout=30)
            
            if r.status_code == 200:
                data = r.json()
                jobs = data.get("data", [])
                log.info(f"Got {len(jobs)} jobs from page {page}")
                all_jobs.extend(jobs)
            else:
                log.warning(f"JSearch API returned status {r.status_code}")
            
            time.sleep(1)  # Rate limiting
        except Exception as e:
            log.error(f"Error fetching JSearch page {page}: {e}")
    
    return all_jobs

def get_job_details(job_id: str) -> Optional[Dict]:
    """
    Fetch detailed job information using Job Details endpoint.
    Returns enhanced job details or None if failed.
    """
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": JSEARCH_HOST
    }
    
    try:
        url = "https://jsearch.p.rapidapi.com/job-details"
        params = {"job_id": job_id}
        
        log.info(f"Fetching job details for {job_id}...")
        r = S.get(url, headers=headers, params=params, timeout=30)
        
        if r.status_code == 200:
            data = r.json()
            details = data.get("data", [{}])[0]
            return details
        else:
            log.warning(f"Job Details API returned status {r.status_code}")
    except Exception as e:
        log.error(f"Error fetching job details for {job_id}: {e}")
    
    return None

def get_job_salary(job_title: str, location: str = None) -> Optional[Dict]:
    """
    Fetch salary estimation using Job Salary endpoint.
    Returns salary data or None if failed.
    """
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": JSEARCH_HOST
    }
    
    try:
        url = "https://jsearch.p.rapidapi.com/salary"
        params = {"job_title": job_title}
        if location:
            params["location"] = location
        
        log.info(f"Fetching salary data for {job_title}...")
        r = S.get(url, headers=headers, params=params, timeout=30)
        
        if r.status_code == 200:
            data = r.json()
            return data.get("data", [{}])[0]
        else:
            log.warning(f"Job Salary API returned status {r.status_code}")
    except Exception as e:
        log.error(f"Error fetching salary for {job_title}: {e}")
    
    return None

def get_company_job_salary(company: str, job_title: str) -> Optional[Dict]:
    """
    Fetch company-specific salary data using Company Job Salary endpoint.
    Returns salary data or None if failed.
    """
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": JSEARCH_HOST
    }
    
    try:
        url = "https://jsearch.p.rapidapi.com/company-job-salary"
        params = {
            "company": company,
            "job_title": job_title
        }
        
        log.info(f"Fetching company salary data for {company} - {job_title}...")
        r = S.get(url, headers=headers, params=params, timeout=30)
        
        if r.status_code == 200:
            data = r.json()
            return data.get("data", [{}])[0]
        else:
            log.warning(f"Company Job Salary API returned status {r.status_code}")
    except Exception as e:
        log.error(f"Error fetching company salary for {company}: {e}")
    
    return None

def enhance_with_api_data(job: Dict) -> Dict:
    """
    Enhance job data with additional API endpoints:
    - Get detailed job information
    - Add salary estimations
    - Add company-specific salary data
    """
    job_id = job.get("external_id")
    job_title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    
    # Get detailed job information if job_id available
    if job_id:
        details = get_job_details(job_id)
        if details:
            # Merge additional details
            if details.get("job_description"):
                job["description"] = details.get("job_description")
            if details.get("job_highlights"):
                job["highlights"] = details.get("job_highlights")
    
    # Get salary estimation
    salary_data = get_job_salary(job_title, location)
    if salary_data:
        job["salary_min"] = salary_data.get("salary_min")
        job["salary_max"] = salary_data.get("salary_max")
        job["salary_currency"] = salary_data.get("salary_currency", "USD")
    
    # Get company-specific salary if available
    if company and job_title:
        company_salary = get_company_job_salary(company, job_title)
        if company_salary:
            job["company_salary_min"] = company_salary.get("salary_min")
            job["company_salary_max"] = company_salary.get("salary_max")
            job["company_salary_currency"] = company_salary.get("salary_currency", "USD")
    
    # Rate limiting between API calls
    time.sleep(0.5)
    
    return job

def normalize_job(raw: Dict) -> Dict:
    """
    Extract and normalize ONLY public, non-sensitive job fields.
    NO personal information, email, phone, user data!
    Adds source attribution.
    """
    return {
        "external_id": raw.get("job_id", ""),
        "title": raw.get("job_title", ""),
        "company": raw.get("employer_name", ""),
        "logo_url": raw.get("employer_logo"),
        "location": raw.get("job_city") or raw.get("job_state") or raw.get("job_country", ""),
        "description": raw.get("job_description", ""),
        "employment_type": raw.get("job_employment_type", ""),
        "posted_at": raw.get("job_posted_at_datetime_utc"),
        "expires_at": raw.get("job_offer_expiration_datetime_utc"),
        "apply_link": raw.get("job_apply_link"),
        "source": raw.get("job_publisher", "JSearch API"),
        "attribution": f"Powered by JSearch API. Source: {raw.get('job_publisher', 'Unknown')}"
    }

def is_duplicate(job: Dict, dedup_store: Dict) -> bool:
    """
    Check if job already posted.
    Deduplication by external_id AND by title+company combo.
    """
    ext_id = job.get("external_id")
    title = job.get("title", "").strip().lower()
    company = job.get("company", "").strip().lower()
    
    if ext_id and ext_id in dedup_store:
        return True
    
    combo_key = f"{title}||{company}"
    if combo_key in dedup_store.get("combos", []):
        return True
    
    return False

def wp_upload_logo_with_alt(logo_url: str, alt_text: str) -> Optional[int]:
    """
    Upload company logo to WordPress media library WITH alt text.
    """
    try:
        r_img = S.get(logo_url, timeout=30)
        if r_img.status_code != 200:
            return None
        
        filename = logo_url.split("/")[-1].split("?")[0] or "company_logo.png"
        
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": r_img.headers.get("Content-Type", "image/png"),
            "Content-Description": alt_text
        }
        
        r_up = S.post(
            WP_MEDIA_ENDPOINT,
            headers=headers,
            data=r_img.content,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            timeout=40
        )
        
        if r_up.status_code in (200, 201):
            media_id = r_up.json().get("id")
            log.info(f"Uploaded logo: {filename} (ID={media_id})")
            return media_id
        
        return None
    except Exception as e:
        log.error(f"Logo upload error: {e}")
        return None

def format_salary_info(job: Dict) -> str:
    """
    Format salary information for job description.
    """
    salary_info = []
    
    if job.get("salary_min") and job.get("salary_max"):
        currency = job.get("salary_currency", "USD")
        salary_info.append(f"Estimated Salary: {currency} {job['salary_min']:,.0f} - {job['salary_max']:,.0f}")
    
    if job.get("company_salary_min") and job.get("company_salary_max"):
        currency = job.get("company_salary_currency", "USD")
        salary_info.append(f"Company Salary Range: {currency} {job['company_salary_min']:,.0f} - {job['company_salary_max']:,.0f}")
    
    return "\n\n".join(salary_info) if salary_info else ""

def wp_post_job(job: Dict, dedup_store: Dict):
    """
    Post job to WordPress if not duplicate.
    Includes all enhanced data from multiple API endpoints.
    """
    if is_duplicate(job, dedup_store):
        log.info(f"⏭️  Skipping duplicate: {job.get('title')} @ {job.get('company')}")
        return
    
    try:
        # Upload logo with alt text if available
        featured_media_id = None
        if job.get("logo_url"):
            alt_text = f"{job.get('company', 'Company')} logo"
            featured_media_id = wp_upload_logo_with_alt(job["logo_url"], alt_text)
        
        # Format job description with salary info
        description = job.get("description", "")
        salary_info = format_salary_info(job)
        if salary_info:
            description += f"\n\n### Salary Information\n{salary_info}"
        
        # Add highlights if available
        if job.get("highlights"):
            description += f"\n\n### Job Highlights\n{json.dumps(job['highlights'], indent=2)}"
        
        # Prepare WP post data
        wp_data = {
            "title": job.get("title", "Untitled Position"),
            "content": description,
            "status": "publish",
            "meta": {
                "_company_name": job.get("company", ""),
                "_job_location": job.get("location", ""),
                "_application": job.get("apply_link", ""),
                "_job_deadline": job.get("expires_at", ""),
                "_job_source_attribution": job.get("attribution", ""),
            }
        }
        
        if featured_media_id:
            wp_data["featured_media"] = featured_media_id
        
        # Post to WordPress
        r = S.post(
            WP_JOB_ENDPOINT,
            json=wp_data,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            timeout=40
        )
        
        if r.status_code in (200, 201):
            post_id = r.json().get("id")
            log.info(f"✅ Posted: {job.get('title')} @ {job.get('company')} (ID={post_id})")
            
            # Update dedup store
            ext_id = job.get("external_id")
            if ext_id:
                dedup_store[ext_id] = int(time.time())
            
            # Track title+company combo
            if "combos" not in dedup_store:
                dedup_store["combos"] = []
            combo_key = f"{job.get('title', '').strip().lower()}||{job.get('company', '').strip().lower()}"
            if combo_key not in dedup_store["combos"]:
                dedup_store["combos"].append(combo_key)
            
            save_dedup(dedup_store)
        else:
            log.error(f"Failed to post job: {r.status_code} - {r.text[:200]}")
    
    except Exception as e:
        log.error(f"Error posting job: {e}")

def remove_expired_jobs_from_wp():
    """
    Remove expired jobs from WordPress based on expiry date.
    """
    log.info("Checking for expired jobs in WordPress...")
    try:
        r = S.get(WP_JOB_ENDPOINT, params={"per_page": 50}, timeout=40)
        
        if r.status_code == 200:
            items = r.json()
            
            for item in items:
                meta = item.get("meta") or {}
                deadline = meta.get("_job_deadline")
                post_id = item.get("id")
                
                if deadline:
                    try:
                        t_exp = int(time.mktime(time.strptime(deadline[:19], "%Y-%m-%dT%H:%M:%S")))
                        if t_exp < int(time.time()):
                            delr = S.delete(
                                f"{WP_JOB_ENDPOINT}/{post_id}",
                                auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
                                timeout=35
                            )
                            if delr.status_code in (200, 204, 410):
                                log.info(f"🗑️  Removed expired job ID={post_id}")
                    except Exception as e:
                        log.warning(f"Failed deadline check for job {post_id}: {e}")
    
    except Exception as e:
        log.warning(f"Failed expired job check: {e}")

def main_loop():
    """
    Main scheduler loop with ALL JSearch API endpoints.
    Continuously fetches jobs, enriches with additional data, posts new ones.
    """
    log.info("🚀 Starting TechJobs360 Scraper with Enhanced JSearch API Integration")
    log.info("📡 Using endpoints: Job Search, Job Details, Job Salary, Company Job Salary")
    
    dedup_store = load_dedup()
    
    while True:
        try:
            log.info("="*60)
            log.info("Starting new scraping cycle...")
            
            # Fetch jobs from primary search endpoint
            jobs = fetch_from_jsearch()
            log.info(f"Fetched {len(jobs)} jobs from Job Search endpoint")
            
            # Process each job
            for idx, raw in enumerate(jobs, 1):
                log.info(f"\nProcessing job {idx}/{len(jobs)}...")
                
                # Normalize basic job data
                job = normalize_job(raw)
                
                # Enhance with additional API data (details, salary, company salary)
                job = enhance_with_api_data(job)
                
                # Post to WordPress
                wp_post_job(job, dedup_store)
                
                # Rate limiting between jobs
                time.sleep(1)
            
            # Cleanup expired jobs
            remove_expired_jobs_from_wp()
            
            log.info("="*60)
            log.info(f"✅ Cycle complete! Sleeping {LOOP_INTERVAL_SEC}s until next scrape...")
            time.sleep(LOOP_INTERVAL_SEC)
            
        except KeyboardInterrupt:
            log.info("\n🛑 Scraper stopped by user")
            break
        except Exception as e:
            log.error(f"Error in main loop: {e}")
            log.info("Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main_loop()
