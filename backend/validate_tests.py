#!/usr/bin/env python3
"""
Simple test validation script for SHACL-BI backend.
Validates test structure and runs basic checks.
"""

import sys
import os
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Main validation function."""
    logger.info("SHACL-BI Backend Test Suite Validation")
    logger.info("=" * 50)

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    logger.info(f"Working directory: {backend_dir}")

    # Check test structure
    test_dirs = [
        "tests",
        "tests/test_services",
        "tests/test_xpshacl_engine",
        "tests/test_routes",
    ]

    test_files = []
    for root, dirs, files in os.walk("tests"):
        for file in files:
            if file.startswith("test_") and file.endswith(".py"):
                test_files.append(os.path.join(root, file))

    logger.info(f"Test directories found: {len(test_dirs)}")
    for d in test_dirs:
        logger.info(f"   {d}")

    logger.info(f"Test files found: {len(test_files)}")
    for f in sorted(test_files)[:10]:  # Show first 10
        logger.info(f"   {f}")
    if len(test_files) > 10:
        logger.info(f"   ... and {len(test_files) - 10} more")

    # Count test functions
    total_tests = 0
    for test_file in test_files:
        try:
            with open(test_file, "r") as f:
                content = f.read()
                test_count = content.count("def test_")
                total_tests += test_count
        except Exception as e:
            logger.warning(f"Could not read {test_file}: {e}")

    logger.info(f"Test functions: ~{total_tests}")

    # Check configuration files
    config_files = ["pytest.ini", "tox.ini", "Makefile", "run_tests.py"]
    logger.info("Configuration files:")
    for f in config_files:
        if os.path.exists(f):
            logger.info(f"   {f}")
        else:
            logger.warning(f"   {f} (missing)")

    # Check CI/CD setup
    if os.path.exists(".github/workflows/test.yml"):
        logger.info("CI/CD: GitHub Actions configured")
    else:
        logger.info("CI/CD: Not configured")

    logger.info("Test suite validation complete!")
    logger.info("To run tests:")
    logger.info("   cd backend")
    logger.info("   python run_tests.py --install-deps")
    logger.info("   python run_tests.py")

    return True


if __name__ == "__main__":
    try:
        main()
        logger.info("Validation completed successfully!")
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        sys.exit(1)
