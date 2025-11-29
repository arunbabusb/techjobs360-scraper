#!/bin/bash
# Local test script for Reed API integration

echo "======================================================"
echo "TechJobs360 - Reed API Local Test"
echo "======================================================"
echo ""

# Check if REED_API_KEY is set
if [ -z "$REED_API_KEY" ]; then
    echo "❌ ERROR: REED_API_KEY is not set!"
    echo ""
    echo "Please set your Reed API key:"
    echo "  export REED_API_KEY='your-reed-api-key-here'"
    echo ""
    echo "Then run this script again:"
    echo "  bash test_local.sh"
    echo ""
    exit 1
fi

echo "✅ REED_API_KEY is set"
echo ""

# Install dependencies if needed
echo "Checking dependencies..."
if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Running Reed API test..."
echo "======================================================"
python3 test_reed.py

echo ""
echo "======================================================"
echo "Test complete!"
echo "======================================================"
