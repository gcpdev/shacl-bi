#!/usr/bin/env python3
"""
Clean test runner script for SHACL-BI backend.
Provides comprehensive testing with coverage reporting.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

# Setup basic logging for test runner
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return result

def install_test_dependencies():
    """Install test dependencies."""
    logger.info("Installing test dependencies...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", "tests/requirements.txt"]
    result = run_command(cmd)
    if result.returncode != 0:
        logger.error(f"Failed to install dependencies: {result.stderr}")
        return False
    logger.info("Dependencies installed successfully.")
    return True

def run_tests_basic():
    """Run basic tests without coverage."""
    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]

    # Add path to PYTHONPATH
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path.cwd())

    result = subprocess.run(cmd, env=env, capture_output=True, text=True)

    if result.stdout:
        logger.info(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        logger.error(f"STDERR:\n{result.stderr}")

    return result.returncode == 0

def main():
    """Main test runner."""
    logger.info("SHACL-BI Backend Test Runner")
    logger.info("=" * 50)

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    logger.info(f"Working directory: {backend_dir}")

    # Install dependencies
    if not install_test_dependencies():
        sys.exit(1)

    # Add current directory to Python path
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    # Run basic tests
    logger.info("\nRunning tests...")
    success = run_tests_basic()

    # Print summary
    logger.info("\n" + "=" * 50)
    if success:
        logger.info("Test execution completed successfully!")
    else:
        logger.error("Test execution failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()