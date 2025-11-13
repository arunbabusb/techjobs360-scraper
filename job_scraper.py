#!/usr/bin/env python3
# TechJobs360 Global Job Scraper - FINAL VERSION (Fully Working)

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

# --------------------------
# PATHS & ENV
# --------------------------
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DEDUP_PATH = BASE_DIR / "posted_jobs.json"

WP_URL = os.environ.get("WP_URL")
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")
JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY")
PROCESS_CONTINENT = os.environ.get("PROCESS_CONTINENT")

REQUESTS_TIMEOUT = 20
USER_AGENT = "TechJobs360Scraper/2.0 (+https://techjobs360.com)"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("techjobs360")


# --------------------------
# CONFIG + DEDUP
# --------------------------
def load_config() -> Dict:
    if not CONFIG_PATH.exists():
        logger.error("Missing config.yaml. Add it to repo root.")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_dedup() -> List[Dict]:
    """Handles legacy and modern dedup formats."""
    if not DEDUP_PATH.exists():
        return []

    try:
        with open(DEDUP_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception:
        return []

    normalized = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                normalized.append({"hash": item, "first_seen": 0})
            elif isinstance(item, dict):
                h = item.get("hash")
                if not h:
                    h = hashlib.sha1(
                        (item.get("title","") + item.get("company","") + item.get("location","")).encode("utf-8")
                    ).hexdigest()

                normalized.append({
                    "hash": h,
                    "title": item.get("title"),
                    "company": item.get("company"),
                    "location": item.get("location"),
                    "url": item.get("url"),
                    "first_seen": int(item.get("first_seen") or 0)
                })
    return normalized


def prune_dedup(dedup_list: List[Dict], max_days: int) -> List[Dict]:
    if not max_days:
        return dedup_list

    cutoff = int((datetime.utcnow() - timedelta(days=max_days)).timestamp())
    kept = []
    for e in dedup_list:
        fs = int(e.get("first_seen", 0))
        if fs >= cutoff:
            kept.append(e)
    return kept


def save_dedup(dedup: List[Dict]):
    with open(DEDUP_PATH, "w", encoding="utf-8") as fh:
        json.dump(dedup, fh, indent=2)


# --------------------------
# HTTP WITH RETRIES
# --------------------------
def http_request(method, url, **kwargs):
    for attempt in range(4):
        try:
            return requests.request(method, url, timeout=REQUESTS_TIMEOUT, **kwargs)
        except Exception as e:
            if attempt == 3:
                raise
            time.sleep(1 + attempt)


# --------------------------
# JSEARCH — CORRECT VERSION
# --------------------------
def query_jsearch(query: str, location: Optional[str] = None) -> List[Dict]:
    """
    EXACT RapidAPI example format:
    GET https://jsearch.p.rapidapi.com/search?query=<query>&num_pages=1

    Headers:
      X-RapidAPI-Key
      X-RapidAPI-Host
    """

    if not JSEARCH_API_KEY:
        logger.warning("No JSEARCH_API_KEY found.")
        return []

    url = "https://jsearch.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        "User-Agent": USER_AGENT,
        "Accept": "application/json"
    }

    params = {
        "query": f"{query} {location}".strip(),
        "num_pages": 1,
        "page": 1,
        "date_posted": "all"
    }

    try:
        r = http_request("GET", url, headers=headers, params=params)
        if r.status_code != 200:
            logger.warning("JSearch Error %s → %s", r.status_code, r.text[:300])
            return []
        data = r.json()

        jobs = []
        for item in data.get("data", []):
            jobs.append({
                "id": item.get("job_id"),
                "title": item.get("job_title"),
                "company": item.get("employer_name"),
                "location": item.get("job_city"),
                "description": item.get("job_description"),
                "url": item.get("job_apply_link"),
                "raw": item
            })

        return jobs

    except Exception as e:
        logger.warning("JSearch exception: %s", e)
        return []


