#!/usr/bin/env python3
"""
Updated job_scraper.py
- Uses config.yaml (continent → country → locales)
- Per-continent pacing & jitter
- JSearch + generic HTML fallback
- Upload logos to WP, post job with continent + country_code tags
- Dedup with pruning by max_age_days
- Optional PROCESS_CONTINENT env var to only run one continent
"""

import os
import sys
import json
import time
import logging
import hashlib
import random
from pathlib import Path
from typing import Dict, List, Optional
import requests
import yaml
from slugify import slugify
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta

# --- Paths & env
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DEDUP_PATH = BASE_DIR / "posted_jobs.json"

WP_URL = os.environ.get("WP_URL")                  # e.g. https://techjobs360.com
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")
JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY")
PROCESS_CONTINENT = os.environ.get("PROCESS_CONTINENT")  # optional e.g. "asia"

# --- HTTP + logging
REQUESTS_TIMEOUT = 20
USER_AGENT = "TechJobs360Scraper/2.0 (+https://techjobs360.com)"
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("techjobs360")

# --- Helpers
def load_config() -> Dict:
    if not CONFIG_PATH.exists():
        logger.error("Missing config.yaml in repo root. Expected at: %s", CONFIG_PATH)
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

def prune_dedup(dedup_list: List[Dict], max_age_days: int) -> List[Dict]:
    if not max_age_days:
        return dedup_list
    cutoff = int((datetime.utcnow() - timedelta(days=max_age_days)).timestamp())
    kept = [e for e in dedup_list if e.get("first_seen", 0) >= cutoff]
    removed = len(dedup_list) - len(kept)
    if removed:
        logger.info("Pruned %d old dedup entries (older than %d days).", removed, max_age_days)
    return kept

# --- Backoff utility
def requests_with_backoff(method, url, **kwargs):
    max_attempts = 4
    delay = 1
    for attempt in range(1, max_attempts + 1):
        try:
            return requests.request(method, url, timeout=REQUESTS_TIMEOUT, **kwargs)
        except requests.RequestException as e:
            logger.warning("Request error (attempt %d/%d) for %s: %s", attempt, max_attempts, url, e)
            if attempt == max_attempts:
                raise
            time.sleep(delay + random.random())
            delay *= 2
    raise RuntimeError("unreachable")

