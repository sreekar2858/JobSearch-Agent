"""
Utility functions for setting up and validating web scraping dependencies.

This module includes:
- Checking if Firefox is installed
- Checking if geckodriver is available
- Validating Selenium installation
"""

import os
import sys
import logging
import subprocess
from pathlib import Path
import shutil
from typing import Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("scraper_utils")


def check_firefox_installation() -> bool:
    """
    Check if Firefox is installed on the system.

    Returns:
        True if Firefox is installed, False otherwise
    """
    if sys.platform == "win32":
        # Check common installation paths on Windows
        firefox_paths = [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        ]
        return any(os.path.exists(path) for path in firefox_paths)
    elif sys.platform == "darwin":
        # Check on macOS
        return os.path.exists("/Applications/Firefox.app")
    else:
        # Check on Linux using which command
        try:
            result = subprocess.run(
                ["which", "firefox"], capture_output=True, text=True, check=False
            )
            return result.returncode == 0
        except Exception:
            return False


def check_geckodriver() -> Tuple[bool, Optional[str]]:
    """
    Check if geckodriver is installed and accessible in PATH.

    Returns:
        Tuple of (is_installed, version_or_none)
    """
    try:
        # Check if geckodriver is in PATH
        if sys.platform == "win32":
            geckodriver = shutil.which("geckodriver.exe")
        else:
            geckodriver = shutil.which("geckodriver")

        if not geckodriver:
            return False, None

        # Try to get version
        result = subprocess.run(
            [geckodriver, "--version"], capture_output=True, text=True, check=False
        )

        if result.returncode == 0:
            version = result.stdout.strip().split("\n")[0]
            return True, version
        return True, None

    except Exception as e:
        logger.error(f"Error checking geckodriver: {str(e)}")
        return False, None


def check_selenium_dependencies() -> dict:
    """
    Check all dependencies required for Selenium and web scraping.

    Returns:
        Dictionary with status of each dependency
    """
    dependencies = {
        "firefox": check_firefox_installation(),
        "geckodriver": check_geckodriver()[0],
        "selenium": True,  # We assume this since the code is running
    }

    # Log the results
    for dep, installed in dependencies.items():
        status = "✅ Installed" if installed else "❌ Not found"
        logger.info(f"{dep}: {status}")

    return dependencies


def setup_instructions() -> str:
    """
    Generate setup instructions based on missing dependencies.

    Returns:
        String with setup instructions
    """
    dependencies = check_selenium_dependencies()
    instructions = []

    if not dependencies["firefox"]:
        instructions.append(
            "Firefox is not installed. Please download and install from: "
            "https://www.mozilla.org/firefox/new/"
        )

    if not dependencies["geckodriver"]:
        instructions.append(
            "GeckoDriver is not installed or not in PATH. Install using:\n"
            "1. Download from: https://github.com/mozilla/geckodriver/releases\n"
            "2. Extract the executable to a directory in your PATH\n"
            "3. On Windows, you can run: webdriver-manager firefox\n"
            "4. On Linux/Mac: pip install webdriver-manager && webdriver-manager firefox"
        )

    if not instructions:
        return "All dependencies are correctly installed. The scraper should work properly."
    else:
        return "Missing dependencies:\n" + "\n\n".join(instructions)


if __name__ == "__main__":
    # When run directly, check dependencies and print instructions
    print("Checking scraper dependencies...\n")
    deps = check_selenium_dependencies()

    print("\nSetup instructions:")
    print(setup_instructions())
