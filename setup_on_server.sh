#!/bin/bash

################################################################################
# TechJobs360 Scraper - Automated Server Setup Script
#
# This script will:
# 1. Install Python dependencies
# 2. Configure environment variables
# 3. Set up cron job to run scraper automatically
# 4. Test the installation
#
# Usage: bash setup_on_server.sh
################################################################################

set -e  # Exit on error

echo "=============================================="
echo "TechJobs360 Scraper - Server Setup"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}Current directory: $SCRIPT_DIR${NC}"
echo ""

################################################################################
# Step 1: Check Python installation
################################################################################

echo -e "${YELLOW}[1/7] Checking Python installation...${NC}"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ Found: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    echo -e "${GREEN}✓ Found: $PYTHON_VERSION${NC}"
    PYTHON_CMD="python"
else
    echo -e "${RED}✗ Python not found!${NC}"
    echo "Please install Python 3.8 or higher."
    echo "Contact your hosting provider (HeroXhost) for assistance."
    exit 1
fi

echo ""

################################################################################
# Step 2: Set up virtual environment
################################################################################

echo -e "${YELLOW}[2/7] Setting up virtual environment...${NC}"

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

echo ""

################################################################################
# Step 3: Install dependencies
################################################################################

echo -e "${YELLOW}[3/7] Installing Python dependencies...${NC}"

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${RED}✗ requirements.txt not found!${NC}"
    exit 1
fi

echo ""

################################################################################
# Step 4: Configure environment variables
################################################################################

echo -e "${YELLOW}[4/7] Configuring environment variables...${NC}"

if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    echo ""
    echo -e "${BLUE}Please enter your WordPress credentials:${NC}"
    echo ""

    # Get WordPress URL
    read -p "WordPress URL (default: http://127.0.0.1): " wp_url
    wp_url=${wp_url:-http://127.0.0.1}

    # Get WordPress username
    read -p "WordPress username: " wp_username

    # Get WordPress app password
    echo "WordPress Application Password (format: xxxx xxxx xxxx xxxx):"
    read -s wp_password
    echo ""

    # Get optional API key
    read -p "JSearch API Key (optional, press Enter to skip): " jsearch_key

    # Create .env file
    cat > .env << EOF
# TechJobs360 Scraper - Environment Configuration
# Generated: $(date)

# WordPress Configuration
WP_URL=$wp_url
WP_USERNAME=$wp_username
WP_APP_PASSWORD=$wp_password

# Optional: JSearch API Key (for RapidAPI)
JSEARCH_API_KEY=$jsearch_key

# Auto-rotation (rotates continents by weekday)
AUTO_ROTATE=true
EOF

    echo -e "${GREEN}✓ Configuration saved to .env${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
    echo -e "${YELLOW}  If you need to update credentials, edit: .env${NC}"
fi

echo ""

################################################################################
# Step 5: Create run script
################################################################################

echo -e "${YELLOW}[5/7] Creating run script...${NC}"

cat > run_scraper.sh << 'EOFSCRIPT'
#!/bin/bash

# TechJobs360 Scraper - Run Script
# This script is executed by cron

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Create logs directory if it doesn't exist
mkdir -p logs

# Run scraper with logging
python job_scraper.py >> logs/scraper.log 2>&1

# Log completion
echo "[$(date)] Scraper run completed" >> logs/cron.log

# Deactivate virtual environment
deactivate
EOFSCRIPT

chmod +x run_scraper.sh

echo -e "${GREEN}✓ Run script created: run_scraper.sh${NC}"
echo ""

################################################################################
# Step 6: Create logs directory
################################################################################

echo -e "${YELLOW}[6/7] Creating logs directory...${NC}"

mkdir -p logs
touch logs/scraper.log
touch logs/cron.log

echo -e "${GREEN}✓ Logs directory created${NC}"
echo ""

################################################################################
# Step 7: Test run
################################################################################

echo -e "${YELLOW}[7/7] Running test...${NC}"
echo ""

# Load environment variables for test
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | grep -v '^$' | xargs)
fi

echo "Testing WordPress connection..."
echo ""

# Test WordPress API access
if [ ! -z "$WP_URL" ] && [ ! -z "$WP_USERNAME" ] && [ ! -z "$WP_APP_PASSWORD" ]; then
    TEST_URL="${WP_URL}/wp-json/"

    echo "Testing: $TEST_URL"

    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -u "${WP_USERNAME}:${WP_APP_PASSWORD}" \
        "$TEST_URL" 2>&1)

    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ WordPress API connection successful!${NC}"
        echo ""
        echo -e "${GREEN}Setup completed successfully!${NC}"
    else
        echo -e "${YELLOW}⚠ WordPress API returned status: $HTTP_CODE${NC}"
        echo "This might be okay if your site requires authentication."
    fi
else
    echo -e "${YELLOW}⚠ Skipping connection test (no credentials in .env)${NC}"
fi

echo ""

################################################################################
# Final instructions
################################################################################

echo "=============================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=============================================="
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Set up cron job:"
echo "   Run: bash setup_cron.sh"
echo ""
echo "2. Or manually test the scraper:"
echo "   Run: ./run_scraper.sh"
echo ""
echo "3. View logs:"
echo "   Run: tail -f logs/scraper.log"
echo ""
echo -e "${BLUE}Files created:${NC}"
echo "  • .env (configuration)"
echo "  • run_scraper.sh (main script)"
echo "  • venv/ (Python environment)"
echo "  • logs/ (log files)"
echo ""
echo -e "${YELLOW}Important:${NC}"
echo "  • Keep your .env file secure (contains passwords)"
echo "  • Check logs regularly: logs/scraper.log"
echo "  • Dedup data stored in: posted_jobs.json"
echo ""
echo "=============================================="
