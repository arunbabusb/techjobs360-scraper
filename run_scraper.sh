#!/bin/bash
# TechJobs360 Scraper - Cron Runner Script
# Place this in your hosting at: /home/youruser/techjobs360-scraper/

# Set WordPress credentials
export WP_URL="https://www.techjobs360.com"
export WP_USERNAME="admintech"
export WP_APP_PASSWORD="PGtv jIHn sa1D 9X8f Hur0 3wZo"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Run the scraper
python3 job_scraper.py >> scraper.log 2>&1

# Optional: Commit changes back to git (if you have git access)
# git add posted_jobs.json
# git commit -m "Update job dedup list"
# git push origin main
