#!/usr/bin/env python3
"""
Simple test runner for Delhi High Court Scraper only
Tests only the core scraper functionality
"""

import sys
import os
import subprocess

def run_scraper_tests():
    """Run only the scraper unit tests"""
    print("🧪 Running Delhi High Court Scraper Tests")
    print("=" * 50)
    
    try:
        # Run the simple scraper test file
        result = subprocess.run([
            sys.executable, 'tests/test_scraper_simple.py'
        ], capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        # Return success/failure based on exit code
        if result.returncode == 0:
            print("\n✅ Scraper tests completed successfully!")
            return True
        else:
            print(f"\n❌ Scraper tests failed with exit code: {result.returncode}")
            return False
            
    except FileNotFoundError:
        print("❌ Error: tests/test_scraper_simple.py not found")
        print("Make sure you're running this from the project root directory")
        return False
    
    except Exception as e:
        print(f"❌ Error running tests: {str(e)}")
        return False

if __name__ == "__main__":
    print("Delhi High Court Scraper - Simple Test Runner")
    print("=" * 50)
    
    # Run scraper tests only
    success = run_scraper_tests()
    
    if success:
        print("\n🎉 All scraper tests passed!")
        sys.exit(0)
    else:
        print("\n💥 Some scraper tests failed. Check the output above.")
        sys.exit(1)
