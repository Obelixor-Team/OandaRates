# Makefile for Code Quality Tools

.PHONY: all check format lint typecheck security complexity clean help

all: check

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  all         : Run all code quality checks (default)"
	@echo "  check       : Run all code quality checks"
	@echo "  format      : Run black to format the code"
	@echo "  lint        : Run ruff to lint the code"
	@echo "  typecheck   : Run mypy to type check the code"
	@echo "  security    : Run bandit to check for security issues"
	@echo "  complexity  : Run radon to check code complexity"
	@echo "  clean       : Clean up generated files"

check: format lint typecheck security complexity

format:
	black .

lint:
	ruff check . --exclude build

typecheck:
	mypy .

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
	rm -f oanda_instrument_log.txt
