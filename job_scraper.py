#!/usr/bin/env python3
"""
job_scraper.py
TechJobs360 FREE Scraper

Features:
- Load config.yaml to control regions & queries
- Query JSearch (if API key provided) or fallback to custom scrapers
- Deduplicate using posted_jobs.json
- Upload company logos to WordPress media (Clearbit fallback)
- Post job as WordPress post via REST API (with app password)
"""

import os
import sys
import json
import time
import logging
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import requests
import yaml
from slugify import slugify
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from tqdm import tqdm

# --- config
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DEDUP_PATH = BASE_DIR / "posted_jobs.json"

WP_URL = os.environ.get("WP_URL")  # must be set in workflow secrets
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")
JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY")

# timeouts & headers
REQUESTS_TIMEOUT = 20
USER_AGENT = "TechJobs360Scraper/1.0 (+https://techjobs360.com)"

# logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("techjobs360")

# --- helpers
def load_config() -> Dict:
    if not CONFIG_PATH.exists():
        logger.error("Missing config.yaml; create one from the example.")
        sys.exit(2)
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def load_dedup() -> List[Dict]:
    if not DEDUP_PATH.exists():
        return []
    with open(DEDUP_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)

def save_dedup(entries: List[Dict]):
    with open(DEDUP_PATH, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)

def hash_job(job: Dict) -> str:
    # create a stable hash for dedup: prefer job_id/url/title+company+location
    key = job.get("id") or job.get("url") or f"{job.get('title','')}{job.get('company','')}{job.get('location','')}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()

def is_duplicate(job_hash: str, dedup_list: List[Dict]) -> bool:
    return any(e.get("hash") == job_hash for e in dedup_list)

def append_to_dedup(job_hash: str, job: Dict, dedup_list: List[Dict]):
    dedup_list.append({
        "hash": job_hash,
        "title": job.get("title"),
        "company": job.get("company"),
        "location": job.get("location"),
        "url": job.get("url"),
        "first_seen": int(time.time())
    })

# --- JSearch integration (example)
def query_jsearch(query: str, location: Optional[str] = None, page: int = 1, per_page: int = 10) -> List[Dict]:
    """
    Query the JSearch API (if you have JSEARCH_API_KEY).
    This is example code — adapt to the actual JSearch / provider response format.
    """
    if not JSEARCH_API_KEY:
        logger.debug("JSEARCH_API_KEY not provided; skipping jsearch.")
        return []

    url = "https://jsearch.p.rapidapi.com/search"  # adapt if needed
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "User-Agent": USER_AGENT
    }
    payload = {
        "query": query,
        "num_pages": 1,
        "page": page,
        "location": location or ""
    }

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=REQUESTS_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        # Adapt parsing: assume data['data'] is a list of jobs
        jobs = []
        for item in data.get("data", []):
            job = {
                "id": item.get("job_id") or item.get("id"),
                "title": item.get("job_title") or item.get("title"),
                "company": item.get("employer_name") or item.get("company"),
                "location": item.get("job_city") or item.get("location"),
                "description": item.get("job_description") or item.get("description") or "",
                "url": item.get("job_apply_link") or item.get("apply_link") or item.get("url"),
                "posted_at": item.get("job_posted_at") or item.get("posted_at"),
                "raw": item
            }
            jobs.append(job)
        return jobs
    except Exception as e:
        logger.warning("JSearch API error: %s", e)
        return []

# --- fallback generic HTML parser (placeholder)
def parse_jobs_from_html(url: str) -> List[Dict]:
    """
    Placeholder for custom HTML scrapers for sites that don't have an API.
    Implement site-specific parsers (Indeed, StackOverflow Jobs, etc.) as needed.
    """
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUESTS_TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        # Example: find job blocks (this needs to be replaced with site-specific logic)
        jobs = []
        for job_el in soup.select(".job, .result, .job-card")[:10]:
            title_el = job_el.select_one(".job-title, .title, h2")
            company_el = job_el.select_one(".company, .company-name")
            location_el = job_el.select_one(".location, .place")
            link_el = job_el.select_one("a")
            if not title_el or not link_el:
                continue
            job = {
                "id": None,
                "title": title_el.get_text(strip=True),
                "company": company_el.get_text(strip=True) if company_el else "",
                "location": location_el.get_text(strip=True) if location_el else "",
                "description": "",
                "url": requests.compat.urljoin(url, link_el.get("href")),
            }
            jobs.append(job)
        return jobs
    except Exception as e:
        logger.warning("HTML parse error for %s : %s", url, e)
        return []

# --- company logo fetcher
def fetch_company_logo_by_domain(domain: str) -> Optional[bytes]:
    """
    Try Clearbit logo first (logo.clearbit.com) which is simple:
    https://logo.clearbit.com/{domain}
    Returns raw image bytes or None.
    """
    if not domain:
        return None
    try:
        url = f"https://logo.clearbit.com/{domain}"
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=REQUESTS_TIMEOUT, stream=True)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            return r.content
    except Exception:
        pass
    return None

def guess_domain_from_company(company_name: str) -> Optional[str]:
    # naive domain guess: slug + .com — fallback; ideally enrich via external service
    if not company_name:
        return None
    guess = slugify(company_name).replace("-", "")
    if not guess:
        return None
    return f"{guess}.com"

