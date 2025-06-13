"""
BugMeNot Scraper CLI
Command-line interface for scraping credentials from bugmenot.com

Usage:
    python cli.py --website glassdoor.com --output latest.json
    python cli.py --website nytimes.com --visible
    python -m src.scraper.buggmenot --website economist.com
"""

import asyncio
import argparse

try:
    from .bugmenot_scraper import BugMeNotScraper
except ImportError:
    # Fallback for direct script execution
    from bugmenot_scraper import BugMeNotScraper

def display_credentials(credentials):
    """Display credentials with metadata in a formatted way"""
    print(f"\n✅ Found {len(credentials)} credentials:")
    for i, cred in enumerate(credentials, 1):
        success_rate = f"{cred['success_rate']}%" if cred.get('success_rate') else "N/A"
        votes = cred.get('votes', 'N/A')
        age = cred.get('age', 'N/A')
        print(f"  {i}. {cred['username']} / {cred['password']}")
        print(f"     Success: {success_rate} | Votes: {votes} | Age: {age}")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="BugMeNot Scraper - Get login credentials from bugmenot.com",
        formatter_class=argparse.RawDescriptionHelpFormatter,        epilog="""
Examples:
  python cli.py --website glassdoor.com --output latest.json
  python cli.py --website nytimes.com --visible
  python -m src.scraper.buggmenot --website economist.com  """
    )
    
    parser.add_argument(
        '--website', '-w',
        type=str,
        required=True,
        help='Website to scrape credentials for (e.g., glassdoor.com)'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Output JSON filename (default: auto-generated)'
    )
    
    parser.add_argument(
        '--visible', '-v',
        action='store_true',
        help='Show browser window (default: headless)'
    )
    
    parser.add_argument(
        '--proxy',
        type=str,
        help='Proxy server (e.g., http://proxy:port or socks5://proxy:port)'
    )
    
    parser.add_argument(
        '--no-anonymize',
        action='store_true',
        help='Disable anonymization features (user agent randomization, WebGL blocking, etc.)'
    )
    
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='Don\'t save results to file'
    )
    
    return parser.parse_args()

def main(args=None, **kwargs):
    """Main function that handles both CLI args and kwargs"""
    print("🔍 BugMeNot Scraper")
    print("=" * 30)
    
    # Parse args if not provided
    if args is None:
        args = parse_args()
      # Use provided args
    website = args.website
    visible = args.visible
    proxy = getattr(args, 'proxy', None)
    anonymize = not getattr(args, 'no_anonymize', False)
    save = not args.no_save
    filename = args.output
    
    # Override with kwargs if provided
    website = kwargs.get('website', website)
    visible = kwargs.get('visible', visible)
    proxy = kwargs.get('proxy', proxy)
    anonymize = kwargs.get('anonymize', anonymize)
    save = kwargs.get('save', save)
    filename = kwargs.get('filename', filename)
    
    print(f"Using website: {website}")
    if proxy:
        print(f"Using proxy: {proxy}")
    print(f"Anonymization: {'enabled' if anonymize else 'disabled'}")
    
    async def scrape():
        scraper = BugMeNotScraper(headless=not visible, proxy=proxy, anonymize=anonymize)
        print(f"\nScraping {website}...")
        credentials = await scraper.scrape(website)
        
        if credentials:
            display_credentials(credentials)
            
            if save:
                scraper.results = credentials
                if filename:
                    scraper.save_json(filename)
                    print(f"\n💾 Results saved to: {filename}")
                else:
                    saved_file = scraper.save_json()
                    print(f"\n💾 Results saved to: {saved_file}")
        else:
            print("❌ No credentials found")
    
    # Run the scraper
    asyncio.run(scrape())

if __name__ == "__main__":
    # Always parse command-line arguments - no interactive mode
    args = parse_args()
    main(args)