# --- JSearch integration
def query_jsearch(query: str, location: Optional[str] = None, per_page: int = 20) -> List[Dict]:
    if not JSEARCH_API_KEY:
        return []
    url = "https://jsearch.p.rapidapi.com/search"  # adapt if your JSearch endpoint differs
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json"
    }
    payload = {"query": query, "location": location or "", "num_pages": 1, "page": 1}
    try:
        r = requests_with_backoff("POST", url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        jobs = []
        for item in data.get("data", []):
            jobs.append({
                "id": item.get("job_id") or item.get("id"),
                "title": item.get("job_title") or item.get("title"),
                "company": item.get("employer_name") or item.get("company"),
                "location": item.get("job_city") or item.get("location"),
                "description": item.get("job_description") or item.get("description") or "",
                "url": item.get("job_apply_link") or item.get("apply_link") or item.get("url"),
                "posted_at": item.get("job_posted_at") or item.get("posted_at"),
                "raw": item
            })
        return jobs
    except Exception as e:
        logger.warning("JSearch query failed for '%s' (%s): %s", query, location, e)
        return []

# --- generic HTML parser fallback (very basic)
def parse_jobs_from_html(endpoint: str, query: str = "", city: str = "") -> List[Dict]:
    try:
        url = endpoint.format(query=requests.utils.quote(query or ""), city=requests.utils.quote(city or ""))
        r = requests_with_backoff("GET", url, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        jobs = []
        # site-specific selector required for production — this is only a generic placeholder
        for el in soup.select(".job, .result, .job-card, .posting")[:15]:
            title = el.select_one("h2, .title, .job-title")
            link = el.select_one("a")
            company = el.select_one(".company, .company-name")
            location = el.select_one(".location, .place")
            if not title or not link:
                continue
            jobs.append({
                "id": None,
                "title": title.get_text(strip=True),
                "company": company.get_text(strip=True) if company else "",
                "location": location.get_text(strip=True) if location else city,
                "description": "",
                "url": requests.compat.urljoin(url, link.get("href"))
            })
        return jobs
    except Exception as e:
        logger.warning("HTML parse failed for %s: %s", endpoint, e)
        return []

# --- logo retrieval + WP upload
def fetch_company_logo_by_domain(domain: str) -> Optional[bytes]:
    if not domain:
        return None
    try:
        url = f"https://logo.clearbit.com/{domain}"
        r = requests_with_backoff("GET", url, headers={"User-Agent": USER_AGENT}, stream=True)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            return r.content
    except Exception:
        pass
    return None

def guess_domain_from_company(company_name: str) -> Optional[str]:
    if not company_name:
        return None
    guess = slugify(company_name).replace("-", "")
    if not guess:
        return None
    return f"{guess}.com"

def wp_auth():
    if not all([WP_URL, WP_USERNAME, WP_APP_PASSWORD]):
        return None
    return (WP_USERNAME, WP_APP_PASSWORD)

def upload_logo_to_wp(image_bytes: bytes, filename: str) -> Optional[int]:
    creds = wp_auth()
    if not creds:
        return None
    media_endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/media"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"', "User-Agent": USER_AGENT}
    try:
        r = requests_with_backoff("POST", media_endpoint, auth=creds, data=image_bytes, headers=headers)
        r.raise_for_status()
        return r.json().get("id")
    except Exception as e:
        logger.warning("WP media upload failed: %s", e)
        return None

# --- WordPress posting
def post_job_to_wp(job: Dict, continent_id: str, country_code: str, posting_cfg: Dict) -> Optional[int]:
    creds = wp_auth()
    if not creds:
        logger.error("Missing WP credentials (WP_URL, WP_USERNAME, WP_APP_PASSWORD). Skipping post.")
        return None

    endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/posts"
    title = job.get("title") or "Untitled job"
    content = job.get("description") or ""
    company = job.get("company", "")
    location = job.get("location", "")
    apply_url = job.get("url", "")
    slug = slugify(f"{title}-{company}-{location}")[:200]

    html_content = f"<p><strong>Company:</strong> {company}</p>"
    html_content += f"<p><strong>Location:</strong> {location}</p>"
    if apply_url:
        html_content += f'<p><strong>Apply:</strong> <a href="{apply_url}" target="_blank" rel="noopener">{apply_url}</a></p>'
    html_content += "<hr/>"
    html_content += content

    payload = {
        "title": title,
        "content": html_content,
        "status": posting_cfg.get("post_status", "publish"),
        "slug": slug,
        "format": "standard"
    }

    # Add tags to help filtering by continent/country (WordPress terms must exist or be created separately)
    # Here we add a simple tag array (names). If your WP maps tags -> IDs differently, adapt accordingly.
    tags = posting_cfg.get("tags", [])[:]
    tags.append(f"continent:{continent_id}")
    if country_code:
        tags.append(f"country:{country_code}")
    if posting_cfg.get("default_country_taxonomy") and country_code:
        tags.append(country_code)

    # Some WP setups require numeric tag IDs; this code sends tag names to default WP endpoint,
    # WordPress will create tags automatically if your WP allows it.

    payload["tags"] = tags

    # Featured media (if uploaded earlier)
    if job.get("_featured_media_id"):
        payload["featured_media"] = job.get("_featured_media_id")

    try:
        r = requests_with_backoff("POST", endpoint, json=payload, auth=creds, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        post_id = r.json().get("id")
        logger.info("Posted job: %s (post id=%s)", title, post_id)
        return post_id
    except Exception as e:
        logger.error("Failed to post job to WP: %s", e)
        return None

# --- main orchestrator
def main():
    config = load_config()
    dedup_list = load_dedup()
    posting_cfg = config.get("posting", {})
    dedup_cfg = config.get("dedup", {})
    max_age_days = int(dedup_cfg.get("max_age_days") or 0)
    dedup_list = prune_dedup(dedup_list, max_age_days)
    original_len = len(dedup_list)

    continents = config.get("continents", [])
    sources = config.get("sources", [])
    global_defaults = config.get("global", {})

    # Optionally process only one continent (use env var PROCESS_CONTINENT)
    if PROCESS_CONTINENT:
        continents = [c for c in continents if c.get("id") == PROCESS_CONTINENT]
        if not continents:
            logger.warning("PROCESS_CONTINENT set to '%s' but no matching continent id found in config.yaml", PROCESS_CONTINENT)
            return

    total_new = 0
    for cont in continents:
        cont_id = cont.get("id")
        cont_name = cont.get("name")
        logger.info("Processing continent: %s (%s)", cont_name, cont_id)

        # Per-continent pacing: read optional override or use defaults
        per_continent_pause = cont.get("pause_seconds", 2)  # base wait between requests for this continent
        if per_continent_pause < 0:
            per_continent_pause = 2

        countries = cont.get("countries", [])
        for country in countries:
            country_code = country.get("code")
            country_name = country.get("name")
            locales = country.get("locales", [])
            for locale in locales:
                city = locale.get("city")
                query = locale.get("query")
                qtext = " ".join([s for s in [query, city, country_name] if s])
                logger.info("Searching: '%s' (continent=%s country=%s)", qtext, cont_id, country_code)

                # iterate sources in order
                candidate_jobs = []
                for source in sources:
                    if not source.get("enabled", True):
                        continue
                    s_type = source.get("type")
                    if s_type == "jsearch":
                        candidate_jobs.extend(query_jsearch(qtext, location=city or country_name, per_page=global_defaults.get("default_per_page", 20)))
                    elif s_type == "html":
                        endpoint = source.get("endpoint")
                        if endpoint:
                            candidate_jobs.extend(parse_jobs_from_html(endpoint, query=query, city=city))
                    else:
                        logger.debug("Unknown source type: %s", s_type)

                    # small polite pause after each source request for this locale
                    sleep_time = per_continent_pause + random.random() * per_continent_pause
                    logger.debug("Sleeping %.2fs after source call", sleep_time)
                    time.sleep(sleep_time)

                # process candidate jobs
                for job in candidate_jobs:
                    jhash = hash_job(job)
                    if is_duplicate(jhash, dedup_list):
                        logger.debug("Duplicate job skipped: %s @ %s", job.get("title"), job.get("company"))
                        continue

                    # attempt logo fetch + upload
                    domain = None
                    raw = job.get("raw") or {}
                    domain = raw.get("company_website") or raw.get("company_domain") or raw.get("domain")
                    if not domain:
                        domain = guess_domain_from_company(job.get("company", ""))

                    logo_bytes = None
                    if domain:
                        logo_bytes = fetch_company_logo_by_domain(domain)

                    if logo_bytes:
                        try:
                            img = Image.open(BytesIO(logo_bytes))
                            img.thumbnail((600, 600))
                            out = BytesIO()
                            fmt = img.format if img.format else "PNG"
                            img.save(out, format=fmt)
                            filename = f"{slugify(job.get('company') or 'company')}-{jhash[:8]}.{fmt.lower()}"
                            media_id = upload_logo_to_wp(out.getvalue(), filename)
                            if media_id:
                                job["_featured_media_id"] = media_id
                        except Exception as e:
                            logger.debug("Logo handling error: %s", e)

                    # post to WP
                    post_id = post_job_to_wp(job, cont_id, country_code, posting_cfg)
                    if post_id:
                        total_new += 1
                        append_to_dedup(jhash, job, dedup_list)
                    else:
                        logger.warning("Failed to post job: %s", job.get("title"))

                # small pause between locales
                time.sleep(per_continent_pause + random.random() * per_continent_pause)

    # persist dedup if changed
    if len(dedup_list) != original_len:
        save_dedup(dedup_list)
        logger.info("Saved dedup file with %d entries.", len(dedup_list))
    else:
        logger.info("No changes to dedup file.")

    logger.info("Completed run. New jobs posted: %d", total_new)


if __name__ == "__main__":
    main()
