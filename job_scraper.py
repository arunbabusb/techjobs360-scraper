#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Real-job scraper -> WordPress (WP Job Manager)
- Verifies WP auth via /users/me (Application Passwords)
- Fetches jobs from Adzuna + JSearch (RapidAPI)
- Posts to /wp-json/wp/v2/job-listings (WP Job Manager)
- Dedupes using REST search
- Clear summary logs
References:
- WP Application Passwords: https://make.wordpress.org/core/2020/11/05/application-passwords-integration-guide/
- WP Job Manager REST base: /wp-json/wp/v2/job-listings
- Adzuna search API: https://developer.adzuna.com/activedocs
- RapidAPI auth headers: https://docs.rapidapi.com/docs/configuring-api-security
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

# ----------------------------
# ENV / SETTINGS
# ----------------------------
WP_BASE_URL      = os.getenv("WP_BASE_URL", "https://techjobs360.com").rstrip("/")
WP_USER          = os.getenv("WP_USER", "")
WP_APP_PASSWORD  = os.getenv("WP_APP_PASSWORD", "")
WP_API_URL       = f"{WP_BASE_URL}/wp-json/wp/v2/job-listings"  # WPJM REST base

# JSearch (RapidAPI)
JSEARCH_API_KEY   = os.getenv("JSEARCH_API_KEY", "")
JSEARCH_HOST      = os.getenv("JSEARCH_HOST", "jsearch.p.rapidapi.com")
JSEARCH_QUERY     = os.getenv("JSEARCH_QUERY", "software developer OR data engineer")
JSEARCH_NUM_PAGES = int(os.getenv("JSEARCH_NUM_PAGES", "2"))

# Adzuna
ADZUNA_APP_ID    = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY   = os.getenv("ADZUNA_APP_KEY", "")
COUNTRIES        = [cc.strip() for cc in os.getenv("COUNTRIES", "in,us,fr,gb,de").split(",")]
ADZUNA_RESULTS_PER_PAGE = int(os.getenv("ADZUNA_RESULTS_PER_PAGE", "20"))
ADZUNA_MAX_DAYS_OLD     = int(os.getenv("ADZUNA_MAX_DAYS_OLD", "3"))
ADZUNA_WHAT             = os.getenv("ADZUNA_WHAT", "software OR developer OR engineer")

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("job_scraper")

def new_session() -> requests.Session:
    s = requests.Session()
    retries = Retry(total=4, backoff_factor=0.6,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=["GET", "POST"])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.mount("http://", HTTPAdapter(max_retries=retries))
    return s

S = new_session()

# ----------------------------
# Helpers
# ----------------------------
def normalize_job(raw: Dict) -> Dict:
    """Map various fields from Adzuna/JSearch to a common shape."""
    title = raw.get("job_title") or raw.get("title")
    description = raw.get("job_description
