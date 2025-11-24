#!/bin/bash

################################################################################
# TechJobs360 Scraper - Status Check Script
#
# This script checks:
# 1. If the scraper is set up on this server
# 2. If cron jobs are configured
# 3. When the last run happened
# 4. If jobs are being posted successfully
# 5. Current system status
#
# Usage: bash check_status.sh
################################################################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     TechJobs360 Scraper - Status Check                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${BLUE}Checking status at: $(date)${NC}"
echo ""

################################################################################
# Section 1: Check if scraper is set up on this server
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}[1] SCRAPER INSTALLATION STATUS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if we're in the right directory
if [ ! -f "job_scraper.py" ]; then
    echo -e "${RED}✗ job_scraper.py not found${NC}"
    echo "  You are not in the scraper directory."
    echo "  Please cd to the scraper directory and run this script again."
    exit 1
fi
echo -e "${GREEN}✓ Scraper files found${NC}"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
else
    echo -e "${YELLOW}⚠ Virtual environment not found${NC}"
    echo -e "  ${YELLOW}→ Run: bash setup_on_server.sh${NC}"
fi

# Check if .env file exists
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ Configuration file (.env) exists${NC}"

    # Check key variables (without showing values)
    if grep -q "WP_URL" .env && grep -q "WP_USERNAME" .env && grep -q "WP_APP_PASSWORD" .env; then
        echo -e "${GREEN}✓ WordPress credentials configured${NC}"
    else
        echo -e "${YELLOW}⚠ .env file incomplete${NC}"
        echo -e "  ${YELLOW}→ Edit .env and add missing credentials${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Configuration file (.env) not found${NC}"
    echo -e "  ${YELLOW}→ Run: bash setup_on_server.sh${NC}"
fi

# Check if run script exists
if [ -f "run_scraper.sh" ] && [ -x "run_scraper.sh" ]; then
    echo -e "${GREEN}✓ Run script (run_scraper.sh) exists and is executable${NC}"
else
    echo -e "${YELLOW}⚠ Run script not found or not executable${NC}"
    echo -e "  ${YELLOW}→ Run: bash setup_on_server.sh${NC}"
fi

echo ""

################################################################################
# Section 2: Check cron job configuration
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}[2] CRON JOB STATUS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if crontab command is available
if ! command -v crontab &> /dev/null; then
    echo -e "${YELLOW}⚠ crontab command not available${NC}"
    echo "  You may need to use cPanel Cron Jobs instead."
    echo ""
    echo "  To set up via cPanel:"
    echo "  1. Log into cPanel"
    echo "  2. Go to 'Cron Jobs'"
    echo "  3. Add job with command: $SCRIPT_DIR/run_scraper.sh"
    echo ""
else
    # Check if cron job exists
    if crontab -l 2>/dev/null | grep -q "run_scraper.sh"; then
        echo -e "${GREEN}✓ Cron job is configured${NC}"
        echo ""
        echo "  Current cron job(s):"
        crontab -l 2>/dev/null | grep "run_scraper.sh" | sed 's/^/  /'
        echo ""

        # Parse the schedule
        CRON_LINE=$(crontab -l 2>/dev/null | grep "run_scraper.sh" | head -1)
        CRON_SCHEDULE=$(echo "$CRON_LINE" | awk '{print $1, $2, $3, $4, $5}')

        echo -e "  ${BLUE}Schedule:${NC} $CRON_SCHEDULE"

        # Interpret the schedule
        MINUTE=$(echo "$CRON_SCHEDULE" | awk '{print $1}')
        HOUR=$(echo "$CRON_SCHEDULE" | awk '{print $2}')

        if [[ "$HOUR" == *","* ]]; then
            HOURS=$(echo "$HOUR" | tr ',' ' ')
            echo -e "  ${BLUE}Runs at hours:${NC} $HOURS"
        elif [[ "$HOUR" == *"/"* ]]; then
            INTERVAL=$(echo "$HOUR" | cut -d'/' -f2)
            echo -e "  ${BLUE}Runs every:${NC} $INTERVAL hours"
        fi

    else
        echo -e "${YELLOW}⚠ No cron job found for run_scraper.sh${NC}"
        echo -e "  ${YELLOW}→ Run: bash setup_cron.sh${NC}"
        echo ""
        echo "  Current crontab:"
        if crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" | head -5; then
            crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" | head -5 | sed 's/^/  /'
        else
            echo "  (empty)"
        fi
    fi
