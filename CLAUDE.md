# CLAUDE.md - TechJobs360 Scraper Documentation for AI Assistants

## Project Overview

**TechJobs360 Scraper** is an automated Python job scraper that aggregates tech jobs from multiple sources (JSearch API, Remotive, RemoteOK, WeWorkRemotely, Indeed, LinkedIn) and posts them to a WordPress job board using WP Job Manager. The scraper includes intelligent deduplication, logo fetching, job classification, and automated posting with full attribution.

**Purpose**: Maintain a fresh, global tech job board by scraping multiple sources, enriching job data, and automatically posting to WordPress while avoiding duplicates.

**Key Features**:
- Multi-source job aggregation (8+ sources)
- Automatic deduplication using hash-based tracking
- Company logo fetching and WordPress media upload
- AI-powered job classification (role, seniority, work type)
- Global coverage with continent-based rotation
- Rate limiting and polite scraping
- Scheduled GitHub Actions workflow (4x daily)

---

## Repository Structure

```
techjobs360-scraper/
├── job_scraper.py          # Main scraper script (~630 lines)
├── config.yaml             # Configuration file (sources, continents, posting)
├── posted_jobs.json        # Deduplication database (tracked jobs)
├── requirements.txt        # Python dependencies
├── README.md              # Project README
├── CLAUDE.md              # This file - AI assistant guide
└── .github/
    └── workflows/
        ├── scraper.yml    # Main scheduled scraper workflow
        └── diag-auth.yml  # WordPress auth diagnostic workflow
```

### File Purposes

| File | Purpose | Size | Modified Frequently? |
|------|---------|------|---------------------|
| `job_scraper.py` | Core scraper logic, source integrations, WP posting | ~630 lines | Yes (features) |
| `config.yaml` | Source toggles, continent/city queries, posting config | ~287 lines | Yes (config changes) |
| `posted_jobs.json` | Job deduplication store (hash, title, company, URL, timestamp) | Growing | Yes (every run) |
| `requirements.txt` | Python dependencies (requests, PyYAML, beautifulsoup4, etc.) | 8 lines | Rarely |
| `.github/workflows/scraper.yml` | Scheduled CI/CD workflow (4x daily at UTC 00:30, 06:30, 12:30, 18:30) | 74 lines | Rarely |
| `.github/workflows/diag-auth.yml` | Manual diagnostic workflow for WP auth testing | 52 lines | Rarely |

---

