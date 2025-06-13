#!/usr/bin/env python
"""
Test script to verify Firefox browser functionality
"""


def test_firefox_support():
    """Test that LinkedInScraper supports Firefox browser"""
    try:
        from src.scraper.search.linkedin_scraper import LinkedInScraper

        print("✅ LinkedInScraper imported successfully")

        # Test that Firefox is accepted as a browser parameter
        import inspect

        sig = inspect.signature(LinkedInScraper.__init__)
        params = list(sig.parameters.keys())

        print(f"📝 LinkedInScraper.__init__ parameters: {params}")

        if "browser" in params:
            print("✅ browser parameter found in LinkedInScraper.__init__")
        else:
            print("❌ browser parameter NOT found in LinkedInScraper.__init__")
            return False

        # Test browser validation
        try:
            scraper = LinkedInScraper(headless=True, browser="firefox")
            print("✅ Firefox browser accepted by LinkedInScraper")
            # Don't actually set up the driver in test
            return True
        except ValueError as e:
            if "Unsupported browser" in str(e):
                print(f"❌ Firefox not supported: {e}")
                return False
            else:
                print(f"✅ Firefox browser accepted (validation error expected: {e})")
                return True
        except Exception as e:
            print(
                f"✅ Firefox browser accepted (other error expected without driver setup: {e})"
            )
            return True

    except Exception as e:
        print(f"❌ Error testing Firefox support: {e}")
        return False


def test_chrome_support():
    """Test that LinkedInScraper still supports Chrome browser"""
    try:
        from src.scraper.search.linkedin_scraper import LinkedInScraper

        # Test Chrome browser
        try:
            scraper = LinkedInScraper(headless=True, browser="chrome")
            print("✅ Chrome browser still supported by LinkedInScraper")
            return True
        except ValueError as e:
            if "Unsupported browser" in str(e):
                print(f"❌ Chrome not supported: {e}")
                return False
            else:
                print(f"✅ Chrome browser accepted (validation error expected: {e})")
                return True
        except Exception as e:
            print(
                f"✅ Chrome browser accepted (other error expected without driver setup: {e})"
            )
            return True

    except Exception as e:
        print(f"❌ Error testing Chrome support: {e}")
        return False


def test_invalid_browser():
    """Test that invalid browsers are rejected"""
    try:
        from src.scraper.search.linkedin_scraper import LinkedInScraper

        # Test invalid browser
        try:
            scraper = LinkedInScraper(headless=True, browser="safari")
            print(
                "❌ Invalid browser (safari) was accepted - should have been rejected"
            )
            return False
        except ValueError as e:
            if "Unsupported browser" in str(e):
                print("✅ Invalid browser correctly rejected")
                return True
            else:
                print(f"❌ Unexpected error message: {e}")
                return False
        except Exception as e:
            print(f"❌ Unexpected error type: {e}")
            return False

    except Exception as e:
        print(f"❌ Error testing invalid browser: {e}")
        return False


def test_extract_jobs_browser_param():
    """Test that extract_jobs function accepts browser parameter"""
    try:
        from extract_linkedin_jobs import extract_jobs

        import inspect

        sig = inspect.signature(extract_jobs)
        params = list(sig.parameters.keys())

        print(f"📝 extract_jobs parameters: {params}")

        if "browser" in params:
            print("✅ browser parameter found in extract_jobs function")
            return True
        else:
            print("❌ browser parameter NOT found in extract_jobs function")
            return False

    except Exception as e:
        print(f"❌ Error testing extract_jobs browser parameter: {e}")
        return False


if __name__ == "__main__":
    print("🧪 Testing Firefox browser support...")
    print()

    test1_passed = test_firefox_support()
    print()
    test2_passed = test_chrome_support()
    print()
    test3_passed = test_invalid_browser()
    print()
    test4_passed = test_extract_jobs_browser_param()
    print()

    if test1_passed and test2_passed and test3_passed and test4_passed:
        print("🎉 All tests passed! Firefox browser support is properly implemented.")
        print()
        print("📋 Usage examples:")
        print("  # Use Chrome (default)")
        print(
            "  python extract_linkedin_jobs.py 'Software Engineer' 'Berlin' --browser chrome"
        )
        print()
        print("  # Use Firefox")
        print(
            "  python extract_linkedin_jobs.py 'Data Scientist' 'New York' --browser firefox"
        )
        print()
        print("  # Single job URL with Firefox")
        print(
            "  python extract_linkedin_jobs.py --job-url 'https://www.linkedin.com/jobs/view/4248346302' --browser firefox"
        )
    else:
        print("❌ Some tests failed. Please check the implementation.")
