"""
BugMeNot Scraper - Gets login credentials from bugmenot.com
"""

import asyncio
import json
import os
import random
import re
from datetime import datetime
from typing import List, Dict, Optional
from playwright.async_api import async_playwright

# Anonymization configuration
ANONYMIZATION_CONFIG = {
    "randomize_user_agent": True,
    "disable_webgl": True,
    "disable_canvas_fingerprinting": True,
    "randomize_timezone": True,
    "randomize_language": True,
    "block_webrtc": True,
    "disable_plugins": True,
}

# Random user agents pool for anonymization
USER_AGENTS_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
]

# Timezone options for randomization
TIMEZONE_OPTIONS = [
    "America/New_York",
    "America/Los_Angeles", 
    "America/Chicago",
    "Europe/London",
    "Europe/Paris",
    "Europe/Berlin",
    "Asia/Tokyo",
    "Australia/Sydney",
]

# Language options for randomization
LANGUAGE_OPTIONS = [
    "en-US,en;q=0.9",
    "en-GB,en;q=0.9",
    "en-CA,en;q=0.9",
    "en-AU,en;q=0.9",
]

class BugMeNotScraper:
    def __init__(self, headless: bool = True, proxy: Optional[str] = None, anonymize: bool = True):
        """
        Initialize BugMeNot scraper.        
        Args:
            headless: Whether to run browser in headless mode
            proxy: Proxy string in format "http://host:port" or "socks5://host:port"
            anonymize: Whether to enable anonymization features
        """
        self.base_url = "http://bugmenot.com"
        self.headless = headless
        self.proxy = proxy
        self.anonymize = anonymize
        self.results = []
    
    async def scrape(self, website: str) -> List[Dict]:
        """Scrape credentials for a website"""
        async with async_playwright() as p:
            # Configure browser launch options
            launch_options = {"headless": self.headless}
            
            # Configure proxy if provided
            if self.proxy:
                proxy_config = {"server": self.proxy}
            else:
                proxy_config = None
            
            browser = await p.chromium.launch(**launch_options)
            
            # Prepare context options with anonymization
            context_options = {
                "viewport": {"width": 1920, "height": 1080}
            }
            
            # Add proxy to context if specified
            if proxy_config:
                context_options["proxy"] = proxy_config
            
            # Anonymization features
            if self.anonymize:
                # Randomize user agent
                if ANONYMIZATION_CONFIG.get("randomize_user_agent"):
                    context_options["user_agent"] = random.choice(USER_AGENTS_POOL)
                    
                # Randomize timezone
                if ANONYMIZATION_CONFIG.get("randomize_timezone"):
                    context_options["timezone_id"] = random.choice(TIMEZONE_OPTIONS)
                    
                # Randomize language
                if ANONYMIZATION_CONFIG.get("randomize_language"):
                    context_options["locale"] = random.choice(LANGUAGE_OPTIONS).split(',')[0]
            
            context = await browser.new_context(**context_options)
            
            # Enhanced anonymization scripts
            if self.anonymize:
                await self._add_anonymization_scripts(context)
            else:
                # Basic webdriver removal
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
            
            page = await context.new_page()
            
            try:
                # Go to BugMeNot page for the website
                url = f"{self.base_url}/view/{website}"
                print(f"Scraping: {url}")
                
                await page.goto(url)
                await page.wait_for_timeout(3000)
                
                # Extract credentials from HTML structure
                credentials = await self._extract_credentials_from_html(page, website)
                
                print(f"Found {len(credentials)} credentials for {website}")
                return credentials
                
            except Exception as e:
                print(f"Error scraping {website}: {e}")
                return []
            finally:
                await context.close()
                await browser.close()
    
    async def _extract_credentials_from_html(self, page, website: str) -> List[Dict]:
        """Extract credentials with stats from HTML structure"""
        credentials = []
        
        # Get all account articles
        account_elements = await page.query_selector_all('article.account')
        
        for account in account_elements:
            try:
                # Extract username
                username_element = await account.query_selector('dt:has-text("Username:") + div kbd')
                username = await username_element.inner_text() if username_element else None
                
                # Extract password
                password_element = await account.query_selector('dt:has-text("Password:") + div kbd')
                password = await password_element.inner_text() if password_element else None
                
                # Extract stats
                success_rate = None
                votes = None
                age = None
                
                # Get stats list items
                stats_elements = await account.query_selector_all('dd.stats ul li')
                for stat_element in stats_elements:
                    stat_text = await stat_element.inner_text()
                    
                    # Extract success rate
                    if 'success rate' in stat_text.lower():
                        success_match = re.search(r'(\d+)%\s*success rate', stat_text)
                        if success_match:
                            success_rate = int(success_match.group(1))
                    
                    # Extract votes
                    elif 'votes' in stat_text.lower():
                        votes_match = re.search(r'(\d+)\s*votes?', stat_text)
                        if votes_match:
                            votes = int(votes_match.group(1))
                    
                    # Extract age
                    elif any(time_word in stat_text.lower() for time_word in ['old', 'months', 'years', 'days']):
                        age = stat_text.strip()
                
                # Validate and add credential
                if username and password and self._is_valid_credential(username, password):
                    credentials.append({
                        'website': website,
                        'username': username.strip(),
                        'password': password.strip(),
                        'success_rate': success_rate,
                        'votes': votes,
                        'age': age,
                        'scraped_at': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                print(f"Error extracting credential from account element: {e}")
                continue
        
        return credentials
    
    def _is_valid_credential(self, username: str, password: str) -> bool:
        """Check if credentials look valid"""
        if not username or not password:
            return False
        
        # Filter out common labels
        invalid_words = ['username', 'password', 'email', 'login', 'user', 'pass', 'example', 'test', 'password:']
        
        if username.lower() in invalid_words or password.lower() in invalid_words:
            return False
        
        # Skip if password is just "Password:" or similar
        if password.lower().endswith(':') or password.lower() == 'password':
            return False
        
        # Minimum length
        if len(username) < 3 or len(password) < 4:
            return False
        
        return True
    
    async def scrape_multiple(self, websites: List[str]) -> List[Dict]:
        """Scrape multiple websites"""
        all_credentials = []
        
        for website in websites:
            credentials = await self.scrape(website)
            all_credentials.extend(credentials)
            self.results.extend(credentials)
            
            # Be nice to the server
            await asyncio.sleep(2)
        
        return all_credentials
    
    def save_json(self, filename: str = None):
        """Save results to JSON"""
        if not filename:
            filename = f"bugmenot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        folder = 'output/bugmenot'
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        filepath = os.path.join(folder, filename)
        # Save results to JSON file
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Saved {len(self.results)} credentials to {filepath}")

        return filepath
    
    def print_results(self):
        """Print all results"""
        if not self.results:
            print("No credentials found")
            return
        
        print(f"\n=== Found {len(self.results)} credentials ===")
        for i, cred in enumerate(self.results, 1):
            print(f"{i}. {cred['website']}")
            print(f"   Username: {cred['username']}")
            print(f"   Password: {cred['password']}")
            if cred.get('success_rate'):
                print(f"   Success Rate: {cred['success_rate']}%")
            if cred.get('votes'):
                print(f"   Votes: {cred['votes']}")
            if cred.get('age'):
                print(f"   Age: {cred['age']}")
            print()

    async def _add_anonymization_scripts(self, context) -> None:
        """Add comprehensive anonymization scripts to the browser context."""
        anonymization_script = """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Override navigator properties
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // Override chrome property
        window.chrome = {
            runtime: {},
            loadTimes: function() {},
            csi: function() {},
            app: {}
        };
        
        // Remove automation signals
        const originalQuery = window.document.querySelector;
        window.document.querySelector = function(selector) {
            if (selector === 'script[src*="automation"]') {
                return null;
            }
            return originalQuery.call(document, selector);
        };
        
        // Disable WebGL fingerprinting if configured
        if (""" + str(ANONYMIZATION_CONFIG.get("disable_webgl", False)).lower() + """) {
            const getContext = HTMLCanvasElement.prototype.getContext;
            HTMLCanvasElement.prototype.getContext = function(type) {
                if (type === 'webgl' || type === 'webgl2') {
                    return null;
                }
                return getContext.call(this, type);
            };
        }
        
        // Disable canvas fingerprinting if configured  
        if (""" + str(ANONYMIZATION_CONFIG.get("disable_canvas_fingerprinting", False)).lower() + """) {
            const toDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function() {
                return 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==';
            };
        }
        
        // Block WebRTC if configured
        if (""" + str(ANONYMIZATION_CONFIG.get("block_webrtc", False)).lower() + """) {
            window.RTCPeerConnection = undefined;
            window.RTCDataChannel = undefined;
            window.RTCSessionDescription = undefined;
        }
        """
        
        await context.add_init_script(anonymization_script)
# Quick usage functions
async def get_credentials(website: str, headless: bool = True, proxy: Optional[str] = None, anonymize: bool = True) -> List[Dict]:
    """Quick function to get credentials for one website"""
    scraper = BugMeNotScraper(headless=headless, proxy=proxy, anonymize=anonymize)
    return await scraper.scrape(website)

async def get_multiple_credentials(websites: List[str], headless: bool = True, proxy: Optional[str] = None, anonymize: bool = True) -> List[Dict]:
    """Quick function to get credentials for multiple websites"""
    scraper = BugMeNotScraper(headless=headless, proxy=proxy, anonymize=anonymize)
    return await scraper.scrape_multiple(websites)

if __name__ == "__main__":
    # Example usage
    async def main():
        scraper = BugMeNotScraper(headless=False)  # Set True to hide browser
        
        # Test websites
        websites = ["nytimes.com", "wsj.com", "economist.com"]
        
        await scraper.scrape_multiple(websites)
        scraper.print_results()
        scraper.save_json()
    
    asyncio.run(main())