## Architecture & Data Flow

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Actions Scheduler                 │
│              (Runs 4x daily: 00:30, 06:30, 12:30, 18:30 UTC)│
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      job_scraper.py                          │
│  1. Load config.yaml + posted_jobs.json (dedup)              │
│  2. Determine continent (auto-rotate by weekday or PROCESS_CONTINENT)│
│  3. For each continent → country → locale:                   │
│     - Query enabled sources (jsearch, remotive, remoteok...) │
│     - Rate limit between sources (pause_seconds + jitter)    │
│     - Collect candidate jobs                                 │
│  4. For each job:                                            │
│     - Check dedup (hash already seen?)                       │
│     - Classify (AI keywords: role, seniority, remote/onsite) │
│     - Fetch company logo (Clearbit)                          │
│     - Upload logo to WP media                                │
│     - Post to WordPress (REST API)                           │
│     - Add hash to dedup list                                 │
│  5. Prune old dedup entries (>60 days)                       │
│  6. Save posted_jobs.json                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               WordPress Job Board (WP Job Manager)           │
│          - Receives jobs via REST API (WP_URL)               │
│          - Auth: WP_USERNAME + WP_APP_PASSWORD               │
│          - Jobs posted with tags, featured media, content    │
└─────────────────────────────────────────────────────────────┘
```

### Continent Auto-Rotation Logic

The scraper uses **weekday-based continent rotation** (configurable via `auto_rotate` in config.yaml):

| Weekday | Continent | Example Queries |
|---------|-----------|-----------------|
| Monday | Asia | Bengaluru, Mumbai, Tokyo, Singapore, Dubai |
| Tuesday | Europe | London, Berlin, Paris, Amsterdam, Dublin |
| Wednesday | North America | San Francisco, New York, Seattle, Toronto |
| Thursday | South America | Sao Paulo, Buenos Aires, Bogota |
| Friday | Africa | Lagos, Cape Town, Nairobi, Cairo |
| Saturday | Oceania | Sydney, Melbourne, Auckland |
| Sunday | Antarctica | Antarctica Base (researcher) |

**Override**: Set `PROCESS_CONTINENT` env var to process a specific continent only.

---

## Key Components & Functions

### 1. Configuration Management (Lines 57-122)

```python
load_config()        # Loads config.yaml (sources, continents, posting, dedup)
load_dedup()         # Loads posted_jobs.json, normalizes to list of dicts
save_dedup(entries)  # Saves dedup list to posted_jobs.json
prune_dedup(dedup_list, max_age_days)  # Removes entries older than N days
```

**Dedup Format** (posted_jobs.json):
```json
[
  {
    "hash": "d2d2f0a8f9e6c3a1f5b8d4c3a1e7f2b4a1b2c3d4",
    "title": "Senior Backend Engineer",
    "company": "Acme Cloud",
    "location": "San Francisco, United States",
    "url": "https://acme.example/jobs/123",
    "first_seen": 1760956800
  }
]
```

### 2. HTTP Request Handling (Lines 126-141)

```python
http_request(method, url, **kwargs)
# - Retries: 4 attempts with exponential backoff (1s, 2s, 4s, 8s)
# - Sets User-Agent: "TechJobs360Scraper-final (+https://techjobs360.com)"
# - Timeout: 20 seconds per request
```

### 3. Job Source Integrations (Lines 146-349)

| Function | Source | Type | Rate | Notes |
|----------|--------|------|------|-------|
| `query_jsearch()` | JSearch API (RapidAPI) | JSON API | Paid | Requires JSEARCH_API_KEY |
| `query_remotive()` | Remotive.com | JSON API | Free | Limit: 50 jobs |
| `query_remoteok()` | RemoteOK.com | JSON API | Free | Limit: 80 jobs |
| `parse_weworkremotely()` | WeWorkRemotely | HTML Parse | Free | Limit: 30 jobs |
| `parse_indeed()` | Indeed | HTML Parse | Free (cautious) | Disabled by default |
| `parse_linkedin()` | LinkedIn | HTML Parse | Free (cautious) | Disabled by default |

**Return Format** (all sources normalized to):
```python
{
  "id": "...",              # Unique job ID (or None)
  "title": "...",           # Job title
  "company": "...",         # Company name
  "location": "...",        # City/country
  "description": "...",     # Job description HTML/text
  "url": "...",             # Apply link
  "raw": {...}              # Original API response
}
```

### 4. Logo Fetching & Media Upload (Lines 354-377)

```python
fetch_logo(domain)                           # Fetches logo from Clearbit API
upload_media_to_wp(image_bytes, filename)    # Uploads to WP /wp-json/wp/v2/media
# - Thumbnails logo to max 600x600px
# - Returns media_id for use as featured_media in posts
```

### 5. WordPress Posting (Lines 382-421)

```python
post_to_wp(job, continent_id, country_code, posting_cfg)
# - Endpoint: WP_URL/wp-json/wp/v2/posts
# - Auth: Basic (WP_USERNAME:WP_APP_PASSWORD)
# - Generates slug from title+company+location
# - Adds tags: ["tech", "jobs", "auto-scraped", "continent:asia", "country:IN", "role:backend", "seniority:senior", "remote"]
# - Status: "publish" or "draft" (from posting.post_status in config.yaml)
# - Returns post_id or None on failure
```

### 6. AI Job Classification (Lines 426-459)

```python
classify_job(title, description)
# Returns: {"seniority": "senior|mid|junior|unspecified",
#           "role": "backend|frontend|fullstack|data|devops|mobile|qa|other",
#           "work_type": "remote|onsite",
#           "skills": ["python", "react", ...]}
# - Keyword-based classification (no external ML API)
# - SENIORITY_KEYWORDS: senior, lead, principal, staff, mid, junior, entry, associate
# - ROLE_KEYWORDS: backend, frontend, fullstack, data, devops, mobile, qa
# - Remote detection: "remote", "work from home"
```

### 7. Main Orchestration (Lines 464-629)

```python
main()
# 1. Load config + dedup
# 2. Prune old dedup entries (max_age_days from config.yaml)
# 3. Determine continents to process (PROCESS_CONTINENT env or auto-rotate)
# 4. For each continent → country → locale:
#    - Query all enabled sources (with rate limiting)
#    - Dedup + classify + fetch logo + post to WP
# 5. Save updated dedup file
# 6. Log: "Run complete. New jobs posted: N"
```

---

## Configuration System (config.yaml)

### Global Settings

```yaml
global:
  default_per_page: 20      # Default jobs per page (jsearch)
  fallback_per_page: 10     # Fallback if API fails
  auto_rotate: true         # Rotate continents by weekday (Mon=Asia, Tue=Europe, etc.)
