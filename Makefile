# Makefile for Code Intelligence Skill

.PHONY: help build clean test check-env install

help:
	@echo "Available commands:"
	@echo "  make build      - Create the .skill archive for AI agents"
	@echo "  make test       - Run Python tests"
	@echo "  make check-env  - Run environment diagnostics"
	@echo "  make install    - Install the project in editable mode"
	@echo "  make clean      - Remove build artifacts and caches"

build:
	python3 build_skill.py

test:
	pytest tests/test_python.py

check-env:
	python3 safe_edit.py check-env

install:
	pip install -e ".[test]"

clean:
	rm -f code-intelligence.skill
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