# --- upload media to WordPress
def wp_auth():
    if not all([WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
        logger.error("WP_URL, WP_USERNAME and WP_APP_PASSWORD environment variables are required to post to WordPress.")
        return None
    return (WP_USERNAME, WP_APP_PASSWORD)

def upload_logo_to_wp(image_bytes: bytes, filename: str) -> Optional[int]:
    """
    Upload image_bytes to WP media. Returns attachment ID or None.
    """
    creds = wp_auth()
    if not creds:
        return None
    media_endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/media"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "User-Agent": USER_AGENT
    }
    try:
        resp = requests.post(media_endpoint, auth=creds, data=image_bytes, headers=headers, timeout=REQUESTS_TIMEOUT)
        resp.raise_for_status()
        info = resp.json()
        return info.get("id")
    except Exception as e:
        logger.warning("Failed to upload media: %s", e)
        return None

def post_job_to_wp(job: Dict) -> Optional[int]:
    """
    Post job to WordPress; returns post id on success.
    """
    creds = wp_auth()
    if not creds:
        return None

    post_endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/posts"
    title = job.get("title") or "Untitled job"
    content = job.get("description") or ""
    company = job.get("company", "")
    location = job.get("location", "")
    apply_url = job.get("url", "")
    slug = slugify(f"{title}-{company}-{location}")[:200]

    # prepare content (simple HTML)
    html_content = f"<p><strong>Company:</strong> {company}</p>"
    html_content += f"<p><strong>Location:</strong> {location}</p>"
    if apply_url:
        html_content += f'<p><strong>Apply:</strong> <a href="{apply_url}" target="_blank" rel="noopener">{apply_url}</a></p>'
    html_content += "<hr/>"
    html_content += content

    payload = {
        "title": title,
        "content": html_content,
        "status": "publish",
        "slug": slug,
        "format": "standard"
    }

    # set author / categories / tags from config if present
    try:
        config = load_config()
        posting = config.get("posting", {})
        payload["status"] = posting.get("post_status", "publish")
        if posting.get("default_author_id"):
            payload["author"] = posting["default_author_id"]
        if posting.get("categories"):
            # categories should be numeric WP term IDs; here we accept strings and omit if missing
            # better: map names to IDs via WP REST - omitted for brevity
            pass
    except Exception:
        pass

    try:
        resp = requests.post(post_endpoint, json=payload, auth=creds, headers={"User-Agent": USER_AGENT}, timeout=REQUESTS_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        post_id = data.get("id")
        logger.info("Posted job to WP: %s (id=%s)", title, post_id)
        # attach featured media if present in job (returned via upload_logo_to_wp)
        if job.get("_featured_media_id") and post_id:
            patch_url = f"{post_endpoint}/{post_id}"
            requests.post(patch_url, json={"featured_media": job["_featured_media_id"]}, auth=creds, headers={"User-Agent": USER_AGENT}, timeout=REQUESTS_TIMEOUT)
        return post_id
    except Exception as e:
        logger.error("Failed to create WP post: %s", e)
        return None

# --- main orchestration
def main():
    config = load_config()
    dedup_list = load_dedup()
    original_dedup_len = len(dedup_list)
    new_jobs_posted = 0

    regions = config.get("regions", [])
    sources = config.get("sources", [])
    if not regions:
        logger.error("No regions configured in config.yaml.")
        return

    candidate_jobs = []

    # aggregate jobs from sources & regions
    for region in regions:
        for locale in region.get("locales", []):
            query = locale.get("query")
            city = locale.get("city")
            qtext = f"{query} {city}" if city else query or ""
            logger.info("Searching for: %s (region: %s)", qtext, region.get("id"))
            # Query each enabled source in order
            for source in sources:
                if not source.get("enabled", True):
                    continue
                s_type = source.get("type")
                if s_type == "jsearch":
                    jobs = query_jsearch(qtext, location=city, per_page=20)
                    candidate_jobs.extend(jobs)
                elif s_type == "html":
                    endpoint = source.get("endpoint")
                    if endpoint:
                        candidate_jobs.extend(parse_jobs_from_html(endpoint))
                else:
                    logger.debug("Unknown source type: %s", s_type)

    # deduplicate candidate jobs by URL/title/company/location
    for job in tqdm(candidate_jobs, desc="Processing jobs"):
        jhash = hash_job(job)
        if is_duplicate(jhash, dedup_list):
            logger.debug("Skipped duplicate: %s @ %s", job.get("title"), job.get("company"))
            continue

        # fetch logo if possible
        logo_bytes = None
        # try to find domain from job raw data if present
        domain = None
        raw = job.get("raw") or {}
        domain = raw.get("company_website") or raw.get("company_domain") or raw.get("domain")
        if not domain:
            domain = guess_domain_from_company(job.get("company", ""))
        if domain:
            logo_bytes = fetch_company_logo_by_domain(domain)

        if logo_bytes:
            # try to resize to a reasonable max size
            try:
                img = Image.open(BytesIO(logo_bytes))
                img.thumbnail((600, 600))
                out = BytesIO()
                img_format = img.format if img.format else "PNG"
                img.save(out, format=img_format)
                out_bytes = out.getvalue()
                filename = f"{slugify(job.get('company') or 'company')}-{jhash[:8]}.{img_format.lower()}"
                media_id = upload_logo_to_wp(out_bytes, filename)
                if media_id:
                    job["_featured_media_id"] = media_id
            except Exception as e:
                logger.debug("Logo processing error: %s", e)

        # post to WP
        post_id = post_job_to_wp(job)
        if post_id:
            new_jobs_posted += 1
            append_to_dedup(jhash, job, dedup_list)
        else:
            logger.warning("Failed to post job: %s", job.get("title"))

    # save dedup only if changed
    if len(dedup_list) != original_dedup_len:
        save_dedup(dedup_list)
        logger.info("Saved dedup file with %d entries.", len(dedup_list))
    else:
        logger.info("No dedup changes; not saving file.")

    logger.info("Run complete. New jobs posted: %d", new_jobs_posted)

if __name__ == "__main__":
    main()
