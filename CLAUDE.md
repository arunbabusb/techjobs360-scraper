# CLAUDE.md - TechJobs360 Scraper

## Repository Overview

**TechJobs360 Scraper** is an automated Python-based job aggregator that scrapes tech jobs from multiple sources (both free APIs and HTML scraping) and publishes them to a WordPress job board using the WP Job Manager plugin.

### Primary Purpose
- Aggregate tech jobs from 8+ different sources globally
- Deduplicate job postings to avoid duplicates
- Enrich jobs with company logos and salary data
- Auto-classify jobs by role, seniority, and work type
- Post jobs to WordPress via REST API
- Run on a schedule (4x daily via GitHub Actions)

### Tech Stack
- **Language**: Python 3.11
- **Key Libraries**: requests, BeautifulSoup4, PyYAML, Pillow, python-slugify
- **APIs**: JSearch (RapidAPI), Remotive, RemoteOK, WeWorkRemotely
- **CI/CD**: GitHub Actions
- **Storage**: WordPress (via REST API), JSON dedup file

---

## Repository Structure

```
techjobs360-scraper/
├── job_scraper.py          # Main scraper script (630 lines)
├── config.yaml             # Configuration for sources, continents, locales
├── posted_jobs.json        # Deduplication database (job hashes)
├── requirements.txt        # Python dependencies
├── README.md               # User-facing documentation
├── CLAUDE.md               # This file - AI assistant guide
└── .github/
    └── workflows/
        ├── scraper.yml     # Main scraper workflow (runs 4x daily)
        └── diag-auth.yml   # WordPress auth diagnostic workflow
```

---

## Core Components

### 1. job_scraper.py
**Location**: `/home/user/techjobs360-scraper/job_scraper.py`

**Main Functions**:
- `load_config()` - Loads config.yaml (line 57)
- `load_dedup()` / `save_dedup()` - Manages posted_jobs.json (lines 64-102)
- `prune_dedup()` - Removes old entries beyond max_age_days (line 104)
- `http_request()` - HTTP wrapper with retry/backoff logic (line 126)
- `query_jsearch()` - RapidAPI JSearch integration (line 146)
- `query_remotive()` - Remotive API (line 184)
- `query_remoteok()` - RemoteOK API (line 212)
- `parse_weworkremotely()` - HTML scraper (line 251)
- `parse_indeed()` - HTML scraper (line 286, disabled by default)
- `parse_linkedin()` - HTML scraper (line 321, disabled by default)
- `fetch_logo()` - Clearbit logo fetcher (line 354)
- `upload_media_to_wp()` - WordPress media upload (line 366)
- `post_to_wp()` - WordPress job post creation (line 382)
- `classify_job()` - Keyword-based job classification (line 441)
- `pick_continent_by_weekday()` - Auto-rotation logic (line 464)
- `main()` - Orchestrates entire scraping flow (line 473)

**Key Design Patterns**:
- Modular source functions (easy to add/remove sources)
- Polite rate limiting with configurable pauses
- Robust error handling (continues on source failures)
- Deduplication using SHA-1 hashes
- Auto-classification using keyword matching

### 2. config.yaml
**Location**: `/home/user/techjobs360-scraper/config.yaml`

**Structure**:
```yaml
global:
  default_per_page: 20
  auto_rotate: true      # Rotate continents by weekday

sources:                 # Enable/disable sources here
  - type: jsearch
    enabled: true
  - type: remotive
    enabled: true
    limit: 60
  # ... 8 more sources

dedup:
  max_age_days: 60       # Prune old entries after 60 days

posting:
  post_status: publish   # 'draft' or 'publish'
  tags:
    - tech
    - jobs
    - auto-scraped

continents:              # 6 continents, 20+ countries, 80+ cities
  - id: africa
    name: Africa
    pause_seconds: 2
    countries:
      - code: NG
        name: Nigeria
        locales:
          - city: Lagos
            query: software engineer
```

**Important Notes**:
- Each locale has a `city` and `query` pair
- `pause_seconds` controls rate limiting per continent
- Sources can be toggled with `enabled: true/false`
- HTML scrapers (Indeed, LinkedIn) require `enabled_html: true`

### 3. posted_jobs.json
**Location**: `/home/user/techjobs360-scraper/posted_jobs.json`

