"""
Utility functions for setting up and validating web scraping dependencies.

This module includes:
- Checking if Playwright is available
- Playwright installation validation
"""

import logging
import subprocess
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("scraper_utils")


def check_playwright_installation() -> Tuple[bool, Optional[str]]:
    """
    Check if Playwright is installed and browsers are available.

    Returns:
        Tuple of (is_installed, version_or_none)
    """
    try:
        # Try to import playwright
        import playwright
        
        # Try to get version
        result = subprocess.run(
            ["playwright", "--version"], capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        else:
            # Playwright is installed but CLI might not be available
            return True, getattr(playwright, '__version__', 'unknown')

    except ImportError:
        logger.error("Playwright is not installed")
        return False, None
    except Exception as e:
        logger.error(f"Error checking Playwright: {str(e)}")
        return False, None


def check_playwright_browsers() -> dict:
    """
    Check if Playwright browsers are installed.

    Returns:
        Dictionary with status of each browser
    """
    browsers = {
        "chromium": False,
        "firefox": False,
        "webkit": False
    }
    
    try:
        # Try to check browser installation
        result = subprocess.run(
            ["playwright", "install", "--dry-run"], 
            capture_output=True, text=True, check=False
        )
        
        if result.returncode == 0:
            output = result.stdout.lower()
            for browser in browsers:
                if f"{browser} is already installed" in output or f"downloading {browser}" not in output:
                    browsers[browser] = True
                    
    except Exception as e:
        logger.warning(f"Could not check browser installation: {e}")
        # Assume browsers are installed if we can't check
        browsers = {browser: True for browser in browsers}
    
    return browsers


def check_dependencies() -> dict:
    """
    Check all dependencies required for Playwright web scraping.

    Returns:
        Dictionary with status of each dependency
    """
    playwright_installed, playwright_version = check_playwright_installation()
    
    dependencies = {
        "playwright": playwright_installed,
        "playwright_version": playwright_version,
        "browsers": check_playwright_browsers() if playwright_installed else {}
    }

    # Log the results
    if playwright_installed:
        logger.info(f"✅ Playwright: Installed (version: {playwright_version})")
        for browser, installed in dependencies["browsers"].items():
            status = "✅ Available" if installed else "❌ Not installed"
            logger.info(f"  {browser}: {status}")
    else:
        logger.error("❌ Playwright: Not installed")

    return dependencies


def setup_instructions() -> str:
    """
    Generate setup instructions based on missing dependencies.

    Returns:
        String with setup instructions
    """
    dependencies = check_dependencies()
    instructions = []

    if not dependencies["playwright"]:
        instructions.append(
            "Playwright is not installed. Install using:\n"
            "pip install playwright\n"
            "playwright install"
        )
    else:
        missing_browsers = [
            browser for browser, installed in dependencies["browsers"].items() 
            if not installed
        ]
        
        if missing_browsers:
            instructions.append(
                f"Missing Playwright browsers: {', '.join(missing_browsers)}\n"
                "Install missing browsers using:\n"
                f"playwright install {' '.join(missing_browsers)}"
            )

    if not instructions:
        return "All dependencies are correctly installed. The scraper should work properly."
    else:
        return "Missing dependencies:\n" + "\n\n".join(instructions)


if __name__ == "__main__":
    # When run directly, check dependencies and print instructions
    print("Checking scraper dependencies...\n")
    deps = check_dependencies()

    print("\nSetup instructions:")
    print(setup_instructions())
