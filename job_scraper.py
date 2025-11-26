#!/usr/bin/env python3
"""
TechJobs360 Combined Global Job Scraper (fixed & formatted)

Features:
- RapidAPI JSearch (if JSEARCH_API_KEY is provided and source enabled)
- Free sources: Remotive, RemoteOK, WeWorkRemotely
- Optional: Indeed / LinkedIn HTML scrapers (disabled by default in config.yaml)
- Dedup (legacy list of hashes or list of dicts), pruning, and saving to posted_jobs.json
- Clearbit logo fetch + WP media upload
- Posts jobs to WordPress via REST API (App Password)
- Simple keyword-based classification (role, seniority, remote/onsite)
- Polite rate-limiting, retries, and robust error handling
- Config driven via config.yaml (continents, sources, posting, dedup)
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
from bs4 import BeautifulSoup
from slugify import slugify
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta

# -------------------------
# Paths & environment
# -------------------------
BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.yaml"
DEDUP_PATH = BASE_DIR / "posted_jobs.json"

WP_URL = os.environ.get("WP_URL")
WP_USERNAME = os.environ.get("WP_USERNAME")
WP_APP_PASSWORD = os.environ.get("WP_APP_PASSWORD")
JSEARCH_API_KEY = os.environ.get("JSEARCH_API_KEY")
PROCESS_CONTINENT = os.environ.get("PROCESS_CONTINENT")
AUTO_ROTATE_ENV = os.environ.get("AUTO_ROTATE", "true").lower() in ("1", "true", "yes")

REQUESTS_TIMEOUT = 20
USER_AGENT = "TechJobs360Scraper-final (+https://techjobs360.com)"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("techjobs360")

# Validate WP_URL has proper scheme
if WP_URL and not (WP_URL.startswith("http://") or WP_URL.startswith("https://")):
    logger.warning("WP_URL is set but missing http:// or https:// scheme. Current value: %s", WP_URL)
    logger.warning("WordPress posting will be disabled. Please set WP_URL to a valid URL like https://techjobs360.com")
    WP_URL = None  # Disable WordPress posting if URL is invalid

# -------------------------
# Helpers: config & dedup
# -------------------------
def load_config() -> Dict:
    if not CONFIG_PATH.exists():
        logger.error("Missing config.yaml - place it in repo root.")
        sys.exit(1)
    with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}

def load_dedup() -> List[Dict]:
    if not DEDUP_PATH.exists():
        return []
    try:
        with open(DEDUP_PATH, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as e:
        logger.warning("Could not read dedup file, starting fresh: %s", e)
        return []
    normalized = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, str):
                normalized.append({"hash": item, "first_seen": 0})
            elif isinstance(item, dict):
                h = item.get("hash")
                if not h:
                    key = (item.get("url") or "") + (item.get("title") or "")
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
        logger.warning("Unexpected dedup file format; expected list.")
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
        try:
            fs = int(e.get("first_seen", 0) or 0)
            if fs >= cutoff:
                kept.append(e)
            else:
                removed += 1
        except Exception:
            removed += 1
    if removed:
        logger.info("Pruned %d old dedup entries", removed)
    return kept

# -------------------------
# HTTP with retries/backoff
# -------------------------
def http_request(method: str, url: str, **kwargs) -> requests.Response:
    attempts = 4
    delay = 1.0
    for attempt in range(1, attempts + 1):
        try:
            headers = kwargs.pop("headers", {}) or {}
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

# -------------------------
# RapidAPI JSearch (kept)
# -------------------------
def query_jsearch(query: str, location: Optional[str] = None, per_page: int = 20) -> List[Dict]:
    if not JSEARCH_API_KEY:
        logger.debug("No JSEARCH_API_KEY set; skipping jsearch")
        return []

    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": JSEARCH_API_KEY,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
        "Accept": "application/json"
    }
    params = {"query": query or "", "location": location or "", "page": 1, "num_pages": 1}

    try:
        resp = http_request("GET", url, headers=headers, params=params)
        if resp.status_code != 200:
            logger.warning("JSearch returned %s for %r/%r: %s", resp.status_code, query, location, (resp.text or "")[:300])
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

# -------------------------
# Remotive (free JSON)
# -------------------------
def query_remotive(query: str, limit: int = 50) -> List[Dict]:
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

# -------------------------
# RemoteOK (free JSON)
# -------------------------
def query_remoteok(query: str, limit: int = 80) -> List[Dict]:
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
            if not item.get("id"):
                continue
            title = item.get("position") or item.get("title") or ""
            company = item.get("company") or ""
            combined = f"{title} {company} {' '.join(item.get('tags') or [])}".lower()
            if qlow and qlow not in combined:
                continue
            jobs.append({
                "id": item.get("id"),
                "title": title,
                "company": company,
                "location": item.get("location") or "",
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

# -------------------------
# WeWorkRemotely HTML parse
# -------------------------
def parse_weworkremotely(query: str, limit: int = 30) -> List[Dict]:
    try:
        url = f"https://weworkremotely.com/remote-jobs/search?term={requests.utils.quote(query or '')}"
        resp = http_request("GET", url)
        if resp.status_code != 200:
            logger.debug("WeWorkRemotely returned %s for %r", resp.status_code, query)
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
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


# ---------------------------
# Arbeitnow (free JSON API)
# ---------------------------
def query_arbeitnow(query: str, limit: int = 50) -> List[Dict]:
    try:
        url = "https://arbeitnow.com/api/job-board-api"
        resp = http_request("GET", url)
        if resp.status_code != 200:
            logger.debug("Arbeitnow returned %s", resp.status_code)
            return []
        data = resp.json()
        jobs = []
        qlow = (query or "").lower()
        for item in data.get("data", []):
            title = item.get("title", "")
            if qlow and qlow not in title.lower():
                continue
            jobs.append({
                "id": item.get("slug"),
                "title": title,
                "company": item.get("company_name", ""),
                "location": item.get("location", ""),
                "description": item.get("description", ""),
                "url": item.get("url", ""),
                "raw": item
            })
            if len(jobs) >= limit:
                break
        return jobs
    except Exception as e:
        logger.warning("Arbeitnow query failed: %s", e)
        return []

# ---------------------------
# Jobicy (free JSON API)
# ---------------------------
def query_jobicy(query: str, limit: int = 50) -> List[Dict]:
    try:
        url = "https://jobicy.com/api/v2/remote-jobs"
        params = {"count": limit}
        if query:
            params["tag"] = query
        resp = http_request("GET", url, params=params)
        if resp.status_code != 200:
            logger.debug("Jobicy returned %s", resp.status_code)
            return []
        data = resp.json()
        jobs = []
        for item in data.get("jobs", []):
            jobs.append({
                "id": item.get("id"),
                "title": item.get("jobTitle", ""),
                "company": item.get("companyName", ""),
                "location": item.get("jobGeo", "Remote"),
                "description": item.get("jobDescription", ""),
                "url": item.get("url", ""),
                "raw": item
            })
        return jobs
    except Exception as e:
        logger.warning("Jobicy query failed: %s", e)
        return []

# ---------------------------
# Himalayas (free JSON API)
# ---------------------------
def query_himalayas(query: str, limit: int = 40) -> List[Dict]:
    try:
        url = "https://himalayas.app/jobs/api"
        params = {"limit": limit}
        if query:
            params["q"] = query
        resp = http_request("GET", url, params=params)
        if resp.status_code != 200:
            logger.debug("Himalayas returned %s", resp.status_code)
            return []
        data = resp.json()
        jobs = []
        for item in data.get("jobs", []):
            jobs.append({
                "id": item.get("id"),
                "title": item.get("title", ""),
                "company": item.get("companyName", ""),
                "location": item.get("locationRestrictions", "Remote"),
                "description": item.get("description", ""),
                "url": f"https://himalayas.app/jobs/{item.get('slug', '')}",
                "raw": item
            })
        return jobs
    except Exception as e:
        logger.warning("Himalayas query failed: %s", e)
        return []


# -------------------------
# Indeed HTML parse (careful)
# -------------------------
def parse_indeed(query: str, city: Optional[str] = None, limit: int = 20) -> List[Dict]:
    try:
        base = "https://www.indeed.com/jobs"
        params = {"q": query or "", "l": city or ""}
        resp = http_request("GET", base, params=params, headers={"User-Agent": USER_AGENT})
        if resp.status_code != 200:
            logger.debug("Indeed returned %s", resp.status_code)
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for card in soup.select(".result, .jobsearch-SerpJobCard")[:limit]:
            title_el = card.select_one("h2.jobTitle, .jobTitle a, a.jobtitle")
            link = title_el.select_one("a") if title_el else card.select_one("a")
            title = title_el.get_text(strip=True) if title_el else (link.get_text(strip=True) if link else "")
            company_el = card.select_one(".company")
            location_el = card.select_one(".location")
            href = link.get("href") if link else None
            if href and not href.startswith("http"):
                href = requests.compat.urljoin("https://www.indeed.com", href)
            jobs.append({
                "id": None,
                "title": title,
                "company": company_el.get_text(strip=True) if company_el else "",
                "location": location_el.get_text(strip=True) if location_el else city or "",
                "description": "",
                "url": href
            })
        return jobs
    except Exception as e:
        logger.warning("Indeed parse failed: %s", e)
        return []

# -------------------------
# LinkedIn HTML parse (BEST EFFORT)
# -------------------------
def parse_linkedin(query: str, location: Optional[str] = None, limit: int = 15) -> List[Dict]:
    try:
        url = "https://www.linkedin.com/jobs/search/"
        params = {"keywords": query or "", "location": location or ""}
        resp = http_request("GET", url, params=params)
        if resp.status_code != 200:
            logger.debug("LinkedIn returned %s", resp.status_code)
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        jobs = []
        for card in soup.select(".result-card.job-result-card")[:limit]:
            title_el = card.select_one(".result-card__title") or card.select_one("h3")
            company_el = card.select_one(".result-card__subtitle") or card.select_one(".result-card__company")
            link_el = card.select_one("a.result-card__full-card-link") or card.select_one("a")
            href = link_el.get("href") if link_el else None
            title = title_el.get_text(strip=True) if title_el else ""
            company = company_el.get_text(strip=True) if company_el else ""
            jobs.append({
                "id": None,
                "title": title,
                "company": company,
                "location": location or "",
                "description": "",
                "url": href
            })
        return jobs
    except Exception as e:
        logger.warning("LinkedIn parse failed: %s", e)
        return []

# -------------------------
# Logo fetch & WP media
# -------------------------
def fetch_logo(domain: str) -> Optional[bytes]:
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

def upload_media_to_wp(image_bytes: bytes, filename: str) -> Optional[int]:
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

# -------------------------
# Post to WordPress
# -------------------------
def post_to_wp(job: Dict, continent_id: str, country_code: str, posting_cfg: Dict) -> Optional[int]:
    if not (WP_URL and WP_USERNAME and WP_APP_PASSWORD):
        logger.error("Missing WP credentials; cannot post.")
        return None
    endpoint = WP_URL.rstrip("/") + "/wp-json/wp/v2/posts"
    title = job.get("title") or "Job"
    company = job.get("company") or ""
    location = job.get("location") or ""
    apply_url = job.get("url") or ""
    slug = slugify(f"{title}-{company}-{location}")[:200]

    content = f"<p><strong>Company:</strong> {company}</p>"
    content += f"<p><strong>Location:</strong> {location}</p>"
    if apply_url:
        content += f'<p><strong>Apply:</strong> <a href="{apply_url}" target="_blank" rel="noopener">{apply_url}</a></p>'
    content += "<hr/>" + (job.get("description") or "")

    tags = posting_cfg.get("tags", []).copy() if posting_cfg else []
    tags.append(f"continent:{continent_id}")
    if country_code:
        tags.append(f"country:{country_code}")

    payload = {
        "title": title,
        "content": content,
        "slug": slug,
        "status": posting_cfg.get("post_status", "draft") if posting_cfg else "draft",
        "tags": tags
    }

    if job.get("_featured_media_id"):
        payload["featured_media"] = job.get("_featured_media_id")

    try:
        resp = http_request("POST", endpoint, auth=(WP_USERNAME, WP_APP_PASSWORD), json=payload)
        resp.raise_for_status()
        return resp.json().get("id")
    except Exception as e:
        logger.error("Failed to post job to WP: %s", e)
        return None

# -------------------------
# Simple AI classification
# -------------------------
SENIORITY_KEYWORDS = {
    "senior": ["senior", "lead", "principal", "sr.", "staff"],
    "mid": ["mid", "experienced"],
    "junior": ["junior", "jr.", "entry", "associate", "graduate"]
}
ROLE_KEYWORDS = {
    "backend": ["backend", "backend engineer", "java", "golang", "python", "ruby", "node"],
    "frontend": ["frontend", "react", "angular", "vue", "javascript", "css", "html"],
    "fullstack": ["full stack", "full-stack", "fullstack"],
    "data": ["data", "data scientist", "data engineer", "ml", "machine learning"],
    "devops": ["devops", "site reliability", "sre", "infrastructure", "ci/cd"],
    "mobile": ["ios", "android", "mobile", "react native", "flutter"],
    "qa": ["qa", "quality assurance", "tester", "automation"]
}

def classify_job(title: str, description: str) -> Dict:
    txt = (" ".join([title or "", description or ""])).lower()
    seniority = "unspecified"
    for level, kws in SENIORITY_KEYWORDS.items():
        if any(k in txt for k in kws):
            seniority = level
            break
    role = "other"
    for r, kws in ROLE_KEYWORDS.items():
        if any(k in txt for k in kws):
            role = r
            break
    remote = "remote" if "remote" in txt or "work from home" in txt else "onsite"
    skills = []
    for r, kws in ROLE_KEYWORDS.items():
        for k in kws:
            if k in txt and k not in skills:
                skills.append(k)
    return {"seniority": seniority, "role": role, "work_type": remote, "skills": skills[:6]}

# -------------------------
# Main orchestration
# -------------------------
def pick_continent_by_weekday(continents: List[Dict]) -> Optional[str]:
    weekday = datetime.utcnow().weekday()
    mapping = {0:"asia",1:"europe",2:"north_america",3:"south_america",4:"africa",5:"oceania",6:"antarctica"}
    target = mapping.get(weekday)
    for c in continents:
        if c.get("id") == target:
            return target
    return continents[0].get("id") if continents else None

def main():
    config = load_config()
    dedup = load_dedup()
    dedup_cfg = config.get("dedup", {}) or {}
    max_age = int(dedup_cfg.get("max_age_days") or 0)
    dedup = prune_dedup(dedup, max_age)
    orig_len = len(dedup)

    sources_cfg = config.get("sources", []) or []
    continents = config.get("continents", []) or []
    posting_cfg = config.get("posting", {}) or {}
    global_cfg = config.get("global", {}) or {}

    # PROCESS_CONTINENT env filter
    if PROCESS_CONTINENT:
        continents = [c for c in continents if c.get("id") == PROCESS_CONTINENT]
        if not continents:
            logger.warning("PROCESS_CONTINENT set but no matching continent found: %s", PROCESS_CONTINENT)
            return

    # AUTO_ROTATE
    auto_rotate_cfg = global_cfg.get("auto_rotate", True)
    if AUTO_ROTATE_ENV or auto_rotate_cfg:
        pick = pick_continent_by_weekday(continents)
        if pick:
            continents = [c for c in continents if c.get("id") == pick] or continents[:1]
            logger.info("AUTO_ROTATE enabled -> processing continent: %s", pick)

    total_new = 0
    for cont in continents:
        cont_id = cont.get("id")
        cont_name = cont.get("name")
        base_pause = float(cont.get("pause_seconds", 2))
        logger.info("== Continent: %s (%s) ==", cont_name, cont_id)

        for country in cont.get("countries", []):
            country_code = country.get("code")
            country_name = country.get("name")
            for loc in country.get("locales", []):
                city = loc.get("city")
                query = loc.get("query")
                qtext = " ".join([s for s in [query, city, country_name] if s]).strip()
                logger.info("Searching: %s", qtext)

                candidate_jobs: List[Dict] = []

                # iterate over configured sources in order
                for src in sources_cfg:
                    if not src.get("enabled", True):
                        continue

                    stype = src.get("type")
                    try:
                        if stype == "jsearch":
                            candidate_jobs += query_jsearch(qtext, location=city or country_name, per_page=global_cfg.get("default_per_page", 20))
                        elif stype == "remotive":
                            candidate_jobs += query_remotive(qtext, limit=src.get("limit", 50))
                        elif stype == "remoteok":
                            candidate_jobs += query_remoteok(qtext, limit=src.get("limit", 80))
                        elif stype == "weworkremotely":
                            candidate_jobs += query_weworkremotely(qtext, limit=src.get("limit", 40))
                        elif stype == "indeed":
                            if src.get("enabled_html", False):
                                candidate_jobs += parse_indeed(query or qtext, city, limit=src.get("limit", 20))
                        elif stype == "arbeitnow":
                            candidate_jobs += query_arbeitnow(qtext, limit=src.get("limit", 50))
                        elif stype == "jobicy":
                            candidate_jobs += query_jobicy(qtext, limit=src.get("limit", 50))
                        elif stype == "himalayas":
                            candidate_jobs += query_himalayas(qtext, limit=src.get("limit", 40))                                
                    elif stype == "linkedin":
                        if src.get("enabled_html", False):
                            candidate_jobs += parse_linkedin(query or qtext, city, limit=src.get("limit", 15))                        elif stype == "html":
                            endpoint = src.get("endpoint")
                            if endpoint:
                                try:
                                    url = endpoint.format(query=requests.utils.quote(query or ""), city=requests.utils.quote(city or ""))
                                    resp = http_request("GET", url)
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

                # process results
                for job in candidate_jobs:
                    hkey = (job.get("id") or job.get("url") or job.get("title") or "")
                    if not hkey:
                        continue

                    jhash = hashlib.sha1(str(hkey).encode("utf-8")).hexdigest()
                    if any(d.get("hash") == jhash for d in dedup):
                        continue

                    # AI classification
                    cls = classify_job(job.get("title") or "", job.get("description") or "")
                    job["_classification"] = cls

                    # Logo
                    raw = job.get("raw") or {}
                    domain = raw.get("company_domain") or raw.get("company_website") or (slugify(job.get("company") or "").replace("-", "") + ".com")
                    logo_bytes = fetch_logo(domain) if domain else None
                    if logo_bytes:
                        try:
                            img = Image.open(BytesIO(logo_bytes))
                            img.thumbnail((600, 600))
                            out = BytesIO()
                            fmt = img.format or "PNG"
                            img.save(out, format=fmt)
                            filename = f"{slugify(job.get('company') or 'company')}-{jhash[:8]}.{fmt.lower()}"
                            media_id = upload_media_to_wp(out.getvalue(), filename)
                            if media_id:
                                job["_featured_media_id"] = media_id
                        except Exception as e:
                            logger.debug("Logo processing error: %s", e)

                    # Merge posting tags with classification
                    posting_tags = posting_cfg.get("tags", [])[:] if posting_cfg else []
                    posting_tags += [f"role:{cls.get('role')}", f"seniority:{cls.get('seniority')}", cls.get("work_type")]
                    posting_cfg["tags"] = posting_tags

                    # Post to WP
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
                    else:
                        logger.debug("Posting failed; not adding to dedup: %s", job.get("title"))

                # pause between locales
                time.sleep(base_pause + random.random() * base_pause)

    # persist dedup
    if len(dedup) != orig_len:
        save_dedup(dedup)
        logger.info("Saved dedup file with %d entries.", len(dedup))
    else:
        logger.info("No changes to dedup file.")

    logger.info("Run complete. New jobs posted: %d", total_new)


if __name__ == "__main__":
    main()