**Purpose**: Deduplication database tracking previously posted jobs

**Format**:
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

**Hash Generation**: SHA-1 of job ID or URL or title (line 569)
**Pruning**: Automatically removes entries older than `max_age_days` (line 104)

---

## Data Flow

### Scraping Workflow

1. **Load Configuration** (`main()` line 474)
   - Load config.yaml
   - Load posted_jobs.json
   - Prune old dedup entries

2. **Continent Selection** (lines 487-499)
   - If `PROCESS_CONTINENT` env var set → filter to that continent
   - If `auto_rotate` enabled → pick continent by weekday (Monday=Asia, Tuesday=Europe, etc.)
   - Otherwise → process all continents

3. **Iterate Through Locales** (lines 502-561)
   ```
   For each continent:
     For each country:
       For each locale (city + query):
         Query all enabled sources
         Pause between sources (rate limiting)
   ```

4. **Job Processing** (lines 564-614)
   ```
   For each job:
     Generate hash from ID/URL/title
     Skip if already in dedup list
     Classify job (role, seniority, work_type)
     Fetch company logo (Clearbit)
     Upload logo to WordPress media
     Post job to WordPress
     Add to dedup list
   ```

5. **Persist Dedup** (lines 618-623)
   - Save updated posted_jobs.json
   - GitHub Actions commits changes back to repo

### Job Classification

**Location**: `classify_job()` at line 441

**Classification Categories**:
- **Seniority**: senior, mid, junior, unspecified
- **Role**: backend, frontend, fullstack, data, devops, mobile, qa, other
- **Work Type**: remote, onsite
- **Skills**: Extracted keywords (max 6)

**Method**: Simple keyword matching against predefined dictionaries (lines 426-439)

---

## Environment Variables

### Required (set in GitHub Secrets)

| Variable | Description | Example |
|----------|-------------|---------|
| `WP_URL` | WordPress site URL | `https://techjobs360.com` |
| `WP_USERNAME` | WordPress username | `admin` |
| `WP_APP_PASSWORD` | WordPress application password | `xxxx xxxx xxxx xxxx` |
| `JSEARCH_API_KEY` | RapidAPI JSearch key (optional) | `xxxxxxxxxxxxxxxx` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `PROCESS_CONTINENT` | Filter to specific continent | (none - all continents) |
| `AUTO_ROTATE` | Enable weekday rotation | `true` |

**Setting Secrets**: GitHub repo → Settings → Secrets and variables → Actions

---

## GitHub Actions

### Main Scraper Workflow
**File**: `.github/workflows/scraper.yml`

**Triggers**:
- Push to `main` branch
- Manual dispatch
- Schedule: `0,6,12,18 hours` (4x daily)

**Steps**:
1. Checkout repository
2. Set up Python 3.11
3. Install dependencies from requirements.txt
4. Run job_scraper.py with environment variables
5. Commit and push posted_jobs.json if changed

**Concurrency**: Only one run at a time (prevents overlapping jobs)

**Timeout**: 60 minutes

### Diagnostic Workflow
**File**: `.github/workflows/diag-auth.yml`

**Purpose**: Test WordPress authentication without running full scraper

**Triggers**: Manual dispatch only

**Steps**:
1. Validate secrets exist
2. Test WordPress REST API auth (GET /wp/v2/users/me)
3. Report success or failure

**Usage**: Run this if scraper fails with auth errors

---

## Development Workflow

### Local Setup

1. **Clone repository**:
   ```bash
   git clone https://github.com/arunbabusb/techjobs360-scraper.git
   cd techjobs360-scraper
   ```

2. **Set up environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   export WP_URL="https://your-site.com"
   export WP_USERNAME="your-username"
   export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
   export JSEARCH_API_KEY="your-rapidapi-key"  # Optional
   ```

4. **Run scraper**:
   ```bash
   python job_scraper.py
   ```

### Testing Individual Sources

To test a specific source without running the full scraper, you can use Python REPL:

```python
from job_scraper import query_remotive, query_remoteok, parse_weworkremotely

# Test Remotive
jobs = query_remotive("python developer", limit=10)
print(f"Found {len(jobs)} jobs from Remotive")

