#!/bin/bash

#############################################
# GeM Scraper Configuration Script
# Configures Chrome/Chromium driver and GeM credentials
#############################################

set -e

echo "========================================"
echo "GeM Scraper Configuration"
echo "========================================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check for Chrome/Chromium
print_info "Checking for Chrome/Chromium browser..."

if command -v google-chrome &> /dev/null; then
    CHROME_PATH=$(which google-chrome)
    print_info "Google Chrome found at: $CHROME_PATH"
elif command -v chromium-browser &> /dev/null; then
    CHROME_PATH=$(which chromium-browser)
    print_info "Chromium browser found at: $CHROME_PATH"
elif command -v chromium &> /dev/null; then
    CHROME_PATH=$(which chromium)
    print_info "Chromium found at: $CHROME_PATH"
else
    print_warning "Chrome/Chromium not found. Installing chromium-browser..."
    apt-get update
    apt-get install -y chromium-browser chromium-chromedriver
    CHROME_PATH=$(which chromium-browser)
    print_info "Chromium installed at: $CHROME_PATH"
fi

# Check for ChromeDriver
print_info "Checking for ChromeDriver..."

if command -v chromedriver &> /dev/null; then
    DRIVER_PATH=$(which chromedriver)
    print_info "ChromeDriver found at: $DRIVER_PATH"
    
    # Check version
    DRIVER_VERSION=$(chromedriver --version)
    print_info "ChromeDriver version: $DRIVER_VERSION"
else
    print_warning "ChromeDriver not found. Installing..."
    apt-get install -y chromium-chromedriver
    print_info "ChromeDriver installed"
fi

# Install Selenium if not already installed
print_info "Checking Python Selenium package..."
pip3 show selenium &> /dev/null || {
    print_info "Installing Selenium..."
    pip3 install selenium
}

# Install BeautifulSoup4 if not already installed
print_info "Checking BeautifulSoup4..."
pip3 show beautifulsoup4 &> /dev/null || {
    print_info "Installing BeautifulSoup4..."
    pip3 install beautifulsoup4
}

# GeM Credentials Configuration
print_info ""
print_info "GeM Portal Credentials Configuration"
print_info "========================================"

# Check if .env file exists
if [ -f "/var/www/hexabid/backend/.env" ]; then
    ENV_FILE="/var/www/hexabid/backend/.env"
elif [ -f "./backend/.env" ]; then
    ENV_FILE="./backend/.env"
else
    print_warning ".env file not found, creating new one"
    ENV_FILE="./backend/.env"
    touch $ENV_FILE
fi

# Check if credentials already exist
if grep -q "GEM_USERNAME" $ENV_FILE; then
    print_info "GeM credentials already configured in $ENV_FILE"
    
    read -p "Do you want to update credentials? (y/n): " update_creds
    
    if [ "$update_creds" != "y" ] && [ "$update_creds" != "Y" ]; then
        print_info "Keeping existing credentials"
    else
        # Remove old credentials
        sed -i '/GEM_USERNAME/d' $ENV_FILE
        sed -i '/GEM_PASSWORD/d' $ENV_FILE
        
        # Add new credentials
        echo "" >> $ENV_FILE
        echo "# GeM Portal Credentials" >> $ENV_FILE
        echo "GEM_USERNAME=\"prashant.hexatech@gmail.com\"" >> $ENV_FILE
        echo "GEM_PASSWORD=\"Hexa@gem123\"" >> $ENV_FILE
        
        print_info "GeM credentials updated in $ENV_FILE"
    fi
else
    # Add credentials
    echo "" >> $ENV_FILE
    echo "# GeM Portal Credentials" >> $ENV_FILE
    echo "GEM_USERNAME=\"prashant.hexatech@gmail.com\"" >> $ENV_FILE
    echo "GEM_PASSWORD=\"Hexa@gem123\"" >> $ENV_FILE
    
    print_info "GeM credentials added to $ENV_FILE"
fi

# Test scraper (optional)
print_info ""
read -p "Do you want to test the GeM scraper now? (y/n): " test_scraper

if [ "$test_scraper" = "y" ] || [ "$test_scraper" = "Y" ]; then
    print_info "Testing GeM scraper..."
    
    # Create test script
    cat > /tmp/test_gem_scraper.py <<'EOF'
import sys
sys.path.append('/var/www/hexabid/backend')
sys.path.append('./backend')

import asyncio
from gem_scraper import GeMScraper
import os

async def test():
    print("Initializing GeM Scraper...")
    scraper = GeMScraper(
        username=os.getenv('GEM_USERNAME'),
        password=os.getenv('GEM_PASSWORD')
    )
    
    print("Attempting to scrape tenders...")
    tenders = await scraper.scrape_latest_tenders(limit=5)
    
    print(f"\nFound {len(tenders)} tenders")
    for tender in tenders:
        print(f"- {tender.get('title', 'N/A')}")
    
    return len(tenders) > 0

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
EOF

    # Run test
    python3 /tmp/test_gem_scraper.py
    
    if [ $? -eq 0 ]; then
        print_info "✓ GeM scraper test successful!"
    else
        print_warning "GeM scraper test failed. Check credentials and network connectivity."
    fi
    
    rm /tmp/test_gem_scraper.py
fi

print_info ""
print_info "========================================"
print_info "GeM Scraper Configuration Complete"
print_info "========================================"
print_info ""
print_info "ChromeDriver: $DRIVER_PATH"
print_info "Credentials configured in: $ENV_FILE"
print_info ""
print_info "Note: The scraper will run in headless mode in production"
print_info "Ensure the server has sufficient memory and network access to gem.gov.in"
print_info ""

exit 0
