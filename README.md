# TechJobs360 Scraper

## Overview
Automated Python scraper for posting tech jobs (from JSearch API) to a WordPress job board (WP Job Manager).

### JSearch API Endpoints

This scraper utilizes **ALL 4 JSearch API endpoints** for comprehensive job data:

1. **Job Search** (`/search`) - Primary endpoint for discovering jobs
   - Searches for jobs based on query, location, and filters
   - Supports pagination for bulk job collection
   - Filters: date_posted, country, employment_type, etc.

2. **Job Details** (`/job-details`) - Enhanced job information
   - Fetches detailed information for specific job IDs
   - Provides comprehensive job descriptions
   - Returns job highlights and requirements

3. **Job Salary** (`/salary`) - Salary estimations
   - Estimates salary ranges for job titles
   - Location-specific salary data
   - Currency-aware salary information

4. **Company Job Salary** (`/company-job-salary`) - Company-specific salary data
   - Salary ranges for specific company + job title combinations
   - More accurate than general salary estimates
   - Helps candidates understand company compensation

### Enhanced Features

✅ **Multi-Endpoint Integration** - Enriches each job with data from multiple API calls
✅ **Salary Information** - Automatically adds salary ranges to job listings
✅ **Job Highlights** - Displays key job requirements and benefits
✅ **Smart Rate Limiting** - Prevents API throttling with intelligent delays
✅ **Error Handling** - Gracefully handles API failures and continues scraping

## Scraping Policy and Compliance Steps
- **Privacy**: Only public job info is processed—title, company, location, logo, description, source, expiry. No personal or sensitive data is ever collected/posted.
- **Renewal/Expiry**: Jobs are regularly checked for expiry based on either posting date or provided deadlines, and expired jobs are removed.
- **Deduplication**: Each job is checked for duplicates by job ID and by title/company combo; previously posted jobs are never re-added.
- **Logo Accessibility**: Logos are uploaded with descriptive alt text (company/name) for accessibility.
- **Source Attribution**: All posts add explicit source attribution (‘Powered by JSearch API’ plus original publisher).

## Attribution
Job data is powered by [JSearch API](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch/) and original listing sources.

## Usage
- Set WP/App credentials and RapidAPI key in environment.
- Run `job_scraper.py` (Python 3) with scheduler/cron.

## Compliance Notes
This project strictly avoids scraping or publishing any personal, sensitive, or user-identifiable data. Only open employment/listing information is processed, with full attribution and deletion of expired content.
