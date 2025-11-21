# CLAUDE.md - AI Assistant Guide for TechJobs360 Scraper

> **Last Updated**: 2025-11-21
> **Project Version**: v2.1 (Multi-source scraper with WordPress integration - ALL sources implemented)

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Repository Structure](#repository-structure)
3. [Architecture & Data Flow](#architecture--data-flow)
4. [Key Components](#key-components)
5. [Development Workflows](#development-workflows)
6. [Configuration Management](#configuration-management)
7. [Testing & Debugging](#testing--debugging)
8. [Common Tasks](#common-tasks)
9. [Code Conventions](#code-conventions)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

**TechJobs360 Scraper** is an automated Python application that:
- Collects tech job listings from multiple sources (paid and free APIs)
- Deduplicates jobs using SHA1 hashing
- Classifies jobs by role, seniority, and work type
- Fetches company logos from Clearbit
- Posts jobs to a WordPress site via REST API
- Runs automatically via GitHub Actions (4x daily)

### Primary Use Cases
- Aggregating global tech jobs for a WordPress job board
- Automated job posting with minimal manual intervention
- Multi-continent job discovery with intelligent rotation

### Tech Stack
- **Language**: Python 3.11+
- **Key Libraries**: requests, BeautifulSoup4, PyYAML, Pillow, python-slugify
- **CI/CD**: GitHub Actions
- **Storage**: JSON file-based deduplication
- **Target Platform**: WordPress (WP Job Manager plugin)

---

## 📁 Repository Structure

```
techjobs360-scraper/
├── .github/
│   └── workflows/
│       ├── scraper.yml          # Main scraper workflow (runs 4x daily)
│       └── diag-auth.yml        # Diagnostics workflow
├── job_scraper.py               # Main application (630 lines)
├── config.yaml                  # Configuration file (continents, sources, settings)
├── posted_jobs.json             # Deduplication database (tracked in git)
├── requirements.txt             # Python dependencies
├── README.md                    # User-facing documentation
└── CLAUDE.md                    # This file (AI assistant guide)
```

### Key Files Explained

#### `job_scraper.py` (Lines: 1-730)
The monolithic main application containing:
- **Lines 1-33**: Imports and module docstring
- **Lines 34-52**: Environment variables and global configuration
- **Lines 57-122**: Config and deduplication helpers
- **Lines 126-141**: HTTP request wrapper with retry logic
- **Lines 145-381**: Job source functions (JSearch, Remotive, RemoteOK, WeWorkRemotely, Arbeitnow, Jobicy, Himalayas, Indeed, LinkedIn)
- **Lines 454-477**: Logo fetching and WordPress media upload
- **Lines 482-521**: WordPress post creation
- **Lines 526-559**: Simple keyword-based job classification
- **Lines 564-729**: Main orchestration logic

#### `config.yaml` (Lines: 1-287)
YAML configuration with:
- **global**: Default settings, auto-rotation
- **sources**: Enable/disable job sources (9 different sources)
- **dedup**: Deduplication settings (max_age_days)
- **posting**: WordPress post settings (status, tags)
- **continents**: 7 continents with 20+ countries and 50+ cities

#### `posted_jobs.json`
JSON array storing deduplicated jobs with structure:
```json
{
  "hash": "sha1-hash-of-job-identifier",
  "title": "Job Title",
  "company": "Company Name",
  "location": "City, Country",
  "url": "https://job-url.com",
  "first_seen": 1234567890
}
```

---

## 🔄 Architecture & Data Flow

### High-Level Flow

```
┌─────────────────┐
│  GitHub Actions │
│  (4x daily)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load config.yaml│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Prune old entries from posted_jobs.json │
└────────┬────────────────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Auto-rotate continent│ (based on weekday if enabled)
└────────┬─────────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ For each continent → country → locale:   │
│   1. Query enabled sources               │
│   2. Apply rate limiting (pause_seconds) │
│   3. Deduplicate by hash                 │
│   4. Classify job (role/seniority/remote)│
│   5. Fetch company logo (Clearbit)       │
│   6. Upload logo to WordPress            │
│   7. Create WordPress post               │
│   8. Add to deduplication database       │
└────────┬─────────────────────────────────┘
         │
         ▼
┌─────────────────────┐
│ Save posted_jobs.json│
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│ Git commit & push   │
└─────────────────────┘
```

### Deduplication Strategy

1. **Hash Generation**: `SHA1(job_id OR url OR title)`
2. **Storage**: Each job stored with hash, metadata, and first_seen timestamp
3. **Pruning**: Jobs older than `dedup.max_age_days` (60 days) are removed
4. **Lookup**: Before posting, check if hash exists in dedup list

### Job Source Priority

Sources are queried in order defined in `config.yaml`:
1. **jsearch** - RapidAPI JSearch (paid, requires API key)
2. **remotive** - Free JSON API (https://remotive.com/api/remote-jobs)
3. **remoteok** - Free JSON API (https://remoteok.com/api)
4. **arbeitnow** - Free JSON API (https://www.arbeitnow.com/api/job-board-api)
5. **jobicy** - Free JSON API (https://jobicy.com/api/v2/remote-jobs)
6. **himalayas** - Free JSON API (https://himalayas.app/jobs/api)
7. **weworkremotely** - HTML scraping (https://weworkremotely.com)
8. **indeed** - HTML scraping (disabled by default, enabled_html: false)
9. **linkedin** - HTML scraping (disabled by default, enabled_html: false)

---

## 🔧 Key Components

### 1. HTTP Request Handler (`http_request`)
**Location**: job_scraper.py:126-141

- Wrapper around `requests.request()`
- Implements exponential backoff (4 attempts, 1s → 2s → 4s → 8s)
- Auto-adds User-Agent header
- 20-second timeout

**When to modify**: When changing retry logic or adding new HTTP headers

### 2. Job Source Functions

#### JSearch API (`query_jsearch`)
**Location**: job_scraper.py:146-179
- **API**: RapidAPI JSearch
- **Auth**: X-RapidAPI-Key header
- **Returns**: List of normalized job dicts

#### Remotive (`query_remotive`)
**Location**: job_scraper.py:184-207
- **Endpoint**: `https://remotive.com/api/remote-jobs`
- **Free**: Yes, no auth required
- **Search**: Query parameter

#### RemoteOK (`query_remoteok`)
**Location**: job_scraper.py:212-246
- **Endpoint**: `https://remoteok.com/api`
- **Free**: Yes, returns all jobs
- **Filtering**: Client-side by query string

#### WeWorkRemotely (`parse_weworkremotely`)
**Location**: job_scraper.py:251-281
- **Method**: HTML parsing (BeautifulSoup)
- **Selectors**: `section.jobs article a`, `.title`, `.company`

#### Arbeitnow (`query_arbeitnow`)
**Location**: job_scraper.py:284-317
- **Endpoint**: `https://www.arbeitnow.com/api/job-board-api`
- **Free**: Yes, no auth required
- **Filtering**: Client-side by query string
- **Features**: Jobs from Europe/Remote, visa sponsorship info

#### Jobicy (`query_jobicy`)
**Location**: job_scraper.py:320-345
- **Endpoint**: `https://jobicy.com/api/v2/remote-jobs`
- **Free**: Yes, no auth required
- **Parameters**: count (max 100), tag (search term)
- **Features**: 50k+ remote jobs, attribution required

#### Himalayas (`query_himalayas`)
**Location**: job_scraper.py:348-381
- **Endpoint**: `https://himalayas.app/jobs/api`
- **Free**: Yes, no auth required
- **Limit**: 20 jobs per request (API max)
- **Features**: Remote jobs, location restrictions, employment types

#### Indeed/LinkedIn Parsers
**Location**: job_scraper.py:384-449
- **Status**: Disabled by default (`enabled_html: false`)
- **Risk**: May violate ToS, require login, or get rate-limited
- **Use**: Only enable for testing or with proper authorization

### 3. Logo Fetching (`fetch_logo`)
**Location**: job_scraper.py:454-464

- **Service**: Clearbit Logo API (`https://logo.clearbit.com/{domain}`)
- **Free tier**: 100 requests/month per domain
- **Fallback**: Returns `None` on failure (logo optional)

### 4. WordPress Integration

#### Media Upload (`upload_media_to_wp`)
**Location**: job_scraper.py:466-477
- **Endpoint**: `/wp-json/wp/v2/media`
- **Auth**: HTTP Basic (username + app password)
- **Format**: Multipart upload with Content-Disposition header

#### Post Creation (`post_to_wp`)
**Location**: job_scraper.py:482-521
- **Endpoint**: `/wp-json/wp/v2/posts`
- **Status**: Configurable (`publish` or `draft`)
- **Slug**: Auto-generated from title + company + location (max 200 chars)
- **Tags**: Includes continent, country, role, seniority, work_type

### 5. Job Classification (`classify_job`)
**Location**: job_scraper.py:541-559

Simple keyword matching for:
- **Seniority**: senior, mid, junior (based on keywords in job_scraper.py:526-529)
- **Role**: backend, frontend, fullstack, data, devops, mobile, qa (job_scraper.py:531-538)
- **Work Type**: remote or onsite
- **Skills**: Extracted from keyword matches (max 6)

**Limitation**: No ML/AI, purely regex/keyword based

---

## 🛠️ Development Workflows

### Running Locally

```bash
# 1. Clone repository
git clone https://github.com/arunbabusb/techjobs360-scraper.git
cd techjobs360-scraper

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
export WP_URL="https://your-wordpress-site.com"
export WP_USERNAME="your-wp-username"
export WP_APP_PASSWORD="your-app-password"
export JSEARCH_API_KEY="your-rapidapi-key"  # Optional
export PROCESS_CONTINENT="asia"  # Optional: test single continent
export AUTO_ROTATE="false"  # Optional: disable rotation

# 4. Run scraper
python job_scraper.py
```

### Testing Specific Components

```python
# Test deduplication logic
from job_scraper import load_dedup, prune_dedup
dedup = load_dedup()
pruned = prune_dedup(dedup, max_age_days=30)
print(f"Pruned {len(dedup) - len(pruned)} entries")

# Test a specific source
from job_scraper import query_remotive, query_arbeitnow, query_jobicy, query_himalayas
jobs = query_remotive("python developer", limit=10)
print(f"Found {len(jobs)} jobs from Remotive")

jobs = query_arbeitnow("backend engineer", limit=10)
print(f"Found {len(jobs)} jobs from Arbeitnow")

jobs = query_jobicy("react", limit=10)
print(f"Found {len(jobs)} jobs from Jobicy")

# Test classification
from job_scraper import classify_job
result = classify_job("Senior Backend Engineer", "Python, AWS, Kubernetes")
print(result)  # {'seniority': 'senior', 'role': 'backend', ...}
```

### GitHub Actions Workflow

**File**: `.github/workflows/scraper.yml`

**Schedule**: Runs at 00:30, 06:30, 12:30, 18:30 UTC (4x daily)

**Manual Trigger**:
```bash
# Via GitHub UI: Actions → TechJobs360 FREE Scraper → Run workflow

# Or via GitHub CLI
gh workflow run scraper.yml
```

**Environment**: Uses GitHub Secrets for credentials
- `WP_URL`
- `WP_USERNAME`
- `WP_APP_PASSWORD`
- `JSEARCH_API_KEY`
- `PROCESS_CONTINENT` (optional)

**Post-run**: Auto-commits `posted_jobs.json` if changed

---

## ⚙️ Configuration Management

### config.yaml Structure

```yaml
global:
  default_per_page: 20          # Jobs per page for paginated APIs
  fallback_per_page: 10         # Fallback if API doesn't specify
  auto_rotate: true             # Enable continent rotation by weekday

sources:
  - type: jsearch               # Source identifier
    enabled: true               # Enable/disable
    limit: 50                   # Max jobs per query (optional)

dedup:
  max_age_days: 60              # Prune jobs older than this

posting:
  post_status: publish          # 'publish' or 'draft'
  tags:
    - tech                      # Default tags for all posts
    - jobs

continents:
  - id: asia                    # Unique identifier
    name: Asia                  # Display name
    pause_seconds: 2            # Rate limiting delay
    countries:
      - code: IN                # ISO country code
        name: India
        locales:
          - city: Bengaluru     # City name
            query: software engineer  # Search query
```

### Auto-Rotation Logic

**File**: job_scraper.py:464-471

Maps weekdays to continents:
- **Monday (0)**: Asia
- **Tuesday (1)**: Europe
- **Wednesday (2)**: North America
- **Thursday (3)**: South America
- **Friday (4)**: Africa
- **Saturday (5)**: Oceania
- **Sunday (6)**: Antarctica

### Adding a New Job Source

1. **Add to config.yaml**:
```yaml
sources:
  - type: newsource
    enabled: true
    limit: 50
```

2. **Implement query function** in job_scraper.py:
```python
def query_newsource(query: str, limit: int = 50) -> List[Dict]:
    try:
        # Implement API call or HTML parsing
        url = "https://newsource.com/api/jobs"
        resp = http_request("GET", url, params={"q": query})
        data = resp.json()

        jobs = []
        for item in data.get("results", [])[:limit]:
            jobs.append({
                "id": item.get("job_id"),
                "title": item.get("title"),
                "company": item.get("employer"),
                "location": item.get("city"),
                "description": item.get("desc"),
                "url": item.get("apply_url"),
                "raw": item  # Store original for debugging
            })
        return jobs
    except Exception as e:
        logger.warning("NewsSource query failed: %s", e)
        return []
```

3. **Add to main loop** (job_scraper.py:520-558):
```python
elif stype == "newsource":
    candidate_jobs += query_newsource(qtext, limit=src.get("limit", 50))
```

### Adding a New City

Edit `config.yaml` under the appropriate continent/country:
```yaml
continents:
  - id: asia
    name: Asia
    countries:
      - code: IN
        name: India
        locales:
          - city: Bengaluru
            query: software engineer
          - city: Mumbai           # Add new city
            query: frontend developer  # Add specific query
```

---

## 🧪 Testing & Debugging

### Enable Debug Logging

Modify job_scraper.py:51:
```python
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
```

### Test Single Continent

```bash
export PROCESS_CONTINENT="asia"
export AUTO_ROTATE="false"
python job_scraper.py
```

### Dry Run Mode (No WordPress Posting)

Remove or comment out WordPress credentials:
```bash
unset WP_URL
unset WP_USERNAME
unset WP_APP_PASSWORD
python job_scraper.py
```

Jobs will be collected and logged but not posted.

### Inspect Deduplication Database

```bash
# View total entries
jq length posted_jobs.json

# View recent entries (last 5)
jq '.[-5:]' posted_jobs.json

# Find jobs from specific company
jq '.[] | select(.company == "Acme Cloud")' posted_jobs.json

# Count jobs by source
jq 'group_by(.source) | map({source: .[0].source, count: length})' posted_jobs.json
```

### Common Issues

#### Issue: "Missing config.yaml"
**Solution**: Ensure config.yaml exists in repository root
```bash
ls -la config.yaml
```

#### Issue: "JSearch returned 403"
**Solution**: Check JSEARCH_API_KEY is valid
```bash
echo $JSEARCH_API_KEY
# Test API key manually
curl -H "X-RapidAPI-Key: $JSEARCH_API_KEY" \
     "https://jsearch.p.rapidapi.com/search?query=python"
```

#### Issue: "WP media upload failed"
**Solution**: Verify WordPress credentials and REST API is enabled
```bash
# Test WordPress API access
curl -u "$WP_USERNAME:$WP_APP_PASSWORD" \
     "$WP_URL/wp-json/wp/v2/posts?per_page=1"
```

#### Issue: "No new jobs posted"
**Solution**: Check deduplication database size
```bash
# If dedup file is too large, prune manually
jq 'map(select(.first_seen > 1700000000))' posted_jobs.json > posted_jobs_new.json
mv posted_jobs_new.json posted_jobs.json
```

---

## 📝 Common Tasks

### Task: Increase Scraping Frequency

Edit `.github/workflows/scraper.yml:11`:
```yaml
schedule:
  - cron: '*/15 * * * *'  # Every 15 minutes (use cautiously)
```

### Task: Change Post Status to Draft

Edit `config.yaml`:
```yaml
posting:
  post_status: draft  # Change from 'publish'
```

### Task: Disable Remote Job Sources

Edit `config.yaml`:
```yaml
sources:
  - type: remotive
    enabled: false
  - type: remoteok
    enabled: false
  - type: arbeitnow
    enabled: false
  - type: jobicy
    enabled: false
  - type: himalayas
    enabled: false
  - type: weworkremotely
    enabled: false
```

### Task: Add Custom Classification Keywords

Edit job_scraper.py:426-438:
```python
SENIORITY_KEYWORDS = {
    "senior": ["senior", "lead", "principal", "sr.", "staff", "expert"],  # Add 'expert'
    # ...
}

ROLE_KEYWORDS = {
    "backend": ["backend", "java", "golang", "python", "ruby", "node", "spring"],  # Add 'spring'
    # ...
}
```

### Task: Increase Rate Limiting

Edit `config.yaml` for specific continent:
```yaml
continents:
  - id: asia
    name: Asia
    pause_seconds: 5  # Increase from 2 to 5 seconds
```

### Task: Test WordPress Connection

```bash
# Test authentication
curl -u "$WP_USERNAME:$WP_APP_PASSWORD" \
     "$WP_URL/wp-json/wp/v2/users/me"

# Test creating a draft post
curl -X POST \
     -u "$WP_USERNAME:$WP_APP_PASSWORD" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Post","content":"Test","status":"draft"}' \
     "$WP_URL/wp-json/wp/v2/posts"
```

---

## 📐 Code Conventions

### Style Guide

- **Line Length**: ~80-100 characters (not strictly enforced)
- **Indentation**: 4 spaces
- **Naming**:
  - Functions: `snake_case` (e.g., `query_jsearch`, `post_to_wp`)
  - Variables: `snake_case` (e.g., `candidate_jobs`, `dedup_list`)
  - Constants: `UPPER_SNAKE_CASE` (e.g., `REQUESTS_TIMEOUT`, `USER_AGENT`)
- **Docstrings**: Module-level only (lines 2-15)
- **Type Hints**: Used for function signatures (e.g., `def query_jsearch(...) -> List[Dict]`)

### Error Handling Philosophy

- **Graceful Degradation**: If one source fails, continue with others
- **Logging**: Log warnings for expected failures, errors for unexpected
- **No Hard Failures**: Never crash the entire scraper for a single job/source
- **Empty Returns**: Return empty lists `[]` on failure, not `None`

Example:
```python
def query_source(query: str) -> List[Dict]:
    try:
        # Attempt to fetch jobs
        ...
    except Exception as e:
        logger.warning("Source failed: %s", e)
        return []  # Return empty list, not None
```

### Logging Levels

- **DEBUG**: Detailed info (e.g., "Fetching jobs for query X")
- **INFO**: Major milestones (e.g., "Processing continent: Asia", "New jobs posted: 10")
- **WARNING**: Expected failures (e.g., "API returned 403", "Logo fetch failed")
- **ERROR**: Critical issues (e.g., "Missing WP credentials", "Cannot read config")

### Git Commit Conventions

**From recent commits**:
- `📊 Update job dedup list` - Auto-commit from GitHub Actions
- `Update job_scraper.py` - Manual code updates
- `Update config.yaml` - Configuration changes
- `URGENT: ...` - Critical fixes (use sparingly)
- `URGENT FIX: Revert to working version` - Rollbacks

**Recommended**:
- Use clear, descriptive messages
- Prefix with emoji for auto-commits (optional)
- Reference issue numbers if applicable

---

## 🚨 Troubleshooting

### Problem: GitHub Actions Failing

**Check**:
1. Workflow logs in GitHub Actions tab
2. Secrets are configured correctly (Settings → Secrets → Actions)
3. Python version matches (3.11 in scraper.yml:32)

**Common Causes**:
- Missing/expired API keys
- WordPress site down or credentials changed
- Merge conflicts in posted_jobs.json

### Problem: Jobs Not Appearing on WordPress

**Debug Steps**:
1. Check post_status in config.yaml (should be `publish` not `draft`)
2. Verify WordPress credentials are correct
3. Check if WordPress REST API is enabled
4. Look for WP errors in GitHub Actions logs

### Problem: Duplicate Jobs Being Posted

**Causes**:
- Deduplication database reset/corrupted
- Job ID/URL changed by source
- Multiple workflow runs simultaneously

**Solution**:
```bash
# Check for concurrent runs
cat .github/workflows/scraper.yml | grep concurrency
# Should show: cancel-in-progress: true

# Manually remove duplicates from posted_jobs.json
jq 'unique_by(.hash)' posted_jobs.json > posted_jobs_deduped.json
mv posted_jobs_deduped.json posted_jobs.json
```

### Problem: Rate Limited by Job Sources

**Symptoms**:
- "RemoteOK returned 429" errors
- Empty job lists despite query

**Solution**:
1. Increase `pause_seconds` in config.yaml
2. Add random delays: `time.sleep(base_pause + random.random() * base_pause)` (already implemented at job_scraper.py:561)
3. Reduce `limit` for aggressive sources

### Problem: Memory Issues

**Symptoms**:
- GitHub Actions timeout (60 minutes)
- Out of memory errors

**Solution**:
1. Reduce number of cities per run
2. Lower `limit` values in config.yaml
3. Process one continent at a time with PROCESS_CONTINENT

---

## 🔐 Security Considerations

### Secrets Management

**Never commit**:
- WordPress credentials
- API keys
- Personal data

**Use**:
- GitHub Secrets for CI/CD
- Environment variables for local dev
- `.env` files (add to .gitignore if needed)

### Data Privacy

**Current Compliance** (from README.md:38-44):
- ✅ Only public job data collected
- ✅ No personal/sensitive data
- ✅ Regular expiry checks (max_age_days)
- ✅ Source attribution included
- ✅ Deduplication prevents spam

### WordPress Security

- Use **Application Passwords** (not account password)
- Limit WordPress user to minimum required permissions (Author/Contributor)
- Enable HTTPS for WP_URL
- Use REST API authentication plugins if needed

---

## 📊 Performance Optimization

### Current Bottlenecks

1. **Sequential Processing**: Cities processed one by one
2. **Logo Fetching**: Synchronous HTTP requests
3. **WordPress API**: One post at a time

### Optimization Ideas (Not Implemented)

```python
# Use async/await for concurrent requests
import asyncio
import aiohttp

async def query_all_sources_async(query: str):
    tasks = [
        query_jsearch_async(query),
        query_remotive_async(query),
        query_remoteok_async(query),
    ]
    results = await asyncio.gather(*tasks)
    return [job for sublist in results for job in sublist]

# Batch WordPress posts
def post_jobs_batch(jobs: List[Dict]):
    # Use WordPress batch endpoint if available
    # Or create multiple posts in parallel threads
    pass
```

**Note**: Before implementing async, test thoroughly to avoid rate limiting.

---

## 🔄 Maintenance Checklist

### Weekly
- [ ] Check GitHub Actions logs for errors
- [ ] Verify jobs are appearing on WordPress site
- [ ] Monitor API usage (JSearch, Clearbit)

### Monthly
- [ ] Review and prune posted_jobs.json (auto-pruned by max_age_days)
- [ ] Update Python dependencies (`pip list --outdated`)
- [ ] Check for new job sources or API changes

### Quarterly
- [ ] Review classification keywords accuracy
- [ ] Audit WordPress post quality
- [ ] Update documentation (README.md, CLAUDE.md)

---

## 🤖 AI Assistant Guidelines

### When Modifying Code

1. **Always read the file first** using Read tool
2. **Understand context** by checking surrounding functions
3. **Test changes locally** before committing
4. **Update CLAUDE.md** if architecture changes
5. **Follow existing conventions** (see Code Conventions section)

### When Adding Features

1. **Check config.yaml** for existing settings
2. **Add configuration options** rather than hardcoding
3. **Implement error handling** (return empty list on failure)
4. **Add logging** at appropriate levels
5. **Update documentation** in this file

### When Debugging

1. **Start with logs** in GitHub Actions
2. **Reproduce locally** with same environment
3. **Use debug logging** (job_scraper.py:51)
4. **Check recent commits** for breaking changes
5. **Consult Troubleshooting section** above

### When Answering Questions

1. **Reference line numbers** (e.g., "job_scraper.py:126-141")
2. **Explain trade-offs** of different approaches
3. **Suggest safer alternatives** for risky changes
4. **Link to documentation** (README.md, config.yaml comments)

---

## 📚 Additional Resources

### External Documentation

- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [WP Job Manager](https://wpjobmanager.com/documentation/)
- [RapidAPI JSearch](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/)
- [Remotive API](https://remotive.com/api-documentation)
- [RemoteOK API](https://remoteok.com/api)
- [Clearbit Logo API](https://clearbit.com/docs#logo-api)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

### Related Files

- `README.md` - User-facing project documentation
- `config.yaml` - Runtime configuration
- `.github/workflows/scraper.yml` - CI/CD workflow

---

## 📞 Contact & Support

For issues related to this codebase:
1. Check GitHub Issues: https://github.com/arunbabusb/techjobs360-scraper/issues
2. Review recent commits for similar problems
3. Consult Troubleshooting section above

---

**End of CLAUDE.md**

*This document is maintained by AI assistants and human developers. Last reviewed: 2025-11-21*

---

## 📝 Changelog

### v2.1 (2025-11-21)
- ✅ Implemented missing job sources: Arbeitnow, Jobicy, Himalayas
- ✅ Fixed silent failure logging for unknown sources (now shows WARNING)
- ✅ Updated documentation to match actual implementation
- ✅ All 9 job sources now fully functional
