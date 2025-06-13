"""
BugMeNot Scraper CLI
Command-line interface for scraping credentials from bugmenot.com

Usage:
    python cli.py --website glassdoor.com --output latest.json
    python cli.py --website nytimes.com --visible
    python cli.py  # Interactive mode
"""

import asyncio
import argparse
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
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --website glassdoor.com --output latest.json
  python cli.py --website nytimes.com --visible
  python cli.py  # Interactive mode
        """
    )
    
    parser.add_argument(
        '--website', '-w',
        type=str,
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
        '--no-save',
        action='store_true',
        help='Don\'t save results to file'
    )
    
    return parser.parse_args()

def main(args=None, **kwargs):
    """Main function that handles both CLI args and kwargs"""
    print("🔍 BugMeNot Scraper")
    print("=" * 30)
    
    # If args is provided (from CLI), use those; otherwise use kwargs or prompt
    if args:
        website = args.website
        visible = args.visible
        save = not args.no_save
        filename = args.output
    else:
        # Get website from kwargs or user input
        website = kwargs.get('website')
        visible = kwargs.get('visible')
        save = kwargs.get('save')
        filename = kwargs.get('filename')
    
    # Get website if not provided
    if not website:
        website = input("Enter website (e.g. nytimes.com): ").strip()
        if not website:
            website = "nytimes.com"
            print(f"Using default: {website}")
    else:
        print(f"Using website: {website}")
    
    # Ask about browser visibility if not specified
    if visible is None:
        visible = input("Show browser? (y/n): ").strip().lower() == 'y'
    
    async def scrape():
        nonlocal save, filename  # Make these variables accessible in the nested function
        
        scraper = BugMeNotScraper(headless=not visible)
        print(f"\nScraping {website}...")
        credentials = await scraper.scrape(website)
        
        if credentials:
            display_credentials(credentials)
            
            # Save option (or use kwargs/args)
            if save is None:
                save = input("\nSave to file? (y/n): ").strip().lower() == 'y'
            if save:
                scraper.results = credentials
                if filename:
                    scraper.save_json(filename)
                else:
                    scraper.save_json()
        else:
            print("❌ No credentials found")
      # Run the scraper
    asyncio.run(scrape())

if __name__ == "__main__":
    import sys
    
    # Check if command-line arguments are provided
    if len(sys.argv) > 1:
        # Parse command-line arguments
        args = parse_args()
        main(args)
    else:
        # Interactive mode - no args
        main()
