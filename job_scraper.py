#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TechJobs360 FREE Job Scraper -> WordPress
100% FREE - No Paid APIs!

Sources:
- JSearch API (FREE tier from RapidAPI)
  Fetches from: LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google for Jobs
  - Arbeitnow API (FREE - No API Key Required!)
   Covers: Jobs in Europe and Remote positions

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


def detect_continent_region(location: str) -> str:
    """Detect continent region from job location"""
    if not location:
        return 'remote-global'
    
    location_lower = location.lower()
    
    # Country to continent mapping
    europe_keywords = ['germany', 'deutschland', 'berlin', 'munich', 'hamburg', 'frankfurt', 
                       'uk', 'united kingdom', 'london', 'france', 'paris', 'netherlands', 
                       'amsterdam', 'switzerland', 'zurich', 'spain', 'italy', 'sweden', 
                       'norway', 'denmark', 'poland', 'austria', 'belgium', 'ireland']
    
    north_america_keywords = ['usa', 'united states', 'america', 'canada', 'mexico', 
                              'san francisco', 'new york', 'los angeles', 'chicago', 
                              'toronto', 'vancouver', 'seattle', 'austin', 'boston']
    
    asia_pacific_keywords = ['india', 'singapore', 'australia', 'japan', 'china', 'korea', 
                            'tokyo', 'sydney', 'melbourne', 'bangalore', 'mumbai', 
                            'new zealand', 'indonesia', 'thailand', 'vietnam', 'philippines']
    
    middle_east_africa_keywords = ['uae', 'dubai', 'saudi arabia', 'israel', 'egypt', 
                                   'south africa', 'kenya', 'nigeria', 'qatar', 'bahrain']
    
    latin_america_keywords = ['brazil', 'mexico', 'argentina', 'chile', 'colombia', 
                             'peru', 'buenos aires', 'sao paulo', 'rio de janeiro']
    
    # Check for remote jobs
    if 'remote' in location_lower or 'anywhere' in location_lower or 'worldwide' in location_lower:
        return 'remote-global'
    
    # Check each region
    for keyword in europe_keywords:
        if keyword in location_lower:
            return 'europe'
    
    for keyword in north_america_keywords:
        if keyword in location_lower:
            return 'north-america'
    
    for keyword in asia_pacific_keywords:
        if keyword in location_lower:
            return 'asia-pacific'
    
    for keyword in middle_east_africa_keywords:
        if keyword in location_lower:
            return 'middle-east-africa'
    
    for keyword in latin_america_keywords:
        if keyword in location_lower:
            return 'latin-america'
    
    # Default to Europe since most current jobs are from Germany
    return 'europe'


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



def fetch_arbeitnow_jobs() -> List[Dict]:
    """
    Fetch jobs from Arbeitnow API (FREE - No API Key Required!)
    Covers: Jobs in Europe and Remote positions
    """
    logger.info("Fetching Arbeitnow jobs (no API key needed)")
    
    jobs = []
    
    # Job categories to search
    search_tags = [
        "software%20engineer",
        "data%20scientist",
        "product%20manager",
        "full%20stack%20developer",
        "devops%20engineer"
    ]
    
    for tag in search_tags:
        try:
            url = f"https://www.arbeitnow.com/api/job-board-api?search={tag}&page=1"
            logger.info(f"Fetching Arbeitnow jobs for: {tag.replace('%20', ' ')}")
            
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except Exception:
                    logger.error(f"Failed to parse JSON from Arbeitnow response for '{tag}'")
                    continue
                
                job_results = data.get('data', [])
                logger.info(f"Found {len(job_results)} jobs for '{tag.replace('%20', ' ')}'")
                
                for job in job_results:
                    # Extract and normalize job data
                    normalized_job = {
                        'job_title': job.get('title', 'Not specified'),
                        'employer_name': job.get('company_name', 'Not specified'),
                        'employer_logo': job.get('company_logo', ''),
                        'job_city': job.get('location', ''),
                        'job_state': '',
                        'job_country': '',
                        'job_description': job.get('description', ''),
                        'job_apply_link': job.get('url', ''),
                        'job_posted_at_datetime_utc': job.get('created_at', ''),
                        'source': 'Arbeitnow API',
                        'job_employment_type': job.get('job_types', ['FULLTIME'])[0] if job.get('job_types') else 'FULLTIME',
                        'job_is_remote': job.get('remote', False),
                    }
                    
                    jobs.append(normalized_job)
                
                # Respect rate limits
                time.sleep(1)
                
            else:
                logger.warning(f"Arbeitnow API error for '{tag}': {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error fetching Arbeitnow jobs for '{tag}': {e}")
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



