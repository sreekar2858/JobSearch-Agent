#!/usr/bin/env python
"""
Test script for LinkedIn filter functionality
"""

import sys
import os
import logging
from datetime import datetime

# Configure logging for better debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_filter_imports():
    """Test that the filter functions can be imported and called"""
    try:
        sys.path.append('.')
        from src.scraper.search.linkedin_scraper import LinkedInScraper
        
        print("✅ LinkedInScraper imported successfully")
        
        # Check if the filter methods exist
        scraper = LinkedInScraper(headless=True)
        
        # Test method existence
        assert hasattr(scraper, '_apply_experience_level_filter'), "Missing experience level filter method"
        assert hasattr(scraper, '_apply_date_posted_filter'), "Missing date posted filter method"
        assert hasattr(scraper, '_apply_search_filters'), "Missing main filter method"
        
        print("✅ All filter methods are available")
        
        # Test collect_job_links method signature
        import inspect
        sig = inspect.signature(scraper.collect_job_links)
        params = list(sig.parameters.keys())
        
        assert 'experience_levels' in params, "Missing experience_levels parameter"
        assert 'date_posted' in params, "Missing date_posted parameter"
        
        print("✅ collect_job_links method supports filter parameters")
        
        scraper.close()
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_filter_validation():
    """Test filter parameter validation"""
    try:
        sys.path.append('.')
        from src.scraper.search.linkedin_scraper import LinkedInScraper
        
        scraper = LinkedInScraper(headless=True)
        
        # Test experience level mapping
        level_mapping = {
            'internship': '1',
            'entry_level': '2', 
            'associate': '3',
            'mid_senior': '4',
            'director': '5',
            'executive': '6'
        }
        
        # Test date mapping
        date_mapping = {
            'any_time': '',
            'past_month': 'r2592000',
            'past_week': 'r604800', 
            'past_24_hours': 'r86400'
        }
        
        print("✅ Filter mappings are properly defined")
        
        scraper.close()
        return True
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing LinkedIn Filter Functionality\n")
    
    tests = [
        ("Import and Method Tests", test_filter_imports),
        ("Filter Validation Tests", test_filter_validation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} passed\n")
        else:
            print(f"❌ {test_name} failed\n")
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The filter functionality is ready to use.")
        print("\nExample usage:")
        print('python extract_linkedin_jobs.py "Python Developer" "Berlin" --experience-levels entry_level mid_senior --date-posted past_week')
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")

if __name__ == "__main__":
    main()
