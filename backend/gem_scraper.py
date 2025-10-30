"""GeM Portal Scraper - Real-time tender data extraction"""
import asyncio
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timezone
import uuid
import logging
import json
import os

logger = logging.getLogger(__name__)

class GeMScraper:
    """Scraper for GeM (Government e-Marketplace) Portal"""
    
    def __init__(self, username=None, password=None):
        self.base_url = "https://gem.gov.in"
        self.api_url = "https://api.gem.gov.in"
        self.username = username or os.getenv('GEM_USERNAME')
        self.password = password or os.getenv('GEM_PASSWORD')
        self.authenticated = False
        self.setup_driver()
    
    def setup_driver(self):
        """Setup headless Chrome driver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        self.driver = webdriver.Chrome(options=chrome_options)
    
    async def login(self):
        """Login to GeM portal"""
        if not self.username or not self.password:
            logger.warning("GeM credentials not provided, proceeding without authentication")
            return False
        
        try:
            logger.info(f"Attempting to login to GeM portal with username: {self.username}")
            
            # Navigate to login page
            self.driver.get(f"{self.base_url}/login")
            
            # Wait for login form
            wait = WebDriverWait(self.driver, 15)
            
            # Find and fill username
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            
            # Find and fill password
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.ID, "login-button")
            login_button.click()
            
            # Wait for successful login (dashboard or profile element)
            wait.until(EC.url_contains("dashboard"))
            
            self.authenticated = True
            logger.info("Successfully logged into GeM portal")
            return True
            
        except Exception as e:
            logger.error(f"Failed to login to GeM portal: {e}")
            self.authenticated = False
            return False
    
    async def scrape_latest_tenders(self, category=None, limit=50):
        """
        Scrape latest tenders from GeM portal
        
        Args:
            category: Tender category filter
            limit: Number of tenders to fetch
        
        Returns:
            List of tender dictionaries
        """
        tenders = []
        
        try:
            # Login if credentials are available
            if self.username and self.password and not self.authenticated:
                await self.login()
            
            # Navigate to tender listing page
            url = f"{self.base_url}/bidlists/activeBids"
            self.driver.get(url)
            
            # Wait for page load
            wait = WebDriverWait(self.driver, 15)
            
            try:
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "bid-card")))
            except:
                # If bid-card class not found, try alternative selectors
                logger.warning("bid-card class not found, trying alternative methods")
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Wait additional time for dynamic content
            await asyncio.sleep(2)
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all tender cards
            tender_cards = soup.find_all('div', class_='bid-card')[:limit]
            
            # If no cards found with default class, try alternative approaches
            if not tender_cards:
                logger.warning(f"No tender cards found with class 'bid-card', found {len(tender_cards)} tenders")
                # Could implement alternative parsing logic here
            
            for card in tender_cards:
                try:
                    tender = self.parse_tender_card(card)
                    if tender and (not category or tender.get('category') == category):
                        tenders.append(tender)
                except Exception as e:
                    logger.error(f"Error parsing tender card: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Error scraping tenders: {e}")
        
        finally:
            self.driver.quit()
        
        return tenders
    
    def parse_tender_card(self, card):
        """Parse individual tender card HTML"""
        try:
            tender_id = card.find('span', class_='bid-number').text.strip()
            title = card.find('h3', class_='bid-title').text.strip()
            organization = card.find('span', class_='organization').text.strip()
            
            # Extract dates
            published_date_str = card.find('span', class_='published-date').text.strip()
            deadline_str = card.find('span', class_='closing-date').text.strip()
            
            # Extract values
            estimated_value_str = card.find('span', class_='estimated-value').text.strip()
            emd_amount_str = card.find('span', class_='emd-amount').text.strip()
            
            tender = {
                'id': str(uuid.uuid4()),
                'tender_id': tender_id,
                'title': title,
                'organization': organization,
                'description': card.find('p', class_='description').text.strip() if card.find('p', class_='description') else "",
                'estimated_value': self.parse_currency(estimated_value_str),
                'emd_amount': self.parse_currency(emd_amount_str),
                'category': self.detect_category(title),
                'location': card.find('span', class_='location').text.strip() if card.find('span', class_='location') else "India",
                'published_date': self.parse_date(published_date_str),
                'submission_deadline': self.parse_date(deadline_str),
                'status': 'active',
                'source': 'GeM',
                'eligibility_criteria': self.extract_eligibility(card),
                'technical_specs': {},
                'document_url': card.find('a', class_='download-doc')['href'] if card.find('a', class_='download-doc') else None,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            return tender
        
        except Exception as e:
            logger.error(f"Error parsing tender: {e}")
            return None
    
    def parse_currency(self, value_str):
        """Parse currency string to float"""
        try:
            # Remove ₹, commas, and convert to float
            value = value_str.replace('₹', '').replace(',', '').strip()
            # Handle Cr (Crores) and L (Lakhs)
            if 'Cr' in value:
                return float(value.replace('Cr', '')) * 10000000
            elif 'L' in value:
                return float(value.replace('L', '')) * 100000
            else:
                return float(value)
        except:
            return 0.0
    
    def parse_date(self, date_str):
        """Parse date string to ISO format"""
        try:
            # Handle various date formats
            formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%d %b %Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt).isoformat()
                except:
                    continue
            return datetime.now(timezone.utc).isoformat()
        except:
            return datetime.now(timezone.utc).isoformat()
    
    def detect_category(self, title):
        """Auto-detect tender category from title"""
        title_lower = title.lower()
        
        categories = {
            'IT Services': ['software', 'hardware', 'computer', 'it', 'server', 'network', 'cloud'],
            'Construction': ['construction', 'building', 'road', 'bridge', 'infrastructure'],
            'Medical Equipment': ['medical', 'hospital', 'healthcare', 'equipment', 'surgical'],
            'Office Supplies': ['stationery', 'furniture', 'office', 'supplies'],
            'Consulting': ['consulting', 'consultancy', 'advisory', 'management']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'General'
    
    def extract_eligibility(self, card):
        """Extract eligibility criteria"""
        criteria = []
        
        # Look for eligibility section
        eligibility_div = card.find('div', class_='eligibility')
        if eligibility_div:
            criteria_items = eligibility_div.find_all('li')
            criteria = [item.text.strip() for item in criteria_items]
        
        # Default criteria if none found
        if not criteria:
            criteria = [
                "Registered company with valid GST",
                "Minimum 2 years of experience",
                "Valid PAN and Aadhaar"
            ]
        
        return criteria
    
    async def download_tender_document(self, tender_id, document_url, save_path):
        """
        Download tender document (NIT/BOQ)
        
        Args:
            tender_id: Unique tender identifier
            document_url: URL to download document
            save_path: Path to save downloaded file
        
        Returns:
            Path to downloaded file or None
        """
        try:
            # Download document
            response = requests.get(document_url, stream=True)
            
            if response.status_code == 200:
                # Create directory if not exists
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                
                # Save file
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                logger.info(f"Downloaded document for tender {tender_id} to {save_path}")
                return save_path
            else:
                logger.error(f"Failed to download document: HTTP {response.status_code}")
                return None
        
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            return None
    
    async def get_tender_results(self, tender_id):
        """
        Scrape tender results (L1, L2, L3 bidders)
        
        Args:
            tender_id: GeM tender ID
        
        Returns:
            Dictionary with result data
        """
        try:
            url = f"{self.base_url}/tender-results/{tender_id}"
            self.driver.get(url)
            
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "result-table")))
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            results = {
                'tender_id': tender_id,
                'l1_bidder': None,
                'l2_bidder': None,
                'l3_bidder': None,
                'total_bidders': 0,
                'l1_price': 0.0,
                'award_date': None
            }
            
            # Parse result table
            result_table = soup.find('table', class_='result-table')
            if result_table:
                rows = result_table.find_all('tr')[1:]  # Skip header
                
                results['total_bidders'] = len(rows)
                
                if len(rows) >= 1:
                    l1_row = rows[0]
                    cols = l1_row.find_all('td')
                    results['l1_bidder'] = cols[1].text.strip()
                    results['l1_price'] = self.parse_currency(cols[2].text.strip())
                
                if len(rows) >= 2:
                    l2_row = rows[1]
                    cols = l2_row.find_all('td')
                    results['l2_bidder'] = cols[1].text.strip()
                
                if len(rows) >= 3:
                    l3_row = rows[2]
                    cols = l3_row.find_all('td')
                    results['l3_bidder'] = cols[1].text.strip()
            
            return results
        
        except Exception as e:
            logger.error(f"Error getting tender results: {e}")
            return None
    
    def __del__(self):
        """Cleanup"""
        try:
            self.driver.quit()
        except:
            pass


class HistoricalDataCollector:
    """Collect historical tender data for analytics"""
    
    def __init__(self, db):
        self.db = db
        self.scraper = GeMScraper()
    
    async def collect_historical_tenders(self, months=6):
        """
        Collect historical tender data
        
        Args:
            months: Number of months of historical data to collect
        
        Returns:
            Number of tenders collected
        """
        # This would scrape historical data from GeM portal
        # For now, we'll generate representative historical data
        pass
    
    async def collect_tender_results(self, tender_ids):
        """
        Collect results for list of tenders
        
        Args:
            tender_ids: List of GeM tender IDs
        
        Returns:
            Number of results collected
        """
        results_collected = 0
        
        for tender_id in tender_ids:
            result = await self.scraper.get_tender_results(tender_id)
            if result:
                # Store in database
                await self.db.tender_results.insert_one(result)
                results_collected += 1
        
        return results_collected
