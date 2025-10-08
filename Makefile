# Makefile for Code Quality Tools

.PHONY: all check format lint typecheck security complexity clean help test

all: check test

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  all         : Run all code quality checks and tests (default)"
	@echo "  check       : Run all code quality checks"
	@echo "  format      : Run black to format the code"
	@echo "  lint        : Run ruff to lint the code"
	@echo "  typecheck   : Run mypy to type check the code"
	@echo "  security    : Run bandit to check for security issues"
	@echo "  complexity  : Run radon to check code complexity"
	@echo "  test        : Run pytest to execute tests"
  clean       : Clean up generated files
  run         : Run the application

check: format lint typecheck security complexity

run:
	python -m src.main

test:
	PYTHONPATH=. pytest

format:
	black .

lint:
	ruff check . --exclude build

typecheck:
	mypy --package src

security:
	bandit -r src/

complexity:
	radon cc src/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info
	rm -f oanda_rates.db
	rm -f oanda_instrument_log.txt
