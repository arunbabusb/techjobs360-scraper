#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechJobs360 FREE Job Scraper -> WordPress
100% FREE - No Paid APIs!

Sources:
- JSearch API (FREE tier from RapidAPI)
  Fetches from: LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google for Jobs

Filters: Last 24 hours only
"""

import os
import sys
import json
import time
import logging
import mimetypes
import re
from typing import Dict, List
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from requests.auth import HTTPBasicAuth

# CONFIG
WP_BASE_URL = "https://techjobs360.com"
WP_USER = "admintech"
WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
DEDUP_FILE = "posted_jobs.json"
JSEARCH_API_KEY = os.getenv("JSEARCH_API_KEY", "")  # JSearch API key
DRY_RUN = os.getenv('DRY_RUN', '0') == '1'  # If set to '1', don't post to WordPress (safe testing)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Requests session with retry
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount('https://', HTTPAdapter(max_retries=retries))
session.mount('http://', HTTPAdapter(max_retries=retries))

def load_posted_jobs() -> set:
    """Load previously posted job IDs"""
    if os.path.exists(DEDUP_FILE):
        try:
            with open(DEDUP_FILE, 'r') as f:
                data = json.load(f)
                return set(data.get('posted_job_ids', []))
        except Exception as e:
            logger.error(f"Error loading posted jobs: {e}")
    return set()


def save_posted_jobs(posted_ids: set):
    """Save posted job IDs"""
    try:
        with open(DEDUP_FILE, 'w') as f:
            json.dump({'posted_job_ids': list(posted_ids)}, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving posted jobs: {e}")


def generate_job_id(job: Dict) -> str:
    """Generate unique ID for job based on title + company + location"""
    title = job.get('job_title', '').lower().strip()
    company = job.get('employer_name', '').lower().strip()
    location = job.get('job_city', '').lower().strip()
    raw = f"{title}_{company}_{location}"
    # keep letters, digits, underscore and dash only
    sanitized = re.sub(r'[^a-z0-9_-]+', '_', raw)
    return sanitized.strip('_')


def fetch_jsearch_jobs() -> List[Dict]:
    """
    Fetch jobs from JSearch API (FREE tier)
    Covers: LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google for Jobs
    """
    if not JSEARCH_API_KEY:
        logger.error("JSEARCH_API_KEY not set in environment")
        return []
    
    jobs = []
    
    # Search queries for comprehensive coverage
    search_queries = [
        "software engineer",
        "data scientist",
        "product manager",
        "full stack developer",
        "devops engineer"
    ]
    
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
    }
    
    for query in search_queries:
        try:
            params = {
                "query": query,
                "page": "1",
                "num_pages": "1",
                "date_posted": "today"  # Last 24 hours
            }
            
            logger.info(f"Fetching JSearch jobs for: {query}")
            response = session.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception:
                    logger.error(f"Failed to parse JSON from JSearch response for '{query}'")
                    continue
                job_results = data.get('data', [])
                
                logger.info(f"Found {len(job_results)} jobs for '{query}'")
                
                for job in job_results:
                    # Extract and normalize job data
                    normalized_job = {
                        'job_title': job.get('job_title', 'Not specified'),
                        'employer_name': job.get('employer_name', 'Not specified'),
                        'employer_logo': job.get('employer_logo', ''),
                        'job_city': job.get('job_city', ''),
                        'job_state': job.get('job_state', ''),
                        'job_country': job.get('job_country', ''),
                        'job_description': job.get('job_description', ''),
                        'job_apply_link': job.get('job_apply_link', ''),
                        'job_posted_at_datetime_utc': job.get('job_posted_at_datetime_utc', ''),
                        'source': 'JSearch API',
                        'job_employment_type': job.get('job_employment_type', 'FULLTIME'),
                        'job_is_remote': job.get('job_is_remote', False),
                    }
                    
                    jobs.append(normalized_job)
                
                # Rate limit: FREE tier allows 5 requests per second
                time.sleep(1)
                
            elif response.status_code == 429:
                logger.warning(f"Rate limit hit for '{query}' - sleeping and skipping")
                time.sleep(5)
            else:
                logger.error(f"JSearch API error for '{query}': {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"Error fetching JSearch jobs for '{query}': {e}")
            continue
    
    return jobs


def upload_logo_to_wordpress(logo_url: str, company_name: str) -> str:
    """Upload company logo to WordPress media library"""
    if not logo_url:
        return ""
    
    if DRY_RUN:
        logger.info(f"DRY_RUN: would download and upload logo for {company_name} from {logo_url}")
        return ""
    
    try:
        # Download logo
        logo_response = session.get(logo_url, timeout=15)
        if logo_response.status_code != 200:
            logger.warning(f"Failed to download logo from {logo_url}: {logo_response.status_code}")
            return ""
        
        # Determine content type and extension
        content_type = ''
        try:
            content_type = (logo_response.headers.get('Content-Type') or '').split(';')[0].lower()
        except Exception:
            content_type = ''
        if not content_type:
            content_type = mimetypes.guess_type(logo_url)[0] or 'image/jpeg'
        ext = mimetypes.guess_extension(content_type) or '.jpg'

        # sanitize filename
        safe_name = re.sub(r'[^A-Za-z0-9._-]+', '_', company_name).strip('_') or 'logo'
        filename = f"{safe_name}_logo{ext}"

        files = {
            'file': (filename, logo_response.content, content_type)
        }
        
        # Upload to WordPress
        wp_media_url = f"{WP_BASE_URL}/wp-json/wp/v2/media"
        upload_response = session.post(
            wp_media_url,
            files=files,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            timeout=30
        )
        
        if upload_response.status_code in (200, 201):
            try:
                media_data = upload_response.json()
                return media_data.get('source_url', '')
            except Exception:
                logger.error("Uploaded logo but failed to parse JSON response from WordPress")
                return ""
        else:
            logger.error(f"Failed to upload media to WordPress: {upload_response.status_code} - {upload_response.text[:200]}")
    
    except Exception as e:
        logger.error(f"Error uploading logo for {company_name}: {e}")
    
    return ""


def post_job_to_wordpress(job: Dict) -> bool:
    """Post a job to WordPress via REST API"""
    try:
        # Build location string
        location_parts = []
        if job.get('job_city'):
            location_parts.append(job['job_city'])
        if job.get('job_state'):
            location_parts.append(job['job_state'])
        if job.get('job_country'):
            location_parts.append(job['job_country'])
        location = ', '.join(location_parts) if location_parts else 'Remote'
        
        # Upload logo if available (skip in DRY_RUN)
        logo_url = ""
        if job.get('employer_logo') and not DRY_RUN:
            logo_url = upload_logo_to_wordpress(job['employer_logo'], job['employer_name'])
        
        # Build job description
        description = job.get('job_description', '').strip()
        if not description:
            description = f"Position available at {job['employer_name']}. Apply via the application link."
        
        # Determine job type
        job_type = job.get('job_employment_type', 'FULLTIME').upper()
        if job.get('job_is_remote'):
            job_type_mapped = 'remote'
        elif 'FULL' in job_type:
            job_type_mapped = 'full-time'
        elif 'PART' in job_type:
            job_type_mapped = 'part-time'
        elif 'CONTRACT' in job_type:
            job_type_mapped = 'contract'
        elif 'INTERN' in job_type:
            job_type_mapped = 'internship'
        else:
            job_type_mapped = 'full-time'
        
        # Prepare WordPress post data
        post_data = {
            'title': f"{job['job_title']} at {job['employer_name']}",
            'content': description,
            'status': 'publish',
            'meta': {
                '_company_name': job['employer_name'],
                '_job_location': location,
                '_application': job.get('job_apply_link', ''),
                '_job_type': job_type_mapped,
                '_company_logo': logo_url,
                '_source': job.get('source', 'JSearch API'),
                '_posted_date': job.get('job_posted_at_datetime_utc', '')
            }
        }

        if DRY_RUN:
            logger.info(f"DRY_RUN - would post: {post_data['title']} (meta: {_short_meta := str(post_data['meta'])[:200]})")
            return True
        
        # Post to WordPress
        wp_post_url = f"{WP_BASE_URL}/wp-json/wp/v2/job_listing"
        response = session.post(
            wp_post_url,
            json=post_data,
            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
            timeout=30
        )
        
        if response.status_code in (200, 201):
            logger.info(f"✓ Posted: {job['job_title']} at {job['employer_name']}")
            return True
        else:
            # try to capture useful error info
            text = response.text or ''
            logger.error(f"Failed to post job: {response.status_code} - {text[:1000]}")
            return False
            
    except Exception as e:
        logger.error(f"Error posting job to WordPress: {e}")
        return False


def main():
    """Main execution function"""
    logger.info("=" * 60)
    logger.info("TechJobs360 FREE Job Scraper - JSearch API")
    logger.info("=" * 60)
    
    # Validate credentials (allow DRY_RUN without WP password)
    if not WP_APP_PASSWORD and not DRY_RUN:
        logger.error("WP_APP_PASSWORD not set")
        sys.exit(1)
    
    if not JSEARCH_API_KEY:
        logger.error("JSEARCH_API_KEY not set")
        sys.exit(1)
    
    # Load posted jobs
    posted_jobs = load_posted_jobs()
    logger.info(f"Loaded {len(posted_jobs)} previously posted jobs")
    
    # Fetch jobs from JSearch API
    logger.info("\n" + "=" * 60)
    logger.info("Fetching jobs from JSearch API...")
    logger.info("=" * 60)
    
    all_jobs = fetch_jsearch_jobs()
    logger.info(f"\nTotal jobs fetched: {len(all_jobs)}")
    
    # Deduplicate and post
    new_posted = 0
    skipped = 0
    
    for job in all_jobs:
        job_id = generate_job_id(job)
        
        if job_id in posted_jobs:
            skipped += 1
            continue
        
        # Post to WordPress
        if post_job_to_wordpress(job):
            posted_jobs.add(job_id)
            new_posted += 1
            time.sleep(2)  # Rate limit for WordPress API
    
    # Save updated posted jobs
    save_posted_jobs(posted_jobs)
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SCRAPING COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total jobs fetched: {len(all_jobs)}")
    logger.info(f"New jobs posted: {new_posted}")
    logger.info(f"Duplicates skipped: {skipped}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