fi

echo ""

################################################################################
# Section 3: Check logs and last run
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}[3] EXECUTION HISTORY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if logs directory exists
if [ -d "logs" ]; then
    echo -e "${GREEN}✓ Logs directory exists${NC}"
    echo ""

    # Check scraper log
    if [ -f "logs/scraper.log" ]; then
        LOG_SIZE=$(du -h logs/scraper.log | awk '{print $1}')
        LOG_LINES=$(wc -l < logs/scraper.log)

        echo -e "  ${BLUE}Scraper log:${NC}"
        echo -e "  • File: logs/scraper.log"
        echo -e "  • Size: $LOG_SIZE"
        echo -e "  • Lines: $LOG_LINES"
        echo ""

        if [ "$LOG_LINES" -gt 0 ]; then
            # Find last run timestamp
            LAST_RUN=$(grep -E "Starting TechJobs360|INFO" logs/scraper.log | tail -1 | awk '{print $1, $2}')

            if [ ! -z "$LAST_RUN" ]; then
                echo -e "  ${GREEN}✓ Last run detected:${NC} $LAST_RUN"
            else
                echo -e "  ${YELLOW}⚠ No run detected in logs${NC}"
            fi

            # Check for errors
            ERROR_COUNT=$(grep -c "ERROR" logs/scraper.log 2>/dev/null || echo 0)
            if [ "$ERROR_COUNT" -gt 0 ]; then
                echo -e "  ${RED}✗ Found $ERROR_COUNT errors in log${NC}"
                echo ""
                echo "  Recent errors:"
                grep "ERROR" logs/scraper.log | tail -3 | sed 's/^/  /'
            else
                echo -e "  ${GREEN}✓ No errors found in log${NC}"
            fi

            echo ""
            echo -e "  ${BLUE}Last 10 log lines:${NC}"
            tail -10 logs/scraper.log | sed 's/^/  /'

        else
            echo -e "  ${YELLOW}⚠ Log file is empty (scraper hasn't run yet)${NC}"
        fi
    else
        echo -e "  ${YELLOW}⚠ No scraper.log file found${NC}"
        echo -e "    The scraper hasn't run yet, or logs directory wasn't created."
    fi

    # Check cron log
    if [ -f "logs/cron.log" ]; then
        echo ""
        echo -e "  ${BLUE}Cron execution log:${NC}"
        CRON_RUNS=$(wc -l < logs/cron.log)
        echo -e "  • Total runs: $CRON_RUNS"

        if [ "$CRON_RUNS" -gt 0 ]; then
            echo -e "  • Last run: $(tail -1 logs/cron.log)"
        fi
    fi

else
    echo -e "${YELLOW}⚠ Logs directory not found${NC}"
    echo -e "  ${YELLOW}→ Run: bash setup_on_server.sh${NC}"
fi

echo ""

