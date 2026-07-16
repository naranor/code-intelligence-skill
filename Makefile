# Makefile for Code Intelligence Skill

.PHONY: help build verify test check-env install install-gemini install-claude install-all uninstall-gemini uninstall-claude clean

help:
	@echo "Available commands:"
	@echo "  make build              - Create the .skill archive for AI agents"
	@echo "  make verify             - Verify the .skill archive integrity"
	@echo "  make test               - Run all tests (unit + installer)"
	@echo "  make check-env          - Run environment diagnostics"
	@echo "  make install            - Install the project in editable mode (pip)"
	@echo "  make install-gemini     - Install the skill into Gemini CLI (user scope)"
	@echo "  make install-claude     - Install the skill into Claude Code (user scope)"
	@echo "  make install-all        - Install the skill into both CLIs (user scope)"
	@echo "  make uninstall-gemini   - Remove Gemini CLI installation"
	@echo "  make uninstall-claude   - Remove Claude Code installation"
	@echo "  make clean              - Remove build artifacts and caches"

build:
	python3 build_skill.py

verify:
	python3 build_skill.py verify

test:
	pytest tests/test_python.py tests/test_installer.py

check-env:
	python3 safe_edit.py check-env

install:
	pip install -e ".[test]"

install-gemini:
	python3 install_skill.py --target gemini-cli --scope user

install-claude:
	python3 install_skill.py --target claude-code --scope user

install-all:
	python3 install_skill.py --target all --scope user

uninstall-gemini:
	python3 install_skill.py --target gemini-cli --uninstall

uninstall-claude:
	python3 install_skill.py --target claude-code --uninstall

clean:
	rm -f code-intelligence.skill
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
