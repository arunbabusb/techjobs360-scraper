#!/bin/bash

################################################################################
# TechJobs360 Scraper - Cron Job Setup Script
#
# This script will:
# 1. Check if cron is available
# 2. Add cron job to run scraper 4 times daily
# 3. Verify the cron job was added correctly
#
# Usage: bash setup_cron.sh
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=============================================="
echo "TechJobs360 Scraper - Cron Job Setup"
echo "=============================================="
echo ""

# Get the absolute path to the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RUN_SCRIPT="$SCRIPT_DIR/run_scraper.sh"

echo -e "${BLUE}Script location: $SCRIPT_DIR${NC}"
echo ""

################################################################################
# Step 1: Check cron availability
################################################################################

echo -e "${YELLOW}[1/4] Checking cron availability...${NC}"

if ! command -v crontab &> /dev/null; then
    echo -e "${RED}✗ crontab command not found${NC}"
    echo ""
    echo "Cron might not be installed or accessible."
    echo ""
    echo -e "${YELLOW}Alternative: Use cPanel Cron Jobs${NC}"
    echo "1. Log into cPanel"
    echo "2. Go to 'Cron Jobs' (under Advanced)"
    echo "3. Add new cron job with these settings:"
    echo ""
    echo "   Minute: 0"
    echo "   Hour: 0,6,12,18"
    echo "   Day: *"
    echo "   Month: *"
    echo "   Weekday: *"
    echo "   Command: $RUN_SCRIPT"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ crontab is available${NC}"
echo ""

################################################################################
# Step 2: Check if run script exists
################################################################################

echo -e "${YELLOW}[2/4] Checking run script...${NC}"

if [ ! -f "$RUN_SCRIPT" ]; then
    echo -e "${RED}✗ run_scraper.sh not found!${NC}"
    echo "Please run setup_on_server.sh first."
    exit 1
fi

if [ ! -x "$RUN_SCRIPT" ]; then
    echo "Making run_scraper.sh executable..."
    chmod +x "$RUN_SCRIPT"
fi

echo -e "${GREEN}✓ Run script found and executable${NC}"
echo ""

################################################################################
# Step 3: Configure cron job
################################################################################

echo -e "${YELLOW}[3/4] Setting up cron job...${NC}"
echo ""

# Show current crontab (if any)
echo "Current cron jobs:"
crontab -l 2>/dev/null | grep -v "^#" | grep -v "^$" || echo "  (none)"
echo ""

# Check if job already exists
if crontab -l 2>/dev/null | grep -q "run_scraper.sh"; then
    echo -e "${YELLOW}⚠ Cron job already exists for run_scraper.sh${NC}"
    echo ""
    read -p "Do you want to replace it? (y/N): " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing cron job."
        exit 0
    fi

    # Remove existing entries
    crontab -l 2>/dev/null | grep -v "run_scraper.sh" | crontab -
    echo "Removed old cron job."
fi

# Cron schedule options
echo -e "${BLUE}Choose schedule:${NC}"
echo "1. Every 6 hours (recommended) - 00:00, 06:00, 12:00, 18:00"
echo "2. Every 4 hours - 00:00, 04:00, 08:00, 12:00, 16:00, 20:00"
echo "3. Every 3 hours - 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00"
echo "4. Daily (once) - 00:00"
echo "5. Custom"
echo ""

read -p "Select option (1-5) [default: 1]: " schedule_choice
schedule_choice=${schedule_choice:-1}

case $schedule_choice in
    1)
        CRON_SCHEDULE="0 0,6,12,18 * * *"
        DESCRIPTION="every 6 hours"
        ;;
    2)
        CRON_SCHEDULE="0 0,4,8,12,16,20 * * *"
        DESCRIPTION="every 4 hours"
        ;;
    3)
        CRON_SCHEDULE="0 0,3,6,9,12,15,18,21 * * *"
        DESCRIPTION="every 3 hours"
        ;;
    4)
        CRON_SCHEDULE="0 0 * * *"
        DESCRIPTION="daily at midnight"
        ;;
    5)
        echo ""
        echo "Enter custom cron schedule (5 fields: minute hour day month weekday)"
        echo "Example: 30 */6 * * * (every 6 hours at :30 minutes)"
        read -p "Schedule: " CRON_SCHEDULE
        DESCRIPTION="custom schedule"
        ;;
    *)
        echo -e "${RED}Invalid choice. Using default (every 6 hours).${NC}"
        CRON_SCHEDULE="0 0,6,12,18 * * *"
        DESCRIPTION="every 6 hours"
        ;;
esac

echo ""
echo "Adding cron job: $DESCRIPTION"
echo "Schedule: $CRON_SCHEDULE"
echo ""

# Add new cron job
(crontab -l 2>/dev/null; echo "# TechJobs360 Scraper - Runs $DESCRIPTION") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_SCHEDULE $RUN_SCRIPT") | crontab -

echo -e "${GREEN}✓ Cron job added successfully${NC}"
echo ""

################################################################################
# Step 4: Verify cron job
################################################################################

echo -e "${YELLOW}[4/4] Verifying cron job...${NC}"
echo ""

echo "Current crontab:"
crontab -l 2>/dev/null
echo ""

if crontab -l 2>/dev/null | grep -q "$RUN_SCRIPT"; then
    echo -e "${GREEN}✓ Cron job verified!${NC}"
else
    echo -e "${RED}✗ Cron job not found in crontab${NC}"
    echo "Something went wrong. Please set up manually."
    exit 1
fi

echo ""

################################################################################
# Final information
################################################################################

echo "=============================================="
echo -e "${GREEN}✓ Cron Job Setup Complete!${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}Schedule:${NC} $DESCRIPTION"
echo -e "${BLUE}Command:${NC} $RUN_SCRIPT"
echo ""
echo -e "${BLUE}Next Run Times:${NC}"

# Calculate next 3 run times (approximate)
case $schedule_choice in
    1)
        echo "  • Today at 00:00, 06:00, 12:00, or 18:00 (whichever is next)"
        ;;
    2)
        echo "  • Today at 00:00, 04:00, 08:00, 12:00, 16:00, or 20:00 (whichever is next)"
        ;;
    3)
        echo "  • Every 3 hours starting from midnight"
        ;;
    4)
        echo "  • Tomorrow at 00:00 (midnight)"
        ;;
    *)
        echo "  • According to your custom schedule"
        ;;
esac

echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo ""
echo "• View cron jobs:"
echo "  crontab -l"
echo ""
echo "• Edit cron jobs:"
echo "  crontab -e"
echo ""
echo "• Remove cron job:"
echo "  crontab -l | grep -v 'run_scraper.sh' | crontab -"
echo ""
echo "• View scraper logs:"
echo "  tail -f $SCRIPT_DIR/logs/scraper.log"
echo ""
echo "• View cron execution log:"
echo "  tail -f $SCRIPT_DIR/logs/cron.log"
echo ""
echo "• Test run manually:"
echo "  $RUN_SCRIPT"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "• First run will happen at the next scheduled time"
echo "• Check logs after first run to ensure it works"
echo "• Logs location: $SCRIPT_DIR/logs/"
echo ""
echo "=============================================="