# Test RemoteOK
jobs = query_remoteok("backend", limit=10)
print(f"Found {len(jobs)} jobs from RemoteOK")
```

### Testing WordPress Integration

1. **Test auth** (without posting):
   ```python
   import os
   import requests

   wp_url = os.environ.get("WP_URL")
   wp_user = os.environ.get("WP_USERNAME")
   wp_pass = os.environ.get("WP_APP_PASSWORD")

   resp = requests.get(
       f"{wp_url}/wp-json/wp/v2/users/me",
       auth=(wp_user, wp_pass)
   )
   print(resp.status_code, resp.json())
   ```

2. **Test with draft posts**:
   - Set `posting.post_status: draft` in config.yaml
   - Run scraper
   - Check WordPress admin for draft posts

### Testing Continent Filtering

To test a specific continent:
```bash
export PROCESS_CONTINENT="asia"
python job_scraper.py
```

Or edit config.yaml temporarily to keep only one continent.

---

## Key Conventions

### Code Style
- **Line Length**: ~100 chars (not strict)
- **Indentation**: 4 spaces
- **Naming**: snake_case for functions/variables
- **Comments**: Inline for complex logic, section headers for major blocks
- **Error Handling**: Try-except with logging, continue on failures

### Logging
- **Level**: INFO for main flow, WARNING for recoverable errors, ERROR for critical failures
- **Format**: `%(asctime)s %(levelname)s %(message)s`
- **Logger**: `logger = logging.getLogger("techjobs360")`

### HTTP Requests
- **Always use**: `http_request()` wrapper (not raw `requests.*`)
- **Timeout**: 20 seconds (configurable via REQUESTS_TIMEOUT)
- **Retries**: 4 attempts with exponential backoff
- **User-Agent**: "TechJobs360Scraper-final (+https://techjobs360.com)"

### Rate Limiting
- **Between sources**: `pause_seconds` + random jitter (line 561)
- **Between locales**: Same pause (line 616)
- **Purpose**: Avoid overwhelming source APIs

### Deduplication
- **Hash key**: job ID → URL → title (in order of preference)
- **Algorithm**: SHA-1 hexdigest
- **Storage**: JSON file with metadata (title, company, location, url, first_seen)
- **Pruning**: Automatic based on `max_age_days`

---

## Common Tasks

### Adding a New Job Source

1. **Create source function** in job_scraper.py:
   ```python
   def query_newsource(query: str, limit: int = 30) -> List[Dict]:
       try:
           url = "https://api.newsource.com/jobs"
           resp = http_request("GET", url, params={"q": query})
           jobs = []
           for item in resp.json().get("jobs", []):
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
           logger.warning("NewsSource failed: %s", e)
           return []
   ```

2. **Add to config.yaml**:
   ```yaml
   sources:
     - type: newsource
       enabled: true
       limit: 30
   ```

3. **Add to main loop** (around line 524):
   ```python
   elif stype == "newsource":
       candidate_jobs += query_newsource(qtext, limit=src.get("limit", 30))
   ```

### Adding a New Continent/Country/City

Edit config.yaml:
```yaml
continents:
  - id: europe
    name: Europe
    pause_seconds: 2
    countries:
      - code: ES
        name: Spain
        locales:
          - city: Madrid
            query: frontend developer
          - city: Barcelona
            query: backend engineer
```

### Changing Scraper Schedule

Edit `.github/workflows/scraper.yml`:
```yaml
schedule:
  - cron: '0 */4 * * *'  # Every 4 hours
```

Cron format: `minute hour day month weekday`

### Disabling a Source

In config.yaml:
```yaml
sources:
  - type: indeed
    enabled: false  # Change to false
```

### Changing Post Status (Draft vs Publish)

In config.yaml:
```yaml
posting:
  post_status: draft  # or 'publish'
```

### Clearing Dedup Cache

```bash
# Backup first
cp posted_jobs.json posted_jobs.backup.json