################################################################################
# Section 4: Check job posting status
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}[4] JOB POSTING STATUS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check dedup file
if [ -f "posted_jobs.json" ]; then
    # Count jobs (simple check for array length)
    JOB_COUNT=$(cat posted_jobs.json | grep -o '"hash"' | wc -l)

    if [ "$JOB_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Jobs have been posted successfully!${NC}"
        echo -e "  • Total jobs posted: ${GREEN}$JOB_COUNT${NC}"
        echo ""

        # Show last 3 jobs
        echo -e "  ${BLUE}Recent jobs:${NC}"
        if command -v python3 &> /dev/null; then
            python3 -c "
import json
try:
    with open('posted_jobs.json', 'r') as f:
        jobs = json.load(f)
    for job in jobs[-3:]:
        print(f\"  • {job.get('title', 'N/A')} at {job.get('company', 'N/A')}\")
except:
    print('  (Unable to parse job details)')
" 2>/dev/null || echo "  (Python not available to show details)"
        else
            echo "  (Python not available to show details)"
        fi

    else
        echo -e "${YELLOW}⚠ No jobs posted yet${NC}"
        echo ""
        echo -e "  ${YELLOW}Possible reasons:${NC}"
        echo "  • Scraper hasn't run yet"
        echo "  • WordPress connection blocked (QUIC.cloud bot protection)"
        echo "  • Authentication failed"
        echo "  • No new jobs found from sources"
        echo ""
        echo -e "  ${BLUE}Recommended actions:${NC}"
        echo "  1. Check logs: tail -f logs/scraper.log"
        echo "  2. Test manually: ./run_scraper.sh"
        echo "  3. Check WordPress credentials in .env"
    fi
else
    echo -e "${YELLOW}⚠ posted_jobs.json not found${NC}"
    echo "  This file is created after the first successful run."
fi

echo ""

################################################################################
# Section 5: System information
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}[5] SYSTEM INFORMATION${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
fi

# Check disk space
DISK_USAGE=$(df -h "$SCRIPT_DIR" | tail -1 | awk '{print $5 " used"}')
echo -e "${BLUE}• Disk usage:${NC} $DISK_USAGE"

# Check script directory
echo -e "${BLUE}• Script location:${NC} $SCRIPT_DIR"

# Current time
echo -e "${BLUE}• Current time:${NC} $(date)"

# Timezone
TIMEZONE=$(date +%Z)
echo -e "${BLUE}• Timezone:${NC} $TIMEZONE"

echo ""

################################################################################
# Section 6: Next steps and recommendations
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${CYAN}[6] RECOMMENDATIONS${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Determine status and give recommendations
if [ ! -f ".env" ] || [ ! -f "run_scraper.sh" ]; then
    echo -e "${YELLOW}⚠ SETUP NOT COMPLETE${NC}"
    echo ""
    echo "  Next step:"
    echo -e "  → ${GREEN}bash setup_on_server.sh${NC}"
    echo ""

elif ! crontab -l 2>/dev/null | grep -q "run_scraper.sh" && command -v crontab &> /dev/null; then
    echo -e "${YELLOW}⚠ CRON JOB NOT CONFIGURED${NC}"
    echo ""
    echo "  Setup is complete but cron job is not running."
    echo ""
    echo "  Next step:"
    echo -e "  → ${GREEN}bash setup_cron.sh${NC}"
    echo ""

elif [ ! -f "posted_jobs.json" ] || [ $(cat posted_jobs.json | grep -o '"hash"' | wc -l) -eq 0 ]; then
    echo -e "${YELLOW}⚠ NO JOBS POSTED YET${NC}"
    echo ""
    echo "  Everything is set up, but no jobs have been posted."
    echo ""
    echo "  Recommended actions:"
    echo -e "  1. ${GREEN}Test manually:${NC} ./run_scraper.sh"
    echo -e "  2. ${GREEN}Check logs:${NC} tail -f logs/scraper.log"
    echo -e "  3. ${GREEN}Verify WordPress connection${NC}"
    echo ""
    echo "  If you see authentication errors:"
    echo "  • Check .env file has correct credentials"
    echo "  • Try using http://127.0.0.1 for WP_URL (bypasses QUIC.cloud)"
    echo "  • Verify WordPress Application Password is correct"
    echo ""

else
    echo -e "${GREEN}✓ EVERYTHING LOOKS GOOD!${NC}"
    echo ""
    echo "  Scraper is set up and running successfully."
    echo ""
    echo "  Maintenance commands:"
    echo -e "  • ${BLUE}View live logs:${NC} tail -f logs/scraper.log"
    echo -e "  • ${BLUE}Test manually:${NC} ./run_scraper.sh"
    echo -e "  • ${BLUE}Check cron jobs:${NC} crontab -l"
    echo -e "  • ${BLUE}View status:${NC} bash check_status.sh"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${BLUE}For more help, see:${NC}"
echo "  • DEPLOY_TO_HEROXHOST.md (setup guide)"
echo "  • HEROXHOST_CRON_SETUP.md (detailed cron guide)"
echo "  • CLAUDE.md (complete documentation)"
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Status check complete                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