```

### Sources Configuration

```yaml
sources:
  - type: jsearch            # RapidAPI JSearch (requires JSEARCH_API_KEY)
    enabled: true

  - type: remotive           # Remotive.com free API
    enabled: true
    limit: 60

  - type: remoteok           # RemoteOK.com free API
    enabled: true
    limit: 80

  - type: weworkremotely     # WeWorkRemotely HTML parse
    enabled: true
    limit: 40

  - type: indeed             # Indeed HTML parse (cautious)
    enabled: true
    enabled_html: false      # Set true to enable HTML scraping

  - type: linkedin           # LinkedIn HTML parse (may require login)
    enabled: true
    enabled_html: false      # Set true to enable HTML scraping

  - type: html               # Custom HTML endpoint
    enabled: false
    endpoint: "https://example.com/search?q={query}&city={city}"
    limit: 10
```

**Best Practice**: Keep `enabled_html: false` for Indeed/LinkedIn unless you have consent/authorization.

### Deduplication Settings

```yaml
dedup:
  max_age_days: 60          # Remove dedup entries older than 60 days
```

### Posting Configuration

```yaml
posting:
  post_status: publish      # "publish" for live posts, "draft" for testing
  tags:
    - tech
    - jobs
    - auto-scraped
```

### Continent/Country/Locale Structure

```yaml
continents:
  - id: asia                # Unique continent identifier
    name: Asia              # Display name
    pause_seconds: 2        # Rate limit delay between requests
    countries:
      - code: IN            # ISO country code
        name: India         # Display name
        locales:
          - city: Bengaluru         # City name
            query: software engineer # Search query
          - city: Mumbai
            query: frontend developer
```

**Total Coverage**: 7 continents, 20+ countries, 50+ cities with targeted queries.

---

## Deduplication & Data Management

### Deduplication Strategy

1. **Hash Generation**: `SHA1(job_id or job_url or job_title)`
2. **Storage**: posted_jobs.json (list of dicts with hash, title, company, location, url, first_seen)
3. **Check**: Before posting, check if hash exists in dedup list
4. **Pruning**: Remove entries older than `max_age_days` (default: 60 days)

### Legacy Compatibility

The scraper handles two dedup formats:
- **Legacy**: List of strings (hashes only)
- **Current**: List of dicts with metadata

When loading, legacy format is auto-converted to current format.

### Pruning Logic (job_scraper.py:104-121)

```python
cutoff = int((datetime.utcnow() - timedelta(days=max_age_days)).timestamp())
kept = [e for e in dedup_list if int(e.get("first_seen", 0) or 0) >= cutoff]
```

**Result**: Old jobs are removed from dedup, allowing them to be re-posted after 60 days.

---

## Environment Variables

### Required Variables

| Variable | Purpose | Example | Where Set |
|----------|---------|---------|-----------|
| `WP_URL` | WordPress site URL | `https://techjobs360.com` | GitHub Secrets |
| `WP_USERNAME` | WordPress username | `admin` | GitHub Secrets |
| `WP_APP_PASSWORD` | WordPress Application Password | `xxxx xxxx xxxx xxxx` | GitHub Secrets |

### Optional Variables

