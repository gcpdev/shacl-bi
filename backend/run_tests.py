#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner script for SHACL-BI backend.
Provides comprehensive testing with coverage reporting.
"""

import sys
import os
import subprocess
import argparse
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

def run_tests_with_coverage(args):
    """Run tests with coverage measurement."""
    test_args = [
        "-m", "pytest",
        "--cov=functions",
        "--cov=routes",
        "--cov=app.py",
        "--cov=config.py",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-report=xml",
        "--cov-fail-under=90"
    ]

    if args.verbose:
        test_args.append("-v")
    if args.pattern:
        test_args.extend(["-k", args.pattern])
    if args.markers:
        test_args.extend(["-m", args.markers])
    if args.path:
        test_args.append(args.path)

    cmd = [sys.executable] + test_args
    result = run_command(cmd)

    if result.returncode == 0:
        logger.info("\nAll tests passed!")
        logger.info(f"Coverage report generated: {Path.cwd()}/htmlcov/index.html")
    else:
        logger.error(f"\nTests failed with return code {result.returncode}")
        if result.stdout:
            logger.info(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.error(f"STDERR: {result.stderr}")

    return result.returncode == 0

def run_unit_tests_only():
    """Run only unit tests (no integration tests)."""
    cmd = [sys.executable, "-m", "pytest", "-m", "unit", "-v"]
    result = run_command(cmd)
    return result.returncode == 0

def run_integration_tests_only():
    """Run only integration tests."""
    cmd = [sys.executable, "-m", "pytest", "-m", "integration", "-v"]
    result = run_command(cmd)
    return result.returncode == 0

def generate_coverage_badge():
    """Generate coverage badge."""
    try:
        import coverage
        cov = coverage.Coverage()
        cov.load()
        total = cov.report(file=open(os.devnull, 'w'))

        # Simple text badge
        badge_color = "brightgreen" if total >= 90 else "yellow" if total >= 70 else "red"
        logger.info(f"\nCoverage Badge: {total:.1f}%")
        logger.info(f"Color: {badge_color}")
    except ImportError:
        logger.info("Coverage module not available for badge generation")

def check_test_quality():
    """Check test quality metrics."""
    logger.info("\n* Checking test quality metrics...")

    # Count test files
    test_files = list(Path("tests").rglob("test_*.py"))
    logger.info(f"* Test files found: {len(test_files)}")

    # Count test functions
    total_tests = 0
    for test_file in test_files:
        with open(test_file, 'r') as f:
            content = f.read()
            test_count = content.count('def test_')
            total_tests += test_count
    logger.info(f"* Test functions: {total_tests}")

    # Check for test structure
    structure_files = [
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/requirements.txt"
    ]
    missing_files = [f for f in structure_files if not Path(f).exists()]
    if missing_files:
        logger.info(f"  Missing test structure files: {missing_files}")
    else:
        logger.info("* Test structure is complete")

    return len(test_files) > 0 and total_tests > 0

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="SHACL-BI Backend Test Runner")
    parser.add_argument("--install", action="store_true", help="Install test dependencies")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--coverage", action="store_true", default=True, help="Run tests with coverage")
    parser.add_argument("--no-coverage", action="store_true", help="Run tests without coverage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--markers", "-m", help="Run tests with specific markers")
    parser.add_argument("--path", help="Run tests in specific path")
    parser.add_argument("--quality", action="store_true", help="Check test quality metrics")
    parser.add_argument("--install-deps", action="store_true", help="Install dependencies first")

    args = parser.parse_args()

    logger.info("SHACL-BI Backend Test Runner")
    logger.info("=" * 50)

    # Change to backend directory
    backend_dir = Path(__file__).parent
    os.chdir(backend_dir)
    logger.info(f"Working directory: {backend_dir}")

    # Install dependencies if requested
    if args.install or args.install_deps:
        if not install_test_dependencies():
            sys.exit(1)

    # Check test quality
    if args.quality:
        if not check_test_quality():
            logger.info(" Test quality check failed")
            sys.exit(1)

    success = True

    # Run tests based on arguments
    if args.unit:
        logger.info("\n* Running unit tests only...")
        success = run_unit_tests_only()
    elif args.integration:
        logger.info("\n* Running integration tests only...")
        success = run_integration_tests_only()
    elif args.no_coverage:
        logger.info("\n* Running tests without coverage...")
        cmd = [sys.executable, "-m", "pytest"]
        if args.verbose:
            cmd.append("-v")
        if args.pattern:
            cmd.extend(["-k", args.pattern])
        if args.markers:
            cmd.extend(["-m", args.markers])
        if args.path:
            cmd.append(args.path)

        result = run_command(cmd)
        success = result.returncode == 0
    else:
        logger.info("\n* Running tests with coverage...")
        success = run_tests_with_coverage(args)
        if success:
            generate_coverage_badge()

    # Print summary
    logger.info("\n" + "=" * 50)
    if success:
        logger.info("* Test execution completed successfully!")
        logger.info("\n* Coverage reports available:")
        logger.info(f"   HTML: {backend_dir}/htmlcov/index.html")
        logger.info(f"   XML:  {backend_dir}/coverage.xml")
        logger.info(f"   Terminal: See above for missing coverage")
    else:
        logger.info("* Test execution failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()