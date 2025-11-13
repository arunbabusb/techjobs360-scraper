#!/usr/bin/env python3
"""
TechJobs360 Global Job Scraper - Combined (RapidAPI + Free Sources)

- Supports: JSearch (RapidAPI), Remotive, RemoteOK, WeWorkRemotely (HTML)
- Dedup (legacy + modern), pruning, WP posting, logo upload (Clearbit)
- Config-driven via config.yaml (continents, sources, posting, dedup)
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

# ---------- Paths & env ----------
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DEDUP_PATH = BASE_DIR / "posted_jobs.json"

WP_URL = os.environ.get("WP_URL")
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")
JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY")
PROCESS_CONTINENT = os.environ.get("PROCESS_CONTINENT")
AUTO_ROTATE = os.environ.get("AUTO_ROTATE", "").lower() in ("1", "true", "yes")

REQUESTS_TIMEOUT = 20
USER_AGENT = "TechJobs360Scraper/combined (+https://techjobs360.com)"

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("techjobs360")

# -----------------------
# Config & dedup helpers
# -----------------------
def load_config() -> Dict:
    if not CONFIG_PATH.exists():
        logger.error("Missing config.yaml in repo root. Create one and try again.")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}

def load_dedup() -> List[Dict]:
    """Normalize posted_jobs.json (legacy list of hashes or list of dicts)."""
    if not DEDUP_PATH.exists():
        return []
    try:
        with open(DEDUP_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        logger.warning("Could not read dedup file: %s", e)
        return []
    normalized = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                normalized.append({"hash": item, "first_seen": 0})
            elif isinstance(item, dict):
                h = item.get("hash")
                if not h:
                    # build fallback hash
                    key = (item.get("url") or item.get("title") or "") + (item.get("company") or "")
                    h = hashlib.sha1(key.encode("utf-8")).hexdigest()
                normalized.append({
                    "hash": h,
                    "title": item.get("title"),
                    "company": item.get("company"),
                    "location": item.get("location"),
                    "url": item.get("url"),
                    "first_seen": int(item.get("first_seen") or 0)
                })
            else:
                logger.debug("Skipping unknown dedup item type: %r", item)
    else:
        logger.warning("Unexpected dedup file format - expected list.")
    return normalized

def save_dedup(entries: List[Dict]):
    try:
        with open(DEDUP_PATH, "w", encoding="utf-8") as fh:
            json.dump(entries, fh, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning("Failed saving dedup file: %s", e)

def prune_dedup(dedup_list: List[Dict], max_age_days: int) -> List[Dict]:
    if not max_age_days:
        return dedup_list
    cutoff = int((datetime.utcnow() - timedelta(days=max_age_days)).timestamp())
    kept = []
    removed = 0
    for e in dedup_list:
        if isinstance(e, dict):
            if int(e.get("first_seen", 0) or 0) >= cutoff:
                kept.append(e)
            else:
                removed += 1
        else:
            removed += 1
    if removed:
        logger.info("Pruned %d old dedup entries (>%d days).", removed, max_age_days)
    return kept

# -----------------------
# HTTP + backoff helper
# -----------------------
def http_request(method: str, url: str, **kwargs) -> requests.Response:
    attempts = 4
    delay = 1.0
    for attempt in range(1, attempts + 1):
        try:
            headers = kwargs.pop("headers", {}) or {}
            # do not override if already provided
            if "User-Agent" not in headers:
                headers["User-Agent"] = USER_AGENT
            return requests.request(method, url, timeout=REQUESTS_TIMEOUT, headers=headers, **kwargs)
        except Exception as e:
            logger.debug("HTTP %s %s failed (%d/%d): %s", method, url, attempt, attempts, e)
            if attempt == attempts:
                raise
            time.sleep(delay + random.random())
            delay *= 2
    raise RuntimeError("unreachable")

# -----------------------
# RapidAPI JSearch (kept)
# -----------------------
def query_jsearch(query: str, location: Optional[str] = None, per_page: int = 20) -> List[Dict]:
    """
    Uses RapidAPI JSearch endpoint. Requires JSEARCH_API_KEY secret.
    Expects RapidAPI host header 'jsearch.p.rapidapi.com'.
    """
    if not JSEARCH_API_KEY:
        logger.debug("JSEARCH_API_KEY not set; skipping jsearch.")
        return []

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        "Accept": "application/json",
    }
    params = {"query": query or "", "location": location or "", "page": 1, "num_pages": 1}

    try:
        resp = http_request("GET", url, headers=headers, params=params)
        if resp.status_code != 200:
            body = (resp.text or "")[:400]
            logger.warning("JSearch returned %s for %r/%r: %s", resp.status_code, query, location, body)
            return []
        data = resp.json()
        jobs = []
        for item in data.get("data", []):
            jobs.append({
                "id": item.get("job_id") or item.get("id"),
                "title": item.get("job_title") or item.get("title"),
                "company": item.get("employer_name") or item.get("company"),
                "location": item.get("job_city") or item.get("location") or location,
                "description": item.get("job_description") or "",
                "url": item.get("job_apply_link") or item.get("apply_link") or item.get("url"),
                "raw": item
            })
        return jobs
    except Exception as e:
        logger.warning("JSearch request exception for %r/%r: %s", query, location, e)
        return []

# -----------------------
# REMOTIVE (free JSON)
# -----------------------
def query_remotive(query: str, limit: int = 50) -> List[Dict]:
    """
    Remotive public API: https://remotive.com/api/remote-jobs?search={query}
    """
    try:
        url = "https://remotive.com/api/remote-jobs"
        params = {"search": query or ""}
        resp = http_request("GET", url, params=params)
        if resp.status_code != 200:
            logger.debug("Remotive returned %s for %r", resp.status_code, query)
            return []
        data = resp.json()
        jobs = []
        for item in data.get("jobs", [])[:limit]:
            jobs.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "company": item.get("company_name") or item.get("company"),
                "location": item.get("candidate_required_location"),
                "description": item.get("description") or "",
                "url": item.get("url") or item.get("job_apply_url"),
                "raw": item
            })
        return jobs
    except Exception as e:
        logger.warning("Remotive query failed for %r: %s", query, e)
        return []

# -----------------------
# REMOTEOK (free JSON)
# -----------------------
def query_remoteok(query: str, limit: int = 100) -> List[Dict]:
    """
    RemoteOK public API: https://remoteok.com/api
    We'll filter by keywords in title/company/tags.
    """
    try:
        url = "https://remoteok.com/api"
        resp = http_request("GET", url)
        if resp.status_code != 200:
            logger.debug("RemoteOK returned %s", resp.status_code)
            return []
        data = resp.json()
        if not isinstance(data, list):
            return []
        qlow = (query or "").lower()
        jobs = []
        for item in data:
            # first entry is metadata often; skip if no id or position
            if not item.get("id") or item.get("is_paid"):
                continue
            title = (item.get("position") or item.get("title") or "").strip()
            company = item.get("company") or ""
            combined = f"{title} {company} {','.join(item.get('tags', []) or [])}".lower()
            if qlow and qlow not in combined:
                # keep a few results if query is empty
                continue
            jobs.append({
                "id": item.get("id"),
                "title": title,
                "company": company,
                "location": item.get("location") or item.get("city") or "",
                "description": item.get("description") or "",
                "url": item.get("url") or item.get("apply_url") or f"https://remoteok.com/remote-jobs/{item.get('id')}",
                "raw": item
            })
            if len(jobs) >= limit:
                break
        return jobs
    except Exception as e:
        logger.warning("RemoteOK query failed: %s", e)
        return []

# -----------------------
# WEWORKREMOTELY (HTML)
# -----------------------
def parse_weworkremotely(query: str, limit: int = 30) -> List[Dict]:
    """
    Simple HTML parse for weworkremotely search page.
    """
    try:
        url = f"https://weworkremotely.com/remote-jobs/search?term={requests.utils.quote(query or '')}"
        resp = http_request("GET", url)
        if resp.status_code != 200:
            logger.debug("WeWorkRemotely returned %s for %r", resp.status_code, query)
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        # job links are in article > a or section > ul > li > a
        for a in soup.select("section.jobs article a, section.jobs ul li a")[:limit]:
            href = a.get("href")
            title_el = a.select_one(".title") or a.select_one("span.title") or a.select_one("h2") or a
            company_el = a.select_one(".company") or a.select_one("span.company")
            title = title_el.get_text(strip=True) if title_el else a.get_text(strip=True)
            company = company_el.get_text(strip=True) if company_el else ""
            if not href:
                continue
            full_url = requests.compat.urljoin("https://weworkremotely.com", href)
            jobs.append({
                "id": None,
                "title": title,
                "company": company,
                "location": "",
                "description": "",
                "url": full_url,
                "raw": {}
            })
        return jobs
    except Exception as e:
        logger.warning("WeWorkRemotely parse failed for %r: %s", query, e)
        return []

# -----------------------
# Logo fetch & WP media
# -----------------------
def fetch_company_logo(domain: str) -> Optional[bytes]:
    if not domain:
        return None
    try:
        url = f"https://logo.clearbit.com/{domain}"
        resp = http_request("GET", url)
        if resp.status_code == 200 and "image" in (resp.headers.get("content-type") or ""):
            return resp.content
    except Exception:
        pass
    return None

def upload_logo_to_wp(image_bytes: bytes, filename: str) -> Optional[int]:
    if not (WP_URL and WP_USERNAME and WP_APP_PASSWORD):
        return None
    endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/media"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    try:
        resp = http_request("POST", endpoint, auth=(WP_USERNAME, WP_APP_PASSWORD), headers=headers, data=image_bytes)
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception as e:
        logger.warning("WP media upload failed: %s", e)
        return None

# -----------------------
# Post job to WordPress
# -----------------------
def post_job_to_wp(job: Dict, continent_id: str, country_code: str, posting_cfg: Dict) -> Optional[int]:
    if not (WP_URL and WP_USERNAME and WP_APP_PASSWORD):
        logger.error("Missing WP credentials; skipping posting.")
        return None
    endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/posts"
    title = job.get("title") or "Job"
    company = job.get("company") or ""
    location = job.get("location") or ""
    apply_url = job.get("url") or ""
    slug = slugify(f"{title}-{company}-{location}")[:200]

    html = f"<p><strong>Company:</strong> {company}</p>"
    html += f"<p><strong>Location:</strong> {location}</p>"
    if apply_url:
        html += f'<p><strong>Apply:</strong> <a href="{apply_url}" target="_blank" rel="noopener">{apply_url}</a></p>'
    html += "<hr/>" + (job.get("description") or "")

    tags = posting_cfg.get("tags", []).copy() if posting_cfg else []
    tags.append(f"continent:{continent_id}")
    if country_code:
        tags.append(f"country:{country_code}")

    payload = {
        "title": title,
        "content": html,
        "slug": slug,
        "status": posting_cfg.get("post_status", "draft") if posting_cfg else "draft",
        "tags": tags
    }

    if job.get("_featured_media_id"):
        payload["featured_media"] = job.get("_featured_media_id")

    try:
        resp = http_request("POST", endpoint, auth=(WP_USERNAME, WP_APP_PASSWORD), json=payload)
        resp.raise_for_status()
        pid = resp.json().get("id")
        logger.info("Posted job to WP: %s (post id=%s)", title, pid)
        return pid
    except Exception as e:
        logger.error("Failed to post job to WP: %s", e)
        return None

# -----------------------
# Main orchestrator
# -----------------------
def main():
    config = load_config()
    dedup_list = load_dedup()
    dedup_cfg = config.get("dedup", {}) or {}
    max_age_days = int(dedup_cfg.get("max_age_days") or 0)
    dedup_list = prune_dedup(dedup_list, max_age_days)
    original_len = len(dedup_list)

    sources_cfg = config.get("sources", []) or []
    continents = config.get("continents", []) or []
    posting_cfg = config.get("posting", {}) or {}
    global_defaults = config.get("global", {}) or {}

    # Optionally pick one continent
    if PROCESS_CONTINENT:
        continents = [c for c in continents if c.get("id") == PROCESS_CONTINENT]
        if not continents:
            logger.warning("PROCESS_CONTINENT set but no matching continent found: %s", PROCESS_CONTINENT)
            return

    # Auto-rotate feature (optional)
    if AUTO_ROTATE and continents:
        weekday = datetime.utcnow().weekday()
        mapping = {0:"asia",1:"europe",2:"north_america",3:"south_america",4:"africa",5:"oceania",6:"antarctica"}
        target = mapping.get(weekday)
        if target:
            continents = [c for c in continents if c.get("id") == target] or continents[:1]

    total_new = 0
    for cont in continents:
        cont_id = cont.get("id")
        cont_name = cont.get("name")
        logger.info("== Continent: %s (%s) ==", cont_name, cont_id)
        base_pause = float(cont.get("pause_seconds", 2))

        for country in cont.get("countries", []):
            country_code = country.get("code")
            country_name = country.get("name")
            for locale in country.get("locales", []):
                city = locale.get("city")
                query = locale.get("query")
                qtext = " ".join([s for s in [query, city, country_name] if s]).strip()
                logger.info("Searching: '%s' (continent=%s country=%s)", qtext, cont_id, country_code)

                candidate_jobs: List[Dict] = []

                # iterate over configured sources in order
                for src in sources_cfg:
                    if not src.get("enabled", True):
                        continue
                    stype = src.get("type")
                    try:
                        if stype == "jsearch":
                            candidate_jobs.extend(query_jsearch(qtext, location=city or country_name, per_page=global_defaults.get("default_per_page", 20)))
                        elif stype == "remotive":
                            candidate_jobs.extend(query_remotive(qtext, limit=src.get("limit", 50)))
                        elif stype == "remoteok":
                            candidate_jobs.extend(query_remoteok(qtext, limit=src.get("limit", 80)))
                        elif stype == "weworkremotely":
                            candidate_jobs.extend(parse_weworkremotely(qtext, limit=src.get("limit", 30)))
                        elif stype == "html":
                            endpoint = src.get("endpoint")
                            if endpoint:
                                # Basic fallback: call the url format from config
                                try:
                                    url = endpoint.format(query=requests.utils.quote(query or ""), city=requests.utils.quote(city or ""))
                                    resp = http_request("GET", url)
                                    # simple parser: find links with job titles
                                    soup = BeautifulSoup(resp.text, "html.parser")
                                    for a in soup.select("a")[:src.get("limit", 10)]:
                                        href = a.get("href")
                                        if not href:
                                            continue
                                        title = a.get_text(strip=True)
                                        candidate_jobs.append({"id": None, "title": title, "company": "", "location": city, "description": "", "url": requests.compat.urljoin(url, href)})
                                except Exception as e:
                                    logger.debug("HTML source parse failed: %s", e)
                        else:
                            logger.debug("Unknown source type in config: %s", stype)
                    except Exception as e:
                        logger.warning("Source %s failed for query=%r: %s", stype, qtext, e)

                    # polite pause per source
                    time.sleep(base_pause + random.random() * base_pause)

                # process candidate jobs
                for job in candidate_jobs:
                    # stable key for hash
                    key = (str(job.get("id") or "") or "") or (job.get("url") or job.get("title") or "")
                    if not key:
                        continue
                    jhash = hashlib.sha1(key.encode("utf-8")).hexdigest()
                    if any(e.get("hash") == jhash for e in dedup_list):
                        continue

                    # attempt logo fetch & upload
                    domain = None
                    raw = job.get("raw") or {}
                    domain = raw.get("company_domain") or raw.get("company_website") or (slugify(job.get("company") or "").replace("-", "") + ".com")
                    logo_bytes = fetch_company_logo(domain) if domain else None
                    if logo_bytes:
                        try:
                            img = Image.open(BytesIO(logo_bytes))
                            img.thumbnail((600,600))
                            out = BytesIO()
                            fmt = img.format or "PNG"
                            img.save(out, format=fmt)
                            filename = f"{slugify(job.get('company') or 'company')}-{jhash[:8]}.{fmt.lower()}"
                            media_id = upload_logo_to_wp(out.getvalue(), filename)
                            if media_id:
                                job["_featured_media_id"] = media_id
                        except Exception as e:
                            logger.debug("Logo processing error: %s", e)

                    # post to WP
                    post_id = post_job_to_wp(job, cont_id, country_code, posting_cfg)
                    if post_id:
                        total_new += 1
                        dedup_list.append({
                            "hash": jhash,
                            "title": job.get("title"),
                            "company": job.get("company"),
                            "location": job.get("location"),
                            "url": job.get("url"),
                            "first_seen": int(time.time())
                        })
                    else:
                        logger.debug("Skipping dedup append because posting failed for job: %s", job.get("title"))

                # pause between locales
                time.sleep(base_pause + random.random() * base_pause)

    # persist dedup if changed
    if len(dedup_list) != original_len:
        save_dedup(dedup_list)
        logger.info("Saved dedup file with %d entries.", len(dedup_list))
    else:
        logger.info("No changes to dedup file.")

    logger.info("Run complete. New jobs posted: %d", total_new)

if __name__ == "__main__":
    main()