| Variable | Purpose | Default | Example |
|----------|---------|---------|---------|
| `JSEARCH_API_KEY` | RapidAPI JSearch key | None (disables jsearch) | `abcd1234...` |
| `PROCESS_CONTINENT` | Process only specific continent | None (uses auto_rotate) | `asia`, `europe`, `north_america` |
| `AUTO_ROTATE` | Enable weekday-based rotation | `true` | `true`, `false`, `1`, `0` |

### Setting Secrets in GitHub

1. Go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Add: `WP_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`, `JSEARCH_API_KEY`

---

## CI/CD Workflows

### 1. scraper.yml (Main Workflow)

**Trigger**:
- Push to `main` branch
- Manual dispatch (`workflow_dispatch`)
- **Schedule**: `cron: '30 0,6,12,18 * * *'` (4x daily at UTC 00:30, 06:30, 12:30, 18:30)

**Steps**:
1. Checkout repository
2. Set up Python 3.11
3. Install dependencies (`pip install -r requirements.txt`)
4. Run scraper (`python job_scraper.py`)
5. Commit and push `posted_jobs.json` if changed
   - Uses git config for "GitHub Actions Bot"
   - Fetches/rebases to avoid conflicts
   - Pushes to `main`

**Concurrency**: `cancel-in-progress: true` (prevents overlapping runs)

**Timeout**: 60 minutes

### 2. diag-auth.yml (Diagnostic Workflow)

**Trigger**: Manual dispatch only (`workflow_dispatch`)

**Purpose**: Test WordPress authentication without running full scraper

**Steps**:
1. Validate secrets exist (`WP_USERNAME`, `WP_APP_PASSWORD`)
2. Test auth: `curl -u "$WP_USERNAME:$WP_APP_PASSWORD" "$WP_BASE_URL/wp-json/wp/v2/users/me"`
3. Report success/failure with actionable messages

**Use Case**: Debug WP auth issues before running full workflow.

---

## Development Guidelines

### Working with This Codebase

#### 1. Adding a New Job Source

**Steps**:
1. Add source function in `job_scraper.py` (follow pattern of `query_remotive()`)
2. Return normalized dict: `{"id", "title", "company", "location", "description", "url", "raw"}`
3. Add source to `config.yaml` under `sources:`
4. Add source call in `main()` around line 520-558

**Example**:
```python
def query_new_source(query: str, limit: int = 50) -> List[Dict]:
    try:
        url = "https://newsource.com/api/jobs"
        resp = http_request("GET", url, params={"q": query})
        if resp.status_code != 200:
            return []
        data = resp.json()
        jobs = []
        for item in data.get("jobs", [])[:limit]:
            jobs.append({
                "id": item.get("id"),
                "title": item.get("title"),
                "company": item.get("company"),
                "location": item.get("location"),
                "description": item.get("description"),
                "url": item.get("url"),
                "raw": item
            })
        return jobs
    except Exception as e:
        logger.warning("New source query failed: %s", e)
        return []
```

#### 2. Modifying Continent/City Coverage

**Edit config.yaml**:
```yaml
continents:
  - id: new_continent
    name: New Continent
    pause_seconds: 2
    countries:
      - code: XX
        name: New Country
        locales:
          - city: New City
            query: backend engineer
```

**Best Practices**:
- Use ISO country codes (US, IN, UK, DE, etc.)
- Use specific queries per city (not just "engineer")
- Adjust `pause_seconds` based on API rate limits (2-5 seconds recommended)

#### 3. Adjusting Classification Keywords

**Edit job_scraper.py** (lines 426-439):
```python
SENIORITY_KEYWORDS = {
    "senior": ["senior", "lead", "principal", "sr.", "staff"],
    "mid": ["mid", "experienced"],
    "junior": ["junior", "jr.", "entry", "associate", "graduate"]
}

ROLE_KEYWORDS = {
    "backend": ["backend", "java", "golang", "python", "ruby", "node"],
    "frontend": ["frontend", "react", "angular", "vue", "javascript"],
    # Add more keywords...
}
```

#### 4. Testing Locally

```bash
# Set environment variables
export WP_URL="https://techjobs360.com"
export WP_USERNAME="your_username"
export WP_APP_PASSWORD="your_app_password"
export JSEARCH_API_KEY="your_jsearch_key"  # Optional
export PROCESS_CONTINENT="asia"  # Optional: test specific continent
export AUTO_ROTATE="false"  # Optional: disable auto-rotation

# Install dependencies
pip install -r requirements.txt

# Run scraper
python job_scraper.py
```

