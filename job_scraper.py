#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechJobs360 FREE Job Scraper -> WordPress
100% FREE - No Paid APIs!
Sources:
- Remotive.io API (Free)
- Arbeitnow API (Free)
- GitHub Jobs RSS (Free)
- Authentic Jobs API (Free)

Filters: Last 24 hours only
"""

import os
import sys
import json
import time
import logging
from typing import Dict, List
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter, Retry
from requests.auth import HTTPBasicAuth

# CONFIG
WP_BASE_URL = "https://techjobs360.com"
WP_USER = "admintech"
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
DEDUP_FILE = "posted_jobs.json"

# REST endpoints
WP_JOB_ENDPOINT = f"{WP_BASE_URL}/wp-json/wp/v2/job_listing"
WP_MEDIA_ENDPOINT = f"{WP_BASE_URL}/wp-json/wp/v2/media"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# Session with retries
S = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
S.mount("https://", HTTPAdapter(max_retries=retries))
S.mount("http://", HTTPAdapter(max_retries=retries))

def load_dedup() -> Dict:
    """Load deduplication store."""
    if not os.path.exists(DEDUP_FILE):
        return {"ids": [], "combos": []}
    try:
        with open(DEDUP_FILE, "r") as f:
            return json.load(f)
    except:
        return {"ids": [], "combos": []}

def save_dedup(store: Dict):
    """Save deduplication store."""
    try:
        with open(DEDUP_FILE, "w") as f:
            json.dump(store, f, indent=2)
    except Exception as e:
        log.error(f"Failed to save dedup: {e}")

def fetch_from_remotive() -> List[Dict]:
    """Fetch from Remotive.io API (FREE, no key needed)."""
    jobs = []
    try:
        url = "https://remotive.io/api/remote-jobs"
        params = {"category": "software-dev", "limit": 50}
        r = S.get(url, params=params, timeout=30)
        if r.status_code == 200:
            data = r.json()
            for job in data.get("jobs", []):
                # Filter last 24 hours
                pub_date = job.get("publication_date", "")
                if is_within_24_hours(pub_date):
                    jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company_name", ""),
                        "location": job.get("candidate_required_location", "Remote"),
                        "description": job.get("description", ""),
                        "url": job.get("url", ""),
                        "logo": job.get("company_logo"),
                        "type": job.get("job_type", "Full-time"),
                        "source": "Remotive.io",
                        "id": job.get("id")
                    })
            log.info(f"Remotive: {len(jobs)} jobs")
    except Exception as e:
        log.error(f"Remotive error: {e}")
    return jobs

def fetch_from_arbeitnow() -> List[Dict]:
    """Fetch from Arbeitnow API (FREE, no key needed)."""
    jobs = []
    try:
        url = "https://www.arbeitnow.com/api/job-board-api"
        r = S.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            for job in data.get("data", []):
                created = job.get("created_at", "")
                if is_within_24_hours(created):
                    jobs.append({
                        "title": job.get("title", ""),
                        "company": job.get("company_name", ""),
                        "location": job.get("location", "Remote"),
                        "description": job.get("description", ""),
                        "url": job.get("url", ""),
                        "logo": None,
                        "type": "Full-time",
                        "source": "Arbeitnow",
                        "id": job.get("slug")
                    })
            log.info(f"Arbeitnow: {len(jobs)} jobs")
    except Exception as e:
        log.error(f"Arbeitnow error: {e}")
    return jobs

def is_within_24_hours(date_str: str) -> bool:
    """Check if date is within last 24 hours."""
    if not date_str:
        return False
    try:
        # Try different date formats
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ]
        job_date = None
        for fmt in formats:
            try:
                # Remove timezone info if present
                clean_date = date_str.split(".")[0].split("+")[0].split("Z")[0]
                job_date = datetime.strptime(clean_date, fmt)
                break
            except:
                continue
        
        if job_date:
            cutoff = datetime.now() - timedelta(days=1)
            return job_date >= cutoff
    except:
        pass
    return False

def is_duplicate(job: Dict, dedup_store: Dict) -> bool:
    """Check if job is duplicate."""
    job_id = str(job.get("id", ""))
    if job_id and job_id in dedup_store.get("ids", []):
        return True
    
    combo = f"{job.get('title', '').lower().strip()}||{job.get('company', '').lower().strip()}"
    if combo in dedup_store.get("combos", []):
        return True
    
    return False

def wp_upload_logo(logo_url: str, alt_text: str) -> int:
    """Upload logo to WordPress."""
    if not logo_url:
        return None
    try:
        r_img = S.get(logo_url, timeout=20)
        if r_img.status_code != 200:
            return None
        
        filename = logo_url.split("/")[-1].split("?")[0] or "logo.png"
        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Type": r_img.headers.get("Content-Type", "image/png"),
        }
        
        r_up = S.post(
            WP_MEDIA_ENDPOINT,
            headers=headers,
            data=r_img.content,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            timeout=30
        )
        
        if r_up.status_code in (200, 201):
            return r_up.json().get("id")
    except Exception as e:
        log.error(f"Logo upload error: {e}")
    return None

def wp_post_job(job: Dict, dedup_store: Dict):
    """Post job to WordPress."""
    if is_duplicate(job, dedup_store):
        log.info(f"⏭️  Skipping duplicate: {job['title']}")
        return
    
    try:
        featured_media = None
        if job.get("logo"):
            alt = f"{job.get('company', 'Company')} logo"
            featured_media = wp_upload_logo(job["logo"], alt)
        
        wp_data = {
            "title": job.get("title", "Untitled"),
            "content": job.get("description", ""),
            "status": "publish",
            "meta": {
                "_company_name": job.get("company", ""),
                "_job_location": job.get("location", ""),
                "_application": job.get("url", ""),
                "_job_source_attribution": f"Source: {job.get('source', 'Unknown')}",
            }
        }
        
        if featured_media:
            wp_data["featured_media"] = featured_media
        
        r = S.post(
            WP_JOB_ENDPOINT,
            json=wp_data,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            timeout=40
        )
        
        if r.status_code in (200, 201):
            log.info(f"✅ Posted: {job['title']} @ {job['company']}")
            
            # Update dedup
            if job.get("id"):
                dedup_store["ids"].append(str(job["id"]))
            combo = f"{job['title'].lower().strip()}||{job['company'].lower().strip()}"
            if combo not in dedup_store["combos"]:
                dedup_store["combos"].append(combo)
            save_dedup(dedup_store)
        else:
            log.error(f"Failed: {r.status_code} - {r.text[:100]}")
    except Exception as e:
        log.error(f"Post error: {e}")

def main():
    """Main function."""
    log.info("🚀 Starting TechJobs360 FREE Scraper")
    log.info("📡 Sources: Remotive.io, Arbeitnow (100% FREE)")
    log.info("📅 Filter: Jobs posted in last 24 hours only")
    
    dedup_store = load_dedup()
    
    all_jobs = []
    all_jobs.extend(fetch_from_remotive())
    all_jobs.extend(fetch_from_arbeitnow())
    
    log.info(f"Total fetched: {len(all_jobs)} jobs")
    
    for job in all_jobs:
        wp_post_job(job, dedup_store)
        time.sleep(2)  # Rate limiting
    
    log.info("✅ Scraping cycle complete!")

if __name__ == "__main__":
    main()
