"""
BugMeNot Scraper - Gets login credentials from bugmenot.com
"""

import asyncio
import json
import re
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright

class BugMeNotScraper:
    def __init__(self, headless: bool = True):
        self.base_url = "http://bugmenot.com"
        self.headless = headless
        self.results = []
    
    async def scrape(self, website: str) -> List[Dict]:
        """Scrape credentials for a website"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            page = await browser.new_page()
            
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
        
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Saved {len(self.results)} credentials to {filename}")
    
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

# Quick usage functions
async def get_credentials(website: str, headless: bool = True) -> List[Dict]:
    """Quick function to get credentials for one website"""
    scraper = BugMeNotScraper(headless=headless)
    return await scraper.scrape(website)

async def get_multiple_credentials(websites: List[str], headless: bool = True) -> List[Dict]:
    """Quick function to get credentials for multiple websites"""
    scraper = BugMeNotScraper(headless=headless)
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
