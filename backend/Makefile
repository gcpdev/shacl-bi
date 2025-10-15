.PHONY: help install install-dev test test-unit test-integration coverage lint format clean quality

# Default target
help:
	@echo "SHACL-BI Backend Test Suite"
	@echo ""
	@echo "Available commands:"
	@echo "  install      Install test dependencies"
	@echo "  install-dev  Install development dependencies"
	@echo "  test         Run all tests with coverage"
	@echo "  test-unit    Run only unit tests"
	@echo "  test-integration Run only integration tests"
	@echo "  coverage     Generate coverage report"
	@echo "  lint         Run linting"
	@echo "  format       Format code"
	@echo "  quality      Run quality checks"
	@echo "  clean        Clean test artifacts"
	@echo "  help         Show this help message"

# Install dependencies
install:
	pip install -r tests/requirements.txt

install-dev:
	pip install -r tests/requirements.txt
	pip install black flake8 isort mypy pytest-xdist

# Test commands
test:
	python run_tests.py --coverage --verbose

test-unit:
	python run_tests.py --unit --verbose

test-integration:
	python run_tests.py --integration --verbose

test-parallel:
	python -m pytest -n auto --cov=functions --cov=routes --cov-report=html

test-fast:
	python -m pytest -m "not slow" --cov=functions --cov=routes

# Coverage
coverage:
	python run_tests.py --coverage
	@echo "Coverage report available at htmlcov/index.html"

coverage-badge:
	python -c "
import coverage
cov = coverage.Coverage()
cov.load()
total = cov.report()
print(f'Coverage: {total:.1f}%')
"

# Code quality
lint:
	flake8 functions routes tests --max-line-length=127
	mypy functions routes --ignore-missing-imports

format:
	black functions routes tests
	isort functions routes tests

quality:
	python run_tests.py --quality
	$(MAKE) lint

# Cleaning
clean:
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf coverage.xml
	rm -rf .pytest_cache/
	rm -rf .tox/
	rm -rf test_report.txt
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Continuous integration targets
ci: install quality test
	@echo "CI pipeline completed successfully"

# Development targets
dev-setup: install-dev
	@echo "Development environment setup complete"

dev-test: test-unit lint
	@echo "Development tests completed"

# Quick checks
quick-check:
	python -c "import sys; print('Python version:', sys.version)"
	python -c "import pytest; print('Pytest installed')"
	python -c "import coverage; print('Coverage installed')"

# Benchmark tests
benchmark:
	python -m pytest --benchmark-only --benchmark-sort=mean

# Generate test matrix
test-matrix:
	python -m pytest --collect-only -q | grep "test session starts" -A 100 | head -20

# Check for missing tests
check-coverage:
	python -m pytest --cov=functions --cov=routes --cov-report=term-missing --cov-fail-under=90

# Full test suite
full-test: clean test coverage lint
	@echo "Full test suite completed"
	@echo "Coverage report: htmlcov/index.html"