# --------------------------
# HTML FALLBACK
# --------------------------
def parse_html(endpoint: str, query: str, city: str) -> List[Dict]:
    try:
        url = endpoint.format(
            query=requests.utils.quote(query),
            city=requests.utils.quote(city)
        )
        r = http_request("GET", url, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        jobs = []
        for block in soup.select("a, .job, .card, .posting")[:10]:
            title = block.get_text(strip=True)
            href = block.get("href")
            if href:
                jobs.append({
                    "id": None,
                    "title": title,
                    "company": "",
                    "location": city,
                    "description": "",
                    "url": href
                })
        return jobs

    except:
        return []


# --------------------------
# LOGOS
# --------------------------
def guess_domain(company: str) -> Optional[str]:
    if not company:
        return None
    d = slugify(company).replace("-", "")
    if d:
        return d + ".com"
    return None


def fetch_logo(domain: str) -> Optional[bytes]:
    if not domain:
        return None
    try:
        r = http_request("GET", f"https://logo.clearbit.com/{domain}")
        if r.status_code == 200:
            return r.content
    except:
        return None


def upload_media_to_wp(bytes_data: bytes, filename: str) -> Optional[int]:
    if not WP_URL:
        return None

    endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/media"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    try:
        r = http_request(
            "POST",
            endpoint,
            auth=(WP_USERNAME, WP_APP_PASSWORD),
            headers=headers,
            data=bytes_data
        )
        r.raise_for_status()
        return r.json().get("id")
    except:
        return None


# --------------------------
# POST TO WORDPRESS
# --------------------------
def post_to_wp(job: Dict, continent_id: str, country_code: str, posting_cfg: Dict) -> Optional[int]:
    endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/posts"

    title = job.get("title")
    company = job.get("company")
    location = job.get("location")
    apply_url = job.get("url")

    content = f"<p><strong>Company:</strong> {company}</p>"
    content += f"<p><strong>Location:</strong> {location}</p>"
    if apply_url:
        content += f'<p><a href="{apply_url}" target="_blank">Apply</a></p>'

    slug = slugify(f"{title}-{company}-{location}")[:200]

    payload = {
        "title": title,
        "slug": slug,
        "content": content,
        "status": posting_cfg.get("post_status", "publish")
    }

    try:
        r = http_request(
            "POST",
            endpoint,
            auth=(WP_USERNAME, WP_APP_PASSWORD),
            json=payload
        )
        r.raise_for_status()
        return r.json().get("id")

    except Exception as e:
        logger.error("Error posting to WP: %s", e)
        return None


# --------------------------
# MAIN
# --------------------------
def main():
    config = load_config()
    dedup = load_dedup()

    # prune old
    max_age = int(config.get("dedup", {}).get("max_age_days", 0))
    dedup = prune_dedup(dedup, max_age)

    continents = config.get("continents", [])
    sources = config.get("sources", [])
    posting_cfg = config.get("posting", {})

    if PROCESS_CONTINENT:
        continents = [c for c in continents if c.get("id") == PROCESS_CONTINENT]

    total_new = 0

    for cont in continents:
        cont_id = cont.get("id")
        cont_name = cont.get("name")
        logger.info("=== CONTINENT: %s ===", cont_name)

        for country in cont.get("countries", []):
            country_code = country.get("code")
            country_name = country.get("name")

            for loc in country.get("locales", []):
                city = loc.get("city")
                query = loc.get("query")

                search = f"{query} {city} {country_name}"
                logger.info("Searching: %s", search)

                found_jobs = []

                # sources
                for s in sources:
                    if not s.get("enabled"):
                        continue

                    if s.get("type") == "jsearch":
                        found_jobs += query_jsearch(query, city)

                    elif s.get("type") == "html":
                        endpoint = s.get("endpoint")
                        if endpoint:
                            found_jobs += parse_html(endpoint, query, city)

                # process results
                for job in found_jobs:
                    hkey = (job.get("id") or job.get("url") or job.get("title"))
                    if not hkey:
                        continue

                    jhash = hashlib.sha1(hkey.encode("utf-8")).hexdigest()
                    if any(d["hash"] == jhash for d in dedup):
                        continue

                    # Logo
                    domain = guess_domain(job.get("company"))
                    logo_bytes = fetch_logo(domain)
                    if logo_bytes:
                        filename = f"{slugify(job.get('company') or 'company')}-{jhash[:8]}.png"
                        media_id = upload_media_to_wp(logo_bytes, filename)
                        if media_id:
                            job["_media"] = media_id

                    # Post
                    post_id = post_to_wp(job, cont_id, country_code, posting_cfg)
                    if post_id:
                        total_new += 1
                        dedup.append({
                            "hash": jhash,
                            "title": job.get("title"),
                            "company": job.get("company"),
                            "location": job.get("location"),
                            "url": job.get("url"),
                            "first_seen": int(time.time())
                        })

    save_dedup(dedup)
    logger.info("Run complete. New jobs posted: %d", total_new)


if __name__ == "__main__":
    main()