def delete_old_jobs(days_old: int = 14) -> int:
    """Delete jobs older than specified days from WordPress"""
    if DRY_RUN:
        logger.info(f"DRY_RUN: would delete jobs older than {days_old} days")
        return 0
    
    try:
        deleted_count = 0
        page = 1
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_old)
        logger.info(f"Deleting jobs posted before: {cutoff_date.strftime('%Y-%m-%d')}")
        
        while True:
            # Get all published jobs
            wp_jobs_url = f"{WP_BASE_URL}/wp-json/wp/v2/job_listing"
            params = {
                'per_page': 100,
                'page': page,
                'status': 'publish'
            }
            
            response = session.get(
                wp_jobs_url,
                params=params,
                auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch jobs: {response.status_code}")
                break
            
            jobs = response.json()
            if not jobs:
                break
            
            for job in jobs:
                job_date_str = job.get('date', '')
                if not job_date_str:
                    continue
                
                try:
                    # Parse WordPress date format
                    job_date = datetime.strptime(job_date_str, '%Y-%m-%dT%H:%M:%S')
                    
                    if job_date < cutoff_date:
                        # Delete this job
                        job_id = job['id']
                        delete_url = f"{WP_BASE_URL}/wp-json/wp/v2/job_listing/{job_id}"
                        delete_response = session.delete(
                            delete_url,
                            auth=HTTPBasicAuth(WP_USER, WP_APP_PASSWORD),
                            timeout=30
                        )
                        
                        if delete_response.status_code in (200, 204):
                            deleted_count += 1
                            logger.info(f"Deleted old job: {job.get('title', {}).get('rendered', 'Unknown')} (ID: {job_id})")
                        else:
                            logger.error(f"Failed to delete job {job_id}: {delete_response.status_code}")
                
                except Exception as e:
                    logger.error(f"Error processing job date: {e}")
            
            page += 1
        
        logger.info(f"Total old jobs deleted: {deleted_count}")
        return deleted_count
    
    except Exception as e:
        logger.error(f"Error deleting old jobs: {e}")
        return 0


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
        

    # Detect continent region from location
    region_slug = detect_continent_region(location)
    
    # Get region term ID from WordPress (we'll create a mapping dict for efficiency)
    region_term_map = {
        'europe': None,
        'north-america': None,
        'asia-pacific': None,
        'middle-east-africa': None,
        'latin-america': None,
        'remote-global': None
    }
    
    # Fetch region term ID from WordPress REST API
    region_term_id = None
    try:
        region_url = f"{WP_BASE_URL}/wp-json/wp/v2/job_listing_region?slug={region_slug}"
        region_response = session.get(region_url, timeout=10)
        if region_response.status_code == 200 and region_response.json():
            region_term_id = region_response.json()[0]['id']
            logger.info(f"Found region '{region_slug}' with ID: {region_term_id}")
    except Exception as e:
        logger.warning(f"Could not fetch region term ID for '{region_slug}': {e}")

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
            ,
        'job_listing_region': [region_term_id] if region_term_id else []    '_posted_date': job.get('job_posted_at_datetime_utc', '')
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
    logger.info("TechJobs360 FREE Job Scraper - MULTIPLE FREE APIs")
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

      # Delete old jobs (older than 2 weeks))
    logger.info("\n" + "=" * 60)
    logger.info("Deleting old jobs...")
    logger.info("=" * 60)
    deleted_count = delete_old_jobs(days_old=14)
    
        # Fetch jobs from MULTIPLE FREE APIs
    logger.info("\n" + "=" * 60)
    logger.info("Fetching jobs from JSearch API...")
    logger.info("=" * 60)
    jsearch_jobs = fetch_jsearch_jobs()
    logger.info(f"JSearch API returned: {len(jsearch_jobs)} jobs")    
    logger.info("\n" + "=" * 60)
    logger.info("Fetching jobs from Arbeitnow API (No API Key!)...")
    logger.info("=" * 60)
    arbeitnow_jobs = fetch_arbeitnow_jobs()
    logger.info(f"Arbeitnow API returned: {len(arbeitnow_jobs)} jobs")
    
    # Combine all jobs from different sources
    all_jobs = jsearch_jobs + arbeitnow_jobs
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
