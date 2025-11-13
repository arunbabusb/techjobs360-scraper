#!/usr/bin/env python3
"""
TechJobs360 Global Job Scraper v2
--------------------------------
Features:
- Reads config.yaml (continents → countries → cities)
- JSearch API + optional HTML fallback
- Dedup with legacy compatibility
- Logo fetch via Clearbit
- Uploads logo to WordPress Media
- Posts job to WordPress with continent + country tags
- Supports PROCESS_CONTINENT for slicing workload
- Safe backoff & retries
- Dedup pruning (max_age_days)
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

# Paths
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DEDUP_PATH = BASE_DIR / "posted_jobs.json"

# Env vars
WP_URL = os.environ.get("WP_URL")
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")
JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY")
PROCESS_CONTINENT = os.environ.get("PROCESS_CONTINENT")

# HTTP settings
REQUESTS_TIMEOUT = 20
USER_AGENT = "TechJobs360Scraper/2.0 (+https://techjobs360.com)"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("techjobs360")


# ----------------------
# CONFIG & DEDUP LOADING
# ----------------------

def load_config() -> Dict:
    if not CONFIG_PATH.exists():
        logger.error("config.yaml missing in repo root!")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_dedup() -> List[Dict]:
    """
    Supports 2 formats:
    1. Legacy: ["hash1", "hash2"]
    2. Modern: [{"hash": "...", "first_seen": ...}, ...]
    """
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
            # Legacy string-only hash list
            if isinstance(item, str):
                normalized.append({"hash": item, "first_seen": 0})
            # Normal dict form
            elif isinstance(item, dict):
                h = item.get("hash")
                if not h:
                    # fallback to hash of title+company+location
                    h = hashlib.sha1(
                        (item.get("title", "") +
                         item.get("company", "") +
                         item.get("location", "")
                         ).encode("utf-8")
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


def prune_dedup(dedup_list: List[Dict], max_age_days: int) -> List[Dict]:
    if not max_age_days:
        return dedup_list

    cutoff = int((datetime.utcnow() - timedelta(days=max_age_days)).timestamp())
    kept = []
    removed = 0

    for e in dedup_list:
        if isinstance(e, dict):
            fs = int(e.get("first_seen", 0))
            if fs >= cutoff:
                kept.append(e)
            else:
                removed += 1
        else:
            removed += 1

    if removed:
        logger.info("Pruned %d old entries", removed)
    return kept


def save_dedup(entries: List[Dict]):
    with open(DEDUP_PATH, "w", encoding="utf-8") as fh:
        json.dump(entries, fh, indent=2, ensure_ascii=False)


# ----------------------
# HTTP + RETRIES
# ----------------------

def http_request(method, url, **kwargs):
    max_attempts = 4
    delay = 1
    for attempt in range(1, max_attempts + 1):
        try:
            return requests.request(method, url, timeout=REQUESTS_TIMEOUT, **kwargs)
        except Exception as e:
            if attempt == max_attempts:
                raise
            logger.warning("Retrying %s %s (%s)...", method, url, e)
            time.sleep(delay + random.random())
            delay *= 2


# ----------------------
# JSEARCH API
# ----------------------

def query_jsearch(query: str, location: str = "") -> List[Dict]:
    if not JSEARCH_API_KEY:
        return []

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "location": location,
        "page": 1,
        "num_pages": 1
    }

    try:
        r = http_request("POST", url, json=payload, headers=headers)
        r.raise_for_status()
        data = r.json()
        jobs = []
        for j in data.get("data", []):
            jobs.append({
                "id": j.get("job_id") or j.get("id"),
                "title": j.get("job_title"),
                "company": j.get("employer_name"),
                "location": j.get("job_city") or location,
                "description": j.get("job_description") or "",
                "url": j.get("job_apply_link"),
                "raw": j
            })
        return jobs
    except Exception as e:
        logger.warning("JSearch failed: %s", e)
        return []


# ----------------------
# GENERIC HTML FALLBACK
# ----------------------

def parse_html(endpoint: str, query: str, city: str) -> List[Dict]:
    try:
        url = endpoint.format(
            query=requests.utils.quote(query or ""),
            city=requests.utils.quote(city or "")
        )
        r = http_request("GET", url, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        jobs = []
        for el in soup.select(".job, .result, .job-card, .posting")[:10]:
            title = el.select_one(".title, h2")
            link = el.select_one("a")
            if not title or not link:
                continue

            company = el.select_one(".company")
            location = el.select_one(".location")
            jobs.append({
                "id": None,
                "title": title.get_text(strip=True),
                "company": company.get_text(strip=True) if company else "",
                "location": location.get_text(strip=True) if location else city,
                "description": "",
                "url": link.get("href")
            })
        return jobs

    except Exception as e:
        logger.warning("HTML parser failed: %s", e)
        return []


# ----------------------
# LOGO FETCH + WP UPLOAD
# ----------------------

def guess_domain(company: str) -> Optional[str]:
    if not company:
        return None
    slug = slugify(company).replace("-", "")
    if not slug:
        return None
    return slug + ".com"


def fetch_logo(domain: str):
    if not domain:
        return None
    try:
        url = f"https://logo.clearbit.com/{domain}"
        r = http_request("GET", url, stream=True)
        if r.status_code == 200 and "image" in r.headers.get("content-type", ""):
            return r.content
    except:
        pass
    return None


def wp_media_upload(image_bytes: bytes, filename: str) -> Optional[int]:
    if not (WP_URL and WP_USERNAME and WP_APP_PASSWORD):
        return None

    url = WP_URL.rstrip("/") + "/wp-json/wp/v2/media"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "User-Agent": USER_AGENT
    }

    try:
        r = http_request("POST", url, auth=(WP_USERNAME, WP_APP_PASSWORD),
                         data=image_bytes, headers=headers)
        r.raise_for_status()
        return r.json().get("id")
    except Exception as e:
        logger.warning("WP media upload failed: %s", e)
        return None


# ----------------------
# WP POSTING
# ----------------------

def post_to_wp(job: Dict, continent_id: str, country_code: str, posting_cfg: Dict) -> Optional[int]:
    if not (WP_URL and WP_USERNAME and WP_APP_PASSWORD):
        logger.error("Missing WP credentials!")
        return None

    endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/posts"

    title = job.get("title")
    company = job.get("company")
    location = job.get("location")
    url = job.get("url")
    slug = slugify(f"{title}-{company}-{location}")[:200]

    html = f"<p><strong>Company:</strong> {company}</p>"
    html += f"<p><strong>Location:</strong> {location}</p>"
    if url:
        html += f'<p><a href="{url}" target="_blank">Apply Here</a></p>'
    html += "<hr/>" + (job.get("description") or "")

    tags = posting_cfg.get("tags", []).copy()
    tags.append(f"continent:{continent_id}")
    tags.append(f"country:{country_code}")

    payload = {
        "title": title,
        "slug": slug,
        "content": html,
        "status": posting_cfg.get("post_status", "publish"),
        "tags": tags
    }

    if job.get("_media"):
        payload["featured_media"] = job["_media"]

    try:
        r = http_request("POST", endpoint, json=payload,
                         auth=(WP_USERNAME, WP_APP_PASSWORD),
                         headers={"User-Agent": USER_AGENT})

        r.raise_for_status()
        return r.json().get("id")
    except Exception as e:
        logger.error("WP posting failed: %s", e)
        return None


# ----------------------
# MAIN SCRAPER
# ----------------------

def main():
    config = load_config()
    dedup = load_dedup()

    dedup_cfg = config.get("dedup", {})
    max_age = int(dedup_cfg.get("max_age_days") or 0)
    dedup = prune_dedup(dedup, max_age)
    orig_len = len(dedup)

    continents = config.get("continents", [])
    sources = config.get("sources", [])
    posting_cfg = config.get("posting", {})

    # Allow filtering by continent
    if PROCESS_CONTINENT:
        continents = [c for c in continents if c.get("id") == PROCESS_CONTINENT]

    total_new = 0

    for cont in continents:
        cont_id = cont.get("id")
        cont_name = cont.get("name")
        logger.info("== Continent: %s (%s) ==", cont_name, cont_id)

        for country in cont.get("countries", []):
            country_code = country.get("code")
            country_name = country.get("name")

            for loc in country.get("locales", []):
                city = loc.get("city")
                query = loc.get("query")
                search_text = f"{query} {city} {country_name}".strip()

                logger.info("Searching: %s", search_text)
                found_jobs = []

                # loop through sources
                for s in sources:
                    if not s.get("enabled", True):
                        continue

                    if s.get("type") == "jsearch":
                        found_jobs += query_jsearch(search_text, city)
                    elif s.get("type") == "html":
                        endpoint = s.get("endpoint")
                        if endpoint:
                            found_jobs += parse_html(endpoint, query, city)

                    time.sleep(1 + random.random())  # polite pause

                # process jobs
                for job in found_jobs:
                    jhash = hashlib.sha1(
                        (job.get("id") or job.get("url") or job.get("title")).encode("utf-8")
                    ).hexdigest()

                    if any(e["hash"] == jhash for e in dedup):
                        continue

                    # logo attempt
                    domain = None
                    raw = job.get("raw") or {}
                    domain = raw.get("company_domain") or guess_domain(job.get("company"))

                    logo_bytes = fetch_logo(domain) if domain else None
                    if logo_bytes:
                        try:
                            img = Image.open(BytesIO(logo_bytes))
                            img.thumbnail((600, 600))
                            out = BytesIO()
                            fmt = img.format or "PNG"
                            img.save(out, format=fmt)
                            fname = f"{slugify(job.get('company') or 'company')}-{jhash[:8]}.{fmt.lower()}"
                            media_id = wp_media_upload(out.getvalue(), fname)
                            if media_id:
                                job["_media"] = media_id
                        except:
                            pass

                    post_id = post_to_wp(job, cont_id, country_code, posting_cfg)
                    if post_id:
                        dedup.append({
                            "hash": jhash,
                            "title": job.get("title"),
                            "company": job.get("company"),
                            "location": job.get("location"),
                            "url": job.get("url"),
                            "first_seen": int(time.time())
                        })
                        total_new += 1

    # Save dedup if changed
    if len(dedup) != orig_len:
        save_dedup(dedup)
        logger.info("Saved updated dedup list (%d entries)", len(dedup))

    logger.info("Run complete. New jobs posted: %d", total_new)


if __name__ == "__main__":
    main()