# Clear (or edit to remove specific entries)
echo "[]" > posted_jobs.json
```

---

## Troubleshooting

### "Missing config.yaml"
- Ensure config.yaml exists in repository root
- Check file permissions (should be readable)

### "Missing WP credentials; cannot post"
- Set environment variables: `WP_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`
- Verify secrets are set in GitHub Actions
- Run diagnostic workflow to test auth

### "JSearch returned 403 for X/Y"
- Check `JSEARCH_API_KEY` is valid
- Verify RapidAPI subscription is active
- Check rate limits on RapidAPI dashboard

### "WP media upload failed"
- Check WordPress user has `upload_files` capability
- Verify WordPress REST API is enabled
- Check image size (should be < 5MB after thumbnail)

### Jobs not appearing on WordPress
- Check `posting.post_status` in config.yaml (draft vs publish)
- Verify WordPress taxonomies exist (WP Job Manager categories)
- Check WordPress admin → Posts for draft posts

### GitHub Actions failing with "non-fast-forward push"
- Workflow includes rebase logic (lines 64-71 of scraper.yml)
- If persistent, check for concurrent runs (should be prevented by concurrency group)

### Duplicate jobs appearing
- Check dedup hash generation (line 569)
- Verify posted_jobs.json is being committed back to repo
- Ensure GitHub Actions has write permissions

### Rate limiting / API throttling
- Increase `pause_seconds` in config.yaml for affected continent
- Reduce number of locales per country
- Disable high-volume sources temporarily

---

## AI Assistant Guidelines

### When Modifying Code

1. **Always read first**: Read job_scraper.py before making changes
2. **Preserve structure**: Keep existing function signatures and flow
3. **Test locally**: Encourage user to test changes locally before pushing
4. **Update config**: If adding sources, update both code and config.yaml
5. **Maintain logging**: Use `logger.info/warning/error` consistently
6. **Handle errors**: Wrap external API calls in try-except
7. **Document changes**: Add inline comments for non-obvious logic

### When Debugging Issues

1. **Check logs first**: GitHub Actions logs show detailed output
2. **Isolate source**: Disable all sources except one to identify culprit
3. **Test auth separately**: Use diag-auth.yml workflow
4. **Verify config**: Check config.yaml syntax (YAML is whitespace-sensitive)
5. **Check dedup file**: Verify posted_jobs.json is valid JSON

### When Adding Features

1. **Consider config-driven**: Can it be toggled in config.yaml?
2. **Maintain backwards compatibility**: Don't break existing config
3. **Add logging**: Log new feature activity at INFO level
4. **Update this file**: Add documentation to CLAUDE.md
5. **Test edge cases**: What if API fails? What if no results?

### Code Quality Standards

- **Readability over cleverness**: Simple, clear code > complex optimizations
- **Fail gracefully**: Log warnings, continue processing other sources
- **DRY principle**: Extract common logic into functions
- **Type hints**: Use where helpful (already used in function signatures)
- **Configuration over code**: Prefer config.yaml settings over hardcoded values

### Git Workflow

- **Branch naming**: Use descriptive names (e.g., `feature/add-stackoverflow-source`)
- **Commit messages**: Clear, imperative mood (e.g., "Add StackOverflow job source")
- **Don't commit secrets**: Never commit API keys or passwords
- **Test before merge**: Ensure GitHub Actions passes before merging to main

---

## Architecture Decisions

### Why Python?
- Rich ecosystem for web scraping (BeautifulSoup, requests)
- Easy to deploy (single-file script)
- GitHub Actions has excellent Python support

### Why WordPress REST API?
- Mature, well-documented API
- Built-in authentication (Application Passwords)
- No need for custom backend

### Why JSON dedup file?
- Simple, human-readable
- Easy to version control
- No database required
- Works well with GitHub Actions

### Why config.yaml?
- Easy to edit (even for non-developers)
- Structured data with validation
- Separates config from code

### Why GitHub Actions?
- Free for public repos
- Scheduled jobs built-in
- Easy secret management
- Automatic git operations

### Why multiple sources?
- Redundancy (if one source fails, others continue)
- Better job coverage
- Free sources reduce API costs

---

## Performance Characteristics

### Scraper Runtime
- **Average**: 15-30 minutes per full run
- **Factors**: Number of locales, sources enabled, pause_seconds
- **Bottleneck**: Rate limiting (intentional, polite scraping)

### API Rate Limits
- **JSearch**: 500-1000 requests/month (depends on plan)
- **Remotive**: No official limit (polite scraping recommended)
- **RemoteOK**: No official limit (includes 1-request API)
- **WeWorkRemotely**: HTML scraping (be polite)

### Memory Usage
- **Typical**: < 100 MB
- **Peak**: ~200 MB (with image processing)
- **GitHub Actions limit**: 7 GB (well within limits)

### Storage
- **posted_jobs.json**: ~50 KB per 100 jobs
- **Expected growth**: ~500 KB per month (with pruning)

---

## Security Considerations

### Secrets Management
- **Never commit**: WP_APP_PASSWORD, JSEARCH_API_KEY
- **Use GitHub Secrets**: Encrypted at rest, masked in logs
- **Rotate regularly**: Change WP Application Password every 90 days

### WordPress Permissions
- **Minimum required**: `edit_posts`, `upload_files`, `publish_posts`
- **Recommended**: Create dedicated "scraper" user with limited permissions
- **Avoid**: Using admin account for scraper

### HTML Scraping
- **Respect robots.txt**: Always check before scraping
- **Rate limiting**: Use pause_seconds to be polite
- **Terms of Service**: Verify scraping is allowed (Indeed, LinkedIn may prohibit)

### Input Validation
- **Job descriptions**: Already HTML-escaped by WordPress
- **URLs**: Validated before posting
- **Images**: Thumbnail + size limits prevent DoS

---

## Future Enhancements

### Potential Improvements
1. **Database backend**: Replace JSON with SQLite/PostgreSQL
2. **Web UI**: Admin panel for config.yaml editing
3. **Email notifications**: Alert on failures or new jobs
4. **Advanced classification**: ML-based role/seniority detection
5. **More sources**: Add Glassdoor, Monster, Stack Overflow Jobs
6. **Monitoring**: Add uptime monitoring and alerting
7. **Testing**: Add unit tests for source functions

### Known Limitations
- **No authentication**: For protected job boards
- **Limited error recovery**: Fails-fast on critical errors
- **No job expiry handling**: Old jobs remain on WordPress (manual cleanup needed)
- **Basic classification**: Keyword-based, not ML-based

---

## Contact & Support

### Repository
- **GitHub**: https://github.com/arunbabusb/techjobs360-scraper
- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: Use GitHub Discussions for questions

### WordPress Site
- **Production**: https://techjobs360.com
- **Support**: Contact via site contact form

### RapidAPI
- **JSearch API**: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/
- **Support**: RapidAPI support for API issues

---

## Changelog

### Recent Updates (Last 10 commits)
- `06c9671` - Update posted_jobs.json (2 days ago)
- `932b7cd` - Update job_scraper.py (2 days ago)
- `292ae5f` - Update job_scraper.py (2 days ago)
- `8a3a1be` - Update config.yaml (2 days ago)
- `e4993a3` - Update scraper.yml (2 days ago)
- `87c1a22` - Update diag-auth.yml (2 days ago)
- `87e447e` - Add 15 more cities for increased job coverage (2 days ago)
- `6378127` - Increase scraper frequency to every 6 hours (2 days ago)

---

## Quick Reference

### File Locations
```
job_scraper.py:126    - http_request() with retry logic
job_scraper.py:146    - query_jsearch() RapidAPI integration
job_scraper.py:382    - post_to_wp() WordPress posting
job_scraper.py:441    - classify_job() AI classification
job_scraper.py:473    - main() orchestration
config.yaml:8         - sources configuration
config.yaml:64        - continents configuration
.github/workflows/scraper.yml:11 - cron schedule
```

### Environment Setup
```bash
export WP_URL="https://techjobs360.com"
export WP_USERNAME="your-username"
export WP_APP_PASSWORD="xxxx xxxx xxxx xxxx"
export JSEARCH_API_KEY="your-key"  # optional
export PROCESS_CONTINENT="asia"    # optional
export AUTO_ROTATE="true"          # optional
```

### Common Commands
```bash
# Run full scraper
python job_scraper.py

# Test single source
python -c "from job_scraper import query_remotive; print(query_remotive('python'))"

# Validate config
python -c "import yaml; yaml.safe_load(open('config.yaml'))"

# Check dedup size
wc -l posted_jobs.json
```

---

**Last Updated**: 2025-11-22
**Version**: 1.0
**Maintainer**: AI Assistant (based on repository analysis)