**Dry Run Testing**: Set `post_status: draft` in config.yaml to avoid publishing live jobs.

#### 5. Debugging Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Missing config.yaml" | File not in repo root | Ensure config.yaml exists in same directory as job_scraper.py |
| "Missing WP credentials" | Env vars not set | Set WP_URL, WP_USERNAME, WP_APP_PASSWORD |
| "JSearch returned 403" | Invalid API key | Check JSEARCH_API_KEY in GitHub Secrets |
| "No new jobs to commit" | All jobs already in dedup | Normal - means no new jobs found |
| "Auth test failed (HTTP 401)" | Invalid WP credentials | Regenerate Application Password in WordPress |
| "Request timeout" | Network/API issue | Check API endpoint availability, increase REQUESTS_TIMEOUT |

---

## AI Assistant Guidelines

### When Modifying This Codebase

#### DO:
- **Read config.yaml first** before making changes to scraper logic
- **Test auth** with `diag-auth.yml` workflow before running full scraper
- **Use descriptive commit messages** (e.g., "Add support for NewAPI source", "Fix dedup pruning bug")
- **Preserve rate limiting** (pause_seconds, random jitter) to avoid bans
- **Keep User-Agent descriptive** for ethical scraping
- **Log errors with context** (`logger.warning("Source X failed for query=%r: %s", query, e)`)
- **Return empty list on failure** (don't crash scraper if one source fails)
- **Normalize all sources** to same dict format before processing

#### DON'T:
- **Remove rate limiting** or aggressive scraping (violates TOS)
- **Commit secrets** (API keys, passwords) to repo
- **Break dedup format** (always maintain hash + metadata)
- **Post to production immediately** (use draft status for testing)
- **Remove attribution** (required by data providers)
- **Enable HTML scrapers by default** (cautious approach)

### Code Style Conventions

1. **Functions**: Use snake_case (`query_remotive()`, `fetch_logo()`)
2. **Variables**: Use snake_case (`total_new`, `continent_id`)
3. **Constants**: Use UPPER_CASE (`REQUESTS_TIMEOUT`, `USER_AGENT`)
4. **Logging**: Use logger (not print): `logger.info()`, `logger.warning()`, `logger.error()`
5. **Type Hints**: Use where helpful: `def query_jsearch(query: str, location: Optional[str] = None) -> List[Dict]`
6. **Docstrings**: Triple-quoted at top of file for module-level docs

### Testing New Features

1. **Local Testing**:
   ```bash
   export PROCESS_CONTINENT="antarctica"  # Small continent for testing
   export AUTO_ROTATE="false"
   python job_scraper.py
   ```

2. **Dry Run** (config.yaml):
   ```yaml
   posting:
     post_status: draft  # Jobs posted as drafts, not published
   ```

3. **Diagnostic Workflow**:
   ```bash
   # In GitHub Actions tab, run "Diagnose WP auth & workflow setup"
   # Verifies WP credentials without running full scraper
   ```

### Common Modification Patterns

#### Pattern 1: Add New Source
1. Write `query_new_source()` function
2. Add to `config.yaml` → `sources:`
3. Add `elif stype == "new_source":` in main loop (line ~520)
4. Test with `PROCESS_CONTINENT="antarctica"` (smallest dataset)

#### Pattern 2: Enhance Job Enrichment
1. Locate `for job in candidate_jobs:` loop (line ~564)
2. Add enrichment logic before `post_to_wp()` call
3. Example: fetch salary data, extract skills, call external API

#### Pattern 3: Modify Classification
1. Edit `SENIORITY_KEYWORDS` or `ROLE_KEYWORDS` (lines 426-439)
2. Or replace `classify_job()` with ML-based classifier
3. Ensure return format: `{"seniority", "role", "work_type", "skills"}`

#### Pattern 4: Change Posting Format
1. Modify `post_to_wp()` function (lines 382-421)
2. Adjust `content` HTML structure
3. Add/remove tags in `payload["tags"]`

---

## Compliance & Ethics

### Data Privacy
- **No personal data**: Only public job listings (title, company, location, description)
- **No user tracking**: No personal emails, resumes, or candidate data
- **Source attribution**: Always include "Powered by [Source]" in posts

### Rate Limiting
- **pause_seconds**: Configurable delay between requests (default: 2s)
- **Random jitter**: `time.sleep(base_pause + random.random() * base_pause)`
- **Retry backoff**: Exponential backoff for failed requests (1s, 2s, 4s, 8s)
- **Concurrent requests**: Never parallel requests to same source

### Terms of Service
- **RapidAPI**: Requires API key, rate limits apply
- **Free APIs**: Respect robots.txt, use polite User-Agent
- **HTML scraping**: Disabled by default for Indeed/LinkedIn (enable only with authorization)

---

## Troubleshooting

### Workflow Failures

**Symptom**: GitHub Action fails with "Auth test failed"
**Cause**: Invalid WP_APP_PASSWORD or expired
**Solution**:
1. Log into WordPress as admin
2. Go to Users → Profile → Application Passwords
3. Generate new password
4. Update `WP_APP_PASSWORD` secret in GitHub

**Symptom**: "No new jobs posted" every run
**Cause**: All jobs already in dedup, or sources returning no results
**Solution**:
1. Check source APIs are online
2. Verify `enabled: true` in config.yaml
3. Clear `posted_jobs.json` for fresh run (CAUTION: will repost all jobs)

**Symptom**: "Request timeout" errors
**Cause**: Network issue or slow API
**Solution**: Increase `REQUESTS_TIMEOUT` in job_scraper.py (line 48)

### Local Development Issues

**Symptom**: "Missing WP credentials"
**Cause**: Environment variables not set
**Solution**: `export WP_URL=...`, `export WP_USERNAME=...`, `export WP_APP_PASSWORD=...`

**Symptom**: "ImportError: No module named 'yaml'"
**Cause**: Dependencies not installed
**Solution**: `pip install -r requirements.txt`

**Symptom**: Logo upload fails
**Cause**: Clearbit API down or domain not found
**Solution**: Logo fetch is non-blocking; scraper continues without logo

---

## Quick Reference

### Key Files

- **job_scraper.py**: Main script (630 lines)
- **config.yaml**: Configuration (sources, continents, posting)
- **posted_jobs.json**: Dedup database (auto-updated)
- **.github/workflows/scraper.yml**: Scheduled workflow

### Key Functions

- `load_config()` → Dict
- `load_dedup()` → List[Dict]
- `query_jsearch(query, location)` → List[Dict]
- `query_remotive(query)` → List[Dict]
- `post_to_wp(job, continent_id, country_code, posting_cfg)` → int|None
- `classify_job(title, description)` → Dict

### Environment Variables

- `WP_URL`, `WP_USERNAME`, `WP_APP_PASSWORD` (required)
- `JSEARCH_API_KEY` (optional)
- `PROCESS_CONTINENT` (optional)
- `AUTO_ROTATE` (optional)

### Testing Commands

```bash
# Test auth
gh workflow run diag-auth.yml

# Run scraper manually
gh workflow run scraper.yml

# Test locally (specific continent)
export PROCESS_CONTINENT="antarctica" && python job_scraper.py
```

### Workflow Schedule

- **00:30 UTC** (06:00 IST) - Morning run
- **06:30 UTC** (12:00 IST) - Noon run
- **12:30 UTC** (18:00 IST) - Evening run
- **18:30 UTC** (00:00 IST) - Midnight run

---

## Version History

- **Current**: Multi-source scraper with auto-rotation, classification, logo fetch
- **Recent Changes**:
  - Added continent auto-rotation by weekday
  - Enhanced deduplication with pruning
  - Added diagnostic workflow for auth testing
  - Improved error handling and logging

---

## Additional Resources

- **JSearch API Docs**: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/
- **WordPress REST API**: https://developer.wordpress.org/rest-api/
- **WP Job Manager**: https://wpjobmanager.com/
- **Clearbit Logo API**: https://clearbit.com/logo

---

*This CLAUDE.md file is maintained for AI assistants working with this codebase. Last updated: 2025-11-21*
